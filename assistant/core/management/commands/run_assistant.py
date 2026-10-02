import importlib
import json
import pkgutil
import queue
import threading
import time

from core.utils.voicing_answer import run_voice
from django.core.management.base import BaseCommand

from core.assistant import actions as actions_pkg
from core.assistant.actions.base import ACTIONS, ActionContext
from core.assistant.config import COMMANDS_JSON_PATH
from core.assistant.nlp.matcher import CommandMatcher
from core.assistant.nlp.text import normalize_text
from core.assistant.listeners.factory import create_listener
from core.assistant.stdin_reader import StdinReader         

LISTEN_TIMEOUT = 7.5
ARG_ACTIONS = {"open", "close", "delete", "open_group"}
WAIT_NO_ARGS = 4.5             
WAIT_WITH_ARGS = 1.5   

def load_actions():
    for module in pkgutil.iter_modules(actions_pkg.__path__):
        if module.name != "base":
            importlib.import_module(f"{actions_pkg.__name__}.{module.name}")
            print(f"Підключено дію-модуль: {module.name}", flush=True)

    print(f"Зареєстровані дії: {sorted(ACTIONS)}", flush=True)

def load_commands_map():
    with open(COMMANDS_JSON_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


class Command(BaseCommand):
    help = "Запускає голосового помічника"

    def handle(self, *args, **options):
        load_actions()
        commands_map = load_commands_map()
        commands_map.pop("answers", None)

        unknown = set(commands_map) - set(ACTIONS)
        if unknown:
            print(f"Увага: у commands.json є дії без реалізації: {sorted(unknown)}", flush=True)

        matcher = CommandMatcher(commands_map)
        running = threading.Event()
        running.set()
        inputs: queue.Queue[tuple[str, bool]] = queue.Queue()

        speaking = threading.Event()
        state = {"end": 0.0}

        def is_running() -> bool:
            return running.is_set()

        def stop():
            running.clear()

        def speak(text):
            print(f"ANSWER: {text}", flush=True)
            speaking.set()
            try:
                run_voice(text).join()
            finally:
                state["end"] = time.monotonic()
                speaking.clear()

        def listen():
            try:
                return inputs.get(timeout=LISTEN_TIMEOUT)[0]
            except queue.Empty:
                return None

        ctx = ActionContext(listen=listen, speak=speak, stop=stop)

        print("Завантажую розпізнавання мови...", flush=True)
        listener = create_listener(is_running)

        def mic_loop():
            while is_running():
                try:
                    text = listener.listen()
                except Exception as error:
                    print(f"LISTENER ERROR: {error}", flush=True)
                    continue
                if text and text.strip():
                    print(f"Голос: {text}", flush=True)
                    inputs.put((text, True))

        threading.Thread(target=mic_loop, daemon=True).start()
        StdinReader(on_text=lambda t: inputs.put((t, False)), is_running=is_running).start()

        print("Помічник запущений. Готовий до команд.", flush=True)

        while is_running():
            try:
                raw, from_voice = inputs.get(timeout=0.5)
            except queue.Empty:
                continue

            if from_voice:
                action_name, matched, text = self.collect(raw, matcher, inputs, is_running)
            else:
                text = normalize_text(raw)
                action_name, matched = matcher.match(text)

            self.process(action_name, matched, text, ctx)

        print("Помічник зупинено.", flush=True)

    @staticmethod
    def collect(raw, matcher, inputs, is_running):
        text = normalize_text(raw)
        action, matched = matcher.match(text)

        if action not in ARG_ACTIONS:
            return action, matched, text

        while is_running():
            args = text.replace(matched, "", 1).strip()
            wait = WAIT_WITH_ARGS if args else WAIT_NO_ARGS
            if not args:
                print("Слухаю продовження...", flush=True)
            try:
                more, _ = inputs.get(timeout=wait)
            except queue.Empty:
                break
            text = normalize_text(f"{text} {more}")

        return action, matched, text

    @staticmethod
    def process(action_name, matched, text, ctx):
        if not text:
            return
        if not action_name:
            print(f"Команду не розпізнано: {text}", flush=True)
            return
        action = ACTIONS.get(action_name)
        if action is None:
            print(f"Дія '{action_name}' не зареєстрована", flush=True)
            return
        try:
            action.execute(ctx, text, matched)
        except Exception as error:
            print(f"Помилка дії {action_name}: {error}", flush=True)
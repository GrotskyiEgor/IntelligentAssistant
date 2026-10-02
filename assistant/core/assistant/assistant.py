import json
from ..utils.voicing_answer import run_voice

from .config import COMMANDS_JSON_PATH
from .nlp.matcher import CommandMatcher
from .nlp.text import normalize_text
from .listeners.factory import create_listener
from .stdin_reader import StdinReader
from .actions import ACTIONS, ActionContext


class Assistant:
    def __init__(self):
        self.running = True

        with open(COMMANDS_JSON_PATH, encoding="utf-8") as f:
            commands = json.load(f)
            
        commands.pop("answers", None)
        self.matcher = CommandMatcher(commands)

        self.listener = create_listener(lambda: self.running)
        self.ctx = ActionContext(
            listen=self.listener.listen,
            speak=run_voice,
            stop=self.stop,
        )
        self.stdin = StdinReader(self.handle_text, lambda: self.running)

    def stop(self):
        self.running = False

    def handle_text(self, text: str):
        text = normalize_text(text)
        action_name, matched = self.matcher.match(text)

        if not action_name:
            print("Дію не визначено", flush=True)
            return

        action = ACTIONS.get(action_name)
        if not action:
            print(f"Немає обробника для дії: {action_name}", flush=True)
            return

        print(f"Дія: {action_name}, знайдено: {matched}", flush=True)
        action.execute(self.ctx, text, matched)

    def run(self):
        print("Асистент запущений", flush=True)
        self.stdin.start()

        while self.running:
            try:
                text = self.listener.listen()
                if text:
                    print("Ви сказали:", repr(text), flush=True)
                    self.handle_text(text)
            except KeyboardInterrupt:
                self.stop()
            except Exception as error:
                print(f"Помилка: {error}", flush=True)
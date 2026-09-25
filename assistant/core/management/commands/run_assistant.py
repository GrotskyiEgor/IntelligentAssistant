import os
import sys
import json
import queue
import platform
import subprocess
import speech_recognition
import threading

import numpy as np
import sounddevice as sd

from pathlib import Path


from torch import cuda as gpu
from faster_whisper import WhisperModel

from rapidfuzz import fuzz, process
from django.core.management.base import BaseCommand

from utils.find_path import find_path
from utils.voicing_answer import run_voice
from core.models import *



COMMANDS_JSON_PATH = Path(__file__).resolve().parent.parent.parent.parent / "utils" / "commands.json"

class Command(BaseCommand):
    def __init__(self):
        super().__init__()

        with open(COMMANDS_JSON_PATH, "r", encoding="utf-8") as file:
            self.commands_map = json.load(file)

        print("Інтелектуальний помічник", flush=True)

        self.run = True
        self.audio_queue = queue.Queue()

        self.stdin_thread = threading.Thread(
            target=self.read_stdin,
            daemon=True
        )
        self.stdin_thread.start()

        if gpu.is_available():
            # print("Графічний процесор знайдено використовую whisper", flush=True)

            self.use_whisper = True
            self.whisper = WhisperModel(
                "large-v3",
                device="cuda",
                compute_type="float16"
            )

        else:
            # print("Графічний процесор не знайдено використовуюэ google speech", flush=True)

            self.use_whisper = False

            self.recognizer = speech_recognition.Recognizer()
            self.microphone = speech_recognition.Microphone()

            print("Налаштовую фоновий шум", flush=True)

            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source=source)

    def read_stdin(self):
        while self.run:
            try:
                text = sys.stdin.readline()

                if not text:
                    break

                text = text.strip()

                if text and len(text):
                    print(f"Текстові команди: {text}", flush=True)
                    self.doing_task(text)

            except Exception as error:
                print(f"STDIN ERROR: {error}", flush=True)
                break

    def handle(self, *args, **kwargs):
        print("Асистент запущений", flush=True)
        print("Слухаю вас", flush=True)

        command = kwargs.get("command")
        if len(command):
            print("Команди:", command, flush=True)

        while self.run:
            try:
                text = self.listen()

                if text:
                    print("Ви сказали:", repr(text), flush=True)
                    self.doing_task(text)

            except KeyboardInterrupt:
                print("KeyboardInterrupt", flush=True)
                self.run = False

            except Exception as error:
                print(f"Помилка: {error}", flush=True)

    def listen(self):
        if self.use_whisper:
            return self.listen_whisper()

        return self.listen_google()

    def listen_google(self):
        with self.microphone as source:
            try:
                audio = self.recognizer.listen(source=source, phrase_time_limit=7.5)
            except Exception as error:
                print(f"LISTEN ERROR: {error}", flush=True)
                return None

        try:
            return self.recognizer.recognize_google(audio, language="uk-UA")
        except speech_recognition.UnknownValueError:
            return None
        except Exception as error:
            print(f"RECOGNIZE ERROR: {error}", flush=True)
            return None

    def listen_whisper(self):
        buffer = []
        silence_chunks = 0
        silence_limit = 40
        speaking = False

        with sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype="float32",
            blocksize=160,
            callback=self.audio_callback
        ):

            while self.run:
                data = self.audio_queue.get()
                volume = np.sqrt(np.mean(data ** 2))
                is_speech = volume > 0.01

                if is_speech:
                    speaking = True
                    silence_chunks = 0
                    buffer.append(data)

                elif speaking:
                    buffer.append(data)
                    silence_chunks += 1

                    if silence_chunks >= silence_limit:
                        if not buffer:
                            continue

                        audio = np.concatenate(buffer, axis=0).flatten()

                        duration_sec = len(audio) / 16000
                        avg_volume = np.sqrt(np.mean(audio ** 2))

                        if duration_sec < 0.4 or avg_volume < 0.015:
                            buffer = []
                            silence_chunks = 0
                            speaking = False
                            continue

                        segments, info = self.whisper.transcribe(
                            audio,
                            language="uk",
                            beam_size=5,
                            temperature=0,
                            vad_filter=True,
                            vad_parameters=dict(min_silence_duration_ms=300)
                        )

                        text = " ".join(
                            segment.text.strip()
                            for segment in segments
                            if segment.text.strip()
                        )

                        buffer = []
                        silence_chunks = 0
                        speaking = False

                        return text

    def doing_task(self, text):
        text_lower = self.normalize_text(text)

        action, matched_word = self.get_action(text_lower)

        if not action:
            print("Дію не визначено")
            return

        print(f"Дія: {action}, знайдено: {matched_word}")

        if action == "help":
            self.help()
            return

        if action == "stop":
            self.run = False
            return

        if action == "add_command":
            self.create_command_by_voice()
            return

        if action == "greeting":
            run_voice("Привіт, чим можу допомогти?")
            return

        if action in ("open", "close"):
            app_text = text_lower.replace(matched_word, "", 1).strip()

            if not app_text:
                run_voice("Не вказано назву програми")
                return

            print(f"Програма: {app_text}")

            user_app = self.find_app(app_text)

            if not user_app:
                run_voice(f"Я не знайшла програму {app_text}")
                return

            print(self.style.SUCCESS(f"Знайдено: {user_app.name}"))

            if action == "open":
                run_voice(f"Відкриваю {user_app.name}")

                if user_app.path:
                    self.open_app(path_app=user_app.path)
                else:
                    run_voice(f"Шукаю {user_app.name}")

                    path = find_path(filename=user_app.name)

                    if path:
                        run_voice(f"Знайшла {user_app.name}")

                        self.open_app(path_app=path)

                        user_app.path = path
                        user_app.save()
                    else:
                        run_voice(
                            f"Я не знайшла шлях до {user_app.name}"
                        )

            elif action == "close":
                run_voice(f"Закриваю {user_app.name}")

                if user_app.path:
                    app_name = os.path.basename(user_app.path)
                    self.close_app(app_name=app_name)
                else:
                    run_voice(
                        f"Я не знаю шлях до {user_app.name}"
                    )

    def create_command_by_voice(self):
        run_voice("Як називається програма?")

        name = self.listen()

        if not name:
            run_voice("Я не почула назву програми")
            return

        name = self.normalize_text(name)

        run_voice(f"Шукаю програму {name}")

        path = find_path(filename=name)

        if not path:
            run_voice(f"Я не знайшла програму {name}")
            return

        run_voice(f"Знайшла {name}. Яке ключове слово використовувати для запуску?")

        keyword = self.listen()

        if not keyword:
            run_voice("Я не почула ключове слово")
            return

        keyword = self.normalize_text(keyword)

        command = AppCommand.objects.create(
            name=name,
            keyword=keyword,
            path=path
        )

        run_voice(f"Команду для {command.name} успішно додано")

    def close_app(self, app_name: str):
        try:
            system = platform.system()

            if system == "Windows":
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", app_name, "/T"],
                    capture_output=True,
                    text=True,
                    encoding="cp866",
                    errors="replace"
                )

                if result.returncode == 0:
                    print(f"Процес {app_name} успішно закрито")
                else:
                    print(f"Не вдалося закрити {app_name}")

            elif system == "Darwin":
                subprocess.run(["pkill", "-f", app_name], capture_output=True, text=True)
            else:
                subprocess.run(["pkill", "-f", app_name], capture_output=True, text=True)

        except Exception as error:
            print(f"Помилка закриття: {error}")

    def open_app(self, path_app: str):
        try:
            print("path_app", path_app)
            system = platform.system()

            if system == "Windows":
                os.startfile(filepath=path_app)
            elif system == "Darwin":
                subprocess.Popen(args=["open", path_app])
            else:
                subprocess.Popen(args=[path_app])

        except Exception as error:
            print(self.style.WARNING(f"Помилка запуску: {error}"))

    def match_phrase(self, text, action_key):
        text = self.normalize_text(text)
        phrases = self.commands_map.get(action_key, [])

        for phrase in phrases:
            phrase_norm = self.normalize_text(phrase)

            if " " in phrase_norm:
                score = fuzz.partial_ratio(phrase_norm, text)

                if score >= 80:
                    return True

            else:
                for word in text.split():
                    score = fuzz.ratio(word, phrase_norm)

                    if score >= 80:
                        return True

        return False

    def get_action(self, text):
        text = self.normalize_text(text)

        best_matches = []

        for action_key, phrases in self.commands_map.items():
            best_score = 0
            best_word = None

            for phrase in phrases:
                phrase_norm = self.normalize_text(phrase)

                if " " in phrase_norm:
                    score = fuzz.partial_ratio(phrase_norm, text)

                    if score > best_score:
                        best_score = score
                        best_word = phrase

                else:
                    for word in text.split():
                        score = fuzz.ratio(word, phrase_norm)

                        if score > best_score:
                            best_score = score
                            best_word = word

            if best_score >= 80:
                best_matches.append(
                    (action_key, best_score, best_word)
                )

        if not best_matches:
            return None, None

        best_matches.sort(key=lambda x: x[1], reverse=True)
        best_action, best_score, best_word = best_matches[0]

        if len(best_matches) > 1:
            second_action, second_score, _ = best_matches[1]

            if (
                second_action != best_action
                and best_score - second_score < 5
            ):
                return None, None

        return best_action, best_word

    def find_app(self, text):
        commands = AppCommand.objects.all()

        best_command = None
        best_score = 0

        text = self.normalize_text(text)

        for command in commands:
            keyword = self.normalize_text(command.keyword)
            name = self.normalize_text(command.name)

            keyword_score = fuzz.ratio(text, keyword)
            name_score = fuzz.ratio(text, name)
            token_score = fuzz.token_set_ratio(text, keyword)

            score = max(keyword_score, name_score, token_score)

            if score > best_score:
                best_score = score
                best_command = command

        if best_score >= 60:
            return best_command

        return None

    def normalize_text(self, text):
        return " ".join(text.lower().strip().split())

    def add_arguments(self, parser):
        parser.add_argument("command", nargs="*", type=str)

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"Стан аудио: {status}", flush=True)

        self.audio_queue.put(indata.copy())
        
    def help(self):
        self.stdout.write("Список можливих дій: \n\n • Додати команду \n • Закрий 'Назва додатку'\n • Відкрий 'Назва додатку'\n • Відкрий/Закрий групу 'Назва групи'\n • Відкрий сайт 'Назва сайту'\n • Збільшити гучність \n • Зменшити гучність \n • Зупинись \n\nСписок додатків: ")

        for app_command in AppCommand.objects.all():
            self.stdout.write(f" • Ключове слово - {app_command.keyword}, Назва додатку - {app_command.name}")
        self.stdout.write("\nГолосові запити:")
        for voice_answer in VoiceAnswer.objects.all():
            self.stdout.write(f' • {voice_answer.request}')
        self.stdout.write("\nСписок сайтів:")
        for site in WebSite.objects.all():
            self.stdout.write(f' • {site.name}, url - {site.url}')

        self.run = False
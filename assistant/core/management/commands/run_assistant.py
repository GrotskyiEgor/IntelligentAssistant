import os
import sys
import queue
import platform
import subprocess
import speech_recognition
import threading

import numpy as np
import sounddevice as sd

from torch import cuda as gpu
from faster_whisper import WhisperModel

from rapidfuzz import fuzz, process
from django.core.management.base import BaseCommand

from utils.find_path import find_path
from utils.voicing_answer import run_voice
from core.models import *


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

        print("Inteligen Assistatnt", flush=True)

        self.run = True
        self.audio_queue = queue.Queue()

        self.stdin_thread = threading.Thread(
            target=self.read_stdin,
            daemon=True
        )
        self.stdin_thread.start()

        if gpu.is_available():
            print("GPU знайдено, використовую whisper", flush=True)

            self.use_whisper = True
            self.whisper = WhisperModel(
                "large-v3",
                device="cuda",
                compute_type="float16"
            )

        else:
            print("GPU не знайдено, використовую google speech", flush=True)

            self.use_whisper = False

            self.recognizer = speech_recognition.Recognizer()
            self.microphone = speech_recognition.Microphone()

            print("Почекайте, налаштовую фоновий шум", flush=True)

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
                    print(f"Text commands: {text}", flush=True)
                    self.doing_task(text)

            except Exception as error:
                print(f"STDIN ERROR: {error}", flush=True)
                break

    def handle(self, *args, **kwargs):
        print("Асистент запущений", flush=True)
        print("Слухаю вас", flush=True)

        command = kwargs.get("command")
        if len(command):
            print("Commands:", command, flush=True)

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
                audio = self.recognizer.listen(source=source, phrase_time_limit=5)
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

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(f"AUDIO STATUS: {status}", flush=True)

        self.audio_queue.put(indata.copy())

    def doing_task(self, text):
        text_lower = text.lower()

        if "допомога" in text_lower:
            self.help()
            return

        if "зупинись" in text_lower:
            self.run = False
            return

        if "додати команду" in text_lower or "додай команду" in text_lower:
            self.create_command_by_voice()
            return

        action = self.get_action(text)

        if not action:
            return

        app_text = text_lower

        command_words = ["відкрий", "відкрити", "запусти", "запустити", "відкривай", "закрий", "закрити", "закривай", "вимкни", "вимкнути"]

        for word in command_words:
            app_text = app_text.replace(word, "")

        app_text = app_text.strip()
        print(f"Дія {action}, програма {app_text}")
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
                    run_voice(f"Я не знайшла шлях до {user_app.name}")

        elif action == "close":
            run_voice(f"Закриваю {user_app.name}")

            if user_app.path:
                app_name = os.path.basename(user_app.path)
                self.close_app(app_name=app_name)
            else:
                run_voice(f"Я не знаю шлях до {user_app.name}")

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

    def get_action(self, text):
        text = self.normalize_text(text)

        open_commands = ["відкрий", "відкрити", "запусти", "запустити", "відкривай"]
        close_commands = ["закрий", "закрити", "закривай", "вимкни", "вимкнути"]

        words = text.split()

        for word in words:
            result = process.extractOne(word, open_commands, scorer=fuzz.ratio)
            if result and result[1] >= 70:
                return "open"

            result = process.extractOne(word, close_commands, scorer=fuzz.ratio)
            if result and result[1] >= 70:
                return "close"

        return None

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
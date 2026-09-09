from django.core.management.base import BaseCommand
import speech_recognition, platform, os, subprocess, webbrowser, pyautogui, pygame
from rapidfuzz import fuzz, process


from utils.find_path import find_path
from utils.voicing_answer import run_voice
from core.models import *


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print(kwargs.get("command"))
        if len(kwargs.get("command")) and kwargs.get("command")[0] == "help":
            self.help()
            return

        self.run = True
        print(self.style.SUCCESS("Асистент запущений..."))

        # Инициализация класса для распознавания голоса
        recognizer = speech_recognition.Recognizer()
        # Считываем микро
        microphone = speech_recognition.Microphone()

        # Получение голоса в source
        with microphone as source:
            print("Почекайте, налаштовую фоновий шум...")

            # Убираем фоновый шум
            recognizer.adjust_for_ambient_noise(source=source)
            print(self.style.SUCCESS("Слухаю вас..."))

            while self.run:
                try:
                    # 5 сек записи голоса
                    audio = recognizer.listen(source=source, phrase_time_limit=3)

                    # audio в текст на uk-UA
                    text = recognizer.recognize_google(audio, language="uk-UA")

                    self.doing_task(text=text, source=source)
                except speech_recognition.UnknownValueError:
                    continue
                except Exception as error:
                    print(self.style.WARNING(f"Помилка!\n{error}"))

    def doing_task(self, text, source):
        print(f"Ви сказали: {text}")

        text_lower = text.lower()

        if "допомога" in text_lower:
            self.help()
            return

        if "зупинись" in text_lower:
            self.run = False
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
        print("assistant help")
        self.run = False

    def close_app(self, app_name: str):
        try:
            # Получение ос
            system = platform.system()

            if system == "Windows":
                result = subprocess.run(
                    args=["taskkill", "/F", "/IM", "chrome.exe", "/T"],
                    capture_output=True,
                    text=True,
                )

                # print("Код возврата:", result.returncode)
                # print("Вывод (stdout):", result.stdout)
                # print("Ошибки (stderr):", result.stderr)
            else: 
                subprocess.run(args=["pkill", app_name])

        except Exception as error:
            print(self.style.WARNING(f"Помилка закриття: {error}"))
            
    def open_app(self, path_app: str):
        try:
            print("path_app", path_app)
            # Получение ос
            system = platform.system()

            if system == "Windows":
                os.startfile(filepath=path_app)
            elif system == "Darwin":
                subprocess.Popen(args = ["open", path_app])
            else:
                subprocess.Popen(args=[path_app])

        except Exception as error:
            print(self.style.WARNING(f"Помилка запуску: {error}"))

    def add_arguments(self, parser):
            parser.add_argument(
                "command",
                nargs="*",
                type=str
            )

    def get_action(self, text):
        text = self.normalize_text(text)

        open_commands = ["відкрий", "відкрити", "запусти", "запустити", "відкривай"]
        close_commands = ["закрий", "закрити", "закривай", "вимкни", "вимкнути"]

        words = text.split()

        for word in words:
            result = process.extractOne(
                word,
                open_commands,
                scorer=fuzz.ratio
            )

            if result and result[1] >= 70:
                return "open"

            result = process.extractOne(
                word,
                close_commands,
                scorer=fuzz.ratio
            )

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

            score = max(
                keyword_score,
                name_score,
                token_score
            )

            if score > best_score:
                best_score = score
                best_command = command

        if best_score >= 60:
            return best_command

        return None

    def normalize_text(self, text):
        return " ".join(text.lower().strip().split())
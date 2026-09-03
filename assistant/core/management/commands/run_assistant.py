from django.core.management.base import BaseCommand
import speech_recognition, platform, os, subprocess, webbrowser, pyautogui, pygame


from core.models import AppCommand

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print(kwargs.get("command"))
        if len(kwargs.get("command")) and kwargs.get("command")[0] == "help":
            self.help()
            return

        self.run = True
        self.stdout.write(self.style.SUCCESS("Асистент запущений..."))

        # Инициализация класса для распознавания голоса
        recognizer = speech_recognition.Recognizer()
        # Считываем микро
        microphone = speech_recognition.Microphone()

        # Получение голоса в source
        with microphone as source:
            self.stdout.write("Почекайте, налаштовую фоновий шум...")

            # Убираем фоновый шум
            recognizer.adjust_for_ambient_noise(source=source)
            self.stdout.write(self.style.SUCCESS("Слухаю вас..."))

            while self.run:
                try:
                    # 5 сек записи голоса
                    audio = recognizer.listen(source=source, phrase_time_limit=5)

                    # audio в текст на uk-UA
                    text = recognizer.recognize_google(audio, language="uk-UA")

                    self.doing_task(text=text, source=source)
                except speech_recognition.UnknownValueError:
                    continue
                except Exception as error:
                    self.stdout.write(self.style.WARNING(f"Помилка!\n{error}"))

    def doing_task(self, text, source):
        self.stdout.write(f"Ви сказали: {text}")

        if "допомога" in text.lower():
            self.help()
        elif "зупинись" in text.lower():
            self.run = False
        elif ("відкрий" or "закрий") in text.lower():
            print("Відкрий програму aбо Закрий програму")
            all_commnds = AppCommand.objects.all()
            list_apps = []

            for command in all_commnds:
                if command.keyword.lower() in text.lower():
                    list_apps.append(command)

            print(list_apps)

    def help(self):
        print("assistant help")
        self.run = False

    def close_app(self, app_name: str):
        try:
            # Получение ос
            system = platform.system()

            if system == "Windows":
                # Завершает внешнюю програму из кода
                subprocess.run(
                    args = ["taskkill", "/IM", app_name, "/F"],
                    stdout= subprocess.DEVNULL,
                    stderr= subprocess.DEVNULL
                )
            else: 
                subprocess.run(args= ["pkill", app_name])

        except Exception as error:
            self.stdout.write(self.style.WARNING(f"Помилка закриття: {error}"))
            
    def open_app(self, path_app: str):
        try:
            # Получение ос
            system = platform.system()

            if system == "Windows":
                os.startfile(filepath=path_app)
            elif system == "Darwin":
                subprocess.Popen(args = ["open", path_app])
            else:
                subprocess.Popen(args=[path_app])

        except Exception as error:
            self.stdout.write(self.style.WARNING(f"Помилка запуску: {error}"))

    def add_arguments(self, parser):
            parser.add_argument(
                "command",
                nargs="*",
                type=str
            )
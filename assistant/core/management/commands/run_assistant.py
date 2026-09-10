import speech_recognition, platform, os, subprocess, webbrowser, pyautogui, pygame, site
import queue, sounddevice as sd, numpy as np

from django.core.management.base import BaseCommand
from faster_whisper import WhisperModel
from torch import cuda

from utils.find_path import find_path
from utils.voicing_answer import run_voice
from core.models import *

class Command(BaseCommand):
    def __init__(self):
        super().__init__()
        
        self.whisper = WhisperModel(
            "medium",
            device="cuda",
            compute_type="float32"
        )

        self.audio_queue = queue.Queue()
        self.run = True
        
    def handle(self, *args, **kwargs):
        if len(kwargs.get("command")) and kwargs.get("command")[0] == "help":
            self.help()
            return

        self.stdout.write(self.style.SUCCESS("Асистент запущений..."))

        while self.run:
            try:
                text = self.listen()

                if not text:
                    continue

                self.doing_task(text=text)

            except Exception as error:
                self.stdout.write(f"Помилка!\n{error}")

    def doing_task(self, text):
        self.stdout.write(f"Ви сказали: {text}")

        if "допомога" in text.lower():
            self.help()
        elif "зупинись" in text.lower():
            self.run = False
        elif "відкрий" in text.lower() or "закрий" in text.lower():
            all_commnds = AppCommand.objects.all()
            list_apps = []

            for command in all_commnds:
                if command.keyword.lower() in text.lower():
                    list_apps.append(command)

            # if "групу" in text.lower():
            #     groups = AppGroup.objects.all()

            #     for group in groups:
            #         if group.name.lower() in text.lower():
            #             list_apps.extend(group.apps.all())

            self.stdout.write(list_apps)
            if list_apps:
                if len(list_apps) >= 1:
                    if "відкрий" in text.lower():
                        run_voice("Відкриваю програми")
                    else:
                        run_voice("Закриваю програми")

                    for user_app in list_apps:
                        if user_app.path:
                            if "відкрий" in text.lower():
                                if len(list_apps) == 1: 
                                    run_voice(f"Відкриваю {user_app.name}")

                                self.open_app(path_app=user_app.path)
                            else:
                                if len(list_apps) == 1: 
                                    (f"Закриваю {user_app.name}")

                                self.close_app(app_name=os.path.basename(user_app.path))

                        else:
                            if len(list_apps) == 1: 
                                run_voice(f"Шукаю {user_app.name}")

                            path = find_path(filename = user_app.name)
                            
                            if path:
                                if len(list_apps) == 1: 
                                    run_voice(f"Знайшла {user_app.name}")

                                if "відкрий" in text.lower():
                                    self.open_app(path_app=path)
                                else: 
                                    self.close_app(app_name=os.path.basename(user_app.path))
                                
                                user_app.path = path
                                user_app.save()
                            else:
                                if len(list_apps) == 1: 
                                    run_voice("Я не знайшла шлях до цієї програми") 
                else:
                    run_voice("Я не знайшла такої програми")    

            self.stdout.write(list_apps)

    def help(self):
        self.stdout.write("assistant help")
        self.run = False

    def close_app(self, app_name: str):
        try:
            self.stdout.write("close apppppp", app_name)
            # Получение ос
            system = platform.system()

            if system == "Windows":
                # Завершает внешнюю програму из кода
                # subprocess.run(
                #     args=["taskkill", "/IM", app_name, "/F"],
                #     stdout=subprocess.DEVNULL,
                #     stderr=subprocess.DEVNULL
                # )

                result = subprocess.run(
                    args=["taskkill", "/F", "/IM", "chrome.exe", "/T"],
                    capture_output=True,  # Захватываем вывод, чтобы прочитать ошибку
                    text=True,
                )

                # self.stdout.write("Код возврата:", result.returncode)
                # self.stdout.write("Вывод (stdout):", result.stdout)
                # self.stdout.write("Ошибки (stderr):", result.stderr)
            else: 
                subprocess.run(args= ["pkill", app_name])

        except Exception as error:
            self.stdout.write(self.style.WARNING(f"Помилка закриття: {error}"))
            
    def open_app(self, path_app: str):
        try:
            self.stdout.write("path_app", path_app)
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

    def audio_callback(self, indata, frames, time, status):
            self.audio_queue.put(indata.copy())

    def listen(self):
            buffer = []

            with sd.InputStream(samplerate=16000, channels=1, callback=self.audio_callback):
                while self.run:
                    data = self.audio_queue.get()
                    buffer.append(data)


                    if len(buffer) > 20:
                        audio = np.concatenate(buffer, axis=0).flatten()

                        segments, _ = self.whisper.transcribe(
                            audio,
                            language="ru",
                            vad_filter=True
                        )

                        for segment in segments:
                            text = segment.text.strip()
                            if text:
                                return text

                        buffer = []
    
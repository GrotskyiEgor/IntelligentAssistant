import speech_recognition
from .base import Listener


class GoogleListener(Listener):
    def __init__(self):
        self.recognizer = speech_recognition.Recognizer()
        self.microphone = speech_recognition.Microphone()
        print("Налаштовую фоновий шум", flush=True)
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source=source)

    def listen(self):
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
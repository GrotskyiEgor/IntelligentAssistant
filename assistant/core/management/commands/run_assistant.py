import queue, sounddevice as sd, numpy as np
from torch import cuda as gpu

from django.core.management.base import BaseCommand
from faster_whisper import WhisperModel

from utils.voicing_answer import run_voice
from utils.handler import define_command


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

        if gpu.is_available():
            self.whisper = WhisperModel(
                "large-v3",
                device="cuda",
                compute_type="int8"
            )
        else:
            self.whisper = WhisperModel(
                "small",
                device="cpu",
                compute_type="int8"
            )

        self.audio_queue = queue.Queue()
        self.run = True

    def handle(self, *args, **kwargs):

        self.write("Assistant started...")
        self.success("Listening...")

        while self.run:
            try:
                text = self.listen()

                if text:
                    self.write(f"> {text}")

                    commands = define_command(text)
                    words = text.split()

                    for cmd, index in commands:
                        if cmd == 'open':
                            app = words[index + 1] if index + 1 < len(words) else None
                            print('Open:', app)

                        if cmd == 'close':
                            app = words[index + 1] if index + 1 < len(words) else None
                            print('Close:', app)

                    # run_voice(f'commands: {command}')

            except Exception as error:
                self.write(f"Помилка!\n{error}")

    def audio_callback(self, indata, frames, time, status):
        if status:
            self.write(str(status))

        self.audio_queue.put(indata.copy())

    def success(self, txt):
        self.stdout.write(self.style.SUCCESS(txt))

    def write(self, txt):
        self.stdout.write(txt)

    def listen(self):

        buffer = []

        silence_chunks = 0

        silence_limit = 50

        speaking = False

        with sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype="float32",
            blocksize=320,
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

                        audio = np.concatenate(
                            buffer,
                            axis=0
                        ).flatten()

                        segments, _ = self.whisper.transcribe(
                            audio,
                            language="ru",
                            beam_size=5,
                            temperature=0,
                            vad_filter=False
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
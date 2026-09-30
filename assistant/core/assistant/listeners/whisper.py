import queue
from typing import Callable

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from .base import Listener

SAMPLE_RATE = 16000


class WhisperListener(Listener):
    def __init__(self, is_running: Callable[[], bool]):
        self.is_running = is_running
        self.audio_queue = queue.Queue()
        self.model = WhisperModel("large-v3", device="cuda", compute_type="float16")

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"Стан аудио: {status}", flush=True)
        self.audio_queue.put(indata.copy())

    def listen(self):
        buffer, silence, speaking = [], 0, False

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                            blocksize=160, callback=self._callback):
            while self.is_running():
                data = self.audio_queue.get()
                if np.sqrt(np.mean(data ** 2)) > 0.01:
                    speaking, silence = True, 0
                    buffer.append(data)
                elif speaking:
                    buffer.append(data)
                    silence += 1
                    if silence >= 40:
                        audio = np.concatenate(buffer).flatten()
                        buffer, silence, speaking = [], 0, False
                        if self._too_quiet_or_short(audio):
                            continue
                        return self._transcribe(audio)

    @staticmethod
    def _too_quiet_or_short(audio):
        return len(audio) / SAMPLE_RATE < 0.4 or np.sqrt(np.mean(audio ** 2)) < 0.015

    def _transcribe(self, audio):
        segments, _ = self.model.transcribe(
            audio, language="uk", beam_size=5, temperature=0,
            vad_filter=True, vad_parameters=dict(min_silence_duration_ms=300),
        )
        return " ".join(s.text.strip() for s in segments if s.text.strip())
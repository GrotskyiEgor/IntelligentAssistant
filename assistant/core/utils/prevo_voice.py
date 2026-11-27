"""Озвучка через бібліотеку prevotts, якщо вона доступна.

speak(text) повертає текст, який лишилося озвучити запасним варіантом (edge-tts):
  - "" - усе вже озвучено через prevotts;
  - увесь текст - prevotts недоступний (немає бібліотеки, ключа, мережі чи звуку);
  - залишок - prevotts зламався посередині.
Помилок назовні не кидає.
"""
import os
import re
import tempfile
import threading
import time
from pathlib import Path

ENV_KEY = "PREVOTTS_API_KEY"
ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
AUDIO_DIR = os.path.join(tempfile.gettempdir(), "prevotts_audio")

# Бібліотека називає файл за текстом, тому текст ріжемо на короткі шматки
# і прибираємо символи, заборонені в іменах файлів.
MAX_CHUNK = 100
COOLDOWN = 300  # скільки секунд не чіпати prevotts після збою
FORBIDDEN = re.compile(r'[<>"/\\|*\x00-\x1f]')

_lock = threading.Lock()
_state = {"client": None, "disabled": False, "retry_at": 0.0}


def _load_key() -> str:
    key = os.environ.get(ENV_KEY, "").strip()
    if key:
        return key

    try:
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{ENV_KEY}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass

    return ""


def _limit_timeouts(client):
    """Бібліотека чекає відповідь до 60 с. Скорочуємо, щоб збій не мовчав хвилину."""
    original = client.session.request

    def request(method, url, **kwargs):
        kwargs["timeout"] = (5, 30)
        return original(method, url, **kwargs)

    client.session.request = request


def _get_client():
    if _state["disabled"] or time.monotonic() < _state["retry_at"]:
        return None
    if _state["client"] is not None:
        return _state["client"]

    with _lock:
        if _state["disabled"]:
            return None
        if _state["client"] is not None:
            return _state["client"]

        try:
            key = _load_key()
            if not key:
                raise RuntimeError(f"не задано {ENV_KEY}")

            from prevotts import Prevo

            client = Prevo(key, AUDIO_DIR)
            _limit_timeouts(client)
            _state["client"] = client
        except Exception as error:
            _state["disabled"] = True
            print(f"TTS: prevotts недоступний ({error}), використовую edge-tts", flush=True)
            return None

    return _state["client"]


def _chunks(text, limit=MAX_CHUNK):
    text = " ".join(FORBIDDEN.sub(" ", text).split())
    sentences = re.split(r"(?<=[.!?…])\s+", text)

    result, current = [], ""
    for sentence in sentences:
        if len(sentence) > limit:
            if current:
                result.append(current)
                current = ""
            piece = ""
            for word in sentence.split():
                word = word[:limit]
                if piece and len(piece) + 1 + len(word) > limit:
                    result.append(piece)
                    piece = word
                else:
                    piece = f"{piece} {word}".strip()
            current = piece
        elif current and len(current) + 1 + len(sentence) > limit:
            result.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()

    if current:
        result.append(current)

    return [chunk for chunk in result if re.search(r"\w", chunk)]


def speak(text) -> str:
    client = _get_client()
    if client is None:
        return text

    chunks = _chunks(text)
    if not chunks:
        return text

    for index, chunk in enumerate(chunks):
        try:
            client.voice(chunk)
        except Exception as error:
            _state["retry_at"] = time.monotonic() + COOLDOWN
            print(f"TTS: збій prevotts ({error}), далі edge-tts", flush=True)
            return " ".join(chunks[index:])

    return ""

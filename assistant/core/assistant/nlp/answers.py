import json
import re
from functools import lru_cache

from ..config import COMMANDS_JSON_PATH
from .text import normalize_text


def _prepare(text):
    text = normalize_text(text.replace("’", "'").replace("ʼ", "'"))
    text = re.sub(r"[^\w' ]+", " ", text)
    return " ".join(text.split())


@lru_cache(maxsize=1)
def _load():
    with open(COMMANDS_JSON_PATH, encoding="utf-8") as file:
        raw = json.load(file).get("answers", {})
    return {key: tuple(_prepare(p) for p in phrases) for key, phrases in raw.items()}


def _contains(text, key):
    padded = f" {_prepare(text)} "
    return any(f" {phrase} " in padded for phrase in _load().get(key, ()))


def is_no(text):
    return _contains(text, "no")


def is_cancel(text):
    return _contains(text, "cancel")


def is_yes(text):
    return not is_no(text) and _contains(text, "yes")
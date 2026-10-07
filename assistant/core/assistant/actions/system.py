import ctypes
import subprocess

from .base import Action, register
from ..nlp.dialog import ask_text
from ..nlp.text import normalize_text

VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_KEYUP = 0x0002

VOLUME_STEPS = 5

YES_WORDS = {
    "так", "ага", "угу", "авжеж", "звісно", "звичайно", "давай",
    "добре", "гаразд", "окей", "ок", "yes", "підтверджую", "точно",
}


def _press_key(vk_code, times=1):
    for _ in range(times):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


def _confirm(ctx, question):
    answer = ask_text(ctx, question, "Я не почула відповідь. Скажіть так або ні")
    if not answer:
        return False
    return bool(set(normalize_text(answer).split()) & YES_WORDS)


@register
class VolumeUp(Action):
    name = "volume_up"

    def execute(self, ctx, text, matched):
        _press_key(VK_VOLUME_UP, VOLUME_STEPS)
        ctx.speak("Гучніше")


@register
class VolumeDown(Action):
    name = "volume_down"

    def execute(self, ctx, text, matched):
        _press_key(VK_VOLUME_DOWN, VOLUME_STEPS)
        ctx.speak("Тихіше")


@register
class Shutdown(Action):
    name = "shutdown"

    def execute(self, ctx, text, matched):
        if not _confirm(ctx, "Ви впевнені, що хочете вимкнути комп'ютер?"):
            return ctx.speak("Скасовую")

        ctx.speak("Вимикаю комп'ютер")
        subprocess.run(["shutdown", "/s", "/t", "5"])


@register
class Restart(Action):
    name = "restart"

    def execute(self, ctx, text, matched):
        if not _confirm(ctx, "Ви впевнені, що хочете перезавантажити комп'ютер?"):
            return ctx.speak("Скасовую")

        ctx.speak("Перезавантажую комп'ютер")
        subprocess.run(["shutdown", "/r", "/t", "5"])
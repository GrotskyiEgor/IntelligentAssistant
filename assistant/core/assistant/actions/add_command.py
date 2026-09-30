from core.models import AppCommand

from ...utils.find_path import find_path
from .base import Action, register
from ..nlp.text import normalize_text


@register
class AddCommand(Action):
    name = "add_command"

    def execute(self, ctx, text, matched):
        ctx.speak("Як називається програма?")
        name = ctx.listen()
        if not name:
            return ctx.speak("Я не почула назву програми")
        name = normalize_text(name)

        ctx.speak(f"Шукаю програму {name}")
        path = find_path(filename=name)
        if not path:
            return ctx.speak(f"Я не знайшла програму {name}")

        ctx.speak(f"Знайшла {name}. Яке ключове слово використовувати для запуску?")
        keyword = ctx.listen()
        if not keyword:
            return ctx.speak("Я не почула ключове слово")

        AppCommand.objects.create(name=name, keyword=normalize_text(keyword), path=path)
        ctx.speak(f"Команду для {name} успішно додано")
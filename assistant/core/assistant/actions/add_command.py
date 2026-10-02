from core.models import AppCommand

from ...utils.find_path import find_path
from .base import Action, register
from ..nlp.dialog import MAX_ATTEMPTS, ask_text, confirm


@register
class AddCommand(Action):
    name = "add_command"

    def execute(self, ctx, text, matched):
        found = self._ask_program(ctx)
        if not found:
            return
        name, path = found

        keyword = ask_text(
            ctx,
            f"Знайшла {name}. Яке ключове слово використовувати для запуску?",
            "Я не почула ключове слово. Повторіть, будь ласка",
        )
        if not keyword:
            return

        if not confirm(ctx, f"Додати команду: програма {name}, ключове слово {keyword}? Скажіть так або ні."):
            return

        AppCommand.objects.create(name=name, keyword=keyword, path=path)
        ctx.speak(f"Команду для {name} успішно додано")

    @staticmethod
    def _ask_program(ctx):
        question = "Як називається програма?"

        for _ in range(MAX_ATTEMPTS):
            name = ask_text(ctx, question, "Я не почула назву програми. Повторіть, будь ласка")
            if not name:
                return None

            ctx.speak(f"Шукаю програму {name}")
            path = find_path(filename=name)
            if path:
                return name, path

            question = f"Я не знайшла програму {name}. Назвіть ще раз або скажіть скасувати"

        ctx.speak("Не вдалося знайти програму, скасовую")
        return None
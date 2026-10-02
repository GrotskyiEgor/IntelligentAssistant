import os

from core.models import AppGroup

from .base import Action, register
from .delete import parse_number
from ..nlp.dialog import MAX_ATTEMPTS, ask_text
from ..nlp.text import normalize_text

GROUP_STEMS = ("груп", "гру")


def _words(text: str) -> list[str]:
    return [w for w in normalize_text(text).split() if not w.startswith(GROUP_STEMS)]

def find_group(query: str):
    words = _words(query)
    if not words:
        return None

    groups = list(AppGroup.objects.order_by("id"))

    number = parse_number(" ".join(words))
    if number is not None:
        for group in groups:
            if str(number) in _words(group.name):
                return group

    query_set = set(words)
    for group in groups:
        name_set = set(_words(group.name))
        if name_set and (name_set <= query_set or query_set <= name_set):
            return group

    return None


@register
class OpenGroup(Action):
    name = "open_group"

    def execute(self, ctx, text, matched):
        query = text.replace(matched, "", 1).strip()
        group = find_group(query) if query else None

        question = "Яку групу відкрити?"
        for _ in range(MAX_ATTEMPTS):
            if group:
                break
            answer = ask_text(ctx, question, "Я не почула назву групи. Повторіть, будь ласка")
            if not answer:
                return
            group = find_group(answer)
            question = "Я не знайшла таку групу. Назвіть ще раз або скажіть скасувати"
        else:
            return ctx.speak("Не вдалося знайти групу, скасовую")

        apps = list(group.apps.all())  # поправь имя связи под свою модель
        if not apps:
            return ctx.speak(f"У групі {group.name} немає програм")

        ctx.speak(f"Відкриваю групу {group.name}")
        for app in apps:
            try:
                os.startfile(app.path)
            except OSError as error:
                print(f"Не вдалося запустити {app.name}: {error}", flush=True)
                ctx.speak(f"Не вдалося запустити {app.name}")
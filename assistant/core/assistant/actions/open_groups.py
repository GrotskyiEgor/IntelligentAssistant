import os

from core.models import AppGroup

from .base import Action, register
from .numbers import parse_number
from ..nlp.dialog import MAX_ATTEMPTS, ask_text
from ..nlp.text import normalize_text

GROUP_STEMS = ("груп", "гру")


def _words(text) -> list[str]:
    return [w for w in normalize_text(text).split() if not w.startswith(GROUP_STEMS)]

def find_group(query):
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
            answer = ask_text(ctx, question, "Не почула назву групи. Повторіть, будь ласка")
            if not answer:
                return
            group = find_group(answer)
            question = "Не знайшла групу. Ще раз?"
        else:
            return ctx.speak("Cкасовую")

        apps = list(group.apps.all())
        if not apps:
            return ctx.speak(f"Група {group.name} порожня")

        ctx.speak(f"Відкриваю {group.name}")
        for app in apps:
            try:
                os.startfile(app.path)
            except OSError as error:
                print(f"Не вдалося запустити {app.name}: {error}", flush=True)
                ctx.speak(f"Не вдалося запустити {app.name}")
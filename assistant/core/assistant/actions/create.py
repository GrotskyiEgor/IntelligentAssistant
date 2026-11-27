import re

from rapidfuzz import fuzz

from core.models import AppCommand, AppGroup, WebSite

from .base import ACTIONS, Action, register
from ..nlp.answers import is_cancel
from ..nlp.dialog import MAX_ATTEMPTS, ask_text, confirm
from ..nlp.text import normalize_text
from ..services.usage import log_action

MAX_CLARIFY = 3
WORD_THRESHOLD = 75

KIND_STEMS = {
    "command": ("команд", "програм", "застосун", "додат"),
    "group": ("груп",),
    "site": ("сайт", "сторін", "веб", "посилан"),
}

URL_RE = re.compile(r"^(https?://)?([\w-]+\.)+[a-z]{2,}(:\d+)?(/\S*)?$", re.IGNORECASE)


def detect_kind(text) -> str | None:
    for word in normalize_text(text).split():
        for kind, stems in KIND_STEMS.items():
            if word.startswith(stems):
                return kind
    return None


def normalize_url(text) -> str | None:
    text = text.strip()
    if " " in text or not URL_RE.match(text):
        return None
    if text.lower().startswith(("http://", "https://")):
        return text
    return f"https://{text}"


def _position(key, words) -> int | None:
    """Позиція слова в тексті, де вимовлено всі слова ключа; None, якщо не знайдено."""
    positions = []
    for key_word in normalize_text(key).split():
        scores = [fuzz.ratio(key_word, word) for word in words]
        if not scores or max(scores) < WORD_THRESHOLD:
            return None
        positions.append(scores.index(max(scores)))
    return min(positions) if positions else None


def find_apps(text, apps) -> list:
    words = [w.strip(".,!?:;") for w in normalize_text(text.replace(",", " ")).split()]
    found = []

    for app in apps:
        positions = [p for p in (_position(app.keyword, words), _position(app.name, words)) if p is not None]
        if positions:
            found.append((min(positions), app))

    found.sort(key=lambda pair: pair[0])
    return [app for _, app in found]


@register
class Create(Action):
    name = "create"

    def execute(self, ctx, text, matched):
        kind = detect_kind(text.replace(matched, "", 1))

        if not kind:
            answer = ask_text(
                ctx,
                "Що створити: команду, групу чи сайт?",
                "Не почула. Команду, групу чи сайт?",
            )
            if not answer:
                return
            kind = detect_kind(answer)
            if not kind:
                return ctx.speak("Не зрозуміла")

        if kind == "command":
            return ACTIONS["add_command"].execute(ctx, text, matched)
        if kind == "site":
            return self.create_site(ctx)
        return self.create_group(ctx)

    @staticmethod
    def create_site(ctx):
        ctx.speak("Скиньте посилання на сайт у чат")
        url = None

        for _ in range(MAX_ATTEMPTS):
            answer = ctx.listen()
            if not answer:
                continue
            if is_cancel(answer):
                return ctx.speak("Скасовано")

            url = normalize_url(answer)
            if url:
                break
            ctx.speak("Це не схоже на посилання. Скиньте ще раз")

        if not url:
            return ctx.speak("Не дочекалась посилання. Скасовую")

        name = ask_text(ctx, "Як назвати сайт?", "Не почула назву. Повторіть")
        if not name:
            return
        if not confirm(ctx, f"Додати сайт {name}?"):
            return

        WebSite.objects.create(url=url, name=name)
        log_action("create", f"site: {name}")
        ctx.speak("Сайт додано")

    @classmethod
    def create_group(cls, ctx):
        apps = cls._ask_apps(ctx)
        if not apps:
            return

        name = ask_text(ctx, "Як назвати групу?", "Не почула назву. Повторіть")
        if not name:
            return

        names = ", ".join(app.name for app in apps)
        if not confirm(ctx, f"Створити групу {name} з програм: {names}?"):
            return

        group = AppGroup.objects.create(name=name)
        group.apps.set(apps)
        log_action("create", f"group: {name}")
        ctx.speak("Групу створено")

    @staticmethod
    def _ask_apps(ctx):
        question = "Назвіть ключові слова програм для групи"

        for _ in range(MAX_CLARIFY):
            answer = ask_text(ctx, question, "Не почула. Назвіть ключові слова")
            if not answer:
                return None

            apps = find_apps(answer, list(AppCommand.objects.all()))
            if not apps:
                question = "Не знайшла жодної програми. Ще раз?"
                continue

            names = ", ".join(app.name for app in apps)
            if confirm(ctx, f"Знайшла: {names}. Вірно?"):
                return apps
            question = "Назвіть ключові слова ще раз"

        ctx.speak("Скасовую")
        return None

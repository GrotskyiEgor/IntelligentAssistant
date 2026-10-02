import re

from core.models import AppCommand, AppGroup, WebSite

from .base import Action, register
from ..nlp.answers import is_cancel, is_no, is_yes
from ..nlp.text import normalize_text

MAX_ATTEMPTS = 5

CATEGORIES = {
    "group": {
        "stems": ("груп",),
        "title": "групу",
        "model": AppGroup,
        "label": lambda o: o.name,
    },
    "app": {
        "stems": ("команд", "програм", "додат", "застосун"),
        "title": "команду",
        "model": AppCommand,
        "label": lambda o: f"{o.name}, ключове слово {o.keyword}",
    },
    "site": {
        "stems": ("сайт", "веб"),
        "title": "сайт",
        "model": WebSite,
        "label": lambda o: o.name,
    },
}

CANCEL_STEMS = ("скасув", "відмін", "відбій", "не треба", "передумав", "стоп")

CARDINALS = {
    "один": 1, "одна": 1, "одну": 1, "два": 2, "дві": 2, "три": 3,
    "чотири": 4, "п'ять": 5, "шість": 6, "сім": 7, "вісім": 8,
    "дев'ять": 9, "десять": 10, "одинадцять": 11, "дванадцять": 12,
    "тринадцять": 13, "чотирнадцять": 14, "п'ятнадцять": 15,
    "шістнадцять": 16, "сімнадцять": 17, "вісімнадцять": 18,
    "дев'ятнадцять": 19, "двадцять": 20,
}

ORDINAL_STEMS = {
    "перш": 1, "друг": 2, "трет": 3, "четвер": 4, "п'ят": 5,
    "шост": 6, "сьом": 7, "восьм": 8, "дев'ят": 9, "десят": 10,
}


def _clean(text: str) -> str:
    return normalize_text(text.replace("’", "'").replace("ʼ", "'"))


def parse_number(text: str) -> int | None:
    text = _clean(text)
    digits = re.search(r"\d+", text)

    if digits:
        return int(digits.group())
    
    for word in text.split():
        word = word.strip(".,!?")
        if word in CARDINALS:
            return CARDINALS[word]
        for stem, number in ORDINAL_STEMS.items():
            if word.startswith(stem):
                return number
            
    return None


def is_cancel(text: str) -> bool:
    text = _clean(text)
    return any(stem in text for stem in CANCEL_STEMS)


def detect_category(text: str) -> str | None:
    for word in _clean(text).split():
        for key, cfg in CATEGORIES.items():
            if word.startswith(cfg["stems"]):
                return key
    return None


@register
class DeleteItem(Action):
    name = "delete"

    def execute(self, ctx, text, matched):
        category = detect_category(text.replace(matched, "", 1))

        if not category:
            ctx.speak("Що видалити: групу, команду чи сайт?")
            answer = ctx.listen()
            if not answer:
                return ctx.speak("Я не почула відповідь")
            if is_cancel(answer):
                return ctx.speak("Гаразд, скасовано")
            category = detect_category(answer)
            if not category:
                return ctx.speak("Я не зрозуміла, що саме видаляти")

        cfg = CATEGORIES[category]
        items = list(cfg["model"].objects.order_by("id"))
        if not items:
            return ctx.speak(f"Немає жодного запису, щоб видалити {cfg['title']}")

        # список только показываем, не озвучиваем
        for index, item in enumerate(items, start=1):
            print(f"ANSWER: {index}. {cfg['label'](item)}", flush=True)
        ctx.speak("Ось список. Назвіть номер, який видалити, або скажіть скасувати.")

        number = self._ask_number(ctx, len(items))
        if number is None:
            return

        item = items[number - 1]
        label = cfg["label"](item)

        if not self._confirm(ctx, number, label):
            return

        item.delete()
        ctx.speak(f"Видалила {number}. {label}")

    @staticmethod
    def _ask_number(ctx, count: int) -> int | None:
        for _ in range(MAX_ATTEMPTS):
            answer = ctx.listen()

            if not answer:
                ctx.speak(f"Я не почула. Назвіть номер від 1 до {count}")
                continue

            if is_cancel(answer):
                ctx.speak("Гаразд, скасовано")
                return None

            number = parse_number(answer)
            if number is not None and 1 <= number <= count:
                return number

            ctx.speak(f"Я не зрозуміла номер. Назвіть число від 1 до {count}")

        ctx.speak("Не вдалося визначити номер, скасовую")
        return None

    @staticmethod
    def _confirm(ctx, number: int, label: str) -> bool:
        ctx.speak(f"Видалити {number}. {label}? Скажіть так або ні.")

        for _ in range(MAX_ATTEMPTS):
            answer = ctx.listen()

            if not answer:
                ctx.speak("Я не почула. Видалити? Скажіть так або ні")
                continue

            if is_cancel(answer) or is_no(answer):
                ctx.speak("Гаразд, скасовано")
                return False

            if is_yes(answer):
                return True

            ctx.speak("Я не зрозуміла. Скажіть так або ні")

        ctx.speak("Відповіді немає, скасовую")
        return False
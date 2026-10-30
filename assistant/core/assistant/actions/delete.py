from rapidfuzz import fuzz

from core.models import AppCommand, AppGroup, WebSite

from .base import Action, register
from ..nlp.answers import is_cancel
from ..nlp.dialog import MAX_ATTEMPTS, confirm
from ..nlp.text import normalize_text

MATCH_THRESHOLD = 70
AMBIGUITY_GAP = 5
 
FILLER_WORDS = {
    "з", "із", "за", "по", "під", "будь", "ласка", "мені",
    "ключовим", "ключове", "словом", "слово", "назвою", "назва",
}
 
CATEGORIES = {
    "group": {
        "stems": ("груп",),
        "title": "групу",
        "model": AppGroup,
        "keys": lambda o: [o.name],
        "label": lambda o: o.name,
    },
    "app": {
        "stems": ("команд", "програм", "додат", "застосун"),
        "title": "команду",
        "model": AppCommand,
        "keys": lambda o: [o.name, o.keyword],
        "label": lambda o: f"{o.name}, ключове слово {o.keyword}",
    },
    "site": {
        "stems": ("сайт", "веб"),
        "title": "сайт",
        "model": WebSite,
        "keys": lambda o: [o.name],
        "label": lambda o: o.name,
    },
}
 
 
def _clean(text) -> str:
    return normalize_text(text.replace("’", "'").replace("ʼ", "'"))
 
 
def detect_category(text) -> str | None:
    for word in _clean(text).split():
        for key, cfg in CATEGORIES.items():
            if word.startswith(cfg["stems"]):
                return key
            
    return None
 
 
def extract_query(text) -> str:
    stems = tuple(stem for cfg in CATEGORIES.values() for stem in cfg["stems"])
    words = []
    for word in _clean(text).split():
        word = word.strip(".,!?:;")
        if not word or word in FILLER_WORDS or word.startswith(stems):
            continue
        words.append(word)
    return " ".join(words)
 
 
@register
class DeleteItem(Action):
    name = "delete"

    def execute(self, ctx, text, matched):
        rest = text.replace(matched, "", 1)
        category = detect_category(rest)

        if not category:
            ctx.speak("Що видалити: групу, команду чи сайт?")
            answer = ctx.listen()

            if not answer:
                return ctx.speak("Не почула")
            if is_cancel(answer):
                return ctx.speak("Скасовано")

            category = detect_category(answer)
            if not category:
                return ctx.speak("Не зрозуміла")
            rest = answer

        cfg = CATEGORIES[category]
        items = list(cfg["model"].objects.order_by("id"))
        if not items:
            return ctx.speak(f"Список порожній")

        item = self._choose(ctx, items, cfg, first_query=extract_query(rest))
        if item is None:
            return

        label = cfg["label"](item)
        if not confirm(ctx, f"Видалити {label}?"):
            return

        item.delete()
        ctx.speak(f"Видалила")

    def _choose(self, ctx, items, cfg, first_query: str = ""):
        query = first_query

        for _ in range(MAX_ATTEMPTS):
            if not query:
                ctx.speak(f"Що саме видалити?")
                answer = ctx.listen()

                if not answer:
                    ctx.speak("Не почула.")
                    continue
                if is_cancel(answer):
                    ctx.speak("Скасовано")
                    return None

                query = extract_query(answer)
                if not query:
                    ctx.speak("Не зрозуміла.")
                    continue

            item, close = self._find(items, query, cfg)
            if item is not None:
                return item

            if close:
                names = ", ".join(cfg["label"](i) for i in close[:3])
                ctx.speak(f"Схожих кілька: {names}. Уточніть")
            else:
                ctx.speak(f"Не знайшла {query}. Ще раз?")
            query = ""

        ctx.speak("Cкасовую")
        return None

    @staticmethod
    def _score(q: str, keys) -> int:
        best = 0
        for key in keys:
            ratio = fuzz.ratio(q, key)
            if ratio == 100:
                return 120
            best = max(best, ratio, fuzz.token_set_ratio(q, key))
        return best

    @classmethod
    def _find(cls, items, query: str, cfg):
        q = _clean(query)
        scored = []

        for item in items:
            keys = [_clean(k) for k in cfg["keys"](item) if k]
            scored.append((cls._score(q, keys), item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        best_score, best = scored[0]

        if best_score < MATCH_THRESHOLD:
            return None, []

        close = [i for s, i in scored if best_score - s < AMBIGUITY_GAP]
        if len(close) > 1:
            return None, close

        return best, []
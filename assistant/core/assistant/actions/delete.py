from rapidfuzz import fuzz
 
from core.models import AppCommand, AppGroup, WebSite
 
from .base import Action, register
from ..nlp.answers import is_cancel, is_no, is_yes
from ..nlp.text import normalize_text
 
MAX_ATTEMPTS = 5
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
 
 
def _clean(text: str) -> str:
    return normalize_text(text.replace("’", "'").replace("ʼ", "'"))
 
 
def detect_category(text: str) -> str | None:
    for word in _clean(text).split():
        for key, cfg in CATEGORIES.items():
            if word.startswith(cfg["stems"]):
                return key
            
    return None
 
 
def extract_query(text: str) -> str:
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
                return ctx.speak("Я не почула відповідь")
            
            if is_cancel(answer):
                return ctx.speak("Гаразд, скасовано")
            category = detect_category(answer)

            if not category:
                return ctx.speak("Я не зрозуміла, що саме видаляти")
            
            rest = answer
 
        cfg = CATEGORIES[category]
        items = list(cfg["model"].objects.order_by("id"))
        if not items:

            return ctx.speak(f"Немає жодного запису, щоб видалити {cfg['title']}")
 
        item = None
        query = extract_query(rest)

        if query:
            item, _ = self._find(items, query, cfg)

            if item is None:
                ctx.speak(f"Не знайшла {query}")
 
        if item is None:
            item = self._choose(ctx, items, cfg)

            if item is None:
                return
 
        label = cfg["label"](item)

        if not self._confirm(ctx, label):
            return
 
        item.delete()
        ctx.speak(f"Видалила {label}")
 
    @staticmethod
    def _find(items, query: str, cfg):
        """Повертає (запис, неоднозначно). Запис None, якщо нічого не підійшло."""
        q = _clean(query)
        scored = []

        for item in items:
            keys = [_clean(k) for k in cfg["keys"](item) if k]
            score = max(
                (max(fuzz.ratio(q, k), fuzz.token_set_ratio(q, k)) for k in keys),
                default=0,
            )
            scored.append((score, item))
 
        scored.sort(key=lambda pair: pair[0], reverse=True)
        best_score, best = scored[0]
 
        if best_score < MATCH_THRESHOLD:
            return None, False
        
        if best_score < 100 and len(scored) > 1 and best_score - scored[1][0] < AMBIGUITY_GAP:
            return None, True
        
        return best, False
 
    def _choose(self, ctx, items, cfg):
        for index, item in enumerate(items, start=1):
            print(f"ANSWER: {index}. {cfg['label'](item)}", flush=True)

        ctx.speak("Ось список. Назвіть, що видалити, або скажіть скасувати.")
 
        for _ in range(MAX_ATTEMPTS):
            answer = ctx.listen()
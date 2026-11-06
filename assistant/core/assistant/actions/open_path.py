from pathlib import Path

from .base import Action, register
from ..nlp.dialog import MAX_ATTEMPTS, ask_text
from ..nlp.text import normalize_text
from ..services import files, precesses
from ..services.usage import log_action

VERB_STEMS = ("відкр", "відчин", "запуск", "запуст", "покаж", "увімк", "розкр", "старт")
FILLER_WORDS = {
    "з", "із", "за", "по", "під", "будь", "ласка", "мені", "назвою", "назва",
    "називається", "яка", "який", "яку", "що", "мою", "мій", "моє",
}

TRAILING_WORDS = {"будь", "ласка", "будь-ласка", "пожалуйста"}
ORDINALS = ("перший", "другий", "третій")
MAX_CLARIFY = 3

_CANCELLED = object()


def extract_query(text, matched, nouns):
    """Лишає тільки назву: прибирає команду, слово «папку»/«файл» і службові слова."""
    if matched and matched in text:
        text = text.replace(matched, "", 1)

    words = [w.strip(" .,!?:;\"'«»") for w in normalize_text(text).split()]
    words = [w for w in words if w]

    while words and (words[0] in FILLER_WORDS or words[0] in nouns or words[0].startswith(VERB_STEMS)):
        words.pop(0)
    while words and words[-1] in TRAILING_WORDS:
        words.pop()

    return " ".join(words)


class _OpenPath(Action):
    want_dirs: bool
    nouns: set
    noun_acc: str
    question: str
    retry: str

    def execute(self, ctx, text, matched):
        query = extract_query(text, matched, self.nouns)
        question = self.question

        for _ in range(MAX_ATTEMPTS):
            if not query:
                answer = ask_text(ctx, question, self.retry)
                if not answer:
                    return
                query = extract_query(answer, "", self.nouns)
                if not query:
                    continue

            target = self.resolve(ctx, query)
            if target is _CANCELLED:
                return
            if target:
                return self.open_target(ctx, target, text)

            question = f"Не знайшла {self.noun_acc} {query}. Ще раз?"
            query = ""

        ctx.speak("Скасовую")

    def resolve(self, ctx, query):
        if self.want_dirs:
            known = files.known_folder(query)
            if known:
                return known

        ctx.speak(f"Шукаю {query}")
        match, options = files.search_and_pick(query, self.want_dirs)

        if match:
            return match.path
        if options:
            return self.clarify(ctx, options)
        return None

    def clarify(self, ctx, options):
        listing = ". ".join(
            f"{ORDINALS[i].capitalize()} — {self.label(m.path, with_parent=True)}"
            for i, m in enumerate(options)
        )
        question = f"Знайшла кілька. {listing}. Яку відкрити?"

        for _ in range(MAX_CLARIFY):
            answer = ask_text(ctx, question, "Не почула. Назвіть номер")
            if not answer:
                return _CANCELLED

            choice = files.narrow(options, answer)
            if choice:
                return choice.path
            question = "Не зрозуміла. Назвіть номер"

        ctx.speak("Скасовую")
        return _CANCELLED

    def open_target(self, ctx, path, text):
        label = self.label(path)
        ctx.speak(f"Відкриваю {self.noun_acc} {label}")
        try:
            precesses.open_path(path)
            log_action(self.name, text)
        except Exception as error:
            print(f"Помилка відкриття: {error}", flush=True)
            ctx.speak(f"Не вдалося відкрити {label}")

    @staticmethod
    def label(path: Path, with_parent=False):
        name = path.name if path.is_dir() else path.stem
        if with_parent and path.parent.name:
            return f"{name}, у {path.parent.name}"
        return name


@register
class OpenFolder(_OpenPath):
    name = "open_folder"
    want_dirs = True
    nouns = {"папку", "папка", "папки", "теку", "тека", "каталог", "директорію", "директорія"}
    noun_acc = "папку"
    question = "Яку папку відкрити?"
    retry = "Не почула назву папки. Повторіть, будь ласка"


@register
class OpenFile(_OpenPath):
    name = "open_file"
    want_dirs = False
    nouns = {"файл", "файли", "файлу", "документ", "документа"}
    noun_acc = "файл"
    question = "Який файл відкрити?"
    retry = "Не почула назву файлу. Повторіть, будь ласка"
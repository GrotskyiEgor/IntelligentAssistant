import subprocess
from pathlib import Path

from .base import Action, register
from .file import narrow, pick, search
from ..nlp.dialog import MAX_ATTEMPTS, ask_text
from ..nlp.text import normalize_text
from ..services.usage import log_action

VERB_STEMS = ("знайд", "знайт", "найд", "найт", "пошук", "шука")
FILLER_WORDS = {
    "з", "із", "за", "по", "під", "будь", "ласка", "мені", "назвою", "назва",
    "називається", "яка", "який", "яку", "що", "мою", "мій", "моє", "де",
}
TRAILING_WORDS = {"будь", "ласка", "будь-ласка", "пожалуйста"}

ORDINALS = ("Перший", "Другий", "Третій")
MAX_CLARIFY = 3

_CANCELLED = object()


def extract_query(text, matched, nouns):
    """Лишає тільки назву: прибирає команду, слово «файл»/«папку» і службові слова."""
    if matched and matched in text:
        text = text.replace(matched, "", 1)

    words = [w.strip(" .,!?:;\"'«»") for w in normalize_text(text).split()]
    words = [w for w in words if w]

    while words and (
        words[0] in FILLER_WORDS
        or words[0] in nouns
        or words[0].startswith(VERB_STEMS)
    ):
        words.pop(0)
    while words and words[-1] in TRAILING_WORDS:
        words.pop()

    return " ".join(words)


def reveal_in_explorer(path):
    """Відкриває Провідник Windows і виділяє знайдений файл/папку."""
    subprocess.Popen(["explorer", f"/select,{path}"])


def _label(path: Path, with_parent=False):
    name = path.name if path.is_dir() else path.stem
    if with_parent and path.parent.name:
        return f"{name}, у {path.parent.name}"
    return name


class _FindPath(Action):
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

            ctx.speak(f"Шукаю {query}")
            matches = search(query, self.want_dirs)

            if not matches:
                question = f"Не знайшла {self.noun_acc} {query}. Ще раз?"
                query = ""
                continue

            target = self.choose(ctx, matches)
            if target is _CANCELLED:
                return

            return self.show(ctx, target, text)

        ctx.speak("Скасовую")

    def choose(self, ctx, matches):
        match, options = pick(matches)
        if match:
            return match.path
        return self.clarify(ctx, options, total=len(matches))

    def clarify(self, ctx, options, total):
        listing = ". ".join(
            f"{ORDINALS[i]} — {_label(m.path, with_parent=True)}"
            for i, m in enumerate(options)
        )
        question = f"Знайшла {total}. {listing}. Який показати?"

        for _ in range(MAX_CLARIFY):
            answer = ask_text(ctx, question, "Не почула. Назвіть номер")
            if not answer:
                return _CANCELLED

            choice = narrow(options, answer)
            if choice:
                return choice.path
            question = "Не зрозуміла. Назвіть номер"

        ctx.speak("Скасовую")
        return _CANCELLED

    def show(self, ctx, path, text):
        ctx.speak(f"Знайшла {self.noun_acc} {_label(path, with_parent=True)}")
        try:
            reveal_in_explorer(path)
            log_action(self.name, text)
        except Exception as error:
            print(f"Помилка показу: {error}", flush=True)
            ctx.speak("Не вдалося відкрити Провідник")


@register
class FindFolder(_FindPath):
    name = "find_folder"
    want_dirs = True
    nouns = {"папку", "папка", "папки", "теку", "тека", "каталог", "директорію", "директорія"}
    noun_acc = "папку"
    question = "Яку папку знайти?"
    retry = "Не почула назву папки. Повторіть, будь ласка"


@register
class FindFile(_FindPath):
    name = "find_file"
    want_dirs = False
    nouns = {"файл", "файли", "файлу", "документ", "документа"}
    noun_acc = "файл"
    question = "Який файл знайти?"
    retry = "Не почула назву файлу. Повторіть, будь ласка"

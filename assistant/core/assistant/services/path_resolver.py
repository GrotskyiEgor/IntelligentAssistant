"""Спільні помічники для команд з файлами й папками: пошук цілі голосом,
уточнення, якщо знайдено кілька варіантів, і захист системних шляхів."""
import os
from pathlib import Path

from ..nlp.dialog import MAX_ATTEMPTS, ask_text
from ..nlp.text import normalize_text
from . import files

CANCELLED = object()
MAX_CLARIFY = 3
ORDINALS = ("перший", "другий", "третій")

FILLER_WORDS = {
    "з", "із", "за", "по", "під", "будь", "ласка", "мені", "назвою", "назва",
    "називається", "яка", "який", "яку", "що", "мою", "мій", "моє",
}
TRAILING_WORDS = {"будь", "ласка", "будь-ласка", "пожалуйста"}

FILE_NOUNS = {"файл", "файли", "файлу", "документ", "документа"}
FOLDER_NOUNS = {"папку", "папка", "папки", "теку", "тека", "каталог", "директорію", "директорія"}


def extract_query(text, matched, nouns, verb_stems, extra_fillers=()):
    """Лишає тільки назву: прибирає команду, слово «папку»/«файл» і службові слова."""
    if matched and matched in text:
        text = text.replace(matched, "", 1)

    fillers = FILLER_WORDS | set(extra_fillers)
    words = [w.strip(" .,!?:;\"'«»") for w in normalize_text(text).split()]
    words = [w for w in words if w]

    while words and (words[0] in fillers or words[0] in nouns or words[0].startswith(verb_stems)):
        words.pop(0)
    while words and words[-1] in TRAILING_WORDS:
        words.pop()
    return " ".join(words)


def label(path: Path, with_parent=False):
    name = path.name if path.is_dir() else path.stem
    if with_parent and path.parent.name:
        return f"{name}, у {path.parent.name}"
    return name


def _clarify(ctx, options, noun_acc):
    listing = ". ".join(
        f"{ORDINALS[i].capitalize()} — {label(m.path, with_parent=True)}"
        for i, m in enumerate(options)
    )
    question = f"Знайшла кілька. {listing}. Яку вибрати?"

    for _ in range(MAX_CLARIFY):
        answer = ask_text(ctx, question, "Не почула. Назвіть номер")
        if not answer:
            return CANCELLED
        choice = files.narrow(options, answer)
        if choice:
            return choice.path
        question = "Не зрозуміла. Назвіть номер"

    ctx.speak("Скасовую")
    return CANCELLED


def resolve_path(ctx, query, want_dirs, noun_acc, allow_known=True):
    """Path | None (не знайдено) | CANCELLED (користувач скасував)."""
    if want_dirs and allow_known:
        known = files.known_folder(query)
        if known:
            return known

    ctx.speak(f"Шукаю {query}")
    match, options = files.search_and_pick(query, want_dirs)
    if match:
        return match.path
    if options:
        return _clarify(ctx, options, noun_acc)
    return None


def ask_and_resolve(ctx, query, want_dirs, noun_acc, question, retry, cleaner, allow_known=True):
    """Знаходить файл/папку: бере query, а якщо порожній чи не знайдено — перепитує.
    Повертає Path або None (скасовано / не знайшла після спроб)."""
    for _ in range(MAX_ATTEMPTS):
        if not query:
            answer = ask_text(ctx, question, retry)
            if not answer:
                return None
            query = cleaner(answer)
            if not query:
                continue

        target = resolve_path(ctx, query, want_dirs, noun_acc, allow_known)
        if target is CANCELLED:
            return None
        if target:
            return target

        question = f"Не знайшла {noun_acc} {query}. Ще раз?"
        query = ""

    ctx.speak("Скасовую")
    return None


def _inside(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def is_protected(path: Path) -> bool:
    """Системні й «кореневі» шляхи, які не можна видаляти чи переносити."""
    try:
        p = path.resolve()
    except OSError:
        p = path

    home = Path.home().resolve()
    exact = {home, home.parent, Path(p.anchor)}
    for folder in files._user_dirs():
        exact.add(folder.resolve())
    if p in exact:
        return True

    system_dirs = [os.environ.get(v) for v in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramData")]
    return any(_inside(p, Path(d)) for d in system_dirs if d)

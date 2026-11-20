import shutil

from .base import Action, register
from ..nlp.dialog import ask_text, confirm
from ..nlp.text import normalize_text
from ..services.path_resolver import (
    FILE_NOUNS, FOLDER_NOUNS, ask_and_resolve, extract_query, is_protected, label, _inside,
)
from ..services.usage import log_action

VERB_STEMS = ("перен", "перем", "перекин")
PREPOSITIONS = {"в", "у", "до", "на"}
FILE_STEMS = ("файл", "документ")
FOLDER_STEMS = ("папк", "тек", "каталог", "директор")
ALL_NOUNS = FILE_NOUNS | FOLDER_NOUNS


def _kind(text):
    """'file' | 'dir' | None за словами-підказками."""
    for word in normalize_text(text).split():
        if word.startswith(FILE_STEMS):
            return "file"
        if word.startswith(FOLDER_STEMS):
            return "dir"
    return None


def _split(rest):
    """«звіт в документи» -> («звіт», «документи»). Розділяє по першому прийменнику."""
    words = normalize_text(rest).split()
    for i, word in enumerate(words):
        if i > 0 and word in PREPOSITIONS:
            return " ".join(words[:i]), " ".join(words[i + 1:])
    return " ".join(words), ""


@register
class MovePath(Action):
    name = "move"

    def execute(self, ctx, text, matched):
        rest = text.replace(matched, "", 1) if matched in text else text
        source_part, dest_part = _split(rest)

        kind = _kind(f"{matched} {source_part}")
        if kind is None:
            answer = ask_text(ctx, "Що перенести: файл чи папку?", "Не почула. Файл чи папку?")
            if not answer:
                return
            kind = _kind(answer)
            if kind is None:
                return ctx.speak("Не зрозуміла")

        want_dirs = kind == "dir"
        noun = "папку" if want_dirs else "файл"

        source_query = extract_query(source_part, "", ALL_NOUNS, VERB_STEMS)
        src = ask_and_resolve(
            ctx, source_query, want_dirs, noun,
            question=f"Яку {noun} перенести?" if want_dirs else "Який файл перенести?",
            retry="Не почула назву. Повторіть, будь ласка",
            cleaner=lambda t: extract_query(t, "", ALL_NOUNS, VERB_STEMS),
            allow_known=False,
        )
        if not src:
            return

        dest_clean = lambda t: extract_query(t, "", FOLDER_NOUNS, (), extra_fillers=PREPOSITIONS)
        dst = ask_and_resolve(
            ctx, dest_clean(dest_part), True, "папку",
            question="У яку папку перенести?",
            retry="Не почула назву папки. Повторіть, будь ласка",
            cleaner=dest_clean,
        )
        if not dst:
            return

        problem = self._check(src, dst)
        if problem:
            return ctx.speak(problem)

        if not confirm(ctx, f"Перенести {noun} {label(src)} у папку {label(dst)}?"):
            return

        try:
            shutil.move(str(src), str(dst))
        except Exception as error:
            print(f"Помилка переносу: {error}", flush=True)
            return ctx.speak("Не вдалося перенести")

        log_action(self.name, f"{src} -> {dst}")
        ctx.speak("Перенесла")

    @staticmethod
    def _check(src, dst):
        if not dst.is_dir():
            return "Це не папка"
        if is_protected(src):
            return "Цю папку переносити не можна"
        if src.parent.resolve() == dst.resolve():
            return "Він уже в цій папці"
        if src.is_dir() and (src.resolve() == dst.resolve() or _inside(dst.resolve(), src.resolve())):
            return "Не можна перенести папку саму в себе"
        if (dst / src.name).exists():
            return "У цій папці вже є така назва"
        return None

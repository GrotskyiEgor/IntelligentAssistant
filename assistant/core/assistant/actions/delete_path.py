import os

from .base import Action, register
from ..nlp.dialog import confirm
from ..services.path_resolver import (
    FILE_NOUNS, FOLDER_NOUNS, ask_and_resolve, extract_query, is_protected, label,
)
from ..services.usage import log_action

VERB_STEMS = ("видал", "стер", "зітр", "зітри", "прибер", "знищ")
COUNT_LIMIT = 1000


def _count_items(path) -> int:
    total = 0
    for _, dirs, names in os.walk(path):
        total += len(dirs) + len(names)
        if total >= COUNT_LIMIT:
            break
    return total


def _move_to_trash(path):
    from send2trash import send2trash  # pip install send2trash
    send2trash(str(path))


class _DeletePath(Action):
    want_dirs: bool
    nouns: set
    noun_acc: str
    question: str
    retry: str

    def execute(self, ctx, text, matched):
        query = extract_query(text, matched, self.nouns, VERB_STEMS)
        target = ask_and_resolve(
            ctx, query, self.want_dirs, self.noun_acc, self.question, self.retry,
            cleaner=lambda t: extract_query(t, "", self.nouns, VERB_STEMS),
            allow_known=False,
        )
        if not target:
            return

        if is_protected(target):
            return ctx.speak("Цю папку видаляти не можна")

        question = f"Видалити {self.noun_acc} {label(target, with_parent=True)}?"
        if self.want_dirs:
            count = _count_items(target)
            if count:
                shown = f"понад {COUNT_LIMIT}" if count >= COUNT_LIMIT else count
                question = f"{question} Усередині елементів: {shown}"

        if not confirm(ctx, question):
            return

        try:
            _move_to_trash(target)
        except ImportError:
            return ctx.speak("Не встановлено send2trash. Видалення вимкнено")
        except Exception as error:
            print(f"Помилка видалення: {error}", flush=True)
            return ctx.speak("Не вдалося видалити")

        log_action(self.name, str(target))
        ctx.speak("Перемістила в кошик")


@register
class DeleteFolder(_DeletePath):
    name = "delete_folder"
    want_dirs = True
    nouns = FOLDER_NOUNS
    noun_acc = "папку"
    question = "Яку папку видалити?"
    retry = "Не почула назву папки. Повторіть, будь ласка"


@register
class DeleteFile(_DeletePath):
    name = "delete_file"
    want_dirs = False
    nouns = FILE_NOUNS
    noun_acc = "файл"
    question = "Який файл видалити?"
    retry = "Не почула назву файлу. Повторіть, будь ласка"

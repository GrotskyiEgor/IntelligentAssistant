from rapidfuzz import fuzz
from core.models import AppCommand
from ..nlp.text import normalize_text
from ..config import APP_THRESHOLD


def find_app(text: str):
    text = normalize_text(text)
    best, best_score = None, 0

    for command in AppCommand.objects.all():
        keyword = normalize_text(command.keyword)
        name = normalize_text(command.name)
        score = max(
            fuzz.ratio(text, keyword),
            fuzz.ratio(text, name),
            fuzz.token_set_ratio(text, keyword),
        )
        if score > best_score:
            best, best_score = command, score

    return best if best_score >= APP_THRESHOLD else None
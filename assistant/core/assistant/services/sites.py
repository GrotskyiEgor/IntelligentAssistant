from core.models import WebSite

from ..nlp.text import normalize_text

NOISE_WORDS = {"сайт", "сторінку", "сторінка", "веб"}


def _words(text: str) -> set[str]:
    return {w for w in normalize_text(text).split() if w not in NOISE_WORDS}


def find_site(query: str):
    query_words = _words(query)
    if not query_words:
        return None

    sites = list(WebSite.objects.order_by("id"))

    for site in sites:
        if _words(site.name) == query_words:
            return site

    for site in sites:
        name_words = _words(site.name)
        if name_words and (name_words <= query_words or query_words <= name_words):
            return site

    return None
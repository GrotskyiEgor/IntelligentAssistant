from core.models import WebSite

from ..nlp.text import normalize_text

NOISE_WORDS = {"сайт", "сторінку", "сторінка", "веб"}


def _words(text) -> set[str]:
    return {w for w in normalize_text(text).split() if w not in NOISE_WORDS}


def site_words(text) -> set[str]:
    """Слова запиту без службових (сайт, сторінка...)."""
    return _words(text)


def has_site_word(text) -> bool:
    """Чи сказали саме "сайт" / "сторінку" у запиті."""
    return any(word in NOISE_WORDS for word in normalize_text(text).split())


def is_exact_site(site, query) -> bool:
    return bool(site) and _words(site.name) == _words(query)


def find_site(query):
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
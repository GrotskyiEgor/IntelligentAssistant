import re
 
from .phrases import store
from .text import normalize_text
 
 
def _padded(text) :
    text = normalize_text(text.replace("’", "'").replace("ʼ", "'"))
    text = re.sub(r"[^\w' ]+", " ", text)
    return f" {' '.join(text.split())} "
 
 
def _contains(text, kind) -> bool:
    store.refresh()
    padded = _padded(text)
    return any(f" {phrase} " in padded for phrase in store.answers(kind))
 
 
def is_no(text) -> bool:
    return _contains(text, "no")
 
 
def is_cancel(text) -> bool:
    return _contains(text, "cancel")
 
 
def is_yes(text) -> bool:
    return not is_no(text) and _contains(text, "yes")
 
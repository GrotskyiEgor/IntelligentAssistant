from rapidfuzz import fuzz
 
from ..config import ASSISTANT_NAMES, NAME_THRESHOLD
 
 
def find_name(text: str) -> str | None:
    words = text.split()
    if not words:
        return None
 
    first = words[0].strip(".,!?:;-—")
    if not first:
        return None
 
    for name in ASSISTANT_NAMES:
        if fuzz.ratio(first, name) >= NAME_THRESHOLD:
            return words[0]
    return None
 
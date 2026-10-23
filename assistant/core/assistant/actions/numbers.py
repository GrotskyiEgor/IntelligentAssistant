import re
 
from ..nlp.text import normalize_text
 
UNITS = {
    "нуль": 0, "один": 1, "одна": 1, "одну": 1, "раз": 1, "два": 2, "дві": 2,
    "три": 3, "чотири": 4, "п'ять": 5, "шість": 6, "сім": 7, "вісім": 8,
    "дев'ять": 9, "десять": 10, "одинадцять": 11, "дванадцять": 12,
    "тринадцять": 13, "чотирнадцять": 14, "п'ятнадцять": 15,
    "шістнадцять": 16, "сімнадцять": 17, "вісімнадцять": 18,
    "дев'ятнадцять": 19,
}
 
TENS = {
    "двадцять": 20, "тридцять": 30, "сорок": 40, "п'ятдесят": 50,
    "шістдесят": 60, "сімдесят": 70, "вісімдесят": 80, "дев'яносто": 90,
}
 
ORDINAL_STEMS = {
    "перш": 1, "друг": 2, "трет": 3, "четвер": 4, "п'ят": 5,
    "шост": 6, "сьом": 7, "восьм": 8, "дев'ят": 9, "десят": 10,
}
ORDINAL_MAX_SUFFIX = 4
 
 
def _clean(text) :
    return normalize_text(text.replace("’", "'").replace("ʼ", "'"))
 
 
def _word_value(word) -> int | None:
    if word in UNITS:
        return UNITS[word]
    if word in TENS:
        return TENS[word]
    for stem, number in ORDINAL_STEMS.items():
        if word.startswith(stem) and len(word) <= len(stem) + ORDINAL_MAX_SUFFIX:
            return number
    return None
 
 
def parse_number(text) -> int | None:
    text = _clean(text)
 
    digits = re.search(r"\d+", text)
    if digits:
        return int(digits.group())
 
    total = None
    for raw in text.split():
        value = _word_value(raw.strip(".,!?:;"))
 
        if value is None:
            if total is not None:
                break
            continue
 
        if total is None:
            total = value
        elif total >= 20 and total % 10 == 0 and 1 <= value <= 9:
            total += value
            break
        else:
            break
 
    return total
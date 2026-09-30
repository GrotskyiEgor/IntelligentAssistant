from rapidfuzz import fuzz
from .text import normalize_text
from ..config import ACTION_THRESHOLD


class CommandMatcher:
    def __init__(self, commands_map: dict[str, list[str]]):
        self.commands_map = commands_map

    def match(self, text: str):
        text = normalize_text(text)
        results = []

        for action, phrases in self.commands_map.items():
            score, word = self._best_score(text, phrases)
            if score >= ACTION_THRESHOLD:
                results.append((action, score, word))

        if not results:
            return None, None

        results.sort(key=lambda r: r[1], reverse=True)
        best = results[0]

        if len(results) > 1:
            second = results[1]
            if second[0] != best[0] and best[1] - second[1] < 5:
                return None, None

        return best[0], best[2]

    @staticmethod
    def _best_score(text, phrases):
        best_score, best_word = 0, None
        for phrase in phrases:
            phrase = normalize_text(phrase)
            if " " in phrase:
                candidates = [(fuzz.partial_ratio(phrase, text), phrase)]
            else:
                candidates = [(fuzz.ratio(w, phrase), w) for w in text.split()]
            for score, word in candidates:
                if score > best_score:
                    best_score, best_word = score, word
        return best_score, best_word
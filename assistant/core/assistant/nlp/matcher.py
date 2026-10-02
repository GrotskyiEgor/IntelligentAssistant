from rapidfuzz import fuzz
from .text import normalize_text
from ..config import ACTION_THRESHOLD

AMBIGUITY_MARGIN = 5


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

        top_score = max(r[1] for r in results)
        close = [r for r in results if top_score - r[1] < AMBIGUITY_MARGIN]

        longest = max(len(r[2]) for r in close)
        winners = [r for r in close if len(r[2]) == longest]

        if len({r[0] for r in winners}) > 1:
            return None, None

        best = max(winners, key=lambda r: r[1])
        return best[0], best[2]

    @staticmethod
    def _best_score(text, phrases):
        best_score, best_word = 0, None
        for phrase in phrases:
            phrase = normalize_text(phrase)
            if " " in phrase:
                if len(text) >= len(phrase) * 0.75:
                    candidates = [(fuzz.partial_ratio(phrase, text), phrase)]
                else:
                    candidates = [(fuzz.ratio(phrase, text), phrase)]
            else:
                candidates = [(fuzz.ratio(w, phrase), w) for w in text.split()]
            for score, word in candidates:
                if score > best_score:
                    best_score, best_word = score, word
        return best_score, best_word
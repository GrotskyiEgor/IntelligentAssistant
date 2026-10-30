from rapidfuzz import fuzz
 
from .phrases import PhraseStore
from .text import normalize_text
from ..config import ACTION_THRESHOLD
 
 
class CommandMatcher:
    def __init__(self, store: PhraseStore):
        self.store = store
 
    def match(self, text):
        self.store.refresh()
        text = normalize_text(text)
        results = []

        for action, phrases in self.store.commands.items():
            score, word = self._best_score(text, phrases)
            if score >= ACTION_THRESHOLD:
                results.append((action, score, word))

        if not results:
            return None, None

        results.sort(key=lambda r: (r[1], len(r[2])), reverse=True)
        best = results[0]

        if len(results) > 1:
            second = results[1]
            if (
                second[0] != best[0]
                and best[1] - second[1] < 5
                and len(best[2]) <= len(second[2])
            ):
                return None, None

        return best[0], best[2]

    @staticmethod
    def _best_score(text, phrases):
        best_score, best_word = 0, None
        for phrase in phrases:
            if " " in phrase:
                if len(text) >= len(phrase):
                    candidates = [(fuzz.partial_ratio(phrase, text), phrase)]
                else:
                    candidates = [(fuzz.ratio(phrase, text), phrase)]
            else:
                candidates = [(fuzz.ratio(w, phrase), w) for w in text.split()]
            for score, word in candidates:
                if score > best_score:
                    best_score, best_word = score, word
        return best_score, best_word
import threading
 
from django.db.models import Count, Max
 
from core.models import CommandPhrase
 
from .text import normalize_text
 
 
class PhraseStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._stamp = None
        self._commands: dict[str, list[str]] = {}
        self._answers: dict[str, list[str]] = {}
 
    @staticmethod
    def _current_stamp():
        data = CommandPhrase.objects.aggregate(n=Count("id"), t=Max("updated_at"))
        return data["n"], data["t"]
 
    def refresh(self, force: bool = False) -> bool:
        stamp = self._current_stamp()

        if not force and stamp == self._stamp:
            return False
 
        commands: dict[str, list[str]] = {}
        answers: dict[str, list[str]] = {}
        rows = CommandPhrase.objects.values_list("kind", "action", "phrase")

        for kind, action, phrase in rows:
            target = commands if kind == "command" else answers
            target.setdefault(action, []).append(normalize_text(phrase))
 
        with self._lock:
            self._commands, self._answers, self._stamp = commands, answers, stamp
        return True
 
    @property
    def commands(self) -> dict[str, list[str]]:
        with self._lock:
            return self._commands
 
    def answers(self, kind) -> list[str]:
        with self._lock:
            return self._answers.get(kind, [])
 
 
store = PhraseStore()
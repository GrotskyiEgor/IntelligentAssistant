import os
import time
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz

from ..nlp.text import normalize_text

MATCH_THRESHOLD = 75
AMBIGUITY_GAP = 5
SEARCH_TIMEOUT = 10.0
MAX_MATCHES = 60

KNOWN_FOLDERS = (
    (("завантаж", "загрузк", "даунлоад"), "Downloads"),
    (("документ",), "Documents"),
    (("робоч", "десктоп", "стіл"), "Desktop"),
    (("зображен", "картин", "фото", "малюнк"), "Pictures"),
    (("музик",), "Music"),
    (("відео", "відос"), "Videos"),
)
USER_FOLDER_NAMES = ("Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos")

SKIP_DIRS = {
    "appdata", "application data", "$recycle.bin", "system volume information",
    "node_modules", "__pycache__", "venv", "env", "site-packages", "windows",
}
SKIP_FILE_EXT = {".ini", ".tmp", ".pyc", ".dll", ".sys", ".dat", ".log"}


@dataclass
class Match:
    path: Path
    score: float
    depth: int

    @property
    def name(self) -> str:
        return self.path.name if self.path.is_dir() else self.path.stem


def _clean(text) -> str:
    text = text.replace("’", "'").replace("ʼ", "'")
    for ch in "_-.,!?":
        text = text.replace(ch, " ")
    return normalize_text(text)


def _skip_dir(name) -> bool:
    return name.startswith(".") or name.lower() in SKIP_DIRS


def _user_dirs() -> list[Path]:
    home = Path.home()
    bases = [home, *sorted(home.glob("OneDrive*"))]
    found = []
    for base in bases:
        for name in USER_FOLDER_NAMES:
            path = base / name
            if path.is_dir() and path not in found:
                found.append(path)
    return found


def known_folder(query):
    words = _clean(query).split()
    if not words:
        return None
    for stems, dirname in KNOWN_FOLDERS:
        if any(word.startswith(stems) for word in words):
            for path in _user_dirs():
                if path.name == dirname:
                    return path
    return None


def _search_roots():
    roots = [(path, 5) for path in _user_dirs()]
    roots.append((Path.home(), 3))
    return roots


def _iter_items(want_dirs, roots, deadline):
    visited = set()
    yielded = set()

    for root, max_depth in roots:
        base = len(root.parts)
        for current, dirs, files in os.walk(root):
            if time.monotonic() > deadline:
                return

            key = os.path.normcase(current)
            if key in visited:
                dirs.clear()
                continue
            visited.add(key)

            dirs[:] = [d for d in dirs if not _skip_dir(d)]
            depth = len(Path(current).parts) - base + 1

            names = dirs if want_dirs else [
                f for f in files
                if not f.startswith((".", "~$")) and os.path.splitext(f)[1].lower() not in SKIP_FILE_EXT
            ]
            for name in names:
                path = Path(current) / name
                if path not in yielded:
                    yielded.add(path)
                    yield path, depth

            if depth >= max_depth:
                dirs.clear()


def _score(query, name) -> float:
    if query == name:
        return 120
    return max(fuzz.ratio(query, name), fuzz.token_set_ratio(query, name))


def search(query, want_dirs, roots=None, timeout=SEARCH_TIMEOUT) -> list[Match]:
    q = _clean(query)
    if not q:
        return []

    deadline = time.monotonic() + timeout
    matches = []

    for path, depth in _iter_items(want_dirs, roots or _search_roots(), deadline):
        name = _clean(path.name if want_dirs else path.stem)
        if not name:
            continue
        score = _score(q, name)
        if score >= MATCH_THRESHOLD:
            matches.append(Match(path, score, depth))
            if len(matches) >= MAX_MATCHES:
                break

    matches.sort(key=lambda m: (-m.score, m.depth, len(str(m.path))))
    return matches


def pick(matches):
    if not matches:
        return None, []

    top = matches[0]
    close = [m for m in matches if top.score - m.score < AMBIGUITY_GAP]
    if len(close) == 1:
        return top, []

    close.sort(key=lambda m: m.depth)
    if close[0].depth < close[1].depth:
        return close[0], []

    return None, close[:3]


def search_and_pick(query, want_dirs):
    return pick(search(query, want_dirs))


def narrow(candidates, answer):
    from ..actions.numbers import parse_number

    number = parse_number(answer)
    if number is not None and 1 <= number <= len(candidates):
        return candidates[number - 1]

    q = _clean(answer)
    if not q:
        return None
    scored = sorted(((_score(q, _clean(m.name)), m) for m in candidates), key=lambda p: -p[0])
    if scored and scored[0][0] >= MATCH_THRESHOLD:
        if len(scored) == 1 or scored[0][0] - scored[1][0] >= AMBIGUITY_GAP:
            return scored[0][1]
    return None
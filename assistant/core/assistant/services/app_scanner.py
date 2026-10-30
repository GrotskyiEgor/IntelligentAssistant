import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Callable
 
from core.models import AppCommand, AssistantState
 
from ..nlp.text import normalize_text
 
SCAN_FLAG = "apps_scanned"
MAX_DEEP_DEPTH = 2 
 
BAD_NAME_PARTS = (
    "uninstall", "удал", "видал", "readme", "documentation", "manual",
    "website", "license", "release notes", "справк", "довідк",
)
BAD_EXE_PARTS = (
    "unins", "uninstall", "setup", "installer", "update", "crash",
    "report", "helper", "service", "redist", "elevate",
)
 
PS_SCRIPT = r"""
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $dirs = @(
        "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    ) | Where-Object { Test-Path $_ }
    $sh = New-Object -ComObject WScript.Shell
    $items = foreach ($f in (Get-ChildItem -Path $dirs -Recurse -Filter *.lnk -ErrorAction SilentlyContinue)) {
        $t = $sh.CreateShortcut($f.FullName).TargetPath
        if ($t) { [pscustomobject]@{ name = $f.BaseName; target = $t } }
    }
    ConvertTo-Json -InputObject @($items) -Compress
"""
 
 
def _is_junk(name, path) -> bool:
    lowered = name.lower()
    stem = os.path.basename(path).lower()
    return any(p in lowered for p in BAD_NAME_PARTS) or any(p in stem for p in BAD_EXE_PARTS)
 
 
def _windows_start_menu() -> list[tuple[str, str]]:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT],
        capture_output=True,
        timeout=180,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    raw = result.stdout.decode("utf-8-sig", errors="replace").strip()
    if not raw:
        return []
 
    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]
 
    found = []
    for item in data:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        target = (item.get("target") or "").strip()
        if name and target.lower().endswith(".exe") and os.path.isfile(target):
            found.append((name, target))
    return found
 
 
def _windows_deep() -> list[tuple[str, str]]:
    roots = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    ]
    found = []
    for root in filter(None, roots):
        if not os.path.isdir(root):
            continue
        base_depth = root.rstrip(os.sep).count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.rstrip(os.sep).count(os.sep) - base_depth >= MAX_DEEP_DEPTH:
                dirnames[:] = []  # глибше не йдемо
            for filename in filenames:
                if filename.lower().endswith(".exe"):
                    found.append((Path(filename).stem, os.path.join(dirpath, filename)))
    return found
 
 
def _mac_apps() -> list[tuple[str, str]]:
    folders = [
        "/Applications",
        "/Applications/Utilities",
        "/System/Applications",
        "/System/Applications/Utilities",
        str(Path.home() / "Applications"),
    ]
    found = []
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for entry in sorted(os.listdir(folder)):
            if entry.endswith(".app"):
                found.append((entry[:-4], os.path.join(folder, entry)))
    return found
 
 
def scan_apps(deep: bool = False) -> list[tuple[str, str]] | None:
    system = platform.system()
    if system == "Windows":
        found = _windows_start_menu()
        if deep:
            found += _windows_deep()
    elif system == "Darwin":
        found = _mac_apps()
    else:
        return None
    return [(name, path) for name, path in found if not _is_junk(name, path)]
 
 
def save_apps(found: list[tuple[str, str]]) -> int:
    existing = list(AppCommand.objects.values_list("path", "name"))
    paths = {os.path.normcase(p) for p, _ in existing}
    names = {normalize_text(n) for _, n in existing}
 
    new = []
    for name, path in found:
        key_path = os.path.normcase(path)
        key_name = normalize_text(name)
        if not key_name or len(path) > 255 or key_path in paths or key_name in names:
            continue
        paths.add(key_path)
        names.add(key_name)
        new.append(AppCommand(name=name[:100], keyword=key_name[:100], path=path))
 
    AppCommand.objects.bulk_create(new)
    return len(new)
 
 
def mark_scanned():
    AssistantState.objects.update_or_create(key=SCAN_FLAG, defaults={"value": "1"})
 
 
def scan_if_first_run(log: Callable[[str], None] = print, deep: bool = False) -> int | None:
    if AssistantState.objects.filter(key=SCAN_FLAG).exists():
        return None
 
    log("ANSWER: Перший запуск, шукаю програми")
    try:
        found = scan_apps(deep=deep)
    except Exception as error:
        log(f"Не вдалося просканувати програми: {error}")
        return None  # прапорець не ставимо, спробуємо наступного разу
 
    if found is None:
        log("Автоматичний пошук програм підтримується лише на Windows і macOS")
        return None
 
    added = save_apps(found)
    mark_scanned()
    log(f"ANSWER: Додала програм: {added}")
    return added
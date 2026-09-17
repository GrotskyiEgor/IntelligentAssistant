import os
import subprocess
import platform
from pathlib import Path


def find_path(filename: str):
    system = platform.system()

    filename = os.path.splitext(filename)[0].lower().strip()

    if system == "Windows":
        return find_windows_app(filename)

    elif system == "Darwin":
        return find_mac_app(filename)

    else:
        return find_linux_app(filename)


def find_windows_app(filename: str):
    try:
        result = subprocess.run(
            ["where", filename + ".exe"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        if result.returncode == 0:
            for path in result.stdout.splitlines():
                path = path.strip()

                if os.path.isfile(path):
                    return path

    except Exception:
        pass

    start_menu_dirs = [
        os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs"
        ),

        os.path.join(
            os.environ.get("PROGRAMDATA", ""),
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs"
        )
    ]

    for start_dir in start_menu_dirs:

        if not os.path.exists(start_dir):
            continue

        for root, dirs, files in os.walk(start_dir):

            for file in files:

                if not file.lower().endswith(".lnk"):
                    continue

                name = os.path.splitext(file)[0].lower()

                if name == filename:
                    shortcut = os.path.join(root, file)

                    target = get_shortcut_target(shortcut)

                    if target and os.path.exists(target):
                        return target

    search_dirs = [
        os.environ.get("LOCALAPPDATA"),
        os.environ.get("APPDATA"),
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)")
    ]

    for base_dir in search_dirs:
        if not base_dir or not os.path.exists(base_dir):
            continue

        for root, dirs, files in os.walk(base_dir):

            depth = root[len(base_dir):].count(os.sep)

            if depth > 4:
                dirs.clear()
                continue

            for file in files:

                if file.lower() == filename + ".exe":
                    return os.path.join(root, file)


    return None


def get_shortcut_target(shortcut_path):
    try:
        powershell = [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "$shell = New-Object -ComObject WScript.Shell; "
                f"$shortcut = $shell.CreateShortcut('{shortcut_path}'); "
                "Write-Output $shortcut.TargetPath"
            )
        ]

        result = subprocess.run(
            powershell,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        target = result.stdout.strip()

        if target:
            return target

    except Exception:
        pass

    return None


def find_mac_app(filename: str):

    search_dirs = [
        "/Applications",
        os.path.expanduser("~/Applications")
    ]

    for directory in search_dirs:

        if not os.path.exists(directory):
            continue

        for root, dirs, files in os.walk(directory):

            for file in files:

                if file.lower() == filename.lower() + ".app":
                    return os.path.join(root, file)

    return None


def find_linux_app(filename: str):
    try:

        result = subprocess.run(
            ["which", filename],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:

            path = result.stdout.strip()

            if os.path.exists(path):
                return path

    except Exception:
        pass

    return None
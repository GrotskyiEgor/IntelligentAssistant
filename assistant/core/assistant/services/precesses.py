import os
import platform
import subprocess


def open_app(path: str):
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen([path])


def close_app(app_name: str) -> bool:
    if platform.system() == "Windows":
        result = subprocess.run(
            ["taskkill", "/F", "/IM", app_name, "/T"],
            capture_output=True, text=True, encoding="cp866", errors="replace",
        )
        return result.returncode == 0
    return subprocess.run(["pkill", "-f", app_name], capture_output=True).returncode == 0
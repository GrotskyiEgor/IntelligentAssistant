import os
import sys
import signal
import ctypes
from pathlib import Path

DJANGO_DIR = Path(__file__).resolve().parent.parent / "assistant"
sys.path.insert(0, str(DJANGO_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "assistant.settings")

import django
django.setup()

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app import MainWindow

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("voice.assistant.app")
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path))
    win = MainWindow()
    win.show()

    signal.signal(signal.SIGINT, lambda *_: win.close())
    heartbeat = QTimer()
    heartbeat.timeout.connect(lambda: None)
    heartbeat.start(200)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
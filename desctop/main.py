import os
import sys
import ctypes

import PyQt6 as qt 

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

    sys.exit(app.exec())
    
if __name__ == "__main__":
    main()


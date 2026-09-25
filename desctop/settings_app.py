import sys, os, subprocess, json, re
import PyQt6 as qt

from PyQt6.QtCore import QProcess, QProcessEnvironment
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt


class SettingsWindow(QWidget):
    def __init__(self, win):
        super().__init__()
        self.setWindowTitle("Налаштування")
        self.setFixedSize(400, 500)
        self.setStyleSheet("background: white;")

        self.json = "settings.json"

        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

        self.win = win
        self.lay = QVBoxLayout()
        self.lay.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.header = QFrame()
        self.header.lay = QHBoxLayout()
        self.header.setLayout(self.header.lay)

        title = QLabel("Налаштування")
        title.setStyleSheet("font-size: 26px; font-weight: bold;")

        save_btn = QPushButton(text="Зберегти")
        save_btn.setStyleSheet("QPushButton { font-size: 15px; background: gainsboro; border-radius: 6px; } QPushButton:hover { background: #b8b8b8; }")
        save_btn.setFixedSize(120, 38)
        save_btn.clicked.connect(self.close)

        self.header.lay.addWidget(title)
        self.header.lay.addWidget(save_btn)

        self.name = QLineEdit()
        self.name.setStyleSheet("font-size: 15px; background: #fafafa; border: 1px solid gainsboro; border-radius: 8px; padding: 0 8px;")
        self.name.setPlaceholderText("Enter assistant name")
        self.name.setFixedHeight(38)

        self.voice = QComboBox()
        self.voice.setStyleSheet("""
            QComboBox {
                font-size: 15px;
                background: #fafafa;
                border: 1px solid gainsboro;
                border-radius: 8px;
                padding: 0 8px;
            }
        """)
        
        self.voice.addItems(["Alex", "Victoria"])
        self.voice.setFixedHeight(38)

        self.background = QCheckBox()
        self.background.setFixedSize(26, 26)

        self.background.setStyleSheet("""
        QCheckBox {
            background: transparent;
        }

        QCheckBox::indicator {
            border-radius: 6px;
        }

        QCheckBox::indicator:checked {
            background: #333333;
        }

        QCheckBox::indicator:unchecked {
            background: #d5d5d5;
        }
        """)

        # background_layout = QHBoxLayout()
        # background_layout.addWidget(QLabel("Work in background"))
        # background_layout.addStretch()
        # background_layout.addWidget(self.background)
        background_layout = QHBoxLayout()
        background_label = QLabel("Працювати у фоновому режимі")
        background_label.setStyleSheet("font-size: 15px;")
        background_layout.addWidget(background_label)
        background_layout.addStretch()
        background_layout.addWidget(self.background)

        self.lay.addWidget(self.header)
        self.lay.addSpacing(20)

        name_label = QLabel("Ім'я помічника:")
        name_label.setStyleSheet("font-size: 15px;")

        self.lay.addWidget(name_label)
        self.lay.addWidget(self.name)

        self.lay.addSpacing(10)

        voice_label = QLabel("Виберіть голос:")
        voice_label.setStyleSheet("font-size: 15px;")

        self.lay.addWidget(voice_label)
        self.lay.addWidget(self.voice)

        self.lay.addSpacing(10)
        # self.lay.addLayout(background_layout)

        self.setLayout(self.lay)
        self.load_settings()

    def validate(self):
        text = self.name.text().strip()
        if len(text) < 3 or len(text) > 15:
            return False
        elif not re.fullmatch(r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9 .,!?'-]+", text):
            return False
        else:
            return text

    def load_settings(self):
        if not os.path.exists(self.json):
            self.name.setText("Assistant")
            self.voice.setCurrentText("Alex")
            return

        with open(self.json, "r", encoding="utf-8") as file:
            settings = json.load(file)

        self.name.setText(
            settings.get("name", "Assistant")
        )

        self.voice.setCurrentText(
            settings.get("voice", "Alex")
        )

    def save_settings(self):
        name = self.validate()

        if name:
            settings = {
                "name": name,
                "voice": self.voice.currentText()
            }

            with open(self.json, "w", encoding="utf-8") as file:
                json.dump(settings, file, ensure_ascii=False, indent=4)

    def closeEvent(self, event):
        self.deleteLater()
        self.save_settings()
        self.win.settings = None
        event.accept()
import json
import os
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QFormLayout, QFrame, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget,
)
from components import Label
from hPyT import title_bar_color
from theme import get_theme_colors


class SettingsWindow(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.json = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")
        self.setWindowTitle("Налаштування")
        self.setFixedSize(420, 510)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        header = QFrame()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        title = QLabel("Налаштування")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        subtitle = Label("Налаштуйте вигляд і параметри помічника")
        subtitle.setStyleSheet("color: #a1a1aa; font-size: 15px;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        form = QFormLayout()
        form.setVerticalSpacing(12)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Наприклад, Помічник")
        self.voice = QComboBox()
        self.voice.addItems(["Alex", "Victoria"])
        self.theme = QComboBox()
        self.theme.addItem("Темна", "dark")
        self.theme.addItem("Світла", "light")
        self.accent = QComboBox()
        self.accent.addItem("Фіолетова", "purple")
        self.accent.addItem("Синя", "blue")
        form.addRow("Ім’я помічника", self.name)
        form.addRow("Голос", self.voice)
        form.addRow("Тема оформлення", self.theme)
        form.addRow("Колір кнопок", self.accent)
        layout.addLayout(form)
        layout.addStretch()

        save_btn = QPushButton("Зберегти")
        save_btn.setFixedHeight(42)
        save_btn.setStyleSheet("QPushButton { background: #7565f7; color: black; border: none; border-radius: 10px; font-weight: 600; } QPushButton:hover { background: #6152de; }")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        self.save_btn = save_btn
        self.inputs = (self.name, self.voice, self.theme, self.accent)
        self.theme.currentIndexChanged.connect(self.on_theme_changed)
        self.accent.currentIndexChanged.connect(self.on_theme_changed)
        self.load_settings()
        self.apply_theme(win.preferences, sync_main=False)

    def on_theme_changed(self, _index=None):
        settings = {"theme": self.theme.currentData(), "accent": self.accent.currentData()}
        self.apply_theme(settings, sync_main=False)
        self.win.apply_theme(settings)

    def apply_theme(self, settings, sync_main=True):
        theme, accent = get_theme_colors(settings)
        self.setStyleSheet(f"background: {theme['window']}; color: {theme['foreground']}; font-size: 14px;")
        title_bar_color.set(self, color=theme["window"])
        for widget in getattr(self, "inputs", (self.name, self.voice, self.theme, self.accent)):
            widget.setFixedHeight(40)
            widget.setStyleSheet(f"QLineEdit, QComboBox {{ background: {theme['field']}; color: {theme['foreground']}; border: 1px solid {theme['border']}; border-radius: 9px; padding: 0 11px; }} QComboBox QAbstractItemView {{ background: {theme['field']}; color: {theme['foreground']}; selection-background-color: {accent['primary']}; }}")
        if hasattr(self, "save_btn"):
            self.save_btn.setStyleSheet(f"QPushButton {{ background: {accent['primary']}; color: black; border: none; border-radius: 10px; font-weight: 600; }} QPushButton:hover {{ background: {accent['hover']}; }}")
        if hasattr(self, "findChildren"):
            for label in self.findChildren(QLabel):
                if label.text() == "Налаштуйте вигляд і параметри помічника":
                    label.setStyleSheet(f"color: {theme['muted']}; font-size: 15px;")
        if sync_main:
            self.win.apply_theme(settings)

    def validate(self):
        text = self.name.text().strip()
        return text if 3 <= len(text) <= 24 and re.fullmatch(r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9 .,!?'-]+", text) else None

    def load_settings(self):
        try:
            with open(self.json, "r", encoding="utf-8") as file:
                settings = json.load(file)
        except (OSError, json.JSONDecodeError):
            settings = {}
        self.name.setText(settings.get("name", "Помічник"))
        self.voice.setCurrentText(settings.get("voice", "Alex"))
        self.theme.setCurrentIndex(max(0, self.theme.findData(settings.get("theme", "dark"))))
        self.accent.setCurrentIndex(max(0, self.accent.findData(settings.get("accent", "purple"))))

    def save_settings(self):
        name = self.validate()
        if not name:
            self.name.setToolTip("Введіть ім’я довжиною від 3 до 24 символів")
            return
        settings = {"name": name, "voice": self.voice.currentText(), "theme": self.theme.currentData(), "accent": self.accent.currentData()}
        with open(self.json, "w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)
        self.win.apply_theme(settings)
        self.close()

    def closeEvent(self, event):
        self.win.settings = None
        event.accept()

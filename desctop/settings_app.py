import json
import os
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import *

from components import Label
from hPyT import title_bar_color
from theme import get_theme_colors


class HorizontalScrollArea(QScrollArea):
    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.angleDelta().x()
        bar = self.horizontalScrollBar()
        bar.setValue(bar.value() - delta)
        event.accept()


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

        self.accent = HorizontalScrollArea()
        self.accent.setWidgetResizable(True)
        self.accent.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.accent.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.accent.setFixedHeight(60)
        self.accent.setFrameShape(QFrame.Shape.NoFrame)
        self.accent.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.accent.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        self.accent.verticalScrollBar().setStyleSheet("QScrollBar { width: 0px; }")
        self.accent.horizontalScrollBar().setStyleSheet("QScrollBar { height: 0px; background: transparent; border: none; }")
        self.accent.viewport().setStyleSheet("background: transparent; border: none;")

        accent_container = QWidget()
        accent_container.setStyleSheet("background: transparent; border: none;")
        accent_layout = QHBoxLayout(accent_container)
        accent_layout.setContentsMargins(0, 0, 0, 0)
        accent_layout.setSpacing(10)
        self.accent.setWidget(accent_container)
        self.accent_buttons = {}
        self.accent_rings = {}
        self.active_accent = "purple"

        theme_data = __import__("json").load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "themes.json"), "r", encoding="utf-8"))
        accent_ids = list(theme_data.get("accents", {}).keys())

        for accent_id in accent_ids:
            ring = QFrame()
            ring.setFixedSize(36, 36)

            btn = QPushButton(ring)
            btn.setProperty("accent_id", accent_id)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setGeometry(5, 5, 26, 26)
            btn.clicked.connect(lambda checked=False, value=accent_id: self.set_accent(value))

            accent_layout.addWidget(ring)
            self.accent_buttons[accent_id] = btn
            self.accent_rings[accent_id] = ring
        accent_container.setFixedWidth(accent_layout.sizeHint().width())
        self.accent.setWidgetResizable(False)

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
        self.inputs = (self.name, self.voice, self.theme)
        self.load_settings()
        self.theme.currentIndexChanged.connect(self.on_theme_changed)
        self.apply_theme(
            {"theme": self.theme.currentData(), "accent": self.active_accent},
            sync_main=False,
        )

    def set_accent(self, accent_id):
        self.active_accent = accent_id
        settings = {"theme": self.theme.currentData(), "accent": accent_id}
        self.apply_theme(settings, sync_main=False)
        self.win.apply_theme(settings)

    def on_theme_changed(self, _index=None):
        settings = {"theme": self.theme.currentData(), "accent": self.active_accent}
        self.apply_theme(settings, sync_main=False)
        self.win.apply_theme(settings)

    def apply_theme(self, settings, sync_main=True):
        self.active_accent = settings.get("accent", self.active_accent)
        theme, accent = get_theme_colors(settings)
        self.setStyleSheet(f"background: {theme['window']}; color: {theme['foreground']}; font-size: 14px;")
        title_bar_color.set(self, color=theme["window"])
        selection_text = "white" if self.active_accent in {"purple", "blue", "lime", "orange"} else "#2d2d2d"
        for widget in getattr(self, "inputs", (self.name, self.voice, self.theme)):
            widget.setFixedHeight(40)
            widget.setStyleSheet(f"""
                QLineEdit, QComboBox {{
                    background: {theme['field']};
                    color: {theme['foreground']};
                    border: 1px solid {theme['border']};
                    border-radius: 9px;
                    padding: 0 11px;
                }}
                QComboBox {{
                    padding-right: 30px;
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 30px;
                    border: none;
                    border-left: 1px solid {theme['border']};
                    border-top-right-radius: 9px;
                    border-bottom-right-radius: 9px;
                }}
                QComboBox QAbstractItemView {{
                    background: {theme['field']};
                    color: {theme['foreground']};
                    border: 1px solid {theme['border']};
                    border-radius: 10px;
                    padding: 3px;
                    selection-background-color: {accent['primary']};
                    outline: none;
                }}
                QComboBox QAbstractItemView::item {{
                    min-height: 28px;
                    padding: 1px 9px;
                    margin: 2px 1px;
                    border-radius: 8px;
                }}
                QComboBox QAbstractItemView::item:hover,
                QComboBox QAbstractItemView::item:selected {{
                    background-color: {accent['primary']};
                    color: {selection_text};
                }}
            """)
        self.accent.setFixedHeight(60)
        self.accent.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        for accent_id, btn in getattr(self, "accent_buttons", {}).items():
            accent_theme = get_theme_colors({"theme": settings.get("theme", "dark"), "accent": accent_id})[1]
            selected = accent_id == self.active_accent
            btn.setStyleSheet(
                f"QPushButton {{ background: {accent_theme['primary']}; border-radius: 13px; border: none; }}"
            )
            ring = self.accent_rings[accent_id]
            ring.setStyleSheet(
                f"QFrame {{ background: transparent; border: {2 if selected else 0}px solid {accent['primary']}; border-radius: 18px; }}"
            )

        if hasattr(self, "save_btn"):
            accent_id = settings.get("accent")
            button_text = "white" if accent_id in {"purple", "blue", "lime", "orange"} else "#2d2d2d"
            self.save_btn.setStyleSheet(f"QPushButton {{ background: {accent['primary']}; color: {button_text}; border: none; border-radius: 10px; font-weight: 600; }} QPushButton:hover {{ background: {accent['hover']}; color: {button_text}; }}")
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
        self.active_accent = settings.get("accent", "purple")
        if self.active_accent not in self.accent_buttons:
            self.active_accent = "purple"

    def save_settings(self):
        name = self.validate()
        if not name:
            self.name.setToolTip("Введіть ім’я довжиною від 3 до 24 символів")
            return
        settings = {"name": name, "voice": self.voice.currentText(), "theme": self.theme.currentData(), "accent": self.active_accent}
        with open(self.json, "w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)
        self.win.apply_theme(settings)
        self.close()

    def closeEvent(self, event):
        self.win.settings = None
        event.accept()

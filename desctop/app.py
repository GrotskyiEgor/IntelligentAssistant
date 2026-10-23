import json
import os

from hPyT import title_bar_color
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QMenuBar, QWidget

from app_parts.app_chat import ChatMixin
from app_parts.app_commands import CommandPanelMixin
from app_parts.app_messages import MessageMixin
from app_parts.app_process import AssistantProcessMixin
from app_parts.app_theme import ThemeMixin
from settings_app import SettingsWindow

class MainWindow(ThemeMixin, ChatMixin, MessageMixin, CommandPanelMixin, AssistantProcessMixin, QMainWindow):
    def __init__(self):
        super().__init__()

        self.assistant_process = None
        self.settings = None


        try:
            with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json"), "r", encoding="utf-8") as file:
                self.preferences = json.load(file)
        except Exception as error:
            print(error)
            self.preferences = {}


        self.setWindowTitle("Голосовий помічник")
        self.setMinimumSize(960, 540)
        self.setFixedSize(1280, 720)
        self.setStyleSheet("background: #181818;")
        
        title_bar_color.set(self, color='#181818')

        self.menubar = QMenuBar()
        self.menubar.setStyleSheet("""
            QMenuBar {
                color: white;
                border: none;
                padding: 2px 6px;
                font-size: 13px;
                font-weight: bold;
            }

            QMenuBar::item {
                background-color: #2f2f2f;
                color: white;
                padding: 6px 14px;
                margin: 2px;
                border-radius: 8px;
            }

            QMenuBar::item:selected {
                background-color: #3b82f6;
                color: white;
            }

            QMenu {
                background-color: #2f2f2f;
                color: white;
                border: 1px solid #4a4a4a;
                border-radius: 11px;
                padding: 4px;
            }

            QMenu::item {
                font-size: 13px;
                font-weight: bold;
                padding: 6px 25px;
                border-radius: 8px;
                color: white;
            }

            QMenu::item:selected {
                background-color: #3b82f6;
                color: white;
            }
        """)

        self.menu = self.menubar.addMenu("Асистент")
        self.menu.setWindowFlags(self.menu.windowFlags() | Qt.WindowType.NoDropShadowWindowHint | Qt.WindowType.FramelessWindowHint)
        self.menu.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        settings_act = self.menu.addAction("Налаштування")
        settings_act.triggered.connect(self.open_settings)

        exit_act = self.menu.addAction("Вихід")
        exit_act.triggered.connect(self.close)

        self.center = QWidget()
        self.center.setObjectName("centralBg")
        self.center.setStyleSheet("QWidget#centralBg { background: #181818; }")
        self.setCentralWidget(self.center)

        self.main_layout = QHBoxLayout(self.center)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setMenuWidget(self.menubar)

        self.create_main_panel()
        self.create_chat()
        self.create_command_panel()

        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.apply_theme(self.preferences)

    def open_settings(self):
        self.settings = SettingsWindow(self)
        self.settings.show()

    def closeEvent(self, e):
        if self.assistant_process is not None:
            self.assistant_process.kill()
            self.assistant_process.waitForFinished(2000)

        if self.settings:
            self.settings.close()

        e.accept()

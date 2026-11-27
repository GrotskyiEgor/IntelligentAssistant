import re
import os
import sys
import json

from hPyT import title_bar_color
from PyQt6.QtCore import Qt, QTimer, QProcess, QProcessEnvironment, QDate, QSize
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import QComboBox, QDateEdit, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenuBar, QPushButton, QScrollArea, QSizePolicy, QStackedWidget, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer, QProcess, QProcessEnvironment

from app_parts.app_chat import ChatMixin
from app_parts.app_commands import CommandPanelMixin
from app_parts.app_messages import MessageMixin
from app_parts.app_process import AssistantProcessMixin
from app_parts.app_theme import ThemeMixin
from settings_app import SettingsWindow
from calendar_app import CalendarPanel
from theme import get_theme_colors
from task_app import TaskForm


class MainWindow(ThemeMixin, ChatMixin, MessageMixin, CommandPanelMixin, AssistantProcessMixin, QMainWindow):
    def __init__(self):
        super().__init__()

        self.assistant_process = None
        self.settings = None
        self.scheduled_tasks = []
        self.task_form = None


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

    def open_scheduled_task(self, task):
        self.current_scheduled_task = dict(task)
        self.messages_frame.hide()
        if hasattr(self, "task_editor"):
            self.messages_frame_back_layout.removeWidget(self.task_editor)
            self.task_editor.deleteLater()
        self.task_editor = QWidget()
        self.task_editor.setObjectName("taskEditor")
        root = QVBoxLayout(self.task_editor)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("taskHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        back = QPushButton()
        back.setObjectName("taskBackButton")
        back.setIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "back.svg")))
        back.setIconSize(QSize(22, 22))
        back.setFixedSize(42, 42)
        back.clicked.connect(self.close_scheduled_task)
        self.task_title = QLineEdit(str(task.get("title", "")))
        self.task_title.setPlaceholderText("Назва задачі")
        self.task_title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header_layout.addWidget(back)
        header_layout.addWidget(self.task_title, 1)
        root.addWidget(header)

        created = task.get("created_at", task.get("created", ""))
        edited = task.get("edited_at", task.get("updated_at", task.get("edited", "")))
        stamp = edited or created
        stamp_text = str(stamp)
        for date_format in ("yyyy-MM-dd", "dd.MM.yy", "dd.MM.yyyy"):
            parsed_stamp = QDate.fromString(stamp_text[:10], date_format)
            if parsed_stamp.isValid():
                stamp_text = parsed_stamp.toString("dd.MM.yy")
                break
        status = QLabel(f"{'Редаговано' if edited else 'Створено'} {stamp_text}" if stamp_text else "Заплановане завдання")
        status.setStyleSheet(f"color: {self.theme['muted']}; background: transparent; border: none; font-size: 15px;")
        root.addWidget(status)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        form = QVBoxLayout(content)
        form.setContentsMargins(2, 4, 2, 4)
        form.setSpacing(8)

        form.addWidget(QLabel("Опис"))
        self.task_description = QTextEdit()
        self.task_description.setPlaceholderText("Додайте опис завдання")
        self.task_description.setPlainText(str(task.get("description", "")))
        self.task_description.setFixedHeight(100)
        form.addWidget(self.task_description)

        form.addWidget(QLabel("Кінцевий термін"))
        self.task_deadline = QDateEdit()
        self.task_deadline.setCalendarPopup(True)
        self.task_deadline.setDisplayFormat("dd.MM.yyyy")
        deadline = str(task.get("deadline", ""))
        parsed = QDate.fromString(deadline[:10], "yyyy-MM-dd")
        if not parsed.isValid():
            parsed = QDate.fromString(deadline[:10], "dd.MM.yyyy")
        if not parsed.isValid():
            parsed = QDate.fromString(deadline[:8], "dd.MM.yy")
        if parsed.isValid():
            self.task_deadline.setDate(parsed)
        else:
            self.task_deadline.setDate(QDate.currentDate())
        form.addWidget(self.task_deadline)

        form.addWidget(QLabel("Складність"))
        self.task_difficulty = QComboBox()
        self.task_difficulty.addItems(["low", "mid", "high"])
        difficulty = str(task.get("difficulty", "mid")).lower()
        self.task_difficulty.setCurrentText(difficulty if difficulty in {"low", "mid", "high"} else "mid")
        form.addWidget(self.task_difficulty)

        photos_title = QHBoxLayout()
        photos_title.addWidget(QLabel("Фото"), 1)
        add_photo = QPushButton("Додати фото")
        add_photo.clicked.connect(self.add_task_photos)
        photos_title.addWidget(add_photo)
        form.addLayout(photos_title)
        self.task_photos = list(task.get("photos", []))
        self.task_photos_layout = QVBoxLayout()
        form.addLayout(self.task_photos_layout)
        self.refresh_task_photos()
        form.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        save = QPushButton("Зберегти")
        save.setFixedHeight(46)
        save.clicked.connect(self.save_scheduled_task)
        root.addWidget(save)

        theme = self.theme
        self.task_editor.setStyleSheet(f"""
            QWidget#taskEditor {{ background: {theme['panel']}; color: {theme['foreground']}; font-size: 15px; }}
            QLabel {{ color: {theme['foreground']}; background: transparent; border: none; font-size: 15px; }}
            QLineEdit, QTextEdit, QComboBox, QDateEdit {{ background: {theme['field']}; color: {theme['foreground']}; border: 1px solid {theme['border']}; border-radius: 10px; padding: 8px; }}
            QComboBox::drop-down, QDateEdit::drop-down {{ background: {theme['field']}; border: none; border-left: 1px solid {theme['border']}; border-top-right-radius: 9px; border-bottom-right-radius: 9px; width: 30px; }}
            QComboBox QAbstractItemView {{ background: {theme['field']}; color: {theme['foreground']}; border: 1px solid {theme['border']}; selection-background-color: {self.accent['primary']}; selection-color: white; outline: none; padding: 4px; }}
            QCalendarWidget QWidget {{ background: {theme['panel']}; color: {theme['foreground']}; }}
            QCalendarWidget QToolButton {{ background: {theme['field']}; color: {theme['foreground']}; border: none; border-radius: 8px; padding: 6px; font-size: 15px; }}
            QCalendarWidget QToolButton:hover {{ background: {self.accent['hover']}; color: white; }}
            QCalendarWidget QMenu {{ background: {theme['panel']}; color: {theme['foreground']}; }}
            QCalendarWidget QSpinBox {{ background: {theme['field']}; color: {theme['foreground']}; border: 1px solid {theme['border']}; border-radius: 8px; padding: 4px; }}
            QCalendarWidget QAbstractItemView:enabled {{ background: {theme['field']}; color: {theme['foreground']}; selection-background-color: {self.accent['primary']}; selection-color: white; outline: none; }}
            QPushButton#taskBackButton {{ background: {theme['field']}; color: {theme['foreground']}; border: 1px solid {theme['border']}; border-radius: 21px; padding: 0; }}
            QPushButton#taskBackButton:hover {{ background: {self.accent['primary']}; border-color: {self.accent['primary']}; }}
            QPushButton {{ background: {self.accent['primary']}; color: white; border: none; border-radius: 10px; padding: 8px 12px; font-weight: bold; }}
            QPushButton:hover {{ background: {self.accent['hover']}; }}
            QScrollArea, QWidget {{ border: none; }}
        """)
        self.messages_frame_back_layout.addWidget(self.task_editor)
        self.task_editor.show()

    def close_scheduled_task(self):
        if hasattr(self, "task_editor"):
            self.messages_frame_back_layout.removeWidget(self.task_editor)
            self.task_editor.deleteLater()
            del self.task_editor
        self.messages_frame.show()

    def add_task_photos(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Оберіть фото", "", "Зображення (*.png *.jpg *.jpeg *.webp *.bmp)")
        self.task_photos.extend(paths)
        self.refresh_task_photos()

    def refresh_task_photos(self):
        while self.task_photos_layout.count():
            item = self.task_photos_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for path in self.task_photos:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 2, 4, 2)
            preview = QLabel()
            preview.setFixedSize(52, 42)
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                preview.setPixmap(pixmap.scaled(52, 42, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            row_layout.addWidget(preview)
            name = QLabel(os.path.basename(path))
            name.setToolTip(path)
            row_layout.addWidget(name, 1)
            remove = QPushButton("×")
            remove.setFixedSize(32, 32)
            remove.clicked.connect(lambda checked=False, value=path: self.remove_task_photo(value))
            row_layout.addWidget(remove)
            self.task_photos_layout.addWidget(row)

    def remove_task_photo(self, path):
        if path in self.task_photos:
            self.task_photos.remove(path)
            self.refresh_task_photos()

    def save_scheduled_task(self):
        task = dict(self.current_scheduled_task)
        task.update({
            "title": self.task_title.text().strip() or "Задача",
            "description": self.task_description.toPlainText().strip(),
            "deadline": self.task_deadline.date().toString("yyyy-MM-dd"),
            "difficulty": self.task_difficulty.currentText(),
            "photos": list(self.task_photos),
        })
        existing_index = next((index for index, item in enumerate(self.scheduled_tasks) if item.get("id") == task.get("id")), None)
        if existing_index is None:
            task.setdefault("id", str(len(self.scheduled_tasks) + 1))
            task.setdefault("created_at", QDate.currentDate().toString("yyyy-MM-dd"))
            self.scheduled_tasks.append(task)
        else:
            task["edited_at"] = QDate.currentDate().toString("yyyy-MM-dd")
            self.scheduled_tasks[existing_index] = task
        self.current_scheduled_task = task
        self.refresh_scheduled_tasks()
        # CreateTask
        print(task)

    def create_scheduled_task(self):
        task_id = str(max((int(task.get("id", 0)) for task in self.scheduled_tasks if str(task.get("id", "")).isdigit()), default=0) + 1)
        self.open_scheduled_task({
            "id": task_id,
            "title": "",
            "description": "",
            "deadline": QDate.currentDate().toString("yyyy-MM-dd"),
            "difficulty": "mid",
            "photos": [],
            "created_at": QDate.currentDate().toString("yyyy-MM-dd"),
        })

    def refresh_scheduled_tasks(self):
        while self.tasks_buttons_layout.count() > 1:
            item = self.tasks_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for task in self.scheduled_tasks:
            button = QPushButton(task.get("title") or "Задача")
            button.setMinimumHeight(40)
            button.setToolTip(task.get("description", ""))
            button.clicked.connect(lambda checked=False, value=task: self.open_scheduled_task(value))
            self.tasks_buttons_layout.insertWidget(self.tasks_buttons_layout.count() - 1, button)

    def open_task_form(self, task=None):
        if self.task_form:
            if task is None:
                return
            self.close_task_form()

        self.task_form = TaskForm(self, task)
        self.task_form.apply_theme(self.theme, self.accent)
        self.messages_frame.hide()
        self.messages_frame_back_layout.addWidget(self.task_form)
        self.task_form.title_input.setFocus()

    def close_task_form(self):
        self.messages_frame_back_layout.removeWidget(self.task_form)
        self.task_form.hide()
        self.task_form.deleteLater()
        self.task_form = None
        self.messages_frame.show()

    def open_settings(self):
        self.settings = SettingsWindow(self)
        self.settings.show()

    def closeEvent(self, e):
        if self.assistant_process is not None:
            self.assistant_process.kill()
            self.assistant_process.waitForFinished(2000)

        if self.settings:
            self.settings.close()

        if self.calendar:
            self.calendar.close()

        e.accept()

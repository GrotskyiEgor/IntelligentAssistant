import os

from django.core.exceptions import ValidationError
from django.db import DatabaseError
from PyQt6.QtCore import QDate, QSize, QTime, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTextEdit, QTimeEdit, QVBoxLayout,
)

from db_response.tasks import create_task, delete_task, update_task


class TaskForm(QFrame):
    def __init__(self, win, task=None):
        super().__init__()
        self.win = win
        self.task = task
        self.photos = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(12)

        self.back_btn = QPushButton()
        self.back_btn.setObjectName("taskBackButton")
        self.back_btn.setToolTip("Повернутися до чату")
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setIcon(QIcon(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "back.svg"
        )))
        self.back_btn.setIconSize(QSize(22, 22))
        self.back_btn.setFixedSize(42, 42)
        self.back_btn.clicked.connect(win.close_task_form)

        title = QLabel("Редагування завдання" if task else "Створення завдання")
        title.setObjectName("taskTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header.addWidget(self.back_btn)
        header.addWidget(title, 1)
        header.addSpacing(42)  # щоб заголовок був по центру
        layout.addLayout(header)

        fields = QFormLayout()
        fields.setSpacing(12)
        layout.addLayout(fields)

        self.title_input = QLineEdit()
        self.title_input.setMaxLength(255)
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(100)

        day = task.day if task else win.calendar.selected_date
        self.day_input = QDateEdit(QDate(day.year, day.month, day.day))
        self.day_input.setCalendarPopup(True)
        self.day_input.setDisplayFormat("dd.MM.yyyy")
        self.time_input = QTimeEdit(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm")

        self.difficulty_input = QComboBox()
        for value, label in ((1, "Легка"), (2, "Середня"), (3, "Складна")):
            self.difficulty_input.addItem(label, value)

        if task:
            self.title_input.setText(task.title)
            self.description_input.setPlainText(getattr(task, "description", "") or "")
            task_time = task.time
            self.time_input.setTime(QTime(task_time.hour, task_time.minute))
            index = self.difficulty_input.findData(task.difficulty)
            if index >= 0:
                self.difficulty_input.setCurrentIndex(index)

        self.photos_btn = QPushButton("Вибрати фото")
        self.photos_btn.clicked.connect(self.select_photos)
        fields.addRow("Назва", self.title_input)
        fields.addRow("Опис", self.description_input)
        fields.addRow("Дата виконання", self.day_input)
        fields.addRow("Час виконання", self.time_input)
        fields.addRow("Складність", self.difficulty_input)
        fields.addRow("Фото", self.photos_btn)

        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        layout.addStretch()

        buttons = QHBoxLayout()
        if task:
            self.delete_btn = QPushButton("Видалити")
            self.delete_btn.setObjectName("taskDeleteButton")
            self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.delete_btn.clicked.connect(self.delete_task)
            buttons.addWidget(self.delete_btn)
        buttons.addStretch()
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(win.close_task_form)
        self.save_btn = QPushButton("Зберегти" if task else "Створити")
        self.save_btn.clicked.connect(self.save_task)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(self.save_btn)
        layout.addLayout(buttons)

    def select_photos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Вибрати фото", "", "Зображення (*.png *.jpg *.jpeg *.webp *.bmp *.gif)"
        )
        if files:
            self.photos = files
            self.photos_btn.setText(f"Вибрано фото: {len(files)}")

    def delete_task(self):
        answer = QMessageBox.question(
            self, "Видалення завдання", f"Видалити завдання «{self.task.title}»?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_task(self.task.pk)
        except DatabaseError:
            self.error_label.setText("Не вдалося видалити завдання з бази даних.")
            return

        self.win.calendar.select_date(self.task.day)
        self.win.close_task_form()

    def save_task(self):
        if not self.title_input.text().strip():
            self.error_label.setText("Вкажіть назву завдання.")
            self.title_input.setFocus()
            return

        data = {
            "title": self.title_input.text(),
            "description": self.description_input.toPlainText(),
            "day": self.day_input.date().toPyDate(),
            "time": self.time_input.time().toPyTime().replace(second=0, microsecond=0),
            "difficulty": self.difficulty_input.currentData(),
        }

        try:
            if self.task is None:
                data["photos"] = self.photos
                task = create_task(data)
            else:
                if self.photos:  # нові фото додаємо лише якщо їх вибрали
                    data["photos"] = self.photos
                task = update_task(self.task.pk, data)
        except ValidationError as error:
            self.error_label.setText(" ".join(error.messages))
            return
        except DatabaseError:
            self.error_label.setText("Не вдалося зберегти завдання в базі даних.")
            return

        self.win.calendar.select_date(task.day)
        self.win.close_task_form()

    def apply_theme(self, theme, accent):
        self.setStyleSheet(f"""
            QLabel {{
                color: {theme['foreground']};
                background: transparent;
            }}

            QLabel#taskTitle {{
                font-size: 20px;
                font-weight: bold;
            }}

            QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QComboBox {{
                background-color: {theme['field']};
                color: {theme['foreground']};
                border: 1px solid {theme['border']};
                border-radius: 9px;
                padding: 6px 10px;
            }}

            QPushButton {{
                background-color: {accent['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 14px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: {accent['hover']};
            }}

            QPushButton#taskDeleteButton {{
                background-color: #dc2626;
            }}

            QPushButton#taskDeleteButton:hover {{
                background-color: #b91c1c;
            }}

            QPushButton#taskBackButton {{
                background-color: {theme['field']};
                border: 1px solid {theme['border']};
                border-radius: 21px;
                padding: 0;
            }}

            QPushButton#taskBackButton:hover {{
                background-color: {accent['primary']};
                border-color: {accent['primary']};
            }}
        """)

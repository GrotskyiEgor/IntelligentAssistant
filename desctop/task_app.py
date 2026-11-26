from django.core.exceptions import ValidationError
from django.db import DatabaseError
from PyQt6.QtCore import QDate, QTime, Qt
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTimeEdit, QVBoxLayout,
)

from db_response.tasks import create_task


class TaskForm(QFrame):
    def __init__(self, win):
        super().__init__()
        self.win = win
        self.photos = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Створення завдання")
        title.setObjectName("taskTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        fields = QFormLayout()
        fields.setSpacing(12)
        layout.addLayout(fields)

        self.title_input = QLineEdit()
        self.title_input.setMaxLength(255)
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(100)

        day = win.calendar.selected_date
        self.day_input = QDateEdit(QDate(day.year, day.month, day.day))
        self.day_input.setCalendarPopup(True)
        self.day_input.setDisplayFormat("dd.MM.yyyy")
        self.time_input = QTimeEdit(QTime.currentTime())
        self.time_input.setDisplayFormat("HH:mm")

        self.difficulty_input = QComboBox()
        for value, label in ((1, "Легка"), (2, "Середня"), (3, "Складна")):
            self.difficulty_input.addItem(label, value)

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
        buttons.addStretch()
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(win.close_task_form)
        self.save_btn = QPushButton("Створити")
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

    def save_task(self):
        if not self.title_input.text().strip():
            self.error_label.setText("Вкажіть назву завдання.")
            self.title_input.setFocus()
            return

        try:
            task = create_task({
                "title": self.title_input.text(),
                "description": self.description_input.toPlainText(),
                "day": self.day_input.date().toPyDate(),
                "time": self.time_input.time().toPyTime().replace(second=0, microsecond=0),
                "difficulty": self.difficulty_input.currentData(),
                "photos": self.photos,
            })
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
        """)

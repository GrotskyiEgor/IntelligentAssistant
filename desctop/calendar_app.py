import calendar as calendar_lib
import datetime

from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtWidgets import *

from hPyT import title_bar_color
from theme import get_theme_colors


MONTHS = (
    "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
    "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень",
)

WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд")


class CreateTaskDialog(QDialog):
    task_saved = pyqtSignal(dict)

    def __init__(self, date, parent=None):
        super().__init__(parent)
        self.date = date
        self.setWindowTitle("Create Task")
        self.setModal(True)
        self.setMinimumWidth(380)

        theme = getattr(parent, "theme", None)
        accent = getattr(parent, "accent", None)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("Create Task")
        header.setObjectName("taskHeader")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        date_label = QLabel(f"{date.day:02d}.{date.month:02d}.{date.year}")
        date_label.setObjectName("taskDate")
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(date_label)

        form = QFormLayout()
        form.setVerticalSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Title")

        self.type_input = QComboBox()
        self.type_input.addItems(["Навчання", "Робота", "Особисте", "Інше"])

        self.start_input = QTimeEdit(QTime(8, 0))
        self.start_input.setDisplayFormat("HH:mm")

        self.end_input = QTimeEdit(QTime(9, 0))
        self.end_input.setDisplayFormat("HH:mm")

        self.description_input = QPlainTextEdit()
        self.description_input.setPlaceholderText("Desc")
        self.description_input.setFixedHeight(90)

        form.addRow("Title", self.title_input)
        form.addRow("Type", self.type_input)
        form.addRow("Start", self.start_input)
        form.addRow("End", self.end_input)
        form.addRow("Desc", self.description_input)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Create task")
        save_btn.clicked.connect(self.save)

        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

        if theme and accent:
            self.setStyleSheet(f"""
                QDialog {{ background: {theme['window']}; color: {theme['foreground']}; font-size: 14px; }}
                QLabel {{ background: transparent; color: {theme['foreground']}; }}
                QLabel#taskHeader {{ font-size: 18px; font-weight: bold; }}
                QLabel#taskDate {{ color: {theme['muted']}; font-size: 12px; }}
                QLineEdit, QComboBox, QTimeEdit, QPlainTextEdit {{
                    background: {theme['field']};
                    color: {theme['foreground']};
                    border: 1px solid {theme['border']};
                    border-radius: 8px;
                    padding: 6px 8px;
                }}
                QComboBox QAbstractItemView {{
                    background: {theme['field']};
                    color: {theme['foreground']};
                    selection-background-color: {accent['primary']};
                }}
                QPushButton {{
                    background: {accent['primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 9px 18px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background: {accent['hover']}; }}
                QPushButton#cancelBtn {{
                    background: {theme['field']};
                    color: {theme['foreground']};
                    border: 1px solid {theme['border']};
                }}
                QPushButton#cancelBtn:hover {{ background: {theme['border']}; }}
            """)

    def save(self):
        task = {
            "date": f"{self.date.day:02d}.{self.date.month:02d}.{self.date.year}",
            "title": self.title_input.text().strip(),
            "type": self.type_input.currentText(),
            "start": self.start_input.time().toString("HH:mm"),
            "end": self.end_input.time().toString("HH:mm"),
            "description": self.description_input.toPlainText().strip(),
        }
        self.task_saved.emit(task)
        self.accept()


class CalendarWindow(QWidget):
    def __init__(self, win):
        super().__init__()
        self.win = win

        today = datetime.date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date = None
        self.day_buttons = []

        self.setWindowTitle("Календар")
        self.setFixedSize(440, 660)
        self.setWindowFlags(
            Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.year_input = QLineEdit(str(self.current_year))
        self.year_input.setPlaceholderText("Рік")
        self.year_input.setFixedHeight(40)
        self.year_input.setFixedWidth(120)
        self.year_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.year_input.textChanged.connect(self.on_year_changed)

        self.month_label = QLabel(MONTHS[self.current_month - 1])
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prev_btn = QPushButton("<")
        self.next_btn = QPushButton(">")
        self.prev_btn.setFixedSize(40, 40)
        self.next_btn.setFixedSize(40, 40)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_month)
        self.next_btn.clicked.connect(self.next_month)

        header_layout.addWidget(self.year_input)
        header_layout.addWidget(self.month_label, 1)
        header_layout.addWidget(self.prev_btn)
        header_layout.addWidget(self.next_btn)
        layout.addWidget(header)

        self.calendar_frame = QFrame()
        self.calendar_frame.setObjectName("calendarFrame")
        calendar_layout = QVBoxLayout(self.calendar_frame)
        calendar_layout.setContentsMargins(12, 12, 12, 12)
        calendar_layout.setSpacing(6)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(4)
        calendar_layout.addLayout(self.grid_layout)
        layout.addWidget(self.calendar_frame, 3)

        bottom = QFrame()
        bottom.setObjectName("dayFrame")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(12, 12, 12, 12)
        bottom_layout.setSpacing(10)

        date_header = QHBoxLayout()
        date_header.setSpacing(8)

        self.day_title = QLabel("Обраний день")
        self.day_title.setFixedHeight(40)
        self.day_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.full_date_label = QLabel()
        self.full_date_label.setFixedHeight(40)
        self.full_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        date_header.addWidget(self.day_title, 3)
        date_header.addWidget(self.full_date_label, 2)
        bottom_layout.addLayout(date_header)

        self.events_frame = QFrame()
        self.events_frame.setObjectName("eventsFrame")
        self.events_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        events_layout = QVBoxLayout(self.events_frame)
        events_layout.setContentsMargins(0, 0, 0, 0)

        self.empty_label = QLabel("Подій поки немає")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        events_layout.addWidget(self.empty_label)

        bottom_layout.addWidget(self.events_frame, 1)

        self.create_btn = QPushButton("Create")
        self.create_btn.setFixedHeight(42)
        self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_btn.clicked.connect(self.open_create_dialog)
        self.create_btn.hide()
        bottom_layout.addWidget(self.create_btn)

        layout.addWidget(bottom, 2)

        self.build_grid()
        self.update_full_date()
        self.apply_theme()

    def build_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.day_buttons = []

        for column, name in enumerate(WEEKDAYS):
            label = QLabel(name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                f"QLabel {{ color: {self.theme['muted'] if getattr(self, 'theme', None) else '#a1a1aa'}; "
                f"background: transparent; border: none; font-size: 12px; font-weight: bold; padding: 0; }}"
            )
            self.grid_layout.addWidget(label, 0, column)

        month_calendar = calendar_lib.monthcalendar(self.current_year, self.current_month)

        for row, week in enumerate(month_calendar, start=1):
            for column, day in enumerate(week):
                if day == 0:
                    placeholder = QLabel()
                    placeholder.setStyleSheet("QLabel { background: transparent; border: none; }")
                    self.grid_layout.addWidget(placeholder, row, column)
                    continue

                button = QPushButton(str(day))
                button.setFixedSize(40, 40)
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                date = datetime.date(self.current_year, self.current_month, day)
                button.clicked.connect(lambda checked=False, value=date: self.select_date(value))
                self.grid_layout.addWidget(button, row, column)
                self.day_buttons.append((date, button))

        self.style_grid()

    def select_date(self, date):
        self.selected_date = date
        self.update_full_date()
        self.style_grid()

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.after_period_change()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.after_period_change()

    def after_period_change(self):
        self.set_year_text(str(self.current_year))
        self.month_label.setText(MONTHS[self.current_month - 1])
        self.move_selection()
        self.build_grid()
        self.update_full_date()

    def on_year_changed(self, text):
        text = text.strip()
        if not text.isdigit() or len(text) != 4:
            return
        year = int(text)
        if year == 0:
            return
        self.current_year = year
        self.move_selection()
        self.build_grid()
        self.update_full_date()

    def move_selection(self):
        if self.selected_date is None:
            return
        last_day = calendar_lib.monthrange(self.current_year, self.current_month)[1]
        day = min(self.selected_date.day, last_day)
        self.selected_date = datetime.date(self.current_year, self.current_month, day)

    def set_year_text(self, text):
        self.year_input.blockSignals(True)
        self.year_input.setText(text)
        self.year_input.blockSignals(False)

    def update_full_date(self):
        if self.selected_date is None:
            self.full_date_label.setText("")
            self.create_btn.hide()
            return
        date = self.selected_date
        self.full_date_label.setText(f"{date.day:02d}.{date.month:02d}.{date.year}")
        self.create_btn.show()

    def open_create_dialog(self):
        if self.selected_date is None:
            return
        dialog = CreateTaskDialog(self.selected_date, self)
        dialog.task_saved.connect(self.create_task)
        dialog.exec()

    def create_task(self, task):
        # CreateTask
        print(task)

    def style_grid(self):
        theme = getattr(self, "theme", None)
        accent = getattr(self, "accent", None)
        button_text = getattr(self, "button_text", "white")
        today = datetime.date.today()

        for date, button in self.day_buttons:
            if date == self.selected_date:
                button.setStyleSheet(
                    f"QPushButton {{ background-color: {accent['primary'] if accent else '#7565f7'}; "
                    f"color: {button_text}; border: none; border-radius: 10px; font-weight: bold; }}"
                )
            elif date == today and theme and accent:
                button.setStyleSheet(
                    f"QPushButton {{ background-color: {theme['field']}; "
                    f"color: {theme['foreground']}; border: 2px solid {accent['primary']}; "
                    f"border-radius: 10px; font-weight: bold; }}"
                )
            elif theme:
                button.setStyleSheet(
                    f"QPushButton {{ background-color: {theme['field']}; "
                    f"color: {theme['foreground']}; border: none; border-radius: 10px; }}"
                    f"QPushButton:hover {{ background-color: {theme['border']}; }}"
                )
            else:
                button.setStyleSheet(
                    "QPushButton { background-color: #27272a; color: #f4f4f5; border: none; border-radius: 10px; }"
                    "QPushButton:hover { background-color: #3f3f46; }"
                )

    def apply_theme(self, settings=None):
        settings = {**self.win.preferences, **(settings or {})}
        self.theme, self.accent = get_theme_colors(settings)
        button_text = "white" if settings.get("accent") in {"purple", "blue", "lime", "orange"} else "#2d2d2d"
        self.button_text = button_text

        self.setStyleSheet(
            f"background: {self.theme['window']}; color: {self.theme['foreground']}; font-size: 14px;"
        )
        title_bar_color.set(self, color=self.theme["window"])

        field_style = f"""
            QLineEdit, QLabel {{
                background: {self.theme['field']};
                color: {self.theme['foreground']};
                border: 1px solid {self.theme['border']};
                border-radius: 9px;
                padding: 0 11px;
            }}
        """
        self.year_input.setFixedHeight(40)
        self.year_input.setStyleSheet(field_style)
        self.day_title.setFixedHeight(40)
        self.day_title.setStyleSheet(field_style)
        self.full_date_label.setFixedHeight(40)
        self.full_date_label.setStyleSheet(field_style)

        self.month_label.setStyleSheet(
            f"QLabel {{ color: {self.theme['foreground']}; background: transparent; "
            f"border: none; font-size: 16px; font-weight: bold; padding: 0; }}"
        )

        for button in (self.prev_btn, self.next_btn):
            button.setFixedSize(40, 40)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.accent['primary']};
                    color: {button_text};
                    border: none;
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.accent['hover']};
                }}
            """)

        self.calendar_frame.setStyleSheet(
            f"QFrame#calendarFrame {{ background-color: {self.theme['panel']}; border-radius: 16px; }}"
        )

        for label in self.calendar_frame.findChildren(QLabel):
            if label.text() in WEEKDAYS:
                label.setStyleSheet(
                    f"QLabel {{ color: {self.theme['muted']}; background: transparent; "
                    f"border: none; font-size: 12px; font-weight: bold; padding: 0; }}"
                )

        bottom = self.events_frame.parent()
        bottom.setStyleSheet(
            f"QFrame#dayFrame {{ background-color: {self.theme['panel']}; border-radius: 16px; }}"
        )
        self.events_frame.setStyleSheet(
            f"QFrame#eventsFrame {{ background-color: {self.theme['window']}; border-radius: 12px; }}"
        )
        self.empty_label.setStyleSheet(
            f"QLabel {{ color: {self.theme['muted']}; background: transparent; border: none; }}"
        )

        self.create_btn.setFixedHeight(42)
        self.create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent['primary']};
                color: {button_text};
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.accent['hover']};
            }}
        """)

        self.style_grid()

    def closeEvent(self, event):
        self.win.calendar = None
        event.accept()

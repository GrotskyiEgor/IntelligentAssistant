import calendar as calendar_lib
import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from theme import get_theme_colors


MONTHS = (
    "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
    "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень",
)

WEEKDAYS = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд")

CELL = 30
SPACING = 3
HEADER_H = 34


class CalendarPanel(QWidget):
    """Календар для вбудови в ліву панель (раніше це було окреме вікно CalendarWindow)."""

    date_selected = pyqtSignal(object)

    def __init__(self, win):
        super().__init__()
        self.win = win

        today = datetime.date.today()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date = today
        self.day_buttons = []

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        self.year_input = QLineEdit(str(self.current_year))
        self.year_input.setPlaceholderText("Рік")
        self.year_input.setFixedSize(64, HEADER_H)
        self.year_input.setMaxLength(4)
        self.year_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.year_input.textChanged.connect(self.on_year_changed)

        self.month_label = QLabel(MONTHS[self.current_month - 1])
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prev_btn = QPushButton("<")
        self.next_btn = QPushButton(">")
        for button in (self.prev_btn, self.next_btn):
            button.setFixedSize(HEADER_H, HEADER_H)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_month)
        self.next_btn.clicked.connect(self.next_month)

        header_layout.addWidget(self.year_input)
        header_layout.addWidget(self.month_label, 1)
        header_layout.addWidget(self.prev_btn)
        header_layout.addWidget(self.next_btn)
        layout.addWidget(header)

        self.calendar_frame = QFrame()
        self.calendar_frame.setObjectName("calendarFrame")
        self.calendar_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        calendar_layout = QVBoxLayout(self.calendar_frame)
        calendar_layout.setContentsMargins(8, 8, 8, 8)

        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(SPACING)
        self.grid_layout.setRowMinimumHeight(0, 20)
        for row in range(1, 7):
            self.grid_layout.setRowMinimumHeight(row, CELL)
        calendar_layout.addLayout(self.grid_layout)
        layout.addWidget(self.calendar_frame)

        self.bottom_frame = QFrame()
        self.bottom_frame.setObjectName("dayFrame")
        bottom_layout = QVBoxLayout(self.bottom_frame)
        bottom_layout.setContentsMargins(8, 8, 8, 8)
        bottom_layout.setSpacing(8)

        self.day_title = QLabel("Обраний день")
        self.day_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_title.setFixedHeight(32)

        self.full_date_label = QLabel()
        self.full_date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.full_date_label.setFixedHeight(32)

        bottom_layout.addWidget(self.day_title)
        bottom_layout.addWidget(self.full_date_label)

        self.events_frame = QFrame()
        self.events_frame.setObjectName("eventsFrame")
        self.events_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        events_layout = QVBoxLayout(self.events_frame)
        events_layout.setContentsMargins(0, 0, 0, 0)

        self.empty_label = QLabel("Подій поки немає")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        events_layout.addWidget(self.empty_label)

        bottom_layout.addWidget(self.events_frame, 1)
        layout.addWidget(self.bottom_frame, 1)

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

        muted = self.theme["muted"] if getattr(self, "theme", None) else "#a1a1aa"

        for column, name in enumerate(WEEKDAYS):
            label = QLabel(name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedSize(CELL, 20)
            label.setStyleSheet(
                f"QLabel {{ color: {muted}; background: transparent; border: none; "
                f"font-size: 12px; font-weight: bold; padding: 0; }}"
            )
            self.grid_layout.addWidget(label, 0, column)

        for row, week in enumerate(calendar_lib.monthcalendar(self.current_year, self.current_month), start=1):
            for column, day in enumerate(week):
                if day == 0:
                    continue

                button = QPushButton(str(day))
                button.setFixedSize(CELL, CELL)
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
        self.date_selected.emit(date)

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

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.prev_month()
        elif delta < 0:
            self.next_month()
        event.accept()

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
        last_day = calendar_lib.monthrange(self.current_year, self.current_month)[1]
        day = min(self.selected_date.day, last_day)
        self.selected_date = datetime.date(self.current_year, self.current_month, day)

    def set_year_text(self, text):
        self.year_input.blockSignals(True)
        self.year_input.setText(text)
        self.year_input.blockSignals(False)

    def update_full_date(self):
        date = self.selected_date
        self.full_date_label.setText(f"{date.day:02d}.{date.month:02d}.{date.year}")

    def style_grid(self):
        theme = getattr(self, "theme", None)
        accent = getattr(self, "accent", None)
        button_text = getattr(self, "button_text", "white")
        today = datetime.date.today()

        for date, button in self.day_buttons:
            if date == self.selected_date:
                button.setStyleSheet(
                    f"QPushButton {{ background-color: {accent['primary'] if accent else '#7565f7'}; "
                    f"color: {button_text}; border: none; border-radius: 8px; font-size: 13px; font-weight: bold; }}"
                )
            elif date == today and theme and accent:
                button.setStyleSheet(
                    f"QPushButton {{ background-color: {theme['field']}; "
                    f"color: {theme['foreground']}; border: 2px solid {accent['primary']}; "
                    f"border-radius: 8px; font-size: 13px; font-weight: bold; }}"
                )
            elif theme:
                button.setStyleSheet(
                    f"QPushButton {{ background-color: {theme['field']}; "
                    f"color: {theme['foreground']}; border: none; border-radius: 8px; font-size: 13px; }}"
                    f"QPushButton:hover {{ background-color: {theme['border']}; }}"
                )
            else:
                button.setStyleSheet(
                    "QPushButton { background-color: #27272a; color: #f4f4f5; border: none; border-radius: 8px; font-size: 13px; }"
                    "QPushButton:hover { background-color: #3f3f46; }"
                )

    def apply_theme(self, settings=None):
        settings = {**self.win.preferences, **(settings or {})}
        self.theme, self.accent = get_theme_colors(settings)
        button_text = "white" if settings.get("accent") in {"purple", "blue", "lime", "orange"} else "#2d2d2d"
        self.button_text = button_text

        self.setStyleSheet(
            f"background: transparent; color: {self.theme['foreground']}; font-size: 14px;"
        )

        field_style = f"""
            QLineEdit, QLabel {{
                background: {self.theme['field']};
                color: {self.theme['foreground']};
                border: 1px solid {self.theme['border']};
                border-radius: 9px;
                padding: 0 6px;
            }}
        """
        self.year_input.setStyleSheet(field_style)
        self.day_title.setStyleSheet(field_style)
        self.full_date_label.setStyleSheet(field_style)

        self.month_label.setStyleSheet(
            f"QLabel {{ color: {self.theme['foreground']}; background: transparent; "
            f"border: none; font-size: 16px; font-weight: bold; padding: 0; }}"
        )

        for button in (self.prev_btn, self.next_btn):
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.accent['primary']};
                    color: {button_text};
                    border: none;
                    border-radius: 9px;
                    font-size: 16px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.accent['hover']};
                }}
            """)

        self.calendar_frame.setStyleSheet(
            f"QFrame#calendarFrame {{ background-color: {self.theme['window']}; border-radius: 14px; }}"
        )
        self.bottom_frame.setStyleSheet(
            f"QFrame#dayFrame {{ background-color: {self.theme['window']}; border-radius: 14px; }}"
        )
        self.events_frame.setStyleSheet(
            f"QFrame#eventsFrame {{ background-color: {self.theme['panel']}; border-radius: 10px; }}"
        )
        self.empty_label.setStyleSheet(
            f"QLabel {{ color: {self.theme['muted']}; background: transparent; border: none; }}"
        )

        for label in self.calendar_frame.findChildren(QLabel):
            if label.text() in WEEKDAYS:
                label.setStyleSheet(
                    f"QLabel {{ color: {self.theme['muted']}; background: transparent; "
                    f"border: none; font-size: 12px; font-weight: bold; padding: 0; }}"
                )

        self.style_grid()
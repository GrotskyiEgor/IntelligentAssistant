import PyQt6 as qt
import sys, os, subprocess, json, re

from hPyT import *
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QProcess, QProcessEnvironment

from settings_app import SettingsWindow
from theme import get_theme_colors


class MainWindow(QMainWindow):
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

        menubar = QMenuBar()
        menubar.setStyleSheet("""
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
            }

            QMenu::item:selected {
                background-color: #3b82f6;
            }
        """)

        menu = menubar.addMenu("Асистент")
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.NoDropShadowWindowHint | Qt.WindowType.FramelessWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        settings_act = menu.addAction("Налаштування")
        settings_act.triggered.connect(self.open_settings)

        exit_act = menu.addAction("Вихід")
        exit_act.triggered.connect(self.close)

        self.center = QWidget()
        self.center.setObjectName("centralBg")
        self.center.setStyleSheet("QWidget#centralBg { background: #181818; }")
        self.setCentralWidget(self.center)

        self.main_layout = QHBoxLayout(self.center)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setMenuWidget(menubar)

        self.create_main_panel()
        self.create_chat()
        self.create_command_panel()

        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.apply_theme(self.preferences)

    def apply_theme(self, settings):
        theme, accent = get_theme_colors(settings)
        dark = settings.get("theme", "dark") == "dark"
        palette = {**theme["replace"], **accent["replace"]}
        self.preferences = dict(settings)
        button_text = "white" if dark else "black"
        color_pattern = re.compile("|".join(re.escape(color) for color in palette), re.IGNORECASE)
        
        for widget in [self, *self.findChildren(QWidget)]:
            if not widget.property("baseStyleSheet"):
                widget.setProperty("baseStyleSheet", widget.styleSheet())
            style = widget.property("baseStyleSheet")
            style = color_pattern.sub(lambda match: palette[match.group(0).lower()], style)
            widget.setStyleSheet(style)
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(f"{widget.styleSheet()}\nQPushButton {{ color: {button_text}; }}")

        self.main_panel_background_frame.setObjectName("mainPanelBackground")
        self.commands_frame.setObjectName("commandsFrame")

        for frame, selector in (
            (self.main_panel_background_frame, "QFrame#mainPanelBackground"),
            (self.messages_frame_back, "QFrame#messages_frame_back"),
            (self.commands_frame, "QFrame#commandsFrame"),
        ):
            frame.setStyleSheet(
                f"{frame.styleSheet()}\n"
                f"{selector} {{ background-color: {theme['panel']}; border-radius: 16px; }}"
            )
            
        if self.settings:
            self.settings.apply_theme(settings, sync_main=False)

        self.setStyleSheet(f"background: {theme['window']}; color: {theme['foreground']};")
        title_bar_color.set(self, color=theme["window"])

    def create_main_panel(self):
        self.main_panel_background_frame = QFrame()
        self.main_panel_background_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.main_panel_background_frame.setFixedSize(270, 660)

        self.main_panel_background_frame.setStyleSheet("""
            QFrame#mainPanelBackground {
                background-color: #292929;
                border-radius: 16px;
            }
        """)

        self.main_panel_background_frame.setContentsMargins(10, 10, 10, 10)

        self.main_panel_title = QLabel("Повідомлення")
        self.main_panel_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_panel_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
                font-size: 20px;
                font-weight: bold;
            }
        """)

        self.messages_layout = QVBoxLayout(self.main_panel_background_frame)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(12)

        self.messages_layout.addWidget(self.main_panel_title)
        self.main_layout.addWidget(self.main_panel_background_frame)

    def create_chat(self):
        self.messages_frame_back = QFrame()
        self.messages_frame_back.setFrameShape(QFrame.Shape.NoFrame)
        self.messages_frame_back.setFixedSize(705, 660)
        self.messages_frame_back.setObjectName("messages_frame_back")

        self.messages_frame_back.setStyleSheet("""
            QFrame#messages_frame_back {
                background-color: #292929;
                border-radius: 16px;
            }
        """)

        self.messages_frame_back_layout = QHBoxLayout(self.messages_frame_back)
        self.messages_frame_back_layout.setContentsMargins(0, 0, 0, 0)

        self.messages_frame = QFrame()
        self.messages_frame.setObjectName("messages_frame")
        self.messages_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.messages_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.messages_frame.setStyleSheet("""
            QFrame#messages_frame {
                background-color: transparent;
                border: none;
            }

            QLabel {
                color: #ffffff;
                background: transparent;
                border: none;
            }

            QScrollArea {
                background: transparent;
                border: none;
            }

            QWidget#messages_container {
                background: transparent;
                border: none;
            }

            QFrame#messageBubbleSent {
                background-color: #0088cc;
                border-radius: 14px;
            }

            QFrame#messageBubbleReceived {
                background-color: #3b3b3b;
                border-radius: 14px;
            }

            QLabel#messageSender {
                color: #c9e8f7;
                font-size: 12px;
                font-weight: bold;
            }

            QLabel#messageText {
                color: #ffffff;
                font-size: 15px;
            }
        """)

        self.messages_layout = QVBoxLayout(self.messages_frame)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(12)

        self.title = QLabel("Повідомлення")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        self.title.setStyleSheet("""
            color: #ffffff;
            background: transparent;
            font-size: 20px;
            font-weight: bold;
            padding-bottom: 5px;
        """)

        self.messages_layout.addWidget(
            self.title,
            alignment=Qt.AlignmentFlag.AlignTop
        )

        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setFrameShape(QFrame.Shape.NoFrame)
        self.messages_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.messages_area.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )
        self.messages_area.viewport().setAutoFillBackground(False)
        self.messages_area.viewport().setStyleSheet("background: transparent;")

        messages_container = QWidget()
        messages_container.setObjectName("messages_container")
        messages_container.setStyleSheet("background: transparent;")

        self.messages_container_layout = QVBoxLayout(messages_container)
        self.messages_container_layout.setContentsMargins(0, 0, 0, 0)
        self.messages_container_layout.setSpacing(12)
        self.messages_container_layout.addStretch()

        self.messages_area.setWidget(messages_container)
        self.messages_layout.addWidget(self.messages_area)

        self.create_input()

        self.messages_layout.addWidget(
            self.input_frame,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.messages_frame_back_layout.addWidget(self.messages_frame)

        self.main_layout.addWidget(self.messages_frame_back)

    def create_input(self):
        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        self.input_frame.setFixedWidth(650)
        self.input_frame.setMinimumHeight(60)

        self.input_frame.setStyleSheet("""
            QFrame#inputFrame {
                background-color: #2a2a2e;
                border-radius: 20px;
                border: 1px solid #4a4a4a;
            }
        """)

        input_layout = QHBoxLayout(self.input_frame)
        input_layout.setContentsMargins(15, 5, 7, 5)
        input_layout.setSpacing(8)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Напишіть повідомлення...")

        self.message_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                color: white;
                font-size: 16px;
            }
        """)

        self.message_input.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("▶")
        self.send_btn.setFixedSize(45, 45)

        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #7565f7;
                color: black;
                border-radius: 14px;
                font-size: 32px;
            }

            QPushButton:hover {
                background-color: #6152de;
            }
        """)

        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)

    def send_message(self):
        text = self.message_input.text().strip()

        if not text:
            return

        self.add_message("Ви", text)

        if self.assistant_process is None:
            self.add_message("Помічник", "Помічник не запущений.")
            self.message_input.clear()
            return

        self.assistant_process.write(
            (text + "\n").encode("utf-8")
        )

        self.assistant_process.waitForBytesWritten(1000)

        self.message_input.clear()

    def add_message(self, sender, text):
        is_outgoing = sender == "Ви"

        row = QWidget()
        row.setStyleSheet("background: transparent;")

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        bubble = QFrame()

        bubble.setObjectName(
            "messageBubbleSent" if is_outgoing else "messageBubbleReceived"
        )

        bubble.setStyleSheet(
            f"background-color: {'#7565f7' if self.preferences.get('accent', 'purple') == 'purple' else '#4f7cff'}; border-radius: 14px;"
            if is_outgoing
            else "background-color: #454545; border-radius: 14px;"
        )

        bubble.setMaximumWidth(440 if is_outgoing else 620)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(3)

        sender_label = QLabel(sender)
        sender_label.setObjectName("messageSender")

        safe_text = "\u200b".join(
            text[i:i + 25]
            for i in range(0, len(text), 25)
        )

        body = QLabel(safe_text)
        body.setObjectName("messageText")
        body.setWordWrap(True)
        body.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        body.setMaximumWidth(410 if is_outgoing else 590)

        bubble_layout.addWidget(sender_label)
        bubble_layout.addWidget(body)

        if is_outgoing:
            row_layout.addStretch(1)
            row_layout.addWidget(
                bubble,
                alignment=Qt.AlignmentFlag.AlignRight
            )
        else:
            row_layout.addWidget(
                bubble,
                alignment=Qt.AlignmentFlag.AlignLeft
            )
            row_layout.addStretch(1)

        self.messages_container_layout.insertWidget(
            self.messages_container_layout.count() - 1,
            row
        )

        QTimer.singleShot(
            0,
            lambda: self.messages_area.verticalScrollBar().setValue(
                self.messages_area.verticalScrollBar().maximum()
            )
        )

    def create_command_panel(self):
        self.commands_frame = QFrame()
        self.commands_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.commands_frame.setFixedSize(270, 660)
        self.commands_frame.setObjectName("commandsFrame")

        self.commands_frame.setStyleSheet("""
            QFrame#commandsFrame {
                background-color: #292929;
                border-radius: 16px;
            }

            QFrame#section_frame {
                background-color: #3a3a3a;
                border: none;
                border-radius: 16px;
            }

            QLabel {
                color: white;
                background: transparent;
                border: none;
            }

            QPushButton {
                background-color: #7565f7;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #3e68e8;
            }

            QPushButton:pressed {
                background-color: #1d4ed8;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
        """)

        self.commands_layout = QVBoxLayout(self.commands_frame)
        self.commands_layout.setContentsMargins(8, 8, 8, 8)
        self.commands_layout.setSpacing(10)

        assistant_frame = QFrame()
        assistant_frame.setObjectName("section_frame")
        assistant_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        assistant_layout = QVBoxLayout(assistant_frame)
        assistant_layout.setContentsMargins(10, 10, 10, 10)
        assistant_layout.setSpacing(10)

        self.commands_label = QLabel("Керування асистентом")
        self.commands_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.commands_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        self.start_btn = QPushButton("Почати", assistant_frame)
        self.start_btn.setFixedSize(220, 42)
        self.start_btn.clicked.connect(self.start_assintant)

        self.stop_btn = QPushButton("Зупинити", assistant_frame)
        self.stop_btn.setFixedSize(220, 42)
        self.stop_btn.clicked.connect(self.stop_assintant)

        self.restart_btn = QPushButton("Перезапустити", assistant_frame)
        self.restart_btn.setFixedSize(220, 42)
        self.restart_btn.clicked.connect(self.restart_assintant)

        assistant_layout.addWidget(
            self.commands_label,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        assistant_layout.addWidget(
            self.start_btn,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        assistant_layout.addWidget(
            self.stop_btn,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        assistant_layout.addWidget(
            self.restart_btn,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.commands_layout.addWidget(assistant_frame)

        groups_frame = QFrame()
        groups_frame.setObjectName("section_frame")
        groups_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        groups_layout = QVBoxLayout(groups_frame)
        groups_layout.setContentsMargins(10, 10, 10, 10)
        groups_layout.setSpacing(10)

        self.groups_label = QLabel("Групи")
        self.groups_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groups_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        self.group1_btn = QPushButton("Група 1", groups_frame)
        self.group1_btn.setFixedSize(105, 45)
        self.group1_btn.clicked.connect(self.group1_clicked)

        self.group2_btn = QPushButton("Група 2", groups_frame)
        self.group2_btn.setFixedSize(105, 45)
        self.group2_btn.clicked.connect(self.group2_clicked)

        groups_layout.addWidget(
            self.groups_label,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        groups_buttons_layout = QHBoxLayout()
        groups_buttons_layout.setSpacing(10)

        groups_buttons_layout.addWidget(
            self.group1_btn,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        groups_buttons_layout.addWidget(
            self.group2_btn,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        groups_layout.addLayout(groups_buttons_layout)

        self.commands_layout.addWidget(groups_frame)

        new_command_frame = QFrame()
        new_command_frame.setObjectName("section_frame")
        new_command_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        new_command_layout = QVBoxLayout(new_command_frame)
        new_command_layout.setContentsMargins(10, 10, 10, 10)
        new_command_layout.setSpacing(8)

        self.new_command_label = QLabel("Нова команда")
        self.new_command_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.new_command_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        self.new_command_btn = QPushButton(
            "Нова команда",
            new_command_frame
        )

        self.new_command_btn.setFixedSize(150, 45)

        new_command_layout.addWidget(
            self.new_command_label,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        new_command_layout.addWidget(
            self.new_command_btn,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.commands_layout.addWidget(new_command_frame)

        self.commands_layout.addStretch()

        self.main_layout.addWidget(self.commands_frame)

    def open_settings(self):
        self.settings = SettingsWindow(self)
        self.settings.show()

    def start_assintant(self):
        if self.assistant_process is not None:
            return

        self.assistant_process = QProcess(self)

        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        self.assistant_process.setProcessEnvironment(env)

        self.assistant_process.readyReadStandardOutput.connect(
            self.read_output
        )

        self.assistant_process.readyReadStandardError.connect(
            self.read_output
        )

        self.assistant_process.finished.connect(
            self.assistant_fineshed
        )

        self.assistant_process.setProcessChannelMode(
            QProcess.ProcessChannelMode.MergedChannels
        )

        python = sys.executable

        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        manage_py = os.path.join(
            base_dir,
            "assistant",
            "manage.py"
        )

        self.assistant_process.start(
            python,
            [manage_py, "run_assistant"]
        )

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)

    def stop_assintant(self, on_stopped=None):
        process = self.assistant_process

        if process is None:
            if on_stopped:
                on_stopped()
            return

        def _handle_finished(*args):
            try:
                process.finished.disconnect(_handle_finished)
            except (TypeError, RuntimeError):
                pass

            if on_stopped:
                on_stopped()

        process.finished.connect(_handle_finished)
        process.kill()

    def restart_assintant(self):
        if self.assistant_process is None:
            self.start_assintant()
            return

        self.restart_btn.setEnabled(False)

        self.stop_assintant(
            on_stopped=self.start_assintant
        )

    def group1_clicked(self):
        print("Натиснуто групу 1")

    def group2_clicked(self):
        print("Натиснуто групу 2")

    def read_output(self):
        data = self.assistant_process.readAllStandardOutput()

        text = bytes(data).decode(
            "utf-8",
            errors="replace"
        )

        if not text:
            return

        print(text, end="")

        for line in text.splitlines():
            line = line.strip()

            if line.startswith("ANSWER:"):
                answer = line[len("ANSWER:"):].strip()

                if answer:
                    self.add_message("Помічник", answer)

    def read_error(self):
        data = self.assistant_process.readAllStandardError()

        text = bytes(data).decode(
            "utf-8",
            errors="replace"
        )

        if text:
            print("ERROR:", text, end="")

    def assistant_fineshed(self, *args):
        print("Помічник завершив роботу.")

        if self.assistant_process is not None:
            self.assistant_process.deleteLater()
            self.assistant_process = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)

    def closeEvent(self, e):
        if self.assistant_process is not None:
            self.assistant_process.kill()
            self.assistant_process.waitForFinished(2000)

        if self.settings:
            self.settings.close()

        e.accept()
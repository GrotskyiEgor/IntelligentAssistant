import PyQt6 as qt
import sys, os, subprocess, json, re

from PyQt6.QtCore import QProcess, QProcessEnvironment
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer


from settings_app import SettingsWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.assistant_process = None
        self.settings = None

        self.setWindowTitle("Intelligent Voice Assistant")
        self.setMinimumSize(960, 540)
        self.setFixedSize(1280, 720)
        self.setStyleSheet("background: grey;")

        menubar = QMenuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                color: white;
                border: none;
                padding: 4px 8px;
                font-size: 15px;
                font-weight: bold;
            }

            QMenuBar::item {
                background-color: #2f2f2f;
                color: white;
                padding: 8px 16px;
                margin: 2px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }

            QMenuBar::item:selected {
                background-color: #3b82f6;
            }

            QMenu {
                background-color: #2f2f2f;
                color: white;
                border: 1px solid #4a4a4a;
                border-radius: 10px;
                padding: 5px;
            }

            QMenu::item {
                padding: 9px 25px;
                border-radius: 6px;
            }

            QMenu::item:selected {
                background-color: #3b82f6;
            }
        """)

        menu = menubar.addMenu("Асистент")

        settings_act = menu.addAction("Налаштування")
        settings_act.triggered.connect(self.open_settings)

        exit_act = menu.addAction("Вихід")
        exit_act.triggered.connect(self.close)

        self.center = QWidget()
        self.center.setObjectName("centralBg")
        self.center.setStyleSheet("QWidget#centralBg { background: grey; }")
        self.setCentralWidget(self.center)

        self.main_layout = QHBoxLayout(self.center)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setMenuWidget(menubar)

        self.create_main_panel()
        self.create_chat()
        self.create_command_panel()

        # self.main_layout.addStretch()

        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)

    def create_main_panel(self):
        self.main_panel_background_frame = QFrame()
        self.main_panel_background_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.main_panel_background_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.main_panel_background_frame.setFixedSize(270, 660)

        self.main_panel_background_frame.setStyleSheet("""
            QFrame {
                background-color: #2f2f2f;
                border-radius: 16px;
            }
        """)

        self.main_panel_background_frame.setContentsMargins(10, 10, 10, 10)


        self.main_panel_title = QLabel("Повідомлення")
        self.main_panel_title.setStyleSheet("""
            color: #ffffff;
            font-size: 20px;
            font-weight: bold;
            padding-bottom: 10px;
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
                background-color: #2f2f2f;
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
            }

            QScrollArea {
                background: transparent;
                border: none;
            }

            QWidget#messages_container {
                background: transparent;
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
        self.title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.title.setStyleSheet("""
            color: #ffffff;
            background: transparent;
            font-size: 20px;
            font-weight: bold;
            padding-bottom: 5px;
        """)
        self.messages_layout.addWidget(self.title, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

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
                background-color: #2f2f2f;
                border-radius: 24px;
                border: 1px solid #4a4a4a;
            }
        """)

        input_layout = QHBoxLayout(self.input_frame)
        input_layout.setContentsMargins(16, 8, 8, 8)
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

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 13px;
                font-size: 20px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)

    def send_message(self):
        text = self.message_input.text().strip()

        if not text:
            return

        self.add_message("Вы", text)

        if self.assistant_process is None:
            self.add_message("Ассистент", "Я не запущен.")
            self.message_input.clear()
            return

        self.assistant_process.write(
            (text + "\n").encode("utf-8")
        )
        self.assistant_process.waitForBytesWritten(1000)

        self.message_input.clear()

    def add_message(self, sender, text):
        is_outgoing = sender == "Вы"
        row = QWidget(self.messages_area.widget())
        row.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        row.setStyleSheet("background: transparent;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)

        bubble = QFrame()
        bubble.setObjectName(
            "messageBubbleSent" if is_outgoing else "messageBubbleReceived"
        )
        bubble.setStyleSheet(
            "background-color: #3b82f6; border-radius: 14px;"
            if is_outgoing
            else "background-color: #454545; border-radius: 14px;"
        )
        bubble.setMaximumWidth(440)
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(3)

        sender_label = QLabel(sender)
        sender_label.setObjectName("messageSender")
        body = QLabel(text)
        body.setObjectName("messageText")
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        body.setMaximumWidth(410)

        bubble_layout.addWidget(sender_label)
        bubble_layout.addWidget(body)

        if is_outgoing:
            row_layout.addStretch(1)
            row_layout.addWidget(bubble, alignment=Qt.AlignmentFlag.AlignRight)
        else:
            row_layout.addWidget(bubble, alignment=Qt.AlignmentFlag.AlignLeft)
            row_layout.addStretch(1)

        self.messages_container_layout.insertWidget(
            self.messages_container_layout.count() - 1,
            row
        )

        QTimer.singleShot(0, lambda: self.messages_area.verticalScrollBar().setValue(
            self.messages_area.verticalScrollBar().maximum()
        ))

    def create_command_panel(self):
        self.commands_frame = QFrame()
        self.commands_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.commands_frame.setFrameShape(QFrame.Shape.NoFrame)
        self.commands_frame.setFixedSize(270, 660)

        self.commands_frame.setStyleSheet("""
            QFrame {
                background-color: #2f2f2f;
                border-radius: 16px;
            }
        """)

        self.commands_frame.setStyleSheet("""
            QFrame {
                background-color: #2f2f2f;
                border-radius: 16px;
            }

            QFrame#section_frame {
                background-color: #2f2f2f;
                border-radius: 16px;
            }

            QLabel {
                color: white;
            }

            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563eb;
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
        self.commands_layout.setContentsMargins(5, 5, 5, 5)
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
        self.commands_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.commands_label.setStyleSheet("""
            color: white;
            font-size: 20px;
            font-weight: bold;
            padding-bottom: 5px;
        """)

        self.start_btn = QPushButton("Почати", assistant_frame)
        self.start_btn.setFixedSize(220, 45)
        self.start_btn.clicked.connect(self.start_assintant)

        self.stop_btn = QPushButton("Зупинити", assistant_frame)
        self.stop_btn.setFixedSize(220, 45)
        self.stop_btn.clicked.connect(self.stop_assintant)

        self.restart_btn = QPushButton("Перезапустити", assistant_frame)
        self.restart_btn.setFixedSize(220, 45)
        self.restart_btn.clicked.connect(self.restart_assintant)

        assistant_layout.addWidget(self.commands_label)

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
        self.groups_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.groups_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding-bottom: 5px;
        """)

        self.group1_btn = QPushButton("Група 1", groups_frame)
        self.group1_btn.setFixedSize(120, 45)
        self.group1_btn.clicked.connect(self.group1_clicked)

        self.group2_btn = QPushButton("Група 2", groups_frame)
        self.group2_btn.setFixedSize(120, 45)
        self.group2_btn.clicked.connect(self.group2_clicked)

        groups_layout.addWidget(self.groups_label)

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
        new_command_layout.setContentsMargins(15, 15, 15, 15)

        self.new_command_btn = QPushButton(
            "Нова команда",
            new_command_frame
        )
        self.new_command_btn.setFixedSize(150, 45)

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

        self.assistant_process.readyReadStandardOutput.connect(self.read_output)
        self.assistant_process.readyReadStandardError.connect(self.read_output)
        self.assistant_process.finished.connect(self.assistant_fineshed)
        self.assistant_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        python = sys.executable
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        manage_py = os.path.join(base_dir, "assistant", "manage.py")

        self.assistant_process.start(python, [manage_py, "run_assistant"])

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)

    def stop_assintant(self, on_stopped=None):
        process = self.assistant_process
        if process is None:
            if on_stopped:
                on_stopped()
            return

        def _handle_finished():
            process.finished.disconnect(_handle_finished)
            if on_stopped:
                on_stopped()

        process.finished.connect(_handle_finished)
        process.kill()

    def restart_assintant(self):
        if self.assistant_process is None:
            self.start_assintant()
            return

        self.restart_btn.setEnabled(False)
        self.stop_assintant(on_stopped=self.start_assintant)

    def group1_clicked(self):
        print("Натиснуто Група 1")

    def group2_clicked(self):
        print("Натиснуто Група 2")

    def closeEvent(self, event):
        if self.assistant_process is not None:
            self.assistant_process.kill()
            self.assistant_process.waitForFinished(2000)

        if self.settings:
            self.settings.close()

        event.accept()
        
    def read_output(self):
        data = self.assistant_process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")

        if not text:
            return

        print(text, end="")

        for line in text.splitlines():
            line = line.strip()

            if line.startswith("ANSWER:"):
                answer = line[len("Відповідь:"):].strip()

                if answer:
                    self.add_message("Ассистент", answer)

    def read_error(self):
        data = self.assistant_process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="replace")

        if text:
            print("ERROR:", text, end="")

    def assistant_fineshed(self):
        print("Помічник завершив роботу.")

        self.assistant_process.deleteLater()
        self.assistant_process = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.main_panel_background_frame.setGeometry(
            0, 0,
            270,
            self.height()
        )

        self.messages_frame.setFixedWidth(
            self.messages_frame_back.width()
        )

        self.commands_frame.setGeometry(
            self.width() - 270,
            0,
            270,
            self.height()
        )

    def closeEvent(self, e):
        self.deleteLater()
        if self.settings:
            self.settings.close()
        e.accept()
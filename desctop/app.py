import sys
import os, subprocess, json
import PyQt6 as qt

from PyQt6.QtCore import QProcess, QProcessEnvironment
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt


class SettingsWindow(QWidget):
    def __init__(self, win):
        super().__init__()
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 500)
        self.setStyleSheet("background: white;")

        self.json = "settings.json"

        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

        self.win = win
        self.lay = QVBoxLayout()
        self.lay.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self.header = QFrame()
        self.header.lay = QHBoxLayout()
        self.header.setLayout(self.header.lay)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 26px; font-weight: bold;")

        save_btn = QPushButton(text="Save")
        save_btn.setStyleSheet("font-size: 15px; background: gainsboro;")
        save_btn.setFixedSize(120, 38)
        save_btn.clicked.connect(self.close)

        self.header.lay.addWidget(title)
        self.header.lay.addWidget(save_btn)

        self.name = QLineEdit()
        self.name.setStyleSheet("font-size: 15px;")
        self.name.setPlaceholderText("Enter assistant name")
        self.name.setFixedHeight(38)

        self.voice = QComboBox()
        self.voice.setStyleSheet("font-size: 15px;")
        self.voice.addItems(["Alex", "Victoria"])
        self.voice.setFixedHeight(38)

        self.background = QCheckBox()
        self.background.setFixedSize(26, 26)

        self.background.setStyleSheet("""
        QCheckBox {
            background: transparent;
        }

        QCheckBox::indicator {
            border-radius: 6px;
        }

        QCheckBox::indicator:checked {
            background: #333333;
        }

        QCheckBox::indicator:unchecked {
            background: #d5d5d5;
        }
        """)

        background_layout = QHBoxLayout()
        background_layout.addWidget(QLabel("Work in background"))
        background_layout.addStretch()
        background_layout.addWidget(self.background)

        self.lay.addWidget(self.header)
        self.lay.addSpacing(20)

        self.lay.addWidget(QLabel("Assistant name:"))
        self.lay.addWidget(self.name)

        self.lay.addSpacing(10)

        self.lay.addWidget(QLabel("Select voice:"))
        self.lay.addWidget(self.voice)

        self.lay.addSpacing(10)
        self.lay.addLayout(background_layout)

        self.setLayout(self.lay)
        self.load_settings()

    def load_settings(self):
        if not os.path.exists(self.json):
            self.name.setText("Assistant")
            self.voice.setCurrentText("Alex")
            return

        with open(self.json, "r", encoding="utf-8") as file:
            settings = json.load(file)

        self.name.setText(
            settings.get("name", "Assistant")
        )

        self.voice.setCurrentText(
            settings.get("voice", "Alex")
        )

    def save_settings(self):
        settings = {
            "name": self.name.text(),
            "voice": self.voice.currentText()
        }

        with open(self.json, "w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)

    def closeEvent(self, event):
        self.deleteLater()
        self.save_settings()
        self.win.settings = None
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.assistant_process = None
        self.settings = None

        self.setWindowTitle("Intelligent Voice Assistant")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("background: white;")

        menubar = QMenuBar()
        menu = menubar.addMenu("Assistant")
        settings_act = menu.addAction("Settings")
        settings_act.triggered.connect(self.open_settings)
        exit_act = menu.addAction("Exit")
        exit_act.triggered.connect(self.close)

        self.center = QWidget()
        self.setCentralWidget(self.center)

        self.main_layout = QHBoxLayout(self.center)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setMenuWidget(menubar)

        self.create_chat()
        self.create_commands()

    def create_chat(self):
        # Chat
        self.messages_frame_back = QFrame(self)
        self.messages_frame_back.setFrameShape(QFrame.Shape.StyledPanel)
        self.messages_frame_back.setGeometry(0, 25, self.width() - 300, self.height() - 25)

        # Даём back-фрейму layout, чтобы центрировать всё внутри него
        self.messages_frame_back_layout = QVBoxLayout(self.messages_frame_back)
        self.messages_frame_back_layout.setContentsMargins(0, 0, 0, 0)

        self.messages_frame = QFrame()
        self.messages_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.messages_frame.setFixedWidth(self.width() - 300)  # ширина "колонки чата"

        self.messages_layout = QVBoxLayout(self.messages_frame)

        self.title = QLabel("Messages")
        self.title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
        """)
        self.messages_layout.addWidget(self.title)

        # Область сообщений
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setFrameShape(QFrame.Shape.NoFrame)

        messages_container = QWidget()
        self.messages_container_layout = QVBoxLayout(messages_container)
        self.messages_container_layout.addStretch()

        self.messages_area.setWidget(messages_container)
        self.messages_layout.addWidget(self.messages_area)

        # Поле ввода
        self.create_input()
        self.messages_layout.addWidget(self.input_frame)

        # Кладём messages_frame по центру back-фрейма
        self.messages_frame_back_layout.addWidget(
            self.messages_frame, alignment=Qt.AlignmentFlag.AlignHCenter
        )

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
        self.message_input.setPlaceholderText("Напишите сообщение...")
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
                background-color: white;
                color: black;
                border-radius: 13px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #dddddd;
            }
        """)

        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_btn)

    def send_message(self):
        text = self.message_input.text().strip()

        if not text:
            return

        # Показываем сообщение пользователя
        self.add_message("Вы", text)

        # Отправляем текст ассистенту
        if self.assistant_process is None:
            self.add_message("Система", "Ассистент не запущен.")
            return

        self.assistant_process.write(
            (text + "\n").encode("utf-8")
        )
        self.assistant_process.waitForBytesWritten(1000)

        self.message_input.clear()

    def add_message(self, sender, text):
        message = QLabel(f"<b>{sender}:</b> {text}")
        message.setWordWrap(True)
        message.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.messages_container_layout.insertWidget(
            self.messages_container_layout.count() - 1,
            message
        )

        self.messages_area.verticalScrollBar().setValue(
            self.messages_area.verticalScrollBar().maximum()
        )

    def create_commands(self):

        # Commands
        self.commands_frame = QFrame(self)
        self.commands_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.commands_frame.setGeometry(self.width() - 300, 25, 300, self.height() - 25)

    
        self.commands_layout = QVBoxLayout(self.commands_frame)
        self.commands_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.commands_layout.setSpacing(15)

        self.start_btn = QPushButton("Start", self.commands_frame)
        self.start_btn.setFixedSize(150, 50)
        self.start_btn.move(60, 30)
        self.start_btn.clicked.connect(self.start_assintant)

        self.stop_btn = QPushButton("Stop", self.commands_frame)
        self.stop_btn.setFixedSize(150, 50)
        self.stop_btn.move(60, 95)
        self.stop_btn.clicked.connect(self.stop_assintant)

        self.restart_btn = QPushButton("Restart", self.commands_frame)
        self.restart_btn.setFixedSize(150, 50)
        self.restart_btn.move(60, 160)
        self.restart_btn.clicked.connect(self.restart_assintant)

        self.commands_label = QLabel("Керування асистентом")
        self.commands_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        self.commands_layout.addWidget(self.commands_label)
        self.commands_layout.addWidget(self.start_btn)
        self.commands_layout.addWidget(self.stop_btn)
        self.commands_layout.addWidget(self.restart_btn)

    def open_settings(self):
        self.settings = SettingsWindow(self)
        self.settings.show()
        
    def start_assintant(self):
        print("start_assintant")
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


    def closeEvent(self, event):
        if self.assistant_process is not None:
            self.assistant_process.kill()
            self.assistant_process.waitForFinished(2000)
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
                answer = line[len("ANSWER:"):].strip()

                if answer:
                    self.add_message("Асистент", answer)

    def read_error(self):
        data = self.assistant_process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="replace")

        if text:
            print("ERROR:", text, end="")

    def assistant_fineshed(self):
        print("assistant_fineshed")

        self.assistant_process.deleteLater()
        self.assistant_process = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.messages_frame_back.setGeometry(0, 25, self.width() - 300, self.height() - 25)
        self.messages_frame.setFixedWidth(self.width() - 300)
        self.commands_frame.setGeometry(self.width() - 300, 25, 300, self.height() - 25)

    def closeEvent(self, e):
        self.deleteLater()
        if self.settings: self.settings.close()
        e.accept()
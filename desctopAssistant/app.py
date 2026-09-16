import sys
import os, subprocess
import PyQt6 as qt

from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.assistant_process = None

        self.setWindowTitle("Intelligent Voice Assistant")
        self.setMinimumSize(1600, 900)

        self.center = QWidget()
        self.setCentralWidget(self.center)

        self.main_layout = QHBoxLayout(self.center)

        # Chat
        self.messages_frame_back = QFrame()
        self.messages_frame_back.setFrameShape(QFrame.Shape.StyledPanel)
        self.messages_frame_back.setFixedWidth(1300)
        
        self.messages_frame = QFrame(self.messages_frame_back)
        self.messages_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.messages_frame.setFixedWidth(500)

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

        messages_container = QWidget()
        self.messages_container_layout = QVBoxLayout(messages_container)

        self.messages_container_layout.addStretch()

        self.messages_area.setWidget(messages_container)

        self.messages_layout.addWidget(self.messages_area)

        #Commands
        self.commands_frame = QFrame()
        self.commands_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.commands_frame.setFixedWidth(300)

        self.restart_btn = QPushButton("Restart", self.commands_frame)
        self.restart_btn.setFixedHeight(120)
        self.restart_btn.clicked.connect(self.restart_assintant)

        self.stop_btn = QPushButton("Stop", self.commands_frame)
        self.stop_btn.setFixedHeight(80)
        self.stop_btn.clicked.connect(self.stop_assintant)

        self.start_btn = QPushButton("Start", self.commands_frame)
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.start_assintant)


        print(type(self.messages_frame_back), type(self.commands_frame))
        self.main_layout.addWidget(self.messages_frame_back)
        self.main_layout.addWidget(self.commands_frame)

        self.main_layout.addStretch()

        
    def start_assintant(self):
        print("start_assintant")

        if self.assistant_process is not None:
            print("Assistant already running")
            return

        self.assistant_process = QProcess(self)

        self.assistant_process.readyReadStandardOutput.connect(
            self.read_output
        )

        self.assistant_process.readyReadStandardError.connect(
            self.read_error
        )

        self.assistant_process.errorOccurred.connect(
            self.process_error
        )

        self.assistant_process.started.connect(
            lambda: print("SIGNAL: process started")
        )

        self.assistant_process.finished.connect(
            self.assistant_fineshed
        )

        python = sys.executable

        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        manage_py = os.path.join(
            base_dir,
            "assistant",
            "manage.py"
        )

        # print("Python:", python)
        # print("Manage:", manage_py)
        # print("Exists:", os.path.exists(manage_py))

        arguments = [
            "-u",
            manage_py,
            "run_assistant"
        ]

        # print("Program:", python)
        # print("Arguments:", arguments)

        # print("Starting process...")

        self.assistant_process.start(
            python,
            arguments
        )

        if self.assistant_process.waitForStarted(3000):
            print("QProcess STARTED")
        else:
            print("QProcess FAILED TO START")
            print("Error:", self.assistant_process.errorString())
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def restart_assintant(self):
        print("restart_assintant")

    def stop_assintant(self):
        print("stop_assintant")
        if self.assistant_process is None:
            return
        
        self.assistant_process.terminate()

        if not self.assistant_process.waitForFinished(3000):
            self.assistant_process.kill()
        
    def read_output(self):
        data = self.assistant_process.readAllStandardOutput()
        text = bytes(data).decode("utf-8", errors="replace")

        if text:
            print("ASSISTANT:", text, end="")

    def read_error(self):
        data = self.assistant_process.readAllStandardError()
        text = bytes(data).decode("utf-8", errors="replace")

        if text:
            print("ERROR:", text)

    def process_error(self, error):
        print("QPROCESS ERROR:", error)
        print("ERROR STRING:", self.assistant_process.errorString())

    def assistant_fineshed(self):
        print("assistant_fineshed")

        self.assistant_process.deleteLater()
        self.assistant_process = None

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
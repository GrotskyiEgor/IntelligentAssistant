from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)


class ChatMixin:
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

        self.main_panel_title = QLabel("Календар")
        self.main_panel_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_panel_title.setStyleSheet("""
            QLabel { color: #ffffff; background: transparent; border: none;
                    font-size: 20px; font-weight: bold; }
        """)

        self.main_panel_layout = QVBoxLayout(self.main_panel_background_frame)
        self.main_panel_layout.setContentsMargins(10, 14, 10, 14)
        self.main_panel_layout.setSpacing(10)

        self.calendar = CalendarPanel(self)

        self.main_panel_layout.addWidget(self.main_panel_title)
        self.main_panel_layout.addWidget(self.calendar, 1)
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

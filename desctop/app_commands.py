from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout


class CommandPanelMixin:
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

        # Разберись с lambda функциями и генераторами for в python

        # Туту вызываешь эту функцию и отображаешь реальные названия групп, список всех приложений что бы их открыть [(name, [app_list]), (name, [app_list])]
        # all_groups = func()

        # for group in all_groups:

        self.group1_btn = QPushButton("Група 1", groups_frame)
        self.group1_btn.setFixedSize(105, 45)

        # Создай лямбда функцию которая откроет все app при нажатии

        self.group2_btn = QPushButton("Група 2", groups_frame)
        self.group2_btn.setFixedSize(105, 45)


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

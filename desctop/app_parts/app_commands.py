from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout
from PyQt6.QtWidgets import QGridLayout

from core.utils.groups import get_groups, open_apps


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

        groups_layout.addWidget(
            self.groups_label,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        self.groups_grid = QGridLayout()
        self.groups_grid.setSpacing(10)
        self.group_buttons = []

        all_groups = get_groups()
        # all_groups = [
        #     ("Робота", ["Telegram", "Chrome", "Discord"]),
        #     ("ігри", ["VS Code", "Aseprite"]),
        # ]

        if not all_groups:
            empty_label = QLabel("Груп ще немає")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            groups_layout.addWidget(empty_label)
        else:
            for index, (name, apps) in enumerate(all_groups):
                btn = QPushButton(name, groups_frame)
                btn.setFixedSize(105, 45)
                
                tooltip_text = "\n".join(getattr(app, 'name', str(app)) for app in apps)
                btn.setToolTip(tooltip_text or "Порожня група")
                
                btn.clicked.connect(lambda checked=False, current_apps=apps: open_apps(current_apps))

                self.groups_grid.addWidget(btn, index // 2, index % 2)
                self.group_buttons.append(btn)

        groups_layout.addLayout(self.groups_grid)
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

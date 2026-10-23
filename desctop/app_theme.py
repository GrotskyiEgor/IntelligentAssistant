import re

from hPyT import title_bar_color
from PyQt6.QtWidgets import QFrame, QPushButton, QWidget

from theme import get_theme_colors


class ThemeMixin:
    def apply_theme(self, settings):
        settings = {**self.preferences, **settings}
        self.preferences = settings
        self.theme, self.accent = get_theme_colors(settings)
        palette = {**self.theme["replace"], **self.accent["replace"]}
        button_text = "white" if settings.get("self.accent") in {"purple", "blue", "lime", "orange"} else "#2d2d2d"
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
                f"{selector} {{ background-color: {self.theme['panel']}; border-radius: 16px; }}"
            )

        self.menubar.setStyleSheet(f"""
            QMenuBar {{
                color: {self.theme['foreground']};
                background-color: {self.theme['window']};
                border: none;
                padding: 2px 6px;
                font-size: 13px;
                font-weight: bold;
            }}

            QMenuBar::item {{
                background-color: {self.theme['panel']};
                color: {self.theme['foreground']};
                padding: 6px 14px;
                margin: 2px;
                border-radius: 8px;
            }}

            QMenuBar::item:selected {{
                background-color: {self.accent['primary']};
                color: white;
            }}

            QMenu {{
                background-color: {self.theme['panel']};
                color: {self.theme['foreground']};
                border: 1px solid {self.theme['border']};
                border-radius: 11px;
                padding: 4px;
            }}

            QMenu::item {{
                font-size: 13px;
                font-weight: bold;
                padding: 6px 25px;
                border-radius: 8px;
                color: {self.theme['foreground']};
            }}

            QMenu::item:selected {{
                background-color: {self.accent['primary']};
                color: white;
            }}
        """)

        self.messages_frame.setStyleSheet(f"""
            QFrame#messages_frame {{
                background: transparent;
                border: none;
            }}

            QLabel {{
                color: {self.theme['foreground']};
                background: transparent;
                border: none;
            }}

            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QWidget#messages_container {{
                background: transparent;
                border: none;
            }}

            QFrame#messageBubbleSent {{
                background-color: {self.accent['primary']};
                border-radius: 14px;
            }}

            QFrame#messageBubbleReceived {{
                background-color: {self.theme['field']};
                border: 1px solid {self.theme['border']};
                border-radius: 14px;
            }}

            QLabel#messageSenderAssistant {{
                color: {self.accent['primary']};
                font-size: 12px;
                font-weight: bold;
            }}

            QLabel#messageSenderUser {{
                color: {button_text};
                font-size: 12px;
                font-weight: bold;
            }}

            QLabel#messageText {{
                color: {self.theme['foreground']};
                font-size: 15px;
            }}

            QLabel#messageTextSent {{
                color: {button_text};
                font-size: 15px;
            }}
        """)
        for bubble in self.messages_frame.findChildren(QFrame):
            if bubble.objectName() == "messageBubbleSent":
                bubble.setStyleSheet(
                    f"background-color: {self.accent['primary']}; border-radius: 14px;"
                )
            elif bubble.objectName() == "messageBubbleReceived":
                bubble.setStyleSheet(
                    f"background-color: {self.theme['field']}; border: 1px solid {self.theme['border']}; border-radius: 14px;"
                )

        self.commands_frame.setStyleSheet(f"""
            QFrame#commandsFrame {{
                background-color: {self.theme['panel']};
                border-radius: 16px;
            }}

            QFrame#section_frame {{
                background-color: {self.theme['field']};
                border: 1px solid {self.theme['border']};
                border-radius: 16px;
            }}

            QLabel {{
                color: {self.theme['foreground']};
                background: transparent;
                border: none;
            }}

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
                color: {button_text};
            }}

            QPushButton:pressed {{
                background-color: {self.accent['hover']};
            }}

            QPushButton:disabled {{
                background-color: {self.theme['field']};
                color: {self.theme['muted']};
            }}
        """)

        self.main_panel_title.setStyleSheet(f"QLabel {{ color: {self.theme['foreground']}; background: transparent; border: none; font-size: 20px; font-weight: bold; }}")
        self.title.setStyleSheet(f"color: {self.theme['foreground']}; background: transparent; font-size: 20px; font-weight: bold; padding-bottom: 5px;")
        self.input_frame.setStyleSheet(f"QFrame#inputFrame {{ background-color: {self.theme['field']}; border-radius: 20px; border: 1px solid {self.theme['border']}; }}")
        self.message_input.setStyleSheet(f"QLineEdit {{ border: none; background: transparent; color: {self.theme['foreground']}; font-size: 16px; }}")
        self.send_btn.setStyleSheet(f"QPushButton {{ background-color: {self.accent['primary']}; color: {button_text}; border-radius: 14px; font-size: 32px; }} QPushButton:hover {{ background-color: {self.accent['hover']}; color: white; }}")

        if self.settings:
            self.settings.apply_theme(settings, sync_main=False)

        self.setStyleSheet(f"background: {self.theme['window']}; color: {self.theme['foreground']};")
        title_bar_color.set(self, color=self.theme["window"])

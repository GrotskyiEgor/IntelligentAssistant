from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class MessageMixin:
    def send_message(self):
        text = self.message_input.text().strip()

        if not text:
            return

        self.add_message("Ви", text)

        if self.assistant_process is None:
            self.add_message(self.assistant_display_name(), "Помічник не запущений.")
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

        if is_outgoing:
            bubble.setStyleSheet(
                f"QFrame#messageBubbleSent {{ background-color: {self.accent['primary']}; border-radius: 14px; }}"
            )
        else:
            bubble.setStyleSheet(
                f"QFrame#messageBubbleReceived {{ background-color: {self.theme['field']}; "
                f"border: 1px solid {self.theme['border']}; border-radius: 14px; }}"
            )

        bubble.setMaximumWidth(440 if is_outgoing else 620)

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(3)

        sender_label = QLabel(sender)
        sender_label.setObjectName(
            "messageSenderUser" if is_outgoing else "messageSenderAssistant"
        )
        sender_label.setStyleSheet("background: transparent; border: none;")

        safe_text = "\u200b".join(
            text[i:i + 25]
            for i in range(0, len(text), 25)
        )

        body = QLabel(safe_text)
        body.setObjectName("messageTextSent" if is_outgoing else "messageText")
        body.setStyleSheet("background: transparent; border: none;")
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

    def assistant_display_name(self):
        return self.preferences.get("name") or "Помічник"

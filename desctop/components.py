from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPainter


class Label(QLabel):
    def paintEvent(self, event):
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        painter = QPainter(self)

        painter.setFont(self.font())
        painter.setPen(self.palette().windowText().color())

        text = self.text()
        rect = self.rect()

        painter.drawText(
            rect,
            self.alignment(),
            text
        )

        painter.setOpacity(0.2)
        painter.translate(0.25, 0)

        painter.drawText(
            rect,
            self.alignment(),
            text
        )
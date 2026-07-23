"""Contextual help button rendered with QPainter."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class PaintedHelpButton(QWidget):
    """Small circular ``?`` button with pixel-controlled rendering.

    The widget uses the same 26 px row height as the sensor checkboxes.  Its
    18 px circle is vertically centered on that row, so help buttons and check
    indicators share the same visual axis.
    """

    clicked = Signal()

    WIDGET_HEIGHT = 26
    CIRCLE_Y = 4.5
    CIRCLE_SIZE = 17.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(18, self.WIDGET_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._hovered = False
        self._pressed = False
        self._text = "?"

    def setText(self, text):
        self._text = str(text)
        self.update()

    def text(self):
        return self._text

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.isEnabled() and event.button() == Qt.LeftButton:
            self._pressed = True
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self._pressed and event.button() == Qt.LeftButton:
            self._pressed = False
            self.update()
            if self.rect().contains(event.position().toPoint()):
                self.clicked.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        if not self._text or not bool(self.property("contextHelpVisible")):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        circle = QRectF(
            0.5,
            self.CIRCLE_Y,
            self.CIRCLE_SIZE,
            self.CIRCLE_SIZE,
        )

        if self._hovered and self.isEnabled():
            background = QColor("#eef4ff")
            border = QColor("#2f6cff")
            text_color = QColor("#1d4ed8")
        else:
            background = QColor("#ffffff")
            border = QColor("#cbd5e1")
            text_color = QColor("#2f6cff")

        painter.setPen(QPen(border, 1.0))
        painter.setBrush(background)
        painter.drawEllipse(circle)

        font = painter.font()
        font.setBold(True)
        font.setPixelSize(11)
        painter.setFont(font)
        painter.setPen(text_color)
        painter.drawText(circle, Qt.AlignCenter, self._text)

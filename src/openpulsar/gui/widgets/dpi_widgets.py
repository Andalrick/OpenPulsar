"""DPI control widgets used by the OpenPulsar main window."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from openpulsar.gui import theme

class DpiRemoveButton(QPushButton):
    """Round DPI-stage remove control drawn independently from font metrics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dpiRemoveButton")
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if not self.isEnabled():
            border = QColor("#d1d5db")
            background = QColor("#f8fafc")
            cross = QColor("#94a3b8")
        elif self.isDown():
            border = QColor(theme.OP_BLUE)
            background = QColor("#dbeafe")
            cross = QColor(theme.OP_BLUE)
        elif self.underMouse():
            border = QColor(theme.OP_BLUE)
            background = QColor(theme.OP_BLUE_SOFT)
            cross = QColor(theme.OP_BLUE)
        else:
            border = QColor("#cbd5e1")
            background = QColor("#ffffff")
            cross = QColor("#64748b")

        outer = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.setPen(QPen(border, 1.0))
        painter.setBrush(background)
        painter.drawEllipse(outer)

        center = outer.center()
        half = 4.0
        painter.setPen(QPen(cross, 1.6, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(
            center.x() - half, center.y() - half,
            center.x() + half, center.y() + half,
        )
        painter.drawLine(
            center.x() + half, center.y() - half,
            center.x() - half, center.y() + half,
        )


class DpiValueControl(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._minimum = 0
        self._maximum = 26000
        self._step = 50

        self.setObjectName("dpiValueControl")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(84, 26)

        self.minus_button = QPushButton("−")
        self.minus_button.setObjectName("dpiMinusButton")
        self.minus_button.setFixedSize(19, 24)
        self._enable_auto_repeat(self.minus_button)

        self.value_label = QLineEdit("0")
        self.value_label.setObjectName("dpiValueEdit")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedSize(44, 24)
        self.value_label.setFrame(False)
        self.value_label.editingFinished.connect(self.commit_edit)

        self.plus_button = QPushButton("+")
        self.plus_button.setObjectName("dpiPlusButton")
        self.plus_button.setFixedSize(19, 24)
        self._enable_auto_repeat(self.plus_button)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.minus_button)
        layout.addWidget(self.value_label)
        layout.addWidget(self.plus_button)

    def _enable_auto_repeat(self, button):
        # Les boutons DPI doivent se comporter comme de vrais steppers :
        # un clic court change une fois la valeur, un clic maintenu fait
        # défiler les DPI sans obliger l'utilisateur à cliquer en boucle.
        button.setAutoRepeat(True)
        button.setAutoRepeatDelay(300)
        button.setAutoRepeatInterval(70)

    def commit_edit(self):
        text = self.value_label.text().strip()

        try:
            value = int(text)
        except ValueError:
            self.setValue(self._value)
            return

        # Snap to the mouse DPI step while preserving bounds.
        if self._step > 0:
            value = round(value / self._step) * self._step

        self.setValue(value)

    def setRange(self, minimum, maximum):
        self._minimum = minimum
        self._maximum = maximum

    def setSingleStep(self, step):
        self._step = step

    def setValue(self, value):
        value = max(self._minimum, min(self._maximum, int(value)))
        self._value = value
        self.value_label.setText(str(value))

    def value(self):
        return self._value

    def step(self):
        return self._step

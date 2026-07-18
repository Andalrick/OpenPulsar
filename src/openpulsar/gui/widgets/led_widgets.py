"""LED-specific Qt widgets used by the OpenPulsar main window."""

from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel

from openpulsar.gui import theme
class LedIndicator(QPushButton):
    """Circular DPI LED swatch drawn independently from font metrics and QSS."""

    def __init__(self, color="#2f6cff", parent=None):
        super().__init__(parent)
        self._color = self._to_qcolor(color)
        self.setObjectName("dpiLedButton")
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

    @staticmethod
    def _to_qcolor(color):
        if isinstance(color, QColor):
            result = QColor(color)
        elif isinstance(color, (tuple, list)) and len(color) >= 3:
            result = QColor(int(color[0]), int(color[1]), int(color[2]))
        else:
            result = QColor(color)

        return result if result.isValid() else QColor("#2f6cff")

    def setColor(self, color):
        new_color = self._to_qcolor(color)
        if new_color != self._color:
            self._color = new_color
            self.update()

    def color(self):
        return QColor(self._color)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        if not self.isEnabled():
            border = QColor("#d1d5db")
            background = QColor("#f8fafc")
            inner = QColor("#94a3b8")
        elif self.underMouse():
            border = QColor(theme.OP_BLUE)
            background = QColor(theme.OP_BLUE_SOFT)
            inner = self._color
        else:
            border = QColor("#cbd5e1")
            background = QColor("#ffffff")
            inner = self._color

        outer = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        painter.setPen(QPen(border, 1.0))
        painter.setBrush(background)
        painter.drawEllipse(outer)

        center = outer.center()

        painter.setPen(Qt.NoPen)
        painter.setBrush(inner)
        painter.drawEllipse(center, 6.0, 6.0)


class LedSettingsButton(QPushButton):
    """Tiny RGB LED button aligned with the DPI color dots."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ledSettingsButton")
        self.setFixedSize(22, 22)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        active = bool(self.property("ledPanelOpen"))

        if not self.isEnabled():
            border = QColor("#d1d5db")
            background = QColor("#f8fafc")
            foreground = QColor("#94a3b8")
            border_width = 1.0
        elif active and self.underMouse():
            border = QColor("#1d4ed8")
            background = QColor("#1d4ed8")
            foreground = QColor("#ffffff")
            border_width = 1.0
        elif active:
            border = QColor(theme.OP_BLUE)
            background = QColor(theme.OP_BLUE)
            foreground = QColor("#ffffff")
            border_width = 1.0
        elif self.underMouse():
            border = QColor(theme.OP_BLUE)
            background = QColor(theme.OP_BLUE_SOFT)
            foreground = QColor("#1d4ed8")
            border_width = 1.0
        else:
            border = QColor("#cbd5e1")
            background = QColor("#ffffff")
            foreground = QColor("#94a3b8")
            border_width = 1.0

        inset = border_width / 2.0
        rect = QRectF(inset, inset, self.width() - border_width, self.height() - border_width)
        painter.setPen(QPen(border, border_width))
        painter.setBrush(background)
        painter.drawRoundedRect(rect, 12.0, 12.0)

        font = QFont(self.font())
        font.setPixelSize(6)
        font.setBold(True)
        painter.setFont(font)

        letters = ("L", "E", "D")
        xs = (4, 9, 14)
        for letter, x in zip(letters, xs):
            painter.setPen(foreground)
            painter.drawText(QRectF(x, 6, 5, 10), Qt.AlignCenter, letter)



class LedGainControl(QWidget):
    """Compact percent stepper used by the LED management overlay."""

    valueChanged = Signal(int)

    def __init__(self, value=100, parent=None):
        super().__init__(parent)
        self._value = 100
        self._minimum = 0
        self._maximum = 100
        self._step = 5

        self.setObjectName("dpiValueControl")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(116, 26)

        self.minus_button = QPushButton("−")
        self.minus_button.setObjectName("dpiMinusButton")
        self.minus_button.setFixedSize(23, 24)
        self.minus_button.setAutoRepeat(True)
        self.minus_button.setAutoRepeatDelay(300)
        self.minus_button.setAutoRepeatInterval(90)
        self.minus_button.clicked.connect(self.previous)

        self.value_label = QLabel("")
        self.value_label.setObjectName("sensorValueLabel")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedSize(68, 24)

        self.plus_button = QPushButton("+")
        self.plus_button.setObjectName("dpiPlusButton")
        self.plus_button.setFixedSize(23, 24)
        self.plus_button.setAutoRepeat(True)
        self.plus_button.setAutoRepeatDelay(300)
        self.plus_button.setAutoRepeatInterval(90)
        self.plus_button.clicked.connect(self.next)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.minus_button)
        layout.addWidget(self.value_label)
        layout.addWidget(self.plus_button)

        self.setValue(value)

    def setValue(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 100
        value = max(self._minimum, min(self._maximum, value))
        changed = value != self._value
        self._value = value
        self._update_label()
        return changed

    def value(self):
        return self._value

    def previous(self):
        if self.setValue(self._value - self._step):
            self.valueChanged.emit(self._value)

    def next(self):
        if self.setValue(self._value + self._step):
            self.valueChanged.emit(self._value)

    def _update_label(self):
        self.value_label.setText(f"{self._value} %")
        self.minus_button.setEnabled(self._value > self._minimum)
        self.plus_button.setEnabled(self._value < self._maximum)


class LedChoiceControl(QWidget):
    """Discrete OpenPulsar pill for LED choices.

    Used for settings that are not free numeric values: brightness steps and
    pulse speed labels. It intentionally reuses the same pill vocabulary as
    Polling/LOD controls.
    """

    valueChanged = Signal(int)

    def __init__(self, choices, value=None, parent=None):
        super().__init__(parent)
        self._choices = list(choices)
        self._index = 0

        self.setObjectName("dpiValueControl")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(116, 26)

        self.previous_button = QPushButton("◀")
        self.previous_button.setObjectName("dpiMinusButton")
        self.previous_button.setFixedSize(23, 24)
        self.previous_button.clicked.connect(self.previous)

        self.value_label = QLabel("")
        self.value_label.setObjectName("sensorValueLabel")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedSize(68, 24)

        self.next_button = QPushButton("▶")
        self.next_button.setObjectName("dpiPlusButton")
        self.next_button.setFixedSize(23, 24)
        self.next_button.clicked.connect(self.next)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.value_label)
        layout.addWidget(self.next_button)

        self.setValue(self._choices[0][1] if value is None else value)

    def setValue(self, value):
        if not self._choices:
            return False

        try:
            value = int(value)
        except (TypeError, ValueError):
            value = self._choices[0][1]

        values = [choice_value for _label, choice_value in self._choices]
        if value in values:
            new_index = values.index(value)
        else:
            new_index = min(
                range(len(values)),
                key=lambda index: abs(values[index] - value),
            )

        changed = new_index != self._index
        self._index = new_index
        self._update_label()
        return changed

    def value(self):
        if not self._choices:
            return 0
        return int(self._choices[self._index][1])

    def setActive(self, active):
        self.setEnabled(bool(active))
        self.setProperty("ledSettingActive", bool(active))
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def previous(self):
        if self._index > 0:
            self._index -= 1
            self._update_label()
            self.valueChanged.emit(self.value())

    def next(self):
        if self._index < len(self._choices) - 1:
            self._index += 1
            self._update_label()
            self.valueChanged.emit(self.value())

    def _update_label(self):
        if not self._choices:
            self.value_label.setText("")
            self.previous_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return

        label, _value = self._choices[self._index]
        self.value_label.setText(str(label))
        self.previous_button.setEnabled(self._index > 0)
        self.next_button.setEnabled(self._index < len(self._choices) - 1)


class LedVerticalSlider(QWidget):
    """Small vertical slider painted like the OpenPulsar scrollbar."""

    valueChanged = Signal(int)

    def __init__(self, value=100, parent=None):
        super().__init__(parent)
        self._value = 100
        self.setObjectName("ledVerticalSlider")
        self.setFixedSize(38, 150)
        self.setMouseTracking(True)
        self.setValue(value)

    def value(self):
        return self._value

    def setValue(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 100
        value = max(0, min(100, value))
        if value == self._value:
            self.update()
            return False
        self._value = value
        self.update()
        return True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        margin_top = 9.0
        margin_bottom = 12.0
        track_width = 8.0
        track = QRectF(
            (self.width() - track_width) / 2.0,
            margin_top,
            track_width,
            self.height() - margin_top - margin_bottom,
        )

        # Rail inactif, très proche de la barre d'ascenseur OpenPulsar.
        painter.setBrush(QColor("#eef2f7"))
        painter.drawRoundedRect(track, track_width / 2.0, track_width / 2.0)

        # Partie active : bleu OpenPulsar.
        fill_height = track.height() * self._value / 100.0
        fill = QRectF(
            track.left(),
            track.bottom() - fill_height,
            track.width(),
            fill_height,
        )
        painter.setBrush(QColor(theme.OP_BLUE))
        painter.drawRoundedRect(fill, track_width / 2.0, track_width / 2.0)

        # Poignée ronde : mini-pilule blanche avec une ombre douce.
        handle_diameter = 20.0
        center_y = track.bottom() - (track.height() * self._value / 100.0)
        center_y = max(
            track.top(),
            min(track.bottom(), center_y),
        )
        handle = QRectF(
            (self.width() - handle_diameter) / 2.0,
            center_y - (handle_diameter / 2.0),
            handle_diameter,
            handle_diameter,
        )

        shadow = handle.translated(0.0, 2.0)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(130, 145, 168, 72))
        painter.drawEllipse(shadow)

        painter.setPen(QPen(QColor("#cbd5e1"), 1.0))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(handle)

    def mousePressEvent(self, event):
        self._set_from_y(event.position().y())
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._set_from_y(event.position().y())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def _set_from_y(self, y):
        top = 9.0
        height = self.height() - 21.0
        ratio = 1.0 - ((float(y) - top) / height)
        value = int(round(max(0.0, min(1.0, ratio)) * 100))
        if self.setValue(value):
            self.valueChanged.emit(self._value)

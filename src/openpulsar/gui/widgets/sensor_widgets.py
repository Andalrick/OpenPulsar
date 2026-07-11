"""Sensor setting control widgets used by the OpenPulsar main window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from .keyboard_widgets import apply_openpulsar_control_effect


class SensorValueControl(QWidget):
    def __init__(
        self,
        values,
        suffix="",
        previous_symbol="◀",
        next_symbol="▶",
        parent=None,
    ):
        super().__init__(parent)

        self._values = list(values)
        self._suffix = suffix
        self._index = 0

        self.setObjectName("dpiValueControl")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(104, 26)
        apply_openpulsar_control_effect(self)

        self.previous_button = QPushButton(previous_symbol)
        self.previous_button.setObjectName("dpiMinusButton")
        self.previous_button.setFixedSize(24, 24)
        self.previous_button.clicked.connect(self.previous)

        self.value_label = QLabel("")
        self.value_label.setObjectName("sensorValueLabel")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedSize(56, 24)

        self.next_button = QPushButton(next_symbol)
        self.next_button.setObjectName("dpiPlusButton")
        self.next_button.setFixedSize(24, 24)
        self.next_button.clicked.connect(self.next)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.value_label)
        layout.addWidget(self.next_button)

        self.setValue(self._values[0])

    def previous(self):
        if not self._values:
            return

        if self._index > 0:
            self._index -= 1

        self._update_label()

    def next(self):
        if not self._values:
            return

        if self._index < len(self._values) - 1:
            self._index += 1

        self._update_label()

    def setValue(self, value):
        if not self._values:
            return

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = float(self._values[0])

        for index, candidate in enumerate(self._values):
            try:
                if abs(float(candidate) - numeric_value) < 1e-6:
                    self._index = index
                    self._update_label()
                    return
            except (TypeError, ValueError):
                pass

        self._index = min(
            range(len(self._values)),
            key=lambda index: abs(float(self._values[index]) - numeric_value),
        )

        self._update_label()

    def value(self):
        if not self._values:
            return 0

        return self._values[self._index]

    def text(self):
        value = self.value()
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return f"{value} {self._suffix}".strip()

    def _update_label(self):
        self.value_label.setText(self.text())

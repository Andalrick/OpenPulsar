"""DPI control widgets used by the OpenPulsar main window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from .keyboard_widgets import apply_openpulsar_control_effect


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
        apply_openpulsar_control_effect(self)

        self.minus_button = QPushButton("−")
        self.minus_button.setObjectName("dpiMinusButton")
        self.minus_button.setFixedSize(20, 24)
        self._enable_auto_repeat(self.minus_button)

        self.value_label = QLineEdit("0")
        self.value_label.setObjectName("dpiValueEdit")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedSize(44, 24)
        self.value_label.setFrame(False)
        self.value_label.editingFinished.connect(self.commit_edit)

        self.plus_button = QPushButton("+")
        self.plus_button.setObjectName("dpiPlusButton")
        self.plus_button.setFixedSize(20, 24)
        self._enable_auto_repeat(self.plus_button)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
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

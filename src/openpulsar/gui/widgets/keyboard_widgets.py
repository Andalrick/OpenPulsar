"""Keyboard command widgets used by the OpenPulsar main window."""

from pathlib import Path
import json
import os

from PySide6.QtCore import Qt, Signal, QEvent, QRectF, QSize
from PySide6.QtGui import QKeySequence, QPainter, QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QScrollArea,
    QScrollBar,
    QVBoxLayout,
    QWidget,
)

from openpulsar.i18n import tr
from .dpi_widgets import DpiRemoveButton, DpiValueControl
from .mouse_button_widgets import MouseButtonCombo
from ..metrics import (
    CONTENT_MARGIN_TOP,
    FOOTER_HEIGHT,
    LEFT_PANEL_WIDTH,
    PANEL_BODY_HEIGHT,
    ROW_HEIGHT as OP_ROW_HEIGHT,
    ROW_SPACING as OP_ROW_SPACING,
)

class OpenPulsarScrollBar(QScrollBar):
    def __init__(self, orientation=Qt.Vertical, parent=None):
        super().__init__(orientation, parent)

        self.setObjectName("openPulsarScrollBar")
        self.setFixedWidth(8)
        self.setMouseTracking(True)
        self.setAutoFillBackground(False)
        self._pressed = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        # On peint toute la zone de la scrollbar pour éviter les artefacts
        # des thèmes Qt/Breeze, puis on dessine un rail fin placé à droite.
        painter.fillRect(self.rect(), QColor("#ffffff"))

        rail_width = 3.0
        rail_offset = -1.0

        # Le rail vit au centre exact de sa gouttière.
        # Il ne participe pas au calcul du contenu.
        rail_x = ((self.width() - rail_width) / 2) + rail_offset

        track_rect = QRectF(
            rail_x,
            0.0,
            rail_width,
            float(self.height()),
        )

        painter.setBrush(QColor("#eef2f7"))
        painter.drawRoundedRect(
            track_rect,
            rail_width / 2,
            rail_width / 2,
        )

        minimum = self.minimum()
        maximum = self.maximum()

        # Rail visible, mais pas de poignée si rien n'est scrollable.
        if maximum <= minimum:
            return

        page_step = max(1, self.pageStep())
        track_height = max(1.0, track_rect.height())

        handle_height = max(
            28.0,
            track_height * page_step / (maximum - minimum + page_step),
        )
        handle_height = min(handle_height, track_height)

        available = track_height - handle_height
        value_ratio = (self.value() - minimum) / (maximum - minimum)
        handle_y = track_rect.y() + (available * value_ratio)

        handle_width = 5.0

        handle_rect = QRectF(
            track_rect.center().x() - (handle_width / 2),
            handle_y,
            handle_width,
            handle_height,
        )

        if self._pressed:
            color = QColor("#1e40af")
        elif self.underMouse():
            color = QColor("#1d4ed8")
        else:
            color = QColor("#2f6cff")

        painter.setBrush(color)
        painter.drawRoundedRect(
            handle_rect,
            handle_width / 2,
            handle_width / 2,
        )

    def mousePressEvent(self, event):
        self._pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._pressed = False
        self.update()
        super().leaveEvent(event)


class KeyboardShortcutButton(QPushButton):
    shortcutChanged = Signal(str, int, Qt.KeyboardModifiers)
    captureStarted = Signal(object)
    captureStopped = Signal(object)

    MODIFIER_KEYS = {
        Qt.Key_Control,
        Qt.Key_Shift,
        Qt.Key_Alt,
        Qt.Key_Meta,
        Qt.Key_AltGr,
    }

    def __init__(self, parent=None):
        super().__init__(tr("Press…"), parent)
        self._capturing = False
        self._previous_shortcut = (None, Qt.NoModifier)
        self.key = None
        self.modifiers = Qt.NoModifier
        self.clicked.connect(self.start_capture)

    def set_shortcut(self, key, modifiers):
        if key is None:
            self.clear_shortcut()
            return

        self.key = int(key)
        self.modifiers = Qt.KeyboardModifiers(modifiers)
        label = shortcut_to_text(self.key, self.modifiers)
        self.setText(label)

    def clear_shortcut(self):
        self.key = None
        self.modifiers = Qt.NoModifier
        self.setText(tr("Press…"))

    def start_capture(self):
        if self._capturing:
            return

        # Let the owning editor stop any other shortcut capture first.
        # Only one button may listen to keyboard events at a time.
        self.captureStarted.emit(self)

        self._previous_shortcut = (self.key, self.modifiers)
        self._capturing = True
        self.setText(tr("Listening…"))
        self.setProperty("capturing", True)
        self.style().unpolish(self)
        self.style().polish(self)

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

        self.setFocus(Qt.MouseFocusReason)

    def restore_previous_shortcut(self):
        key, modifiers = self._previous_shortcut
        self.set_shortcut(key, modifiers)

    def cancel_capture(self):
        if not self._capturing:
            return

        # Capturing does not alter the stored shortcut until a key is accepted,
        # so cancelling only has to restore its visible label.
        if self.key is None:
            self.setText(tr("Press…"))
        else:
            self.setText(shortcut_to_text(self.key, self.modifiers))
        self.stop_capture()

    def stop_capture(self):
        if not self._capturing:
            return

        self._capturing = False
        self.setProperty("capturing", False)
        self.style().unpolish(self)
        self.style().polish(self)

        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)

        self.captureStopped.emit(self)

    def eventFilter(self, watched, event):
        if not self._capturing:
            return False

        if event.type() != QEvent.KeyPress:
            return False

        key = event.key()

        if key == Qt.Key_Escape:
            self.cancel_capture()
            return True

        if key in self.MODIFIER_KEYS:
            return True

        modifiers = event.modifiers() & (
            Qt.ControlModifier
            | Qt.ShiftModifier
            | Qt.AltModifier
            | Qt.MetaModifier
        )

        self.key = int(key)
        self.modifiers = modifiers
        label = shortcut_to_text(self.key, self.modifiers)
        self.setText(label)
        self.shortcutChanged.emit(label, self.key, self.modifiers)
        self.stop_capture()
        return True


def shortcut_to_text(key, modifiers):
    modifier_value = int(modifiers.value) if hasattr(modifiers, "value") else int(modifiers)
    return QKeySequence(modifier_value | int(key)).toString(QKeySequence.NativeText)


class KeyboardCommandRow(QWidget):
    ROW_WIDTH = 316
    ROW_HEIGHT = OP_ROW_HEIGHT

    # La ligne reste alignée quelle que soit la commande :
    # - commande avec paramètre : [commande] [paramètre] [raccourci] [×]
    # - commande simple :        [commande fusionnée    ] [raccourci] [×]
    # Le champ raccourci est dimensionné pour accueillir au moins 12 caractères
    # du type "Ctrl+Shift+A".
    PILL_WIDTH = 84
    PILL_SPACING = 8
    ACTION_WIDTH_WITH_PARAMETER = PILL_WIDTH
    PARAMETER_WIDTH = PILL_WIDTH
    ACTION_WIDTH_SIMPLE = (PILL_WIDTH * 2) + PILL_SPACING
    SHORTCUT_WIDTH = PILL_WIDTH

    # Les identifiants restent en anglais dans le code et dans le JSON.
    # L'affichage passe systématiquement par tr(...).
    COMMAND_PLACEHOLDER = "Choose a command"

    DPI_STEP_COMMANDS = {
        "DPI Value+",
        "DPI Value-",
    }
    DPI_SET_COMMAND = "Set DPI"

    DPI_STEPS = ["50", "100", "200"]

    SIMPLE_COMMANDS = [
        "DPI Cycle",
        "DPI Stage+",
        "DPI Stage-",
        "DPI Stage 1",
        "DPI Stage 2",
        "DPI Stage 3",
        "DPI Stage 4",
        "DPI Stage 5",
        "DPI Stage 6",
        "Profile Cycle+",
        "Profile Cycle-",
        "Profile 1",
        "Profile 2",
        "Profile 3",
        "Profile 4",
        "Profile 5",
    ]

    COMMANDS = [
        COMMAND_PLACEHOLDER,
        "DPI Value+",
        "DPI Value-",
        DPI_SET_COMMAND,
        *SIMPLE_COMMANDS,
    ]

    LEGACY_ACTIONS = {
        "Choisir une commande": "Choose a command",
        "Valeur DPI+": "DPI Value+",
        "Valeur DPI-": "DPI Value-",
        "Définir DPI": "Set DPI",
        "Cycle DPI": "DPI Cycle",
        "Palier DPI+": "DPI Stage+",
        "Palier DPI-": "DPI Stage-",
        "Palier DPI 1": "DPI Stage 1",
        "Palier DPI 2": "DPI Stage 2",
        "Palier DPI 3": "DPI Stage 3",
        "Palier DPI 4": "DPI Stage 4",
        "Palier DPI 5": "DPI Stage 5",
        "Palier DPI 6": "DPI Stage 6",
        "Cycle Profil": "Profile Cycle+",
        "Cycle Profil+": "Profile Cycle+",
        "Cycle Profil-": "Profile Cycle-",
        "Profil+": "Profile Cycle+",
        "Profil-": "Profile Cycle-",
        "Profil suivant": "Profile Cycle+",
        "Profil précédent": "Profile Cycle-",
        "Profil 1": "Profile 1",
        "Profil 2": "Profile 2",
        "Profil 3": "Profile 3",
        "Profil 4": "Profile 4",
        "Profil 5": "Profile 5",
    }

    # Compatibilité avec la version expérimentale générique :
    # [Commande] [Paramètre/mode] [Touche]
    GENERIC_ACTIONS = {
        ("Valeur DPI", "+50"): ("DPI Value+", "50"),
        ("Valeur DPI", "+100"): ("DPI Value+", "100"),
        ("Valeur DPI", "+200"): ("DPI Value+", "200"),
        ("Valeur DPI", "-50"): ("DPI Value-", "50"),
        ("Valeur DPI", "-100"): ("DPI Value-", "100"),
        ("Valeur DPI", "-200"): ("DPI Value-", "200"),
        ("Palier DPI", "Cycle normal"): ("DPI Cycle", None),
        ("Palier DPI", "Incrémental"): ("DPI Stage+", None),
        ("Palier DPI", "Décrémental"): ("DPI Stage-", None),
        ("Profil", "Cycle normal"): ("Profile Cycle+", None),
        ("Profil", "Cycle inversé"): ("Profile Cycle-", None),
        ("Profil", "Incrémental"): ("Profile Cycle+", None),
        ("Profil", "Décrémental"): ("Profile Cycle-", None),
    }

    commandTriggered = Signal(str, str)
    rowChanged = Signal()

    def __init__(
        self,
        parent=None,
        dpi_stage_count_provider=None,
        dpi_min=50,
        dpi_max=26000,
        dpi_step=50,
    ):
        super().__init__(parent)

        self._dpi_stage_count_provider = dpi_stage_count_provider
        self._dpi_min = int(dpi_min)
        self._dpi_max = int(dpi_max)
        self._dpi_step = int(dpi_step)

        self.setObjectName("keyboardCommandRow")
        self.setFixedSize(self.ROW_WIDTH, self.ROW_HEIGHT)

        self.action_combo = MouseButtonCombo()
        self.action_combo.setObjectName("keyboardCommandActionCombo")
        self.action_combo.setFixedSize(self.ACTION_WIDTH_SIMPLE, 26)
        self.action_combo.set_action_menu_width(self.ACTION_WIDTH_SIMPLE)
        self.action_combo.set_keep_one_group_open(True)
        self.action_combo.popupAboutToShow.connect(self._refresh_action_groups)
        self._refresh_action_groups()
        self.action_combo.currentIndexChanged.connect(self._on_action_changed)

        self.parameter_combo = QComboBox()
        self.parameter_combo.setObjectName("keyboardCommandCombo")
        self.parameter_combo.setFixedSize(self.PARAMETER_WIDTH, 26)
        self.parameter_combo.setView(QListView())
        self.parameter_combo.setMaxVisibleItems(len(self.DPI_STEPS))
        self.parameter_combo.currentTextChanged.connect(self._on_parameter_changed)

        self.dpi_value_control = DpiValueControl()
        self.dpi_value_control.setRange(self._dpi_min, self._dpi_max)
        self.dpi_value_control.setSingleStep(self._dpi_step)
        self.dpi_value_control.setValue(max(self._dpi_min, min(self._dpi_max, 800)))
        self.dpi_value_control.minus_button.clicked.connect(
            lambda checked=False: self._change_set_dpi_value(-1)
        )
        self.dpi_value_control.plus_button.clicked.connect(
            lambda checked=False: self._change_set_dpi_value(1)
        )
        self.dpi_value_control.value_label.editingFinished.connect(self._on_dpi_value_edited)
        self.dpi_value_control.setVisible(False)

        self.shortcut_button = KeyboardShortcutButton()
        self.shortcut_button.setObjectName("keyboardShortcutButton")
        self.shortcut_button.setFixedSize(self.SHORTCUT_WIDTH, 26)
        self.shortcut_button.setCursor(Qt.PointingHandCursor)

        self.remove_button = DpiRemoveButton()

        row_layout = QHBoxLayout(self)
        row_layout.setContentsMargins(4, 7, 4, 7)
        row_layout.setSpacing(8)
        row_layout.setAlignment(Qt.AlignVCenter)
        row_layout.addWidget(self.action_combo, alignment=Qt.AlignVCenter)
        row_layout.addWidget(self.parameter_combo, alignment=Qt.AlignVCenter)
        row_layout.addWidget(self.dpi_value_control, alignment=Qt.AlignVCenter)
        row_layout.addWidget(self.shortcut_button, alignment=Qt.AlignVCenter)
        row_layout.addWidget(self.remove_button, alignment=Qt.AlignVCenter)

        self.update_parameter_state(self.current_action())

    def _available_dpi_stage_count(self):
        if self._dpi_stage_count_provider is None:
            return 6

        try:
            count = int(self._dpi_stage_count_provider())
        except (TypeError, ValueError):
            return 6

        return max(1, min(count, 6))

    def _refresh_action_groups(self):
        dpi_stage_count = self._available_dpi_stage_count()
        direct_stage_actions = [
            (tr(f"DPI Stage {stage}"), f"DPI Stage {stage}")
            for stage in range(1, dpi_stage_count + 1)
        ]
        command_groups = [
            (tr("DPI adjustment"), [
                (tr("DPI Value+"), "DPI Value+"),
                (tr("DPI Value-"), "DPI Value-"),
                (tr("Set DPI"), "Set DPI"),
            ]),
            (tr("DPI stages"), [
                (tr("DPI Cycle"), "DPI Cycle"),
                (tr("DPI Stage+"), "DPI Stage+"),
                (tr("DPI Stage-"), "DPI Stage-"),
                *direct_stage_actions,
            ]),
            (tr("Profiles"), [
                (tr("Profile Cycle+"), "Profile Cycle+"),
                (tr("Profile Cycle-"), "Profile Cycle-"),
                (tr("Profile 1"), "Profile 1"),
                (tr("Profile 2"), "Profile 2"),
                (tr("Profile 3"), "Profile 3"),
                (tr("Profile 4"), "Profile 4"),
                (tr("Profile 5"), "Profile 5"),
            ]),
        ]
        self.action_combo.set_action_menu_height(
            258 + max(0, dpi_stage_count - 4) * 24
        )
        self.action_combo.set_action_groups(
            command_groups,
            placeholder=(tr(self.COMMAND_PLACEHOLDER), self.COMMAND_PLACEHOLDER),
        )

    def current_action(self):
        return self.action_combo.currentData() or self.COMMAND_PLACEHOLDER

    def _on_action_changed(self, _index):
        self.update_parameter_state(self.current_action())
        self.rowChanged.emit()

    def _on_parameter_changed(self, _text):
        self.shortcut_button.setEnabled(self.current_action() in self.COMMANDS[1:])
        self.rowChanged.emit()

    def _change_set_dpi_value(self, direction):
        value = self.dpi_value_control.value() + (int(direction) * self._dpi_step)
        self.dpi_value_control.setValue(value)
        self.rowChanged.emit()

    def _on_dpi_value_edited(self):
        self.rowChanged.emit()

    def update_parameter_state(self, action):
        previous = self.parameter_combo.currentText()
        self.parameter_combo.blockSignals(True)
        self.parameter_combo.clear()

        self.dpi_value_control.setVisible(False)
        self.dpi_value_control.setEnabled(False)

        if action in self.DPI_STEP_COMMANDS:
            self.action_combo.setFixedWidth(self.ACTION_WIDTH_WITH_PARAMETER)
            self.parameter_combo.setFixedWidth(self.PARAMETER_WIDTH)
            self.shortcut_button.setFixedWidth(self.SHORTCUT_WIDTH)

            self.parameter_combo.addItems(self.DPI_STEPS)
            self.parameter_combo.setEnabled(True)
            self.parameter_combo.setVisible(True)
            if previous in self.DPI_STEPS:
                self.parameter_combo.setCurrentText(previous)
            self.shortcut_button.setEnabled(True)
        elif action == self.DPI_SET_COMMAND:
            self.action_combo.setFixedWidth(self.ACTION_WIDTH_WITH_PARAMETER)
            self.shortcut_button.setFixedWidth(self.SHORTCUT_WIDTH)

            self.parameter_combo.setVisible(False)
            self.parameter_combo.setEnabled(False)
            self.dpi_value_control.setVisible(True)
            self.dpi_value_control.setEnabled(True)
            self.shortcut_button.setEnabled(True)
        elif action == self.COMMAND_PLACEHOLDER:
            self.action_combo.setFixedWidth(self.ACTION_WIDTH_SIMPLE)
            self.shortcut_button.setFixedWidth(self.SHORTCUT_WIDTH)

            self.parameter_combo.setVisible(False)
            self.parameter_combo.setEnabled(False)
            self.shortcut_button.setEnabled(False)
        else:
            self.action_combo.setFixedWidth(self.ACTION_WIDTH_SIMPLE)
            self.shortcut_button.setFixedWidth(self.SHORTCUT_WIDTH)

            self.parameter_combo.setVisible(False)
            self.parameter_combo.setEnabled(False)
            self.shortcut_button.setEnabled(True)

        self.parameter_combo.blockSignals(False)

    def _normalized_action_parameter(self):
        action = self.current_action()
        if action == self.COMMAND_PLACEHOLDER:
            return None, None

        if action in self.DPI_STEP_COMMANDS:
            parameter = self.parameter_combo.currentText()
        elif action == self.DPI_SET_COMMAND:
            parameter = str(self.dpi_value_control.value())
        else:
            parameter = None
        return action, parameter

    def to_dict(self):
        action, parameter = self._normalized_action_parameter()
        if action is None:
            return None

        data = {
            "action": action,
            "parameter": parameter,
            "key": self.shortcut_button.key,
            "modifiers": int(self.shortcut_button.modifiers.value)
            if hasattr(self.shortcut_button.modifiers, "value")
            else int(self.shortcut_button.modifiers),
        }
        return data

    def _convert_legacy_data(self, data):
        action = data.get("action", self.COMMAND_PLACEHOLDER)
        parameter = data.get("parameter")

        # Format expérimental générique : [Commande] [Paramètre/mode] [Touche]
        generic_key = (action, parameter)
        if generic_key in self.GENERIC_ACTIONS:
            return self.GENERIC_ACTIONS[generic_key]

        # Ancien format francophone ou ancien nommage interne.
        action = self.LEGACY_ACTIONS.get(action, action)

        if action in self.DPI_STEP_COMMANDS:
            return action, str(data.get("step", parameter or "100"))

        if action == self.DPI_SET_COMMAND:
            return action, str(parameter or data.get("dpi", "800"))

        if action in self.SIMPLE_COMMANDS or action == "DPI Cycle":
            return action, None

        return action, parameter

    def load_dict(self, data):
        action, parameter = self._convert_legacy_data(data)

        index = self.action_combo.findData(action)
        self.action_combo.setCurrentIndex(index if index >= 0 else 0)

        if action in self.DPI_STEP_COMMANDS and parameter is not None:
            parameter_index = self.parameter_combo.findText(str(parameter))
            if parameter_index >= 0:
                self.parameter_combo.setCurrentIndex(parameter_index)
        elif action == self.DPI_SET_COMMAND and parameter is not None:
            try:
                self.dpi_value_control.setValue(int(parameter))
            except (TypeError, ValueError):
                self.dpi_value_control.setValue(800)

        key = data.get("key")
        modifiers = data.get("modifiers", 0)
        if key is not None:
            self.shortcut_button.set_shortcut(key, modifiers)
        else:
            self.shortcut_button.clear_shortcut()

    def has_shortcut(self):
        return self.shortcut_button.key is not None

    def matches_key_event(self, event):
        if not self.has_shortcut():
            return False

        modifiers = event.modifiers() & (
            Qt.ControlModifier
            | Qt.ShiftModifier
            | Qt.AltModifier
            | Qt.MetaModifier
        )

        return (
            int(event.key()) == self.shortcut_button.key
            and modifiers == self.shortcut_button.modifiers
        )

    def matches_shortcut_values(self, key, modifiers):
        if not self.has_shortcut():
            return False

        modifiers = modifiers & (
            Qt.ControlModifier
            | Qt.ShiftModifier
            | Qt.AltModifier
            | Qt.MetaModifier
        )

        return (
            int(key) == self.shortcut_button.key
            and modifiers == self.shortcut_button.modifiers
        )

    def trigger_command(self):
        action, parameter = self._normalized_action_parameter()
        if action is None:
            return

        self.commandTriggered.emit(action, parameter or "")


class KeyboardCommandsEditor(QWidget):
    CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "OpenPulsar"
    CONFIG_FILE = CONFIG_DIR / "keyboard_commands.json"

    VISIBLE_ROWS = 6
    ROW_HEIGHT = OP_ROW_HEIGHT
    ROW_SPACING = OP_ROW_SPACING

    CONTENT_MARGIN = 3
    SCROLLBAR_GUTTER = 9

    ROWS_WIDTH = KeyboardCommandRow.ROW_WIDTH
    CONTENT_WIDTH = ROWS_WIDTH + (CONTENT_MARGIN * 2)
    SCROLL_WIDTH = CONTENT_WIDTH + SCROLLBAR_GUTTER
    SCROLL_HEIGHT = (VISIBLE_ROWS * ROW_HEIGHT) + ((VISIBLE_ROWS - 1) * ROW_SPACING)

    dpiValueChangeRequested = Signal(int)
    dpiValueSetRequested = Signal(int)
    dpiStageModeRequested = Signal(str)
    dpiStageDirectRequested = Signal(int)
    profileModeRequested = Signal(str)
    profileDirectRequested = Signal(int)
    commandsChanged = Signal(list)

    def __init__(
        self,
        parent=None,
        dpi_stage_count_provider=None,
        dpi_min=50,
        dpi_max=26000,
        dpi_step=50,
    ):
        super().__init__(parent)

        self._dpi_stage_count_provider = dpi_stage_count_provider
        self._dpi_min = int(dpi_min)
        self._dpi_max = int(dpi_max)
        self._dpi_step = int(dpi_step)

        self.setObjectName("keyboardCommandsEditor")
        self.setFixedSize(LEFT_PANEL_WIDTH, PANEL_BODY_HEIGHT)

        root = QVBoxLayout(self)
        # Keep the same breathing room below the header as the DPI body.
        root.setContentsMargins(0, CONTENT_MARGIN_TOP, 0, 10)
        root.setSpacing(10)

        self.rows_container = QWidget()
        self.rows_container.setObjectName("keyboardCommandRowsContainer")

        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(self.ROW_SPACING)
        self.rows_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.command_rows = []
        self._active_shortcut_capture = None
        self._loading_commands = False
        self.local_shortcuts_enabled = True

        self.scroll_wrapper = QWidget()
        self.scroll_wrapper.setObjectName("keyboardCommandsScrollWrapper")
        self.scroll_wrapper.setFixedSize(self.SCROLL_WIDTH, self.SCROLL_HEIGHT)

        scroll_wrapper_layout = QHBoxLayout(self.scroll_wrapper)
        scroll_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        scroll_wrapper_layout.setSpacing(2)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("keyboardCommandsScrollArea")
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setFixedSize(self.CONTENT_WIDTH, self.SCROLL_HEIGHT)
        self.scroll_area.setWidget(self.rows_container)

        self.command_scrollbar = OpenPulsarScrollBar(Qt.Vertical)
        self.command_scrollbar.setFixedSize(
            self.SCROLLBAR_GUTTER,
            self.SCROLL_HEIGHT,
        )

        scroll_wrapper_layout.addWidget(self.scroll_area)
        scroll_wrapper_layout.addWidget(self.command_scrollbar)

        internal_scrollbar = self.scroll_area.verticalScrollBar()
        self.command_scrollbar.valueChanged.connect(internal_scrollbar.setValue)
        internal_scrollbar.valueChanged.connect(self.command_scrollbar.setValue)

        # Local confirmation card used for shortcut conflicts. It is attached
        # to the scroll wrapper so it always remains inside the Keyboard
        # Commands panel.
        self.shortcut_conflict_overlay = QWidget(self.scroll_wrapper)
        self.shortcut_conflict_overlay.setObjectName("shortcutConflictOverlay")
        self.shortcut_conflict_overlay.setAttribute(Qt.WA_StyledBackground, True)
        self.shortcut_conflict_overlay.setGeometry(self.scroll_wrapper.rect())

        overlay_layout = QVBoxLayout(self.shortcut_conflict_overlay)
        overlay_layout.setContentsMargins(8, 8, 8, 8)
        overlay_layout.setAlignment(Qt.AlignCenter)

        self.shortcut_conflict_card = QWidget()
        self.shortcut_conflict_card.setObjectName("shortcutConflictCard")
        self.shortcut_conflict_card.setAttribute(Qt.WA_StyledBackground, True)
        self.shortcut_conflict_card.setFixedSize(self.CONTENT_WIDTH - 12, 96)

        card_layout = QVBoxLayout(self.shortcut_conflict_card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignCenter)

        # Reuse the exact dimensions of the smallest Keyboard Commands pill.
        # The regular row controls are 84 x 26 px.
        pill_size = QSize(KeyboardCommandRow.PILL_WIDTH, 26)

        conflict_summary = QHBoxLayout()
        conflict_summary.setContentsMargins(0, 0, 0, 0)
        conflict_summary.setSpacing(8)
        conflict_summary.setAlignment(Qt.AlignCenter)

        self.shortcut_conflict_shortcut = QLabel()
        self.shortcut_conflict_shortcut.setObjectName("shortcutConflictShortcutPill")
        self.shortcut_conflict_shortcut.setFixedSize(pill_size)
        self.shortcut_conflict_shortcut.setAlignment(Qt.AlignCenter)
        conflict_summary.addWidget(self.shortcut_conflict_shortcut)

        self.shortcut_conflict_relation = QLabel(tr("Already used by"))
        self.shortcut_conflict_relation.setObjectName("shortcutConflictRelationLabel")
        self.shortcut_conflict_relation.setAlignment(Qt.AlignCenter)
        conflict_summary.addWidget(self.shortcut_conflict_relation)

        self.shortcut_conflict_command = QLabel()
        self.shortcut_conflict_command.setObjectName("shortcutConflictCommandPill")
        self.shortcut_conflict_command.setFixedSize(pill_size)
        self.shortcut_conflict_command.setAlignment(Qt.AlignCenter)
        conflict_summary.addWidget(self.shortcut_conflict_command)

        card_layout.addLayout(conflict_summary)

        conflict_buttons = QHBoxLayout()
        conflict_buttons.setContentsMargins(0, 0, 0, 0)
        conflict_buttons.setSpacing(KeyboardCommandRow.PILL_SPACING)
        conflict_buttons.setAlignment(Qt.AlignCenter)

        self.shortcut_conflict_reassign = QPushButton(tr("Reassign"))
        self.shortcut_conflict_reassign.setObjectName("shortcutConflictPrimaryButton")
        self.shortcut_conflict_reassign.setFixedSize(pill_size)
        self.shortcut_conflict_reassign.clicked.connect(
            self._reassign_conflicting_shortcut
        )

        self.shortcut_conflict_cancel = QPushButton(tr("Cancel"))
        self.shortcut_conflict_cancel.setObjectName("shortcutConflictSecondaryButton")
        self.shortcut_conflict_cancel.setFixedSize(pill_size)
        self.shortcut_conflict_cancel.clicked.connect(
            self._cancel_conflicting_shortcut
        )

        conflict_buttons.addWidget(self.shortcut_conflict_reassign)
        conflict_buttons.addWidget(self.shortcut_conflict_cancel)
        card_layout.addLayout(conflict_buttons)

        overlay_layout.addWidget(self.shortcut_conflict_card)
        self.shortcut_conflict_overlay.hide()
        self._pending_shortcut_conflict = None

        self.add_command_button = QPushButton(tr("+ Add keyboard command"))
        self.add_command_button.setObjectName("addListButton")
        self.add_command_button.setFixedSize(220, 30)
        self.add_command_button.clicked.connect(lambda checked=False: self.add_keyboard_command_row())

        self.command_footer = QWidget()
        self.command_footer.setObjectName("keyboardCommandFooterRow")
        self.command_footer.setFixedSize(230, FOOTER_HEIGHT)

        command_footer_layout = QHBoxLayout(self.command_footer)
        command_footer_layout.setContentsMargins(4, 4, 4, 4)
        command_footer_layout.setSpacing(8)
        command_footer_layout.setAlignment(Qt.AlignVCenter)
        command_footer_layout.addWidget(self.add_command_button, alignment=Qt.AlignVCenter)

        root.addWidget(self.scroll_wrapper, alignment=Qt.AlignHCenter)
        root.addStretch()
        root.addWidget(self.command_footer, alignment=Qt.AlignHCenter)

        self._update_rows_container_size()

        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

        # Commands are profile-scoped. MainWindow loads the active profile commands.

    def eventFilter(self, watched, event):
        if not self.local_shortcuts_enabled:
            return False

        if event.type() != QEvent.KeyPress or event.isAutoRepeat():
            return False

        focus = QApplication.focusWidget()
        if isinstance(focus, (QLineEdit, QComboBox)):
            return False

        for row in self.command_rows:
            if row.shortcut_button._capturing:
                return False

        for row in self.command_rows:
            if row.matches_key_event(event):
                row.trigger_command()
                return True

        return False

    def set_local_shortcuts_enabled(self, enabled):
        self.local_shortcuts_enabled = bool(enabled)

    def trigger_shortcut(self, key, modifiers):
        modifiers = Qt.KeyboardModifiers(modifiers)

        for row in self.command_rows:
            if row.shortcut_button._capturing:
                return False

        for row in self.command_rows:
            if row.matches_shortcut_values(key, modifiers):
                row.trigger_command()
                return True

        return False

    def _update_rows_container_size(self):
        rows_height = (
            len(self.command_rows) * self.ROW_HEIGHT
            + max(0, len(self.command_rows) - 1) * self.ROW_SPACING
        )

        self.rows_container.setFixedSize(
            self.CONTENT_WIDTH,
            max(self.SCROLL_HEIGHT, rows_height),
        )

        self._sync_command_scrollbar()

    def _sync_command_scrollbar(self):
        internal_scrollbar = self.scroll_area.verticalScrollBar()

        self.command_scrollbar.setRange(
            internal_scrollbar.minimum(),
            internal_scrollbar.maximum(),
        )
        self.command_scrollbar.setPageStep(internal_scrollbar.pageStep())
        self.command_scrollbar.setSingleStep(internal_scrollbar.singleStep())
        self.command_scrollbar.setValue(internal_scrollbar.value())
        self.command_scrollbar.update()

    def add_keyboard_command_row(self, data=None):
        row = KeyboardCommandRow(
            dpi_stage_count_provider=self._dpi_stage_count_provider,
            dpi_min=self._dpi_min,
            dpi_max=self._dpi_max,
            dpi_step=self._dpi_step,
        )
        row.remove_button.clicked.connect(
            lambda checked=False, row=row: self.remove_keyboard_command_row(row)
        )
        row.commandTriggered.connect(self.execute_keyboard_command)
        row.shortcut_button.captureStarted.connect(self._on_shortcut_capture_started)
        row.shortcut_button.captureStopped.connect(self._on_shortcut_capture_stopped)
        row.shortcut_button.shortcutChanged.connect(
            lambda _label, key, modifiers, row=row: self._on_shortcut_changed(
                row, key, modifiers
            )
        )
        row.rowChanged.connect(self.save_keyboard_commands)

        if data is not None:
            row.load_dict(data)

        self.command_rows.append(row)
        self.rows_layout.addWidget(row, alignment=Qt.AlignHCenter)
        self._update_rows_container_size()

        if not self._loading_commands:
            self.save_keyboard_commands()

    def _on_shortcut_capture_started(self, shortcut_button):
        active_button = self._active_shortcut_capture
        if active_button is not None and active_button is not shortcut_button:
            active_button.cancel_capture()

        self._active_shortcut_capture = shortcut_button

    def _on_shortcut_capture_stopped(self, shortcut_button):
        if self._active_shortcut_capture is shortcut_button:
            self._active_shortcut_capture = None

    def _on_shortcut_changed(self, changed_row, key, modifiers):
        conflict_row = next(
            (
                row
                for row in self.command_rows
                if row is not changed_row
                and row.matches_shortcut_values(key, modifiers)
            ),
            None,
        )

        if conflict_row is None:
            changed_row.rowChanged.emit()
            return

        shortcut = shortcut_to_text(key, modifiers)
        self.shortcut_conflict_shortcut.setText(shortcut)
        self.shortcut_conflict_command.setText(
            conflict_row.action_combo.currentText()
        )
        self._pending_shortcut_conflict = (changed_row, conflict_row)
        self.add_command_button.setEnabled(False)
        self.shortcut_conflict_overlay.setGeometry(self.scroll_wrapper.rect())
        self.shortcut_conflict_overlay.show()
        self.shortcut_conflict_overlay.raise_()
        self.shortcut_conflict_reassign.setFocus(Qt.OtherFocusReason)

    def _close_shortcut_conflict(self):
        self._pending_shortcut_conflict = None
        self.shortcut_conflict_overlay.hide()
        self.add_command_button.setEnabled(True)

    def _reassign_conflicting_shortcut(self):
        pending = self._pending_shortcut_conflict
        if pending is None:
            return

        changed_row, conflict_row = pending
        conflict_row.shortcut_button.clear_shortcut()
        conflict_row.rowChanged.emit()
        changed_row.rowChanged.emit()
        self._close_shortcut_conflict()

    def _cancel_conflicting_shortcut(self):
        pending = self._pending_shortcut_conflict
        if pending is None:
            return

        changed_row, _conflict_row = pending
        changed_row.shortcut_button.restore_previous_shortcut()
        changed_row.rowChanged.emit()
        self._close_shortcut_conflict()

    def remove_keyboard_command_row(self, row):
        if row not in self.command_rows:
            return

        if self._active_shortcut_capture is row.shortcut_button:
            row.shortcut_button.cancel_capture()

        self.command_rows.remove(row)
        self.rows_layout.removeWidget(row)
        row.setParent(None)
        row.deleteLater()
        self._update_rows_container_size()
        self.save_keyboard_commands()

    @classmethod
    def load_legacy_keyboard_commands(cls):
        if not cls.CONFIG_FILE.exists():
            return []

        try:
            payload = json.loads(cls.CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

        commands = payload.get("commands", [])
        if not isinstance(commands, list):
            return []

        return [command for command in commands if isinstance(command, dict)]

    def commands_to_list(self):
        commands = []
        for row in self.command_rows:
            data = row.to_dict()
            if data is not None:
                commands.append(data)
        return commands

    def set_keyboard_commands(self, commands):
        commands = commands if isinstance(commands, list) else []

        self._loading_commands = True
        try:
            for row in list(self.command_rows):
                self.rows_layout.removeWidget(row)
                row.setParent(None)
                row.deleteLater()
            self.command_rows.clear()

            for command_data in commands:
                if isinstance(command_data, dict):
                    self.add_keyboard_command_row(command_data)
        finally:
            self._loading_commands = False
            self._update_rows_container_size()

    def save_keyboard_commands(self):
        if self._loading_commands:
            return
        self.commandsChanged.emit(self.commands_to_list())

    def execute_keyboard_command(self, action, parameter):
        if action == "Set DPI":
            try:
                value = int(parameter)
            except (TypeError, ValueError):
                return
            self.dpiValueSetRequested.emit(value)
        elif action in {"DPI Value+", "DPI Value-"}:
            try:
                step = int(parameter)
            except (TypeError, ValueError):
                return

            if action == "DPI Value-":
                step = -step

            self.dpiValueChangeRequested.emit(step)
        elif action == "DPI Cycle":
            self.dpiStageModeRequested.emit("Cycle normal")
        elif action == "DPI Stage+":
            self.dpiStageModeRequested.emit("Incrémental")
        elif action == "DPI Stage-":
            self.dpiStageModeRequested.emit("Décrémental")
        elif action.startswith("DPI Stage "):
            try:
                dpi_stage = int(action.split()[-1])
            except (TypeError, ValueError):
                return
            self.dpiStageDirectRequested.emit(dpi_stage)
        elif action == "Profile Cycle+":
            self.profileModeRequested.emit("Cycle normal")
        elif action == "Profile Cycle-":
            self.profileModeRequested.emit("Cycle inversé")
        elif action.startswith("Profile "):
            try:
                profile_slot = int(action.split()[-1])
            except (TypeError, ValueError):
                return
            self.profileDirectRequested.emit(profile_slot)

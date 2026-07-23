from pathlib import Path
import json
import os
import sys

from PySide6.QtCore import Qt, Signal, QSize, QEvent
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from openpulsar.i18n import tr, set_language
from .metrics import PANEL_BORDER_WIDTH, PANEL_RADIUS
from .theme import op_radius


ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


def picture_path(name):
    for category in ("icons", "backgrounds", "devices"):
        candidate = ASSETS_DIR / category / name
        if candidate.exists():
            return str(candidate)
    return str(ASSETS_DIR / "icons" / name)


class SettingsStore:
    CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "OpenPulsar"
    CONFIG_FILE = CONFIG_DIR / "settings.json"

    DEFAULTS = {
        "language": "system",
        "persistent_mode": False,
        "show_context_help": True,
        "about_welcome_seen": False,
    }

    @classmethod
    def load(cls):
        try:
            payload = json.loads(cls.CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}

        settings = dict(cls.DEFAULTS)
        if isinstance(payload, dict):
            settings.update(
                {
                    key: value
                    for key, value in payload.items()
                    if key in cls.DEFAULTS
                }
            )
        return settings

    @classmethod
    def save(cls, settings):
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONFIG_FILE.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        cls.set_autostart_enabled(bool(settings.get("persistent_mode", False)))

    @classmethod
    def autostart_file(cls):
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return config_home / "autostart" / "openpulsar.desktop"

    @classmethod
    def set_autostart_enabled(cls, enabled):
        autostart_file = cls.autostart_file()

        if not enabled:
            try:
                autostart_file.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass
            return

        try:
            autostart_file.parent.mkdir(parents=True, exist_ok=True)

            executable = Path(sys.argv[0]).resolve()
            if executable.exists():
                exec_line = f'{sys.executable} "{executable}" --tray'
            else:
                exec_line = "openpulsar --tray"

            autostart_file.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=OpenPulsar\n"
                "Comment=OpenPulsar persistent mode\n"
                f"Exec={exec_line}\n"
                "Icon=openpulsar\n"
                "Terminal=false\n"
                "X-GNOME-Autostart-enabled=true\n",
                encoding="utf-8",
            )
        except OSError:
            pass


class SettingsPillSelector(QWidget):
    """OpenPulsar pill selector: previous arrow / current value / next arrow."""

    currentValueChanged = Signal(object)

    def __init__(self, choices, parent=None):
        super().__init__(parent)

        self._choices = list(choices)
        self._index = 0

        self.setObjectName("settingsPillSelector")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(150, 28)

        self.previous_button = QPushButton("◀")
        self.previous_button.setObjectName("settingsPillPrevious")
        self.previous_button.setFixedSize(25, 26)
        self.previous_button.setCursor(Qt.PointingHandCursor)
        self.previous_button.clicked.connect(self.previous)

        self.value_label = QLabel("")
        self.value_label.setObjectName("settingsPillValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedSize(98, 26)

        self.next_button = QPushButton("▶")
        self.next_button.setObjectName("settingsPillNext")
        self.next_button.setFixedSize(25, 26)
        self.next_button.setCursor(Qt.PointingHandCursor)
        self.next_button.clicked.connect(self.next)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.value_label)
        layout.addWidget(self.next_button)

        self._update_label()

    def previous(self):
        if not self._choices:
            return
        self._index = (self._index - 1) % len(self._choices)
        self._update_label()
        self.currentValueChanged.emit(self.current_value())

    def next(self):
        if not self._choices:
            return
        self._index = (self._index + 1) % len(self._choices)
        self._update_label()
        self.currentValueChanged.emit(self.current_value())

    def set_current_value(self, value):
        for index, (choice_value, _label_key) in enumerate(self._choices):
            if choice_value == value:
                self._index = index
                self._update_label()
                return
        self._index = 0
        self._update_label()

    def current_value(self):
        if not self._choices:
            return None
        return self._choices[self._index][0]

    def _update_label(self):
        if not self._choices:
            self.value_label.setText("—")
            return
        _value, label_key = self._choices[self._index]
        self.value_label.setText(tr(label_key))




class SettingsPercentPillSelector(QWidget):
    """Compact OpenPulsar percent selector: previous / value / next."""

    currentValueChanged = Signal(int)

    def __init__(self, minimum=0, maximum=100, step=5, parent=None):
        super().__init__(parent)

        self._minimum = int(minimum)
        self._maximum = int(maximum)
        self._step = int(step)
        self._value = 100

        self.setObjectName("settingsPillSelector")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(246, 28)

        self.previous_button = QPushButton("−")
        self.previous_button.setObjectName("settingsPillPrevious")
        self.previous_button.setFixedSize(27, 26)
        self.previous_button.setCursor(Qt.PointingHandCursor)
        self.previous_button.setAutoRepeat(True)
        self.previous_button.setAutoRepeatDelay(300)
        self.previous_button.setAutoRepeatInterval(90)
        self.previous_button.clicked.connect(self.previous)

        self.value_label = QLabel("")
        self.value_label.setObjectName("settingsPillValue")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setFixedSize(190, 26)

        self.next_button = QPushButton("+")
        self.next_button.setObjectName("settingsPillNext")
        self.next_button.setFixedSize(27, 26)
        self.next_button.setCursor(Qt.PointingHandCursor)
        self.next_button.setAutoRepeat(True)
        self.next_button.setAutoRepeatDelay(300)
        self.next_button.setAutoRepeatInterval(90)
        self.next_button.clicked.connect(self.next)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.value_label)
        layout.addWidget(self.next_button)

        self._update_label()

    def set_value(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 100

        value = max(self._minimum, min(self._maximum, value))
        if value == self._value:
            self._update_label()
            return

        self._value = value
        self._update_label()

    def value(self):
        return self._value

    def previous(self):
        self.set_value(self._value - self._step)
        self.currentValueChanged.emit(self._value)

    def next(self):
        self.set_value(self._value + self._step)
        self.currentValueChanged.emit(self._value)

    def _update_label(self):
        self.value_label.setText(f"{self._value} %")
        self.previous_button.setEnabled(self._value > self._minimum)
        self.next_button.setEnabled(self._value < self._maximum)

class SettingsHelpPopup(QFrame):
    def __init__(self, title, body, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsHelpPopup")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(Qt.Widget)
        self.setFixedWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("settingsHelpPopupTitle")
        title_label.setWordWrap(True)

        body_label = QLabel(body)
        body_label.setObjectName("settingsHelpPopupBody")
        body_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(body_label)

        self.setStyleSheet("""
        QFrame#settingsHelpPopup {
            background-color: #ffffff;
            border: {panel_border_width}px solid #cbd5e1;
            border-radius: {panel_radius}px;
        }
        QLabel#settingsHelpPopupTitle {
            color: #1f2937;
            font-family: Inter, Segoe UI, Arial;
            font-size: 12px;
            font-weight: 800;
        }
        QLabel#settingsHelpPopupBody {
            color: #334155;
            font-family: Inter, Segoe UI, Arial;
            font-size: 12px;
        }
        """.replace("{panel_border_width}", str(PANEL_BORDER_WIDTH))
            .replace("{panel_radius}", str(PANEL_RADIUS))
            .replace("{radius_28}", str(op_radius(28)))
            .replace("{radius_30}", str(op_radius(30)))
            .replace("{radius_36}", str(op_radius(36))))

    def mousePressEvent(self, event):
        self.close()
        event.accept()


class SettingsDialog(QWidget):
    """Compact settings popover integrated inside the OpenPulsar window."""

    settingsChanged = Signal(dict)

    LANGUAGE_CHOICES = [
        ("system", "settings.language.system"),
        ("fr", "settings.language.french"),
        ("en", "settings.language.english"),
        ("de", "settings.language.german"),
        ("es", "settings.language.spanish"),
    ]

    PERSISTENT_CHOICES = [
        (False, "settings.persistent.disabled"),
        (True, "settings.persistent.enabled"),
    ]

    CONTEXT_HELP_CHOICES = [
        (False, "settings.context_help.hidden"),
        (True, "settings.context_help.visible"),
    ]

    CARD_WIDTH = 180
    CARD_HEIGHT = 245

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("settingsPopover")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)

        self.settings = SettingsStore.load()
        self._loading = True
        self.help_popup = None

        self.build_ui()
        self.apply_style()
        self.load_values()

        self._loading = False

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(9)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)

        icon = QLabel()
        icon.setObjectName("settingsPopoverIcon")
        icon.setFixedSize(18, 18)
        icon.setPixmap(QIcon(picture_path("icon_settings.svg")).pixmap(QSize(16, 16)))
        icon.setAlignment(Qt.AlignCenter)

        title = QLabel(tr("settings.title"))
        title.setObjectName("settingsPopoverTitle")
        self.settings_title = title

        title_row.addWidget(icon)
        title_row.addWidget(title)
        title_row.addStretch()
        root.addLayout(title_row)

        self.language_selector = SettingsPillSelector(self.LANGUAGE_CHOICES)
        self.persistent_selector = SettingsPillSelector(self.PERSISTENT_CHOICES)
        self.context_help_selector = SettingsPillSelector(self.CONTEXT_HELP_CHOICES)

        root.addWidget(
            self.make_setting_row(
                tr("settings.language.title"),
                self.language_selector,
                "language",
            )
        )
        root.addWidget(
            self.make_setting_row(
                tr("settings.persistent.title"),
                self.persistent_selector,
                "persistent",
            )
        )
        root.addWidget(
            self.make_setting_row(
                tr("settings.context_help.title"),
                self.context_help_selector,
                "context_help",
            )
        )
        root.addStretch()

        self.apply_button = QPushButton(tr("settings.apply"))
        self.apply_button.setObjectName("settingsApplyButton")
        self.apply_button.setCursor(Qt.PointingHandCursor)
        self.apply_button.setFixedHeight(30)
        self.apply_button.clicked.connect(self.apply_values)
        root.addWidget(self.apply_button)

        self.language_selector.currentValueChanged.connect(self.mark_dirty)
        self.persistent_selector.currentValueChanged.connect(self.mark_dirty)
        self.context_help_selector.currentValueChanged.connect(self.mark_dirty)

    def make_setting_row(self, title_text, selector, object_prefix=None):
        row = QWidget()
        row.setObjectName("settingsRow")
        row.setAttribute(Qt.WA_StyledBackground, True)
        row.setFixedHeight(50)

        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label_row = QHBoxLayout()
        label_row.setContentsMargins(0, 0, 0, 0)
        label_row.setSpacing(6)

        title = QLabel(title_text)
        title.setObjectName("settingsRowTitle")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        if object_prefix:
            setattr(self, f"{object_prefix}_title", title)

        label_row.addWidget(title)
        label_row.addStretch()
        layout.addLayout(label_row)
        layout.addWidget(selector, alignment=Qt.AlignHCenter)

        return row

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus(Qt.PopupFocusReason)
        self.raise_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.help_popup is not None:
            self.help_popup.close()
            self.help_popup = None
        super().closeEvent(event)

    def load_values(self):
        self.language_selector.set_current_value(self.settings.get("language"))
        self.persistent_selector.set_current_value(bool(self.settings.get("persistent_mode")))
        self.context_help_selector.set_current_value(bool(self.settings.get("show_context_help", True)))

    def mark_dirty(self, *_args):
        if self._loading:
            return

    def apply_values(self, *_args):
        if self._loading:
            return

        self.settings["language"] = self.language_selector.current_value()
        self.settings["persistent_mode"] = bool(self.persistent_selector.current_value())
        self.settings["show_context_help"] = bool(self.context_help_selector.current_value())
        SettingsStore.save(self.settings)
        self.settingsChanged.emit(dict(self.settings))

    def show_setting_help(self, prefix, button):
        if not prefix:
            return

        title_key = f"settings.{prefix}.title"
        description_key = f"settings.{prefix}.description"

        if self.help_popup is not None:
            self.help_popup.close()
            self.help_popup = None

        popup = SettingsHelpPopup(tr(title_key), tr(description_key), self)
        x = button.x() + button.width() + 8
        y = button.y() - 8
        if x + popup.width() > self.width() - 8:
            x = max(8, self.width() - popup.width() - 8)
            y = button.y() + button.height() + 8
        if y + popup.height() > self.height() - 8:
            y = max(8, self.height() - popup.height() - 8)
        popup.move(x, y)
        popup.show()
        popup.raise_()
        self.help_popup = popup

    def refresh_translated_labels(self):
        if hasattr(self, "settings_title"):
            self.settings_title.setText(tr("settings.title"))

        for selector in (
            getattr(self, "language_selector", None),
            getattr(self, "persistent_selector", None),
            getattr(self, "context_help_selector", None),
        ):
            if selector is not None:
                selector._update_label()

        rows = (
            ("language_title", "settings.language.title"),
            ("persistent_title", "settings.persistent.title"),
            ("context_help_title", "settings.context_help.title"),
        )
        for title_attr, title_key in rows:
            label = getattr(self, title_attr, None)
            if label is not None:
                label.setText(tr(title_key))

        if hasattr(self, "apply_button"):
            self.apply_button.setText(tr("settings.apply"))

    def apply_style(self):
        self.setStyleSheet("""
        QWidget#settingsPopover {
            background-color: #ffffff;
            border: {panel_border_width}px solid #2f6cff;
            border-radius: {panel_radius}px;
        }

        QWidget#settingsPopover QWidget {
            color: #1f2937;
            font-family: Inter, Segoe UI, Arial;
            font-size: 12px;
        }

        QLabel#settingsPopoverTitle {
            color: #334155;
            font-size: 13px;
            font-weight: 800;
        }

        QLabel#settingsRowTitle {
            color: #1f2937;
            font-size: 12px;
            font-weight: 700;
        }

        QPushButton#helpButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {radius_36}px;
            padding: 0px;
            color: #2f6cff;
            font-weight: 700;
            font-size: 11px;
        }

        QPushButton#helpButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QWidget#settingsPillSelector {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {radius_28}px;
        }

        QLabel#settingsPillValue {
            background-color: #ffffff;
            border: none;
            color: #1f2937;
            padding: 0px;
        }

        QPushButton#settingsPillPrevious,
        QPushButton#settingsPillNext {
            background-color: transparent;
            border: none;
            border-radius: 0px;
            padding: 0px;
            font-weight: bold;
            color: #334155;
        }

        QPushButton#settingsPillPrevious {
            border-right: 1px solid #e2e8f0;
            border-top-left-radius: 7px;
            border-bottom-left-radius: 7px;
        }

        QPushButton#settingsPillNext {
            border-left: 1px solid #e2e8f0;
            border-top-right-radius: 7px;
            border-bottom-right-radius: 7px;
        }

        QPushButton#settingsPillPrevious:hover,
        QPushButton#settingsPillNext:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QPushButton#settingsApplyButton {
            background-color: #2f6cff;
            border: 1px solid #2f6cff;
            border-radius: {radius_30}px;
            color: #ffffff;
            font-size: 12px;
            font-weight: 800;
        }

        QPushButton#settingsApplyButton:enabled {
            color: #ffffff;
        }

        QPushButton#settingsApplyButton:hover {
            background-color: #1d4ed8;
            border: 1px solid #1d4ed8;
            color: #ffffff;
        }

        QPushButton#settingsApplyButton:pressed {
            background-color: #1e40af;
            border: 1px solid #1e40af;
            color: #ffffff;
        }
        """.replace("{panel_border_width}", str(PANEL_BORDER_WIDTH))
            .replace("{panel_radius}", str(PANEL_RADIUS))
            .replace("{radius_28}", str(op_radius(28)))
            .replace("{radius_30}", str(op_radius(30)))
            .replace("{radius_36}", str(op_radius(36))))

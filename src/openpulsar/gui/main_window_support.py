"""Backward-compatible re-exports for historical MainWindow imports.

Most widgets and helpers now live in focused modules under ``gui.widgets`` or
``gui.profile``.  This module remains intentionally tiny while older call sites
are migrated to direct imports.
"""

from .profile.profile_extras_store import ProfileExtrasStore, apply_profile_extras
from .widgets.common_widgets import (
    ASSETS_DIR,
    LED_PALETTE,
    TAB_ICONS,
    apply_openpulsar_panel_effect,
    asset_path,
    hex_to_color,
    make_section_header,
    picture_path,
    qss_url,
)
from .widgets.dpi_widgets import DpiValueControl
from .widgets.keyboard_widgets import (
    KeyboardCommandRow,
    KeyboardCommandsEditor,
    KeyboardShortcutButton,
    OpenPulsarScrollBar,
    shortcut_to_text,
)
from .widgets.mouse_button_widgets import MouseButtonCombo, MouseButtonEditor
from .widgets.qt_delegates import ActionTreeDelegate, CenteredComboDelegate
from .widgets.sensor_widgets import SensorValueControl

__all__ = [
    "ASSETS_DIR",
    "LED_PALETTE",
    "TAB_ICONS",
    "ActionTreeDelegate",
    "CenteredComboDelegate",
    "DpiValueControl",
    "KeyboardCommandRow",
    "KeyboardCommandsEditor",
    "KeyboardShortcutButton",
    "MouseButtonCombo",
    "MouseButtonEditor",
    "OpenPulsarScrollBar",
    "ProfileExtrasStore",
    "SensorValueControl",
    "apply_openpulsar_panel_effect",
    "apply_profile_extras",
    "asset_path",
    "hex_to_color",
    "make_section_header",
    "picture_path",
    "qss_url",
    "shortcut_to_text",
]

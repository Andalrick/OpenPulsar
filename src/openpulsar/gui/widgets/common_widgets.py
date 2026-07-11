"""Shared OpenPulsar GUI helpers and lightweight widget utilities."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QLabel, QGraphicsDropShadowEffect, QHBoxLayout, QWidget
from ..metrics import HEADER_HEIGHT

from openpulsar.core.dpi import Color
from openpulsar.gui import theme


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"


def asset_path(name, category=None):
    """Return an absolute path for an OpenPulsar asset.

    ``name`` may be a plain filename (icon/background) or a relative path such
    as ``Pulsar/XliteV3_Wired_size2_device.svg`` for device illustrations.
    """
    if category is not None:
        return str(ASSETS_DIR / category / name)

    candidates = (
        ASSETS_DIR / "icons" / name,
        ASSETS_DIR / "backgrounds" / name,
        ASSETS_DIR / "devices" / name,
        ASSETS_DIR / name,
    )
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(ASSETS_DIR / "icons" / name)


def picture_path(name):
    """Compatibility helper for historical call sites."""
    return asset_path(name)


def qss_url(name):
    """Return an asset path suitable for use inside Qt stylesheets."""
    return f'"{Path(asset_path(name)).as_posix()}"'


LED_PALETTE = [
    ("Red", "#FF0000"),
    ("Pink", "#FF00AA"),
    ("Purple", "#A000FF"),
    ("Blue", "#0000FF"),
    ("Cyan", "#00FFFF"),
    ("Green", "#00FF00"),
    ("Yellow", "#FFFF00"),
    ("Orange", "#FF8000"),
    ("White", "#FFFFFF"),
    ("Off", "#000000"),
]


TAB_ICONS = {
    "buttons": {
        "active": picture_path("icon_mouse_white.svg"),
        "inactive": picture_path("icon_mouse_blue.svg"),
    },
    "keyboard_commands": {
        "active": picture_path("icon_keyboard_white.svg"),
        "inactive": picture_path("icon_keyboard_blue.svg"),
    },
}


def hex_to_color(hex_value):
    value = hex_value.lstrip("#")
    return Color(
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def apply_openpulsar_panel_effect(widget, blur=None, offset_y=None, alpha=None):
    """Apply the subtle OpenPulsar floating-panel shadow."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur if blur is not None else theme.OP_PANEL_SHADOW_BLUR)
    effect.setOffset(0, offset_y if offset_y is not None else theme.OP_PANEL_SHADOW_OFFSET_Y)
    color = QColor(theme.OP_PANEL_SHADOW_COLOR)
    color.setAlpha(alpha if alpha is not None else theme.OP_PANEL_SHADOW_ALPHA)
    effect.setColor(color)
    widget.setGraphicsEffect(effect)


def apply_openpulsar_control_effect(widget, blur=None, offset_y=None, alpha=None):
    """Apply the very small OpenPulsar shadow used by floating controls."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur if blur is not None else theme.OP_CONTROL_SHADOW_BLUR)
    effect.setOffset(0, offset_y if offset_y is not None else theme.OP_CONTROL_SHADOW_OFFSET_Y)
    color = QColor(theme.OP_PANEL_SHADOW_COLOR)
    color.setAlpha(alpha if alpha is not None else theme.OP_CONTROL_SHADOW_ALPHA)
    effect.setColor(color)
    widget.setGraphicsEffect(effect)


def make_section_header(icon_path, title):
    header = QWidget()
    header.setObjectName("sectionHeader")
    # Same height as the main tabs: panel titles align visually.
    header.setFixedHeight(HEADER_HEIGHT)

    layout = QHBoxLayout(header)
    layout.setContentsMargins(0, 1, 0, 0)
    layout.setSpacing(6)
    layout.setAlignment(Qt.AlignVCenter)

    icon = QLabel()
    icon.setObjectName("sectionIcon")
    icon.setFixedSize(20, 20)
    icon.setAlignment(Qt.AlignCenter)
    icon.setPixmap(
        QPixmap(icon_path).scaled(
            16,
            16,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
    )

    label = QLabel(title)
    label.setObjectName("sectionTitle")

    layout.addWidget(icon)
    layout.addWidget(label)
    layout.addStretch()

    return header

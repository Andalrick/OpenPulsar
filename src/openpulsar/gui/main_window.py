from openpulsar.i18n import tr
from openpulsar.logging_utils import get_logger
from .settings_dialog import SettingsDialog, SettingsStore
from . import theme
from PySide6.QtWidgets import (
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QStyle,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListView,
    QPushButton,
    QLabel,
    QComboBox,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QCheckBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QSpinBox,
    QLineEdit,
    QMenu,
    QWidgetAction,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QScrollArea,
    QScrollBar,
    QApplication,
    QSystemTrayIcon,
    QGraphicsDropShadowEffect,
)

from openpulsar.devices.registry import find_supported_device
from openpulsar.devices.pulsar import PulsarXliteWired
from openpulsar.core.device_mapper import (
    read_profile_from_mouse,
    apply_profile_to_mouse,
    BUTTON_IDS,
    encode_button_action,
)
from openpulsar.core.serialization import (
    save_profile as save_profile_file,
    load_profile as load_profile_file,
)
from openpulsar.core.dpi import DpiStage, Color

from openpulsar.core.buttons import (
    DisabledAction,
    MouseAction,
    MediaAction,
    DpiAction,
    KeyboardAction,
)

from openpulsar.core.buttons import OpenPulsarSpecialAction
from openpulsar.hid import HID_MODS, HID_KEYS
from openpulsar.core.special_actions import SpecialAction
from openpulsar.core.global_shortcuts import GlobalShortcutManager

from PySide6.QtCore import (
    Qt,
    QSignalBlocker,
    QThread,
    Signal,
    QTimer,
    QSize,
    QRectF,
    QEvent,
    QProcess,
)

from PySide6.QtGui import QColor, QPixmap, QIcon, QPainter, QKeySequence, QAction, QActionGroup, QPen, QBrush, QFont, QPalette
from functools import partial
from copy import deepcopy

logger = get_logger(__name__)
from pathlib import Path
import json
import os
import select
import sys
import time


from .widgets.led_widgets import (
    LedSettingsButton,
    LedGainControl,
    LedChoiceControl,
    LedVerticalSlider,
)
from .profile.profile_extras_store import ProfileExtrasStore, apply_profile_extras
from .widgets.common_widgets import (
    ASSETS_DIR,
    LED_PALETTE,
    TAB_ICONS,
    apply_openpulsar_control_effect,
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
from .widgets.popup_widgets import HelpPopup, AboutPopup, AboutHoverButton
from .main_window_styles import (
    DARK_THEME_OVERLAY_QSS,
    background_stylesheet,
    light_theme_stylesheet,
)
from .main_window_actions import action_to_text as format_button_action
from .main_window_actions import text_to_action as parse_button_action
from .main_window_led import (
    apply_led_correction_to_color,
    led_correction_gains_for_profile,
    remove_led_correction_from_color,
)
from .main_window_profile_style import profile_segment_style
from .main_window_led_panel import LedPanelMixin
from .main_window_dpi_panel import DpiPanelMixin
from .main_window_profiles import ProfileMixin

from .main_window_navigation import (
    _main_tab_style,
    select_main_tab,
)
from .main_window_shortcuts import (
    start_global_shortcuts,
    on_global_shortcut_pressed,
    on_global_shortcuts_availability_changed,
)
from .main_window_tray import TrayMixin
from .main_window_dialogs import DialogMixin

from .main_window_device import DeviceMixin

class MainWindow(DeviceMixin, ProfileMixin, DpiPanelMixin, LedPanelMixin, TrayMixin, DialogMixin, QMainWindow):
    _main_tab_style = _main_tab_style
    select_main_tab = select_main_tab

    start_global_shortcuts = start_global_shortcuts
    on_global_shortcut_pressed = on_global_shortcut_pressed
    on_global_shortcuts_availability_changed = on_global_shortcuts_availability_changed


    def __init__(self, start_in_tray=False):
        super().__init__()

        self.start_in_tray = bool(start_in_tray)
        self._force_quit = False
        self._shutting_down = False

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.cleanup_resources)

        self.setWindowTitle("OpenPulsar")
        self.setFixedSize(540, 720)
        self.app_settings = SettingsStore.load()
        self.persistent_mode = bool(self.app_settings.get("persistent_mode", False))
        self.apply_light_theme()

        self.mouse = find_supported_device() or PulsarXliteWired()
        self.mouse.open()

        self.active_slot = 1
        self.active_dpi_stage = 1
        self._usb_connected = True
        self._last_firmware = tr("status.unknown")
        self.listener = None
        self.light_refresh_timer = None
        self.start_hidraw_listener()

        self.current_slot = 1
        self.current_profile = None
        self.dpi_stage_colors = []
        self._loading_profile = False
        self._applying_profile = False

        self._pending_apply = False
        self._pending_sections = set()
        self._pending_sections_by_slot = {}
        self._pending_profiles_by_slot = {}
        self._pending_dpi_stage_base_count_by_slot = {}

        self.help_popup = None
        self.about_popup = None
        self.settings_overlay = None
        self.global_shortcut_manager = None
        self.context_help_buttons = []

        self.auto_apply_timer = QTimer(self)
        self.auto_apply_timer.setSingleShot(True)
        self.auto_apply_timer.timeout.connect(self.flush_auto_apply)

        from .main_window_ui import build_main_ui
        build_main_ui(self)
        self.start_light_refresh()

    # LED panel behavior lives in LedPanelMixin.

    # Dialog / popover behavior lives in DialogMixin.

    def led_correction_gains(self, profile=None):
        profile = profile or getattr(self, "current_profile", None)
        return led_correction_gains_for_profile(profile)

    def apply_led_correction(self, color, profile=None):
        return apply_led_correction_to_color(
            color,
            self.led_correction_gains(profile),
        )

    def remove_led_correction(self, color, profile=None):
        return remove_led_correction_from_color(
            color,
            self.led_correction_gains(profile),
        )

    def profile_with_led_correction(self, profile):
        calibrated = deepcopy(profile)
        for stage in calibrated.dpi_stages:
            stage.color = self.apply_led_correction(stage.color, profile=profile)
        return calibrated

    def led_correction_changed(self, previous_settings, new_settings):
        return False

    def refresh_profiles_after_led_correction_change(self, previous_settings):
        # LED correction is now profile-scoped. Only the active profile is
        # rewritten when its own gain changes, via auto_apply("colors").
        return

    def on_settings_changed(self, settings):
        self.app_settings = dict(settings)
        self.apply_application_settings()
        self.update_tray_visibility_action()
        self.restart_openpulsar()

    def apply_application_settings(self):
        if not hasattr(self, "app_settings"):
            self.app_settings = SettingsStore.load()

        # OpenPulsar assume désormais un thème clair unique avec son fond géométrique.
        self.apply_light_theme()
        self.update_context_help_visibility()

    def apply_background_setting(self):
        central = self.centralWidget()
        if central is None:
            return

        background = self.app_settings.get("background", "openpulsar")
        central.setStyleSheet(background_stylesheet(background))

    def apply_theme_overlay(self):
        theme = self.app_settings.get("theme", "system")

        if theme != "openpulsar_dark":
            return

        # Première version volontairement sobre : le thème sombre garde les
        # composants OpenPulsar mais assombrit le fond global et les cartes.
        self.setStyleSheet(self.styleSheet() + DARK_THEME_OVERLAY_QSS)

    def apply_light_theme(self):
        self.setStyleSheet(light_theme_stylesheet())


    def _flush_pending_changes_before_close(self):
        """Best-effort final flush before a real application shutdown.

        In non-persistent mode, closing the window must not silently drop the
        last auto-apply batch. The normal auto-apply timer may still be waiting
        for its debounce delay, so stop it and flush immediately.
        """
        if not getattr(self, "_pending_apply", False):
            return

        logger.debug("Closing with pending changes: flushing before shutdown")

        if hasattr(self, "auto_apply_timer"):
            self.auto_apply_timer.stop()

        self.flush_auto_apply()

    def closeEvent(self, event):
        if self.persistent_mode and not self._force_quit:
            self.hide()
            self.update_tray_visibility_action()
            event.ignore()
            return

        self._flush_pending_changes_before_close()
        self.cleanup_resources()
        super().closeEvent(event)

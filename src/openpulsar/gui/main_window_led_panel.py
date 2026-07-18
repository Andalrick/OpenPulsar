from openpulsar.i18n import tr
from openpulsar.logging_utils import get_logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from .errors import HARDWARE_STATE_ERRORS
from .metrics import ROW_HEIGHT
from .profile.profile_extras_store import ProfileExtrasStore
from .widgets.common_widgets import picture_path
from .widgets.led_widgets import LedChoiceControl, LedGainControl, LedIndicator

import time

logger = get_logger(__name__)


class LedPanelMixin:
    def build_led_panel(self):
        panel = QWidget()
        panel.setObjectName("ledManagementPanel")
        panel.setAttribute(Qt.WA_StyledBackground, True)

        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self.led_red_gain_control = LedGainControl(100)
        self.led_green_gain_control = LedGainControl(100)
        self.led_blue_gain_control = LedGainControl(100)
        self.led_gain_controls = [
            self.led_red_gain_control,
            self.led_green_gain_control,
            self.led_blue_gain_control,
        ]

        for css_color, control, key in (
            ("#ff0000", self.led_red_gain_control, "led_red_gain"),
            ("#00ff00", self.led_green_gain_control, "led_green_gain"),
            ("#0000ff", self.led_blue_gain_control, "led_blue_gain"),
        ):
            root.addWidget(
                self.make_led_control_row(css_color, control),
                alignment=Qt.AlignHCenter,
            )
            control.valueChanged.connect(
                lambda value, key=key: self.on_led_setting_changed(key, value)
            )

        root.addWidget(self.make_led_subtitle_row(tr("led.brightness_pulse")), alignment=Qt.AlignHCenter)

        self.led_brightness_control = LedChoiceControl(
            [
                ("25 %", 25),
                ("50 %", 50),
                ("75 %", 75),
                ("100 %", 100),
            ],
            100,
        )
        self.led_pulse_control = LedChoiceControl(
            [
                (tr("led.pulse.very_slow"), 25),
                (tr("led.pulse.slow"), 50),
                (tr("led.pulse.medium"), 75),
                (tr("led.pulse.fast"), 100),
            ],
            75,
        )

        self.led_brightness_control.valueChanged.connect(
            lambda value: self.on_led_setting_changed("led_brightness", value)
        )
        self.led_pulse_control.valueChanged.connect(
            lambda value: self.on_led_setting_changed("led_pulse", value)
        )

        brightness_row, self.led_brightness_toggle = self.make_led_control_row(
            "☀",
            self.led_brightness_control,
            text_icon=True,
            toggle_callback=self.toggle_led_enabled,
        )
        root.addWidget(brightness_row, alignment=Qt.AlignHCenter)

        pulse_row, self.led_pulse_toggle = self.make_led_control_row(
            "♡",
            self.led_pulse_control,
            text_icon=True,
            toggle_callback=self.toggle_led_pulse_enabled,
        )
        root.addWidget(pulse_row, alignment=Qt.AlignHCenter)

        root.addStretch()

        return panel

    def make_led_subtitle_row(self, title):
        row = QWidget()
        row.setObjectName("ledSubtitleRow")
        row.setFixedSize(160, ROW_HEIGHT)

        layout = QVBoxLayout(row)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(6)

        separator = QWidget()
        separator.setObjectName("ledPanelSeparator")
        separator.setFixedHeight(1)

        label = QLabel(title)
        label.setObjectName("ledSubtitleLabel")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setFixedHeight(24)

        layout.addWidget(separator)
        layout.addWidget(label)
        return row

    def make_led_control_row(self, marker, control, text_icon=False, toggle_callback=None):
        row = QWidget()
        row.setObjectName("ledGainRow")
        row.setFixedSize(160, ROW_HEIGHT)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(4, 7, 4, 7)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignVCenter)

        if text_icon:
            icon_button = QPushButton()
            icon_button.setObjectName("ledGainColorButton")
            icon_button.setFixedSize(24, 24)
            icon_button.setText(str(marker))
            icon_button.setCursor(Qt.PointingHandCursor)
            if callable(toggle_callback):
                icon_button.clicked.connect(toggle_callback)
            icon_button.setStyleSheet("""
                QPushButton#ledGainColorButton {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    border-radius: 12px;
                    color: #64748b;
                    font-size: 14px;
                    font-weight: 700;
                    padding: 0px;
                }
                QPushButton#ledGainColorButton:hover {
                    background-color: #eef4ff;
                    border: 1px solid #2f6cff;
                    color: #1d4ed8;
                }
                QPushButton#ledGainColorButton[ledToggleActive="true"] {
                    background-color: #2f6cff;
                    border: 1px solid #2f6cff;
                    color: #ffffff;
                }
                QPushButton#ledGainColorButton[ledToggleActive="true"]:hover {
                    background-color: #1d4ed8;
                    border: 1px solid #1d4ed8;
                    color: #ffffff;
                }
                QPushButton#ledGainColorButton[ledToggleActive="false"] {
                    background-color: #ffffff;
                    border: 1px solid #cbd5e1;
                    color: #64748b;
                }
                QPushButton#ledGainColorButton[ledToggleActive="false"]:hover {
                    background-color: #eef4ff;
                    border: 1px solid #2f6cff;
                    color: #1d4ed8;
                }
            """)
        else:
            # Exact same 26 px swatch used by the DPI-stage rows.
            icon_button = LedIndicator(marker)
            icon_button.setCursor(Qt.ArrowCursor)
            icon_button.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        layout.addWidget(icon_button, alignment=Qt.AlignVCenter)
        layout.addWidget(control, alignment=Qt.AlignVCenter)
        if text_icon:
            return row, icon_button
        return row

    def toggle_led_panel(self):
        if not hasattr(self, "dpi_content_stack"):
            return
        self.set_led_panel_visible(self.dpi_content_stack.currentWidget() is not self.led_panel)

    def set_led_panel_visible(self, visible):
        if not hasattr(self, "dpi_content_stack"):
            return
        visible = bool(visible)

        self.led_settings_button.setProperty("ledPanelOpen", visible)
        self.led_settings_button.style().unpolish(self.led_settings_button)
        self.led_settings_button.style().polish(self.led_settings_button)
        self.led_settings_button.update()
        if self.dpi_header_title is not None:
            self.dpi_header_title.setText(tr("led.rgb_gain") if visible else "DPI")
            self.dpi_header_title.setContentsMargins(0, 0, 0, 0)
        if self.dpi_header_icon is not None:
            icon_name = "icon_rgb_sliders.svg" if visible else "icon_target.svg"
            self.dpi_header_icon.setPixmap(
                QPixmap(picture_path(icon_name)).scaled(
                    16,
                    16,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
            self.dpi_header_icon.show()
        if visible:
            self.sync_led_panel_from_profile()
            self.dpi_content_stack.setCurrentWidget(self.led_panel)
        else:
            self.dpi_content_stack.setCurrentWidget(self.dpi_page)


    def _set_led_toggle_visual_state(self, button, active):
        if button is None:
            return
        button.setProperty("ledToggleActive", bool(active))
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

    def update_led_toggle_states(self):
        profile = self.current_profile
        led_enabled = bool(getattr(profile, "led_enabled", True)) if profile is not None else True
        pulse_enabled = bool(getattr(profile, "led_pulse_enabled", False)) if profile is not None else False

        if hasattr(self, "led_brightness_control"):
            self.led_brightness_control.setActive(led_enabled)
        if hasattr(self, "led_pulse_control"):
            self.led_pulse_control.setActive(pulse_enabled and led_enabled)

        self._set_led_toggle_visual_state(getattr(self, "led_brightness_toggle", None), led_enabled)
        self._set_led_toggle_visual_state(getattr(self, "led_pulse_toggle", None), pulse_enabled and led_enabled)

    def toggle_led_enabled(self):
        if self.current_profile is None or self._loading_profile:
            return
        self.current_profile.led_enabled = not bool(getattr(self.current_profile, "led_enabled", True))
        ProfileExtrasStore.save_slot(self.current_slot, self.current_profile)
        self.update_led_toggle_states()
        self.auto_apply("led_settings")

    def toggle_led_pulse_enabled(self):
        if self.current_profile is None or self._loading_profile:
            return
        if not bool(getattr(self.current_profile, "led_enabled", True)):
            return
        self.current_profile.led_pulse_enabled = not bool(getattr(self.current_profile, "led_pulse_enabled", False))
        ProfileExtrasStore.save_slot(self.current_slot, self.current_profile)
        self.update_led_toggle_states()
        self.auto_apply("led_settings")

    def sync_led_panel_from_profile(self):
        profile = self.current_profile
        mapping = (
            (getattr(self, "led_red_gain_control", None), "led_red_gain", 100),
            (getattr(self, "led_green_gain_control", None), "led_green_gain", 100),
            (getattr(self, "led_blue_gain_control", None), "led_blue_gain", 100),
            (getattr(self, "led_brightness_control", None), "led_brightness", 100),
            (getattr(self, "led_pulse_control", None), "led_pulse", 75),
        )
        for widget, attr, fallback in mapping:
            if widget is not None:
                widget.blockSignals(True)
                widget.setValue(getattr(profile, attr, fallback) if profile is not None else fallback)
                widget.blockSignals(False)
        self.update_led_toggle_states()

    def on_led_setting_changed(self, key, value):
        if self.current_profile is None or self._loading_profile:
            return

        value = max(0, min(100, int(value)))
        setattr(self.current_profile, key, value)
        ProfileExtrasStore.save_slot(self.current_slot, self.current_profile)

        if key in ("led_red_gain", "led_green_gain", "led_blue_gain"):
            if hasattr(self, "refresh_dpi_led_display_colors"):
                self.refresh_dpi_led_display_colors()
            self.auto_apply("colors")
        elif key in ("led_brightness", "led_pulse", "led_enabled", "led_pulse_enabled"):
            self.update_led_toggle_states()
            self.auto_apply("led_settings")

    def apply_led_output_settings_to_mouse(self, profile=None, slot=None):
        if not getattr(self, "_usb_connected", False):
            return

        profile = profile or self.current_profile
        slot = int(slot or self.current_slot)
        if profile is None:
            return

        led_enabled = bool(getattr(profile, "led_enabled", True))
        pulse_enabled = bool(getattr(profile, "led_pulse_enabled", False))

        try:
            brightness_percent = int(getattr(profile, "led_brightness", 100))
        except (TypeError, ValueError):
            brightness_percent = 100
        brightness_percent = max(25, min(100, brightness_percent))

        lo, hi = self.mouse.capabilities.brightness_range
        brightness_value = int(round(lo + ((hi - lo) * brightness_percent / 100.0)))

        try:
            pulse_percent = int(getattr(profile, "led_pulse", 75))
        except (TypeError, ValueError):
            pulse_percent = 75
        pulse_percent = max(25, min(100, pulse_percent))

        try:
            if not led_enabled:
                self.mouse.set_led_effect("off", slot)
                time.sleep(0.03)
                return

            self.mouse.set_brightness(brightness_value, slot)
            time.sleep(0.02)

            if not pulse_enabled:
                self.mouse.set_led_effect("steady", slot)
            else:
                self.mouse.set_led_effect("breath", slot)
                if getattr(self.mouse.capabilities, "has_breath_speed", False):
                    lo_speed, hi_speed = self.mouse.capabilities.breath_speed_range
                    # Firmware speed is inverted on tested Pulsar devices:
                    # lower raw value means faster breathing.
                    speed = int(round(hi_speed - ((hi_speed - lo_speed) * pulse_percent / 100.0)))
                    self.mouse.set_breath_speed(speed, slot)
            time.sleep(0.03)
        except HARDWARE_STATE_ERRORS as e:
            logger.debug(f"LED OUTPUT SETTINGS FAILED P{slot}: {e}")

"""Minimal MainWindow smoke tests.

These tests instantiate the real Qt window with a fake mouse driver.  They are
kept intentionally small: the goal is to catch GUI refactor regressions such as
missing imports, broken mixin wiring, or shutdown crashes without requiring
Pulsar hardware.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from openpulsar.core.buttons import DpiAction, MouseAction  # noqa: E402
from openpulsar.devices.pulsar.xlite_wired import PulsarXliteWired  # noqa: E402
from openpulsar.gui.profile.profile_extras_store import ProfileExtrasStore  # noqa: E402
from openpulsar.gui.settings_dialog import SettingsStore  # noqa: E402


class FakeMouse:
    """Small in-memory mouse driver used by GUI smoke tests."""

    capabilities = PulsarXliteWired.capabilities

    def __init__(self):
        self.current_vid_pid = self.capabilities.vid_pid_pairs[0]
        self.opened = False
        self.closed = False
        self.active_stage = 1
        self.diag = []

    def _diag(self, message: str) -> None:
        self.diag.append(str(message))

    def open(self) -> None:
        self.opened = True

    def close(self) -> None:
        self.closed = True

    def reconnect(self) -> None:
        self.opened = True

    def is_connected(self) -> bool:
        return True

    def get_model_name(self) -> str:
        return self.capabilities.name

    def get_connection_type(self) -> str:
        return "usb"

    def get_device_image(self):
        return self.capabilities.image

    def get_firmware_version(self) -> str:
        return "VTEST"

    def get_supported_polling_rates(self):
        return list(self.capabilities.polling_rates)

    def get_supported_lod_values(self):
        return list(self.capabilities.lod_values)

    def set_diagnostic_suppressed(self, _enabled: bool) -> None:
        pass

    def get_dpi_stages(self, _profile: int) -> dict:
        return {
            "active": self.active_stage,
            "count": 3,
            "stages": [(400, 400), (800, 800), (1200, 1200)],
        }

    def set_dpi_stages(self, _stages, active: int, _profile: int) -> None:
        self.active_stage = int(active)

    def get_active_dpi_stage(self, _profile: int) -> int:
        return self.active_stage

    def set_active_dpi_stage(self, stage: int, _profile: int) -> None:
        self.active_stage = int(stage)

    def get_stage_color(self, stage: int, _profile: int):
        colors = {
            1: (255, 0, 0),
            2: (0, 255, 0),
            3: (0, 0, 255),
        }
        return colors.get(int(stage), (255, 255, 255))

    def set_stage_color(self, *_args) -> None:
        pass

    def get_polling_rate(self, _profile: int = 1) -> int:
        return 1000

    def set_polling_rate(self, *_args) -> None:
        pass

    def get_debounce(self, _profile: int = 1) -> int:
        return 3

    def set_debounce(self, *_args) -> None:
        pass

    def get_lod(self, _profile: int = 1) -> float:
        return 1.0

    def set_lod(self, *_args) -> None:
        pass

    def get_motion_sync(self, _profile: int = 1) -> bool:
        return False

    def set_motion_sync(self, *_args) -> None:
        pass

    def get_angle_snap(self, _profile: int = 1) -> bool:
        return False

    def set_angle_snap(self, *_args) -> None:
        pass

    def get_ripple_control(self, _profile: int = 1) -> bool:
        return False

    def set_ripple_control(self, *_args) -> None:
        pass

    def get_brightness(self, _profile: int = 1) -> int:
        return 255

    def set_brightness(self, *_args) -> None:
        pass

    def get_led_effect(self, _profile: int = 1) -> str:
        return "steady"

    def set_led_effect(self, *_args) -> None:
        pass

    def get_breath_speed(self, _profile: int = 1) -> int:
        return 25

    def set_breath_speed(self, *_args) -> None:
        pass

    def get_button(self, button_id: int, _profile: int):
        if button_id == self.capabilities.buttons.get("dpi"):
            action = DpiAction(3)
        else:
            action = MouseAction(button_id)
        from openpulsar.core.device_mapper import encode_button_action

        return encode_button_action(action)

    def set_button(self, *_args) -> None:
        pass

    def set_active_profile(self, *_args) -> None:
        pass

    def refresh_profile(self, *_args) -> None:
        pass


@pytest.fixture
def qapp():
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def isolated_config(monkeypatch, tmp_path):
    settings_file = tmp_path / "settings.json"
    profile_extras_file = tmp_path / "profile_extras.json"
    monkeypatch.setattr(SettingsStore, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(SettingsStore, "CONFIG_FILE", settings_file)
    monkeypatch.setattr(SettingsStore, "load", classmethod(lambda cls: dict(cls.DEFAULTS)))
    monkeypatch.setattr(ProfileExtrasStore, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(ProfileExtrasStore, "CONFIG_FILE", profile_extras_file)


def test_main_window_constructs_and_closes(monkeypatch, qapp, isolated_config):
    from openpulsar.gui import main_window as main_window_module
    from openpulsar.gui.main_window import MainWindow

    fake_mouse = FakeMouse()
    monkeypatch.setattr(main_window_module, "find_supported_device", lambda: fake_mouse)
    monkeypatch.setattr(MainWindow, "start_global_shortcuts", lambda self: None)

    window = MainWindow(start_in_tray=False)
    try:
        assert window.mouse is fake_mouse
        assert fake_mouse.opened is True
        assert window.current_profile is not None
        assert window.current_slot == 1
        assert window.active_dpi_stage == 1
    finally:
        window.cleanup_resources()
        window.close()

    assert fake_mouse.closed is True


def test_auto_apply_keeps_profile_slot_context(monkeypatch, qapp, isolated_config):
    from openpulsar.gui import main_window as main_window_module
    from openpulsar.gui.main_window import MainWindow

    fake_mouse = FakeMouse()
    calls = []

    def record_motion_sync(value, slot):
        calls.append((int(slot), bool(value)))

    fake_mouse.set_motion_sync = record_motion_sync
    monkeypatch.setattr(main_window_module, "find_supported_device", lambda: fake_mouse)
    monkeypatch.setattr(MainWindow, "start_global_shortcuts", lambda self: None)

    window = MainWindow(start_in_tray=False)
    try:
        # P1: user enables Motion Sync and auto-apply captures P1 immediately.
        window.motion_sync_check.setChecked(True)
        window.auto_apply("motion_sync")

        # User switches to P2 before the deferred auto-apply flushes.
        window.load_slot(1)
        window.motion_sync_check.setChecked(False)
        window.auto_apply("motion_sync")

        window.flush_auto_apply()
    finally:
        window.cleanup_resources()
        window.close()

    assert (1, True) in calls
    assert (2, False) in calls

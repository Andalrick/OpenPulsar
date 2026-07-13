"""Tests for local per-profile UI extras persistence."""

from openpulsar.core.dpi import Color, DpiStage
from openpulsar.core.profile import Profile
from openpulsar.gui.profile.profile_extras_store import (
    ProfileExtrasStore,
    apply_profile_extras,
    restore_logical_led_colors,
)


def _isolate_store(tmp_path, monkeypatch):
    config_dir = tmp_path / "OpenPulsar"
    config_file = config_dir / "profile_extras.json"
    monkeypatch.setattr(ProfileExtrasStore, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(ProfileExtrasStore, "CONFIG_FILE", config_file)
    return config_file


def test_keyboard_commands_round_trip(tmp_path, monkeypatch):
    _isolate_store(tmp_path, monkeypatch)

    commands = [
        {"label": "Copy", "sequence": "ctrl+c"},
        {"label": "Paste", "sequence": "ctrl+v"},
    ]

    ProfileExtrasStore.save_keyboard_commands(1, commands)

    assert ProfileExtrasStore.load_keyboard_commands(1) == commands


def test_keyboard_commands_are_isolated_by_slot(tmp_path, monkeypatch):
    _isolate_store(tmp_path, monkeypatch)

    slot_1_commands = [{"label": "Copy", "sequence": "ctrl+c"}]
    slot_2_commands = [{"label": "Paste", "sequence": "ctrl+v"}]

    ProfileExtrasStore.save_keyboard_commands(1, slot_1_commands)
    ProfileExtrasStore.save_keyboard_commands(2, slot_2_commands)

    assert ProfileExtrasStore.load_keyboard_commands(1) == slot_1_commands
    assert ProfileExtrasStore.load_keyboard_commands(2) == slot_2_commands


def test_save_slot_preserves_keyboard_commands_and_led_extras(tmp_path, monkeypatch):
    _isolate_store(tmp_path, monkeypatch)

    profile = Profile(name="Profile 1")
    profile.keyboard_commands = [{"label": "Launch", "sequence": "ctrl+alt+l"}]
    profile.led_red_gain = 70
    profile.led_green_gain = 80
    profile.led_blue_gain = 90
    profile.led_enabled = False
    profile.led_brightness = 35
    profile.led_pulse_enabled = True
    profile.led_pulse = 45
    profile.dpi_stages = [
        DpiStage(800, Color(255, 128, 0)),
        DpiStage(1600, Color(0, 64, 255)),
    ]

    ProfileExtrasStore.save_slot(1, profile)
    loaded = ProfileExtrasStore.load_slot(1)

    assert loaded["keyboard_commands"] == profile.keyboard_commands
    assert loaded["led"] == {
        "red_gain": 70,
        "green_gain": 80,
        "blue_gain": 90,
        "logical_colors": [
            {"r": 255, "g": 128, "b": 0},
            {"r": 0, "g": 64, "b": 255},
        ],
        "enabled": False,
        "brightness": 35,
        "pulse_enabled": True,
        "pulse": 45,
    }


def test_apply_profile_extras_restores_keyboard_commands_and_led_values():
    profile = Profile(name="Profile 1")

    apply_profile_extras(
        profile,
        {
            "keyboard_commands": [{"label": "Mute", "sequence": "ctrl+m"}],
            "led": {
                "red_gain": 55,
                "green_gain": 65,
                "blue_gain": 75,
                "enabled": True,
                "brightness": 85,
                "pulse_enabled": True,
                "pulse": 95,
            },
        },
    )

    assert profile.keyboard_commands == [{"label": "Mute", "sequence": "ctrl+m"}]
    assert profile.led_red_gain == 55
    assert profile.led_green_gain == 65
    assert profile.led_blue_gain == 75
    assert profile.led_enabled is True
    assert profile.led_brightness == 85
    assert profile.led_pulse_enabled is True
    assert profile.led_pulse == 95


def test_restore_logical_led_colors_is_lossless_with_zero_gain():
    profile = Profile(
        name="Profile 1",
        dpi_stages=[DpiStage(800, Color(0, 0, 0))],
        led_green_gain=0,
    )
    extras = {
        "led": {
            "green_gain": 0,
            "logical_colors": [{"r": 255, "g": 128, "b": 0}],
        }
    }

    assert restore_logical_led_colors(profile, extras) is True
    assert profile.dpi_stages[0].color == Color(255, 128, 0)


def test_restore_logical_led_colors_rejects_stage_count_mismatch():
    profile = Profile(
        name="Profile 1",
        dpi_stages=[
            DpiStage(800, Color(10, 20, 30)),
            DpiStage(1600, Color(40, 50, 60)),
        ],
    )
    extras = {
        "led": {
            "logical_colors": [{"r": 255, "g": 128, "b": 0}],
        }
    }

    assert restore_logical_led_colors(profile, extras) is False
    assert profile.dpi_stages[0].color == Color(10, 20, 30)
    assert profile.dpi_stages[1].color == Color(40, 50, 60)

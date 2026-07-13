"""Persistence helpers for local per-profile UI extras."""

from pathlib import Path
import json
import os

from openpulsar.core.dpi import Color


class ProfileExtrasStore:
    """Local per-slot settings not fully stored by the mouse firmware."""

    CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "OpenPulsar"
    CONFIG_FILE = CONFIG_DIR / "profile_extras.json"

    @classmethod
    def load_all(cls):
        try:
            payload = json.loads(cls.CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        return payload if isinstance(payload, dict) else {}

    @classmethod
    def load_slot(cls, slot: int) -> dict:
        payload = cls.load_all()
        value = payload.get(str(int(slot)), {})
        return value if isinstance(value, dict) else {}

    @classmethod
    def save_all(cls, payload: dict) -> None:
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONFIG_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_keyboard_commands(cls, slot: int):
        extras = cls.load_slot(slot)
        commands = extras.get("keyboard_commands")
        if not isinstance(commands, list):
            return None
        return [command for command in commands if isinstance(command, dict)]

    @classmethod
    def save_keyboard_commands(cls, slot: int, commands) -> None:
        payload = cls.load_all()
        slot_key = str(int(slot))
        extras = payload.get(slot_key, {})
        if not isinstance(extras, dict):
            extras = {}
        extras["keyboard_commands"] = [
            command for command in list(commands or []) if isinstance(command, dict)
        ]
        payload[slot_key] = extras
        cls.save_all(payload)

    @classmethod
    def save_slot(cls, slot: int, profile) -> None:
        payload = cls.load_all()
        slot_key = str(int(slot))
        previous = payload.get(slot_key, {})
        if not isinstance(previous, dict):
            previous = {}

        payload[slot_key] = {
            "keyboard_commands": list(
                getattr(profile, "keyboard_commands", previous.get("keyboard_commands", []))
            ),
            "led": {
                "red_gain": int(getattr(profile, "led_red_gain", 100)),
                "green_gain": int(getattr(profile, "led_green_gain", 100)),
                "blue_gain": int(getattr(profile, "led_blue_gain", 100)),
                # Keep the user-facing colors losslessly.  The mouse stores
                # colors after RGB gain correction, so reading them back and
                # applying the inverse cannot recover clipped/zeroed channels
                # or rounding exactly.
                "logical_colors": [
                    {
                        "r": int(stage.color.r),
                        "g": int(stage.color.g),
                        "b": int(stage.color.b),
                    }
                    for stage in getattr(profile, "dpi_stages", [])
                ],
                "enabled": bool(getattr(profile, "led_enabled", True)),
                "brightness": int(getattr(profile, "led_brightness", 100)),
                "pulse_enabled": bool(getattr(profile, "led_pulse_enabled", False)),
                "pulse": int(getattr(profile, "led_pulse", 75)),
            },
        }
        cls.save_all(payload)


def apply_profile_extras(profile, extras: dict):
    if not isinstance(extras, dict):
        return profile

    led = extras.get("led", {})
    if not isinstance(led, dict):
        led = {}

    def percent(key, fallback):
        try:
            return max(0, min(100, int(led.get(key, fallback))))
        except (TypeError, ValueError):
            return fallback

    profile.led_red_gain = percent("red_gain", getattr(profile, "led_red_gain", 100))
    profile.led_green_gain = percent("green_gain", getattr(profile, "led_green_gain", 100))
    profile.led_blue_gain = percent("blue_gain", getattr(profile, "led_blue_gain", 100))

    stored_brightness = percent("brightness", getattr(profile, "led_brightness", 100))
    profile.led_enabled = bool(led.get("enabled", stored_brightness > 0))
    profile.led_brightness = stored_brightness if stored_brightness > 0 else 100

    stored_pulse = percent("pulse", getattr(profile, "led_pulse", 75))
    profile.led_pulse_enabled = bool(led.get("pulse_enabled", stored_pulse > 0))
    profile.led_pulse = stored_pulse if stored_pulse > 0 else 75

    commands = extras.get("keyboard_commands")
    if isinstance(commands, list):
        profile.keyboard_commands = [command for command in commands if isinstance(command, dict)]

    return profile


def restore_logical_led_colors(profile, extras: dict) -> bool:
    """Restore exact UI colors saved before hardware RGB correction.

    Return ``True`` only when the saved list is complete and valid for the
    profile currently reported by the mouse.  Older configuration files, or
    profiles whose DPI-stage count changed outside OpenPulsar, deliberately
    fall back to hardware colors plus inverse correction.
    """
    if not isinstance(extras, dict):
        return False

    led = extras.get("led", {})
    if not isinstance(led, dict):
        return False

    stored_colors = led.get("logical_colors")
    stages = getattr(profile, "dpi_stages", [])
    if not isinstance(stored_colors, list) or len(stored_colors) != len(stages):
        return False

    restored = []
    for payload in stored_colors:
        if not isinstance(payload, dict):
            return False

        try:
            channels = tuple(int(payload[channel]) for channel in ("r", "g", "b"))
        except (KeyError, TypeError, ValueError):
            return False

        if any(channel < 0 or channel > 255 for channel in channels):
            return False

        restored.append(Color(*channels))

    for stage, color in zip(stages, restored):
        stage.color = color

    return True

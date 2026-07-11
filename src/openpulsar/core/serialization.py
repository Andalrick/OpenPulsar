import json
from pathlib import Path

from .dpi import Color, DpiStage
from .profile import Profile
from .buttons import action_from_dict


def profile_to_dict(profile: Profile) -> dict:
    return {
        "name": profile.name,
        "polling_rate": profile.polling_rate,
        "debounce": profile.debounce,
        "lod": getattr(profile, "lod", 1),
        "motion_sync": profile.motion_sync,
        "angle_snap": profile.angle_snap,
        "ripple_control": profile.ripple_control,
        "dpi_stages": [
            {
                "dpi": stage.dpi,
                "color": {
                    "r": stage.color.r,
                    "g": stage.color.g,
                    "b": stage.color.b,
                },
            }
            for stage in profile.dpi_stages
        ],
        "buttons": {
            name: action.to_dict()
            for name, action in profile.buttons.items()
        },
        "active_dpi_stage": int(getattr(profile, "active_dpi_stage", 1)),
        "keyboard_commands": list(getattr(profile, "keyboard_commands", [])),
        "led": {
            "red_gain": int(getattr(profile, "led_red_gain", 100)),
            "green_gain": int(getattr(profile, "led_green_gain", 100)),
            "blue_gain": int(getattr(profile, "led_blue_gain", 100)),
            "enabled": bool(getattr(profile, "led_enabled", True)),
            "brightness": int(getattr(profile, "led_brightness", 100)),
            "pulse_enabled": bool(getattr(profile, "led_pulse_enabled", False)),
            "pulse": int(getattr(profile, "led_pulse", 75)),
        },
    }


def profile_from_dict(data: dict) -> Profile:
    led = data.get("led", {}) if isinstance(data.get("led", {}), dict) else {}

    raw_brightness = int(led.get("brightness", data.get("led_brightness", 100)))
    raw_pulse = int(led.get("pulse", data.get("led_pulse", 0)))

    return Profile(
        name=data.get("name", "Unnamed"),
        polling_rate=data.get("polling_rate", 1000),
        debounce=data.get("debounce", 3),
        lod=data.get("lod", 1),
        motion_sync=data.get("motion_sync", False),
        angle_snap=data.get("angle_snap", False),
        ripple_control=data.get("ripple_control", False),
        buttons={
            name: action_from_dict(action)
            for name, action in data.get("buttons", {}).items()
        },
        active_dpi_stage=max(1, int(data.get("active_dpi_stage", 1))),
        keyboard_commands=list(data.get("keyboard_commands", [])),
        led_red_gain=int(led.get("red_gain", data.get("led_red_gain", 100))),
        led_green_gain=int(led.get("green_gain", data.get("led_green_gain", 100))),
        led_blue_gain=int(led.get("blue_gain", data.get("led_blue_gain", 100))),
        led_enabled=bool(led.get("enabled", data.get("led_enabled", raw_brightness > 0))),
        led_brightness=max(25, raw_brightness),
        led_pulse_enabled=bool(led.get("pulse_enabled", data.get("led_pulse_enabled", raw_pulse > 0))),
        led_pulse=max(25, raw_pulse if raw_pulse > 0 else 75),
        dpi_stages=[
            DpiStage(
                dpi=stage["dpi"],
                color=Color(
                    stage["color"]["r"],
                    stage["color"]["g"],
                    stage["color"]["b"],
                ),
            )
            for stage in data.get("dpi_stages", [])
        ] or [DpiStage(800, Color(41, 150, 205))],
    )


def save_profile(profile: Profile, path: str | Path) -> None:
    path = Path(path)
    path.write_text(
        json.dumps(profile_to_dict(profile), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_profile(path: str | Path) -> Profile:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return profile_from_dict(data)

from dataclasses import dataclass, field

from .buttons import ButtonAction
from .dpi import Color, DpiStage


@dataclass
class Profile:
    name: str = "Unnamed"

    polling_rate: int = 1000
    debounce: int = 3
    lod: float = 1.0

    motion_sync: bool = False
    angle_snap: bool = False
    ripple_control: bool = False

    dpi_stages: list[DpiStage] = field(
        default_factory=lambda: [
            DpiStage(800, Color(41, 150, 205))
        ]
    )

    buttons: dict[str, ButtonAction] = field(default_factory=dict)

    # Active DPI stage is also profile-local in the mouse firmware.
    active_dpi_stage: int = 1

    # OpenPulsar-only per-profile settings. These are not all stored by the
    # mouse firmware, so the GUI persists them alongside the hardware profile.
    keyboard_commands: list[dict] = field(default_factory=list)

    led_red_gain: int = 100
    led_green_gain: int = 100
    led_blue_gain: int = 100
    led_enabled: bool = True
    led_brightness: int = 100
    led_pulse_enabled: bool = False
    led_pulse: int = 75

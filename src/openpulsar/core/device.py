"""
Core classes for OpenPulsar device drivers.

Each supported model implements a DeviceDriver subclass with its own protocol.
The GUI and CLI use DeviceCapabilities to adapt dynamically to the hardware.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeviceCapabilities:
    """Describes what a specific mouse model supports."""

    name: str                                   # e.g. "Pulsar X2A Medium Wired"
    vid_pid_pairs: list[tuple[int, int]]        # [(0x3710, 0x1404)]
    interface_num: int                          # USB interface to claim
    report_size: int                            # HID report size in bytes

    num_profiles: int                           # 5 for X2A, 1 for X2 v2 Mini
    max_dpi_stages: int                         # 6 for X2A, 4 for X2 v2 Mini
    dpi_min: int                                # 100
    dpi_max: int                                # 26000
    dpi_step: int                               # 100

    buttons: dict[str, int]                     # name -> button_id
    polling_rates: list[int]                    # [125, 250, 500, 1000]
    lod_values: list[float]                     # [0.7, 1.0, 2.0] in mm

    # Optional per-VID:PID polling lists for model-specific wired variants.
    connection_polling_rates: dict[tuple[int, int], list[int]] = field(default_factory=dict)

    # Connection status metadata for the GUI. Gen1-only devices are USB.
    connection_type: str = "usb"
    connection_types: dict[tuple[int, int], str] = field(default_factory=dict)

    has_led: bool               = True
    led_effects: list[str]      = field(default_factory=lambda: ['off', 'steady', 'breath'])
    has_breath_speed: bool      = True
    brightness_range: tuple[int, int] = (0, 255)
    breath_speed_range: tuple[int, int] = (0, 100)

    has_angle_snap: bool        = True
    has_ripple_control: bool    = True
    has_motion_sync: bool       = True
    has_debounce: bool          = True
    debounce_range: tuple[int, int] = (0, 20)

    has_stage_colors: bool      = True
    has_reset: bool             = True

    # Labels for GUI display of buttons (optional override)
    button_labels: dict[str, str] = field(default_factory=dict)

    # Relative path under assets/devices/<Brand>/ for the default device illustration.
    image: str | None = None

    # Optional per-VID:PID illustrations.
    connection_images: dict[tuple[int, int], str] = field(default_factory=dict)


class DeviceDriver(ABC):
    """Abstract base for all OpenPulsar mouse drivers.

    Subclasses must define `capabilities` as a class variable and implement
    the required abstract methods.  Optional methods have default
    implementations that raise NotImplementedError — the GUI/CLI check
    `capabilities.has_*` before calling them.
    """

    capabilities: DeviceCapabilities  # must be set as a class variable

    def __init__(self):
        self.current_vid_pid: tuple[int, int] | None = None

    def get_connection_type(self) -> str:
        """Return the current physical connection type. Gen1-only devices use USB."""
        caps = self.capabilities
        if self.current_vid_pid is not None:
            connection_type = caps.connection_types.get(self.current_vid_pid)
            if connection_type:
                return str(connection_type).lower()
        return str(getattr(caps, "connection_type", "usb")).lower()

    def get_device_image(self) -> str | None:
        """Return the best illustration for the currently connected mode."""
        caps = self.capabilities
        if self.current_vid_pid is not None:
            image = caps.connection_images.get(self.current_vid_pid)
            if image:
                return image
        return caps.image

    def get_supported_polling_rates(self) -> list[int]:
        """Return polling rates available for the current connection mode."""
        caps = self.capabilities
        if self.current_vid_pid is not None:
            rates = caps.connection_polling_rates.get(self.current_vid_pid)
            if rates:
                return list(rates)
        return list(caps.polling_rates)

    def get_supported_lod_values(self) -> list[float]:
        """Return LOD distances exposed by this model, in millimeters."""
        return list(self.capabilities.lod_values)

    # ── Connection lifecycle ──────────────────────────────────────────────

    @abstractmethod
    def open(self) -> None:
        """Open the USB device and claim the interface."""

    @abstractmethod
    def close(self) -> None:
        """Release the USB interface and re-attach the kernel driver."""

    # ── Global settings ───────────────────────────────────────────────────

    @abstractmethod
    def get_polling_rate(self) -> int: ...

    @abstractmethod
    def set_polling_rate(self, hz: int) -> None: ...

    def get_debounce(self) -> int:
        raise NotImplementedError

    def set_debounce(self, ms: int) -> None:
        raise NotImplementedError

    def get_angle_snap(self) -> bool:
        raise NotImplementedError

    def set_angle_snap(self, enabled: bool) -> None:
        raise NotImplementedError

    def get_ripple_control(self) -> bool:
        raise NotImplementedError

    def set_ripple_control(self, enabled: bool) -> None:
        raise NotImplementedError

    def get_motion_sync(self) -> bool:
        raise NotImplementedError

    def set_motion_sync(self, enabled: bool) -> None:
        raise NotImplementedError

    # ── Per-profile DPI ───────────────────────────────────────────────────

    @abstractmethod
    def get_dpi_stages(self, profile: int) -> dict:
        """Return {'active': int, 'count': int, 'stages': [(dpi_x, dpi_y), ...]}."""

    @abstractmethod
    def set_dpi_stages(self, stages: list[int], active: int, profile: int) -> None: ...

    @abstractmethod
    def get_active_dpi_stage(self, profile: int) -> int: ...

    @abstractmethod
    def set_active_dpi_stage(self, stage: int, profile: int) -> None: ...

    def get_active_profile(self) -> int:
        """Return the active hardware profile slot, 1-based."""
        raise NotImplementedError

    def set_active_profile(self, profile: int) -> None:
        """Ask the firmware to switch/reload the active profile."""
        raise NotImplementedError

    def refresh_profile(self, profile: int) -> None:
        """Reload a profile after writes that need firmware refresh."""
        self.set_active_profile(profile)

    # ── Per-profile optional settings ─────────────────────────────────────

    def get_lod(self, profile: int) -> float:
        raise NotImplementedError

    def set_lod(self, mm: float, profile: int) -> None:
        raise NotImplementedError

    def get_brightness(self, profile: int) -> int:
        raise NotImplementedError

    def set_brightness(self, value: int, profile: int) -> None:
        raise NotImplementedError

    def get_led_effect(self, profile: int) -> str:
        raise NotImplementedError

    def set_led_effect(self, effect: str, profile: int) -> None:
        raise NotImplementedError

    def get_breath_speed(self, profile: int) -> int:
        raise NotImplementedError

    def set_breath_speed(self, speed: int, profile: int) -> None:
        raise NotImplementedError

    def get_stage_color(self, stage: int, profile: int) -> tuple[int, int, int]:
        raise NotImplementedError

    def set_stage_color(self, stage: int, r: int, g: int, b: int, profile: int) -> None:
        raise NotImplementedError

    def get_button(self, btn_id: int, profile: int) -> tuple[int, int, int]:
        """Return (type, action1, action2) raw bytes."""
        raise NotImplementedError

    def set_button(self, btn_id: int, btn_type: int, a1: int, a2: int,
                   profile: int) -> None:
        raise NotImplementedError

    def reset_to_defaults(self, profile: int) -> None:
        raise NotImplementedError

    # ── Hidraw (for tray / DPI notifications) ─────────────────────────────

    def find_hidraw(self) -> Optional[str]:
        """Return /dev/hidrawN path for DPI event listening, or None."""
        return None

    def parse_hidraw_event(self, data: bytes) -> Optional[dict]:
        """Parse a hidraw event. Return {'dpi': int, 'stage': int} or None."""
        return None

"""
Pulsar Sonix Gen1 protocol driver.

USB protocol reverse-engineered from Wireshark captures of Pulsar Fusion on Windows.
Interface 3, Feature report (wValue=0x0300), 64-byte packets.

Packet format:
  [0]     direction: 0x00=CMD (host→device), 0x01=RSP (device→host)
  [1]     command category
  [2]     register (bit7=0: write, bit7=1: read)
  [3]     sub-register
  [4-5]   always 0x00
  [6]     profile: 0x00=global, 0x01-0x05=profile 1-5
  [7-61]  payload
  [62-63] checksum: little-endian uint16 of sum(bytes[0:62])

Global settings (profile=0): polling rate, debounce, angle snap, ripple, motion sync
Per-profile settings (profile=1-5): DPI stages, LOD, brightness, LED effect, button bindings
"""

# Portions copyright (c) 2026 Packerlschupfer, used under the MIT License.
# See THIRD-PARTY-NOTICES.md for attribution and complete license terms.

import struct
import glob
import os
from typing import Optional

import usb.core
import usb.util

from openpulsar.core.device import DeviceDriver
from openpulsar.hid import BTN_TYPE_MOUSE, BTN_TYPE_DPI
from openpulsar.logging_utils import get_logger

logger = get_logger(__name__)

# ── Encoding tables ──────────────────────────────────────────────────────────

# Sonix Gen1 encoding used by first supported models.
POLL_HZ_TO_VAL = {125: 1, 250: 2, 500: 4, 1000: 8}
POLL_VAL_TO_HZ = {v: k for k, v in POLL_HZ_TO_VAL.items()}

LOD_MM_TO_VAL  = {1: 0, 2: 1}
LOD_VAL_TO_MM  = {v: k for k, v in LOD_MM_TO_VAL.items()}

# Sonix V2 encoding observed on X3-class devices.
# Write values are bit masks; read values are timer/divider-like values.
POLL_V2_HZ_TO_WRITE_VAL = {
    125: 0x40,
    250: 0x20,
    500: 0x10,
    1000: 0x08,
    2000: 0x04,
    4000: 0x02,
    8000: 0x01,
}
POLL_V2_WRITE_VAL_TO_HZ = {v: k for k, v in POLL_V2_HZ_TO_WRITE_VAL.items()}
POLL_V2_READ_VAL_TO_HZ = {
    240: 125,
    120: 250,
    60: 500,
    30: 1000,
    15: 2000,
    8: 4000,
    4: 8000,
}

# Sonix V2 LOD uses tenths of a millimeter: 0x07=0.7mm, 0x0a=1.0mm, 0x14=2.0mm.
LOD_V2_MM_TO_VAL = {0.7: 0x07, 1.0: 0x0A, 2.0: 0x14}
LOD_V2_VAL_TO_MM = {v: k for k, v in LOD_V2_MM_TO_VAL.items()}

LED_NAME_TO_VAL = {'off': 0, 'steady': 1, 'breath': 2}
LED_VAL_TO_NAME = {v: k for k, v in LED_NAME_TO_VAL.items()}

# Factory default button bindings (from Pulsar Fusion reset capture)
BUTTON_DEFAULTS = {
    0x01: (BTN_TYPE_MOUSE, 0x01, 0x00),  # left   → left click
    0x02: (BTN_TYPE_MOUSE, 0x02, 0x00),  # right  → right click
    0x03: (BTN_TYPE_MOUSE, 0x03, 0x00),  # wheel  → wheel click
    0x04: (BTN_TYPE_MOUSE, 0x04, 0x00),  # thumb1 → forward
    0x05: (BTN_TYPE_MOUSE, 0x05, 0x00),  # thumb2 → backward
    0x06: (BTN_TYPE_MOUSE, 0x04, 0x00),  # thumb3 → forward
    0x07: (BTN_TYPE_MOUSE, 0x05, 0x00),  # thumb4 → backward
    0x0b: (BTN_TYPE_DPI,   0x03, 0x00),  # dpi    → dpiloop
}


class SonixGen1Protocol(DeviceDriver):
    """Generic driver for Pulsar mice using the Sonix Gen1 HID protocol.

    Concrete mouse models must subclass this class and provide their own
    ``DeviceCapabilities`` declaration.  The protocol implementation stays
    model-agnostic here; model differences live in ``openpulsar.devices``.
    """

    _WVALUE = 0x0300  # HID Feature report, report ID 0

    def __init__(self):
        super().__init__()
        self._dev = None
        self._iface = None
        self._interface_probe_log = []
        self._diagnostic_log = []
        self._diagnostic_suppressed = False
        self._interface_selection_mode = "not selected"
        self._interface_candidates_snapshot = []

    # ── Diagnostics / interface discovery ───────────────────────────────

    def _diag(self, message: str) -> None:
        if getattr(self, "_diagnostic_suppressed", False):
            return
        logger.debug("%s", message)
        try:
            self._diagnostic_log.append(str(message))
            # Keep reports readable and bounded even after long GUI sessions.
            if len(self._diagnostic_log) > 300:
                del self._diagnostic_log[:-300]
        except (usb.core.USBError, OSError, RuntimeError) as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)

    def get_diagnostic_log(self) -> list[str]:
        return list(getattr(self, "_diagnostic_log", []))

    def set_diagnostic_suppressed(self, suppressed: bool) -> None:
        """Temporarily silence TX/RX diagnostic logging.

        The GUI refresh manager polls tiny self-changing state every 300 ms.
        Without suppression, those routine reads would flood the exported
        diagnostic report and hide the useful command/response history.
        """
        self._diagnostic_suppressed = bool(suppressed)


    def get_interface_probe_log(self) -> list[str]:
        return list(getattr(self, "_interface_probe_log", []))

    def get_selected_interface(self) -> int | None:
        return self._iface if self._iface is not None else self.capabilities.interface_num

    def get_interface_selection_mode(self) -> str:
        return getattr(self, "_interface_selection_mode", "unknown")

    def get_interface_candidates(self) -> list[int]:
        return list(getattr(self, "_interface_candidates_snapshot", []))

    def _describe_usb_interfaces(self, dev) -> list[str]:
        lines = []
        try:
            cfg = dev.get_active_configuration()
            selected = self._iface
            for interface in cfg:
                number = int(interface.bInterfaceNumber)
                cls = int(interface.bInterfaceClass)
                subclass = int(interface.bInterfaceSubClass)
                proto = int(interface.bInterfaceProtocol)
                kind = "HID" if cls == 0x03 else f"class 0x{cls:02x}"
                marker = " <- selected" if selected == number else ""
                lines.append(
                    f"Interface {number}: {kind} "
                    f"(subclass=0x{subclass:02x}, protocol=0x{proto:02x}){marker}"
                )
        except (usb.core.USBError, OSError, AttributeError, TypeError, ValueError) as exc:
            lines.append(f"Unable to enumerate USB interfaces: {exc}")
        return lines

    def get_usb_interface_descriptions(self) -> list[str]:
        dev = getattr(self, "_dev", None)
        if dev is None:
            return ["USB device is not open"]
        return self._describe_usb_interfaces(dev)

    def _interface_candidates(self, dev) -> list[int]:
        candidates = []

        def add(value):
            try:
                value = int(value)
            except (TypeError, ValueError):
                logger.debug("Ignoring invalid interface candidate %r", value, exc_info=True)
                return
            if value not in candidates:
                candidates.append(value)

        add(getattr(self.capabilities, "interface_num", 0))

        try:
            cfg = dev.get_active_configuration()
            for interface in cfg:
                add(interface.bInterfaceNumber)
        except (usb.core.USBError, OSError, RuntimeError) as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)

        # Safe fallback for common Pulsar / Sonix layouts.
        for iface in range(0, 5):
            add(iface)

        return candidates

    def _release_candidate_interface(self, dev, iface: int, detached: bool) -> None:
        try:
            usb.util.release_interface(dev, iface)
        except (usb.core.USBError, OSError, RuntimeError) as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)
        if detached:
            try:
                dev.attach_kernel_driver(iface)
            except (usb.core.USBError, OSError, RuntimeError) as exc:
                logger.debug("Ignored best-effort operation failure", exc_info=True)

    def _probe_interface(self) -> bool:
        """Return True if the currently selected interface speaks Gen1."""
        try:
            rsp = self._read(0x01, 0x09, 0x02, 0)
            return len(rsp) >= 8
        except (usb.core.USBError, OSError, IOError, RuntimeError) as exc:
            self._diag(f"[Gen1] Probe failed on interface {self._iface}: {exc}")
            return False

    # ── Device information ────────────────────────────────────────────────

    def get_model_name(self) -> str:
        return self.capabilities.name

    def get_firmware_version(self) -> str:
        """Return the USB device/firmware version exposed by bcdDevice.

        Pulsar publishes the Xlite Wired firmware as V1.0, which matches
        the USB bcdDevice value seen in captures (0x1000 -> V1.0).
        If a future Sonix firmware command is identified, it can replace this.
        """
        if self._dev is None:
            return "unknown"

        try:
            bcd = int(self._dev.bcdDevice)
        except (TypeError, ValueError, AttributeError):
            logger.debug("Unable to parse USB bcdDevice firmware value", exc_info=True)
            return "unknown"

        major = (bcd >> 12) & 0xF
        minor = (bcd >> 8) & 0xF
        patch = (bcd >> 4) & 0xF
        build = bcd & 0xF

        # 0x1000 -> V1.0, 0x1001 -> V1.0.1, 0x1010 -> V1.1
        if patch or build:
            return f"V{major}.{minor}.{patch}{build}"
        return f"V{major}.{minor}"

    def is_connected(self) -> bool:
        """Return True when any declared VID:PID for this model is present."""
        for vid, pid in self.capabilities.vid_pid_pairs:
            if usb.core.find(idVendor=vid, idProduct=pid) is not None:
                self.current_vid_pid = (vid, pid)
                return True
        return False

    def reconnect(self) -> None:
        """Drop a stale PyUSB handle and open the currently plugged device."""
        try:
            self.close()
        except (usb.core.USBError, OSError, RuntimeError):
            logger.debug("Ignoring close failure during reconnect", exc_info=True)
            self._dev = None
        self.open()

    # ── Connection lifecycle ──────────────────────────────────────────────

    def open(self) -> None:
        caps = self.capabilities
        dev = None
        found_vid_pid = None
        for vid, pid in caps.vid_pid_pairs:
            dev = usb.core.find(idVendor=vid, idProduct=pid)
            if dev is not None:
                found_vid_pid = (vid, pid)
                break

        if dev is None or found_vid_pid is None:
            ids = ", ".join(
                f"VID=0x{vid:04x}, PID=0x{pid:04x}"
                for vid, pid in caps.vid_pid_pairs
            )
            raise RuntimeError(f"{caps.name} not found ({ids}). Is the mouse plugged in?")

        self._dev = dev
        self.current_vid_pid = found_vid_pid
        self._interface_probe_log = []
        self._interface_selection_mode = "automatic"
        self._diag(f"[{self.__class__.__name__}] Opening VID=0x{found_vid_pid[0]:04x} PID=0x{found_vid_pid[1]:04x}")

        declared_iface = getattr(caps, "interface_num", None)
        candidates = self._interface_candidates(dev)
        self._interface_candidates_snapshot = list(candidates)
        self._interface_probe_log.extend([
            "Searching HID interface...",
            f"Selection mode: automatic",
            f"Declared interface: {declared_iface}",
            f"Candidate order: {', '.join(str(i) for i in candidates)}",
        ])
        self._interface_probe_log.extend(self._describe_usb_interfaces(dev))

        last_error = None
        for iface in candidates:
            detached = False
            self._interface_probe_log.append(f"Testing interface {iface}")
            self._diag(f"[{self.__class__.__name__}] Testing interface {iface}")

            try:
                try:
                    if dev.is_kernel_driver_active(iface):
                        dev.detach_kernel_driver(iface)
                        detached = True
                except (NotImplementedError, usb.core.USBError) as exc:
                    self._diag(f"[{self.__class__.__name__}] Kernel-driver check/detach skipped on interface {iface}: {exc}")

                usb.util.claim_interface(dev, iface)
                self._iface = iface

                if self._probe_interface():
                    if declared_iface is not None and iface == declared_iface:
                        self._interface_selection_mode = "automatic (declared interface succeeded)"
                    else:
                        self._interface_selection_mode = "automatic fallback"
                    self._interface_probe_log.append(f"Interface {iface}: OK ✔")
                    self._interface_probe_log.append(f"Selected interface: {iface}")
                    self._interface_probe_log.append(f"Final selection mode: {self._interface_selection_mode}")
                    self._diag(f"[{self.__class__.__name__}] Selected interface {iface}")
                    return

                self._interface_probe_log.append(f"Interface {iface}: no valid response")
                self._release_candidate_interface(dev, iface, detached)

            except (usb.core.USBError, OSError, IOError, RuntimeError) as exc:
                last_error = exc
                self._interface_probe_log.append(f"Interface {iface}: {type(exc).__name__}: {exc}")
                self._diag(f"[{self.__class__.__name__}] Interface {iface} failed: {type(exc).__name__}: {exc}")
                self._release_candidate_interface(dev, iface, detached)
                continue

        # Safe fallback: auto-detection must never make a previously usable
        # model unusable.  If no probe validates an interface, keep the device
        # open on the declared interface so the UI can start in degraded mode
        # and the user can export a diagnostic report.
        fallback_iface = declared_iface
        if fallback_iface is None:
            fallback_iface = candidates[0] if candidates else 0

        self._iface = int(fallback_iface)
        self._interface_selection_mode = "automatic failed, using declared interface"
        self._interface_probe_log.append("No interface passed protocol validation.")
        if last_error is not None:
            self._interface_probe_log.append(f"Last auto-detect error: {type(last_error).__name__}: {last_error}")
        self._interface_probe_log.append(f"Fallback selected interface: {self._iface}")

        detached = False
        try:
            try:
                if dev.is_kernel_driver_active(self._iface):
                    dev.detach_kernel_driver(self._iface)
                    detached = True
            except (NotImplementedError, usb.core.USBError) as exc:
                self._diag(f"[{self.__class__.__name__}] Fallback kernel-driver check/detach skipped on interface {self._iface}: {exc}")
            usb.util.claim_interface(dev, self._iface)
            self._interface_probe_log.append(f"Fallback interface {self._iface}: claimed ✔")
            self._diag(f"[{self.__class__.__name__}] Fallback selected interface {self._iface}")
        except (usb.core.USBError, OSError, RuntimeError) as exc:
            # Keep going anyway: many diagnostic fields (model, VID/PID, USB
            # descriptors, bcdDevice firmware fallback) do not require a
            # successful protocol probe.  Later reads will fail gracefully in
            # the existing best-effort profile loading path.
            self._interface_probe_log.append(f"Fallback interface {self._iface}: claim failed: {type(exc).__name__}: {exc}")
            self._diag(f"[{self.__class__.__name__}] Fallback interface {self._iface} claim failed: {type(exc).__name__}: {exc}")
        self._interface_probe_log.append(f"Selected interface: {self._iface}")
        self._interface_probe_log.append(f"Final selection mode: {self._interface_selection_mode}")
        return

    def close(self) -> None:
        if self._dev is None:
            return
        iface = self.get_selected_interface()
        if iface is not None:
            try:
                usb.util.release_interface(self._dev, iface)
            except (usb.core.USBError, OSError, RuntimeError) as exc:
                logger.debug("Ignored best-effort operation failure", exc_info=True)
            try:
                self._dev.attach_kernel_driver(iface)
            except (usb.core.USBError, OSError, RuntimeError) as exc:
                logger.debug("Ignored best-effort operation failure", exc_info=True)
        self._dev = None
        self._iface = None

    # ── Low-level protocol helpers ────────────────────────────────────────

    def _checksum(self, data: bytes) -> bytes:
        return struct.pack('<H', sum(data[:62]) & 0xFFFF)

    def _build(self, cat, reg, sub, profile, payload=()):
        buf = bytearray(64)
        buf[0] = 0x00       # direction: CMD
        buf[1] = cat
        buf[2] = reg
        buf[3] = sub
        buf[6] = profile
        for i, b in enumerate(payload):
            buf[7 + i] = b
        cs = self._checksum(buf)
        buf[62] = cs[0]
        buf[63] = cs[1]
        return bytes(buf)

    def _build_read(self, cat, reg, sub, profile, payload=()):
        return self._build(cat, reg | 0x80, sub, profile, payload)

    def _set_report(self, data):
        iface = self.get_selected_interface()
        self._diag(f"[TX iface={iface}] {bytes(data).hex(' ')}")
        self._dev.ctrl_transfer(0x21, 0x09, self._WVALUE, iface, data, timeout=1000)

    def _get_report(self) -> bytes:
        iface = self.get_selected_interface()
        rsp = bytes(self._dev.ctrl_transfer(
            0xA1, 0x01, self._WVALUE, iface, self.capabilities.report_size, timeout=1000))
        self._diag(f"[RX iface={iface}] {rsp.hex(' ')}")
        return rsp

    def _cmd(self, cat, reg, sub, profile, payload=()):
        self._set_report(self._build(cat, reg, sub, profile, payload))
        rsp = self._get_report()
        if rsp[0] not in (0x01, 0x02):
            raise IOError(f"Unexpected response byte: 0x{rsp[0]:02x}")
        return rsp

    def _read(self, cat, reg, sub, profile, payload=()):
        self._set_report(self._build_read(cat, reg, sub, profile, payload))
        rsp = self._get_report()
        if rsp[0] != 0x01:
            raise IOError(f"Bad response direction byte: 0x{rsp[0]:02x}")
        return rsp

    # ── Global settings ───────────────────────────────────────────────────

    def get_polling_rate(self, profile: int = 0) -> int:
        rsp = self._read(0x01, 0x09, 0x02, profile)
        return POLL_VAL_TO_HZ.get(rsp[7], rsp[7] * 125)

    def set_polling_rate(self, hz: int, profile: int = 0) -> None:
        val = POLL_HZ_TO_VAL.get(hz)
        if val is None:
            raise ValueError(f"Polling rate must be one of {sorted(POLL_HZ_TO_VAL)}")
        self._cmd(0x01, 0x09, 0x02, profile, [val])

    def get_debounce(self, profile: int = 0) -> int:
        rsp = self._read(0x04, 0x03, 0x03, profile)
        return rsp[7]

    def set_debounce(self, ms: int, profile: int = 0) -> None:
        lo, hi = self.capabilities.debounce_range
        if not lo <= ms <= hi:
            raise ValueError(f"Debounce must be {lo}–{hi} ms")
        self._cmd(0x04, 0x03, 0x03, profile, [ms])

    def get_angle_snap(self, profile: int = 0) -> bool:
        rsp = self._read(0x07, 0x04, 0x02, profile)
        return bool(rsp[7])

    def set_angle_snap(self, enabled: bool, profile: int = 0) -> None:
        self._cmd(0x07, 0x04, 0x02, profile, [1 if enabled else 0])

    def get_ripple_control(self, profile: int = 0) -> bool:
        rsp = self._read(0x07, 0x03, 0x02, profile)
        return bool(rsp[7])

    def set_ripple_control(self, enabled: bool, profile: int = 0) -> None:
        self._cmd(0x07, 0x03, 0x02, profile, [1 if enabled else 0])

    def get_motion_sync(self, profile: int = 0) -> bool:
        rsp = self._read(0x07, 0x05, 0x02, profile)
        return bool(rsp[7])

    def set_motion_sync(self, enabled: bool, profile: int = 0) -> None:
        self._cmd(0x07, 0x05, 0x02, profile, [1 if enabled else 0])

    # ── Per-profile: LOD ──────────────────────────────────────────────────

    def get_lod(self, profile: int) -> float:
        rsp = self._read(0x07, 0x02, 0x03, profile)
        return LOD_VAL_TO_MM.get(rsp[7], rsp[7])

    def set_lod(self, mm: float, profile: int) -> None:
        normalized = float(mm)
        supported = {float(value) for value in self.get_supported_lod_values()}
        if supported and normalized not in supported:
            allowed = ", ".join(f"{value:g}" for value in sorted(supported))
            raise ValueError(f"LOD must be one of {allowed} mm")

        # Sonix Gen1 stores 1/2 mm as compact enum values.
        normalized_int = int(normalized)
        val = LOD_MM_TO_VAL.get(normalized_int)
        if val is None:
            allowed = ", ".join(f"{value:g}" for value in sorted(LOD_MM_TO_VAL))
            raise ValueError(f"LOD must be one of {allowed} mm")
        self._cmd(0x07, 0x02, 0x03, profile, [val, val])

    # ── Per-profile: LED ──────────────────────────────────────────────────

    def get_brightness(self, profile: int) -> int:
        rsp = self._read(0x03, 0x03, 0x03, profile, [0x01])
        return rsp[8]

    def set_brightness(self, value: int, profile: int) -> None:
        lo, hi = self.capabilities.brightness_range
        if not lo <= value <= hi:
            raise ValueError(f"Brightness must be {lo}–{hi}")
        self._cmd(0x03, 0x03, 0x03, profile, [0x01, value])

    def get_led_effect(self, profile: int) -> str:
        rsp = self._read(0x03, 0x04, 0x0F, profile, [0x01])
        return LED_VAL_TO_NAME.get(rsp[8], f"unknown(0x{rsp[8]:02x})")

    def set_led_effect(self, effect: str, profile: int) -> None:
        val = LED_NAME_TO_VAL.get(effect)
        if val is None:
            raise ValueError(f"Effect must be one of {list(LED_NAME_TO_VAL)}")
        self._cmd(0x03, 0x04, 0x0F, profile, [0x01, val])

    def get_breath_speed(self, profile: int) -> int:
        rsp = self._read(0x03, 0x04, 0x0F, profile, [0x01])
        return rsp[11]

    def set_breath_speed(self, speed: int, profile: int) -> None:
        lo, hi = self.capabilities.breath_speed_range
        if not lo <= speed <= hi:
            raise ValueError(f"Breath speed must be {lo}–{hi}")
        self._cmd(0x03, 0x04, 0x0F, profile, [0x01, 0x02, 0x00, 0x00, speed])

    # ── Per-profile: DPI stages ───────────────────────────────────────────

    def get_dpi_stages(self, profile: int) -> dict:
        rsp = self._read(0x05, 0x04, 0x15, profile)
        active     = rsp[7]
        num_stages = rsp[8]
        stages = []
        for i in range(num_stages):
            base = 9 + i * 5
            dpi_x = struct.unpack_from('<H', rsp, base + 1)[0]
            dpi_y = struct.unpack_from('<H', rsp, base + 3)[0]
            stages.append((dpi_x, dpi_y))
        return {'active': active, 'count': num_stages, 'stages': stages}

    def set_dpi_stages(self, stages: list[int], active: int, profile: int) -> None:
        caps = self.capabilities
        if not 1 <= len(stages) <= caps.max_dpi_stages:
            raise ValueError(f"Must have 1–{caps.max_dpi_stages} DPI stages")
        if not 1 <= active <= len(stages):
            raise ValueError(f"Active stage must be 1–{len(stages)}")
        for dpi in stages:
            if not caps.dpi_min <= dpi <= caps.dpi_max:
                raise ValueError(
                    f"DPI value {dpi} out of range {caps.dpi_min}–{caps.dpi_max}")
        payload = [active, len(stages)]
        for i, dpi in enumerate(stages):
            lo = dpi & 0xFF
            hi = (dpi >> 8) & 0xFF
            payload += [i + 1, lo, hi, lo, hi]
        self._cmd(0x05, 0x04, 0x21, profile, payload)

    def get_active_dpi_stage(self, profile: int) -> int:
        rsp = self._read(0x05, 0x01, 0x02, profile)
        return rsp[7]

    def set_active_dpi_stage(self, stage: int, profile: int) -> None:
        if not 1 <= stage <= self.capabilities.max_dpi_stages:
            raise ValueError(f"DPI stage must be 1–{self.capabilities.max_dpi_stages}")
        self._cmd(0x05, 0x01, 0x02, profile, [stage])

    # ── Per-profile: active profile / refresh ─────────────────────────────

    def get_active_profile(self) -> int:
        """Read the active hardware profile slot, 1-based.

        This is the read counterpart of the profile switch/reload command
        observed in Pulsar Fusion captures.  Firmware variants may echo the
        selected slot either in the command profile byte or in the first payload
        byte, so validate both positions and return the first plausible slot.
        """
        rsp = self._read(0x02, 0x06, 0x01, 0)
        max_profiles = self.capabilities.num_profiles

        for candidate in (rsp[7], rsp[6]):
            try:
                slot = int(candidate)
            except (TypeError, ValueError):
                continue
            if 1 <= slot <= max_profiles:
                return slot

        raise IOError(
            "Unable to decode active profile from response: "
            f"profile_byte={rsp[6]!r}, payload0={rsp[7]!r}"
        )

    def set_active_profile(self, profile: int) -> None:
        """Experimental: ask the firmware to switch/reload the active profile.

        This mirrors the command shape found in Pulsar Fusion captures:
            00 02 06 01 00 00 <profile> ...
        If confirmed, it can be used both for real profile switching and for
        forcing a profile refresh after RGB/DPI writes.
        """
        if not 1 <= profile <= self.capabilities.num_profiles:
            raise ValueError(
                f"Profile must be 1–{self.capabilities.num_profiles}"
            )


        self._cmd(
            0x02,
            0x06,
            0x01,
            profile,
        )

    def refresh_profile(self, profile: int) -> None:
        """Experimental helper to reload the current profile in firmware."""
        self.set_active_profile(profile)

    # ── Per-profile: DPI stage colors ─────────────────────────────────────

    def get_stage_color(self, stage: int, profile: int) -> tuple[int, int, int]:
        rsp = self._read(0x05, 0x05, 0x05, profile, [stage])

        return (rsp[8], rsp[9], rsp[10])

    def set_stage_color(self, stage: int, r: int, g: int, b: int,
                        profile: int) -> None:
        for val, name in [(r, 'R'), (g, 'G'), (b, 'B')]:
            if not 0 <= val <= 255:
                raise ValueError(f"{name} must be 0–255")
        if not 1 <= stage <= self.capabilities.max_dpi_stages:
            raise ValueError(f"Stage must be 1–{self.capabilities.max_dpi_stages}")

        self._cmd(0x05, 0x05, 0x05, profile, [stage, r, g, b])

    # ── Per-profile: Button bindings ──────────────────────────────────────

    def get_button(self, btn_id: int, profile: int) -> tuple[int, int, int]:
        rsp = self._read(0x04, 0x01, 0x06, profile, [btn_id, 0xff])
        return (rsp[8], rsp[9], rsp[10])

    def set_button(self, btn_id: int, btn_type: int, a1: int, a2: int,
                   profile: int) -> None:
        self._cmd(0x04, 0x01, 0x06, profile, [btn_id, btn_type, a1, a2])

    # ── Factory reset ─────────────────────────────────────────────────────

    def reset_to_defaults(self, profile: int) -> None:
        self._cmd(0x02, 0x05, 0x01, profile)
        pkt = self._build(0x02, 0x06, 0x01, profile)
        self._set_report(pkt)
        try:
            self._get_report()
        except (usb.core.USBError, OSError, RuntimeError) as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)  # device may have already reset

    # ── Hidraw support ────────────────────────────────────────────────────

    def find_hidraw(self) -> Optional[str]:
        ids = {
            (f'{vid:04x}', f'{pid:04x}')
            for vid, pid in self.capabilities.vid_pid_pairs
        }
        for path in sorted(glob.glob('/sys/class/hidraw/hidraw*/device/uevent')):
            try:
                text = open(path).read().lower()
                if not any(vid in text and pid in text for vid, pid in ids):
                    continue
                phys_line = [l for l in text.splitlines() if 'hid_phys' in l]
                if phys_line and phys_line[0].endswith('/input1'):
                    return '/dev/' + path.split('/')[4]
            except OSError:
                continue
        return None

    def parse_hidraw_event(self, data: bytes) -> Optional[dict]:
        if len(data) >= 3 and data[0] == 0x05 and data[1] == 0x01:
            return {
                "type": "profile",
                "profile": data[2],
            }

        if len(data) >= 7 and data[0] == 0x05 and data[1] == 0x05:
            dpi = struct.unpack_from("<H", data, 3)[0]
            stage = data[2] + 1

            return {
                "type": "dpi",
                "dpi": dpi,
                "stage": stage,
            }

        return None


# Backward-compatible alias for older imports.
SonixWiredProtocol = SonixGen1Protocol

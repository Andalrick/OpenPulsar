"""Global keyboard shortcut support for OpenPulsar.

This backend intentionally uses the Linux evdev interface directly so it can
keep working when the OpenPulsar window is hidden in the tray. On Wayland,
normal Qt key events are local to the focused window, so they are not enough
for persistent keyboard commands.

If the current user is not allowed to read /dev/input/event* devices, the
backend simply stays inactive and OpenPulsar keeps its local in-window
shortcut handling.
"""

from __future__ import annotations

import glob
import os
import select
import struct
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from PySide6.QtCore import QObject, QThread, Qt, Signal


EV_KEY = 0x01
KEY_RELEASE = 0
KEY_PRESS = 1
KEY_REPEAT = 2

# struct input_event on 64-bit Linux:
# struct timeval { long tv_sec; long tv_usec; } + unsigned short type/code + int value
_INPUT_EVENT_FORMAT = "llHHI"
_INPUT_EVENT_SIZE = struct.calcsize(_INPUT_EVENT_FORMAT)


MODIFIER_CODES = {
    29: Qt.ControlModifier,   # KEY_LEFTCTRL
    97: Qt.ControlModifier,   # KEY_RIGHTCTRL
    42: Qt.ShiftModifier,     # KEY_LEFTSHIFT
    54: Qt.ShiftModifier,     # KEY_RIGHTSHIFT
    56: Qt.AltModifier,       # KEY_LEFTALT
    100: Qt.AltModifier,      # KEY_RIGHTALT / AltGr, exposed as Alt for shortcut matching
    125: Qt.MetaModifier,     # KEY_LEFTMETA
    126: Qt.MetaModifier,     # KEY_RIGHTMETA
}


KEY_CODE_TO_QT = {
    1: Qt.Key_Escape,
    2: Qt.Key_1,
    3: Qt.Key_2,
    4: Qt.Key_3,
    5: Qt.Key_4,
    6: Qt.Key_5,
    7: Qt.Key_6,
    8: Qt.Key_7,
    9: Qt.Key_8,
    10: Qt.Key_9,
    11: Qt.Key_0,
    12: Qt.Key_Minus,
    13: Qt.Key_Equal,
    14: Qt.Key_Backspace,
    15: Qt.Key_Tab,
    16: Qt.Key_Q,
    17: Qt.Key_W,
    18: Qt.Key_E,
    19: Qt.Key_R,
    20: Qt.Key_T,
    21: Qt.Key_Y,
    22: Qt.Key_U,
    23: Qt.Key_I,
    24: Qt.Key_O,
    25: Qt.Key_P,
    26: Qt.Key_BracketLeft,
    27: Qt.Key_BracketRight,
    28: Qt.Key_Return,
    30: Qt.Key_A,
    31: Qt.Key_S,
    32: Qt.Key_D,
    33: Qt.Key_F,
    34: Qt.Key_G,
    35: Qt.Key_H,
    36: Qt.Key_J,
    37: Qt.Key_K,
    38: Qt.Key_L,
    39: Qt.Key_Semicolon,
    40: Qt.Key_Apostrophe,
    41: Qt.Key_QuoteLeft,
    43: Qt.Key_Backslash,
    44: Qt.Key_Z,
    45: Qt.Key_X,
    46: Qt.Key_C,
    47: Qt.Key_V,
    48: Qt.Key_B,
    49: Qt.Key_N,
    50: Qt.Key_M,
    51: Qt.Key_Comma,
    52: Qt.Key_Period,
    53: Qt.Key_Slash,
    57: Qt.Key_Space,
    58: Qt.Key_CapsLock,
    59: Qt.Key_F1,
    60: Qt.Key_F2,
    61: Qt.Key_F3,
    62: Qt.Key_F4,
    63: Qt.Key_F5,
    64: Qt.Key_F6,
    65: Qt.Key_F7,
    66: Qt.Key_F8,
    67: Qt.Key_F9,
    68: Qt.Key_F10,
    87: Qt.Key_F11,
    88: Qt.Key_F12,
    102: Qt.Key_Home,
    103: Qt.Key_Up,
    104: Qt.Key_PageUp,
    105: Qt.Key_Left,
    106: Qt.Key_Right,
    107: Qt.Key_End,
    108: Qt.Key_Down,
    109: Qt.Key_PageDown,
    110: Qt.Key_Insert,
    111: Qt.Key_Delete,
}


def _keyboard_event_paths() -> List[str]:
    """Return likely keyboard event devices, with a conservative fallback."""
    paths: List[str] = []

    for pattern in (
        "/dev/input/by-id/*-event-kbd",
        "/dev/input/by-path/*-event-kbd",
    ):
        for path in glob.glob(pattern):
            try:
                resolved = str(Path(path).resolve())
            except OSError:
                continue
            if resolved not in paths:
                paths.append(resolved)

    # Some keyboards do not expose a convenient by-id/by-path kbd symlink.
    # The fallback is harmless: non-keyboard devices are opened read-only and
    # ignored unless they emit mapped EV_KEY keyboard codes.
    if not paths:
        for path in sorted(glob.glob("/dev/input/event*")):
            if path not in paths:
                paths.append(path)

    return paths


def _modifier_mask(pressed_codes: Set[int]) -> int:
    mask = Qt.NoModifier
    for code in pressed_codes:
        modifier = MODIFIER_CODES.get(code)
        if modifier is not None:
            mask |= modifier

    return int(mask.value) if hasattr(mask, "value") else int(mask)


class EvdevShortcutListener(QThread):
    shortcutPressed = Signal(int, int)
    availabilityChanged = Signal(bool, str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._running = False
        self._fds: List[int] = []
        self._pressed_codes: Set[int] = set()
        self._active = False
        self._status_message = ""

    def is_active(self) -> bool:
        return self._active

    def status_message(self) -> str:
        return self._status_message

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        self._fds = []
        self._pressed_codes.clear()

        denied = 0
        for path in _keyboard_event_paths():
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            except PermissionError:
                denied += 1
                continue
            except OSError:
                continue
            self._fds.append(fd)

        if not self._fds:
            self._active = False
            if denied:
                self._status_message = (
                    "Global keyboard shortcuts unavailable: permission denied "
                    "on /dev/input event devices."
                )
            else:
                self._status_message = "Global keyboard shortcuts unavailable: no keyboard event device found."
            self.availabilityChanged.emit(False, self._status_message)
            return

        self._active = True
        self._status_message = "Global keyboard shortcuts active."
        self.availabilityChanged.emit(True, self._status_message)

        try:
            while self._running:
                try:
                    readable, _, _ = select.select(self._fds, [], [], 0.15)
                except (OSError, ValueError):
                    break

                for fd in readable:
                    self._read_events(fd)
        finally:
            for fd in self._fds:
                try:
                    os.close(fd)
                except OSError:
                    pass
            self._fds = []
            self._pressed_codes.clear()
            self._active = False
            self.availabilityChanged.emit(False, "Global keyboard shortcuts stopped.")

    def _read_events(self, fd: int):
        while self._running:
            try:
                chunk = os.read(fd, _INPUT_EVENT_SIZE * 16)
            except BlockingIOError:
                return
            except OSError:
                return

            if not chunk:
                return

            usable = len(chunk) - (len(chunk) % _INPUT_EVENT_SIZE)
            for offset in range(0, usable, _INPUT_EVENT_SIZE):
                _sec, _usec, event_type, code, value = struct.unpack(
                    _INPUT_EVENT_FORMAT,
                    chunk[offset:offset + _INPUT_EVENT_SIZE],
                )

                if event_type != EV_KEY:
                    continue

                if value == KEY_PRESS:
                    self._pressed_codes.add(code)
                    self._handle_key_press(code)
                elif value == KEY_RELEASE:
                    self._pressed_codes.discard(code)
                elif value == KEY_REPEAT:
                    # Keyboard commands should behave as one-shot actions.
                    continue

    def _handle_key_press(self, code: int):
        if code in MODIFIER_CODES:
            return

        qt_key = KEY_CODE_TO_QT.get(code)
        if qt_key is None:
            return

        self.shortcutPressed.emit(int(qt_key), _modifier_mask(self._pressed_codes))


class GlobalShortcutManager(QObject):
    shortcutPressed = Signal(int, int)
    availabilityChanged = Signal(bool, str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._listener: Optional[EvdevShortcutListener] = None
        self._active = False

    def is_active(self) -> bool:
        return self._active

    def start(self) -> bool:
        if self._listener is not None:
            return self._active

        listener = EvdevShortcutListener()
        listener.shortcutPressed.connect(self.shortcutPressed)
        listener.availabilityChanged.connect(self._on_availability_changed)
        listener.start()
        self._listener = listener
        return self._active

    def stop(self):
        listener = self._listener
        if listener is None:
            return

        listener.stop()
        listener.wait(1500)
        self._listener = None
        self._active = False

    def _on_availability_changed(self, active: bool, message: str):
        self._active = bool(active)
        self.availabilityChanged.emit(active, message)

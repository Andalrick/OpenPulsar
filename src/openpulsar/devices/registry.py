"""Supported OpenPulsar devices.

This registry is the canonical list used by OpenPulsar to detect validated
and officially supported mice.
"""

from __future__ import annotations

from typing import Type

import usb.core

from openpulsar.core.device import DeviceDriver
from openpulsar.devices.pulsar import (
    PulsarX2AWired,
    PulsarX2Wired,
    PulsarX2HWired,
    PulsarXliteWired,
)


SUPPORTED_DEVICES: list[Type[DeviceDriver]] = [
    PulsarXliteWired,
    PulsarX2AWired,
    PulsarX2Wired,
    PulsarX2HWired,
]


def iter_supported_devices() -> list[Type[DeviceDriver]]:
    return SUPPORTED_DEVICES.copy()


def find_supported_device() -> DeviceDriver | None:
    """Return an instance of the first connected supported mouse."""

    for device_cls in SUPPORTED_DEVICES:
        for vid, pid in device_cls.capabilities.vid_pid_pairs:
            if usb.core.find(idVendor=vid, idProduct=pid) is not None:
                return device_cls()
    return None

"""Device declarations and registry."""

from .registry import SUPPORTED_DEVICES, find_supported_device, iter_supported_devices

__all__ = ["SUPPORTED_DEVICES", "find_supported_device", "iter_supported_devices"]

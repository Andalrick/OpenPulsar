import sys
import types

usb_module = types.ModuleType("usb")
usb_core_module = types.ModuleType("usb.core")
class USBError(Exception):
    pass

usb_core_module.find = lambda **_kwargs: None
usb_core_module.USBError = USBError
usb_util_module = types.ModuleType("usb.util")
usb_util_module.claim_interface = lambda *_args, **_kwargs: None
usb_util_module.release_interface = lambda *_args, **_kwargs: None
usb_module.core = usb_core_module
usb_module.util = usb_util_module
sys.modules.setdefault("usb", usb_module)
sys.modules.setdefault("usb.core", usb_core_module)
sys.modules.setdefault("usb.util", usb_util_module)

from openpulsar.devices.pulsar import PulsarX2HWired, PulsarX2Wired
from openpulsar.devices.registry import SUPPORTED_DEVICES


def test_x2_wired_identity_and_registration() -> None:
    capabilities = PulsarX2Wired.capabilities

    assert capabilities.name == "Pulsar X2 Wired"
    assert capabilities.vid_pid_pairs == [(0x3710, 0x1402)]
    assert capabilities.image == "Pulsar/X2_Wired_size2_device.svg"
    assert PulsarX2Wired in SUPPORTED_DEVICES


def test_x2_wired_matches_x2h_capabilities() -> None:
    x2 = PulsarX2Wired.capabilities
    x2h = PulsarX2HWired.capabilities

    assert x2.interface_num == x2h.interface_num
    assert x2.report_size == x2h.report_size
    assert x2.num_profiles == x2h.num_profiles
    assert x2.max_dpi_stages == x2h.max_dpi_stages
    assert x2.dpi_min == x2h.dpi_min
    assert x2.dpi_max == x2h.dpi_max
    assert x2.dpi_step == x2h.dpi_step
    assert x2.buttons == x2h.buttons
    assert x2.polling_rates == x2h.polling_rates
    assert x2.lod_values == x2h.lod_values
    assert x2.button_labels == x2h.button_labels

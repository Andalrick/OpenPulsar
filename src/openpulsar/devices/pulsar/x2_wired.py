from openpulsar.core.device import DeviceCapabilities
from openpulsar.protocol import SonixGen1Protocol


class PulsarX2Wired(SonixGen1Protocol):
    """Capability sheet for the Pulsar X2 Wired.

    Uses the same Sonix Gen1 wired protocol and capabilities as the X2H Wired,
    with a lower-profile shell and its own USB product identifier.
    """

    capabilities = DeviceCapabilities(
        name="Pulsar X2 Wired",
        vid_pid_pairs=[(0x3710, 0x1402)],
        interface_num=3,
        report_size=64,
        num_profiles=5,
        max_dpi_stages=6,
        dpi_min=100,
        dpi_max=26000,
        dpi_step=100,
        buttons={
            "left": 0x01,
            "right": 0x02,
            "wheel": 0x03,
            "thumb_back": 0x04,
            "thumb_front": 0x05,
            "dpi": 0x0B,
        },
        polling_rates=[125, 250, 500, 1000],
        lod_values=[1.0, 2.0],
        image="Pulsar/X2_Wired_size2_device.svg",
        button_labels={
            "left": "Left Click",
            "right": "Right Click",
            "wheel": "Wheel Click",
            "thumb_back": "Side Back (Backward)",
            "thumb_front": "Side Front (Forward)",
            "dpi": "DPI Button",
        },
    )

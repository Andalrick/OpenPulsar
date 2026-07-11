from openpulsar.core.buttons import KeyboardAction, MouseAction
from openpulsar.core.dpi import Color, DpiStage
from openpulsar.core.profile import Profile
from openpulsar.core.serialization import profile_from_dict, profile_to_dict


def test_profile_round_trip_keeps_local_and_hardware_fields():
    profile = Profile(
        name="Test profile",
        polling_rate=500,
        debounce=4,
        lod=2.0,
        motion_sync=True,
        angle_snap=False,
        ripple_control=True,
        dpi_stages=[DpiStage(800, Color(1, 2, 3)), DpiStage(1600, Color(4, 5, 6))],
        buttons={"left": MouseAction(1), "thumb_back": KeyboardAction(1, 6)},
        keyboard_commands=[{"label": "copy", "sequence": "ctrl+c"}],
        led_red_gain=80,
        led_green_gain=90,
        led_blue_gain=100,
        led_enabled=True,
        led_brightness=75,
        led_pulse_enabled=True,
        led_pulse=50,
    )

    loaded = profile_from_dict(profile_to_dict(profile))

    assert loaded.name == profile.name
    assert loaded.polling_rate == 500
    assert loaded.debounce == 4
    assert loaded.lod == 2.0
    assert loaded.motion_sync is True
    assert loaded.ripple_control is True
    assert [stage.dpi for stage in loaded.dpi_stages] == [800, 1600]
    assert [(s.color.r, s.color.g, s.color.b) for s in loaded.dpi_stages] == [(1, 2, 3), (4, 5, 6)]
    assert loaded.buttons == profile.buttons
    assert loaded.keyboard_commands == profile.keyboard_commands
    assert loaded.led_brightness == 75
    assert loaded.led_pulse == 50


def test_profile_from_old_flat_led_fields():
    loaded = profile_from_dict({"led_brightness": 0, "led_pulse": 0})
    assert loaded.led_brightness == 25
    assert loaded.led_pulse == 75
    assert loaded.led_enabled is False

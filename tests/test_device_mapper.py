import pytest

from openpulsar.core.buttons import (
    DisabledAction,
    DpiAction,
    KeyboardAction,
    MediaAction,
    MouseAction,
    OpenPulsarSpecialAction,
)
from openpulsar.core.device_mapper import decode_button_action, encode_button_action
from openpulsar.core.special_actions import SpecialAction


@pytest.mark.parametrize(
    "action, encoded",
    [
        (DisabledAction(), (0, 0, 0)),
        (MouseAction(4), (1, 4, 0)),
        (DpiAction(3), (9, 3, 0)),
        (KeyboardAction(1, 6), (2, 1, 6)),
        (MediaAction(0x00E9), (13, 0xE9, 0x00)),
        (OpenPulsarSpecialAction(SpecialAction.NEXT_PROFILE), (8, 3, 0)),
        (OpenPulsarSpecialAction(SpecialAction.PREVIOUS_PROFILE), (8, 4, 0)),
    ],
)
def test_button_action_encoding_round_trip(action, encoded):
    assert encode_button_action(action) == encoded
    assert decode_button_action(*encoded) == action


def test_decode_unknown_action_fails_loudly():
    with pytest.raises(ValueError):
        decode_button_action(99, 1, 2)

from openpulsar.core.device_mapper import is_valid_button_action


def test_invalid_mouse_button_action_is_rejected():
    assert not is_valid_button_action(MouseAction(0))
    assert not is_valid_button_action(MouseAction(99))
    assert is_valid_button_action(MouseAction(1))


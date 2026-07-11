import pytest

from openpulsar.hid import (
    BTN_TYPE_DPI,
    BTN_TYPE_KEYBOARD,
    BTN_TYPE_MEDIA,
    BTN_TYPE_MOUSE,
    BTN_TYPE_PROFILE,
    BTN_TYPE_SCROLL,
    BTN_TYPE_XCLICK,
    HID_KEYS,
    HID_MODS,
    describe_button,
    parse_button_function,
)


def test_parse_mouse_actions():
    assert parse_button_function("left") == (BTN_TYPE_MOUSE, 0x01, 0x00)
    assert parse_button_function("forward") == (BTN_TYPE_MOUSE, 0x04, 0x00)
    assert describe_button(BTN_TYPE_MOUSE, 0x05, 0) == "backward"


def test_parse_dpi_profile_scroll_xclick():
    assert parse_button_function("dpiloop") == (BTN_TYPE_DPI, 0x03, 0x00)
    assert parse_button_function("profile+") == (BTN_TYPE_PROFILE, 0x03, 0x00)
    assert parse_button_function("scrolldown") == (BTN_TYPE_SCROLL, 0xFF, 0x00)
    assert parse_button_function("xclick") == (BTN_TYPE_XCLICK, 0x01, 0x00)


def test_parse_keyboard_shortcut():
    btn_type, modifiers, key = parse_button_function("ctrl+shift+f5")
    assert btn_type == BTN_TYPE_KEYBOARD
    assert modifiers == (HID_MODS["ctrl"] | HID_MODS["shift"])
    assert key == HID_KEYS["f5"]
    assert describe_button(btn_type, modifiers, key) == "ctrl+shift+f5"


def test_parse_media_action():
    btn_type, a1, a2 = parse_button_function("vol+")
    assert btn_type == BTN_TYPE_MEDIA
    assert describe_button(btn_type, a1, a2) == "vol+"


def test_parse_unknown_key_is_helpful():
    with pytest.raises(ValueError) as excinfo:
        parse_button_function("ctrl+notakey")
    msg = str(excinfo.value)
    assert "Unknown button function or key" in msg
    assert "Keyboard" in msg

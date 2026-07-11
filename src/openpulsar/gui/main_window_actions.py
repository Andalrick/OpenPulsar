from openpulsar.i18n import tr
from openpulsar.core.buttons import (
    DisabledAction,
    MouseAction,
    MediaAction,
    DpiAction,
    KeyboardAction,
    OpenPulsarSpecialAction,
)
from openpulsar.core.special_actions import SpecialAction
from openpulsar.hid import HID_MODS, HID_KEYS


def action_to_text(action):
    if isinstance(action, DisabledAction):
        return tr("Disabled")

    if isinstance(action, MouseAction):
        return {
            1: tr("Left Click"),
            2: tr("Right Click"),
            3: tr("Middle Click"),
            4: tr("Back"),
            5: tr("Forward"),
        }.get(action.button, tr("Left Click"))

    if isinstance(action, DpiAction):
        return {
            1: tr("DPI Up"),
            2: tr("DPI Down"),
            3: tr("DPI Cycle"),
        }.get(action.action, tr("DPI Cycle"))

    if isinstance(action, MediaAction):
        return {
            205: tr("Play Pause"),
            181: tr("Next Track"),
            182: tr("Previous Track"),
            226: tr("Mute"),
            233: tr("Volume Up"),
            234: tr("Volume Down"),
        }.get(action.consumer_id, tr("Play Pause"))

    if isinstance(action, KeyboardAction):
        shortcut_actions = {
            (HID_MODS["ctrl"], HID_KEYS["c"]): tr("Copy"),
            (HID_MODS["ctrl"], HID_KEYS["v"]): tr("Paste"),
            (HID_MODS["ctrl"], HID_KEYS["x"]): tr("Cut"),
            (HID_MODS["ctrl"], HID_KEYS["z"]): tr("Undo"),
            (HID_MODS["ctrl"], HID_KEYS["y"]): tr("Redo"),
        }
        return shortcut_actions.get(
            (action.modifiers, action.key),
            tr("Copy"),
        )

    if isinstance(action, OpenPulsarSpecialAction):
        if action.action == SpecialAction.NEXT_PROFILE:
            return tr("Profile Next")

        if action.action == SpecialAction.PREVIOUS_PROFILE:
            return tr("Profile Previous")

    return tr("Left Click")


def text_to_action(text):
    if text == tr("Left Click"):
        return MouseAction(button=1)

    if text == tr("Right Click"):
        return MouseAction(button=2)

    if text == tr("Middle Click"):
        return MouseAction(button=3)

    if text == tr("Back"):
        return MouseAction(button=4)

    if text == tr("Forward"):
        return MouseAction(button=5)

    if text == tr("DPI Cycle"):
        return DpiAction(action=3)

    if text == tr("DPI Up"):
        return DpiAction(action=1)

    if text == tr("DPI Down"):
        return DpiAction(action=2)

    if text == tr("Play Pause"):
        return MediaAction(consumer_id=205)

    if text == tr("Next Track"):
        return MediaAction(consumer_id=181)

    if text == tr("Previous Track"):
        return MediaAction(consumer_id=182)

    if text == tr("Mute"):
        return MediaAction(consumer_id=226)

    if text == tr("Volume Up"):
        return MediaAction(consumer_id=233)

    if text == tr("Volume Down"):
        return MediaAction(consumer_id=234)

    if text == tr("Copy"):
        return KeyboardAction(
            modifiers=HID_MODS["ctrl"],
            key=HID_KEYS["c"],
        )

    if text == tr("Paste"):
        return KeyboardAction(
            modifiers=HID_MODS["ctrl"],
            key=HID_KEYS["v"],
        )

    if text == tr("Cut"):
        return KeyboardAction(
            modifiers=HID_MODS["ctrl"],
            key=HID_KEYS["x"],
        )

    if text == tr("Undo"):
        return KeyboardAction(
            modifiers=HID_MODS["ctrl"],
            key=HID_KEYS["z"],
        )

    if text == tr("Redo"):
        return KeyboardAction(
            modifiers=HID_MODS["ctrl"],
            key=HID_KEYS["y"],
        )

    if text == tr("Profile Next"):
        return OpenPulsarSpecialAction(
            action=SpecialAction.NEXT_PROFILE,
        )

    if text == tr("Profile Previous"):
        return OpenPulsarSpecialAction(
            action=SpecialAction.PREVIOUS_PROFILE,
        )

    if text == tr("Disabled"):
        return DisabledAction()

    return MouseAction(button=1)

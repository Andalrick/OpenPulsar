from dataclasses import dataclass

from .special_actions import SpecialAction


@dataclass
class ButtonAction:
    def to_dict(self):
        raise NotImplementedError


@dataclass
class DisabledAction(ButtonAction):
    def to_dict(self):
        return {"type": "disabled"}


@dataclass
class MouseAction(ButtonAction):
    button: int

    def to_dict(self):
        return {"type": "mouse", "button": self.button}


@dataclass
class KeyboardAction(ButtonAction):
    modifiers: int
    key: int

    def to_dict(self):
        return {"type": "keyboard", "modifiers": self.modifiers, "key": self.key}


@dataclass
class MediaAction(ButtonAction):
    consumer_id: int

    def to_dict(self):
        return {"type": "media", "consumer_id": self.consumer_id}


@dataclass
class DpiAction(ButtonAction):
    action: int

    def to_dict(self):
        return {"type": "dpi", "action": self.action}


@dataclass
class OpenPulsarSpecialAction(ButtonAction):
    action: SpecialAction

    def to_dict(self):
        return {"type": "special", "action": self.action.value}


def action_from_dict(data):
    action_type = data["type"]

    if action_type == "disabled":
        return DisabledAction()

    if action_type == "mouse":
        return MouseAction(button=data["button"])

    if action_type == "keyboard":
        return KeyboardAction(modifiers=data["modifiers"], key=data["key"])

    if action_type == "media":
        return MediaAction(consumer_id=data["consumer_id"])

    if action_type == "dpi":
        return DpiAction(action=data["action"])

    if action_type == "special":
        return OpenPulsarSpecialAction(action=SpecialAction(data["action"]))

    raise ValueError(f"Unknown action type: {action_type}")

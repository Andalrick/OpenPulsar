import time

from openpulsar.logging_utils import get_logger

from openpulsar.core.buttons import (
    ButtonAction,
    DisabledAction,
    DpiAction,
    KeyboardAction,
    MediaAction,
    MouseAction,
    OpenPulsarSpecialAction,
)
from openpulsar.core.dpi import Color, DpiStage
from openpulsar.core.profile import Profile
from openpulsar.core.special_actions import SpecialAction


logger = get_logger(__name__)

HARDWARE_READ_ERRORS = (OSError, IOError, RuntimeError, ValueError, TypeError, AttributeError)


BUTTON_IDS = {
    "left": 0x01,
    "right": 0x02,
    "wheel": 0x03,
    "thumb_back": 0x04,
    "thumb_front": 0x05,
    "dpi": 0x0B,
}


def is_valid_button_action(action: ButtonAction) -> bool:
    if isinstance(action, MouseAction):
        return action.button in {1, 2, 3, 4, 5}

    if isinstance(action, DpiAction):
        return action.action in {1, 2, 3}

    if isinstance(action, MediaAction):
        return action.consumer_id in {205, 181, 182, 226, 233, 234}

    if isinstance(action, KeyboardAction):
        return bool(action.key)

    if isinstance(action, (DisabledAction, OpenPulsarSpecialAction)):
        return True

    return False


def encode_button_action(action: ButtonAction) -> tuple[int, int, int]:
    if isinstance(action, DisabledAction):
        return 0, 0, 0

    if isinstance(action, MouseAction):
        return 1, action.button, 0

    if isinstance(action, DpiAction):
        return 9, action.action, 0

    if isinstance(action, KeyboardAction):
        return 2, action.modifiers, action.key

    if isinstance(action, MediaAction):
        return 13, action.consumer_id & 0xFF, action.consumer_id >> 8

    if isinstance(action, OpenPulsarSpecialAction):
        if action.action == SpecialAction.NEXT_PROFILE:
            return 8, 3, 0

        if action.action == SpecialAction.PREVIOUS_PROFILE:
            return 8, 4, 0

        raise ValueError(
            f"Unsupported OpenPulsar special action: {action.action}"
        )

    raise TypeError(f"Unsupported button action: {action!r}")


def decode_button_action(
    button_type: int,
    a1: int,
    a2: int,
) -> ButtonAction:
    if button_type == 0:
        return DisabledAction()

    if button_type == 1:
        return MouseAction(
            button=a1,
        )

    if button_type == 9:
        return DpiAction(action=a1)

    if button_type == 2:
        return KeyboardAction(
            modifiers=a1,
            key=a2,
        )

    if button_type == 13:
        return MediaAction(
            consumer_id=a1 | (a2 << 8),
        )

    if button_type == 8:
        if a1 == 3:
            return OpenPulsarSpecialAction(
                action=SpecialAction.NEXT_PROFILE,
            )

        if a1 == 4:
            return OpenPulsarSpecialAction(
                action=SpecialAction.PREVIOUS_PROFILE,
            )

    raise ValueError(
        f"Unsupported button action: {(button_type, a1, a2)!r}"
    )


def apply_profile_to_mouse(
    mouse,
    profile: Profile,
    slot: int,
    progress_callback=None,
) -> None:
    if progress_callback:
        progress_callback("Writing polling rate")

    mouse.set_polling_rate(profile.polling_rate, slot)
    time.sleep(0.05)

    if progress_callback:
        progress_callback("Writing debounce")

    mouse.set_debounce(profile.debounce, slot)
    time.sleep(0.05)

    if hasattr(profile, "lod"):
        if progress_callback:
            progress_callback("Writing LOD")

        mouse.set_lod(profile.lod, slot)
        time.sleep(0.05)

    if progress_callback:
        progress_callback("Writing motion sync")

    mouse.set_motion_sync(profile.motion_sync, slot)
    time.sleep(0.05)

    if progress_callback:
        progress_callback("Writing angle snap")

    mouse.set_angle_snap(profile.angle_snap, slot)
    time.sleep(0.05)

    if progress_callback:
        progress_callback("Writing ripple control")

    mouse.set_ripple_control(profile.ripple_control, slot)
    time.sleep(0.05)

    if progress_callback:
        progress_callback("Writing DPI stages")

    dpi_values = [stage.dpi for stage in profile.dpi_stages]

    active_dpi_stage = max(1, min(int(getattr(profile, "active_dpi_stage", 1)), len(dpi_values) or 1))

    mouse.set_dpi_stages(
        dpi_values,
        active_dpi_stage,
        slot,
    )
    time.sleep(0.05)

    if getattr(mouse.capabilities, "has_stage_colors", True):
        if progress_callback:
            progress_callback("Writing DPI colors")

        for index, stage in enumerate(
            profile.dpi_stages,
            start=1,
        ):
            mouse.set_stage_color(
                index,
                stage.color.r,
                stage.color.g,
                stage.color.b,
                slot,
            )

            time.sleep(0.05)

    if progress_callback:
        progress_callback("Writing buttons")

    button_ids = getattr(mouse.capabilities, "buttons", None) or BUTTON_IDS

    for button_name, action in profile.buttons.items():
        button_id = button_ids.get(button_name) or BUTTON_IDS.get(button_name)
        if button_id is None:
            continue

        button_type, a1, a2 = encode_button_action(
            action
        )

        try:
            mouse.set_button(
                button_id,
                button_type,
                a1,
                a2,
                slot,
            )
        except NotImplementedError:
            continue

        time.sleep(0.05)

    # Dynamic state reconciliation is handled by the GUI light refresh.
    # Full profile writes should not force an artificial profile reload.

    if progress_callback:
        progress_callback("Done")


def read_profile_from_mouse(
    mouse,
    slot: int,
    name: str = "Imported",
) -> Profile:
    dpi = mouse.get_dpi_stages(slot)

    stages = []

    for index, value in enumerate(
        dpi["stages"],
        start=1,
    ):
        dpi_value = value[0]

        if getattr(mouse.capabilities, "has_stage_colors", True):
            try:
                r, g, b = mouse.get_stage_color(
                    index,
                    slot,
                )
            except HARDWARE_READ_ERRORS as exc:
                logger.debug("Unable to read DPI stage color %s for slot %s: %s", index, slot, exc)
                r, g, b = (255, 255, 255)
        else:
            r, g, b = (255, 255, 255)

        stages.append(
            DpiStage(
                dpi=dpi_value,
                color=Color(
                    r,
                    g,
                    b,
                ),
            )
        )

    buttons = {}

    button_ids = getattr(mouse.capabilities, "buttons", None) or BUTTON_IDS

    for button_name, button_id in button_ids.items():
        try:
            button_type, a1, a2 = mouse.get_button(
                button_id,
                slot,
            )

            action = decode_button_action(
                button_type,
                a1,
                a2,
            )

            if not is_valid_button_action(action):
                raise ValueError(
                    f"Invalid decoded button action for {button_name}: "
                    f"{(button_type, a1, a2)!r} -> {action!r}"
                )

            buttons[button_name] = action
        except HARDWARE_READ_ERRORS as exc:
            logger.debug(
                "Unable to read button %s for slot %s from hardware: %s",
                button_name,
                slot,
                exc,
                exc_info=True,
            )
            # Do not invent button mappings here. The UI must reflect values
            # successfully decoded from the mouse, not factory defaults.
            continue

    try:
        active_dpi_stage = mouse.get_active_dpi_stage(slot)
        if not 1 <= active_dpi_stage <= len(stages):
            active_dpi_stage = 1
    except HARDWARE_READ_ERRORS as exc:
        logger.debug("Unable to read active DPI stage for slot %s: %s", slot, exc)
        active_dpi_stage = 1

    # LED brightness/effect are per-profile firmware settings.
    # RGB gain is profile-local in OpenPulsar because it defines the logical
    # color compensation used when writing this profile's stage colors.
    try:
        lo, hi = mouse.capabilities.brightness_range
        raw_brightness = mouse.get_brightness(slot)
        led_brightness = int(round(((raw_brightness - lo) * 100) / max(1, hi - lo)))
        led_brightness = min((25, 50, 75, 100), key=lambda value: abs(value - led_brightness))
    except HARDWARE_READ_ERRORS as exc:
        logger.debug("Unable to read LED brightness for slot %s: %s", slot, exc)
        led_brightness = 100

    try:
        effect = mouse.get_led_effect(slot)
        led_enabled = effect != "off"
        led_pulse_enabled = effect == "breath"
        if led_pulse_enabled:
            raw_speed = mouse.get_breath_speed(slot)
            lo_speed, hi_speed = mouse.capabilities.breath_speed_range
            # Firmware speed is inverted on tested Pulsar devices: lower is faster.
            pulse = int(round(((hi_speed - raw_speed) * 100) / max(1, hi_speed - lo_speed)))
            led_pulse = min((25, 50, 75, 100), key=lambda value: abs(value - pulse))
        else:
            led_pulse = 75
    except HARDWARE_READ_ERRORS as exc:
        logger.debug("Unable to read LED effect for slot %s: %s", slot, exc)
        led_enabled = True
        led_pulse_enabled = False
        led_pulse = 75

    def _try_setting(getter, fallback):
        try:
            return getter(slot)
        except HARDWARE_READ_ERRORS as exc:
            name = getattr(getter, "__name__", repr(getter))
            logger.debug("Unable to read %s for slot %s: %s", name, slot, exc)
            return fallback

    return Profile(
        name=name,
        polling_rate=_try_setting(mouse.get_polling_rate, 1000),
        debounce=_try_setting(mouse.get_debounce, 3),
        lod=_try_setting(mouse.get_lod, 1.0),
        motion_sync=_try_setting(mouse.get_motion_sync, False),
        angle_snap=_try_setting(mouse.get_angle_snap, False),
        ripple_control=_try_setting(mouse.get_ripple_control, False),
        dpi_stages=stages,
        buttons=buttons,
        active_dpi_stage=active_dpi_stage,
        led_enabled=led_enabled,
        led_brightness=led_brightness,
        led_pulse_enabled=led_pulse_enabled,
        led_pulse=led_pulse,
    )

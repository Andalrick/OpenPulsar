from openpulsar.core.dpi import Color


def led_correction_gains_for_profile(profile):
    def gain(attr):
        try:
            value = int(getattr(profile, attr, 100))
        except (TypeError, ValueError):
            value = 100
        return max(0, min(100, value)) / 100.0

    return (
        gain("led_red_gain"),
        gain("led_green_gain"),
        gain("led_blue_gain"),
    )


def apply_led_correction_to_color(color, gains):
    """Return the color actually sent to the physical LED."""
    if not isinstance(color, Color):
        return color

    red_gain, green_gain, blue_gain = gains

    return Color(
        max(0, min(255, int(round(color.r * red_gain)))),
        max(0, min(255, int(round(color.g * green_gain)))),
        max(0, min(255, int(round(color.b * blue_gain)))),
    )


def remove_led_correction_from_color(color, gains):
    """Convert a hardware LED color back to the logical UI color."""
    if not isinstance(color, Color):
        return color

    red_gain, green_gain, blue_gain = gains

    def restore(channel, gain):
        if gain <= 0:
            return channel
        return max(0, min(255, int(round(channel / gain))))

    return Color(
        restore(color.r, red_gain),
        restore(color.g, green_gain),
        restore(color.b, blue_gain),
    )

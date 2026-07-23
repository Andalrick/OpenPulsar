"""OpenPulsar UI design constants.

The UI is intentionally built around a small set of reusable "pill" controls.
Keeping these values in one place makes future theme/color editing easier while
preserving the current fixed-window design.
"""

OP_BLUE = "#2f6cff"
OP_BLUE_TEXT = "#0f63ff"
OP_BLUE_SOFT = "#eef4ff"

OP_WHITE = "#ffffff"
OP_TEXT = "#1f2937"
OP_TEXT_DARK = "#0f172a"

OP_BORDER = "#cbd5e1"
OP_BORDER_SOFT = "#d8e1f2"
OP_PANEL_BORDER = "#d9e0ec"

OP_RADIUS_RATIO = 0.25
OP_CIRCLE_RADIUS_RATIO = 0.50


def op_radius(height: int) -> int:
    """Return the standard corner radius for an interactive control."""
    if height <= 0:
        raise ValueError("height must be greater than zero")
    return round(height * OP_RADIUS_RATIO)


def op_circle_radius(height: int) -> int:
    """Return the radius required to make a square control circular."""
    if height <= 0:
        raise ValueError("height must be greater than zero")
    return round(height * OP_CIRCLE_RADIUS_RATIO)


def op_padding_x(height: int) -> int:
    """Return the standard horizontal padding for an interactive control."""
    if height <= 0:
        raise ValueError("height must be greater than zero")
    return round(height * 0.65)


def op_icon_size(height: int) -> int:
    """Return the standard icon size for an interactive control."""
    if height <= 0:
        raise ValueError("height must be greater than zero")
    return round(height * 0.60)


def op_spacing(height: int) -> int:
    """Return the standard internal spacing for an interactive control."""
    if height <= 0:
        raise ValueError("height must be greater than zero")
    return round(height * 0.30)



# Standard control heights and their derived corner radii.
# Rectangular interactive controls follow: radius = height / 4.
# Square icon controls use op_circle_radius(height): radius = height / 2.
OP_CONTROL_HEIGHT_XS = 16
OP_CONTROL_HEIGHT_S = 24
OP_CONTROL_HEIGHT_M = 26
OP_CONTROL_HEIGHT_L = 28
OP_CONTROL_HEIGHT_XL = 30
OP_CONTROL_HEIGHT_XXL = 32

OP_CONTROL_RADIUS_XS = op_radius(OP_CONTROL_HEIGHT_XS)
OP_CONTROL_RADIUS_S = op_radius(OP_CONTROL_HEIGHT_S)
OP_CONTROL_RADIUS_M = op_radius(OP_CONTROL_HEIGHT_M)
OP_CONTROL_RADIUS_L = op_radius(OP_CONTROL_HEIGHT_L)
OP_CONTROL_RADIUS_XL = op_radius(OP_CONTROL_HEIGHT_XL)
OP_CONTROL_RADIUS_XXL = op_radius(OP_CONTROL_HEIGHT_XXL)

OP_PILL_HEIGHT = 28
OP_PILL_RADIUS = op_radius(OP_PILL_HEIGHT)
OP_PILL_PADDING_X = op_padding_x(OP_PILL_HEIGHT)
OP_PILL_ICON_SIZE = op_icon_size(OP_PILL_HEIGHT)
OP_PILL_SPACING = op_spacing(OP_PILL_HEIGHT)

# Backwards-compatible generic control radius.
OP_RADIUS = OP_PILL_RADIUS
OP_PILL_BORDER = 1
OP_PILL_BORDER_ACTIVE = 2

OP_MARGIN_OUTER = 16
OP_PANEL_SPACING = 12
OP_CONTROL_SPACING = 8
OP_ANIMATION_MS = 150

OP_DANGER = "#ef4444"
OP_DANGER_SOFT = "#fff7f7"
OP_DANGER_HOVER = "#fff1f2"
OP_DANGER_TEXT = "#dc2626"
OP_DANGER_TEXT_HOVER = "#b91c1c"

# Floating panel / “feuillet” treatment.
OP_PANEL_BG_TOP = "#ffffff"
OP_PANEL_BG_BOTTOM = "#f8fbff"
OP_PANEL_BORDER_LIGHT = "#e7edf6"
OP_PANEL_BORDER = "#d5deec"
OP_PANEL_BORDER_DARK = "#c8d3e2"
OP_PANEL_SHADOW_COLOR = "#8291a8"
OP_PANEL_SHADOW_BLUR = 30
OP_PANEL_SHADOW_OFFSET_Y = 4
OP_PANEL_SHADOW_ALPHA = 118

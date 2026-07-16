
from .metrics import PANEL_BORDER_WIDTH


def profile_segment_style(
    active=False,
    left_radius=False,
    right_radius=False,
    accent=False,
):
    bg = "#2f6cff" if (active or accent) else "#ffffff"
    fg = "#ffffff" if (active or accent) else "#1f2937"
    hover_bg = "#2f6cff" if (active or accent) else "#eef4ff"
    hover_fg = "#ffffff" if (active or accent) else "#1d4ed8"
    border = "#2f6cff" if (active or accent) else "#d9e0ec"
    radius_left = 12 if left_radius else 0
    radius_right = 12 if right_radius else 0
    weight = "700" if (active or accent) else "500"
    font_size = "16px" if accent else "14px"

    # Important : on ne change pas l'épaisseur ni la géométrie
    # de la bordure au survol. Sinon un segment au milieu, comme P3,
    # affiche un contour incomplet dans la barre segmentée.
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: {PANEL_BORDER_WIDTH}px solid {border};
            border-left: 0px;
            border-radius: 0px;
            border-top-left-radius: {radius_left}px;
            border-bottom-left-radius: {radius_left}px;
            border-top-right-radius: {radius_right}px;
            border-bottom-right-radius: {radius_right}px;
            padding: 0px;
            font-weight: {weight};
            font-size: {font_size};
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            color: {hover_fg};
            border: {PANEL_BORDER_WIDTH}px solid {border};
            border-left: 0px;
        }}
        QPushButton:pressed {{
            background-color: #2f6cff;
            color: #ffffff;
            border: {PANEL_BORDER_WIDTH}px solid #2f6cff;
            border-left: 0px;
        }}
    """

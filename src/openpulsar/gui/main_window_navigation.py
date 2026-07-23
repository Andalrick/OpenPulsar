from PySide6.QtGui import QIcon

from .metrics import PANEL_BORDER_WIDTH, PANEL_RADIUS
from .widgets.common_widgets import TAB_ICONS


def _main_tab_style(self, active=False, side="left"):
    radius = PANEL_RADIUS
    left_radius = radius if side == "left" else 0
    right_radius = radius if side == "right" else 0

    bg = "#2f6cff" if active else "#ffffff"
    fg = "#ffffff" if active else "#334155"
    border = "#2f6cff" if active else "#cbd5e1"
    hover_bg = "#2f6cff" if active else "#eef4ff"
    hover_fg = "#ffffff" if active else "#1d4ed8"
    weight = "700" if active else "600"

    shared_edge = "border-left: none;" if side == "right" else ""

    return f"""
        QPushButton#mainTabButton {{
            background-color: {bg};
            border: {PANEL_BORDER_WIDTH}px solid {border};
            {shared_edge}
            border-radius: 0px;
            border-top-left-radius: {left_radius}px;
            border-top-right-radius: {right_radius}px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            padding: 0px;
            color: {fg};
            font-size: 13px;
            font-weight: {weight};
        }}
        QPushButton#mainTabButton:hover {{
            background-color: {hover_bg};
            border: {PANEL_BORDER_WIDTH}px solid #2f6cff;
            color: {hover_fg};
        }}
    """


def select_main_tab(self, index):
    persistent_prompt = index == 1 and not self.persistent_mode

    self.main_stack.setCurrentIndex(index)

    if persistent_prompt:
        self.ask_enable_persistent_for_keyboard_commands()

    self.buttons_tab_button.setIcon(
        QIcon(
            TAB_ICONS["buttons"][
                "active" if index == 0 else "inactive"
            ]
        )
    )
    self.logic_tab_button.setIcon(
        QIcon(
            TAB_ICONS["keyboard_commands"][
                "active" if index == 1 else "inactive"
            ]
        )
    )

    self.buttons_tab_button.setStyleSheet(
        self._main_tab_style(active=index == 0, side="left")
    )
    self.logic_tab_button.setStyleSheet(
        self._main_tab_style(active=index == 1, side="right")
    )

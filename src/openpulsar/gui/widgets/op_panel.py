"""Reusable OpenPulsar panel primitives."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from ..metrics import HEADER_HEIGHT, PANEL_BODY_HEIGHT, PANEL_HEIGHT
from .common_widgets import apply_openpulsar_panel_effect


class OPPanel(QWidget):
    """Two-part OpenPulsar panel with an autonomous header and body.

    Both parts are independent widgets. The header owns the upper corners,
    while the body owns the lower corners. This avoids QGroupBox title margins
    and guarantees pixel-identical panel heights.
    """

    def __init__(
        self,
        width: int,
        *,
        header: QWidget,
        body: QWidget,
        parent: QWidget | None = None,
        shadow: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("opPanel")
        self.setFixedSize(width, PANEL_HEIGHT)

        header.setObjectName(header.objectName() or "opPanelHeader")
        body.setObjectName(body.objectName() or "opPanelBody")
        header.setFixedSize(width, HEADER_HEIGHT)
        body.setFixedSize(width, PANEL_BODY_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(header)
        layout.addWidget(body)

        self.header = header
        self.body = body

        if shadow:
            apply_openpulsar_panel_effect(self)

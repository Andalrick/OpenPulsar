"""Geometry contract for the shared OpenPulsar panel component."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QWidget

from openpulsar.gui.metrics import HEADER_HEIGHT, PANEL_BODY_HEIGHT, PANEL_HEIGHT
from openpulsar.gui.widgets.op_panel import OPPanel


def test_op_panel_uses_shared_geometry():
    app = QApplication.instance() or QApplication([])
    header = QWidget()
    body = QWidget()
    panel = OPPanel(180, header=header, body=body, shadow=False)

    assert panel.height() == PANEL_HEIGHT
    assert header.height() == HEADER_HEIGHT
    assert body.height() == PANEL_BODY_HEIGHT
    assert header.height() + body.height() == panel.height()

    panel.close()

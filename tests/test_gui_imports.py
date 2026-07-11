"""Smoke-test GUI module imports.

These tests intentionally do not create a QApplication or instantiate widgets.
They only verify that GUI modules remain importable after refactors, which
catches missing explicit imports such as QTimer after removing wildcard imports.
"""

import importlib

import pytest

pytest.importorskip("PySide6")


@pytest.mark.parametrize(
    "module_name",
    [
        "openpulsar.gui.app",
        "openpulsar.gui.main_window",
        "openpulsar.gui.main_window_actions",
        "openpulsar.gui.main_window_device",
        "openpulsar.gui.main_window_dialogs",
        "openpulsar.gui.main_window_dpi_panel",
        "openpulsar.gui.main_window_led_panel",
        "openpulsar.gui.main_window_profiles",
        "openpulsar.gui.main_window_support",
        "openpulsar.gui.main_window_tray",
        "openpulsar.gui.main_window_ui",
        "openpulsar.gui.settings_dialog",
        "openpulsar.gui.profile.profile_extras_store",
        "openpulsar.gui.widgets.common_widgets",
        "openpulsar.gui.widgets.dpi_widgets",
        "openpulsar.gui.widgets.keyboard_widgets",
        "openpulsar.gui.widgets.led_widgets",
        "openpulsar.gui.widgets.mouse_button_widgets",
        "openpulsar.gui.widgets.popup_widgets",
        "openpulsar.gui.widgets.qt_delegates",
        "openpulsar.gui.widgets.sensor_widgets",
    ],
)
def test_gui_module_imports(module_name):
    importlib.import_module(module_name)

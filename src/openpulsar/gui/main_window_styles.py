"""Stylesheets used by the OpenPulsar main window.

This module intentionally contains only QSS/text helpers so it can be
extracted from main_window.py without touching runtime behaviour.
"""

from .metrics import PANEL_BORDER_WIDTH, PANEL_RADIUS
from .theme import (
    OP_PILL_RADIUS,
    OP_CONTROL_RADIUS_XS,
    OP_CONTROL_RADIUS_S,
    OP_CONTROL_RADIUS_M,
    OP_CONTROL_RADIUS_L,
    OP_CONTROL_RADIUS_XL,
    OP_CONTROL_RADIUS_XXL,
    op_radius,
    op_circle_radius,
)
from .widgets.common_widgets import qss_url


LIGHT_THEME_QSS = """
        QMainWindow {
            background-color: #f4f6fb;
        }

        QWidget#centralWidget {
            background-image: url({background_image});
            background-repeat: no-repeat;
            background-position: top left;
        }

        QWidget#headerSpacer {
            background: transparent;
        }

        QWidget {
            color: #1f2937;
            font-family: Inter, Segoe UI, Arial;
            font-size: 12px;
        }

        QGroupBox {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #ffffff,
                stop: 0.78 rgba(255, 255, 255, 246),
                stop: 1 #f8fbff
            );
            border: {panel_border_width}px solid #c7d2e2;
            border-radius: {panel_radius}px;
            margin-top: 10px;
            padding: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 6px;
            color: #334155;
            font-weight: bold;
        }

        QGroupBox#profilesBox {
            padding: 0px;
        }

        QWidget#buttonsPanel,
        QWidget#opPanel {
            background-color: transparent;
            border: none;
        }

        QWidget#opPanelHeader {
            background-color: #ffffff;
            border: {panel_border_width}px solid #c7d2e2;
            border-bottom: none;
            border-top-left-radius: {panel_radius}px;
            border-top-right-radius: {panel_radius}px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        }

        QWidget#opPanelBody {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #ffffff,
                stop: 0.78 rgba(255, 255, 255, 246),
                stop: 1 #f8fbff
            );
            border: {panel_border_width}px solid #c7d2e2;
            border-top: none;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: {panel_radius}px;
            border-bottom-right-radius: {panel_radius}px;
        }

        QGroupBox#sensorBox {
            padding: 0px;
        }

        QGroupBox#subPanelBox {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #ffffff,
                stop: 1 #fbfdff
            );
            border: {panel_border_width}px solid #cdd8e8;
            border-radius: {panel_radius}px;
        }

        QLabel {
            color: #1f2937;
        }

        QWidget#sectionHeader {
            background-color: transparent;
        }

        QLabel#sectionTitle {
            color: #334155;
            font-size: 13px;
            font-weight: 600;
            padding-top: 0px;
        }

        QLabel#sectionIcon {
            background-color: transparent;
        }

        QLabel#noDeviceLabel {
            background-color: transparent;
        }

        QPushButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_32}px;
            padding: 6px;
            color: #1f2937;
        }

        QPushButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
        }

        QPushButton:pressed {
                background-color: #dbeafe;
        }


        QPushButton#logExportButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: {control_radius_20}px;
            padding: 1px;
        }

        QPushButton#logExportButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
        }

        QPushButton#logExportButton:pressed {
            background-color: #dbeafe;
            border: 1px solid #2f6cff;
        }

        QPushButton#settingsButton {
            background-color: rgba(255, 255, 255, 0);
            border: 1px solid rgba(203, 213, 225, 0);
            border-radius: {control_radius_32}px;
            padding: 4px;
        }

        QPushButton#settingsButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
        }

        QPushButton#settingsButton[settingsOpen="true"] {
            background-color: #ffffff;
            border: 1px solid #2f6cff;
        }

        QPushButton#settingsButton:pressed {
            background-color: #dbeafe;
            border: 1px solid #2f6cff;
        }

        QComboBox,
        QSpinBox {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_28}px;
            padding: 4px 8px;
            color: #1f2937;
            min-height: 20px;
        }

        QComboBox:hover,
        QSpinBox:hover,
        QComboBox:focus,
        QSpinBox:focus {
            border: 1px solid #2f6cff;
            background-color: #eef4ff;
            padding: 3px 7px;
        }

        QComboBox::drop-down {
            border: none;
            width: 22px;
        }

        QComboBox#mouseButtonCombo::drop-down {
            width: 0px;
            border: none;
        }

        QComboBox#mouseButtonCombo::down-arrow {
            image: none;
            width: 0px;
            height: 0px;
        }


        QWidget#dpiStageRow {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: {row_radius}px;
        }

        QWidget#dpiStageRow:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
        }

        QWidget#dpiStageRow[active="true"] {
            background-color: #2f6cff;
            border: 1px solid #2f6cff;
        }

        QWidget#dpiStageRow[active="true"] QWidget#dpiValueControl {
            background-color: #ffffff;
            border-color: #ffffff;
        }

        QWidget#dpiStageRow[active="true"] QLineEdit#dpiValueEdit {
            background-color: #ffffff;
            color: #111827;
        }

        QWidget#dpiStageRow[active="true"] QPushButton#dpiMinusButton,
        QWidget#dpiStageRow[active="true"] QPushButton#dpiPlusButton {
            background-color: #ffffff;
            color: #2f6cff;
        }

        QWidget#dpiStageRow[active="true"] QPushButton#dpiMinusButton:hover,
        QWidget#dpiStageRow[active="true"] QPushButton#dpiPlusButton:hover {
            background-color: #eef4ff;
            color: #1d4ed8;
        }

        QWidget#dpiValueControl {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_26}px;
        }

        QWidget#dpiValueControl:disabled {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
        }

        QLineEdit#dpiValueEdit {
            background-color: #ffffff;
            border: none;
            color: #1f2937;
            padding: 0;
            selection-background-color: #2f6cff;
            selection-color: #ffffff;
        }

        QLineEdit#dpiValueEdit:focus {
            background-color: #ffffff;
            color: #111827;
        }

        QLabel#sensorValueLabel {
            background-color: #ffffff;
            border: none;
            color: #1f2937;
            padding: 0;
        }

        QLabel#sensorValueLabel:disabled {
            background-color: #f8fafc;
            color: #94a3b8;
        }

        QPushButton#dpiMinusButton,
        QPushButton#dpiPlusButton {
            background-color: transparent;
            border: none;
            border-radius: 0;
            padding: 0;
            font-weight: bold;
            color: #334155;
        }

        QPushButton#dpiMinusButton {
            border-right: 1px solid #e2e8f0;
            border-top-left-radius: 7px;
            border-bottom-left-radius: 7px;
        }

        QPushButton#dpiPlusButton {
            border-left: 1px solid #e2e8f0;
            border-top-right-radius: 7px;
            border-bottom-right-radius: 7px;
        }

        QPushButton#dpiMinusButton:hover,
        QPushButton#dpiPlusButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QPushButton#dpiMinusButton:disabled,
        QPushButton#dpiPlusButton:disabled {
            background-color: #f8fafc;
            color: #cbd5e1;
        }

        QPushButton#dpiLedButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 0;
        }

        QPushButton#dpiLedButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
        }

        QPushButton#ledSettingsButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            padding: 0px;
            color: #1f2937;
            font-size: 6px;
            font-weight: 900;
        }

        QPushButton#ledSettingsButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QPushButton#ledSettingsButton[ledPanelOpen="true"] {
            background-color: #ffffff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QWidget#ledManagementPanel,
        QWidget#dpiPage {
            background-color: transparent;
            border: none;
        }

        QStackedWidget#dpiContentStack {
            background-color: transparent;
            border: none;
        }

        QLabel#ledPanelTitle,
        QLabel#ledSubtitleLabel {
            color: #1f2937;
            font-size: 12px;
            font-weight: 800;
        }

        QWidget#ledSubtitleRow,
        QWidget#ledGainRow,
        QWidget#ledSliderColumn {
            background-color: transparent;
        }

        QWidget#ledPanelSeparator {
            background-color: #e2e8f0;
            border: none;
        }

        QLabel#ledSliderIcon {
            background-color: transparent;
            color: #334155;
            font-size: 15px;
            font-weight: 800;
        }

        QComboBox#mouseButtonCombo {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_16}px;
            padding-left: 8px;
            padding-right: 0px;
            min-height: 16px;
        }

        QComboBox#mouseButtonCombo:hover,
        QComboBox#mouseButtonCombo:focus {
            border: 1px solid #2f6cff;
            background-color: #eef4ff;
            color: #1d4ed8;
            padding-left: 7px;
            padding-right: 0px;
        }


        QMenu#mouseButtonActionMenu {
            background-color: #ffffff;
            border: 1px solid #d8e1f2;
            border-radius: {panel_radius}px;
            padding: 0px;
        }

        QTreeWidget#mouseButtonActionTree {
            background-color: #ffffff;
            border: 1px solid #d8e1f2;
            border-radius: {panel_radius}px;
            padding: 3px;
            outline: 0;
            color: #0f172a;
            font-size: 11px;
            selection-background-color: transparent;
        }

        QTreeWidget#mouseButtonActionTree::item {
            min-height: 18px;
            padding: 0px 2px;
            border-radius: 0px;
        }

        QTreeWidget#mouseButtonActionTree::item:hover {
            background-color: #eef4ff;
            color: #0f63ff;
        }

        QTreeWidget#mouseButtonActionTree::item:selected {
            background: transparent;
            color: #0f63ff;
        }

        QTreeWidget#mouseButtonActionTree::branch {
            background: transparent;
            border-image: none;
            image: none;
            width: 10px;
        }

        QTreeWidget#mouseButtonActionTree::branch:closed:has-children {
            image: url({tree_triangle_closed});
        }

        QTreeWidget#mouseButtonActionTree::branch:open:has-children {
            image: url({tree_triangle_open});
        }

        QCheckBox {
            spacing: 8px;
        }

        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_16}px;
            background-color: #ffffff;
        }

        QCheckBox::indicator:hover {
            border: 1px solid #2f6cff;
            background-color: #eef4ff;
        }

        QCheckBox::indicator:checked {
            background-color: #2f6cff;
            border: 1px solid #2f6cff;
            image: url({check_icon});
        }


        QMenu#dpiColorMenu {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {panel_radius}px;
            padding: 0px;
        }

        QWidget#dpiColorPalette {
            background-color: #ffffff;
            border-radius: {panel_radius}px;
        }

        QPushButton#helpButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {help_button_radius}px;
            padding: 0px;
            color: #2f6cff;
            font-weight: 700;
            font-size: 11px;
        }

        QPushButton#helpButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QPushButton#helpButton[contextHelpVisible="false"] {
            background-color: transparent;
            border: 1px solid transparent;
            color: transparent;
        }

        QPushButton#helpButton[contextHelpVisible="false"]:hover {
            background-color: transparent;
            border: 1px solid transparent;
            color: transparent;
        }

        QWidget#helpLabel {
            background-color: transparent;
        }

        QWidget#helpPopup {
            background-color: #ffffff;
            border: {panel_border_width}px solid #2f6cff;
            border-radius: {panel_radius}px;
        }

        QWidget#aboutPopup {
            background-color: #ffffff;
            border: {panel_border_width}px solid #2f6cff;
            border-radius: {panel_radius}px;
        }

        QLabel#helpPopupTitle {
            color: #1f2937;
            font-weight: 700;
            font-size: 13px;
        }

        QLabel#helpPopupBody {
            color: #334155;
            font-size: 12px;
            line-height: 1.25;
        }

        QLabel#aboutProductName {
            color: #1f2937;
            font-size: 18px;
            font-weight: 700;
        }

        QLabel#aboutVersion {
            color: #64748b;
            font-size: 12px;
        }

        QPushButton#aboutLinkButton {
            background-color: #ffffff;
            border: 1px solid #2f6cff;
            border-radius: {control_radius_30}px;
            padding: 0px;
            color: #1d4ed8;
            font-weight: 600;
        }

        QPushButton#aboutLinkButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QLabel#usbStatusIndicator {
            background-color: transparent;
            border: none;
            font-size: 13px;
            font-weight: 900;
            padding: 0px;
        }

        QPushButton#aboutHoverButton {
            background-color: transparent;
            border: none;
            border-radius: 16px;
            padding: 0px;
            color: transparent;
            font-weight: 700;
            font-size: 16px;
        }

        QPushButton#aboutHoverButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QPushButton#aboutHoverButton[aboutOpen="true"] {
            background-color: #2f6cff;
            border: 1px solid #2f6cff;
            color: #ffffff;
        }


        QPushButton#mainTabButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_28}px;
            padding: 0 12px;
            color: #334155;
            font-weight: 600;
        }

        QPushButton#mainTabButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QWidget#mainTabBar {
            background-color: transparent;
        }

        QStackedWidget#mainStack {
            background-color: #ffffff;
            border: {panel_border_width}px solid #cbd5e1;
            border-top: none;
            border-radius: 0px;
            border-bottom-left-radius: {panel_radius}px;
            border-bottom-right-radius: {panel_radius}px;
        }


        QWidget#keyboardCommandsEditor {
            background-color: transparent;
        }

        QWidget#keyboardCommandRowsContainer {
            background-color: transparent;
        }

        QWidget#shortcutConflictOverlay {
            background-color: rgba(255, 255, 255, 220);
        }

        QWidget#shortcutConflictCard {
            background-color: #ffffff;
            border: 1px solid #93b4ff;
            border-radius: {panel_radius}px;
        }

        QLabel#shortcutConflictRelationLabel {
            background-color: transparent;
            border: none;
            color: #334155;
            font-size: 12px;
        }

        QLabel#shortcutConflictShortcutPill,
        QLabel#shortcutConflictCommandPill {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_26}px;
            color: #334155;
            font-size: 12px;
            font-weight: 600;
        }

        QPushButton#shortcutConflictPrimaryButton,
        QPushButton#shortcutConflictSecondaryButton {
            min-height: 24px;
            max-height: 26px;
            padding: 0px 8px;
            border-radius: {control_radius_26}px;
            font-size: 12px;
            font-weight: 600;
        }

        QPushButton#shortcutConflictPrimaryButton {
            background-color: #2f6cff;
            border: 1px solid #2f6cff;
            color: #ffffff;
        }

        QPushButton#shortcutConflictPrimaryButton:hover {
            background-color: #1d4ed8;
            border-color: #1d4ed8;
        }

        QPushButton#shortcutConflictSecondaryButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            color: #334155;
        }

        QPushButton#shortcutConflictSecondaryButton:hover {
            background-color: #eef4ff;
            border-color: #2f6cff;
            color: #1d4ed8;
        }

        QScrollArea#keyboardCommandsScrollArea {
            background-color: transparent;
            border: none;
        }

        QScrollBar#openPulsarScrollBar {
            background-color: #ffffff;
            border: none;
            padding: 0px;
            margin: 0px;
        }

        QScrollArea#keyboardCommandsScrollArea QWidget {
            background-color: transparent;
        }

        QWidget#keyboardCommandRow {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: {row_radius}px;
        }

        QComboBox#keyboardCommandCombo,
        QComboBox#keyboardCommandActionCombo {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_26}px;
            padding-top: 0px;
            padding-bottom: 0px;
            padding-left: 8px;
            padding-right: 4px;
            color: #1f2937;
            min-height: 24px;
            max-height: 26px;
        }

        QComboBox#keyboardCommandCombo::drop-down,
        QComboBox#keyboardCommandActionCombo::drop-down {
            width: 0px;
            border: none;
        }

        QComboBox#keyboardCommandCombo::down-arrow,
        QComboBox#keyboardCommandActionCombo::down-arrow {
            image: none;
            width: 0px;
            height: 0px;
        }

        QComboBox#keyboardCommandCombo QAbstractItemView,
        QComboBox#keyboardCommandCombo QListView {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 4px;
            padding: 2px;
            color: #1f2937;
            selection-background-color: #eef4ff;
            selection-color: #0f63ff;
            outline: 0px;
        }

        QComboBox#keyboardCommandCombo QAbstractItemView::item,
        QComboBox#keyboardCommandCombo QListView::item {
            min-height: 24px;
            padding-left: 6px;
            padding-right: 6px;
            background-color: #ffffff;
            color: #1f2937;
        }

        QComboBox#keyboardCommandCombo QAbstractItemView::item:hover,
        QComboBox#keyboardCommandCombo QAbstractItemView::item:selected,
        QComboBox#keyboardCommandCombo QListView::item:hover,
        QComboBox#keyboardCommandCombo QListView::item:selected {
            background-color: #eef4ff;
            color: #0f63ff;
        }

        QComboBox#keyboardCommandCombo:hover,
        QComboBox#keyboardCommandActionCombo:hover,
        QComboBox#keyboardCommandCombo:focus,
        QComboBox#keyboardCommandActionCombo:focus {
            border: 1px solid #2f6cff;
            background-color: #eef4ff;
            color: #1d4ed8;
            padding-left: 7px;
            padding-right: 3px;
        }

        QPushButton#keyboardShortcutButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {control_radius_26}px;
            padding: 0px;
            color: #334155;
            font-weight: 600;
        }

        QPushButton#keyboardShortcutButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }

        QPushButton#addListButton {
            background-color: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: {pill_radius}px;
            padding: 0px;
            color: #1f2937;
            font-weight: 500;
            font-size: 12px;
        }

        QPushButton#addListButton:hover {
            background-color: #eef4ff;
            border: 1px solid #2f6cff;
            color: #1d4ed8;
        }


        """

DARK_THEME_OVERLAY_QSS = """
            QMainWindow {
                background-color: #0f172a;
            }
            QGroupBox {
                background-color: rgba(15, 23, 42, 235);
                border: 1px solid #334155;
            }
            QLabel, QWidget {
                color: #e5e7eb;
            }
            QLabel#sectionTitle {
                color: #dbeafe;
            }
            QGroupBox::title {
                color: #dbeafe;
            }
            """


def background_stylesheet(background: str) -> str:
    if background == "none":
        return """
                QWidget#centralWidget {
                    background-color: #f4f6fb;
                    background-image: none;
                }
            """
    return """
                QWidget#centralWidget {
                    background-image: url({background_image});
                    background-repeat: no-repeat;
                    background-position: top left;
                }
                """.replace("{background_image}", qss_url("Background_OpenPulsar.svg"))


def light_theme_stylesheet() -> str:
    return (
        LIGHT_THEME_QSS.replace("{panel_radius}", str(PANEL_RADIUS))
        .replace("{pill_radius}", str(OP_PILL_RADIUS))
        .replace("{control_radius_16}", str(OP_CONTROL_RADIUS_XS))
        .replace("{help_button_radius}", str(op_circle_radius(18)))
        .replace("{control_radius_20}", str(op_radius(20)))
        .replace("{control_radius_26}", str(OP_CONTROL_RADIUS_M))
        .replace("{control_radius_28}", str(OP_CONTROL_RADIUS_L))
        .replace("{control_radius_30}", str(OP_CONTROL_RADIUS_XL))
        .replace("{control_radius_32}", str(OP_CONTROL_RADIUS_XXL))
        .replace("{row_radius}", str(op_radius(38)))
        .replace("{panel_border_width}", str(PANEL_BORDER_WIDTH))
        .replace("{background_image}", qss_url("Background_OpenPulsar.svg"))
        .replace("{check_icon}", qss_url("check.svg"))
        .replace("{tree_triangle_closed}", qss_url("tree_triangle_closed.svg"))
        .replace("{tree_triangle_open}", qss_url("tree_triangle_open.svg"))
    )

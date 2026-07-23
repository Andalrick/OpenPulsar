from openpulsar.i18n import tr

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QComboBox,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QCheckBox, QFormLayout,
    QGridLayout, QGroupBox, QSpinBox, QSizePolicy, QStackedWidget,
    QScrollArea, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QKeySequence
from PySide6.QtCore import QTimer

from functools import partial
import sys

from openpulsar.core.dpi import DpiStage
from openpulsar.core.buttons import (
    DisabledAction, MouseAction, MediaAction, DpiAction, KeyboardAction,
    OpenPulsarSpecialAction,
)
from openpulsar.hid import HID_MODS, HID_KEYS

from . import theme
from .widgets.led_widgets import (
    LedIndicator,
    LedSettingsButton,
    LedGainControl,
    LedChoiceControl,
    LedVerticalSlider,
)
from .profile.profile_extras_store import ProfileExtrasStore, apply_profile_extras
from .widgets.common_widgets import (
    ASSETS_DIR,
    LED_PALETTE,
    TAB_ICONS,
    apply_openpulsar_panel_effect,
    asset_path,
    hex_to_color,
    make_section_header,
    picture_path,
    qss_url,
)
from .widgets.dpi_widgets import DpiRemoveButton, DpiStageRow, DpiValueControl
from .widgets.keyboard_widgets import (
    KeyboardCommandRow,
    KeyboardCommandsEditor,
    KeyboardShortcutButton,
    OpenPulsarScrollBar,
    shortcut_to_text,
)
from .widgets.mouse_button_widgets import MouseButtonCombo, MouseButtonEditor
from .widgets.qt_delegates import ActionTreeDelegate, CenteredComboDelegate
from .widgets.sensor_widgets import SensorValueControl
from .widgets.popup_widgets import HelpPopup, AboutPopup, AboutHoverButton
from .widgets.op_panel import OPPanel
from .widgets.help_button import PaintedHelpButton
from .metrics import (
    CONTENT_MARGIN_BOTTOM,
    CONTENT_MARGIN_TOP,
    CONTENT_MARGIN_X,
    DPI_PANEL_WIDTH,
    PANEL_GAP,
    PROFILE_TO_MAIN_GAP,
    MAIN_TO_SENSOR_GAP,
    PROFILE_RIBBON_WIDTH,
    PROFILE_RIBBON_HEIGHT,
    FOOTER_HEIGHT,
    HEADER_HEIGHT,
    LEFT_PANEL_WIDTH,
    PANEL_BODY_HEIGHT,
    PANEL_HEIGHT,
    ROW_HEIGHT,
    ROW_SPACING,
)


def build_main_ui(self):
    central = QWidget()
    central.setObjectName("centralWidget")
    self.setCentralWidget(central)
    self.apply_application_settings()

    root = QVBoxLayout(central)
    root.setSpacing(PANEL_GAP)

    root.addSpacing(-15)

    # Le branding est maintenant intégré au wallpaper.
    # On garde simplement un espace transparent en haut
    # pour ne pas recouvrir le logo du fond.
    header_spacer = QWidget()
    header_spacer.setObjectName("headerSpacer")
    header_spacer.setFixedHeight(54)
    root.addWidget(header_spacer)

    left_layout = QVBoxLayout()

    # Continuous profile ribbon.  The container is deliberately transparent:
    # each segment draws its own background and border, just like the main
    # tab strip.  Its width matches the two panels below, including their gap.
    profiles_ribbon = QWidget()
    profiles_ribbon.setObjectName("profilesRibbon")
    profiles_ribbon.setFixedWidth(PROFILE_RIBBON_WIDTH)
    # Exact same shadow recipe as the application panels.
    apply_openpulsar_panel_effect(profiles_ribbon)
    profiles_layout = QVBoxLayout(profiles_ribbon)
    profiles_layout.setContentsMargins(0, 0, 0, 0)
    profiles_layout.setSpacing(0)

    self.import_profile_button = QPushButton()
    self.import_profile_button.setIcon(
        QIcon(picture_path("openpulsar_import.svg"))
    )
    profile_icon_size = theme.op_icon_size(PROFILE_RIBBON_HEIGHT)
    self.import_profile_button.setIconSize(QSize(profile_icon_size, profile_icon_size))

    self.prev_profile_button = QPushButton("←")
    self.next_profile_button = QPushButton("→")

    self.export_profile_button = QPushButton()
    self.export_profile_button.setIcon(
        QIcon(picture_path("openpulsar_export.svg"))
    )
    self.export_profile_button.setIconSize(QSize(profile_icon_size, profile_icon_size))


    self.import_profile_button.clicked.connect(self.import_current_profile)
    self.export_profile_button.clicked.connect(self.export_current_profile)
    self.prev_profile_button.clicked.connect(self.previous_slot)
    self.next_profile_button.clicked.connect(self.next_slot)

    self.profile_labels = []

    profiles_row = QHBoxLayout()
    profiles_row.setSpacing(0)
    profiles_row.setContentsMargins(0, 0, 0, 0)
    # La barre profil doit remplir le cadre : pas de centrage flottant.

    # Contrôle segmenté plein cadre : chaque segment s’étire
    # pour occuper toute la largeur disponible du cadre profils.
    for button in (
        self.import_profile_button,
        self.prev_profile_button,
        self.next_profile_button,
        self.export_profile_button,
    ):
        button.setFixedHeight(PROFILE_RIBBON_HEIGHT)
        button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

    profiles_row.addWidget(self.import_profile_button, 1)
    profiles_row.addWidget(self.prev_profile_button, 1)

    for slot in range(1, self.mouse.capabilities.num_profiles + 1):
        label = QPushButton(f"P{slot}")
        label.setFixedHeight(PROFILE_RIBBON_HEIGHT)
        label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        label.clicked.connect(
            lambda checked=False, slot=slot: self.activate_profile(slot)
        )

        self.profile_labels.append(label)
        profiles_row.addWidget(label, 1)

    profiles_row.addWidget(self.next_profile_button, 1)
    profiles_row.addWidget(self.export_profile_button, 1)

    profiles_layout.addLayout(profiles_row)

    # The vertical breathing room is deliberately redistributed: the main
    # panels sit farther below the profile ribbon and closer to the sensor
    # panel, while preserving the same total stack height.
    right_layout = QVBoxLayout()
    right_layout.setContentsMargins(0, 0, 0, 0)
    right_layout.setSpacing(0)
    right_layout.addSpacing(2)
    right_layout.addWidget(profiles_ribbon, alignment=Qt.AlignLeft)
    right_layout.addSpacing(PROFILE_TO_MAIN_GAP - 2)

    sensor_box = QGroupBox("")
    sensor_box.setObjectName("sensorBox")
    apply_openpulsar_panel_effect(sensor_box)

    sensor_layout = QVBoxLayout()
    sensor_layout.setSpacing(8)
    sensor_layout.setContentsMargins(6, 0, 10, 10)

    sensor_layout.addWidget(
        make_section_header(
            picture_path("icon_chip.svg"),
            tr("Sensor"),
        )
    )

    sensor_content_layout = QHBoxLayout()
    sensor_content_layout.setSpacing(8)

    performance_box = QGroupBox(tr("Performance"))
    performance_box.setObjectName("subPanelBox")
    apply_openpulsar_panel_effect(performance_box, blur=22, offset_y=3, alpha=78)
    performance_layout = QFormLayout()
    performance_layout.setContentsMargins(8, 8, 8, 8)
    performance_layout.setHorizontalSpacing(8)
    performance_layout.setVerticalSpacing(8)
    performance_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
    performance_layout.setFormAlignment(Qt.AlignTop)

    tracking_box = QGroupBox(tr("Tracking"))
    tracking_box.setObjectName("subPanelBox")
    apply_openpulsar_panel_effect(tracking_box, blur=22, offset_y=3, alpha=78)
    tracking_layout = QFormLayout()
    tracking_layout.setContentsMargins(8, 8, 8, 8)
    tracking_layout.setHorizontalSpacing(8)
    tracking_layout.setVerticalSpacing(8)
    tracking_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
    tracking_layout.setFormAlignment(Qt.AlignTop)

    # Le panneau DPI et le panneau souris utilisent le même composant OPPanel.
    # Le header et le corps ont ainsi une géométrie commune et centralisée.
    dpi_header = make_section_header(
        picture_path("icon_target.svg"),
        "DPI",
    )
    dpi_header.setObjectName("opPanelHeader")
    self.dpi_header_title = None
    self.dpi_header_icon = None
    for label in dpi_header.findChildren(QLabel):
        if label.objectName() == "sectionTitle":
            self.dpi_header_title = label
        elif label.objectName() == "sectionIcon":
            self.dpi_header_icon = label

    dpi_header_layout = dpi_header.layout()
    # Optical inset specific to the narrow DPI panel: keep the target icon
    # and the LED control away from the rounded corners while preserving
    # their shared vertical alignment with the title.
    dpi_header_layout.setContentsMargins(3, 1, 3, 0)

    self.led_settings_button = LedSettingsButton()
    self.led_settings_button.clicked.connect(self.toggle_led_panel)

    dpi_help_button = PaintedHelpButton()
    dpi_help_button.setObjectName("helpButton")
    self.dpi_help_button = dpi_help_button
    self.context_help_buttons.append(dpi_help_button)
    dpi_help_button.clicked.connect(
        lambda checked=False, button=dpi_help_button: self.show_dpi_or_led_help(button)
    )

    dpi_header_layout.insertWidget(
        dpi_header_layout.count() - 1,
        dpi_help_button,
        alignment=Qt.AlignBottom,
    )
    dpi_header_layout.addWidget(self.led_settings_button, alignment=Qt.AlignVCenter)

    dpi_body = QWidget()
    dpi_body.setObjectName("opPanelBody")

    dpi_body_layout = QVBoxLayout(dpi_body)
    dpi_body_layout.setSpacing(ROW_SPACING)
    dpi_body_layout.setContentsMargins(
        CONTENT_MARGIN_X,
        CONTENT_MARGIN_TOP,
        CONTENT_MARGIN_X,
        CONTENT_MARGIN_BOTTOM,
    )

    # Les 6 emplacements DPI existent toujours.
    # Si seuls 3 stages sont actifs, les 3 autres lignes restent vides.
    # Résultat : rien ne grandit, rien ne rétrécit.
    self.dpi_stage_rows = []

    # Header à onglets du panneau souris. Le corps sera injecté dans OPPanel
    # une fois le QStackedWidget construit.
    self.buttons_tab_button = QPushButton(tr("Buttons"))
    self.logic_tab_button = QPushButton(tr("Keyboard commands"))

    for tab_button in (
        self.buttons_tab_button,
        self.logic_tab_button,
    ):
        tab_button.setObjectName("mainTabButton")
        tab_button.setFixedHeight(HEADER_HEIGHT)
        tab_button.setIconSize(QSize(16, 16))
        tab_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        tab_button.setFocusPolicy(Qt.NoFocus)
        tab_button.setCursor(Qt.PointingHandCursor)

    self.buttons_tab_button.clicked.connect(
        lambda checked=False: self.select_main_tab(0)
    )
    self.logic_tab_button.clicked.connect(
        lambda checked=False: self.select_main_tab(1)
    )

    tab_bar = QWidget()
    tab_bar.setObjectName("mainTabBar")
    tab_bar.setFixedSize(LEFT_PANEL_WIDTH, HEADER_HEIGHT)

    tab_bar_layout = QHBoxLayout(tab_bar)
    tab_bar_layout.setContentsMargins(0, 0, 0, 0)
    tab_bar_layout.setSpacing(0)
    tab_bar_layout.addWidget(self.buttons_tab_button, 1)
    tab_bar_layout.addWidget(self.logic_tab_button, 1)


    self.polling_control = SensorValueControl(
        self.mouse.get_supported_polling_rates(),
        suffix="Hz",
        previous_symbol="◀",
        next_symbol="▶",
    )

    self.debounce_control = SensorValueControl(
        range(16),
        suffix="ms",
        previous_symbol="−",
        next_symbol="+",
    )

    self.lod_control = SensorValueControl(
        self.mouse.get_supported_lod_values(),
        suffix="mm",
        previous_symbol="▼",
        next_symbol="▲",
    )

    self.motion_sync_check = QCheckBox()
    self.angle_snap_check = QCheckBox()
    self.ripple_control_check = QCheckBox()

    for checkbox in (
        self.motion_sync_check,
        self.angle_snap_check,
        self.ripple_control_check,
    ):
        checkbox.setFixedHeight(26)

    self.left_button_combo = MouseButtonCombo()
    self.right_button_combo = MouseButtonCombo()
    self.middle_button_combo = MouseButtonCombo()
    self.back_button_combo = MouseButtonCombo()
    self.forward_button_combo = MouseButtonCombo()
    self.dpi_button_combo = MouseButtonCombo()

    button_action_groups = [
        (tr("Buttons"), [
            tr("Left Click"),
            tr("Right Click"),
            tr("Middle Click"),
            tr("Back"),
            tr("Forward"),
        ]),
        (tr("DPI & Profiles"), [
            tr("DPI Cycle"),
            tr("DPI Up"),
            tr("DPI Down"),
            tr("Profile Next"),
            tr("Profile Previous"),
        ]),
        (tr("Multimedia"), [
            tr("Play Pause"),
            tr("Next Track"),
            tr("Previous Track"),
            tr("Mute"),
            tr("Volume Up"),
            tr("Volume Down"),
        ]),
        (tr("Shortcuts"), [
            tr("Copy"),
            tr("Paste"),
            tr("Cut"),
            tr("Undo"),
            tr("Redo"),
        ]),
    ]

    dpi_button_choices = [
        tr("DPI Cycle"),
        tr("Profile Next"),
        tr("Profile Previous"),
        tr("Disabled"),
    ]

    for combo in (
        self.left_button_combo,
        self.right_button_combo,
        self.middle_button_combo,
        self.back_button_combo,
        self.forward_button_combo,
    ):
        combo.set_keep_one_group_open(True)
        combo.set_action_groups(
            button_action_groups,
            standalone_actions=[(tr("Disabled"), tr("Disabled"), True)],
        )

        combo.protectedClicked.connect(self.show_left_click_lock_popup)

    self.dpi_button_combo.addItems(dpi_button_choices)
    disabled_index = self.dpi_button_combo.findText(tr("Disabled"))
    self.dpi_button_combo.setItemData(
        disabled_index,
        QColor("#dc2626"),
        Qt.ForegroundRole,
    )

    self.dpi_boxes = []
    self.dpi_led_buttons = []
    self.dpi_minus_buttons = []
    self.dpi_plus_buttons = []
    self.dpi_remove_buttons = []
    self.led_gain_controls = []

    self.dpi_content_stack = QStackedWidget()
    self.dpi_content_stack.setObjectName("dpiContentStack")
    self.dpi_content_stack.setFixedWidth(DPI_PANEL_WIDTH - (2 * CONTENT_MARGIN_X))

    self.dpi_page = QWidget()
    self.dpi_page.setObjectName("dpiPage")
    dpi_page_layout = QVBoxLayout(self.dpi_page)
    dpi_page_layout.setContentsMargins(0, 0, 0, 0)
    dpi_page_layout.setSpacing(ROW_SPACING)

    for i in range(
        self.mouse.capabilities.max_dpi_stages
    ):

        led_button = LedIndicator()
        led_button.clicked.connect(
            lambda checked=False, stage=i + 1, button=led_button: self.handle_dpi_led_click(
                stage,
                button,
            )
        )
        self.dpi_led_buttons.append(led_button)

        dpi_box = DpiValueControl()
        dpi_box.setRange(
            self.mouse.capabilities.dpi_min,
            self.mouse.capabilities.dpi_max,
        )
        dpi_box.setSingleStep(
            self.mouse.capabilities.dpi_step,
        )
        dpi_box.minus_button.clicked.connect(
            lambda checked=False, stage=i + 1: self.change_dpi_stage(stage, -1)
        )
        dpi_box.plus_button.clicked.connect(
            lambda checked=False, stage=i + 1: self.change_dpi_stage(stage, 1)
        )
        self.dpi_boxes.append(dpi_box)
        self.dpi_minus_buttons.append(dpi_box.minus_button)
        self.dpi_plus_buttons.append(dpi_box.plus_button)

        remove_button = DpiRemoveButton()
        remove_button.clicked.connect(
            lambda checked=False, stage=i + 1: self.remove_dpi_stage(stage)
        )
        self.dpi_remove_buttons.append(remove_button)

        row_widget = DpiStageRow()
        row_widget.setFixedSize(160, ROW_HEIGHT)
        row_widget.clicked.connect(
            lambda stage=i + 1: self.set_active_dpi_stage(stage)
        )

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(4, 6, 4, 6)
        row_layout.setSpacing(8)
        row_layout.setAlignment(Qt.AlignVCenter)
        row_layout.addWidget(led_button, alignment=Qt.AlignVCenter)
        row_layout.addWidget(dpi_box, alignment=Qt.AlignVCenter)
        row_layout.addWidget(remove_button, alignment=Qt.AlignVCenter)

        self.dpi_stage_rows.append(row_widget)
        dpi_page_layout.addWidget(row_widget, alignment=Qt.AlignHCenter)

    self.add_dpi_button = QPushButton(tr("+ Add stage"))
    self.add_dpi_button.setObjectName("addListButton")
    self.add_dpi_button.setFixedSize(150, theme.OP_PILL_HEIGHT)
    self.add_dpi_button.clicked.connect(self.add_dpi_stage)

    dpi_footer = QWidget()
    dpi_footer.setObjectName("dpiFooterRow")
    dpi_footer.setFixedSize(160, FOOTER_HEIGHT)
    dpi_footer_layout = QHBoxLayout(dpi_footer)
    dpi_footer_layout.setContentsMargins(4, 4, 4, 4)
    dpi_footer_layout.setSpacing(8)
    dpi_footer_layout.setAlignment(Qt.AlignVCenter)
    dpi_footer_layout.addWidget(self.add_dpi_button, alignment=Qt.AlignVCenter)

    dpi_page_layout.addStretch()
    dpi_page_layout.addWidget(dpi_footer, alignment=Qt.AlignHCenter)

    self.led_panel = self.build_led_panel()
    self.dpi_content_stack.addWidget(self.dpi_page)
    self.dpi_content_stack.addWidget(self.led_panel)
    self.dpi_content_stack.setCurrentWidget(self.dpi_page)
    dpi_body_layout.addWidget(self.dpi_content_stack, alignment=Qt.AlignHCenter)

    dpi_group = OPPanel(
        DPI_PANEL_WIDTH,
        header=dpi_header,
        body=dpi_body,
    )
    self.dpi_group = dpi_group

    sensor_rows = (
        (performance_layout, "Polling", "polling", self.polling_control),
        (performance_layout, "Debounce", "debounce", self.debounce_control),
        (performance_layout, "LOD", "lod", self.lod_control),
        (tracking_layout, "Motion Sync", "motion_sync", self.motion_sync_check),
        (tracking_layout, "Angle Snap", "angle_snap", self.angle_snap_check),
        (tracking_layout, "Ripple Control", "ripple_control", self.ripple_control_check),
    )
    for form_layout, text, help_key, control in sensor_rows:
        form_layout.addRow(self.make_help_label(text, help_key), control)
        form_layout.setAlignment(control, Qt.AlignLeft | Qt.AlignVCenter)

    performance_box.setLayout(performance_layout)
    tracking_box.setLayout(tracking_layout)

    sensor_content_layout.addWidget(performance_box)
    sensor_content_layout.addWidget(tracking_box)

    sensor_layout.addLayout(sensor_content_layout)

    sensor_box.setLayout(sensor_layout)

    self.mouse_button_editor = MouseButtonEditor(
        self.left_button_combo,
        self.right_button_combo,
        self.middle_button_combo,
        self.back_button_combo,
        self.forward_button_combo,
        self.dpi_button_combo,
    )
    get_device_image = getattr(self.mouse, "get_device_image", None)
    device_image = get_device_image() if callable(get_device_image) else getattr(
        getattr(self.mouse, "capabilities", None), "image", None
    )
    if device_image:
        self.mouse_button_editor.set_device_image(picture_path(device_image))

    buttons_page = QWidget()
    buttons_page_layout = QVBoxLayout(buttons_page)
    buttons_page_layout.setContentsMargins(0, 0, 0, 0)
    buttons_page_layout.setSpacing(0)
    buttons_page_layout.addWidget(
        self.mouse_button_editor,
        alignment=Qt.AlignCenter,
    )

    logic_page = QWidget()
    logic_page.setFixedSize(LEFT_PANEL_WIDTH, PANEL_BODY_HEIGHT)

    logic_page_layout = QVBoxLayout(logic_page)
    logic_page_layout.setContentsMargins(0, 0, 0, 0)
    logic_page_layout.setSpacing(0)

    self.keyboard_commands_editor = KeyboardCommandsEditor(
        dpi_stage_count_provider=self.enabled_dpi_stage_count,
        dpi_min=self.mouse.capabilities.dpi_min,
        dpi_max=self.mouse.capabilities.dpi_max,
        dpi_step=self.mouse.capabilities.dpi_step,
    )
    self.keyboard_commands_editor.dpiValueChangeRequested.connect(self.change_active_dpi_value)
    self.keyboard_commands_editor.dpiValueSetRequested.connect(self.set_active_dpi_value)
    self.keyboard_commands_editor.dpiStageModeRequested.connect(self.change_active_dpi_stage_by_mode)
    self.keyboard_commands_editor.dpiStageDirectRequested.connect(self.set_active_dpi_stage)
    self.keyboard_commands_editor.profileModeRequested.connect(self.change_profile_by_mode)
    self.keyboard_commands_editor.profileDirectRequested.connect(self.activate_profile)
    self.keyboard_commands_editor.commandsChanged.connect(self.on_keyboard_commands_changed)
    self.keyboard_commands_editor.persistentModeEnableRequested.connect(
        self.enable_persistent_for_keyboard_commands
    )
    self.keyboard_commands_editor.persistentModeCancelled.connect(
        lambda: self.select_main_tab(0)
    )
    self.start_global_shortcuts()
    logic_page_layout.addWidget(
        self.keyboard_commands_editor,
        alignment=Qt.AlignCenter,
    )

    self.main_stack = QStackedWidget()
    self.main_stack.setObjectName("mainStack")
    self.main_stack.setFixedSize(LEFT_PANEL_WIDTH, PANEL_BODY_HEIGHT)
    self.main_stack.addWidget(buttons_page)
    self.main_stack.addWidget(logic_page)

    buttons_box = OPPanel(
        LEFT_PANEL_WIDTH,
        header=tab_bar,
        body=self.main_stack,
    )
    buttons_box.setObjectName("buttonsPanel")

    self.select_main_tab(1 if "--keyboard-commands" in sys.argv[1:] else 0)

    middle_layout = QHBoxLayout()
    middle_layout.setSpacing(PANEL_GAP)
    middle_layout.addWidget(buttons_box)
    middle_layout.addWidget(dpi_group)

    right_layout.addLayout(middle_layout)
    right_layout.addSpacing(MAIN_TO_SENSOR_GAP)
    right_layout.addWidget(sensor_box)

    root.addLayout(right_layout)

    # Widgets inserted later in the stack can otherwise paint over the expanded
    # bounding rectangle of the ribbon shadow. Raising it after layout ensures
    # the shadow remains visible, just like those of the larger panels.
    QTimer.singleShot(0, profiles_ribbon.raise_)

    footer = QWidget()

    footer_layout = QHBoxLayout(footer)
    footer_layout.setContentsMargins(0, 0, 0, 0)

    self.status_indicator = QLabel("●")
    self.status_indicator.setObjectName("usbStatusIndicator")
    self.status_indicator.setFixedSize(14, 14)
    self.status_indicator.setAlignment(Qt.AlignCenter)

    self.log_button = QPushButton()
    self.log_button.setObjectName("logExportButton")
    self.log_button.setIcon(QIcon(picture_path("log-icon.svg")))
    self.log_button.setIconSize(QSize(15, 15))
    self.log_button.setFixedSize(20, 20)
    self.log_button.setCursor(Qt.PointingHandCursor)
    self.log_button.setFocusPolicy(Qt.NoFocus)
    self.log_button.setToolTip(tr("diagnostic.export.tooltip"))
    self.log_button.clicked.connect(self.export_diagnostic_log)

    self.status_label = QLabel("")
    self.status_label.setAlignment(Qt.AlignCenter)

    self.connection_icon = QLabel()
    self.connection_icon.setObjectName("connectionTypeIcon")
    self.connection_icon.setFixedSize(18, 18)
    self.connection_icon.setAlignment(Qt.AlignCenter)

    status_row = QHBoxLayout()
    status_row.setContentsMargins(0, 0, 0, 0)
    status_row.setSpacing(6)
    status_row.setAlignment(Qt.AlignCenter)
    status_row.addWidget(self.log_button)
    status_row.addWidget(self.status_label)
    status_row.addWidget(self.status_indicator)
    status_row.addWidget(self.connection_icon)

    footer_layout.addStretch()
    footer_layout.addLayout(status_row)
    footer_layout.addStretch()

    root.addWidget(footer)

    self.about_hover_zone = AboutHoverButton(self.centralWidget())
    self.about_hover_zone.setGeometry(10, 11, 32, 32)
    self.about_hover_zone.clicked.connect(self.show_about_popup)
    self.about_hover_zone.raise_()

    self.settings_button = QPushButton(self.centralWidget())
    self.settings_button.setObjectName("settingsButton")
    self.settings_button.setGeometry(490, 13, 32, 32)
    self.settings_button.setIcon(QIcon(picture_path("icon_settings.svg")))
    self.settings_button.setIconSize(QSize(32, 32))
    self.settings_button.setCursor(Qt.PointingHandCursor)
    self.settings_button.setFocusPolicy(Qt.NoFocus)
    self.settings_button.clicked.connect(self.show_settings_dialog)
    self.settings_button.raise_()

    self.tray_icon = None
    if self.persistent_mode:
        self.create_tray_icon()

    self.update_device_status()

    self.usb_monitor_timer = QTimer(self)
    self.usb_monitor_timer.timeout.connect(self.check_usb_connection)
    self.usb_monitor_timer.start(1000)

    self.update_slot_labels()
    self.load_hardware_active_profile()
    self.apply_led_output_settings_to_mouse()
    self.connect_auto_apply()

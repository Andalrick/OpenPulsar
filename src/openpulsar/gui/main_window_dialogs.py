from openpulsar.i18n import tr
from .settings_dialog import SettingsDialog, SettingsStore
from .profile.profile_extras_store import ProfileExtrasStore
from .widgets.popup_widgets import HelpPopup, AboutPopup
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)


class DialogMixin:
    def make_help_label(self, text, key):
        widget = QWidget()
        widget.setObjectName("helpLabel")

        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label = QLabel(text)

        button = QPushButton("?")
        button.setObjectName("helpButton")
        button.setFixedSize(18, 18)
        button.setCursor(Qt.PointingHandCursor)
        self.context_help_buttons.append(button)

        button.clicked.connect(
            lambda checked=False, key=key, anchor=button: self.show_help_popup(
                key,
                anchor,
            )
        )

        layout.addWidget(label)
        layout.addWidget(button)
        layout.addStretch()
        self.update_context_help_visibility()

        return widget


    def update_context_help_visibility(self):
        visible = bool(self.app_settings.get("show_context_help", True))
        for button in getattr(self, "context_help_buttons", []):
            if button is None:
                continue
            button.setText("?" if visible else "")
            button.setEnabled(visible)
            button.setCursor(Qt.PointingHandCursor if visible else Qt.ArrowCursor)
            button.setProperty("contextHelpVisible", visible)
            button.style().unpolish(button)
            button.style().polish(button)
            button.update()

    def ask_enable_persistent_for_keyboard_commands(self):
        box = QMessageBox(self)
        box.setWindowTitle(tr("keyboard.persistent_required.title"))
        box.setText(tr("keyboard.persistent_required.body"))
        enable_button = box.addButton(
            tr("keyboard.persistent_required.enable"),
            QMessageBox.AcceptRole,
        )
        box.addButton(
            tr("keyboard.persistent_required.cancel"),
            QMessageBox.RejectRole,
        )
        box.exec()

        if box.clickedButton() is not enable_button:
            return

        settings = SettingsStore.load()
        settings["persistent_mode"] = True
        SettingsStore.save(settings)
        self.app_settings = dict(settings)
        self.persistent_mode = True
        self.restart_openpulsar(["--keyboard-commands"])

    def on_keyboard_commands_changed(self, commands):
        if self._loading_profile:
            return

        commands = [command for command in list(commands or []) if isinstance(command, dict)]

        if self.current_profile is None:
            ProfileExtrasStore.save_keyboard_commands(self.current_slot, commands)
            return

        self.current_profile.keyboard_commands = commands

        # Keyboard commands are profile-local OpenPulsar extras. Save them via
        # both the narrow helper and the full extras snapshot.  The narrow helper
        # preserves them even if another profile refresh happens immediately; the
        # full snapshot keeps the historical storage path in sync.
        ProfileExtrasStore.save_keyboard_commands(self.current_slot, commands)
        ProfileExtrasStore.save_slot(self.current_slot, self.current_profile)

    def show_dpi_or_led_help(self, anchor):
        if (
            hasattr(self, "dpi_content_stack")
            and hasattr(self, "led_panel")
            and self.dpi_content_stack.currentWidget() is self.led_panel
        ):
            self.show_help_popup("led_correction", anchor)
            return

        self.show_help_popup("dpi", anchor)

    def show_help_popup(self, key, anchor):
        if not bool(self.app_settings.get("show_context_help", True)):
            return

        help_texts = {
            "polling": (tr("help.polling.title"), tr("help.polling.body")),
            "debounce": (tr("help.debounce.title"), tr("help.debounce.body")),
            "lod": (tr("help.lod.title"), tr("help.lod.body")),
            "motion_sync": (tr("help.motion_sync.title"), tr("help.motion_sync.body")),
            "angle_snap": (tr("help.angle_snap.title"), tr("help.angle_snap.body")),
            "ripple_control": (tr("help.ripple_control.title"), tr("help.ripple_control.body")),
            "dpi": (tr("help.dpi.title"), tr("help.dpi.body")),
            "led_correction": (tr("help.led_correction.title"), tr("help.led_correction.body")),
            "left_click_lock": (tr("help.left_click_lock.title"), tr("help.left_click_lock.body")),
        }

        if key not in help_texts:
            return

        if self.help_popup is not None:
            self.help_popup.close()
            self.help_popup = None

        if self.about_popup is not None:
            self.about_popup.close()
            self.about_popup = None

        title, body = help_texts[key]
        popup = HelpPopup(title, body, self.centralWidget())

        margin = 8
        parent = self.centralWidget()
        parent_rect = parent.rect()

        anchor_pos = anchor.mapTo(parent, anchor.rect().bottomRight())

        x = anchor_pos.x() + 8
        y = anchor_pos.y() - 4

        if x + popup.width() + margin > parent_rect.width():
            x = anchor.mapTo(parent, anchor.rect().topLeft()).x() - popup.width() - 8

        if y + popup.height() + margin > parent_rect.height():
            y = parent_rect.height() - popup.height() - margin

        x = max(margin, min(x, parent_rect.width() - popup.width() - margin))
        y = max(margin, min(y, parent_rect.height() - popup.height() - margin))

        popup.move(x, y)
        popup.show()
        popup.raise_()

        self.help_popup = popup


    def show_left_click_lock_popup(self, anchor):
        self.show_help_popup("left_click_lock", anchor)

    def show_about_popup(self):
        if self.help_popup is not None:
            self.help_popup.close()
            self.help_popup = None

        if self.about_popup is not None:
            self.about_popup.close()
            return

        self.about_popup = AboutPopup(self.centralWidget())
        self.about_popup.closed.connect(self.on_about_popup_closed)
        self.about_popup.move(6, 51)
        self.about_popup.show()
        self.about_popup.raise_()
        self.about_hover_zone.set_open(True)

    def on_about_popup_closed(self):
        self.about_popup = None
        self.about_hover_zone.set_open(False)

    def show_first_run_about(self):
        if self.start_in_tray or self.app_settings.get("about_welcome_seen", False):
            return

        self.show_about_popup()
        self.app_settings["about_welcome_seen"] = True

        try:
            SettingsStore.save(self.app_settings)
        except OSError:
            # A read-only configuration directory should not prevent startup.
            pass

    def show_settings_dialog(self):
        if self.help_popup is not None:
            self.help_popup.close()
            self.help_popup = None

        if self.about_popup is not None:
            self.about_popup.close()
            self.about_popup = None

        if self.settings_overlay is not None:
            self.settings_overlay.close()
            self.settings_overlay = None
            self.set_settings_button_open(False)
            return

        self.settings_overlay = SettingsDialog(self.centralWidget())
        self.settings_overlay.settingsChanged.connect(self.on_settings_changed)
        self.settings_overlay.destroyed.connect(
            lambda *_: (setattr(self, "settings_overlay", None), self.set_settings_button_open(False))
        )

        self.position_settings_popover()
        self.settings_overlay.show()
        self.settings_overlay.raise_()
        self.settings_button.raise_()
        self.set_settings_button_open(True)

    def set_settings_button_open(self, open_):
        if not hasattr(self, "settings_button"):
            return
        self.settings_button.setProperty("settingsOpen", bool(open_))
        self.settings_button.style().unpolish(self.settings_button)
        self.settings_button.style().polish(self.settings_button)
        self.settings_button.update()

    def position_settings_popover(self):
        if self.settings_overlay is None:
            return

        parent = self.centralWidget()
        if parent is None:
            return

        width = getattr(getattr(self, "dpi_group", None), "width", lambda: 180)()
        self.settings_overlay.setFixedWidth(width)

        if hasattr(self, "dpi_group"):
            x = self.dpi_group.mapTo(parent, self.dpi_group.rect().topLeft()).x()
        else:
            x = max(0, parent.width() - width - 16)

        y = self.settings_button.y() + self.settings_button.height() + 8
        x = max(0, min(x, parent.width() - self.settings_overlay.width()))
        y = max(0, min(y, parent.height() - self.settings_overlay.height()))
        self.settings_overlay.move(x, y)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.update_tray_visibility_action()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_tray_visibility_action()












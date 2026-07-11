import sys
from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from openpulsar.i18n import tr
from openpulsar.logging_utils import get_logger
from .errors import HARDWARE_STATE_ERRORS
from .widgets.common_widgets import picture_path

logger = get_logger(__name__)


class TrayMixin:
    """System tray and persistent-mode behavior for MainWindow."""

    def create_tray_icon(self):
        """Create the tray icon used by OpenPulsar persistent mode."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = None
            return

        tray_icon = QSystemTrayIcon(self)
        tray_icon.setIcon(
            QIcon(picture_path("openpulsar_tray.svg"))
        )

        tray_menu = QMenu(self)
        self.tray_menu = tray_menu

        self.tray_visibility_action = QAction(self)
        self.tray_visibility_action.triggered.connect(self.toggle_window_from_tray)

        self.tray_profile_menu = QMenu("Profil", tray_menu)
        self.tray_dpi_menu = QMenu("Palier DPI", tray_menu)

        quit_action = QAction(tr("tray.quit"), self)
        quit_action.triggered.connect(self.quit_from_tray)

        tray_menu.addAction(self.tray_visibility_action)
        tray_menu.addSeparator()
        tray_menu.addMenu(self.tray_profile_menu)
        tray_menu.addMenu(self.tray_dpi_menu)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        tray_icon.setContextMenu(tray_menu)
        tray_icon.activated.connect(self.on_tray_activated)
        tray_icon.show()

        self.tray_icon = tray_icon
        self.update_tray_visibility_action()



    def cleanup_resources(self):
        """Stop background work before Qt destroys the application.

        This method is intentionally idempotent because it can be reached from
        the tray Quit action, the window close event, a restart request, or
        QApplication.aboutToQuit.
        """
        if self._shutting_down:
            return

        self._shutting_down = True

        if self.help_popup is not None:
            self.help_popup.close()
            self.help_popup = None

        if self.about_popup is not None:
            self.about_popup.close()
            self.about_popup = None

        if self.settings_overlay is not None:
            self.settings_overlay.close()
            self.settings_overlay = None

        if hasattr(self, "persist_keyboard_commands_for_current_slot"):
            try:
                self.persist_keyboard_commands_for_current_slot()
            except HARDWARE_STATE_ERRORS:
                logger.debug("Failed to persist keyboard commands during cleanup", exc_info=True)

        if self.global_shortcut_manager is not None:
            self.global_shortcut_manager.stop()
            self.global_shortcut_manager = None

        if hasattr(self, "auto_apply_timer"):
            self.auto_apply_timer.stop()

        if hasattr(self, "usb_monitor_timer"):
            self.usb_monitor_timer.stop()

        self._pending_apply = False
        self._pending_sections.clear()

        self.stop_hidraw_listener()

        try:
            self.mouse.close()
        except HARDWARE_STATE_ERRORS as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)

        tray_icon = getattr(self, "tray_icon", None)
        if tray_icon is not None:
            tray_icon.hide()


    def quit_from_tray(self):
        self._force_quit = True
        self.cleanup_resources()
        app = QApplication.instance()
        if app is not None:
            app.quit()


    def restart_openpulsar(self, extra_args=None):
        executable = Path(sys.argv[0]).resolve()
        args = [str(executable)]
        if extra_args:
            args.extend(str(arg) for arg in extra_args)
        self._force_quit = True
        self.cleanup_resources()
        QProcess.startDetached(sys.executable, args)
        app = QApplication.instance()
        if app is not None:
            app.quit()


    def ask_restart_for_persistent_mode(self, enabled):
        title = tr("settings.persistent.restart.title")
        body = tr(
            "settings.persistent.restart.enabled.body"
            if enabled
            else "settings.persistent.restart.disabled.body"
        )

        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(body)
        restart_button = box.addButton(
            tr("settings.persistent.restart.now"),
            QMessageBox.AcceptRole,
        )
        box.addButton(
            tr("settings.persistent.restart.later"),
            QMessageBox.RejectRole,
        )
        box.exec()

        if box.clickedButton() is restart_button:
            self.restart_openpulsar()


    def on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            self.toggle_window_from_tray()


    def toggle_window_from_tray(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_from_tray()
        self.update_tray_visibility_action()


    def show_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()
        self.update_tray_visibility_action()


    def update_tray_visibility_action(self):
        action = getattr(self, "tray_visibility_action", None)
        if action is None:
            return
        action.setText(tr("tray.hide") if self.isVisible() else tr("tray.show"))
        self.update_tray_quick_actions()


    def update_tray_quick_actions(self):
        """Synchronize the tray quick-action submenus.

        The tray intentionally stays minimal: profile and DPI stage only.
        The main window remains the place for fine-grained configuration.
        """
        profile_menu = getattr(self, "tray_profile_menu", None)
        dpi_menu = getattr(self, "tray_dpi_menu", None)

        if profile_menu is None or dpi_menu is None:
            return

        profile_menu.clear()
        dpi_menu.clear()

        device_ready = bool(self._usb_connected and self.current_profile is not None)
        profile_menu.setEnabled(device_ready)
        dpi_menu.setEnabled(device_ready)

        if not device_ready:
            return

        profile_menu.setTitle(f"Profil (P{self.current_slot})")
        active_stage = max(1, min(getattr(self, "active_dpi_stage", 1), len(self.current_profile.dpi_stages)))
        dpi_menu.setTitle(f"Palier DPI ({active_stage})")

        profile_group = QActionGroup(profile_menu)
        profile_group.setExclusive(True)
        self.tray_profile_action_group = profile_group

        profile_count = getattr(self.mouse.capabilities, "num_profiles", 5)
        for slot in range(1, profile_count + 1):
            action = QAction(f"P{slot}", profile_menu)
            action.setCheckable(True)
            action.setChecked(slot == self.current_slot)
            action.triggered.connect(
                lambda checked=False, slot=slot: self.activate_profile(slot)
            )
            profile_group.addAction(action)
            profile_menu.addAction(action)

        dpi_group = QActionGroup(dpi_menu)
        dpi_group.setExclusive(True)
        self.tray_dpi_action_group = dpi_group

        stage_count = len(self.current_profile.dpi_stages)

        for stage in range(1, stage_count + 1):
            action = QAction(f"Palier {stage}", dpi_menu)
            action.setCheckable(True)
            action.setChecked(stage == active_stage)
            action.triggered.connect(
                lambda checked=False, stage=stage: self.set_active_dpi_stage(stage)
            )
            dpi_group.addAction(action)
            dpi_menu.addAction(action)


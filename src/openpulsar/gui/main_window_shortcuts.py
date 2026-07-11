from openpulsar.logging_utils import get_logger

logger = get_logger(__name__)

from openpulsar.core.global_shortcuts import GlobalShortcutManager


def start_global_shortcuts(self):
    """Start global shortcut listening when available.

    On Wayland, Qt only receives key events while the application has
    focus. The global listener uses Linux input devices when the current
    user is allowed to read them. If that is not available, OpenPulsar
    keeps the existing local in-window shortcut handling.
    """
    if self.global_shortcut_manager is not None:
        return

    manager = GlobalShortcutManager(self)
    manager.shortcutPressed.connect(self.on_global_shortcut_pressed)
    manager.availabilityChanged.connect(self.on_global_shortcuts_availability_changed)
    manager.start()
    self.global_shortcut_manager = manager


def on_global_shortcut_pressed(self, key, modifiers):
    if hasattr(self, "keyboard_commands_editor"):
        self.keyboard_commands_editor.trigger_shortcut(key, modifiers)


def on_global_shortcuts_availability_changed(self, active, message):
    if hasattr(self, "keyboard_commands_editor"):
        self.keyboard_commands_editor.set_local_shortcuts_enabled(not active)

    # Useful during development: if permissions are missing, the user sees
    # the reason in the terminal without breaking the application.
    logger.debug(f"OpenPulsar global shortcuts: {message}")


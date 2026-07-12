import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from openpulsar.gui.main_window import MainWindow
from openpulsar.logging_utils import configure_logging
from openpulsar.gui.settings_dialog import SettingsStore
from openpulsar.gui.single_instance import SingleInstanceGuard


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

# Certains lancements manuels utilisent encore des chemins relatifs hérités.
# On force donc le cwd à la racine du projet pour garder un rendu identique
# en lancement manuel ou autostart.
os.chdir(PROJECT_ROOT)


def picture_path(name):
    for category in ("icons", "backgrounds", "devices"):
        candidate = ASSETS_DIR / category / name
        if candidate.exists():
            return str(candidate)
    return str(ASSETS_DIR / "icons" / name)


def main():
    configure_logging()
    app = QApplication(sys.argv)

    instance_guard = SingleInstanceGuard(app)
    if not instance_guard.acquire():
        return 0
    app._openpulsar_single_instance_guard = instance_guard
    app.aboutToQuit.connect(instance_guard.release)

    app.setWindowIcon(QIcon(picture_path("Icon_OpenPulsar.svg")))

    settings = SettingsStore.load()
    persistent_mode = bool(settings.get("persistent_mode", False))
    start_in_tray = persistent_mode and "--tray" in sys.argv[1:]

    if persistent_mode:
        app.setQuitOnLastWindowClosed(False)

    window = MainWindow(start_in_tray=start_in_tray)

    def activate_existing_window():
        if window.isMinimized():
            window.showNormal()
        else:
            window.show()
        window.raise_()
        window.activateWindow()
        if hasattr(window, "update_tray_visibility_action"):
            window.update_tray_visibility_action()

    instance_guard.set_activation_handler(activate_existing_window)

    # En mode --tray, on ne montre la fenêtre que si le tray n'a pas pu être créé.
    if not start_in_tray or getattr(window, "tray_icon", None) is None:
        window.show()

    return app.exec()


if __name__ == "__main__":
    main()

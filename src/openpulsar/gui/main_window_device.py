"""Device connection and status helpers for MainWindow.

These functions are bound back onto MainWindow as methods.  Keeping them here
lets main_window.py stay focused on window orchestration while preserving the
original Qt object ownership and call flow.
"""

from PySide6.QtCore import QTimer, QSize, Qt
from PySide6.QtGui import QIcon, QTransform
from PySide6.QtWidgets import QFileDialog, QMessageBox

from datetime import datetime
from pathlib import Path
import getpass
import glob
import grp
import os
import platform
import pwd
import stat
import sys

from openpulsar.i18n import tr
from openpulsar.logging_utils import get_logger
from .errors import BEST_EFFORT_ERRORS, HARDWARE_STATE_ERRORS
from .widgets.common_widgets import picture_path

logger = get_logger(__name__)


def start_hidraw_listener(self):
    """Gen1-only build: no persistent hidraw listener.

    Device state is read on startup and after explicit writes.  This avoids
    keeping hidraw devices open permanently and keeps the stable Gen1 branch
    focused on command/response USB feature reports.
    """
    try:
        if hasattr(self.mouse, "_diag"):
            self.mouse._diag("[HIDRAW] Listener disabled in Gen1-only build")
    except BEST_EFFORT_ERRORS as exc:
        logger.debug("Ignored best-effort operation failure", exc_info=True)


def stop_hidraw_listener(self):
    self.listener = None


def start_light_refresh(self):
    """Start a lightweight state refresh loop for Gen1 mice.

    Gen1 mice do not appear to emit asynchronous input reports reliably for
    profile/stage changes.  Instead of keeping a permanent hidraw listener
    open, poll only the tiny state that can change from the mouse itself:
    active hardware profile and active DPI stage.
    """
    if not hasattr(self, "light_refresh_timer") or self.light_refresh_timer is None:
        self.light_refresh_timer = QTimer(self)
        self.light_refresh_timer.setInterval(300)
        self.light_refresh_timer.timeout.connect(self.refresh_light_state)

    if not self.light_refresh_timer.isActive():
        self.light_refresh_timer.start()
        try:
            if hasattr(self.mouse, "_diag"):
                self.mouse._diag("[Refresh] Lightweight refresh started (300 ms)")
        except BEST_EFFORT_ERRORS as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)


def stop_light_refresh(self):
    timer = getattr(self, "light_refresh_timer", None)
    if timer is not None and timer.isActive():
        timer.stop()
        try:
            if hasattr(self.mouse, "_diag"):
                self.mouse._diag("[Refresh] Lightweight refresh stopped")
        except BEST_EFFORT_ERRORS as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)


def get_hardware_active_profile(self):
    """Return the active hardware profile slot, or None if unavailable."""
    if not getattr(self, "_usb_connected", False):
        return None

    reader = getattr(self.mouse, "get_active_profile", None)
    if not callable(reader):
        return None

    try:
        slot = int(reader())
    except HARDWARE_STATE_ERRORS:
        logger.debug("Could not read active hardware profile", exc_info=True)
        return None

    max_profiles = getattr(getattr(self.mouse, "capabilities", None), "num_profiles", 0)
    if not 1 <= slot <= max_profiles:
        logger.debug("Ignoring invalid active hardware profile slot: %r", slot)
        return None

    return slot


def load_hardware_active_profile(self, fallback_slot=1):
    """Load the profile currently selected in hardware, with a safe fallback."""
    slot = self.get_hardware_active_profile()
    if slot is None:
        slot = int(fallback_slot or 1)

    max_profiles = getattr(getattr(self.mouse, "capabilities", None), "num_profiles", 1)
    slot = max(1, min(int(slot), max_profiles))
    self.current_slot = slot
    self.active_slot = slot
    self.load_slot(slot - 1)


def refresh_light_state(self):
    """Poll only small self-changing state and update the UI if needed."""
    if getattr(self, "_shutting_down", False):
        return
    if not getattr(self, "_usb_connected", False):
        return
    if getattr(self, "_loading_profile", False) or getattr(self, "_applying_profile", False):
        return
    if getattr(self, "_pending_apply", False):
        return
    if getattr(self, "current_profile", None) is None:
        return

    suppressor = getattr(self.mouse, "set_diagnostic_suppressed", None)
    try:
        if callable(suppressor):
            suppressor(True)

        hardware_slot = self.get_hardware_active_profile()
        if hardware_slot is not None and hardware_slot != getattr(self, "current_slot", None):
            previous_slot = getattr(self, "current_slot", None)
            try:
                if hasattr(self.mouse, "_diag"):
                    self.mouse._diag(
                        f"[Refresh] Active profile changed: P{previous_slot} -> P{hardware_slot}"
                    )
            except BEST_EFFORT_ERRORS as exc:
                logger.debug("Ignored best-effort operation failure", exc_info=True)
            self.load_slot(hardware_slot - 1)
            return

        try:
            visible_count = self.enabled_dpi_stage_count()
        except HARDWARE_STATE_ERRORS:
            logger.debug("Failed to read visible DPI stage count during refresh", exc_info=True)
            visible_count = 0
        if visible_count <= 0:
            return

        active_stage = self.mouse.get_active_dpi_stage(self.current_slot)
    except HARDWARE_STATE_ERRORS:
        logger.debug("Light refresh could not read active hardware state", exc_info=True)
        return
    finally:
        if callable(suppressor):
            try:
                suppressor(False)
            except BEST_EFFORT_ERRORS as exc:
                logger.debug("Ignored best-effort operation failure", exc_info=True)

    try:
        active_stage = int(active_stage)
    except (TypeError, ValueError):
        logger.debug("Light refresh received a non-integer active DPI stage: %r", active_stage, exc_info=True)
        return

    if not 1 <= active_stage <= visible_count:
        return

    if active_stage == getattr(self, "active_dpi_stage", None):
        return

    previous = getattr(self, "active_dpi_stage", None)
    self.active_dpi_stage = active_stage
    if self.current_profile is not None:
        self.current_profile.active_dpi_stage = active_stage
    self.update_dpi_stars(active_stage)
    self.update_tray_quick_actions()

    try:
        if hasattr(self.mouse, "_diag"):
            self.mouse._diag(
                f"[Refresh] Active DPI stage changed: {previous} -> {active_stage}"
            )
    except BEST_EFFORT_ERRORS as exc:
        logger.debug("Ignored best-effort operation failure", exc_info=True)


def check_usb_connection(self):
    try:
        connected = self.mouse.is_connected()
    except HARDWARE_STATE_ERRORS:
        logger.debug("USB connection check failed", exc_info=True)
        connected = False

    if connected == self._usb_connected:
        return

    self._usb_connected = connected

    if not connected:
        logger.debug("USB DISCONNECTED")
        self.stop_hidraw_listener()
        self.stop_light_refresh()
        self._pending_apply = False
        self._pending_sections.clear()
        try:
            self.mouse.close()
        except BEST_EFFORT_ERRORS as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)

        # La souris n'est plus utilisable : on évite de conserver
        # un ancien modèle/profil visuellement actif. C'est aussi
        # plus sain pour le futur support multi-souris.
        self.clear_device_ui()
        self.set_no_device_state(True)
        self.set_device_controls_enabled(False)
        self.update_device_status()
        self.update_tray_quick_actions()
        return

    logger.debug("USB RECONNECTED")

    try:
        self.mouse.reconnect()
        self.set_no_device_state(False)
        self.set_device_controls_enabled(True)
        self.start_hidraw_listener()
        self.start_light_refresh()
        self.update_device_status()
        self.update_tray_quick_actions()
        QTimer.singleShot(150, self.load_hardware_active_profile)
    except HARDWARE_STATE_ERRORS as e:
        logger.debug(f"USB RECONNECT FAILED: {e}")
        self._usb_connected = False
        self.clear_device_ui()
        self.set_no_device_state(True)
        self.set_device_controls_enabled(False)
        self.update_device_status()
        self.update_tray_quick_actions()


def set_no_device_state(self, enabled: bool):
    """Affiche l'état visuel lorsqu'aucune souris compatible n'est présente."""
    enabled = bool(enabled)

    if hasattr(self, "mouse_button_editor"):
        self.mouse_button_editor.set_no_device_state(enabled)

    if enabled:
        for combo in self.button_mapping_combos():
            combo.hidePopup()


def set_device_controls_enabled(self, enabled: bool):
    """Active/désactive uniquement les contrôles liés à la souris."""
    widgets = []

    widgets.extend([
        self.import_profile_button,
        self.prev_profile_button,
        self.next_profile_button,
        self.export_profile_button,
        self.add_dpi_button,
        getattr(self, "led_settings_button", None),
        self.polling_control,
        self.debounce_control,
        self.lod_control,
        self.motion_sync_check,
        self.angle_snap_check,
        self.ripple_control_check,
        self.left_button_combo,
        self.right_button_combo,
        self.middle_button_combo,
        self.back_button_combo,
        self.forward_button_combo,
        self.dpi_button_combo,
    ])

    widgets.extend(self.profile_labels)
    widgets.extend(self.dpi_stage_rows)
    widgets.extend(self.dpi_led_buttons)
    widgets.extend(self.dpi_boxes)
    widgets.extend(self.dpi_remove_buttons)

    for widget in widgets:
        if widget is None:
            continue
        try:
            widget.setEnabled(enabled)
        except BEST_EFFORT_ERRORS as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)

    if not enabled:
        self.set_led_panel_visible(False)


def clear_device_ui(self):
    """Vide l'interface quand aucune souris n'est connectée.

    On garde la fenêtre ouverte, mais on supprime les anciennes valeurs
    pour ne pas laisser croire qu'une souris débranchée est encore pilotée.
    """
    self._loading_profile = True

    try:
        self.current_profile = None
        self.dpi_stage_colors = []
        self._last_firmware = tr("status.unknown")

        self.polling_control.setValue(
            self.mouse.get_supported_polling_rates()[0]
        )
        self.debounce_control.setValue(0)
        self.lod_control.setValue(
            self.mouse.get_supported_lod_values()[0]
        )

        self.motion_sync_check.setChecked(False)
        self.angle_snap_check.setChecked(False)
        self.ripple_control_check.setChecked(False)

        for combo in self.button_mapping_combos():
            combo.setCurrentIndex(-1)
            combo.setProperty("leftClickProtected", False)
            combo.setStyleSheet("")

        for index, box in enumerate(self.dpi_boxes):
            box.setValue(0)
            # Ne pas modifier la visibilité ici : les widgets DPI
            # participent à la géométrie fixe. On garde exactement les
            # mêmes lignes qu'avant le débranchement, simplement grisées
            # via set_device_controls_enabled(False).
            self.update_dpi_led(index, self.default_dpi_color(index))

        self.update_dpi_stars(0)
        self.update_slot_labels()
        self.update_tray_quick_actions()

    finally:
        self._loading_profile = False


def _connection_status_data(self):
    """Return wired USB status metadata for the Gen1-only build."""
    return "usb", "usb-symbol.svg", tr("status.usb_connection")



def update_device_status(self):
    status = tr("status.connected") if self._usb_connected else tr("status.disconnected")

    if not self._usb_connected:
        model = tr("status.unknown_mouse")
        firmware = tr("status.unknown")
        connection_kind = "usb"
        connection_icon = "usb-symbol.svg"
        connection_tooltip = tr("status.usb_connection")
    else:
        model = tr("status.pulsar_mouse")
        firmware = self._last_firmware

        try:
            if hasattr(self.mouse, "get_model_name"):
                model = self.mouse.get_model_name()
            else:
                model = self.mouse.capabilities.name
        except BEST_EFFORT_ERRORS as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)

        try:
            if hasattr(self.mouse, "get_firmware_version"):
                current_firmware = self.mouse.get_firmware_version()
                if current_firmware not in {"inconnu", "unknown", ""}:
                    firmware = current_firmware
                    self._last_firmware = current_firmware
        except BEST_EFFORT_ERRORS as exc:
            logger.debug("Ignored best-effort operation failure", exc_info=True)

        connection_kind, connection_icon, connection_tooltip = (
            self._connection_status_data()
        )

    self.status_label.setText(
        f"{model}   |   Firmware {firmware}   |   {status}"
    )

    indicator_color = "#22c55e" if self._usb_connected else "#ef4444"
    indicator_tooltip = status

    if hasattr(self, "status_indicator"):
        self.status_indicator.setStyleSheet(
            f"""
            QLabel#usbStatusIndicator {{
                color: {indicator_color};
            }}
            """
        )
    if hasattr(self, "connection_icon"):
        self.connection_icon.clear()
        if self._usb_connected and connection_icon:
            icon_size = QSize(16, 16)
            pixmap = QIcon(picture_path(connection_icon)).pixmap(icon_size)
            if connection_kind == "usb":
                pixmap = pixmap.transformed(
                    QTransform().rotate(90),
                    Qt.SmoothTransformation,
                )
            self.connection_icon.setPixmap(pixmap)
            self.connection_icon.setToolTip(connection_tooltip)
            self.connection_icon.setVisible(True)
        else:
            self.connection_icon.hide()



def _safe_diag_value(label: str, getter):
    try:
        return f"{label}: {getter()}"
    except HARDWARE_STATE_ERRORS as exc:
        return f"{label}: ERROR: {exc}"


def _format_vid_pid(pair):
    if not pair:
        return "unknown"
    try:
        return f"0x{pair[0]:04x}:0x{pair[1]:04x}"
    except (TypeError, ValueError, IndexError):
        logger.debug("Unable to format VID:PID pair %r", pair, exc_info=True)
        return str(pair)


def _format_diag_list(values):
    try:
        return ", ".join(str(v) for v in values) if values else "none"
    except (TypeError, ValueError):
        logger.debug("Unable to format diagnostic list %r", values, exc_info=True)
        return str(values)


def _current_user_groups() -> tuple[str, list[str]]:
    """Return current username and group names for diagnostics."""
    try:
        username = getpass.getuser()
    except (OSError, KeyError):
        logger.debug("Unable to determine current username", exc_info=True)
        username = "unknown"

    groups = []
    try:
        gids = os.getgroups()
        for gid in gids:
            try:
                groups.append(grp.getgrgid(gid).gr_name)
            except KeyError:
                groups.append(str(gid))
    except BEST_EFFORT_ERRORS as exc:
        logger.debug("Ignored best-effort operation failure", exc_info=True)

    try:
        primary_gid = os.getgid()
        primary_group = grp.getgrgid(primary_gid).gr_name
        if primary_group not in groups:
            groups.insert(0, primary_group)
    except BEST_EFFORT_ERRORS as exc:
        logger.debug("Ignored best-effort operation failure", exc_info=True)

    return username, sorted(set(groups))


def _hidraw_permission_report() -> list[str]:
    """Build a diagnostic section for /dev/hidraw permissions."""
    lines = ["Permissions", "-----------", "", "hidraw devices", "--------------"]
    paths = sorted(glob.glob("/dev/hidraw*"))
    any_ok = False
    any_denied = False

    if not paths:
        lines.append("No /dev/hidraw* devices found")
    else:
        for path in paths:
            lines.append(path)
            try:
                st = os.stat(path)
                try:
                    owner = pwd.getpwuid(st.st_uid).pw_name
                except KeyError:
                    owner = str(st.st_uid)
                try:
                    group = grp.getgrgid(st.st_gid).gr_name
                except KeyError:
                    group = str(st.st_gid)
                mode = stat.filemode(st.st_mode)
                lines.append(f"  Owner : {owner}")
                lines.append(f"  Group : {group}")
                lines.append(f"  Mode  : {mode}")
                try:
                    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
                    os.close(fd)
                    access = "OK"
                    any_ok = True
                except PermissionError as exc:
                    access = f"DENIED ({exc})"
                    any_denied = True
                except OSError as exc:
                    access = f"ERROR ({exc})"
                lines.append(f"  Access: {access}")
            except OSError as exc:
                lines.append(f"  Error : {exc}")
            lines.append("")

    username, groups = _current_user_groups()
    lines.extend([
        "Current user",
        "------------",
        f"Username : {username}",
        f"Groups   : {', '.join(groups) if groups else 'unknown'}",
        "",
        "Summary",
        "-------",
    ])

    if paths and any_ok:
        lines.append("HIDRAW access : OK")
    elif paths and any_denied:
        lines.append("HIDRAW access : FAILED")
        lines.append("")
        lines.append("Recommendation:")
        lines.append("Install the OpenPulsar udev rules, reconnect the mouse, then log out and back in if group membership changed.")
    elif paths:
        lines.append("HIDRAW access : ERROR")
    else:
        lines.append("HIDRAW access : NOT FOUND")

    return lines


def build_diagnostic_report(self) -> str:
    """Build a human-readable diagnostic report for issue reports."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mouse = getattr(self, "mouse", None)
    lines = []

    lines.extend([
        "OpenPulsar Diagnostic Report",
        "============================",
        f"Generated: {now}",
        "",
        "System",
        "------",
        f"Platform: {platform.platform()}",
        f"Python: {sys.version.split()[0]}",
        "",
        "Application",
        "-----------",
        "OpenPulsar: development build",
        f"Connected according to UI: {bool(getattr(self, '_usb_connected', False))}",
        "",
    ])

    if mouse is None:
        lines.extend(["Device", "------", "No mouse object available", ""])
        return "\n".join(lines)

    caps = getattr(mouse, "capabilities", None)
    lines.extend(["Device", "------"])
    if caps is not None:
        lines.append(f"Model capability name: {getattr(caps, 'name', 'unknown')}")
        lines.append(f"Declared VID:PID pairs: {', '.join(_format_vid_pid(pair) for pair in getattr(caps, 'vid_pid_pairs', []))}")
        lines.append(f"Declared interface: {getattr(caps, 'interface_num', 'unknown')}")
        lines.append(f"Report size: {getattr(caps, 'report_size', 'unknown')}")
        lines.append(f"Profiles: {getattr(caps, 'num_profiles', 'unknown')}")
        lines.append(f"Max DPI stages: {getattr(caps, 'max_dpi_stages', 'unknown')}")
        lines.append(f"Polling rates: {getattr(caps, 'polling_rates', 'unknown')}")
        lines.append(f"LOD values: {getattr(caps, 'lod_values', 'unknown')}")
    else:
        lines.append("No capabilities object available")

    lines.append(f"Current VID:PID: {_format_vid_pid(getattr(mouse, 'current_vid_pid', None))}")
    lines.append(f"Protocol class: {mouse.__class__.__module__}.{mouse.__class__.__name__}")
    if hasattr(mouse, "get_selected_interface"):
        lines.append(_safe_diag_value("Selected interface", mouse.get_selected_interface))
    if hasattr(mouse, "get_interface_selection_mode"):
        lines.append(_safe_diag_value("Interface selection mode", mouse.get_interface_selection_mode))
    if hasattr(mouse, "get_interface_candidates"):
        lines.append(_safe_diag_value("Interface candidates", lambda: _format_diag_list(mouse.get_interface_candidates())))
    if hasattr(mouse, "get_connection_type"):
        lines.append(_safe_diag_value("Connection type", mouse.get_connection_type))
    if hasattr(mouse, "get_model_name"):
        lines.append(_safe_diag_value("Reported model", mouse.get_model_name))
    if hasattr(mouse, "get_firmware_version"):
        lines.append(_safe_diag_value("Firmware", mouse.get_firmware_version))

    lines.extend(["", "USB interfaces", "--------------"])
    if hasattr(mouse, "get_usb_interface_descriptions"):
        usb_interfaces = mouse.get_usb_interface_descriptions()
        lines.extend(usb_interfaces or ["No USB interface information available"])
    else:
        lines.append("Protocol does not expose USB interface descriptions")

    lines.extend(["", *_hidraw_permission_report()])

    lines.extend(["", "Interface selection", "-------------------"])
    if hasattr(mouse, "get_interface_selection_mode"):
        lines.append(_safe_diag_value("Mode", mouse.get_interface_selection_mode))
    if hasattr(mouse, "get_selected_interface"):
        lines.append(_safe_diag_value("Selected", mouse.get_selected_interface))
    if hasattr(mouse, "get_interface_candidates"):
        lines.append(_safe_diag_value("Candidate order", lambda: _format_diag_list(mouse.get_interface_candidates())))

    lines.extend(["", "Interface probe", "---------------"])
    if hasattr(mouse, "get_interface_probe_log"):
        probe_log = mouse.get_interface_probe_log()
        lines.extend(probe_log or ["No interface probe log available"])
    else:
        lines.append("Protocol does not expose interface probe logs")

    lines.extend(["", "Communication log", "-----------------"])
    if hasattr(mouse, "get_diagnostic_log"):
        diag = mouse.get_diagnostic_log()
        lines.extend(diag or ["No communication log available"])
    else:
        lines.append("Protocol does not expose communication logs")

    lines.append("")
    return "\n".join(lines)


def export_diagnostic_log(self):
    """Ask where to save and export a diagnostic .txt report."""
    mouse = getattr(self, "mouse", None)
    model = "OpenPulsar"
    try:
        if mouse is not None and hasattr(mouse, "get_model_name"):
            model = mouse.get_model_name()
        elif mouse is not None and hasattr(mouse, "capabilities"):
            model = mouse.capabilities.name
    except BEST_EFFORT_ERRORS as exc:
        logger.debug("Ignored best-effort operation failure", exc_info=True)

    safe_model = "".join(ch if ch.isalnum() else "_" for ch in model).strip("_") or "OpenPulsar"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    default_name = f"OpenPulsar_{safe_model}_{timestamp}.txt"

    path, _ = QFileDialog.getSaveFileName(
        self,
        tr("diagnostic.save_dialog.title"),
        str(Path.home() / default_name),
        tr("diagnostic.file_filter"),
    )
    if not path:
        return

    try:
        Path(path).write_text(self.build_diagnostic_report(), encoding="utf-8")
    except OSError as exc:
        QMessageBox.warning(
            self,
            tr("diagnostic.export_error.title"),
            tr("diagnostic.export_error.body").format(error=exc),
        )
        return

    QMessageBox.information(
        self,
        tr("diagnostic.export_success.title"),
        tr("diagnostic.export_success.body"),
    )



class DeviceMixin:
    """Device/status/diagnostic behavior for MainWindow."""

    start_hidraw_listener = start_hidraw_listener
    stop_hidraw_listener = stop_hidraw_listener
    start_light_refresh = start_light_refresh
    stop_light_refresh = stop_light_refresh
    get_hardware_active_profile = get_hardware_active_profile
    load_hardware_active_profile = load_hardware_active_profile
    refresh_light_state = refresh_light_state
    check_usb_connection = check_usb_connection
    set_no_device_state = set_no_device_state
    set_device_controls_enabled = set_device_controls_enabled
    clear_device_ui = clear_device_ui
    _connection_status_data = _connection_status_data
    build_diagnostic_report = build_diagnostic_report
    export_diagnostic_log = export_diagnostic_log
    update_device_status = update_device_status

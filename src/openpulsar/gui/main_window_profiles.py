"""Profile, button mapping, and auto-apply helpers for MainWindow."""

import copy
import time

from PySide6.QtCore import QSignalBlocker, QTimer
from PySide6.QtWidgets import QFileDialog

from openpulsar.i18n import tr
from openpulsar.logging_utils import get_logger
from openpulsar.core.device_mapper import (
    read_profile_from_mouse,
    apply_profile_to_mouse,
    BUTTON_IDS,
    encode_button_action,
)
from openpulsar.core.serialization import (
    save_profile as save_profile_file,
    load_profile as load_profile_file,
)
from openpulsar.core.dpi import DpiStage

from .errors import HARDWARE_STATE_ERRORS
from .main_window_actions import action_to_text as format_button_action
from .main_window_actions import text_to_action as parse_button_action
from .main_window_profile_style import profile_segment_style
from .metrics import PANEL_BORDER_WIDTH
from .profile.profile_extras_store import ProfileExtrasStore, apply_profile_extras
from .widgets.keyboard_widgets import KeyboardCommandsEditor
from .widgets.op_dialog import OPDialog

logger = get_logger(__name__)


class ProfileMixin:
    def _profile_segment_style(
        self,
        active=False,
        left_radius=False,
        right_radius=False,
        accent=False,
    ):
        return profile_segment_style(
            active=active,
            left_radius=left_radius,
            right_radius=right_radius,
            accent=accent,
        )

    def update_slot_labels(self):
        self.import_profile_button.setStyleSheet(
            self._profile_segment_style(
                accent=True,
                left_radius=True,
            ).replace(
                "border-left: 0px;",
                f"border-left: {PANEL_BORDER_WIDTH}px solid #2f6cff;",
            )
        )

        self.prev_profile_button.setStyleSheet(
            self._profile_segment_style()
        )

        self.next_profile_button.setStyleSheet(
            self._profile_segment_style()
        )

        self.export_profile_button.setStyleSheet(
            self._profile_segment_style(
                accent=True,
                right_radius=True,
            )
        )

        for slot, label in enumerate(
            self.profile_labels,
            start=1,
        ):
            label.setText(f"P{slot}")
            label.setStyleSheet(
                self._profile_segment_style(
                    active=(slot == self.current_slot),
                )
            )



    def action_to_text(self, action):
        return format_button_action(action)

    def text_to_action(self, text):
        return parse_button_action(text)

    def button_mapping_combos(self):
        return (
            self.left_button_combo,
            self.right_button_combo,
            self.middle_button_combo,
            self.back_button_combo,
            self.forward_button_combo,
        )

    def _set_button_combo_from_action(self, combo, button_name, action):
        text = self.action_to_text(action)
        index = combo.findText(text)
        if index < 0:
            logger.debug(
                "Button mapping text is not available in combo: %s -> %r (%r)",
                button_name,
                text,
                action,
            )
            return
        combo.setCurrentIndex(index)

    def _apply_button_mappings_to_ui(self, profile):
        """Apply decoded hardware button mappings to the visible combo boxes.

        This is deliberately separate from the rest of profile loading so a
        best-effort failure while refreshing LOD/DPI/LED state cannot leave all
        combo boxes at their construction-time default (Left Click).
        """
        buttons = getattr(profile, "buttons", {}) or {}
        mapping = (
            ("left", self.left_button_combo),
            ("right", self.right_button_combo),
            ("wheel", self.middle_button_combo),
            ("thumb_back", self.back_button_combo),
            ("thumb_front", self.forward_button_combo),
            ("dpi", self.dpi_button_combo),
        )
        for button_name, combo in mapping:
            action = buttons.get(button_name)
            if action is None:
                logger.debug("No decoded hardware mapping for button %s", button_name)
                continue
            self._set_button_combo_from_action(combo, button_name, action)

    def update_left_click_lock(self):
        combos = self.button_mapping_combos()
        left_click_text = tr("Left Click")

        left_click_combos = [
            combo
            for combo in combos
            if combo.currentText() == left_click_text
        ]

        for combo in combos:
            combo.setProperty("leftClickProtected", False)
            combo.setStyleSheet("")
            combo.update()

        if len(left_click_combos) == 1:
            protected_combo = left_click_combos[0]
            protected_combo.setProperty("leftClickProtected", True)
            protected_combo.setStyleSheet("""
                QComboBox#mouseButtonCombo {
                    background-color: #fff7f7;
                    border: 1px solid #ef4444;
                    border-radius: 4px;
                    padding-left: 8px;
                    padding-right: 0px;
                    color: #dc2626;
                    min-height: 16px;
                }

                QComboBox#mouseButtonCombo:hover {
                    background-color: #fff1f2;
                    border: 1px solid #dc2626;
                    color: #b91c1c;
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
            """)
            protected_combo.update()

    def on_profile_changed(self, profile):
        if self._loading_profile or self._applying_profile:
            return

        logger.debug("HIDRAW PROFILE EVENT %s", profile)

        self.active_slot = profile
        self.current_slot = profile
        self.load_slot(profile - 1)

    def connect_auto_apply(self):
        section_widgets = [
            (self.left_button_combo, "buttons"),
            (self.right_button_combo, "buttons"),
            (self.middle_button_combo, "buttons"),
            (self.back_button_combo, "buttons"),
            (self.forward_button_combo, "buttons"),
            (self.dpi_button_combo, "buttons"),
        ]

        for widget, section in section_widgets:
            widget.currentTextChanged.connect(
                lambda *_args: self.update_left_click_lock()
            )
            widget.currentTextChanged.connect(
                lambda *_args, section=section: self.auto_apply(section)
            )

        sensor_controls = [
            (self.polling_control, "polling"),
            (self.debounce_control, "debounce"),
            (self.lod_control, "lod"),
        ]

        for control, section in sensor_controls:
            control.previous_button.clicked.connect(
                lambda *_args, section=section: self.auto_apply(section)
            )
            control.next_button.clicked.connect(
                lambda *_args, section=section: self.auto_apply(section)
            )

        checkbox_sections = [
            (self.motion_sync_check, "motion_sync"),
            (self.angle_snap_check, "angle_snap"),
            (self.ripple_control_check, "ripple_control"),
        ]

        for checkbox, section in checkbox_sections:
            checkbox.toggled.connect(
                lambda *_args, section=section: self.auto_apply(section)
            )

        for dpi_box in self.dpi_boxes:
            dpi_box.value_label.editingFinished.connect(
                lambda section="dpi": self.auto_apply(section)
            )

    def auto_apply(self, section="all", *args):
        if self._loading_profile or self._applying_profile:
            return

        if self.current_profile is None:
            return

        if isinstance(section, str):
            sections = {section}
        else:
            sections = set(section)

        # Capture the profile targeted by this user action immediately.
        # Deferred apply callbacks must never infer the target profile later
        # from self.current_slot, because the user may have changed profile in
        # the meantime.
        target_slot = self.current_slot
        profile = self._sync_profile_from_ui(
            target_slot=target_slot,
            profile=self.current_profile,
        )

        self._pending_apply = True
        self._pending_sections.update(sections)
        self._pending_sections_by_slot.setdefault(target_slot, set()).update(sections)
        self._pending_profiles_by_slot[target_slot] = copy.deepcopy(profile)
        self.auto_apply_timer.start(300)

    def flush_auto_apply(self):
        if not self._pending_apply:
            return

        if self._loading_profile or self._applying_profile:
            self.auto_apply_timer.start(250)
            return

        pending_sections_by_slot = {
            slot: set(sections)
            for slot, sections in self._pending_sections_by_slot.items()
        }
        pending_profiles_by_slot = {
            slot: copy.deepcopy(profile)
            for slot, profile in self._pending_profiles_by_slot.items()
        }
        pending_dpi_stage_base_count_by_slot = dict(
            getattr(self, "_pending_dpi_stage_base_count_by_slot", {})
        )

        # Backward compatibility for any caller/test that still only fills the
        # legacy global set.  New code should use the slot-aware maps above.
        if not pending_sections_by_slot and self._pending_sections:
            pending_sections_by_slot[self.current_slot] = set(self._pending_sections)

        self._pending_apply = False
        self._pending_sections.clear()
        self._pending_sections_by_slot.clear()
        self._pending_profiles_by_slot.clear()
        if hasattr(self, "_pending_dpi_stage_base_count_by_slot"):
            self._pending_dpi_stage_base_count_by_slot.clear()

        for target_slot, sections in pending_sections_by_slot.items():
            self.send_to_mouse(
                sections,
                target_slot=target_slot,
                profile=pending_profiles_by_slot.get(target_slot),
                dpi_stage_base_count=pending_dpi_stage_base_count_by_slot.get(target_slot),
            )

    def persist_keyboard_commands_for_current_slot(self):
        if getattr(self, "_loading_profile", False):
            return
        if not hasattr(self, "keyboard_commands_editor"):
            return

        commands = self.keyboard_commands_editor.commands_to_list()
        if self.current_profile is not None:
            self.current_profile.keyboard_commands = commands
        ProfileExtrasStore.save_keyboard_commands(self.current_slot, commands)

    def activate_profile(self, slot):
        logger.debug("ACTIVATE PROFILE %s", slot)

        self.persist_keyboard_commands_for_current_slot()

        try:
            self.mouse.set_active_profile(slot)

            # read-after-write
            self.current_slot = slot
            self.active_slot = slot
            self.load_slot(slot - 1)

            logger.debug("PROFILE ACTIVATED")
        except HARDWARE_STATE_ERRORS as e:
            logger.debug("ACTIVATE PROFILE FAILED: %s", e)

    def previous_slot(self):
        slot = self.current_slot - 1

        if slot < 1:
            slot = self.mouse.capabilities.num_profiles

        self.activate_profile(slot)

    def next_slot(self):
        slot = self.current_slot + 1

        if slot > self.mouse.capabilities.num_profiles:
            slot = 1

        self.activate_profile(slot)

    def change_profile_by_mode(self, mode):
        profile_count = self.mouse.capabilities.num_profiles
        if profile_count <= 0:
            return

        current = self.current_slot
        if not 1 <= current <= profile_count:
            current = 1

        if mode == "Incrémental":
            next_profile = min(current + 1, profile_count)
        elif mode == "Décrémental":
            next_profile = max(current - 1, 1)
        elif mode == "Cycle inversé":
            next_profile = current - 1
            if next_profile < 1:
                next_profile = profile_count
        else:
            next_profile = current + 1
            if next_profile > profile_count:
                next_profile = 1

        if next_profile == current:
            return

        self.activate_profile(next_profile)

    def load_slot(self, row):
        if row < 0 or not self._usb_connected:
            return

        self.set_no_device_state(False)
        slot = row + 1

        self._loading_profile = True

        try:
            profile = read_profile_from_mouse(
                self.mouse,
                slot=slot,
                name=f"Slot {slot}",
            )
            extras = ProfileExtrasStore.load_slot(slot)
            apply_profile_extras(profile, extras)

            stored_commands = ProfileExtrasStore.load_keyboard_commands(slot)
            if stored_commands is not None:
                profile.keyboard_commands = stored_commands
            elif not getattr(profile, "keyboard_commands", None):
                profile.keyboard_commands = KeyboardCommandsEditor.load_legacy_keyboard_commands()

            for stage in profile.dpi_stages:
                stage.color = self.remove_led_correction(stage.color, profile=profile)

            logger.debug("LOADED:")
            for i, stage in enumerate(profile.dpi_stages):
                logger.debug(
                    i + 1,
                    stage.color.r,
                    stage.color.g,
                    stage.color.b,
                )

            self.current_slot = slot
            self.current_profile = profile

            # Restore profile-local keyboard commands as soon as the profile is
            # known.  This keeps the keyboard command page in sync even if a
            # later best-effort UI refresh fails while reading hardware state.
            if hasattr(self, "keyboard_commands_editor"):
                self.keyboard_commands_editor.set_keyboard_commands(
                    getattr(profile, "keyboard_commands", [])
                )

            self.dpi_stage_colors = [
                stage.color
                for stage in profile.dpi_stages
            ]
            self.update_slot_labels()

            # Apply hardware button mappings early.  The remaining hardware/UI
            # refresh below is best-effort and must not prevent the button
            # combos from reflecting the mappings decoded from the mouse.
            self._apply_button_mappings_to_ui(profile)

            self.polling_control.setValue(profile.polling_rate)
            self.debounce_control.setValue(profile.debounce)

            try:
                self.lod_control.setValue(
                    self.mouse.get_lod(slot)
                )
            except HARDWARE_STATE_ERRORS as exc:
                logger.debug("Unable to refresh LOD for slot %s: %s", slot, exc, exc_info=True)
                if hasattr(profile, "lod"):
                    self.lod_control.setValue(profile.lod)

            self.motion_sync_check.setChecked(profile.motion_sync)
            self.angle_snap_check.setChecked(profile.angle_snap)
            self.ripple_control_check.setChecked(profile.ripple_control)

            for row in self.dpi_stage_rows:
                row.hide()

            for dpi_box in self.dpi_boxes:
                dpi_box.hide()

            for remove_button in self.dpi_remove_buttons:
                remove_button.hide()

            for minus_button in self.dpi_minus_buttons:
                minus_button.hide()

            for plus_button in self.dpi_plus_buttons:
                plus_button.hide()

            for led_button in self.dpi_led_buttons:
                led_button.hide()

            for index, stage in enumerate(profile.dpi_stages):
                self.dpi_boxes[index].setValue(stage.dpi)
                self.dpi_stage_rows[index].show()
                self.dpi_boxes[index].show()
                self.dpi_led_buttons[index].show()
                self.dpi_minus_buttons[index].show()
                self.dpi_plus_buttons[index].show()

                if index < len(self.dpi_stage_colors):
                    color = self.dpi_stage_colors[index]
                else:
                    color = stage.color

                self.update_dpi_led(index, color)
                self.dpi_remove_buttons[index].show()

            synced_stage = self.sync_active_dpi_indicator(slot)
            if synced_stage is not None:
                profile.active_dpi_stage = synced_stage
            else:
                # Dynamic state is allowed to arrive on the next light refresh.
                # Do not invent an active DPI stage during profile loading.
                self.active_dpi_stage = 0
                self.update_dpi_stars(0)
            self.update_tray_quick_actions()

            self._apply_button_mappings_to_ui(profile)
            self.update_left_click_lock()
            if synced_stage is not None:
                self.active_dpi_stage = max(1, min(int(synced_stage), len(profile.dpi_stages) or 1))
                self.update_dpi_stars(self.active_dpi_stage)
            self.sync_led_panel_from_profile()
            if hasattr(self, "keyboard_commands_editor"):
                self.keyboard_commands_editor.set_keyboard_commands(
                    getattr(profile, "keyboard_commands", [])
                )

        except HARDWARE_STATE_ERRORS as e:
            logger.debug("Failed to load slot %s: %s", slot, e, exc_info=True)

        finally:
            self._loading_profile = False

    def _set_ui_from_profile(self, profile):
        """Charge un Profile dans l'interface sans écrire immédiatement en USB."""
        self._loading_profile = True

        try:
            self.current_profile = profile
            self.dpi_stage_colors = [
                stage.color
                for stage in profile.dpi_stages
            ]

            self.polling_control.setValue(profile.polling_rate)
            self.debounce_control.setValue(profile.debounce)

            if hasattr(profile, "lod"):
                self.lod_control.setValue(profile.lod)

            self.motion_sync_check.setChecked(profile.motion_sync)
            self.angle_snap_check.setChecked(profile.angle_snap)
            self.ripple_control_check.setChecked(profile.ripple_control)

            for row in self.dpi_stage_rows:
                row.hide()

            for dpi_box in self.dpi_boxes:
                dpi_box.hide()

            for remove_button in self.dpi_remove_buttons:
                remove_button.hide()

            for minus_button in self.dpi_minus_buttons:
                minus_button.hide()

            for plus_button in self.dpi_plus_buttons:
                plus_button.hide()

            for led_button in self.dpi_led_buttons:
                led_button.hide()

            for index, stage in enumerate(profile.dpi_stages):
                if index >= len(self.dpi_boxes):
                    break

                self.dpi_boxes[index].setValue(stage.dpi)
                self.dpi_stage_rows[index].show()
                self.dpi_boxes[index].show()
                self.dpi_led_buttons[index].show()
                self.dpi_minus_buttons[index].show()
                self.dpi_plus_buttons[index].show()
                self.update_dpi_led(index, stage.color)
                self.dpi_remove_buttons[index].show()

            active_stage = max(1, min(int(getattr(profile, "active_dpi_stage", 1)), len(profile.dpi_stages) or 1))
            self.active_dpi_stage = active_stage
            self.update_dpi_stars(active_stage)
            self._apply_button_mappings_to_ui(profile)
            self.update_left_click_lock()
            self.sync_led_panel_from_profile()
            if hasattr(self, "keyboard_commands_editor"):
                self.keyboard_commands_editor.set_keyboard_commands(
                    getattr(profile, "keyboard_commands", [])
                )

        finally:
            self._loading_profile = False

    def import_current_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("profile.import.dialog.title").format(slot=self.current_slot),
            "",
            tr("profile.file_dialog.filter"),
        )

        if not path:
            return

        try:
            imported_profile = load_profile_file(path)

            # On conserve les touches éventuellement absentes du JSON
            # pour éviter de casser un vieux profil partiel.
            if self.current_profile is not None:
                for name, action in self.current_profile.buttons.items():
                    imported_profile.buttons.setdefault(name, action)

            imported_profile.name = f"Slot {self.current_slot}"
            self._set_ui_from_profile(imported_profile)
            self.send_to_mouse({"all"})

        except HARDWARE_STATE_ERRORS as e:
            OPDialog.error(
                self,
                tr("profile.import.error.title"),
                tr("profile.import.error.body").format(error=e),
            )

    def export_current_profile(self):
        if self.current_profile is None:
            return

        default_name = f"openpulsar_P{self.current_slot}.json"

        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("profile.export.dialog.title").format(slot=self.current_slot),
            default_name,
            tr("profile.file_dialog.filter"),
        )

        if not path:
            return

        if not path.lower().endswith(".json"):
            path += ".json"

        try:
            profile = self._sync_profile_from_ui(target_slot=self.current_slot)
            profile.name = f"Slot {self.current_slot}"
            save_profile_file(profile, path)

        except HARDWARE_STATE_ERRORS as e:
            OPDialog.error(
                self,
                tr("profile.export.error.title"),
                tr("profile.export.error.body").format(error=e),
            )


    def _sync_profile_from_ui(self, target_slot=None, profile=None):
        """Met à jour le profil affiché depuis l'interface, sans écrire USB.

        target_slot is captured when the user action is created.  It must be
        used for persistence instead of reading self.current_slot later.
        """
        target_slot = int(target_slot or self.current_slot)
        profile = profile or self.current_profile

        if profile is None:
            return None

        profile.polling_rate = self.polling_control.value()
        profile.debounce = self.debounce_control.value()
        profile.lod = self.lod_control.value()

        profile.motion_sync = self.motion_sync_check.isChecked()
        profile.angle_snap = self.angle_snap_check.isChecked()
        profile.ripple_control = self.ripple_control_check.isChecked()

        if hasattr(self, "led_red_gain_control"):
            profile.led_red_gain = self.led_red_gain_control.value()
            profile.led_green_gain = self.led_green_gain_control.value()
            profile.led_blue_gain = self.led_blue_gain_control.value()
            profile.led_brightness = self.led_brightness_control.value()
            profile.led_pulse = self.led_pulse_control.value()
            profile.led_enabled = bool(getattr(profile, "led_enabled", True))
            profile.led_pulse_enabled = bool(getattr(profile, "led_pulse_enabled", False))

        if hasattr(self, "keyboard_commands_editor"):
            profile.keyboard_commands = self.keyboard_commands_editor.commands_to_list()

        for index, box in enumerate(self.dpi_boxes):
            if self.is_dpi_stage_enabled(index) and hasattr(box, "commit_edit"):
                box.commit_edit()

        old_stages = profile.dpi_stages
        profile.dpi_stages = []

        for index, box in enumerate(self.dpi_boxes):
            if not self.is_dpi_stage_enabled(index):
                continue

            if index < len(self.dpi_stage_colors):
                color = self.dpi_stage_colors[index]
            elif index < len(old_stages):
                color = old_stages[index].color
            else:
                color = self.default_dpi_color(index)

            profile.dpi_stages.append(
                DpiStage(
                    dpi=box.value(),
                    color=color,
                )
            )

        profile.buttons["left"] = self.text_to_action(
            self.left_button_combo.currentText()
        )

        profile.buttons["right"] = self.text_to_action(
            self.right_button_combo.currentText()
        )

        profile.buttons["wheel"] = self.text_to_action(
            self.middle_button_combo.currentText()
        )

        profile.buttons["thumb_back"] = self.text_to_action(
            self.back_button_combo.currentText()
        )

        profile.buttons["thumb_front"] = self.text_to_action(
            self.forward_button_combo.currentText()
        )

        profile.buttons["dpi"] = self.text_to_action(
            self.dpi_button_combo.currentText()
        )

        visible_count = len(profile.dpi_stages)
        active_stage = int(getattr(self, "active_dpi_stage", getattr(profile, "active_dpi_stage", 1)))
        profile.active_dpi_stage = max(1, min(active_stage, visible_count or 1))

        if not self._loading_profile:
            ProfileExtrasStore.save_slot(target_slot, profile)

        return profile

    def _write_dpi_stage_expansion_sequence(self, profile, base_count, target_slot):
        """Apply a Gen1-safe DPI stage expansion sequence.

        The Gen1 firmware applies DPI LED colors reliably only for the
        currently active DPI stage.  When several stages are created during
        one auto-apply window, replay the creation in order at flush time:
        extend to stage N, make N active, then write color N.
        """
        slot = int(target_slot)
        final_count = len(profile.dpi_stages)
        base_count = max(0, min(int(base_count or 0), final_count))

        if base_count >= final_count:
            return False

        for stage_count in range(base_count + 1, final_count + 1):
            dpi_values = [stage.dpi for stage in profile.dpi_stages[:stage_count]]
            self.mouse.set_dpi_stages(dpi_values, stage_count, slot)
            time.sleep(0.05)

            self.mouse.set_active_dpi_stage(stage_count, slot)
            time.sleep(0.03)

            color = profile.dpi_stages[stage_count - 1].color
            corrected_color = self.apply_led_correction(color, profile=profile)
            self.mouse.set_stage_color(
                stage_count,
                corrected_color.r,
                corrected_color.g,
                corrected_color.b,
                slot,
            )
            time.sleep(0.03)

        profile.active_dpi_stage = final_count
        return True

    def _write_partial_sections(self, profile, sections, active_stage, target_slot, dpi_stage_base_count=None):
        slot = int(target_slot)

        if "polling" in sections:
            logger.debug("PARTIAL SEND: polling")
            self.mouse.set_polling_rate(profile.polling_rate, slot)
            time.sleep(0.02)

        if "debounce" in sections:
            logger.debug("PARTIAL SEND: debounce")
            self.mouse.set_debounce(profile.debounce, slot)
            time.sleep(0.02)

        if "motion_sync" in sections:
            logger.debug("PARTIAL SEND: motion_sync")
            self.mouse.set_motion_sync(profile.motion_sync, slot)
            time.sleep(0.02)

        if "angle_snap" in sections:
            logger.debug("PARTIAL SEND: angle_snap")
            self.mouse.set_angle_snap(profile.angle_snap, slot)
            time.sleep(0.02)

        if "ripple_control" in sections:
            logger.debug("PARTIAL SEND: ripple_control")
            self.mouse.set_ripple_control(profile.ripple_control, slot)
            time.sleep(0.02)

        if "lod" in sections:
            logger.debug("PARTIAL SEND: lod")
            self.mouse.set_lod(profile.lod, slot)
            time.sleep(0.02)

        handled_dpi_expansion = False
        if "dpi" in sections:
            logger.debug("PARTIAL SEND: dpi")

            if dpi_stage_base_count is not None and int(dpi_stage_base_count) < len(profile.dpi_stages):
                handled_dpi_expansion = self._write_dpi_stage_expansion_sequence(
                    profile,
                    dpi_stage_base_count,
                    slot,
                )
                active_stage = len(profile.dpi_stages)
            else:
                dpi_values = [stage.dpi for stage in profile.dpi_stages]
                self.mouse.set_dpi_stages(dpi_values, active_stage, slot)
                time.sleep(0.05)

        if "colors" in sections and not handled_dpi_expansion:
            logger.debug("PARTIAL SEND: colors")
            # Gen1 applies DPI-stage LED changes reliably only for the
            # active DPI stage.  OpenPulsar's UI only allows editing the
            # active stage color, so only that stage is written here.
            color_stage = max(1, min(active_stage, len(profile.dpi_stages) or 1))
            stage = profile.dpi_stages[color_stage - 1]
            corrected_color = self.apply_led_correction(stage.color, profile=profile)
            self.mouse.set_stage_color(
                color_stage,
                corrected_color.r,
                corrected_color.g,
                corrected_color.b,
                slot,
            )
            time.sleep(0.03)

        if "led_settings" in sections:
            logger.debug("PARTIAL SEND: led_settings")
            self.apply_led_output_settings_to_mouse(profile, slot)
            time.sleep(0.02)

        if "buttons" in sections:
            logger.debug("PARTIAL SEND: buttons")
            for button_name, action in profile.buttons.items():
                button_id = BUTTON_IDS[button_name]
                button_type, a1, a2 = encode_button_action(action)
                self.mouse.set_button(
                    button_id,
                    button_type,
                    a1,
                    a2,
                    slot,
                )
                time.sleep(0.03)

    def send_to_mouse(self, sections=None, target_slot=None, profile=None, dpi_stage_base_count=None):
        target_slot = int(target_slot or self.current_slot)

        if (
            self._loading_profile
            or self._applying_profile
        ):
            return

        if profile is None and self.current_profile is None:
            return

        if not self._usb_connected:
            logger.debug("USB disconnected: apply ignored")
            return

        sections = set(sections or {"all"})
        full_apply = "all" in sections

        self._applying_profile = True

        try:
            if profile is None:
                profile = self._sync_profile_from_ui(target_slot=target_slot)
            else:
                profile = copy.deepcopy(profile)

            active_stage = max(1, min(int(getattr(profile, "active_dpi_stage", getattr(self, "active_dpi_stage", 1))), len(profile.dpi_stages) or 1))

            logger.debug("SENDING SECTIONS: %s", sorted(sections))
            for i, stage in enumerate(profile.dpi_stages):
                logger.debug(
                    i + 1,
                    stage.color.r,
                    stage.color.g,
                    stage.color.b,
                )

            if full_apply:
                # Chemin de sécurité : ancien comportement complet.
                apply_profile_to_mouse(
                    self.mouse,
                    self.profile_with_led_correction(profile),
                    target_slot,
                )
                self.apply_led_output_settings_to_mouse(profile, target_slot)
            else:
                self._write_partial_sections(
                    profile,
                    sections,
                    active_stage,
                    target_slot,
                    dpi_stage_base_count=dpi_stage_base_count,
                )

            # Do not force a profile reload after writes. Dynamic states
            # (active profile / active DPI stage) are reconciled by the
            # normal light refresh cycle.

            active_stage = max(
                1,
                min(
                    int(getattr(profile, "active_dpi_stage", active_stage)),
                    len(profile.dpi_stages) or 1,
                ),
            )
            self.mouse.set_active_dpi_stage(
                active_stage,
                target_slot,
            )

            # read-after-write: on confirme le stage réellement actif avant de
            # mettre à jour le contour dans l’UI.  If the user has already
            # moved to another profile, this call updates the profile-local
            # state but must not repaint the currently displayed profile.
            self.sync_active_dpi_indicator(target_slot)
            self.update_tray_quick_actions()

        except HARDWARE_STATE_ERRORS as e:
            logger.debug(f"Erreur envoi souris: {e}")

        finally:
            self._applying_profile = False

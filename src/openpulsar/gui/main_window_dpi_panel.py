from functools import partial

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout, QMenu, QPushButton, QWidget, QWidgetAction

from openpulsar.core.dpi import Color
from openpulsar.logging_utils import get_logger

from .errors import HARDWARE_STATE_ERRORS
from .widgets.common_widgets import LED_PALETTE, hex_to_color

logger = get_logger(__name__)


class DpiPanelMixin:
    def default_dpi_color(self, index):
        name, hex_value = LED_PALETTE[index % len(LED_PALETTE)]
        return hex_to_color(hex_value)

    def next_unused_dpi_color(self):
        """Return the first non-Off LED color unused by the current profile.

        This is used only while creating a new DPI stage, before the pending
        auto-apply snapshot is captured.  It must not trigger a separate
        colors apply: the new stage and its color are written together as one
        transaction.
        """
        self._ensure_dpi_stage_colors()

        used = {
            (color.r, color.g, color.b)
            for color in self.dpi_stage_colors[: self.enabled_dpi_stage_count()]
        }

        for name, hex_value in LED_PALETTE:
            color = hex_to_color(hex_value)
            if name == "Off":
                continue
            if (color.r, color.g, color.b) not in used:
                return color

        raise RuntimeError("No unused DPI LED color available")

    def is_dpi_stage_enabled(self, index):
        """Return True if a DPI stage is enabled in the profile.

        Do not use QWidget.isVisible() here: when OpenPulsar is hidden in the
        tray, every child widget becomes non-visible even though the DPI stage
        still exists. isHidden() only reflects whether the stage widget itself
        was explicitly hidden by the profile logic.
        """
        if index < 0 or index >= len(self.dpi_boxes):
            return False
        return not self.dpi_boxes[index].isHidden()

    def enabled_dpi_stage_indices(self):
        return [
            index
            for index in range(len(self.dpi_boxes))
            if self.is_dpi_stage_enabled(index)
        ]

    def enabled_dpi_stage_count(self):
        return len(self.enabled_dpi_stage_indices())

    def _ensure_dpi_stage_colors(self):
        enabled_count = self.enabled_dpi_stage_count()

        while len(self.dpi_stage_colors) < enabled_count:
            self.dpi_stage_colors.append(
                self.default_dpi_color(len(self.dpi_stage_colors))
            )

    def set_dpi_stage_color(self, stage, color):
        index = stage - 1

        logger.debug(
            "SET COLOR",
            "stage=", stage,
            "index=", index,
            "rgb=", color.r, color.g, color.b,
        )

        if index < 0 or index >= len(self.dpi_boxes):
            return

        if not self.is_dpi_stage_enabled(index):
            return

        active_stage = int(getattr(self.current_profile, "active_dpi_stage", getattr(self, "active_dpi_stage", 1))) if self.current_profile is not None else int(getattr(self, "active_dpi_stage", 1))
        if stage != active_stage:
            logger.debug(
                "Ignoring LED color edit for inactive DPI stage",
                "stage=", stage,
                "active_stage=", active_stage,
            )
            return

        self._ensure_dpi_stage_colors()

        while len(self.dpi_stage_colors) <= index:
            self.dpi_stage_colors.append(
                self.default_dpi_color(len(self.dpi_stage_colors))
            )

        self.dpi_stage_colors[index] = color

        if self.current_profile is not None and index < len(self.current_profile.dpi_stages):
            self.current_profile.dpi_stages[index].color = color

        self.update_dpi_led(index, color)

        if self.current_profile is not None:
            logger.debug("CURRENT DPI COLORS:")
            for i, s in enumerate(self.current_profile.dpi_stages):
                logger.debug(
                    i + 1,
                    s.color.r,
                    s.color.g,
                    s.color.b,
                )

        self.auto_apply("colors")


    def handle_dpi_led_click(self, stage, button):
        """Left-click behavior for a DPI LED swatch.

        First click on an inactive stage makes that DPI stage active.
        A second click on the already-active stage opens the LED color palette.
        This matches the Gen1 firmware constraint: LED colors are only edited
        reliably for the active DPI stage, while keeping the swatches visually
        unchanged.
        """
        index = stage - 1

        if index < 0 or not self.is_dpi_stage_enabled(index):
            return

        active_stage = int(getattr(self.current_profile, "active_dpi_stage", getattr(self, "active_dpi_stage", 1))) if self.current_profile is not None else int(getattr(self, "active_dpi_stage", 1))

        if stage != active_stage:
            self.set_active_dpi_stage(stage)
            return

        self.show_dpi_color_palette(
            stage,
            button.mapToGlobal(button.rect().bottomLeft()),
        )

    def choose_dpi_color(self, stage, color, menu, checked=False):
        self.set_dpi_stage_color(stage, color)
        menu.close()

    def show_dpi_color_palette(self, stage, global_pos):
        logger.debug("OPEN PALETTE FOR STAGE %s", stage)
        menu = QMenu(self)
        menu.setObjectName("dpiColorMenu")

        palette_widget = QWidget(menu)
        palette_widget.setObjectName("dpiColorPalette")

        grid = QGridLayout(palette_widget)
        grid.setContentsMargins(6, 6, 6, 6)
        grid.setSpacing(6)

        for index, (name, hex_value) in enumerate(LED_PALETTE):
            button = QPushButton()
            button.setObjectName("dpiColorChoice")
            button.setFixedSize(22, 22)
            button.setStyleSheet(f"""
                QPushButton#dpiColorChoice {{
                    background-color: {hex_value};
                    border: 1px solid #cbd5e1;
                    border-radius: 11px;
                    padding: 0;
                }}

                QPushButton#dpiColorChoice:hover {{
                    border: 2px solid #2f6cff;
                }}
            """)

            color = hex_to_color(hex_value)

            button.clicked.connect(
                partial(self.choose_dpi_color, stage, color, menu)
            )

            if name == "Off":
                row = 3
                column = 1
            else:
                row = index // 3
                column = index % 3

            grid.addWidget(button, row, column)

        action = QWidgetAction(menu)
        action.setDefaultWidget(palette_widget)
        menu.addAction(action)

        menu.exec(global_pos)

    def dpi_color_to_css(self, color):
        if isinstance(color, Color):
            return f"rgb({color.r}, {color.g}, {color.b})"

        if isinstance(color, tuple) and len(color) >= 3:
            return f"rgb({color[0]}, {color[1]}, {color[2]})"

        return "#2f6cff"

    def dpi_led_display_color(self, color):
        """Return the logical color shown in the UI swatch.

        DPI stage colors are kept as user-facing logical colors in the UI.
        Profile-local LED gains are applied only when writing to the mouse,
        and removed only when reading hardware colors back from the mouse.
        Applying the inverse correction again here can make colors look wrong
        in the UI, for example Orange turning into Yellow when green gain is
        below 100%.
        """
        return color

    def refresh_dpi_led_display_colors(self):
        self._ensure_dpi_stage_colors()
        for index in self.enabled_dpi_stage_indices():
            if index < len(self.dpi_stage_colors):
                self.update_dpi_led(index, self.dpi_stage_colors[index])

    def update_dpi_led(self, index, color):
        if index < 0 or index >= len(self.dpi_led_buttons):
            return

        css_color = self.dpi_color_to_css(self.dpi_led_display_color(color))

        self.dpi_led_buttons[index].setText("●")
        self.dpi_led_buttons[index].setStyleSheet(f"""
            QPushButton#dpiLedButton {{
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                color: {css_color};
                font-size: 17px;
                padding: 0;
            }}

            QPushButton#dpiLedButton:hover {{
                background-color: #eef4ff;
                border: 1px solid #2f6cff;
            }}
        """)

    def cycle_active_dpi_stage(self):
        self.change_active_dpi_stage_by_mode("Cycle normal")

    def change_active_dpi_stage_by_mode(self, mode):
        if self.current_profile is None:
            return

        visible_count = self.enabled_dpi_stage_count()

        if visible_count <= 0:
            return

        active_stage = int(getattr(self.current_profile, "active_dpi_stage", getattr(self, "active_dpi_stage", 1)))
        if not 1 <= active_stage <= visible_count:
            active_stage = 1

        if mode == "Incrémental":
            next_stage = min(active_stage + 1, visible_count)
        elif mode == "Décrémental":
            next_stage = max(active_stage - 1, 1)
        elif mode == "Cycle inversé":
            next_stage = active_stage - 1
            if next_stage < 1:
                next_stage = visible_count
        else:
            next_stage = active_stage + 1
            if next_stage > visible_count:
                next_stage = 1

        if next_stage == active_stage:
            return

        self.set_active_dpi_stage(next_stage)

    def change_active_dpi_value(self, delta):
        if self.current_profile is None:
            return

        active_stage = int(getattr(self.current_profile, "active_dpi_stage", getattr(self, "active_dpi_stage", 1)))
        index = active_stage - 1

        if index < 0 or index >= len(self.dpi_boxes):
            return

        box = self.dpi_boxes[index]

        if not self.is_dpi_stage_enabled(index):
            return

        value = box.value() + int(delta)
        value = max(
            self.mouse.capabilities.dpi_min,
            min(
                self.mouse.capabilities.dpi_max,
                value,
            ),
        )

        # Respecte le pas matériel de la souris.
        dpi_step = self.mouse.capabilities.dpi_step
        if dpi_step > 0:
            value = round(value / dpi_step) * dpi_step

        box.setValue(value)
        self.auto_apply("dpi")

    def change_dpi_stage(self, stage, direction):
        index = stage - 1

        if index < 0 or index >= len(self.dpi_boxes):
            return

        box = self.dpi_boxes[index]

        if not self.is_dpi_stage_enabled(index):
            return

        step = self.mouse.capabilities.dpi_step
        value = box.value() + (direction * step)

        value = max(
            self.mouse.capabilities.dpi_min,
            min(
                self.mouse.capabilities.dpi_max,
                value,
            ),
        )

        box.setValue(value)
        self.auto_apply("dpi")

    def add_dpi_stage(self):
        visible = self.enabled_dpi_stage_count()

        if visible >= self.mouse.capabilities.max_dpi_stages:
            return

        box = self.dpi_boxes[visible]

        self._ensure_dpi_stage_colors()

        if visible >= len(self.dpi_stage_colors):
            self.dpi_stage_colors.append(
                self.next_unused_dpi_color()
            )

        visible_values = [
            self.dpi_boxes[index].value()
            for index in self.enabled_dpi_stage_indices()
        ]

        if len(visible_values) >= 2:
            step = visible_values[-1] - visible_values[-2]
            if step <= 0:
                step = self.mouse.capabilities.dpi_step

            new_value = visible_values[-1] + step
        elif len(visible_values) == 1:
            new_value = visible_values[0] + 400
        else:
            new_value = 800

        dpi_step = self.mouse.capabilities.dpi_step
        dpi_min = self.mouse.capabilities.dpi_min
        dpi_max = self.mouse.capabilities.dpi_max

        new_value = max(dpi_min, min(dpi_max, new_value))
        new_value = round(new_value / dpi_step) * dpi_step

        box.setValue(new_value)
        box.show()
        self.dpi_led_buttons[visible].show()
        self.dpi_minus_buttons[visible].show()
        self.dpi_plus_buttons[visible].show()
        self.update_dpi_led(visible, self.dpi_stage_colors[visible])
        self.dpi_remove_buttons[visible].show()

        # A newly created DPI stage becomes the active stage immediately in
        # the UI, but the hardware write is still deferred by auto-apply.
        # If the user clicks + several times quickly, the flush will replay
        # the Gen1-safe sequence in order: create stage N -> activate N ->
        # write color N, for every newly created stage.
        active_stage = visible + 1
        self.active_dpi_stage = active_stage
        if self.current_profile is not None:
            self.current_profile.active_dpi_stage = active_stage
        self.update_dpi_stars(active_stage)
        self.update_tray_quick_actions()

        target_slot = self.current_slot
        if hasattr(self, "_pending_dpi_stage_base_count_by_slot"):
            self._pending_dpi_stage_base_count_by_slot.setdefault(
                target_slot,
                visible,
            )
        self.auto_apply({"dpi", "colors"})

    def remove_dpi_stage(self, stage=None):
        visible_indices = self.enabled_dpi_stage_indices()

        if len(visible_indices) <= 1:
            return

        if stage is None:
            remove_index = visible_indices[-1]
        else:
            remove_index = stage - 1

        if remove_index not in visible_indices:
            return

        current_active_stage = int(getattr(self.current_profile, "active_dpi_stage", getattr(self, "active_dpi_stage", 1)))
        current_active_index = current_active_stage - 1

        remaining_values = [
            self.dpi_boxes[index].value()
            for index in visible_indices
            if index != remove_index
        ]

        self._ensure_dpi_stage_colors()

        remaining_colors = [
            self.dpi_stage_colors[index]
            if index < len(self.dpi_stage_colors)
            else self.default_dpi_color(index)
            for index in visible_indices
            if index != remove_index
        ]

        self.dpi_stage_colors = list(remaining_colors)

        for index, box in enumerate(self.dpi_boxes):
            if index < len(remaining_values):
                box.setValue(remaining_values[index])
                box.show()
                self.dpi_led_buttons[index].show()
                self.dpi_minus_buttons[index].show()
                self.dpi_plus_buttons[index].show()

                if index < len(remaining_colors):
                    self.update_dpi_led(index, remaining_colors[index])
                else:
                    self.update_dpi_led(index, self.default_dpi_color(index))

                self.dpi_remove_buttons[index].show()
            else:
                box.hide()
                self.dpi_led_buttons[index].hide()
                self.dpi_minus_buttons[index].hide()
                self.dpi_plus_buttons[index].hide()
                self.dpi_remove_buttons[index].hide()

        if remove_index == current_active_index:
            active_stage = max(1, current_active_stage - 1)
        elif remove_index < current_active_index:
            active_stage = current_active_stage - 1
        else:
            active_stage = current_active_stage

        active_stage = max(1, min(active_stage, len(remaining_values)))

        self.active_dpi_stage = active_stage
        if self.current_profile is not None:
            self.current_profile.active_dpi_stage = active_stage

        try:
            self.mouse.set_active_dpi_stage(
                active_stage,
                self.current_slot,
            )
        except HARDWARE_STATE_ERRORS as e:
            logger.debug(f"Erreur sélection stage DPI après suppression: {e}")

        self.update_dpi_stars(active_stage)
        self.auto_apply({"dpi", "colors"})

    def sync_active_dpi_indicator(self, slot=None, allow_refresh=False):
        """Relit le stage DPI actif et met à jour le cadre bleu.

        Aucun changement artificiel de profil n'est provoqué ici. Si la souris
        ne fournit pas encore une valeur valide, l'indicateur reste neutre et
        le prochain refresh léger retentera naturellement la lecture.
        """
        if self.current_profile is None:
            return

        slot = slot or self.current_slot
        visible_count = self.enabled_dpi_stage_count()

        if visible_count <= 0:
            return

        try:
            active_stage = self.mouse.get_active_dpi_stage(slot)

            if not 1 <= active_stage <= visible_count:
                logger.debug(
                    "ACTIVE DPI INVALID:",
                    active_stage,
                    "-> wait next light refresh",
                )
                return None

            self.active_dpi_stage = active_stage
            if self.current_profile is not None and slot == self.current_slot:
                self.current_profile.active_dpi_stage = active_stage
            self.update_dpi_stars(active_stage)
            self.update_tray_quick_actions()
            return active_stage

        except HARDWARE_STATE_ERRORS as e:
            logger.debug(f"Erreur lecture stage DPI actif: {e}")
            return None

    def update_dpi_stars(self, active_stage: int):
        for index, row in enumerate(
            self.dpi_stage_rows,
            start=1,
        ):
            is_visible = self.is_dpi_stage_enabled(index - 1)
            is_active = index == active_stage and is_visible

            if not is_visible:
                row.setStyleSheet("""
                    QWidget#dpiStageRow {
                        background-color: transparent;
                        border: 2px solid transparent;
                        border-radius: 10px;
                    }
                """)
                continue

            if is_active:
                row.setStyleSheet("""
                    QWidget#dpiStageRow {
                        background-color: #f8fbff;
                        border: 2px solid #2f6cff;
                        border-radius: 10px;
                    }
                """)
            else:
                row.setStyleSheet("""
                    QWidget#dpiStageRow {
                        background-color: transparent;
                        border: 2px solid transparent;
                        border-radius: 10px;
                    }
                """)

    def set_active_dpi_stage(self, stage: int):
        if self.current_profile is None:
            return

        visible_count = self.enabled_dpi_stage_count()
        if not 1 <= stage <= visible_count:
            return

        previous_stage = getattr(self, "active_dpi_stage", 1)
        current_slot = self.current_slot

        # UI optimiste : on affiche immédiatement le choix utilisateur.
        # La souris confirme ensuite via une relecture légèrement différée.
        self.active_dpi_stage = stage
        self.current_profile.active_dpi_stage = stage
        self.update_dpi_stars(stage)
        self.update_tray_quick_actions()

        try:
            self.mouse.set_active_dpi_stage(
                stage,
                current_slot,
            )

            QTimer.singleShot(
                80,
                lambda slot=current_slot: self.sync_active_dpi_indicator(slot),
            )

        except HARDWARE_STATE_ERRORS as e:
            logger.debug(f"Erreur stage DPI actif: {e}")

            # Si la souris refuse l'écriture, l'UI revient à l'état connu.
            self.active_dpi_stage = previous_stage
            if self.current_profile is not None:
                self.current_profile.active_dpi_stage = previous_stage
            self.update_dpi_stars(previous_stage)
            self.update_tray_quick_actions()

    def on_dpi_changed(self, stage):
        if self._loading_profile or self._applying_profile:
            return

        if self.current_slot != self.active_slot:
            return

        try:
            self.sync_active_dpi_indicator(self.current_slot)
            self.update_tray_quick_actions()

        except HARDWARE_STATE_ERRORS as e:
            logger.debug(f"HIDRAW DPI EVENT FAILED: {e}")



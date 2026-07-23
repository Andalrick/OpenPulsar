"""Mouse-button mapping widgets."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QLabel,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
    QWidgetAction,
)

from ..metrics import LEFT_PANEL_WIDTH, PANEL_BODY_HEIGHT
from .common_widgets import picture_path
from .qt_delegates import ActionTreeDelegate, CenteredComboDelegate


class ActionTreeWidget(QTreeWidget):
    """Action tree that can keep its current top-level group open."""

    def __init__(self, keep_one_group_open=False, parent=None):
        super().__init__(parent)
        self._keep_one_group_open = keep_one_group_open

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if (
            self._keep_one_group_open
            and item is not None
            and item.parent() is None
            and item.isExpanded()
        ):
            return

        super().mousePressEvent(event)


class MouseButtonCombo(QComboBox):
    protectedClicked = Signal(object)
    popupAboutToShow = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._action_groups = []
        self._standalone_actions = []
        self._open_menu = None
        self._action_menu_width = None
        self._action_menu_height = 234
        self._keep_one_group_open = False

    def set_action_menu_width(self, width):
        """Keep the category popup at a stable width when the combo resizes."""
        self._action_menu_width = int(width)

    def set_action_menu_height(self, height):
        """Set a fixed popup height large enough for the biggest category."""
        self._action_menu_height = int(height)

    def set_keep_one_group_open(self, enabled):
        self._keep_one_group_open = bool(enabled)

    def set_action_groups(self, groups, placeholder=None, standalone_actions=None):
        """Configure a compact selector with expandable categories.

        Actions may be plain labels or ``(label, data)`` pairs.  The latter
        lets translated selectors keep stable internal action identifiers.
        """
        current_text = self.currentText()
        current_data = self.currentData()
        signals_were_blocked = self.blockSignals(True)
        self._action_groups = []
        self._standalone_actions = []
        self.clear()

        if placeholder is not None:
            placeholder_label, placeholder_data = placeholder
            self.addItem(placeholder_label, placeholder_data)

        for group_name, actions in groups:
            normalized_actions = []
            for action in actions:
                if isinstance(action, (tuple, list)) and len(action) == 2:
                    label, data = action
                else:
                    label = data = action

                normalized_actions.append((label, data))
                self.addItem(label, data)

            self._action_groups.append((group_name, normalized_actions))

        for action in standalone_actions or []:
            if isinstance(action, (tuple, list)) and len(action) >= 2:
                label, data = action[:2]
                is_danger = bool(action[2]) if len(action) >= 3 else False
            else:
                label = data = action
                is_danger = False

            self._standalone_actions.append((label, data, is_danger))
            self.addItem(label, data)
            if is_danger:
                self.setItemData(
                    self.count() - 1,
                    QColor("#dc2626"),
                    Qt.ForegroundRole,
                )

        if current_data is not None:
            index = self.findData(current_data)
            if index >= 0:
                self.setCurrentIndex(index)
        elif current_text:
            index = self.findText(current_text)
            if index >= 0:
                self.setCurrentIndex(index)

        self.blockSignals(signals_were_blocked)

    def is_left_click_protected(self):
        return bool(self.property("leftClickProtected"))

    def mousePressEvent(self, event):
        if self.is_left_click_protected():
            self.protectedClicked.emit(self)
            return
        super().mousePressEvent(event)

    def hidePopup(self):
        if self._open_menu is not None:
            self._open_menu.close()
            self._open_menu = None
        super().hidePopup()

    def showPopup(self):
        if self.is_left_click_protected():
            self.protectedClicked.emit(self)
            return

        self.popupAboutToShow.emit()

        if not self._action_groups:
            super().showPopup()
            return

        # Parent the popup to the top-level window rather than the scroll-area
        # combo: it stays above command rows while inheriting OpenPulsar QSS.
        menu = QMenu(self.window())
        self._open_menu = menu
        menu.setObjectName("mouseButtonActionMenu")

        tree = ActionTreeWidget(self._keep_one_group_open)
        tree.setObjectName("mouseButtonActionTree")
        tree.setHeaderHidden(True)
        tree.setRootIsDecorated(True)
        tree.setItemsExpandable(True)
        tree.setExpandsOnDoubleClick(False)
        tree.setSelectionMode(QAbstractItemView.SingleSelection)
        tree.setUniformRowHeights(True)
        tree.setIndentation(10)
        tree.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        menu_width = self._action_menu_width or max(130, self.width())
        tree.setFixedSize(menu_width, self._action_menu_height)
        tree.setItemDelegate(ActionTreeDelegate(tree))

        current_text = self.currentText()
        current_data = self.currentData()

        for group_name, actions in self._action_groups:
            group_item = QTreeWidgetItem(tree, [group_name])
            group_item.setFlags(Qt.ItemIsEnabled)

            for label, data in actions:
                action_item = QTreeWidgetItem(group_item, [label])
                action_item.setData(0, Qt.UserRole, data)

                if data == current_data or label == current_text:
                    group_item.setExpanded(True)

        for label, data, is_danger in self._standalone_actions:
            action_item = QTreeWidgetItem(tree, [label])
            action_item.setData(0, Qt.UserRole, data)
            action_item.setData(0, Qt.UserRole + 1, is_danger)
            if is_danger:
                action_item.setForeground(0, QColor("#dc2626"))

        if self._keep_one_group_open and not any(
            tree.topLevelItem(i).isExpanded()
            for i in range(tree.topLevelItemCount())
        ):
            tree.topLevelItem(0).setExpanded(True)

        def collapse_other_groups(open_item):
            for i in range(tree.topLevelItemCount()):
                group_item = tree.topLevelItem(i)
                if group_item is not open_item:
                    group_item.setExpanded(False)

        def on_item_expanded(item):
            if item.parent() is None:
                collapse_other_groups(item)

        def on_item_collapsed(item):
            if not self._keep_one_group_open or item.parent() is not None:
                return

            has_open_group = any(
                tree.topLevelItem(i).isExpanded()
                for i in range(tree.topLevelItemCount())
            )
            if not has_open_group:
                item.setExpanded(True)

        def on_item_clicked(item, _column):
            action_data = item.data(0, Qt.UserRole)

            if action_data is None:
                if self._keep_one_group_open:
                    if not item.isExpanded():
                        collapse_other_groups(item)
                        item.setExpanded(True)
                else:
                    will_open = not item.isExpanded()
                    if will_open:
                        collapse_other_groups(item)
                    item.setExpanded(will_open)
                return

            index = self.findData(action_data)
            if index >= 0:
                self.setCurrentIndex(index)
            menu.close()

        tree.itemExpanded.connect(on_item_expanded)
        tree.itemCollapsed.connect(on_item_collapsed)
        tree.itemClicked.connect(on_item_clicked)

        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(tree)
        menu.addAction(widget_action)
        popup_position = self.mapToGlobal(self.rect().bottomLeft())
        popup_position.setX(popup_position.x() - 2)
        menu.exec(popup_position)
        if self._open_menu is menu:
            self._open_menu = None


class MouseButtonEditor(QWidget):
    def __init__(
        self,
        left_combo,
        right_combo,
        middle_combo,
        back_combo,
        forward_combo,
        dpi_combo,
        parent=None,
    ):
        super().__init__(parent)
        self.setFixedSize(LEFT_PANEL_WIDTH, PANEL_BODY_HEIGHT)

        self.device_background = QLabel(self)
        self.device_background.setAlignment(Qt.AlignCenter)
        self.device_background.setGeometry(-1, 0, 340, 360)

        self.mouse_image = QLabel(self)
        self.mouse_image.setAlignment(Qt.AlignCenter)
        self.mouse_image.setGeometry(-1, 0, 340, 360)

        self._device_background_path = picture_path("Device_background.svg")
        self._mouse_pixmap_path = picture_path("Pulsar/Xlite_Wired_size2_device.svg")

        self._set_label_image(self.device_background, self._device_background_path)
        self._set_label_image(self.mouse_image, self._mouse_pixmap_path)

        self.combos = (
            left_combo,
            right_combo,
            middle_combo,
            back_combo,
            forward_combo,
            dpi_combo,
        )

        delegate = CenteredComboDelegate(self)

        for combo in self.combos:
            combo.setParent(self)
            combo.setObjectName("mouseButtonCombo")
            combo.setFixedSize(90, 16)
            combo.setMaxVisibleItems(18)
            combo.setEditable(False)
            combo.setFocusPolicy(Qt.NoFocus)
            combo.setItemDelegate(delegate)
            combo.raise_()

        middle_combo.move(125, 88)
        left_combo.move(53, 45)
        right_combo.move(195, 45)
        forward_combo.move(33, 143)
        back_combo.move(33, 188)
        dpi_combo.move(168, 200)

    def _set_label_image(self, label, path):
        pix = QPixmap(path)
        label.setPixmap(
            pix.scaled(
                340,
                360,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def set_device_image(self, path):
        self._mouse_pixmap_path = path
        self._set_label_image(self.mouse_image, self._mouse_pixmap_path)

    def set_no_device_state(self, enabled: bool):
        enabled = bool(enabled)
        self.device_background.show()
        self.device_background.lower()
        self.mouse_image.setVisible(not enabled)
        if not enabled:
            self.mouse_image.raise_()

        for combo in self.combos:
            combo.hidePopup()
            combo.setVisible(not enabled)
            if not enabled:
                combo.raise_()

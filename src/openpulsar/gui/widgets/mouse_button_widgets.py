"""Mouse-button mapping widgets."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
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
from .common_widgets import apply_openpulsar_control_effect, picture_path
from .qt_delegates import ActionTreeDelegate, CenteredComboDelegate


class MouseButtonCombo(QComboBox):
    protectedClicked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._action_groups = []
        apply_openpulsar_control_effect(self)
        self._open_menu = None

    def set_action_groups(self, groups):
        """Configure a compact selector with expandable categories."""
        current = self.currentText()
        self._action_groups = list(groups)
        self.clear()

        for _group_name, actions in self._action_groups:
            for action in actions:
                self.addItem(action)

        if current:
            index = self.findText(current)
            if index >= 0:
                self.setCurrentIndex(index)

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

        if not self._action_groups:
            super().showPopup()
            return

        menu = QMenu(self)
        self._open_menu = menu
        menu.setObjectName("mouseButtonActionMenu")

        tree = QTreeWidget()
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
        tree.setFixedSize(130, 210)
        tree.setItemDelegate(ActionTreeDelegate(tree))

        current_text = self.currentText()

        for group_name, actions in self._action_groups:
            group_item = QTreeWidgetItem(tree, [group_name])
            group_item.setFlags(Qt.ItemIsEnabled)

            for action in actions:
                action_item = QTreeWidgetItem(group_item, [action])
                action_item.setData(0, Qt.UserRole, action)

                if action == current_text:
                    group_item.setExpanded(True)

        def collapse_other_groups(open_item):
            for i in range(tree.topLevelItemCount()):
                group_item = tree.topLevelItem(i)
                if group_item is not open_item:
                    group_item.setExpanded(False)

        def on_item_expanded(item):
            if item.parent() is None:
                collapse_other_groups(item)

        def on_item_clicked(item, _column):
            action = item.data(0, Qt.UserRole)

            if action is None:
                will_open = not item.isExpanded()
                if will_open:
                    collapse_other_groups(item)
                item.setExpanded(will_open)
                return

            index = self.findText(action)
            if index >= 0:
                self.setCurrentIndex(index)
            menu.close()

        tree.itemExpanded.connect(on_item_expanded)
        tree.itemClicked.connect(on_item_clicked)

        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(tree)
        menu.addAction(widget_action)
        menu.exec(self.mapToGlobal(self.rect().bottomLeft()))
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

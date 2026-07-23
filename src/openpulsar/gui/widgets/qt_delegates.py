"""Custom Qt delegates used by OpenPulsar widgets."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QBrush, QPalette
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle

from openpulsar.gui import theme


class CenteredComboDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignCenter


class ActionTreeDelegate(QStyledItemDelegate):
    """Paint the action tree selection as one clean OpenPulsar highlight."""

    def paint(self, painter, option, index):
        option = QStyleOptionViewItem(option)
        is_action = index.data(Qt.UserRole) is not None
        is_danger = bool(index.data(Qt.UserRole + 1))
        is_selected = bool(option.state & QStyle.State_Selected)

        if is_selected and is_action:
            painter.save()
            viewport = option.widget.viewport() if option.widget else None
            width = viewport.width() if viewport is not None else option.rect.width()
            rect = option.rect
            highlight = rect.adjusted(2 - rect.x(), 1, width - rect.right() - 3, -1)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(theme.OP_BLUE_SOFT)))
            painter.drawRoundedRect(QRectF(highlight), 4, 4)
            painter.restore()

            text_color = theme.OP_DANGER_TEXT if is_danger else theme.OP_BLUE_TEXT
            option.palette.setColor(QPalette.Text, QColor(text_color))
            option.palette.setColor(QPalette.HighlightedText, QColor(text_color))
        elif is_danger:
            option.palette.setColor(QPalette.Text, QColor(theme.OP_DANGER_TEXT))
            option.palette.setColor(QPalette.HighlightedText, QColor(theme.OP_DANGER_TEXT))

        option.state &= ~QStyle.State_Selected
        super().paint(painter, option, index)

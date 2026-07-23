"""OpenPulsar-native modal dialogs.

This module replaces QMessageBox with a small frameless dialog that follows the
same geometry, typography and button hierarchy as the rest of OpenPulsar.
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..metrics import PANEL_RADIUS
from ..theme import OP_CONTROL_HEIGHT_L, OP_DANGER, OP_PILL_RADIUS


class DialogKind(str, Enum):
    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"


class OPDialog(QDialog):
    """Frameless modal dialog styled as an OpenPulsar component."""

    _ACCENTS = {
        DialogKind.INFORMATION: ("i", "#2f6cff"),
        DialogKind.WARNING: ("!", "#f59e0b"),
        DialogKind.ERROR: ("×", OP_DANGER),
        DialogKind.QUESTION: ("?", "#22a447"),
    }

    def __init__(
        self,
        parent: QWidget | None,
        *,
        title: str,
        message: str,
        kind: DialogKind = DialogKind.INFORMATION,
        primary_text: str = "OK",
        secondary_text: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("opDialog")
        self.setModal(True)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumWidth(430)

        self._drag_origin: QPoint | None = None
        self._result_primary = False

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(0)

        self.card = QFrame(self)
        self.card.setObjectName("opDialogCard")
        root.addWidget(self.card)

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 5)
        shadow.setColor(QColor(15, 23, 42, 115))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.header = QFrame(self.card)
        self.header.setObjectName("opDialogHeader")
        self.header.setFixedHeight(38)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 0, 7, 0)
        header_layout.setSpacing(8)

        glyph, accent = self._ACCENTS[kind]
        icon = QLabel(glyph, self.header)
        icon.setObjectName("opDialogIcon")
        icon.setProperty("accent", accent)
        icon.setFixedSize(22, 22)
        icon.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title, self.header)
        title_label.setObjectName("opDialogTitle")

        close_button = QPushButton("×", self.header)
        close_button.setObjectName("opDialogClose")
        close_button.setFixedSize(24, 24)
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.setFocusPolicy(Qt.NoFocus)
        close_button.clicked.connect(self.reject)

        header_layout.addWidget(icon)
        header_layout.addWidget(title_label, 1)
        header_layout.addWidget(close_button)

        body = QFrame(self.card)
        body.setObjectName("opDialogBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(18, 16, 18, 14)
        body_layout.setSpacing(16)

        message_label = QLabel(message, body)
        message_label.setObjectName("opDialogMessage")
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_label.setMinimumWidth(360)
        body_layout.addWidget(message_label)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)
        actions.addStretch()

        self.primary_button = QPushButton(primary_text, body)
        self.primary_button.setObjectName("opDialogPrimary")
        self.primary_button.setFixedHeight(OP_CONTROL_HEIGHT_L)
        self.primary_button.setMinimumWidth(92)
        self.primary_button.setCursor(Qt.PointingHandCursor)
        self.primary_button.clicked.connect(self._accept_primary)

        self.secondary_button: QPushButton | None = None
        if secondary_text:
            self.secondary_button = QPushButton(secondary_text, body)
            self.secondary_button.setObjectName("opDialogSecondary")
            self.secondary_button.setFixedHeight(OP_CONTROL_HEIGHT_L)
            self.secondary_button.setMinimumWidth(92)
            self.secondary_button.setCursor(Qt.PointingHandCursor)

        actions.addWidget(self.primary_button)
        if self.secondary_button is not None:
            self.secondary_button.clicked.connect(self.reject)
            actions.addWidget(self.secondary_button)

        body_layout.addLayout(actions)
        card_layout.addWidget(self.header)
        card_layout.addWidget(body)

        radius = PANEL_RADIUS
        button_radius = OP_PILL_RADIUS
        self.setStyleSheet(
            f"""
            QFrame#opDialogCard {{
                background: transparent;
                border: none;
            }}
            QFrame#opDialogHeader {{
                background-color: #4b5560;
                border: 1px solid #3f4852;
                border-bottom: none;
                border-top-left-radius: {radius}px;
                border-top-right-radius: {radius}px;
            }}
            QLabel#opDialogIcon {{
                background-color: {accent};
                color: #ffffff;
                border-radius: 11px;
                font-weight: 700;
                font-size: 14px;
            }}
            QLabel#opDialogTitle {{
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton#opDialogClose {{
                background-color: #ef4d5d;
                color: #34404a;
                border: none;
                border-radius: 12px;
                padding: 0;
                font-size: 20px;
                font-weight: 400;
            }}
            QPushButton#opDialogClose:hover {{
                background-color: #ff6675;
                color: #ffffff;
            }}
            QFrame#opDialogBody {{
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-top: none;
                border-bottom-left-radius: {radius}px;
                border-bottom-right-radius: {radius}px;
            }}
            QLabel#opDialogMessage {{
                color: #1f2937;
                font-family: Inter, Segoe UI, Arial;
                font-size: 12px;
            }}
            QPushButton#opDialogPrimary,
            QPushButton#opDialogSecondary {{
                min-height: {OP_CONTROL_HEIGHT_L}px;
                border-radius: {button_radius}px;
                padding: 0 14px;
                font-family: Inter, Segoe UI, Arial;
                font-size: 12px;
            }}
            QPushButton#opDialogPrimary {{
                background-color: #2f6cff;
                border: 1px solid #2f6cff;
                color: #ffffff;
                font-weight: 600;
            }}
            QPushButton#opDialogPrimary:hover {{
                background-color: #245ee8;
                border-color: #245ee8;
            }}
            QPushButton#opDialogPrimary:pressed {{
                background-color: #1d4ed8;
            }}
            QPushButton#opDialogSecondary {{
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                color: #1f2937;
            }}
            QPushButton#opDialogSecondary:hover {{
                background-color: #eef4ff;
                border-color: #2f6cff;
                color: #1d4ed8;
            }}
            """
        )

        self.primary_button.setDefault(True)
        self.primary_button.setFocus()

    def _accept_primary(self) -> None:
        self._result_primary = True
        self.accept()

    def primary_selected(self) -> bool:
        return self._result_primary

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self.header.geometry().contains(event.position().toPoint()):
            self._drag_origin = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_origin is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_origin)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    @classmethod
    def show_dialog(
        cls,
        parent: QWidget | None,
        *,
        title: str,
        message: str,
        kind: DialogKind = DialogKind.INFORMATION,
        primary_text: str = "OK",
        secondary_text: str | None = None,
    ) -> bool:
        dialog = cls(
            parent,
            title=title,
            message=message,
            kind=kind,
            primary_text=primary_text,
            secondary_text=secondary_text,
        )
        dialog.exec()
        return dialog.primary_selected()

    @classmethod
    def information(cls, parent, title: str, message: str, primary_text: str = "OK") -> bool:
        return cls.show_dialog(
            parent,
            title=title,
            message=message,
            kind=DialogKind.INFORMATION,
            primary_text=primary_text,
        )

    @classmethod
    def warning(
        cls,
        parent,
        title: str,
        message: str,
        primary_text: str = "OK",
        secondary_text: str | None = None,
    ) -> bool:
        return cls.show_dialog(
            parent,
            title=title,
            message=message,
            kind=DialogKind.WARNING,
            primary_text=primary_text,
            secondary_text=secondary_text,
        )

    @classmethod
    def error(cls, parent, title: str, message: str, primary_text: str = "OK") -> bool:
        return cls.show_dialog(
            parent,
            title=title,
            message=message,
            kind=DialogKind.ERROR,
            primary_text=primary_text,
        )

    @classmethod
    def question(
        cls,
        parent,
        title: str,
        message: str,
        primary_text: str,
        secondary_text: str,
    ) -> bool:
        return cls.show_dialog(
            parent,
            title=title,
            message=message,
            kind=DialogKind.QUESTION,
            primary_text=primary_text,
            secondary_text=secondary_text,
        )

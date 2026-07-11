from openpulsar.i18n import tr

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
)


class HelpPopup(QWidget):
    def __init__(self, title, body, parent=None):
        super().__init__(parent)

        self.setObjectName("helpPopup")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(340, 260)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("helpPopupTitle")

        close_button = QPushButton("×")
        close_button.setObjectName("helpPopupCloseButton")
        close_button.setFixedSize(22, 22)
        close_button.clicked.connect(self.close)

        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(close_button)

        body_label = QLabel(body)
        body_label.setObjectName("helpPopupBody")
        body_label.setWordWrap(True)
        body_label.setAlignment(Qt.AlignTop)
        body_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        root.addLayout(header)
        root.addWidget(body_label, 1)


class AboutPopup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("helpPopup")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedSize(520, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)

        header = QHBoxLayout()

        title = QLabel(tr("about.title"))
        title.setObjectName("helpPopupTitle")

        close_button = QPushButton("×")
        close_button.setObjectName("helpPopupCloseButton")
        close_button.setFixedSize(22, 22)
        close_button.clicked.connect(self.close)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_button)

        body = QLabel(tr("about.body"))
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignTop)

        layout.addLayout(header)
        layout.addWidget(body)


class AboutHoverButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("", parent)

        self.setObjectName("aboutHoverButton")
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

    def enterEvent(self, event):
        self.setText("?")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setText("")
        super().leaveEvent(event)

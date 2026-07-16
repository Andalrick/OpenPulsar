from importlib.metadata import PackageNotFoundError, version as package_version

from openpulsar.i18n import tr

from PySide6.QtCore import Qt, Signal
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
)

from .dpi_widgets import DpiRemoveButton


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

        close_button = DpiRemoveButton()
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
    closed = Signal()

    GITHUB_URL = "https://github.com/Andalrick/OpenPulsar"
    DISCORD_URL = "https://discord.gg/eeGT2TVW8"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("aboutPopup")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setFixedSize(528, 634)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()

        title = QLabel(tr("about.title"))
        title.setObjectName("helpPopupTitle")

        close_button = DpiRemoveButton()
        close_button.clicked.connect(self.close)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_button)

        product = QLabel("OpenPulsar")
        product.setObjectName("aboutProductName")

        try:
            current_version = package_version("openpulsar")
        except PackageNotFoundError:
            current_version = "dev"

        version = QLabel(tr("about.version").format(version=current_version))
        version.setObjectName("aboutVersion")

        body = QLabel(tr("about.body"))
        body.setObjectName("helpPopupBody")
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignTop)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse)

        links = QHBoxLayout()
        links.setSpacing(10)
        links.addStretch()

        for label, url in (
            ("GitHub", self.GITHUB_URL),
            ("Discord", self.DISCORD_URL),
        ):
            button = QPushButton(label)
            button.setObjectName("aboutLinkButton")
            button.setFixedSize(110, 30)
            button.setCursor(Qt.PointingHandCursor)
            button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(
                lambda checked=False, target=url: QDesktopServices.openUrl(QUrl(target))
            )
            links.addWidget(button)

        links.addStretch()

        layout.addLayout(header)
        layout.addWidget(product)
        layout.addWidget(version)
        layout.addWidget(body, 1)
        layout.addLayout(links)

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class AboutHoverButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("", parent)

        self.setObjectName("aboutHoverButton")
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setProperty("aboutOpen", False)

    def set_open(self, open_):
        self.setProperty("aboutOpen", bool(open_))
        self.setText("?" if open_ or self.underMouse() else "")
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def enterEvent(self, event):
        self.setText("?")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.property("aboutOpen"):
            self.setText("")
        super().leaveEvent(event)

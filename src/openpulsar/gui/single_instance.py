"""Single-instance coordination for the OpenPulsar GUI."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject
from PySide6.QtNetwork import QLocalServer, QLocalSocket


SERVER_NAME = "io.github.andalrick.OpenPulsar"
_ACTIVATE_MESSAGE = b"ACTIVATE\n"


class SingleInstanceGuard(QObject):
    """Ensure only one GUI process owns the mouse at a time.

    A later launch connects to the first process, asks it to reveal its window,
    and exits before constructing ``MainWindow`` or opening the USB device.
    """

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._handle_connections)
        self._activation_handler: Callable[[], None] | None = None
        self._activation_pending = False
        self._owns_server = False

    def acquire(self) -> bool:
        """Return ``True`` for the primary instance, otherwise notify it."""
        if self._notify_existing_instance():
            return False

        # A crashed process can leave a stale Unix-domain socket behind.
        QLocalServer.removeServer(SERVER_NAME)
        if self._server.listen(SERVER_NAME):
            self._owns_server = True
            return True

        # Another process may have won the race between our probe and listen.
        if self._notify_existing_instance(timeout_ms=500):
            return False

        raise RuntimeError(
            f"Unable to create or contact the OpenPulsar instance server: "
            f"{self._server.errorString()}"
        )

    def set_activation_handler(self, handler: Callable[[], None]) -> None:
        """Register the callback used to reveal the existing main window."""
        self._activation_handler = handler
        if self._activation_pending:
            self._activation_pending = False
            handler()

    def release(self) -> None:
        """Release the local server, notably before an application restart."""
        if not self._owns_server:
            return
        self._server.close()
        QLocalServer.removeServer(SERVER_NAME)
        self._owns_server = False

    def _notify_existing_instance(self, timeout_ms: int = 250) -> bool:
        socket = QLocalSocket(self)
        socket.connectToServer(SERVER_NAME)
        if not socket.waitForConnected(timeout_ms):
            socket.abort()
            socket.deleteLater()
            return False

        socket.write(_ACTIVATE_MESSAGE)
        socket.flush()
        socket.waitForBytesWritten(timeout_ms)
        socket.disconnectFromServer()
        socket.deleteLater()
        return True

    def _handle_connections(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            socket.readAll()
            socket.disconnectFromServer()
            socket.deleteLater()

            if self._activation_handler is None:
                self._activation_pending = True
            else:
                self._activation_handler()

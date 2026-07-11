"""Application logging helpers for OpenPulsar.

The GUI keeps its exported diagnostic report for device-level TX/RX traces.
This module handles application logs so debug prints do not leak into normal
stdout/stderr output.
"""

from __future__ import annotations

import logging
import os

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def configure_logging(level: int | str | None = None) -> None:
    """Configure root logging once.

    The default level is WARNING to keep the GUI quiet. Developers can set
    OPENPULSAR_LOG=DEBUG, INFO, WARNING, ERROR or CRITICAL.
    """
    if level is None:
        level = os.environ.get("OPENPULSAR_LOG", "WARNING")

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.WARNING)

    logging.basicConfig(level=level, format=_LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

"""Logging helpers for the application.

Provides a convenience `get_logger` factory that configures a stream and
rotating file handler for consistent logging across modules.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

_formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)

_file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
_file_handler.setFormatter(_formatter)


def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger with stream and rotating file handlers.

    Ensures a consistent logging setup across the application and avoids
    adding duplicate handlers when called multiple times.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        logger.addHandler(_stream_handler)
        logger.addHandler(_file_handler)
    return logger

"""
Configuración centralizada de logging.
- Rotación diaria, 30 días de retención
- DEBUG → archivo
- INFO+ → stderr
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
_LOG_CONFIGURED = False


def setup_logging():
    global _LOG_CONFIGURED
    if _LOG_CONFIGURED:
        return
    _LOG_CONFIGURED = True

    os.makedirs(LOGS_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    file_handler = TimedRotatingFileHandler(
        os.path.join(LOGS_DIR, "ryr.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(levelname)-8s | %(message)s",
    ))

    if not root.handlers:
        root.addHandler(file_handler)
        root.addHandler(console_handler)

    logging.getLogger("storage").setLevel(logging.DEBUG)
    logging.getLogger("utils").setLevel(logging.DEBUG)

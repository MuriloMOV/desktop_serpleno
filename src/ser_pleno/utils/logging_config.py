# -*- coding: utf-8 -*-
"""Configuração centralizada de logging para o desktop."""

import logging
import os
from logging.handlers import RotatingFileHandler

from ser_pleno.config.paths import get_project_root

LOG_DIR = os.path.join(get_project_root(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "ser_pleno_desktop.log")

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: int = logging.INFO) -> None:
    """Configura logging raiz da aplicação com handler de arquivo e console.

    Deve ser chamada uma única vez no startup (antes de qualquer log).
    """
    root = logging.getLogger()
    root.setLevel(level)

    if root.handlers:
        return

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # Arquivo rotativo (5 MB x 3 backups)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError:
        pass

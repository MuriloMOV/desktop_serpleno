# -*- coding: utf-8 -*-
"""Configuração centralizada de logging para o desktop."""

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from ser_pleno.config.paths import get_project_root

LOG_DIR = os.path.join(get_project_root(), "logs")
LOG_FILE = os.path.join(LOG_DIR, "ser_pleno_desktop.log")

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_STRUCTURED_LOG = logging.getLogger("apps.desktop.structured")


def log_event(event: str, **kwargs: Any) -> None:
    """Registra um evento estruturado no log."""
    payload: Dict[str, Any] = {"event": event}
    payload.update(kwargs)
    try:
        _STRUCTURED_LOG.info(json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        _STRUCTURED_LOG.info("%s %s", event, kwargs)


def log_login(user_id: int, username: str = "") -> None:
    log_event("login", user_id=user_id, username=username)


def log_logout(user_id: int, username: str = "") -> None:
    log_event("logout", user_id=user_id, username=username)


def log_sync_start(entity: str, count: int = 0) -> None:
    log_event("sync_start", entity=entity, count=count)


def log_sync_complete(entity: str, success: bool = True, **kwargs: Any) -> None:
    log_event("sync_complete", entity=entity, success=success, **kwargs)


def log_sync_error(entity: str, error: str, **kwargs: Any) -> None:
    log_event("sync_error", entity=entity, error=error, **kwargs)


def log_external_call(method: str, endpoint: str, status_code: int = 0, **kwargs: Any) -> None:
    log_event("external_call", method=method, endpoint=endpoint, status_code=status_code, **kwargs)


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

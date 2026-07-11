# -*- coding: utf-8 -*-
"""Metricas de ativacao de fallback offline."""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

_METRICS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "config",
    "fallback_metrics.json",
)

_lock = threading.Lock()


def _default_metrics() -> Dict[str, Any]:
    return {
        "read_fallback_total": 0,
        "write_fallback_total": 0,
        "by_repository": {},
        "last_read_fallback": None,
        "last_write_fallback": None,
        "started_at": datetime.now().isoformat(),
    }


def _load_metrics() -> Dict[str, Any]:
    if not os.path.exists(_METRICS_FILE):
        return _default_metrics()
    try:
        with open(_METRICS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _default_metrics()
        return data
    except Exception:
        return _default_metrics()


def _save_metrics(metrics: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(_METRICS_FILE), exist_ok=True)
        with open(_METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.debug("Falha ao salvar metricas de fallback: %s", exc)


def record_fallback(fallback_type: str, repository: str, method: str, entity: str = "") -> None:
    """Registra uma ativacao de fallback (read ou write)."""
    if fallback_type not in ("read", "write"):
        return
    with _lock:
        metrics = _load_metrics()
        key = f"{fallback_type}_fallback_total"
        metrics[key] = metrics.get(key, 0) + 1
        metrics[f"last_{fallback_type}_fallback"] = datetime.now().isoformat()
        repo_map = metrics.setdefault("by_repository", {})
        repo_entry = repo_map.setdefault(repository, {"total": 0, "read": 0, "write": 0, "methods": {}})
        repo_entry["total"] = repo_entry.get("total", 0) + 1
        repo_entry[fallback_type] = repo_entry.get(fallback_type, 0) + 1
        methods = repo_entry.setdefault("methods", {})
        methods[method] = methods.get(method, 0) + 1
        _save_metrics(metrics)


def get_fallback_metrics() -> Dict[str, Any]:
    """Retorna metricas atuais de fallback."""
    with _lock:
        return _load_metrics()


def reset_fallback_metrics() -> None:
    """Reseta metricas (util para testes)."""
    with _lock:
        _save_metrics(_default_metrics())

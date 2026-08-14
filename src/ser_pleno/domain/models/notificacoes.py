"""Modelos de dominio para notificacoes."""

from __future__ import annotations

from typing import Any


def _safe_str(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value)


def _safe_bool(value: Any) -> bool:
    return bool(value)


def _safe_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return fallback


def map_notification(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _safe_int(row.get("id")),
        "recipient_id": _safe_int(row.get("recipient_id")),
        "actor_id": _safe_int(row.get("actor_id")),
        "notification_type": _safe_str(row.get("notification_type"), "system"),
        "title": _safe_str(row.get("title")),
        "message": _safe_str(row.get("message")),
        "student_id": _safe_int(row.get("student_id")),
        "data": row.get("data") or {},
        "is_read": _safe_bool(row.get("is_read")),
        "created_at": _safe_str(row.get("created_at")),
    }

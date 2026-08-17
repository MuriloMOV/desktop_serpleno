# -*- coding: utf-8 -*-
"""Repositorio de audit logs."""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timedelta
from typing import Any

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    with_local_fallback,
)
from ser_pleno.infrastructure.api.api import ClienteAPI

try:
    from ser_pleno.config.operation_mode import get_operation_config
except Exception:
    get_operation_config = None  # type: ignore

import logging

logger = logging.getLogger(__name__)


class AuditLogsRepository:
    def __init__(self, auth_service=None):
        self._api = ClienteAPI(auth_service=auth_service)

    @with_local_fallback("_local_listar_logs")
    def listar_logs(self, params: dict[str, Any] | None = None):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_listar_logs(params)

        response = self._api.get("desktop/audit-logs/", params=params)
        if response.get("success"):
            data = response.get("data", {})
            if isinstance(data, dict):
                return data
            return {"results": data, "count": len(data) if isinstance(data, list) else 0}
        return self._local_listar_logs(params)

    @with_local_fallback("_local_obter_estatisticas")
    def obter_estatisticas(self, params: dict[str, Any] | None = None):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_estatisticas(params)

        response = self._api.get("desktop/audit-logs/stats/", params=params)
        if response.get("success"):
            return response.get("data", {})
        return self._local_estatisticas(params)

    def _local_listar_logs(self, params: dict[str, Any] | None = None):
        rows = []
        try:
            from ser_pleno.repositories.base import fetch_all
            query = """
                SELECT id, user_id, action, model_name, object_id, changes, ip_address, user_agent, created_at
                FROM audit_log
                WHERE 1=1
            """
            args = []
            if params:
                if params.get("user"):
                    query += " AND user_id = %s"
                    args.append(params["user"])
                if params.get("action"):
                    query += " AND action = %s"
                    args.append(params["action"])
                if params.get("model_name"):
                    query += " AND model_name = %s"
                    args.append(params["model_name"])
                if params.get("date_from"):
                    query += " AND DATE(created_at) >= %s"
                    args.append(params["date_from"])
                if params.get("date_to"):
                    query += " AND DATE(created_at) <= %s"
                    args.append(params["date_to"])
            query += " ORDER BY created_at DESC LIMIT 200"
            rows = fetch_all(query, tuple(args))
        except Exception as exc:
            logger.error("Erro ao buscar audit logs local: %s", exc)

        results = []
        for r in rows:
            results.append({
                "id": r.get("id"),
                "user": r.get("user_id"),
                "action": r.get("action"),
                "model_name": r.get("model_name"),
                "object_id": r.get("object_id"),
                "changes": r.get("changes") or {},
                "ip_address": r.get("ip_address"),
                "user_agent": r.get("user_agent"),
                "created_at": r.get("created_at").strftime("%Y-%m-%d %H:%M:%S") if hasattr(r.get("created_at"), "strftime") else str(r.get("created_at")),
            })
        return {"results": results, "count": len(results)}

    def _local_estatisticas(self, params: dict[str, Any] | None = None):
        hoje = datetime.now().date()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        try:
            from ser_pleno.repositories.base import fetch_all, fetch_one
            hoje_rows = fetch_all("SELECT action, COUNT(*) as total FROM audit_log WHERE DATE(created_at) = CURDATE() GROUP BY action")
            semana_rows = fetch_all("SELECT action, COUNT(*) as total FROM audit_log WHERE DATE(created_at) >= %s GROUP BY action", (inicio_semana.strftime("%Y-%m-%d"),))
            modelo_rows = fetch_all("SELECT model_name, COUNT(*) as total FROM audit_log GROUP BY model_name ORDER BY total DESC LIMIT 10")
            usuario_rows = fetch_all("SELECT user_id, COUNT(*) as total FROM audit_log GROUP BY user_id ORDER BY total DESC LIMIT 10")
            total_row = fetch_one("SELECT COUNT(*) as total FROM audit_log")
            total = total_row.get("total") if total_row else 0
        except Exception as exc:
            logger.error("Erro ao buscar estatisticas de audit local: %s", exc)
            return {}

        def _to_dict(rows):
            return {r.get("action") or r.get("model_name") or r.get("user_id"): r.get("total", 0) for r in rows}

        return {
            "total": total or 0,
            "today": _to_dict(hoje_rows),
            "week": _to_dict(semana_rows),
            "by_model": _to_dict(modelo_rows),
            "by_user": _to_dict(usuario_rows),
        }

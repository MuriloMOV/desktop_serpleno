# -*- coding: utf-8 -*-
"""Repositorio de alertas avancados."""

from typing import Any, Dict, List, Optional
import logging

from ser_pleno.config.operation_mode import get_operation_config
from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
)

logger = logging.getLogger(__name__)


class AlertasRepository:
    @with_local_fallback("_local_listar_alertas")
    def listar_alertas(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        config = get_operation_config()
        if config.should_use_api():
            try:
                from ser_pleno.infrastructure.api.api import ClienteAPI
                api = ClienteAPI()
                params = {}
                if filters:
                    mapping = {
                        "alert_type": "alert_type",
                        "severity": "severity",
                        "is_read": "is_read",
                        "is_resolved": "is_resolved",
                        "data_inicio": "data_inicio",
                        "data_fim": "data_fim",
                    }
                    for key, param_key in mapping.items():
                        val = filters.get(key)
                        if val is not None and val != "":
                            params[param_key] = val
                response = api.get("alerts/", params=params if params else None)
                if response.get("success"):
                    return response.get("data", [])
            except Exception as e:
                logger.error("Erro ao listar alertas via API: %s", e)

        query = "SELECT * FROM desktop_alert WHERE 1=1"
        params = []
        if filters:
            if filters.get("alert_type"):
                query += " AND alert_type = %s"
                params.append(filters["alert_type"])
            if filters.get("severity"):
                query += " AND severity = %s"
                params.append(filters["severity"])
            if filters.get("is_read") is not None:
                query += " AND is_read = %s"
                params.append(1 if filters["is_read"] else 0)
            if filters.get("is_resolved") is not None:
                query += " AND is_resolved = %s"
                params.append(1 if filters["is_resolved"] else 0)
            if filters.get("data_inicio"):
                query += " AND DATE(created_at) >= %s"
                params.append(filters["data_inicio"])
            if filters.get("data_fim"):
                query += " AND DATE(created_at) <= %s"
                params.append(filters["data_fim"])
        query += " ORDER BY created_at DESC"
        return fetch_all(query, tuple(params) if params else None)

    def _local_listar_alertas(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        rows = local_cache.list_alerts()
        if filters:
            if filters.get("alert_type"):
                rows = [r for r in rows if r.get("alert_type") == filters["alert_type"]]
            if filters.get("severity"):
                rows = [r for r in rows if r.get("severity") == filters["severity"]]
            if filters.get("is_read") is not None:
                rows = [r for r in rows if bool(r.get("is_read")) == filters["is_read"]]
            if filters.get("is_resolved") is not None:
                rows = [r for r in rows if bool(r.get("is_resolved")) == filters["is_resolved"]]
            if filters.get("data_inicio"):
                rows = [r for r in rows if (r.get("created_at") or "")[:10] >= filters["data_inicio"]]
            if filters.get("data_fim"):
                rows = [r for r in rows if (r.get("created_at") or "")[:10] <= filters["data_fim"]]
        rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return rows

    @with_local_fallback("_local_marcar_alerta_lido")
    def marcar_alerta_lido(self, alert_id: int) -> int:
        def _mysql():
            execute_non_query(
                "UPDATE desktop_alert SET is_read = 1 WHERE id = %s",
                (alert_id,),
            )
            return 1

        def _local(mysql_result):
            local_cache.update("alerts", {"is_read": 1}, "id", alert_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="alerts", entity_id=alert_id,
            queue_data_fn=lambda r, eid: {"id": alert_id, "is_read": 1},
        )

    @with_local_fallback("_local_dispensar_alerta")
    def dispensar_alerta(self, alert_id: int) -> int:
        def _mysql():
            execute_non_query(
                "UPDATE desktop_alert SET is_resolved = 1, resolved_at = NOW() WHERE id = %s",
                (alert_id,),
            )
            return 1

        def _local(mysql_result):
            local_cache.update("alerts", {"is_resolved": 1, "resolved_at": "now"}, "id", alert_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="alerts", entity_id=alert_id,
            queue_data_fn=lambda r, eid: {"id": alert_id, "is_resolved": 1},
        )

    @with_local_fallback("_local_marcar_todos_lidos")
    def marcar_todos_lidos(self) -> int:
        def _mysql():
            count = execute_non_query("UPDATE desktop_alert SET is_read = 1 WHERE is_read = 0")
            return count if count else 1

        def _local(mysql_result):
            alerts = local_cache.list_all("alerts", where_clause="is_read=0")
            for alert in alerts:
                local_cache.update("alerts", {"is_read": 1}, "id", alert.get("id"))
            return len(alerts)

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="alerts", entity_id="bulk",
            queue_data_fn=lambda r, eid: None,
        )

    def _local_marcar_alerta_lido(self, alert_id: int) -> int:
        local_cache.update("alerts", {"is_read": 1}, "id", alert_id)
        return 1

    def _local_dispensar_alerta(self, alert_id: int) -> int:
        local_cache.update("alerts", {"is_resolved": 1, "resolved_at": "now"}, "id", alert_id)
        return 1

    def _local_marcar_todos_lidos(self) -> int:
        alerts = local_cache.list_all("alerts", where_clause="is_read=0")
        for alert in alerts:
            local_cache.update("alerts", {"is_read": 1}, "id", alert.get("id"))
        return len(alerts)

    @with_local_fallback("_local_contar_nao_lidos")
    def contar_nao_lidos(self) -> int:
        query = "SELECT COUNT(*) as total FROM desktop_alert WHERE is_read = 0"
        row = fetch_one(query)
        return row.get("total", 0) if row else 0

    def _local_contar_nao_lidos(self) -> int:
        rows = local_cache.list_alerts()
        return sum(1 for r in rows if not r.get("is_read"))

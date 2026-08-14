"""Repositorio de notificacoes."""

from __future__ import annotations

import logging

from ser_pleno.config.operation_mode import get_operation_config
from ser_pleno.domain.models.notificacoes import map_notification
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.repositories.base import (
    execute_non_query,
    fetch_all,
    fetch_one,
    local_cache,
    with_local_fallback,
    write_with_fallback,
)

logger = logging.getLogger(__name__)


class NotificacoesRepository:
    @with_local_fallback("_local_listar")
    def listar(self, recipient_id: int, unread_only: bool = False) -> list[dict]:
        config = get_operation_config()
        if config.should_use_api():
            try:
                api = ClienteAPI()
                params: dict = {"recipient_id": recipient_id}
                if unread_only:
                    params["unread_only"] = "true"
                response = api.get("notifications/", params=params)
                if response.get("success"):
                    return [map_notification(r) for r in response.get("data", [])]
            except Exception as e:
                logger.error("Erro ao listar notificacoes via API: %s", e)

        query = "SELECT * FROM desktop_notification WHERE recipient_id = %s"
        params_list: list = [recipient_id]
        if unread_only:
            query += " AND is_read = 0"
        query += " ORDER BY created_at DESC"
        rows = fetch_all(query, tuple(params_list))
        return [map_notification(r) for r in rows]

    def _local_listar(self, recipient_id: int, unread_only: bool = False) -> list[dict]:
        rows = local_cache.list_notifications(recipient_id=recipient_id, unread_only=unread_only)
        rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return [map_notification(r) for r in rows]

    @with_local_fallback("_local_marcar_lida")
    def marcar_lida(self, notification_id: int) -> int:
        def _mysql():
            execute_non_query(
                "UPDATE desktop_notification SET is_read = 1 WHERE id = %s",
                (notification_id,),
            )
            return 1

        def _local(mysql_result):
            local_cache.update("notifications", {"is_read": 1}, "id", notification_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="notifications", entity_id=notification_id,
            queue_data_fn=lambda r, eid: {"id": notification_id, "is_read": 1},
        )

    @with_local_fallback("_local_marcar_todas_lidas")
    def marcar_todas_lidas(self, recipient_id: int) -> int:
        def _mysql():
            count = execute_non_query(
                "UPDATE desktop_notification SET is_read = 1 WHERE recipient_id = %s AND is_read = 0",
                (recipient_id,),
            )
            return count if count else 1

        def _local(mysql_result):
            notifications = local_cache.list_all(
                "notifications",
                where_clause="recipient_id=? AND is_read=0",
                params=(recipient_id,),
            )
            for n in notifications:
                local_cache.update("notifications", {"is_read": 1}, "id", n.get("id"))
            return len(notifications)

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="notifications", entity_id="bulk",
            queue_data_fn=lambda r, eid: None,
        )

    def _local_marcar_lida(self, notification_id: int) -> int:
        local_cache.update("notifications", {"is_read": 1}, "id", notification_id)
        return 1

    def _local_marcar_todas_lidas(self, recipient_id: int) -> int:
        notifications = local_cache.list_all(
            "notifications",
            where_clause="recipient_id=? AND is_read=0",
            params=(recipient_id,),
        )
        for n in notifications:
            local_cache.update("notifications", {"is_read": 1}, "id", n.get("id"))
        return len(notifications)

    def contar_nao_lidas(self, recipient_id: int) -> int:
        query = "SELECT COUNT(*) as total FROM desktop_notification WHERE recipient_id = %s AND is_read = 0"
        row = fetch_one(query, (recipient_id,))
        return row.get("total", 0) if row else 0

    def _local_contar_nao_lidas(self, recipient_id: int) -> int:
        rows = local_cache.list_notifications(recipient_id=recipient_id, unread_only=True)
        return len(rows)

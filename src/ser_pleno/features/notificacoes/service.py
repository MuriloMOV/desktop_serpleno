# -*- coding: utf-8 -*-
"""Service de Notificacoes — orquestrador com cache TTL."""

from __future__ import annotations

import logging

from ser_pleno.config.operation_mode import get_operation_config
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.features.notificacoes.repo import NotificacoesRepository
from ser_pleno.utils.cache import TTLCache

logger = logging.getLogger(__name__)


class ServicoNotificacoes:
    def __init__(self, auth_service=None):
        self.repo = NotificacoesRepository()
        self._api = ClienteAPI(auth_service=auth_service)
        self._auth_service = auth_service
        self._list_cache = TTLCache(ttl=30)
        self._count_cache = TTLCache(ttl=30)

    def listar(self, recipient_id: int, unread_only: bool = False) -> dict:
        cached = self._list_cache.get()
        if cached is not None and not unread_only:
            return {"success": True, "data": cached}

        config = get_operation_config()
        if config.should_use_api():
            try:
                params: dict = {"recipient_id": recipient_id}
                if unread_only:
                    params["unread_only"] = "true"
                response = self._api.get("notifications/", params=params)
                if response.get("success"):
                    data = response.get("data", [])
                    if not unread_only:
                        self._list_cache.set(data)
                    return {"success": True, "data": data}
            except Exception as e:
                logger.error("Erro ao listar notificacoes via API: %s", e)

        rows = self.repo.listar(recipient_id, unread_only=unread_only)
        if not unread_only:
            self._list_cache.set(rows)
        return {"success": True, "data": rows}

    def marcar_lida(self, notification_id: int, recipient_id: int) -> dict:
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post(f"notifications/{notification_id}/read/")
                if response.get("success"):
                    self._invalidate_caches(recipient_id)
                    return {"success": True, "message": "Notificacao marcada como lida"}
            except Exception as e:
                logger.error("Erro ao marcar notificacao como lida via API: %s", e)

        self.repo.marcar_lida(notification_id)
        self._invalidate_caches(recipient_id)
        return {"success": True, "message": "Notificacao marcada como lida"}

    def marcar_todas_lidas(self, recipient_id: int) -> dict:
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post("notifications/read-all/")
                if response.get("success"):
                    self._invalidate_caches(recipient_id)
                    return {"success": True, "message": "Todas as notificacoes marcadas como lidas"}
            except Exception as e:
                logger.error("Erro ao marcar todas notificacoes como lidas via API: %s", e)

        self.repo.marcar_todas_lidas(recipient_id)
        self._invalidate_caches(recipient_id)
        return {"success": True, "message": "Todas as notificacoes marcadas como lidas"}

    def contar_nao_lidas(self, recipient_id: int) -> dict:
        cached = self._count_cache.get()
        if cached is not None:
            return {"success": True, "data": cached}

        config = get_operation_config()
        if config.should_use_api():
            try:
                params = {"recipient_id": recipient_id, "unread_only": "true"}
                response = self._api.get("notifications/", params=params)
                if response.get("success"):
                    count = len(response.get("data", []))
                    self._count_cache.set(count)
                    return {"success": True, "data": count}
            except Exception as e:
                logger.error("Erro ao contar notificacoes nao lidas via API: %s", e)

        count = self.repo.contar_nao_lidas(recipient_id)
        self._count_cache.set(count)
        return {"success": True, "data": count}

    def _invalidate_caches(self, recipient_id: int) -> None:
        self._list_cache.invalidate()
        self._count_cache.invalidate()

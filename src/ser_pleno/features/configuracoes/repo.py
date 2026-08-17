# -*- coding: utf-8 -*-
"""Repositorio de configuracoes."""

from ser_pleno.repositories.base import (
    fetch_all,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
)
from ser_pleno.infrastructure.api.sync_service import queue_sync


class ConfiguracoesRepository:
    @with_local_fallback("_local_obter_configuracoes")
    def obter_configuracoes(self):
        return fetch_all("SELECT * FROM user_preferences")

    def _local_obter_configuracoes(self):
        return local_cache.list_user_preferences()

    def atualizar_configuracoes(self, dados):
        query = "UPDATE user_preferences SET theme = %s, notifications = %s WHERE user_id = %s"
        params = (dados['theme'], dados['notifications'], dados['user_id'])
        prefs = {
            "user_id": dados.get("user_id"),
            "theme": dados.get("theme"),
            "notifications": dados.get("notifications"),
        }

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.upsert_user_preferences(prefs)
            return 1

        def _queue_data(mysql_result, entity_id):
            return prefs

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="user_preferences", entity_id=dados.get("user_id"),
            queue_data_fn=_queue_data,
        )

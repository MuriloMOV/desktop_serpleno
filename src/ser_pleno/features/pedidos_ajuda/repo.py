# -*- coding: utf-8 -*-
"""Repositorio de Pedidos de Ajuda."""

from ser_pleno.repositories.base import (
    fetch_all,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
)
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.config.operation_mode import get_operation_config
import logging

logger = logging.getLogger(__name__)


class PedidosAjudaRepository:
    @with_local_fallback("_local_listar_pedidos_ajuda")
    def listar_pedidos_ajuda(self, status=None):
        config = get_operation_config()
        if config.should_use_api():
            try:
                api = ClienteAPI()
                params = {}
                if status:
                    params["status"] = status
                response = api.get("help-requests/", params=params if params else None)
                if response.get("success"):
                    return response.get("data", [])
            except Exception as e:
                logger.error("Erro ao listar pedidos de ajuda via API: %s", e)

        query = (
            "SELECT hr.*, a.nome as aluno_nome, a.curso as aluno_curso, a.sala as aluno_sala "
            "FROM help_requests hr "
            "LEFT JOIN students a ON hr.aluno_id = a.id "
            "WHERE 1=1"
        )
        params = []
        if status:
            query += " AND hr.status = %s"
            params.append(status)
        query += " ORDER BY hr.created_at DESC"
        return fetch_all(query, tuple(params) if params else None)

    def _local_listar_pedidos_ajuda(self, status=None):
        rows = local_cache.list_all("help_requests")
        if status:
            rows = [r for r in rows if r.get("status") == status]
        alunos = {s.get("id"): s for s in local_cache.list_all("students")}
        for r in rows:
            aluno_id = r.get("aluno_id")
            aluno = alunos.get(aluno_id, {})
            r["aluno_nome"] = aluno.get("nome", "")
            r["aluno_curso"] = aluno.get("curso", "")
            r["aluno_sala"] = aluno.get("sala", "")
        rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
        return rows

    @with_local_fallback("_local_atualizar_status")
    def atualizar_status(self, pedido_id, novo_status, notas=None):
        def _mysql():
            if notas:
                execute_non_query(
                    "UPDATE help_requests SET status = %s, dados_extras = "
                    "JSON_SET(COALESCE(dados_extras, '{}'), '$.notas', %s), "
                    "updated_at = NOW() WHERE id = %s",
                    (novo_status, notas, pedido_id),
                )
            else:
                execute_non_query(
                    "UPDATE help_requests SET status = %s, updated_at = NOW() WHERE id = %s",
                    (novo_status, pedido_id),
                )
            return 1

        def _local(mysql_result):
            local_cache.update(
                "help_requests", {"status": novo_status, "updated_at": "now"}, "id", pedido_id,
            )
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="help_requests", entity_id=pedido_id,
            queue_data_fn=lambda r, eid: {"id": pedido_id, "status": novo_status},
        )

    def _local_atualizar_status(self, pedido_id, novo_status, notas=None):
        local_cache.update(
            "help_requests", {"status": novo_status, "updated_at": "now"}, "id", pedido_id,
        )
        return 1

    @with_local_fallback("_local_responder_pedido")
    def responder_pedido(self, pedido_id, resposta, status="resolved"):
        def _mysql():
            execute_non_query(
                "UPDATE help_requests SET status = %s, dados_extras = "
                "JSON_SET(COALESCE(dados_extras, '{}'), '$.resposta', %s, "
                "'$.respondido_em', NOW()), updated_at = NOW() WHERE id = %s",
                (status, resposta, pedido_id),
            )
            return 1

        def _local(mysql_result):
            local_cache.update(
                "help_requests", {"status": status, "updated_at": "now"}, "id", pedido_id,
            )
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="help_requests", entity_id=pedido_id,
            queue_data_fn=lambda r, eid: {"id": pedido_id, "status": status, "resposta": resposta},
        )

    def _local_responder_pedido(self, pedido_id, resposta, status="resolved"):
        local_cache.update(
            "help_requests", {"status": status, "updated_at": "now"}, "id", pedido_id,
        )
        return 1

    def contar_por_status(self, status):
        config = get_operation_config()
        if config.should_use_api():
            try:
                api = ClienteAPI()
                response = api.get("help-requests/", params={"status": status})
                if response.get("success"):
                    return len(response.get("data", []))
            except Exception as e:
                logger.error("Erro ao contar pedidos via API: %s", e)

        rows = self.listar_pedidos_ajuda(status=status)
        return len(rows) if rows else 0

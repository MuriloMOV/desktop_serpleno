# -*- coding: utf-8 -*-
"""Service de Pedidos de Ajuda — orquestrador."""

from ser_pleno.repositories.pedidos_ajuda import PedidosAjudaRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.config.operation_mode import get_operation_config
import logging

logger = logging.getLogger(__name__)


def _safe_str(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value)


def _safe_bool(value) -> bool:
    return bool(value)


def _map_help_request(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "type": row.get("tipo") or row.get("type") or "",
        "message": row.get("mensagem") or row.get("message") or "",
        "priority": row.get("prioridade") or row.get("priority") or "",
        "status": row.get("status") or "",
        "location": row.get("localizacao") or row.get("location") or "",
        "extra_data": row.get("dados_extras") or row.get("extra_data") or {},
        "created_at": _safe_str(row.get("created_at")),
        "viewed_at": _safe_str(row.get("viewed_at")),
        "resolved_at": _safe_str(row.get("resolved_at")),
        "student_id": row.get("aluno_id") or row.get("student_id"),
        "student_name": row.get("aluno_nome") or row.get("student_name") or "",
        "student_course": row.get("aluno_curso") or row.get("student_course") or "",
        "student_class": row.get("aluno_sala") or row.get("student_class") or "",
    }


class ServicoPedidosAjuda:
    def __init__(self, auth_service=None):
        self.repo = PedidosAjudaRepository()
        self._api = ClienteAPI(auth_service=auth_service)
        self._auth_service = auth_service

    def listar_pedidos(self, status=None):
        config = get_operation_config()
        if config.should_use_api():
            try:
                params = {}
                if status:
                    params["status"] = status
                response = self._api.get("help-requests/", params=params if params else None)
                if response.get("success"):
                    return {"success": True, "data": [_map_help_request(r) for r in response.get("data", [])]}
            except Exception as e:
                logger.error("Erro ao listar pedidos de ajuda via API: %s", e)

        rows = self.repo.listar_pedidos_ajuda(status=status)
        return {"success": True, "data": [_map_help_request(r) for r in rows]}

    def listar_pendentes(self):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.get("help-requests/pendentes/")
                if response.get("success"):
                    return {"success": True, "data": [_map_help_request(r) for r in response.get("data", [])]}
            except Exception as e:
                logger.error("Erro ao listar pendentes via API: %s", e)

        rows = self.repo.listar_pedidos_ajuda(status="pending")
        return {"success": True, "data": [_map_help_request(r) for r in rows]}

    def marcar_visto(self, pedido_id):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post(f"help-requests/{pedido_id}/update/", json={"status": "viewed"})
                if response.get("success"):
                    return {"success": True, "message": "Pedido marcado como visto"}
            except Exception as e:
                logger.error("Erro ao marcar pedido como visto via API: %s", e)

        self.repo.atualizar_status(pedido_id, "viewed")
        return {"success": True, "message": "Pedido marcado como visto"}

    def iniciar_atendimento(self, pedido_id):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post(f"help-requests/{pedido_id}/update/", json={"status": "in_progress"})
                if response.get("success"):
                    return {"success": True, "message": "Atendimento iniciado"}
            except Exception as e:
                logger.error("Erro ao iniciar atendimento via API: %s", e)

        self.repo.atualizar_status(pedido_id, "in_progress")
        return {"success": True, "message": "Atendimento iniciado"}

    def resolver_pedido(self, pedido_id):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post(f"help-requests/{pedido_id}/update/", json={"status": "resolved"})
                if response.get("success"):
                    return {"success": True, "message": "Pedido resolvido"}
            except Exception as e:
                logger.error("Erro ao resolver pedido via API: %s", e)

        self.repo.atualizar_status(pedido_id, "resolved")
        return {"success": True, "message": "Pedido resolvido"}

    def responder_pedido(self, pedido_id, resposta):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post(f"help-requests/{pedido_id}/respond/", json={"response": resposta, "status": "resolved"})
                if response.get("success"):
                    return {"success": True, "message": "Resposta enviada"}
            except Exception as e:
                logger.error("Erro ao responder pedido via API: %s", e)

        self.repo.responder_pedido(pedido_id, resposta, status="resolved")
        return {"success": True, "message": "Resposta enviada"}

    def contar_pendentes(self):
        return self.repo.contar_por_status("pending")

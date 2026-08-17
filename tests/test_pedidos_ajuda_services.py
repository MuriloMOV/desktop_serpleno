# -*- coding: utf-8 -*-
"""Testes de services — Pedidos de Ajuda."""

import pytest
from unittest.mock import MagicMock, patch

from ser_pleno.features.pedidos_ajuda.service import ServicoPedidosAjuda, _map_help_request


class TestMapHelpRequest:
    def test_map_completo(self):
        row = {
            "id": 1,
            "tipo": "suporte",
            "mensagem": "Preciso de ajuda",
            "prioridade": "alta",
            "status": "pending",
            "localizacao": "Sala 1",
            "dados_extras": {"resposta": "Ok", "notas": "Teste"},
            "created_at": "2026-01-01 10:00:00",
            "viewed_at": "2026-01-01 10:05:00",
            "resolved_at": None,
            "aluno_id": 5,
        }
        result = _map_help_request(row)
        assert result["id"] == 1
        assert result["type"] == "suporte"
        assert result["message"] == "Preciso de ajuda"
        assert result["priority"] == "alta"
        assert result["status"] == "pending"
        assert result["location"] == "Sala 1"
        assert result["extra_data"] == {"resposta": "Ok", "notas": "Teste"}
        assert result["created_at"] == "2026-01-01 10:00:00"
        assert result["viewed_at"] == "2026-01-01 10:05:00"
        assert result["resolved_at"] == ""
        assert result["student_id"] == 5

    def test_map_com_alias_api(self):
        row = {
            "id": 2,
            "type": "duvida",
            "message": "Dúvida",
            "priority": "media",
            "status": "resolved",
            "location": "",
            "extra_data": {},
            "created_at": "2026-01-01 09:00:00",
            "viewed_at": None,
            "resolved_at": "2026-01-01 10:00:00",
            "student_id": 3,
        }
        result = _map_help_request(row)
        assert result["type"] == "duvida"
        assert result["message"] == "Dúvida"
        assert result["resolved_at"] == "2026-01-01 10:00:00"

    def test_map_valores_none(self):
        row = {
            "id": 3,
            "tipo": None,
            "mensagem": None,
            "prioridade": None,
            "status": None,
            "localizacao": None,
            "dados_extras": None,
            "created_at": None,
            "viewed_at": None,
            "resolved_at": None,
            "aluno_id": None,
        }
        result = _map_help_request(row)
        assert result["type"] == ""
        assert result["message"] == ""
        assert result["priority"] == ""
        assert result["status"] == ""
        assert result["location"] == ""
        assert result["extra_data"] == {}
        assert result["created_at"] == ""
        assert result["student_id"] is None


class TestServicoPedidosAjuda:
    @patch("ser_pleno.features.pedidos_ajuda.service.get_operation_config")
    def test_listar_pedidos_local(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.should_use_api.return_value = False
        mock_get_config.return_value = mock_config

        service = ServicoPedidosAjuda()
        mock_repo = MagicMock()
        mock_repo.listar_pedidos_ajuda.return_value = [
            {"id": 1, "tipo": "suporte", "status": "pending", "mensagem": "Ajuda", "prioridade": "alta", "localizacao": "", "dados_extras": {}, "created_at": "2026-01-01 10:00:00", "viewed_at": None, "resolved_at": None, "aluno_id": 1, "updated_at": None},
        ]
        service.repo = mock_repo

        result = service.listar_pedidos()
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["type"] == "suporte"

    @patch("ser_pleno.features.pedidos_ajuda.service.get_operation_config")
    def test_listar_pedidos_com_filtro(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.should_use_api.return_value = False
        mock_get_config.return_value = mock_config

        service = ServicoPedidosAjuda()
        mock_repo = MagicMock()
        mock_repo.listar_pedidos_ajuda.return_value = []
        service.repo = mock_repo

        result = service.listar_pedidos(status="pending")
        assert result["success"] is True
        mock_repo.listar_pedidos_ajuda.assert_called_once_with(status="pending")

    @patch("ser_pleno.features.pedidos_ajuda.service.get_operation_config")
    def test_marcar_visto_local(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.should_use_api.return_value = False
        mock_get_config.return_value = mock_config

        service = ServicoPedidosAjuda()
        mock_repo = MagicMock()
        mock_repo.atualizar_status.return_value = 1
        service.repo = mock_repo

        result = service.marcar_visto(1)
        assert result["success"] is True
        assert result["message"] == "Pedido marcado como visto"
        mock_repo.atualizar_status.assert_called_once_with(1, "viewed")

    @patch("ser_pleno.features.pedidos_ajuda.service.get_operation_config")
    def test_iniciar_atendimento_local(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.should_use_api.return_value = False
        mock_get_config.return_value = mock_config

        service = ServicoPedidosAjuda()
        mock_repo = MagicMock()
        mock_repo.atualizar_status.return_value = 1
        service.repo = mock_repo

        result = service.iniciar_atendimento(1)
        assert result["success"] is True
        assert result["message"] == "Atendimento iniciado"
        mock_repo.atualizar_status.assert_called_once_with(1, "in_progress")

    @patch("ser_pleno.features.pedidos_ajuda.service.get_operation_config")
    def test_resolver_pedido_local(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.should_use_api.return_value = False
        mock_get_config.return_value = mock_config

        service = ServicoPedidosAjuda()
        mock_repo = MagicMock()
        mock_repo.atualizar_status.return_value = 1
        service.repo = mock_repo

        result = service.resolver_pedido(1)
        assert result["success"] is True
        assert result["message"] == "Pedido resolvido"
        mock_repo.atualizar_status.assert_called_once_with(1, "resolved")

    @patch("ser_pleno.features.pedidos_ajuda.service.get_operation_config")
    def test_responder_pedido_local(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.should_use_api.return_value = False
        mock_get_config.return_value = mock_config

        service = ServicoPedidosAjuda()
        mock_repo = MagicMock()
        mock_repo.responder_pedido.return_value = 1
        service.repo = mock_repo

        result = service.responder_pedido(1, "Minha resposta")
        assert result["success"] is True
        assert result["message"] == "Resposta enviada"
        mock_repo.responder_pedido.assert_called_once_with(1, "Minha resposta", status="resolved")

    @patch("ser_pleno.features.pedidos_ajuda.service.get_operation_config")
    def test_contar_pendentes(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.should_use_api.return_value = False
        mock_get_config.return_value = mock_config

        service = ServicoPedidosAjuda()
        mock_repo = MagicMock()
        mock_repo.contar_por_status.return_value = 3
        service.repo = mock_repo

        result = service.contar_pendentes()
        assert result == 3
        mock_repo.contar_por_status.assert_called_once_with("pending")

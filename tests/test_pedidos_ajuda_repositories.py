# -*- coding: utf-8 -*-
"""Testes de repositories — Pedidos de Ajuda."""

import pytest
from unittest.mock import MagicMock, patch

from ser_pleno.repositories.pedidos_ajuda import PedidosAjudaRepository


class TestPedidosAjudaRepository:
    @patch("ser_pleno.repositories.pedidos_ajuda.fetch_all")
    def test_listar_pedidos_ajuda_sem_filtro(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "tipo": "suporte", "status": "pending", "mensagem": "Ajuda 1", "prioridade": "alta", "dados_extras": {}, "created_at": "2026-01-01 10:00:00", "viewed_at": None, "resolved_at": None, "aluno_id": 1, "updated_at": None},
            {"id": 2, "tipo": "duvida", "status": "resolved", "mensagem": "Ajuda 2", "prioridade": "media", "dados_extras": {}, "created_at": "2026-01-01 09:00:00", "viewed_at": "2026-01-01 09:30:00", "resolved_at": "2026-01-01 10:00:00", "aluno_id": 2, "updated_at": None},
        ]
        with patch("ser_pleno.repositories.pedidos_ajuda.get_operation_config") as mock_cfg:
            mock_cfg.return_value.should_use_api.return_value = False
            repo = PedidosAjudaRepository()
            result = repo.listar_pedidos_ajuda()
        assert len(result) == 2
        assert result[0]["id"] == 1
        mock_fetch_all.assert_called_once()

    @patch("ser_pleno.repositories.pedidos_ajuda.fetch_all")
    def test_listar_pedidos_ajuda_com_filtro_status(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id": 1, "tipo": "suporte", "status": "pending", "mensagem": "Ajuda 1", "prioridade": "alta", "dados_extras": {}, "created_at": "2026-01-01 10:00:00", "viewed_at": None, "resolved_at": None, "aluno_id": 1, "updated_at": None},
        ]
        with patch("ser_pleno.repositories.pedidos_ajuda.get_operation_config") as mock_cfg:
            mock_cfg.return_value.should_use_api.return_value = False
            repo = PedidosAjudaRepository()
            result = repo.listar_pedidos_ajuda(status="pending")
        assert len(result) == 1
        assert result[0]["status"] == "pending"
        mock_fetch_all.assert_called_once()

    @patch("ser_pleno.repositories.pedidos_ajuda.write_with_fallback")
    def test_atualizar_status(self, mock_write):
        mock_write.return_value = 1
        repo = PedidosAjudaRepository()
        result = repo.atualizar_status(1, "viewed")
        assert result == 1
        mock_write.assert_called_once()

    @patch("ser_pleno.repositories.pedidos_ajuda.write_with_fallback")
    def test_atualizar_status_com_notas(self, mock_write):
        mock_write.return_value = 1
        repo = PedidosAjudaRepository()
        result = repo.atualizar_status(1, "in_progress", notas="Em atendimento")
        assert result == 1
        mock_write.assert_called_once()

    @patch("ser_pleno.repositories.pedidos_ajuda.write_with_fallback")
    def test_responder_pedido(self, mock_write):
        mock_write.return_value = 1
        repo = PedidosAjudaRepository()
        result = repo.responder_pedido(1, "Resposta teste", status="resolved")
        assert result == 1
        mock_write.assert_called_once()

    @patch("ser_pleno.repositories.pedidos_ajuda.PedidosAjudaRepository.listar_pedidos_ajuda")
    def test_contar_por_status(self, mock_listar):
        mock_listar.return_value = [
            {"id": 1, "status": "pending"},
            {"id": 2, "status": "pending"},
        ]
        with patch("ser_pleno.repositories.pedidos_ajuda.get_operation_config") as mock_cfg:
            mock_cfg.return_value.should_use_api.return_value = False
            repo = PedidosAjudaRepository()
            result = repo.contar_por_status("pending")
        assert result == 2
        mock_listar.assert_called_once_with(status="pending")

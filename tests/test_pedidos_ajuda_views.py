# -*- coding: utf-8 -*-
"""Testes de views — Pedidos de Ajuda."""

import pytest
from unittest.mock import MagicMock, patch
import customtkinter as ctk

from ser_pleno.presentation.views.pedidos_ajuda import PedidosAjudaFrame, ResponderModal


class TestPedidosAjudaFrame:
    def test_inicializacao(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        assert view is not None
        assert hasattr(view, "controller")
        assert hasattr(view, "pedidos")
        assert hasattr(view, "_filtro_status")
        assert hasattr(view, "_cards_container")
        assert hasattr(view, "seg_status")
        assert hasattr(view, "status_lbl")
        assert hasattr(view, "notificacao_lbl")

    def test_get_status_filtro_todos(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        view._filtro_status = "Todos"
        assert view._get_status_filtro() is None

    def test_get_status_filtro_pending(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        view._filtro_status = "pending"
        assert view._get_status_filtro() == "pending"

    def test_parse_pedidos_dict_com_data(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        res = {"success": True, "data": [{"id": 1, "status": "pending"}]}
        result = view._parse_pedidos(res)
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_parse_pedidos_dict_success_false(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        res = {"success": False, "message": "Erro"}
        result = view._parse_pedidos(res)
        assert result == []

    def test_parse_pedidos_lista(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        res = [{"id": 1}, {"id": 2}]
        result = view._parse_pedidos(res)
        assert len(result) == 2

    def test_parse_pedidos_dict_single(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        res = {"id": 1, "status": "pending"}
        result = view._parse_pedidos(res)
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_parse_pedidos_invalido(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        result = view._parse_pedidos("invalido")
        assert result == []

    def test_on_mudar_filtro(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        view.carregar_pedidos_async = MagicMock()
        view._on_mudar_filtro(2)
        assert view._filtro_status == "viewed"
        view.carregar_pedidos_async.assert_called_once()

    def test_load_data(self, app, controller):
        view = PedidosAjudaFrame(app, controller)
        view.carregar_pedidos_async = MagicMock()
        view.load_data()
        view.carregar_pedidos_async.assert_called_once()

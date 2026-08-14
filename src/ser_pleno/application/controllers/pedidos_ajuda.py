# -*- coding: utf-8 -*-
"""Controller de Pedidos de Ajuda — medicao entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.pedidos_ajuda import ServicoPedidosAjuda


class PedidosAjudaController(BaseController):
    """Coordena as requisicoes da View de Pedidos de Ajuda."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoPedidosAjuda, auth_service=auth_service)
        self.app = app
        self.usuario_logado = getattr(app, "usuario_logado", None) if app else None
        self.usuario_logado_id = getattr(app, "usuario_logado_id", None) if app else None

    def get_service(self):
        return self._service

    def listar_pedidos(self, status=None):
        """Lista pedidos de ajuda."""
        return self._service.listar_pedidos(status=status)

    def listar_pendentes(self):
        """Lista apenas pedidos pendentes."""
        return self._service.listar_pendentes()

    def marcar_visto(self, pedido_id):
        """Marca um pedido como visto."""
        return self._service.marcar_visto(pedido_id)

    def iniciar_atendimento(self, pedido_id):
        """Inicia o atendimento de um pedido."""
        return self._service.iniciar_atendimento(pedido_id)

    def resolver_pedido(self, pedido_id):
        """Resolve um pedido."""
        return self._service.resolver_pedido(pedido_id)

    def responder_pedido(self, pedido_id, resposta):
        """Responde a um pedido de ajuda."""
        return self._service.responder_pedido(pedido_id, resposta)

    def contar_pendentes(self):
        """Conta pedidos pendentes."""
        return self._service.contar_pendentes()

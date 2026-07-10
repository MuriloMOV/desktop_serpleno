# -*- coding: utf-8 -*-
"""Controller de Dashboard — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.dashboard import ServicoDashboard


class DashboardController(BaseController):
    """Coordena as requisições da View de Dashboard."""

    def __init__(self):
        super().__init__(ServicoDashboard)

    def get_service(self):
        return self._service

    def carregar_kpis(self):
        """Carrega KPIs do dashboard."""
        return self._service.obter_kpis()

    def obter_notificacoes_ajuda(self):
        """Obtém notificações de ajuda."""
        return self._service.obter_notificacoes_ajuda()

    def obter_notificacoes_alertas(self):
        """Obtém notificações de alertas."""
        return self._service.obter_notificacoes_alertas()

    def marcar_notificacao_como_lida(self, notificacao_id, tipo="alerta"):
        """Marca uma notificação como lida."""
        self._service.marcar_notificacao_como_lida(notificacao_id, tipo)

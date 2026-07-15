# -*- coding: utf-8 -*-
"""Controller de Dashboard — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.dashboard import ServicoDashboard


class DashboardController(BaseController):
    """Coordena as requisições da View de Dashboard."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoDashboard, auth_service=auth_service)
        self.app = app
        self.usuario_logado = getattr(app, "usuario_logado", None) if app else None
        self.usuario_logado_id = getattr(app, "usuario_logado_id", None) if app else None

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

    def mostrar_login(self):
        """Abre a tela de login."""
        if self.app:
            return self.app.mostrar_login()

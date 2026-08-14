# -*- coding: utf-8 -*-
"""Controller de Alertas Avancados — medicao entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.alertas import ServicoAlertas


class AlertasController(BaseController):
    """Coordena as requisicoes da View de Alertas Avancados."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoAlertas, auth_service=auth_service)
        self.app = app
        self.usuario_logado = getattr(app, "usuario_logado", None) if app else None
        self.usuario_logado_id = getattr(app, "usuario_logado_id", None) if app else None

    def get_service(self):
        return self._service

    def listar_alertas(self, filters=None):
        return self._service.listar_alertas(filters)

    def get_alertas_criticos(self):
        return self._service.get_alertas_criticos()

    def marcar_alerta_lido(self, alert_id):
        return self._service.marcar_alerta_lido(alert_id)

    def dispensar_alerta(self, alert_id):
        return self._service.dispensar_alerta(alert_id)

    def marcar_todos_lidos(self):
        return self._service.marcar_todos_lidos()

    def contar_nao_lidos(self):
        return self._service.contar_nao_lidos()

# -*- coding: utf-8 -*-
"""Controller de Audit Logs — mediacao entre View e Services."""

from __future__ import annotations

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.audit_logs import ServicoAuditLogs


class AuditLogsController(BaseController):
    """Coordena as requisicoes da View de Audit Logs."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoAuditLogs, auth_service=auth_service)
        self.app = app
        self.usuario_logado = getattr(app, "usuario_logado", None) if app else None
        self.usuario_logado_id = getattr(app, "usuario_logado_id", None) if app else None

    def get_service(self):
        return self._service

    def listar_logs(self, filtros: dict | None = None):
        return self._service.listar_logs(filtros)

    def obter_estatisticas(self, filtros: dict | None = None):
        return self._service.obter_estatisticas(filtros)

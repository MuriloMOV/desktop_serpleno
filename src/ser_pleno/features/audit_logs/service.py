# -*- coding: utf-8 -*-
"""Servico de audit logs."""

from __future__ import annotations

import logging

from ser_pleno.features.audit_logs.repo import AuditLogsRepository

logger = logging.getLogger(__name__)


class ServicoAuditLogs:
    def __init__(self, auth_service=None):
        self.repo = AuditLogsRepository(auth_service=auth_service)

    def listar_logs(self, filtros: dict | None = None):
        return self.repo.listar_logs(filtros)

    def obter_estatisticas(self, filtros: dict | None = None):
        return self.repo.obter_estatisticas(filtros)

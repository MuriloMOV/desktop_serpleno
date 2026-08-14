# -*- coding: utf-8 -*-
"""Controller de Analytics — mediacao entre View e Services."""

from __future__ import annotations

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.analytics import ServicoAnalytics


class AnalyticsController(BaseController):
    """Coordena as requisicoes da View de Analytics."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoAnalytics, auth_service=auth_service)
        self.app = app
        self.usuario_logado = getattr(app, "usuario_logado", None) if app else None
        self.usuario_logado_id = getattr(app, "usuario_logado_id", None) if app else None

    def get_service(self):
        return self._service

    def carregar_estatisticas(self):
        return self._service.obter_estatisticas_dashboard()

    def carregar_tendencias(self, metric: str = "mood", days: int = 30):
        return self._service.obter_tendencias(metric, days)

    def carregar_performance(self):
        return self._service.obter_performance()

    def buscar_global(self, query: str):
        return self._service.buscar_global(query)

    def carregar_quick_actions(self):
        return self._service.obter_quick_actions()

    def carregar_mood_timeline(self, student_id: int = None, days: int = 30):
        return self._service.obter_mood_timeline(student_id=student_id, days=days)

    def carregar_wellness_distribution(self):
        return self._service.obter_wellness_distribution()

    def carregar_risk_overview(self):
        return self._service.obter_risk_overview()

    def carregar_dados_estudante(self, student_id: int):
        return self._service.obter_dados_estudante(student_id)

    def carregar_engagement_stats(self):
        return self._service.obter_engagement_stats()

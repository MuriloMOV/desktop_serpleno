# -*- coding: utf-8 -*-
"""Servico de analytics e tendencias."""

from __future__ import annotations

import logging

from ser_pleno.repositories.analytics import AnalyticsRepository
from ser_pleno.infrastructure.api.api import ClienteAPI

logger = logging.getLogger(__name__)


class ServicoAnalytics:
    def __init__(self, auth_service=None):
        self.repo = AnalyticsRepository(auth_service=auth_service)
        self._api = ClienteAPI(auth_service=auth_service)

    def obter_estatisticas_dashboard(self):
        return self.repo.obter_estatisticas_dashboard()

    def obter_tendencias(self, metric: str = "mood", days: int = 30):
        return self.repo.obter_tendencias(metric, days)

    def obter_performance(self):
        return self.repo.obter_performance()

    def buscar_global(self, query: str):
        return self.repo.buscar_global(query)

    def obter_quick_actions(self):
        return self.repo.obter_quick_actions()

    def obter_mood_timeline(self, student_id: int = None, days: int = 30):
        try:
            params = {"days": days}
            if student_id:
                params["student_id"] = student_id
            response = self._api.get("serpleno/mood-timeline/", params=params)
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", [])}
        except Exception as e:
            logger.error(f"Erro ao obter mood timeline: {e}")
            return {"success": False, "message": str(e)}

    def obter_wellness_distribution(self):
        try:
            response = self._api.get("serpleno/wellness/")
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", {})}
        except Exception as e:
            logger.error(f"Erro ao obter wellness distribution: {e}")
            return {"success": False, "message": str(e)}

    def obter_risk_overview(self):
        try:
            response = self._api.get("serpleno/risk-overview/")
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", {})}
        except Exception as e:
            logger.error(f"Erro ao obter risk overview: {e}")
            return {"success": False, "message": str(e)}

    def obter_dados_estudante(self, student_id: int):
        try:
            response = self._api.get(f"serpleno/student/{student_id}/")
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", {})}
        except Exception as e:
            logger.error(f"Erro ao obter dados do estudante: {e}")
            return {"success": False, "message": str(e)}

    def obter_engagement_stats(self):
        try:
            response = self._api.get("serpleno/engagement/")
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", {})}
        except Exception as e:
            logger.error(f"Erro ao obter engagement stats: {e}")
            return {"success": False, "message": str(e)}

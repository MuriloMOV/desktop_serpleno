"""Servico de analytics e tendencias."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from ser_pleno.features.analytics.repo import AnalyticsRepository
from ser_pleno.infrastructure.api.api import ClienteAPI

logger = logging.getLogger(__name__)


class ServicoAnalytics:
    def __init__(self, auth_service=None):
        self.repo = AnalyticsRepository(auth_service=auth_service)
        self._auth_service = auth_service
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
            params: dict[str, Any] = {"days": days}
            if student_id is not None:
                params["student_id"] = student_id
            response = self._api.get("serpleno/mood-timeline/", params=params)
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", [])}
        except Exception as exc:
            logger.error("Erro ao obter mood timeline: %s", exc)
            return {"success": False, "message": str(exc)}

    def obter_wellness_distribution(self):
        try:
            response = self._api.get("serpleno/wellness/")
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", {})}
        except Exception as exc:
            logger.error("Erro ao obter wellness distribution: %s", exc)
            return {"success": False, "message": str(exc)}

    def obter_risk_overview(self):
        try:
            response = self._api.get("serpleno/risk-overview/")
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", {})}
        except Exception as exc:
            logger.error("Erro ao obter risk overview: %s", exc)
            return {"success": False, "message": str(exc)}

    def obter_dados_estudante(self, student_id: int):
        try:
            response = self._api.get(f"serpleno/student/{student_id}/")
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", {})}
        except Exception as exc:
            logger.error("Erro ao obter dados do estudante: %s", exc)
            return {"success": False, "message": str(exc)}

    def obter_engagement_stats(self):
        try:
            response = self._api.get("serpleno/engagement/")
            if response.get("success"):
                return response
            return {"success": True, "data": response.get("data", {})}
        except Exception as exc:
            logger.error("Erro ao obter engagement stats: %s", exc)
            return {"success": False, "message": str(exc)}

    def calculate_dashboard_stats(
        self,
        student_id: int,
        date_range: tuple[date, date] | None = None,
    ) -> dict[str, Any]:
        try:
            if date_range is not None:
                start, end = date_range
                params: dict[str, Any] = {"start": start.isoformat(), "end": end.isoformat()}
                response = self._api.get(f"analytics/dashboard/{student_id}/", params=params)
            else:
                response = self._api.get(f"analytics/dashboard/{student_id}/")
            if response.get("success"):
                return response.get("data", {})
            return {}
        except Exception as exc:
            logger.error("Erro ao calcular dashboard stats: %s", exc)
            return {}

    def calculate_trend_stats(
        self,
        data: list[dict[str, Any]],
        period_type: str = "daily",
    ) -> dict[str, Any]:
        if not data:
            return {"labels": [], "values": [], "trend": "neutral", "change": 0.0}
        values: list[float] = []
        labels: list[str] = []
        if period_type == "weekly" and len(data) > 7:
            step = max(1, len(data) // 7)
            data = data[::step]
        if period_type == "monthly" and len(data) > 30:
            step = max(1, len(data) // 30)
            data = data[::step]
        for item in data:
            val = item.get("value") or item.get("media_humor") or item.get("count") or 0
            values.append(float(val))
            labels.append(str(item.get("data") or item.get("date") or item.get("label", "")))
        if len(values) < 2:
            change = 0.0
        else:
            first = values[0] if values[0] != 0 else 0.1
            change = round(((values[-1] - values[0]) / first) * 100, 2)
        trend = "up" if change > 5 else "down" if change < -5 else "neutral"
        return {"labels": labels, "values": values, "trend": trend, "change": change}

    def calculate_performance_stats(self) -> dict[str, Any]:
        try:
            data = self.repo.obter_performance() or {}
            if isinstance(data, dict):
                return data
            return {}
        except Exception as exc:
            logger.error("Erro ao calcular performance stats: %s", exc)
            return {}

    def search_students(self, query: str) -> list[dict[str, Any]]:
        try:
            result = self.repo.buscar_global(query) or {}
            students = result.get("students", []) if isinstance(result, dict) else []
            return students[:50]
        except Exception as exc:
            logger.error("Erro ao buscar estudantes: %s", exc)
            return []

    def get_quick_actions(self, student_id: int | None = None) -> dict[str, Any]:
        try:
            actions: list[dict[str, Any]] = []
            if student_id is not None:
                actions.extend([
                    {"id": "schedule", "label": "Agendar atendimento", "icon": "📅"},
                    {"id": "mood", "label": "Registrar humor", "icon": "😊"},
                    {"id": "screening", "label": "Nova triagem", "icon": "📋"},
                    {"id": "intervention", "label": "Registrar intervenção", "icon": "🤝"},
                ])
            else:
                actions.extend([
                    {"id": "students", "label": "Ver estudantes", "icon": "👥"},
                    {"id": "reports", "label": "Gerar relatório", "icon": "📊"},
                    {"id": "dashboard", "label": "Ir para dashboard", "icon": "📈"},
                ])
            return {"success": True, "data": actions}
        except Exception as exc:
            logger.error("Erro ao obter quick actions: %s", exc)
            return {"success": True, "data": []}

    def calculate_retention_rate(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        try:
            return self.repo.calcular_taxa_retencao(start_date, end_date)
        except Exception as exc:
            logger.error("Erro ao calcular taxa de retencao: %s", exc)
            return {
                "retention_rate": 0.0,
                "total_students": 0,
                "retained_students": 0,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

    def calculate_conversion_rate(
        self,
        stage_from: str,
        stage_to: str,
        date_range: tuple[date, date] | None = None,
    ) -> dict[str, Any]:
        try:
            start, end = date_range if date_range else (None, None)
            return self.repo.calcular_taxa_conversao(stage_from, stage_to, start, end)
        except Exception as exc:
            logger.error("Erro ao calcular taxa de conversao: %s", exc)
            return {
                "conversion_rate": 0.0,
                "from_stage": stage_from,
                "to_stage": stage_to,
                "total": 0,
                "converted": 0,
            }

    def get_student_journey(self, student_id: int) -> dict[str, Any]:
        try:
            return self.repo.obter_jornada_estudante(student_id)
        except Exception as exc:
            logger.error("Erro ao obter jornada do estudante: %s", exc)
            return {"student_id": student_id, "events": []}

    def get_peak_hours(self) -> dict[str, Any]:
        try:
            return self.repo.obter_horarios_pico()
        except Exception as exc:
            logger.error("Erro ao obter horarios de pico: %s", exc)
            return {"peak_hours": [], "hour_distribution": {}}

    def get_psychologist_workload(self) -> dict[str, Any]:
        try:
            return self.repo.obter_carga_psicologos()
        except Exception as exc:
            logger.error("Erro ao obter carga de psicologos: %s", exc)
            return {"workload": [], "total_appointments": 0}

    def predict_no_show(self, appointment_id: int) -> dict[str, Any]:
        try:
            return self.repo.prever_falta(appointment_id)
        except Exception as exc:
            logger.error("Erro ao prever falta: %s", exc)
            return {
                "appointment_id": appointment_id,
                "no_show_probability": 0.0,
                "risk_factors": [],
                "risk_level": "low",
            }

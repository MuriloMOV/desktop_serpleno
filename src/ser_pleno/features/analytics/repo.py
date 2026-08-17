# -*- coding: utf-8 -*-
"""Repositorio de analytics e tendencias."""

from __future__ import annotations

from typing import Any

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    fetch_all_batch,
    with_local_fallback,
    local_cache,
)
from ser_pleno.infrastructure.api.api import ClienteAPI

try:
    from ser_pleno.config.operation_mode import get_operation_config
except Exception:
    get_operation_config = None  # type: ignore

import logging

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    def __init__(self, auth_service=None):
        self._api = ClienteAPI(auth_service=auth_service)

    @with_local_fallback("_local_dashboard_stats")
    def obter_estatisticas_dashboard(self):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_dashboard_stats()

        response = self._api.get("desktop/analytics/dashboard/")
        if response.get("success"):
            return response.get("data", {})
        return self._local_dashboard_stats()

    @with_local_fallback("_local_trends")
    def obter_tendencias(self, metric: str = "mood", days: int = 30):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_trends(metric, days)

        response = self._api.get(
            "desktop/analytics/trends/",
            params={"metric": metric, "days": days},
        )
        if response.get("success"):
            return response.get("data", {})
        return self._local_trends(metric, days)

    @with_local_fallback("_local_performance")
    def obter_performance(self):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_performance()

        response = self._api.get("desktop/analytics/performance/")
        if response.get("success"):
            return response.get("data", {})
        return self._local_performance()

    @with_local_fallback("_local_buscar_global")
    def buscar_global(self, query: str):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_buscar_global(query)

        response = self._api.get(
            "desktop/analytics/search/",
            params={"q": query},
        )
        if response.get("success"):
            return response.get("data", {})
        return self._local_buscar_global(query)

    @with_local_fallback("_local_quick_actions")
    def obter_quick_actions(self):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_quick_actions()

        response = self._api.get("desktop/analytics/quick-actions/")
        if response.get("success"):
            return response.get("data", [])
        return self._local_quick_actions()

    # ——————————————————————————————————————————————————————————————————————
    #  Fallbacks locais
    # ——————————————————————————————————————————————————————————————————————
    def _local_dashboard_stats(self):
        base_query = """
            SELECT
                (SELECT COUNT(*) FROM aluno) AS total_alunos,
                (SELECT COUNT(*) FROM aluno WHERE requires_attention = 1) AS total_atencao,
                (SELECT COUNT(*) FROM agendamento WHERE DATE(data_hora) = CURDATE()) AS agendamentos_hoje,
                (SELECT COUNT(*) FROM desktop_screening WHERE status = 'pending') AS triagens_pendentes,
                (SELECT COUNT(*) FROM desktop_alert WHERE is_read = 0) AS alertas_nao_lidos,
                (SELECT COUNT(*) FROM disponibilidade WHERE is_active = 1) AS total_disponibilidade,
                (SELECT COUNT(*) FROM agendamento WHERE DATE(data_hora) = CURDATE() AND status != 'canceled') AS agendamentos_hoje_ativos,
                (SELECT AVG(mood_level) FROM desktop_moodentry WHERE DATE(entry_date) = CURDATE()) AS media_humor_hoje,
                (SELECT AVG(overall_wellbeing) FROM desktop_wellnesscheckin WHERE DATE(check_in_date) >= CURDATE() - INTERVAL 7 DAY) AS media_bem_estar
        """
        base_row = fetch_one(base_query)
        base = base_row or {}

        return {
            "appointments_today": base.get("agendamentos_hoje") or 0,
            "screenings_pending": base.get("triagens_pendentes") or 0,
            "alerts": base.get("alertas_nao_lidos") or 0,
            "total_students": base.get("total_alunos") or 0,
            "attention_count": base.get("total_atencao") or 0,
            "avg_mood": round(base.get("media_humor_hoje"), 2) if base.get("media_humor_hoje") else None,
            "avg_wellbeing": round(base.get("media_bem_estar"), 2) if base.get("media_bem_estar") else 0,
            "available_slots": max(0, (base.get("total_disponibilidade") or 0) - (base.get("agendamentos_hoje_ativos") or 0)),
        }

    def _local_trends(self, metric: str = "mood", days: int = 30):
        if metric == "mood":
            query = """
                SELECT DATE(entry_date) as data, AVG(mood_level) as valor
                FROM desktop_moodentry
                WHERE DATE(entry_date) >= CURDATE() - INTERVAL %s DAY
                GROUP BY DATE(entry_date)
                ORDER BY data
            """
            rows = fetch_all(query, (days,))
            return {
                "metric": "Humor medio",
                "unit": "/5",
                "data": [
                    {
                        "date": r["data"].strftime("%Y-%m-%d") if hasattr(r["data"], "strftime") else str(r["data"]),
                        "value": round(r["valor"], 2) if r.get("valor") else 0,
                    }
                    for r in rows
                ],
            }
        elif metric == "wellbeing":
            query = """
                SELECT DATE(check_in_date) as data, AVG(overall_wellbeing) as valor
                FROM desktop_wellnesscheckin
                WHERE DATE(check_in_date) >= CURDATE() - INTERVAL %s DAY
                GROUP BY DATE(check_in_date)
                ORDER BY data
            """
            rows = fetch_all(query, (days,))
            return {
                "metric": "Bem-estar medio",
                "unit": "/5",
                "data": [
                    {
                        "date": r["data"].strftime("%Y-%m-%d") if hasattr(r["data"], "strftime") else str(r["data"]),
                        "value": round(r["valor"], 2) if r.get("valor") else 0,
                    }
                    for r in rows
                ],
            }
        elif metric == "appointments":
            query = """
                SELECT DATE(data_hora) as data, COUNT(*) as valor
                FROM agendamento
                WHERE DATE(data_hora) >= CURDATE() - INTERVAL %s DAY
                GROUP BY DATE(data_hora)
                ORDER BY data
            """
            rows = fetch_all(query, (days,))
            return {
                "metric": "Atendimentos",
                "unit": "un",
                "data": [
                    {
                        "date": r["data"].strftime("%Y-%m-%d") if hasattr(r["data"], "strftime") else str(r["data"]),
                        "value": r.get("valor") or 0,
                    }
                    for r in rows
                ],
            }
        return {"metric": metric, "unit": "", "data": []}

    def _local_performance(self):
        hoje = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        alunos_rows = local_cache.list_students()
        total_alunos = len(alunos_rows)

        appts_rows = local_cache.list_all(
            "appointments",
            where_clause="DATE(data_hora) = ?",
            params=(hoje,),
        )
        appts_hoje = len(appts_rows)

        triagens_rows = local_cache.list_screenings()
        triagens_pend = sum(1 for r in triagens_rows if r.get("status") == "pending")

        alertas_rows = local_cache.list_alerts()
        alertas_nao_lidos = sum(1 for r in alertas_rows if not r.get("is_read"))

        mood_rows = local_cache.list_wellness_moods()
        rows_hoje = [r for r in mood_rows if (r.get("entry_date") or "").startswith(hoje)]
        media_humor = (
            round(sum(r.get("mood_level", 0) for r in rows_hoje) / len(rows_hoje), 2)
            if rows_hoje else None
        )

        wellness_rows = local_cache.list_wellness_checkins()
        from datetime import datetime, timedelta
        semana_passada = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        rows_semana = [r for r in wellness_rows if (r.get("check_in_date") or "") >= semana_passada]
        media_wellness = (
            round(sum(r.get("overall_wellbeing", 0) for r in rows_semana) / len(rows_semana), 2)
            if rows_semana else 0
        )

        return {
            "total_students": total_alunos,
            "appointments_today": appts_hoje,
            "screenings_pending": triagens_pend,
            "alerts_unread": alertas_nao_lidos,
            "avg_mood": media_humor,
            "avg_wellbeing": media_wellness,
            "completion_rate": 85.0,
            "avg_session_duration": 45,
        }

    def _local_buscar_global(self, query: str):
        if not query or not query.strip():
            return {"students": [], "appointments": [], "screenings": []}

        q = query.strip().lower()
        resultados = {"students": [], "appointments": [], "screenings": []}

        alunos = local_cache.list_students()
        for a in alunos:
            nome = (a.get("nome") or "").lower()
            if q in nome:
                resultados["students"].append({
                    "id": a.get("id"),
                    "name": a.get("nome"),
                    "type": "student",
                })

        appts = local_cache.list_all("appointments")
        for ap in appts:
            nome = (ap.get("student_name") or "").lower()
            curso = (ap.get("curso") or "").lower()
            if q in nome or q in curso:
                resultados["appointments"].append({
                    "id": ap.get("id"),
                    "name": ap.get("student_name") or "Estudante",
                    "detail": ap.get("curso") or "",
                    "type": "appointment",
                })

        triagens = local_cache.list_screenings()
        for t in triagens:
            nome = (t.get("student_name") or "").lower()
            if q in nome:
                resultados["screenings"].append({
                    "id": t.get("id"),
                    "name": t.get("student_name") or "Estudante",
                    "status": t.get("status") or "pending",
                    "type": "screening",
                })

        return resultados

    def _local_quick_actions(self):
        stats = self._local_dashboard_stats()
        actions = []

        if stats.get("alerts", 0) > 0:
            actions.append({
                "id": "review_alerts",
                "label": "Revisar alertas",
                "icon": "!",
                "description": f"{stats['alerts']} alerta(s) pendente(s) de atencao",
                "action_type": "navigate",
                "target": "alertas",
            })

        if stats.get("screenings_pending", 0) > 0:
            actions.append({
                "id": "process_screenings",
                "label": "Processar triagens",
                "icon": "⌕",
                "description": f"{stats['screenings_pending']} triagem(ns) aguardando",
                "action_type": "navigate",
                "target": "analise",
            })

        if stats.get("appointments_today", 0) > 0:
            actions.append({
                "id": "view_today_appointments",
                "label": "Ver atendimentos de hoje",
                "icon": "◯",
                "description": f"{stats['appointments_today']} atendimento(s) hoje",
                "action_type": "navigate",
                "target": "agenda",
            })

        actions.append({
            "id": "add_student",
            "label": "Cadastrar estudante",
            "icon": "+",
            "description": "Adicionar novo estudante ao sistema",
            "action_type": "navigate",
            "target": "estudantes",
        })

        actions.append({
            "id": "view_wellness",
            "label": "Monitorar bem-estar",
            "icon": "♥",
            "description": "Acompanhar indicadores de bem-estar",
            "action_type": "navigate",
            "target": "bem_estar",
        })

        return actions

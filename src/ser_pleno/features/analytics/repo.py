"""Repositorio de analytics e tendencias."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    local_cache,
    with_local_fallback,
)

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

    @with_local_fallback("_local_calcular_taxa_retencao")
    def calcular_taxa_retencao(self, start_date: date, end_date: date):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_calcular_taxa_retencao(start_date, end_date)

        query = """
            WITH previous_period AS (
                SELECT DISTINCT student_id
                FROM agendamento
                WHERE DATE(data_hora) >= DATE_SUB(%s, INTERVAL 30 DAY)
                  AND DATE(data_hora) < %s
                  AND status != 'canceled'
            ),
            current_period AS (
                SELECT DISTINCT student_id
                FROM agendamento
                WHERE DATE(data_hora) >= %s AND DATE(data_hora) <= %s
                  AND status != 'canceled'
            )
            SELECT
                COUNT(DISTINCT pp.student_id) AS total_students,
                COUNT(DISTINCT cp.student_id) AS retained_students,
                ROUND(
                    COUNT(DISTINCT cp.student_id) / COUNT(DISTINCT pp.student_id) * 100,
                    2
                ) AS retention_rate
            FROM previous_period pp
            LEFT JOIN current_period cp ON pp.student_id = cp.student_id
        """
        return fetch_one(query, (start_date.isoformat(), start_date.isoformat(), start_date.isoformat(), end_date.isoformat()))

    @with_local_fallback("_local_calcular_taxa_conversao")
    def calcular_taxa_conversao(self, stage_from: str, stage_to: str, start_date: date | None, end_date: date | None):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_calcular_taxa_conversao(stage_from, stage_to, start_date, end_date)

        date_filter = ""
        params: tuple = (stage_from, stage_to, stage_from)
        if start_date and end_date:
            date_filter = "AND DATE(data_hora) >= %s AND DATE(data_hora) <= %s"
            params = (stage_from, stage_to, stage_from, start_date.isoformat(), end_date.isoformat())

        query = f"""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = %s THEN 1 ELSE 0 END) AS converted,
                ROUND(
                    SUM(CASE WHEN status = %s THEN 1 ELSE 0 END) / COUNT(*) * 100,
                    2
                ) AS conversion_rate
            FROM agendamento
            WHERE status = %s
              {date_filter}
        """
        return fetch_one(query, params)

    @with_local_fallback("_local_obter_jornada_estudante")
    def obter_jornada_estudante(self, student_id: int):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_obter_jornada_estudante(student_id)

        query = """
            SELECT 'orientation' AS event_type, session_date AS event_date, title AS detail, psychologist_id AS professional_id, created_at AS ts
            FROM desktop_orientation WHERE student_id = %s
            UNION ALL
            SELECT 'intervention', date, intervention_type, conducted_by_id, created_at
            FROM desktop_intervention WHERE student_id = %s
            UNION ALL
            SELECT 'screening', completed_date, status, conducted_by_id, updated_at
            FROM desktop_screening WHERE student_id = %s AND completed_date IS NOT NULL
            UNION ALL
            SELECT 'appointment', DATE(data_hora), motivo, NULL, created_at
            FROM agendamento WHERE student_id = %s
            UNION ALL
            SELECT 'mood', entry_date, CONCAT('Humor ', mood_level), recorded_by_id, created_at
            FROM desktop_moodentry WHERE student_id = %s
            ORDER BY event_date ASC, ts ASC
        """
        rows = fetch_all(query, (student_id, student_id, student_id, student_id, student_id))
        return {
            "student_id": student_id,
            "events": [
                {
                    "type": r.get("event_type"),
                    "date": r.get("event_date").isoformat() if hasattr(r.get("event_date"), "isoformat") else str(r.get("event_date") or ""),
                    "detail": r.get("detail", ""),
                    "professional_id": r.get("professional_id"),
                }
                for r in rows
            ],
        }

    @with_local_fallback("_local_obter_horarios_pico")
    def obter_horarios_pico(self):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_obter_horarios_pico()

        query = """
            SELECT HOUR(data_hora) AS hour, COUNT(*) AS count
            FROM agendamento
            WHERE status != 'canceled'
            GROUP BY HOUR(data_hora)
            ORDER BY count DESC
        """
        rows = fetch_all(query)
        peak_hours = [{"hour": r.get("hour"), "count": r.get("count", 0)} for r in rows]
        hour_distribution = {r.get("hour"): r.get("count", 0) for r in rows}
        return {"peak_hours": peak_hours, "hour_distribution": hour_distribution}

    @with_local_fallback("_local_obter_carga_psicologos")
    def obter_carga_psicologos(self):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_obter_carga_psicologos()

        query = """
            SELECT
                COALESCE(au.username, 'Nao atribuido') AS name,
                COUNT(DISTINCT o.id) AS orientations,
                COUNT(DISTINCT i.id) AS interventions,
                COUNT(DISTINCT s.id) AS screenings,
                COUNT(DISTINCT o.id) + COUNT(DISTINCT i.id) + COUNT(DISTINCT s.id) AS total
            FROM auth_user au
            LEFT JOIN desktop_orientation o ON o.psychologist_id = au.id
            LEFT JOIN desktop_intervention i ON i.conducted_by_id = au.id
            LEFT JOIN desktop_screening s ON s.conducted_by_id = au.id
            GROUP BY au.id, au.username
            ORDER BY total DESC
        """
        rows = fetch_all(query)
        workload = [
            {
                "name": r.get("name", "Nao atribuido"),
                "orientations": r.get("orientations", 0),
                "interventions": r.get("interventions", 0),
                "screenings": r.get("screenings", 0),
                "total": r.get("total", 0),
            }
            for r in rows
        ]
        return {"workload": workload, "total_appointments": sum(w["total"] for w in workload)}

    @with_local_fallback("_local_prever_falta")
    def prever_falta(self, appointment_id: int):
        config = get_operation_config()
        if not config or not config.should_use_api():
            return self._local_prever_falta(appointment_id)

        query = """
            SELECT
                a.student_id,
                COUNT(CASE WHEN a.status IN ('canceled', 'no_show') THEN 1 END) AS past_no_shows,
                COUNT(*) AS total_appointments
            FROM agendamento a
            WHERE a.student_id = (SELECT student_id FROM agendamento WHERE id = %s)
            GROUP BY a.student_id
        """
        row = fetch_one(query, (appointment_id,))
        if not row:
            return {
                "appointment_id": appointment_id,
                "no_show_probability": 0.0,
                "risk_factors": [],
                "risk_level": "low",
            }

        total = row.get("total_appointments", 0)
        past_no_shows = row.get("past_no_shows", 0)
        probability = round(past_no_shows / total * 100, 2) if total > 0 else 0.0

        risk_factors = []
        if past_no_shows > 0:
            risk_factors.append(f"{past_no_shows} falta(s) anterior(es)")

        if probability >= 70:
            risk_level = "high"
        elif probability >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "appointment_id": appointment_id,
            "no_show_probability": probability,
            "risk_factors": risk_factors,
            "risk_level": risk_level,
        }

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

        if stats.get("available_slots", 0) > 0:
            actions.append({
                "id": "schedule_appointment",
                "label": "Agendar atendimento",
                "icon": "📅",
                "description": f"{stats['available_slots']} horario(s) disponivel(is)",
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

    def _local_calcular_taxa_retencao(self, start_date: date, end_date: date):
        appts = local_cache.list_all("appointments")
        prev_start = start_date - timedelta(days=30)

        students_prev = set()
        students_curr = set()

        for apt in appts:
            apt_date_str = apt.get("data_hora", "")[:10]
            if not apt_date_str:
                continue
            try:
                apt_date = datetime.strptime(apt_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            status = apt.get("status", "")
            if status in ("canceled", "cancelled", "no_show"):
                continue

            if prev_start <= apt_date < start_date:
                students_prev.add(apt.get("student_id"))
            if start_date <= apt_date <= end_date:
                students_curr.add(apt.get("student_id"))

        total = len(students_prev)
        retained = len(students_prev & students_curr)
        rate = round(retained / total * 100, 2) if total > 0 else 0.0

        return {
            "retention_rate": rate,
            "total_students": total,
            "retained_students": retained,
        }

    def _local_calcular_taxa_conversao(self, stage_from: str, stage_to: str, start_date: date | None, end_date: date | None):
        appts = local_cache.list_all("appointments")

        students_from = set()
        students_to = set()

        for apt in appts:
            apt_date_str = apt.get("data_hora", "")[:10]
            if not apt_date_str:
                continue
            try:
                apt_date = datetime.strptime(apt_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue

            if start_date and end_date:
                if not (start_date <= apt_date <= end_date):
                    continue

            status = apt.get("status", "")
            if status == stage_from:
                students_from.add(apt.get("student_id"))
            if status == stage_to:
                students_to.add(apt.get("student_id"))

        total = len(students_from)
        converted = len(students_from & students_to)
        rate = round(converted / total * 100, 2) if total > 0 else 0.0

        return {
            "conversion_rate": rate,
            "from_stage": stage_from,
            "to_stage": stage_to,
            "total": total,
            "converted": converted,
        }

    def _local_obter_jornada_estudante(self, student_id: int):
        events: list[dict[str, Any]] = []

        orientations = local_cache.list_orientations(student_id=student_id)
        for o in orientations:
            events.append({
                "type": "orientation",
                "date": o.get("session_date", ""),
                "detail": o.get("title", ""),
                "professional_id": o.get("psychologist"),
            })

        interventions = local_cache.list_interventions(student_id=student_id)
        for i in interventions:
            events.append({
                "type": "intervention",
                "date": i.get("date", ""),
                "detail": i.get("intervention_type", ""),
                "professional_id": i.get("conducted_by_id"),
            })

        screenings = local_cache.list_screenings(student_id=student_id)
        for s in screenings:
            scheduled = s.get("scheduled_date")
            if scheduled:
                events.append({
                    "type": "screening",
                    "date": scheduled,
                    "detail": f"Triagem: {s.get('status', '')}",
                    "professional_id": s.get("conducted_by_id"),
                })

        moods = local_cache.list_wellness_moods(student_id=student_id)
        for m in moods:
            events.append({
                "type": "mood",
                "date": m.get("entry_date", ""),
                "detail": f"Humor: {m.get('mood_level', '')}/5",
                "professional_id": m.get("recorded_by_id"),
            })

        events.sort(key=lambda x: x.get("date", ""))
        return {"student_id": student_id, "events": events}

    def _local_obter_horarios_pico(self):
        appts = local_cache.list_all("appointments")
        hour_counts: dict[int, int] = {}

        for apt in appts:
            data_hora = apt.get("data_hora", "")
            if not data_hora:
                continue
            try:
                parts = data_hora.split(" ")
                time_part = parts[1] if len(parts) > 1 else parts[0]
                hour = int(time_part.split(":")[0])
            except (IndexError, ValueError):
                continue

            status = apt.get("status", "")
            if status in ("canceled", "cancelled", "no_show"):
                continue

            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [{"hour": h, "count": c} for h, c in sorted_hours[:5]]

        return {
            "peak_hours": peak_hours,
            "hour_distribution": dict(sorted_hours),
        }

    def _local_obter_carga_psicologos(self):
        orientations = local_cache.list_orientations()
        interventions = local_cache.list_interventions()
        screenings = local_cache.list_screenings()

        workload: dict[str, dict[str, Any]] = {}

        for o in orientations:
            name = o.get("psychologist") or "Nao atribuido"
            entry = workload.setdefault(name, {"name": name, "orientations": 0, "interventions": 0, "screenings": 0, "total": 0})
            entry["orientations"] += 1
            entry["total"] += 1

        for i in interventions:
            conducted_by = i.get("conducted_by_id")
            name = f"Profissional {conducted_by}" if conducted_by else "Nao atribuido"
            entry = workload.setdefault(name, {"name": name, "orientations": 0, "interventions": 0, "screenings": 0, "total": 0})
            entry["interventions"] += 1
            entry["total"] += 1

        for s in screenings:
            conducted_by = s.get("conducted_by_id")
            name = f"Profissional {conducted_by}" if conducted_by else "Nao atribuido"
            entry = workload.setdefault(name, {"name": name, "orientations": 0, "interventions": 0, "screenings": 0, "total": 0})
            entry["screenings"] += 1
            entry["total"] += 1

        result = sorted(workload.values(), key=lambda x: x["total"], reverse=True)
        return {"workload": result, "total_appointments": sum(w["total"] for w in result)}

    def _local_prever_falta(self, appointment_id: int):
        appts = local_cache.list_all("appointments")

        student_id = None
        for apt in appts:
            if apt.get("id") == appointment_id:
                student_id = apt.get("student_id")
                break

        if student_id is None:
            return {
                "appointment_id": appointment_id,
                "no_show_probability": 0.0,
                "risk_factors": [],
                "risk_level": "low",
            }

        student_appts = [a for a in appts if a.get("student_id") == student_id]
        total = len(student_appts)
        no_shows = sum(1 for a in student_appts if a.get("status") in ("canceled", "cancelled", "no_show"))

        probability = round(no_shows / total * 100, 2) if total > 0 else 0.0
        risk_factors = []
        if no_shows > 0:
            risk_factors.append(f"{no_shows} falta(s) anterior(es)")

        if probability >= 70:
            risk_level = "high"
        elif probability >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "appointment_id": appointment_id,
            "no_show_probability": probability,
            "risk_factors": risk_factors,
            "risk_level": risk_level,
        }

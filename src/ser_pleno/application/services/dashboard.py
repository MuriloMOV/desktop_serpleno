from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from ser_pleno.features.agenda.service import ServicoAgendamento
from ser_pleno.features.bem_estar.service import ServicoBemEstar
from ser_pleno.features.dashboard.service import ServicoDashboard
from ser_pleno.features.estudantes.service import ServicoEstudante
from ser_pleno.features.orientacoes.service import ServicoOrientacoes

logger = logging.getLogger(__name__)


def _get_role(user_profile: dict[str, Any]) -> str:
    return user_profile.get("role", "visitante")


def _build_students_context() -> dict[str, Any]:
    service = ServicoEstudante()
    service._should_use_api = lambda: False
    students_result = service.listar_estudantes()
    students: list[dict[str, Any]] = students_result.get("data", []) if isinstance(students_result, dict) else []
    total_students = len(students)
    attention_students = sum(1 for s in students if s.get("requires_attention"))
    return {
        "total_students": total_students,
        "attention_students": attention_students,
        "recent_students": students[:10],
    }


def _build_agenda_context() -> dict[str, Any]:
    service = ServicoAgendamento()
    today = date.today().isoformat()
    appointments = service.listar_agendamentos(data=today) or []
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_end = week_start + timedelta(days=6)
    return {
        "today_appointments": len(appointments),
        "today_list": appointments[:20],
        "week_range": {
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
        },
    }


def _build_screening_context() -> dict[str, Any]:
    try:
        from ser_pleno.features.triagem.service import ServicoTriagem

        service = ServicoTriagem()
        pending = service.listar_triagens(status="pending") if hasattr(service, "listar_triagens") else {"success": True, "data": []}
        pending_list = pending.get("data", []) if isinstance(pending, dict) else []
        return {
            "pending_count": len(pending_list),
            "pending_list": pending_list[:20],
        }
    except Exception as exc:
        logger.error("Erro ao montar contexto de triagem: %s", exc)
        return {"pending_count": 0, "pending_list": []}


def _build_communication_context() -> dict[str, Any]:
    try:
        dashboard_service = ServicoDashboard()
        dashboard_service._should_use_api = lambda: False
        kpis = dashboard_service.obter_kpis() or {}
        return {
            "unread_alerts": kpis.get("alerts", 0),
            "unread_notifications": 0,
        }
    except Exception as exc:
        logger.error("Erro ao montar contexto de comunicação: %s", exc)
        return {"unread_alerts": 0, "unread_notifications": 0}


def _build_guidance_context() -> dict[str, Any]:
    try:
        service = ServicoOrientacoes()
        service._should_use_api = lambda: False
        orientations = service.listar_orientacoes() or {"success": True, "data": {"orientations": []}}
        orientations_data = orientations.get("data", {}) if isinstance(orientations, dict) else {}
        orientation_list = orientations_data.get("orientations", []) if isinstance(orientations_data, dict) else []
        today = date.today().isoformat()
        published = [o for o in orientation_list if o.get("session_date") and o.get("session_date") <= today]
        return {
            "total_published": len(published),
            "recent_published": published[:10],
        }
    except Exception as exc:
        logger.error("Erro ao montar contexto de orientações: %s", exc)
        return {"total_published": 0, "recent_published": []}


def _build_wellness_context() -> dict[str, Any]:
    service = ServicoBemEstar()
    service._should_use_api = lambda: False
    dashboard = service.obter_dashboard() or {"success": True, "data": {}}
    data = dashboard.get("data", {}) if isinstance(dashboard, dict) else {}
    summary = data.get("summary", {}) if isinstance(data, dict) else {}
    return {
        "average_mood": summary.get("average_mood"),
        "moods": data.get("moods", []),
        "checkins": data.get("checkins", []),
    }


def build_dashboard_context(user_profile: dict[str, Any]) -> dict[str, Any]:
    role = _get_role(user_profile)
    context: dict[str, Any] = {
        "role": role,
        "user": user_profile,
        "students": _build_students_context(),
        "agenda": _build_agenda_context(),
        "screening": _build_screening_context(),
        "communication": _build_communication_context(),
        "guidance": _build_guidance_context(),
        "wellness": _build_wellness_context(),
    }
    if role == "admin":
        context["admin"] = {
            "total_users": 0,
            "recent_logins": [],
        }
    if role == "psicologo":
        context["psychologist"] = {
            "my_appointments_today": context["agenda"].get("today_appointments", 0),
            "my_students": context["students"].get("total_students", 0),
        }
    if role == "coordenador":
        context["coordinator"] = {
            "pending_approvals": context["screening"].get("pending_count", 0),
            "team_alerts": context["communication"].get("unread_alerts", 0),
        }
    return context


def build_students_context() -> dict[str, Any]:
    return _build_students_context()


def build_agenda_context() -> dict[str, Any]:
    return _build_agenda_context()


def build_screening_context() -> dict[str, Any]:
    return _build_screening_context()


def build_communication_context() -> dict[str, Any]:
    return _build_communication_context()


def build_guidance_context() -> dict[str, Any]:
    return _build_guidance_context()


def build_wellness_context() -> dict[str, Any]:
    return _build_wellness_context()

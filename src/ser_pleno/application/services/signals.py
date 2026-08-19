from __future__ import annotations

import logging
import os
from typing import Any

from ser_pleno.application.services._helpers import invalidate_related_caches
from ser_pleno.features.agenda.repo import AgendamentoRepository
from ser_pleno.features.orientacoes.repo import OrientacaoRepository
from ser_pleno.repositories.autenticacao import AutenticacaoRepository

logger = logging.getLogger(__name__)


def ensure_desktop_profile_for_staff(user_id: int) -> None:
    try:
        repo = AutenticacaoRepository()
        user = repo.obter_usuario_por_id(user_id)
        if user and user.get("is_staff"):
            invalidate_related_caches("user_profile", [user_id])
    except Exception as exc:
        logger.error("Erro ao garantir perfil desktop para staff %s: %s", user_id, exc)


def sync_appointment_to_agendamento(appointment_id: int) -> None:
    try:
        repo = AgendamentoRepository()
        agendamento = repo.obter_agendamento_para_sincronizacao(appointment_id)
        if not agendamento:
            return
        invalidate_related_caches("appointment", [appointment_id])
    except Exception as exc:
        logger.error("Erro ao sincronizar agendamento %s: %s", appointment_id, exc)


def alert_from_help_request(request_id: int) -> None:
    try:
        from ser_pleno.features.pedidos_ajuda.repo import PedidosAjudaRepository

        repo = PedidosAjudaRepository()
        rows = repo.listar_pedidos_ajuda(status="pending")
        request = next((r for r in rows if r.get("id") == request_id), None)
        if request:
            invalidate_related_caches("help_request", [request_id])
    except Exception as exc:
        logger.error("Erro ao gerar alerta de pedido de ajuda %s: %s", request_id, exc)


def alert_from_mood(student_id: int, mood_value: int) -> None:
    try:
        if mood_value <= 2:
            invalidate_related_caches("mood_alert", [student_id])
    except Exception as exc:
        logger.error("Erro ao gerar alerta de humor para estudante %s: %s", student_id, exc)


def available_time_saved(time_id: Any) -> None:
    try:
        invalidate_related_caches("availability", [int(time_id) if time_id is not None else 0])
    except Exception as exc:
        logger.error("Erro ao processar available_time_saved: %s", exc)


def available_time_deleted(time_id: Any) -> None:
    try:
        invalidate_related_caches("availability", [int(time_id) if time_id is not None else 0])
    except Exception as exc:
        logger.error("Erro ao processar available_time_deleted: %s", exc)


def disponibilidade_saved(disp_id: Any) -> None:
    try:
        invalidate_related_caches("disponibilidade", [int(disp_id) if disp_id is not None else 0])
    except Exception as exc:
        logger.error("Erro ao processar disponibilidade_saved: %s", exc)


def disponibilidade_deleted(disp_id: Any) -> None:
    try:
        invalidate_related_caches("disponibilidade", [int(disp_id) if disp_id is not None else 0])
    except Exception as exc:
        logger.error("Erro ao processar disponibilidade_deleted: %s", exc)


def delete_orientation_attachment_file(attachment_id: int) -> None:
    try:
        repo = OrientacaoRepository()
        anexo = repo.obter_anexo(attachment_id)
        if anexo and anexo.get("file"):
            file_path = anexo["file"]
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as exc:
        logger.error("Erro ao deletar arquivo de anexo %s: %s", attachment_id, exc)

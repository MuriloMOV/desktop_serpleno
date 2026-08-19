from __future__ import annotations

import logging
from typing import Any

from ser_pleno.features.bem_estar.repo import BemEstarRepository
from ser_pleno.features.estudantes.repo import EstudanteRepository
from ser_pleno.features.pedidos_ajuda.service import ServicoPedidosAjuda

logger = logging.getLogger(__name__)

_MOOD_TEXT_TO_VALUE: dict[str, int] = {
    "muito triste": 1,
    "muito ruim": 1,
    "triste": 3,
    "ruim": 3,
    "neutro": 5,
    "normal": 5,
    "bem": 7,
    "boa": 7,
    "muito bem": 9,
    "otimo": 10,
    "ótimo": 10,
    "feliz": 8,
    "animado": 9,
    "ansioso": 4,
    "estressado": 3,
    "cansado": 3,
    "irritado": 2,
    "preocupado": 4,
}

_VALUE_TO_EMOJI: dict[int, str] = {
    0: "😵",
    1: "☹",
    2: "🙁",
    3: "😕",
    4: "😐",
    5: "🙂",
    6: "😊",
    7: "😄",
    8: "😁",
    9: "🤩",
    10: "🥳",
}


def map_humor_to_value(mood_text: str) -> int:
    normalized = (mood_text or "").strip().lower()
    return _MOOD_TEXT_TO_VALUE.get(normalized, 5)


def map_value_to_emoji(value: int) -> str:
    value = max(0, min(10, int(value)))
    return _VALUE_TO_EMOJI.get(value, "😐")


def calculate_student_risk_level(student_id: int) -> dict[str, Any]:
    repo = EstudanteRepository()
    bem_estar_repo = BemEstarRepository()
    reasons: list[str] = []
    try:
        student = repo.obter(student_id)
        if not student:
            return {"student_id": student_id, "risk_level": "low", "reasons": ["Estudante não encontrado"]}
        priority = student.get("priority_level") or 0
        if student.get("requires_attention"):
            reasons.append(student.get("attention_reason") or "Requer atenção")
        if priority >= 4:
            reasons.append("Prioridade crítica")
        elif priority == 3:
            reasons.append("Prioridade alta")
        mood_history = bem_estar_repo.obter_humor_estudante(student_id)
        if isinstance(mood_history, list) and mood_history:
            recent = mood_history[-5:]
            low_moods = sum(1 for m in recent if m.get("mood_level", 5) <= 3)
            if low_moods >= 3:
                reasons.append("Histórico recente de baixo humor")
        if not reasons:
            risk = "low"
        elif priority >= 4 or any(r in reasons for r in ["Prioridade crítica", "Histórico recente de baixo humor"]):
            risk = "high"
        elif priority == 3 or len(reasons) >= 2:
            risk = "medium"
        else:
            risk = "low"
        return {"student_id": student_id, "risk_level": risk, "reasons": reasons}
    except Exception as exc:
        logger.error("Erro ao calcular risco do estudante %s: %s", student_id, exc)
        return {"student_id": student_id, "risk_level": "low", "reasons": [str(exc)]}


def get_help_requests_service() -> list[dict[str, Any]]:
    service = ServicoPedidosAjuda()
    result = service.listar_pendentes()
    return result.get("data", []) if isinstance(result, dict) else []


def update_help_request_service(request_id: int, dados: dict[str, Any]) -> dict[str, Any]:
    service = ServicoPedidosAjuda()
    if dados.get("status") == "in_progress":
        return service.iniciar_atendimento(request_id)
    if dados.get("status") == "resolved":
        return service.resolver_pedido(request_id)
    return service.marcar_visto(request_id)


def respond_help_request_service(request_id: int, response: str) -> dict[str, Any]:
    service = ServicoPedidosAjuda()
    return service.responder_pedido(request_id, response)

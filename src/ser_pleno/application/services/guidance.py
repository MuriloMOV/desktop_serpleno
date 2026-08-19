from __future__ import annotations

import logging
import os
from typing import Any

from ser_pleno.features.orientacoes.repo import OrientacaoRepository

logger = logging.getLogger(__name__)


def publish_orientation_if_ready(orientation: dict[str, Any]) -> dict[str, Any]:
    required_fields = ["title", "content", "student_id", "session_date"]
    missing = [f for f in required_fields if not orientation.get(f)]
    if missing:
        return {
            "success": False,
            "message": f"Campos obrigatórios ausentes: {', '.join(missing)}",
            "data": None,
        }
    repo = OrientacaoRepository()
    try:
        orientation_id = repo.criar_orientacao(
            student_id=orientation.get("student_id"),
            title=orientation.get("title"),
            theme=orientation.get("theme"),
            session_date=orientation.get("session_date"),
            content=orientation.get("content"),
            is_markdown=orientation.get("is_markdown", False),
            motivational_message=orientation.get("motivational_message", ""),
            action_plan=orientation.get("action_plan", []),
            psychologist=orientation.get("psychologist", "Equipe SerPleno"),
        )
        return {
            "success": True,
            "message": "Orientação publicada com sucesso",
            "data": {"id": orientation_id},
        }
    except Exception as exc:
        logger.error("Erro ao publicar orientação: %s", exc)
        return {"success": False, "message": str(exc), "data": None}


def generate_orientation_attachment(orientation: dict[str, Any]) -> dict[str, Any]:
    content = orientation.get("content", "")
    title = orientation.get("title", "Orientacao")
    if not content:
        return {"success": False, "message": "Conteúdo vazio", "data": None}
    try:
        from ser_pleno.application.services.pdf import gerar_pdf_relatorio

        report_data = {"title": title, "content": content, "theme": orientation.get("theme")}
        pdf_bytes = gerar_pdf_relatorio(report_type="orientation", report_data=report_data, report_name=title)
        base_name = f"{title.replace(' ', '_').replace('/', '_')}"
        ext = "pdf"
        file_path = os.path.join(__import__("tempfile").gettempdir(), f"{base_name}.{ext}")
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        return {
            "success": True,
            "message": "Anexo gerado com sucesso",
            "data": {"file_path": file_path, "file_name": os.path.basename(file_path), "size": len(pdf_bytes)},
        }
    except ImportError as exc:
        logger.error("Biblioteca de PDF não disponível: %s", exc)
        return {"success": False, "message": "Biblioteca de PDF não disponível", "data": None}
    except Exception as exc:
        logger.error("Erro ao gerar anexo: %s", exc)
        return {"success": False, "message": str(exc), "data": None}


def validate_orientation_content(content: Any) -> dict[str, Any]:
    errors: list[str] = []
    if content is None:
        return {"success": False, "valid": False, "errors": ["Conteúdo não pode ser None"]}
    text = str(content).strip()
    if not text:
        errors.append("Conteúdo não pode estar vazio")
    if len(text) < 10:
        errors.append("Conteúdo muito curto")
    return {
        "success": True,
        "valid": len(errors) == 0,
        "errors": errors,
        "content": text,
    }

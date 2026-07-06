# -*- coding: utf-8 -*-
"""Mapeamentos seguros de linhas de banco para dicionários."""

from __future__ import annotations


def safe_str(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value)


def safe_bool(value) -> bool:
    return bool(value)


def map_row(row: dict, mapping: dict) -> dict:
    """Mapeia um row do banco para dict usando {dest: (src, transform_fn | None)}."""
    result = {}
    for dest, spec in mapping.items():
        if isinstance(spec, tuple):
            src, transform = spec
            val = row.get(src)
            result[dest] = transform(val) if transform else val
        else:
            result[dest] = row.get(spec)
    return result


# Mapeadores específicos de comunicação
def mapear_alerta(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "alert_type": row.get("alert_type"),
        "severity": row.get("severity"),
        "message": row.get("message"),
        "details": row.get("details"),
        "is_read": safe_bool(row.get("is_read")),
        "is_resolved": safe_bool(row.get("is_resolved")),
        "resolved_at": safe_str(row.get("resolved_at")),
        "created_at": safe_str(row.get("created_at")),
        "assigned_to_id": row.get("assigned_to_id"),
        "resolved_by_id": row.get("resolved_by_id"),
        "student_id": row.get("student_id"),
    }


def mapear_pedido(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "tipo": row.get("tipo"),
        "mensagem": row.get("mensagem"),
        "prioridade": row.get("prioridade"),
        "status": row.get("status"),
        "localizacao": row.get("localizacao"),
        "dados_extras": row.get("dados_extras"),
        "created_at": safe_str(row.get("created_at")),
        "viewed_at": safe_str(row.get("viewed_at")),
        "resolved_at": safe_str(row.get("resolved_at")),
        "aluno_id": row.get("aluno_id"),
    }


def mapear_contato(row: dict, id_usuario_logado=None) -> dict:
    nome_completo = f"{safe_str(row.get('first_name'))} {safe_str(row.get('last_name'))}".strip()
    if not nome_completo:
        nome_completo = safe_str(row.get("username"), "Usuário")
    return {
        "id": row.get("id"),
        "name": nome_completo,
        "email": row.get("email"),
        "student_name": row.get("student_name"),
        "role": row.get("role"),
        "is_staff": safe_bool(row.get("is_staff") or row.get("is_superuser")),
    }


def mapear_mensagem(row: dict) -> dict:
    mensagem = {
        "id": row.get("id"),
        "sender_id": row.get("sender_id"),
        "recipient_id": row.get("recipient_id"),
        "text": row.get("text"),
        "timestamp": safe_str(row.get("timestamp")),
        "read": safe_bool(row.get("read")),
    }
    if row.get("caminho_arquivo"):
        mensagem["caminho_arquivo"] = row.get("caminho_arquivo")
        mensagem["tipo_arquivo"] = row.get("tipo_arquivo")
    return mensagem

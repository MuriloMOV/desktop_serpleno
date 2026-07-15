# -*- coding: utf-8 -*-
"""Service de Comunicação — orquestrador, sem SQL inline."""

from ser_pleno.repositories.comunicacao import ComunicacaoRepository
from typing import Optional


# ===== Mappers de domínio (comunicação) =====

def _safe_str(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value)


def _safe_bool(value) -> bool:
    return bool(value)


def _map_alert(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "alert_type": row.get("alert_type"),
        "severity": row.get("severity"),
        "message": row.get("message"),
        "details": row.get("details"),
        "is_read": _safe_bool(row.get("is_read")),
        "is_resolved": _safe_bool(row.get("is_resolved")),
        "resolved_at": _safe_str(row.get("resolved_at")),
        "created_at": _safe_str(row.get("created_at")),
        "assigned_to_id": row.get("assigned_to_id"),
        "resolved_by_id": row.get("resolved_by_id"),
        "student_id": row.get("student_id"),
    }


def _map_help_request(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "type": row.get("tipo"),
        "message": row.get("mensagem"),
        "priority": row.get("prioridade"),
        "status": row.get("status"),
        "location": row.get("localizacao"),
        "extra_data": row.get("dados_extras"),
        "created_at": _safe_str(row.get("created_at")),
        "viewed_at": _safe_str(row.get("viewed_at")),
        "resolved_at": _safe_str(row.get("resolved_at")),
        "student_id": row.get("aluno_id"),
    }


def _map_contact(row: dict, logged_user_id=None) -> dict:
    full_name = f"{_safe_str(row.get('first_name'))} {_safe_str(row.get('last_name'))}".strip()
    if not full_name:
        full_name = _safe_str(row.get("username"), "Usuário")
    return {
        "id": row.get("id"),
        "name": full_name,
        "email": row.get("email"),
        "student_name": row.get("student_name"),
        "role": row.get("role"),
        "is_staff": _safe_bool(row.get("is_staff") or row.get("is_superuser")),
    }


def _map_message(row: dict) -> dict:
    message = {
        "id": row.get("id"),
        "sender_id": row.get("sender_id"),
        "recipient_id": row.get("recipient_id"),
        "text": row.get("text"),
        "timestamp": _safe_str(row.get("timestamp")),
        "read": _safe_bool(row.get("read")),
    }
    if row.get("caminho_arquivo"):
        message["file_path"] = row.get("caminho_arquivo")
        message["file_type"] = row.get("tipo_arquivo")
    return message


class ServicoComunicacao:
    def __init__(self, auth_service=None):
        self.repo = ComunicacaoRepository()

    def listar_alertas(self):
        rows = self.repo.listar_alertas()
        return {"success": True, "data": [_map_alert(r) for r in rows]}

    def marcar_alerta_lido(self, id_alerta):
        self.repo.marcar_alerta_lido(id_alerta)
        return {"success": True, "message": "Alerta marcado como lido"}

    def marcar_todos_lidos(self):
        self.repo.marcar_todos_lidos()
        return {"success": True, "message": "Todos os alertas marcados como lidos"}

    def listar_pedidos_ajuda(self):
        rows = self.repo.listar_pedidos_ajuda()
        return {"success": True, "data": [_map_help_request(r) for r in rows]}

    def listar_contatos(self, id_usuario_logado: Optional[int] = None):
        rows = self.repo.listar_contatos(id_usuario_logado=id_usuario_logado)
        contatos = []
        for row in rows:
            role = row.get("role")
            if role not in ["admin", "analista", "coordenador", "suporte"]:
                continue
            if id_usuario_logado and row.get("id") == id_usuario_logado:
                continue
            contatos.append(_map_contact(row, id_usuario_logado))
        return {"success": True, "data": contatos}

    def obter_mensagens(self, usuario_id: int, conversa_id: int) -> dict:
        rows = self.repo.obter_mensagens(usuario_id, conversa_id)
        return {"success": True, "data": [_map_message(r) for r in rows]}

    def enviar_mensagem(self, usuario_id: int, destinatario_id: int, texto: str) -> dict:
        msg_id = self.repo.enviar_mensagem(usuario_id, destinatario_id, texto)
        return {"success": True, "data": {"id": msg_id}}

    def obter_mensagens_grupo(self) -> dict:
        rows = self.repo.obter_mensagens_grupo()
        return {"success": True, "data": [_map_message(r) for r in rows]}

    def enviar_mensagem_grupo(self, usuario_id: int, *args) -> dict:
        if len(args) == 1:
            texto = args[0]
            msg_id = self.repo.enviar_mensagem_grupo_texto(usuario_id, texto)
        elif len(args) >= 3:
            nome = args[0]
            caminho = args[1]
            categoria = args[2] if len(args) > 2 else ""
            msg_id = self.repo.enviar_mensagem_grupo_arquivo(
                usuario_id, nome, caminho, categoria
            )
        else:
            return {"success": False, "error": "Argumentos inválidos"}
        return {"success": True, "data": {"id": msg_id}}

    def marcar_mensagem_lida(self, mensagem_id: int) -> dict:
        self.repo.marcar_mensagem_lida(mensagem_id)
        return {"success": True}

    def contar_mensagens_nao_lidas(self, usuario_id: int) -> dict:
        total = self.repo.contar_mensagens_nao_lidas(usuario_id)
        return {"success": True, "data": total}


# -*- coding: utf-8 -*-
"""Service de Comunicação —” orquestrador, sem SQL inline."""

from ser_pleno.repositories.comunicacao import ComunicacaoRepository
from ser_pleno.utils.mappers import (
    mapear_alerta,
    mapear_pedido,
    mapear_contato,
    mapear_mensagem,
    safe_str,
)
from typing import Optional


class ServicoComunicacao:
    def __init__(self):
        self.repo = ComunicacaoRepository()

    def listar_alertas(self):
        rows = self.repo.listar_alertas()
        return {"success": True, "data": [mapear_alerta(r) for r in rows]}

    def marcar_alerta_lido(self, id_alerta):
        self.repo.marcar_alerta_lido(id_alerta)
        return {"success": True, "message": "Alerta marcado como lido"}

    def marcar_todos_lidos(self):
        self.repo.marcar_todos_lidos()
        return {"success": True, "message": "Todos os alertas marcados como lidos"}

    def listar_pedidos_ajuda(self):
        rows = self.repo.listar_pedidos_ajuda()
        return {"success": True, "data": [mapear_pedido(r) for r in rows]}

    def listar_contatos(self, id_usuario_logado: Optional[int] = None):
        rows = self.repo.listar_contatos(id_usuario_logado=id_usuario_logado)
        contatos = []
        for row in rows:
            role = row.get("role")
            if role not in ["admin", "analista", "coordenador", "suporte"]:
                continue
            if id_usuario_logado and row.get("id") == id_usuario_logado:
                continue
            contatos.append(mapear_contato(row, id_usuario_logado))
        return {"success": True, "data": contatos}

    def obter_mensagens(self, usuario_id: int, conversa_id: int) -> dict:
        rows = self.repo.obter_mensagens(usuario_id, conversa_id)
        return {"success": True, "data": [mapear_mensagem(r) for r in rows]}

    def enviar_mensagem(self, usuario_id: int, destinatario_id: int, texto: str) -> dict:
        msg_id = self.repo.enviar_mensagem(usuario_id, destinatario_id, texto)
        return {"success": True, "data": {"id": msg_id}}

    def obter_mensagens_grupo(self) -> dict:
        rows = self.repo.obter_mensagens_grupo()
        return {"success": True, "data": [mapear_mensagem(r) for r in rows]}

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


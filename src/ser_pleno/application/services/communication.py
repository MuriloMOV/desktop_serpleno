from __future__ import annotations

import logging
import mimetypes
import os
from typing import Any

from ser_pleno.infrastructure.api.mural import ServicoMural

logger = logging.getLogger(__name__)

ALLOWED_ATTACHMENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024


class ServicoComunicacao:
    def __init__(self, auth_service=None):
        self._auth_service = auth_service
        self._mural = ServicoMural(auth_service=auth_service)

    def listar_mensagens(self, busca=None, pagina=1, categoria=None, status=None, data_inicio=None, data_fim=None):
        return self._mural.listar_mensagens(
            busca=busca,
            pagina=pagina,
            categoria=categoria,
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

    def obter_mensagem(self, mensagem_id: int):
        return self._mural.obter_mensagem(mensagem_id)

    def criar_mensagem(self, dados: dict[str, Any]):
        return self._mural.criar_mensagem(dados)

    def atualizar_mensagem(self, mensagem_id: int, dados: dict[str, Any]):
        return self._mural.atualizar_mensagem(mensagem_id, dados)

    def deletar_mensagem(self, mensagem_id: int):
        return self._mural.deletar_mensagem(mensagem_id)

    def upload_attachment(self, filepath: str) -> dict[str, Any]:
        if not os.path.exists(filepath):
            return {"success": False, "message": "Arquivo não encontrado"}
        size = os.path.getsize(filepath)
        if size > MAX_ATTACHMENT_SIZE_BYTES:
            return {"success": False, "message": "Arquivo excede o tamanho máximo permitido"}
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type not in ALLOWED_ATTACHMENT_TYPES:
            return {"success": False, "message": "Tipo de arquivo não permitido"}
        return self._mural.upload_attachment(filepath)

    @staticmethod
    def map_message_to_template(message: dict[str, Any]) -> dict[str, Any]:
        return {
            "subject": message.get("titulo") or message.get("title") or message.get("subject", ""),
            "body": message.get("conteudo") or message.get("content") or message.get("body", ""),
            "author": message.get("autor") or message.get("author") or message.get("sender", ""),
            "created_at": message.get("publicado_em") or message.get("created_at") or message.get("date", ""),
            "category": message.get("categoria") or message.get("category") or "informativo",
            "attachments": message.get("attachments") or message.get("blocos") or [],
        }

# -*- coding: utf-8 -*-
"""Controller de Quadro de Avisos — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.mural import ServicoMural


class QuadroAvisosController(BaseController):
    """Coordena as requisições da View de Quadro de Avisos."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoMural, auth_service=auth_service)
        self.app = app

    def get_service(self):
        return self._service

    def listar_mensagens(self):
        """Lista publicações do mural."""
        return self._service.listar_mensagens()

    def obter_mensagem(self, mensagem_id):
        """Obtém uma publicação específica."""
        return self._service.obter_mensagem(mensagem_id)

    def criar_mensagem(self, payload):
        """Cria uma nova publicação."""
        return self._service.criar_mensagem(payload)

    def atualizar_mensagem(self, mensagem_id, payload):
        """Atualiza uma publicação existente."""
        return self._service.atualizar_mensagem(mensagem_id, payload)

    def deletar_mensagem(self, mensagem_id):
        """Deleta uma publicação."""
        return self._service.deletar_mensagem(mensagem_id)

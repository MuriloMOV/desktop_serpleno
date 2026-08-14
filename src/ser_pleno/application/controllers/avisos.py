# -*- coding: utf-8 -*-
"""Controller de Quadro de Avisos — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.mural import ServicoMural


class AvisosController(BaseController):
    """Coordena as requisições da View de Quadro de Avisos."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoMural, auth_service=auth_service)
        self.usuario_logado = getattr(app, "usuario_logado", None) if app else None

    def get_service(self):
        return self._service

    def listar_mensagens(self, busca=None, pagina=1):
        return self._service.listar_mensagens(busca=busca, pagina=pagina)

    def obter_mensagem(self, mensagem_id):
        return self._service.obter_mensagem(mensagem_id)

    def criar_mensagem(self, payload):
        return self._service.criar_mensagem(payload)

    def atualizar_mensagem(self, mensagem_id, payload):
        return self._service.atualizar_mensagem(mensagem_id, payload)

    def deletar_mensagem(self, mensagem_id):
        return self._service.deletar_mensagem(mensagem_id)

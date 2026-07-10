# -*- coding: utf-8 -*-
"""Controller de Autenticação — mediação explícita entre View e Service."""

from ser_pleno.application.services.autenticacao import ServicoAutenticacao
from ser_pleno.application.controllers.base import BaseController


class AutenticacaoController(BaseController):
    """Controller para autenticação."""

    def __init__(self):
        super().__init__(ServicoAutenticacao)

    @property
    def auth_service(self):
        """Retorna a instância do serviço de autenticação subjacente."""
        return self.get_service()

    def login(self, usuario, senha):
        return self.get_service().login(usuario, senha)

    def alterar_senha(self, senha_atual, nova_senha):
        return self.get_service().alterar_senha(senha_atual, nova_senha)

# -*- coding: utf-8 -*-
"""Controller de Configurações — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.configuracoes import ServicoConfiguracoes
from ser_pleno.application.services.autenticacao import ServicoAutenticacao


class ConfiguracoesController(BaseController):
    """Coordena as requisições da View de Configurações."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoConfiguracoes, auth_service=auth_service)
        self.app = app
        self.usuario_logado = getattr(app, "usuario_logado", None) if app else None
        self.usuario_logado_id = getattr(app, "usuario_logado_id", None) if app else None
        self._servico_autenticacao = ServicoAutenticacao()

    def get_service(self):
        return self._service

    def obter_configuracoes(self):
        """Obtém as configurações do sistema."""
        return self._service.obter_configuracoes()

    def atualizar_configuracoes(self, dados):
        """Atualiza as configurações do sistema."""
        return self._service.atualizar_configuracoes(dados)

    def alterar_senha(self, senha_atual, nova_senha):
        """Altera a senha do usuário logado."""
        return self._servico_autenticacao.alterar_senha(senha_atual, nova_senha)

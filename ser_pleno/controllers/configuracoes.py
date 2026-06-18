# -*- coding: utf-8 -*-
"""Controller de Configurações — mediação entre View e Services."""

from services.configuracoes import ServicoConfiguracoes


class ConfiguracoesController:
    """Coordena as requisições da View de Configurações."""

    def __init__(self, servico=None):
        self.servico = servico or ServicoConfiguracoes()

    def obter_configuracoes(self):
        return self.servico.obter_configuracoes()

    def atualizar_configuracoes(self, dados):
        return self.servico.atualizar_configuracoes(dados)

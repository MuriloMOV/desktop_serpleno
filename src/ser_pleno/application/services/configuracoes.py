# -*- coding: utf-8 -*-
"""Service de ConfiguraçÓµes — orquestrador, sem SQL inline."""

from ser_pleno.repositories.configuracoes import ConfiguracoesRepository


class ServicoConfiguracoes:
    def __init__(self):
        self.repo = ConfiguracoesRepository()

    def obter_configuracoes(self):
        result = self.repo.obter_configuracoes()
        return {"success": True, "data": result}

    def atualizar_configuracoes(self, dados):
        self.repo.atualizar_configuracoes(dados)
        return {"success": True, "message": "ConfiguraçÓµes atualizadas com sucesso"}

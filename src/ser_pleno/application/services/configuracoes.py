# -*- coding: utf-8 -*-
"""Service de Configurações — orquestrador, sem SQL inline."""

from ser_pleno.repositories.configuracoes import ConfiguracoesRepository
from ser_pleno.repositories.autenticacao import AutenticacaoRepository


class ServicoConfiguracoes:
    def __init__(self, auth_service=None):
        self.repo = ConfiguracoesRepository()
        self._auth_service = auth_service

    def obter_configuracoes(self):
        result = self.repo.obter_configuracoes()
        return {"success": True, "data": result}

    def atualizar_configuracoes(self, dados):
        self.repo.atualizar_configuracoes(dados)
        return {"success": True, "message": "Configurações atualizadas com sucesso"}

    def atualizar_perfil(self, dados):
        try:
            if not self._auth_service or not self._auth_service.user:
                return {"success": False, "message": "Nenhum usuário logado"}
            user_id = self._auth_service.user.get("id")
            repo = AutenticacaoRepository()
            repo.atualizar_usuario(
                user_id,
                email=dados.get("email"),
                first_name=dados.get("first_name"),
                last_name=dados.get("last_name"),
            )
            return {"success": True, "message": "Perfil atualizado com sucesso"}
        except Exception as e:
            return {"success": False, "message": str(e)}


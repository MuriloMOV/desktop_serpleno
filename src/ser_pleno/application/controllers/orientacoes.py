# -*- coding: utf-8 -*-
"""Controller de Orientações — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.orientacoes import ServicoOrientacoes


class OrientacoesController(BaseController):
    """Coordena as requisições da View de Orientações."""

    def __init__(self, auth_service=None):
        super().__init__(ServicoOrientacoes, auth_service=auth_service)

    def get_service(self):
        return self._service

    def listar_orientacoes(self, id_estudante=None, tema=None, pagina=1):
        """Lista orientações com filtros opcionais."""
        return self._service.listar_orientacoes(id_estudante, tema, pagina)

    def obter_orientacao(self, id_orientacao):
        """Obtém detalhes de uma orientação específica."""
        return self._service.obter_orientacao(id_orientacao)

    def criar_orientacao(self, dados, arquivos=None):
        """Cria uma nova orientação."""
        return self._service.criar_orientacao(dados, arquivos)

    def atualizar_orientacao(self, id_orientacao, dados, arquivos=None):
        """Atualiza uma orientação existente."""
        return self._service.atualizar_orientacao(id_orientacao, dados, arquivos)

    def deletar_orientacao(self, id_orientacao):
        """Deleta uma orientação."""
        return self._service.deletar_orientacao(id_orientacao)

    def get_preset(self, chave):
        """Retorna um preset específico."""
        return self._service.get_preset(chave)

    def get_presets(self):
        """Retorna todos os presets disponíveis."""
        return self._service.get_presets()

    def duplicar_orientacao(self, id_orientacao, id_estudante=None):
        """Duplica uma orientação existente."""
        return self._service.duplicar_orientacao(id_orientacao, id_estudante)

    def obter_estatisticas(self, id_estudante=None):
        """Obtém estatísticas das orientações."""
        return self._service.obter_estatisticas(id_estudante)

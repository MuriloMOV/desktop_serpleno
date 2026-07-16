# -*- coding: utf-8 -*-
"""Controller de Análise de Triagem — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.triagem import ServicoTriagem


class TriagemController(BaseController):
    """Coordena as requisições da View de Análise de Triagem."""

    def __init__(self):
        super().__init__(ServicoTriagem)

    def get_service(self):
        return self._service

    def listar_triagens(self, busca=None, status=None, prioridade=None, id_estudante=None, pagina=1):
        """Lista triagens com filtros opcionais."""
        return self._service.listar_triagens(busca, status, prioridade, id_estudante, pagina)

    def obter_triagem(self, id_triagem):
        """Obtém detalhes de uma triagem específica."""
        return self._service.obter_triagem(id_triagem)

    def criar_triagem(self, dados):
        """Cria uma nova triagem."""
        return self._service.criar_triagem(dados)

    def atualizar_triagem(self, id_triagem, dados):
        """Atualiza uma triagem existente."""
        return self._service.atualizar_triagem(id_triagem, dados)

    def deletar_triagem(self, id_triagem):
        """Deleta uma triagem."""
        return self._service.deletar_triagem(id_triagem)

    def listar_formularios(self):
        """Lista formulários de triagem disponíveis."""
        return self._service.listar_formularios()

# -*- coding: utf-8 -*-
"""Controller de Estudantes — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.estudantes import ServicoEstudante


class EstudantesController(BaseController):
    """Coordena as requisições da View de Estudantes."""

    def __init__(self, auth_service=None):
        super().__init__(ServicoEstudante, auth_service=auth_service)

    def get_service(self):
        return self._service

    def listar_estudantes(self, busca=None, possui_laudo=None, requer_atencao=None, pagina=1):
        """Lista estudantes com filtros opcionais."""
        return self._service.listar_estudantes(busca, possui_laudo, requer_atencao, pagina)

    def obter_estudante(self, id_estudante):
        """Obtém detalhes de um estudante específico."""
        return self._service.obter_estudante(id_estudante)

    def criar_estudante(self, dados):
        """Cria um novo estudante."""
        return self._service.criar_estudante(dados)

    def atualizar_estudante(self, id_estudante, dados):
        """Atualiza um estudante existente."""
        return self._service.atualizar_estudante(id_estudante, dados)

    def deletar_estudante(self, id_estudante):
        """Deleta um estudante."""
        return self._service.deletar_estudante(id_estudante)

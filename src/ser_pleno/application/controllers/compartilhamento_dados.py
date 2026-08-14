# -*- coding: utf-8 -*-
"""Controller de Compartilhamento de Dados Clínicos — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.compartilhamento_dados import ServicoCompartilhamentoDadosClinicos


class CompartilhamentoDadosController(BaseController):
    """Coordena as requisições da View de Compartilhamento de Dados Clínicos."""

    def __init__(self):
        super().__init__(ServicoCompartilhamentoDadosClinicos)

    def get_service(self):
        return self._service

    def listar_compartilhamentos(
        self,
        busca: str = None,
        data_type: str = None,
        student_id: int = None,
        page: int = 1,
    ):
        """Lista compartilhamentos com filtros opcionais."""
        return self._service.listar_compartilhamentos(
            busca=busca, data_type=data_type, student_id=student_id, page=page
        )

    def compartilhar(self, dados: dict):
        """Compartilha dados clínicos com outro usuário."""
        return self._service.compartilhar(dados)

    def descompartilhar(self, dados: dict):
        """Descompartilha dados clínicos."""
        return self._service.descompartilhar(dados)

    def bulk_share(self, dados: dict):
        """Compartilhamento em massa."""
        return self._service.bulk_share(dados)

    def bulk_unshare(self, dados: dict):
        """Descompartilhamento em massa."""
        return self._service.bulk_unshare(dados)

    def listar_estudantes_compartilhados(self):
        """Lista estudantes compartilhados com o usuário atual."""
        return self._service.listar_estudantes_compartilhados()

    def obter_historico_compartilhamento(self, student_id: int):
        """Obtém histórico de compartilhamento por estudante."""
        return self._service.obter_historico_compartilhamento(student_id)

    def obter_relatorio_compartilhamento(self):
        """Obtém relatório de compartilhamento."""
        return self._service.obter_relatorio_compartilhamento()

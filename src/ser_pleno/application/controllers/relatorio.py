# -*- coding: utf-8 -*-
"""Controller de Relatórios — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.relatorios import ServicoRelatorio


class RelatorioController(BaseController):
    """Coordena as requisições da View de Relatórios."""

    def __init__(self):
        super().__init__(ServicoRelatorio)

    def get_service(self):
        return self._service

    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1):
        """Lista relatórios com filtros opcionais."""
        return self._service.listar_relatorios(tipo, data_inicio, pagina)

    def obter_estatisticas(self, periodo='month'):
        """Obtém estatísticas básicas."""
        return self._service.obter_estatisticas(periodo)

    def gerar_relatorio(self, dados):
        """Gera um novo relatório."""
        return self._service.gerar_relatorio(dados)

    def baixar_relatorio(self, id_relatorio):
        """Obtém o caminho de um relatório para download."""
        return self._service.baixar_relatorio(id_relatorio)

    def deletar_relatorio(self, id_relatorio):
        """Deleta um relatório."""
        return self._service.deletar_relatorio(id_relatorio)

    def exportar_estudantes(self):
        """Exporta todos os estudantes."""
        return self._service.exportar_estudantes()

    def exportar_agendamentos(self):
        """Exporta todos os agendamentos."""
        return self._service.exportar_agendamentos()

    def exportar_triagens(self):
        """Exporta todas as triagens."""
        return self._service.exportar_triagens()

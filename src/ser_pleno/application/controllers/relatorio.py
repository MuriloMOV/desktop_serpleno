# -*- coding: utf-8 -*-
"""Controller de Relatórios — mediação entre View e Services."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.relatorios import ServicoRelatorio


class RelatorioController(BaseController):
    """Coordena as requisições da View de Relatórios."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoRelatorio, auth_service=auth_service)
        self.app = app

    def get_service(self) -> ServicoRelatorio:
        return self._service

    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1, search=None, data_fim=None):
        """Lista relatórios com filtros opcionais."""
        return self._service.listar_relatorios(tipo, data_inicio, pagina, search, data_fim)

    def obter_estatisticas(self, periodo='month'):
        """Obtém estatísticas básicas."""
        return self._service.obter_estatisticas(periodo)

    def obter_comparacao_estatisticas(self, periodo_inicio, periodo_fim):
        """Obtém comparação de estatísticas entre dois períodos."""
        return self._service.obter_comparacao_estatisticas(periodo_inicio, periodo_fim)

    def gerar_relatorio(self, dados):
        """Gera um novo relatório."""
        return self._service.gerar_relatorio(dados)

    def gerar_relatorio_por_template(self, id_template: int, parametros: Optional[dict] = None):
        """Gera relatório baseado em template."""
        return self._service.gerar_relatorio_por_template(id_template, parametros)

    def baixar_relatorio(self, id_relatorio):
        """Obtém o caminho de um relatório para download."""
        return self._service.baixar_relatorio(id_relatorio)

    def deletar_relatorio(self, id_relatorio):
        """Deleta um relatório."""
        return self._service.deletar_relatorio(id_relatorio)

    def deletar_lote(self, ids_relatorios: List[int]):
        """Deleta múltiplos relatórios."""
        return self._service.deletar_lote(ids_relatorios)

    def baixar_lote(self, ids_relatorios: List[int]):
        """Download de múltiplos relatórios."""
        return self._service.baixar_lote(ids_relatorios)

    def exportar_estudantes(self):
        """Exporta todos os estudantes."""
        return self._service.exportar_estudantes()

    def exportar_agendamentos(self):
        """Exporta todos os agendamentos."""
        return self._service.exportar_agendamentos()

    def exportar_triagens(self):
        """Exporta todas as triagens."""
        return self._service.exportar_triagens()

    def listar_templates(self, tipo=None, apenas_ativos=True):
        """Lista templates de relatório."""
        from ser_pleno.application.services.report_templates import ServicoReportTemplate
        svc = ServicoReportTemplate(auth_service=getattr(self, '_auth_service', None))
        return svc.listar_templates(tipo, apenas_ativos)

    def criar_template(self, dados: Dict[str, Any]):
        """Cria template de relatório."""
        from ser_pleno.application.services.report_templates import ServicoReportTemplate
        svc = ServicoReportTemplate(auth_service=getattr(self, '_auth_service', None))
        return svc.criar_template(dados)

    def atualizar_template(self, id_template: int, dados: Dict[str, Any]):
        """Atualiza template de relatório."""
        from ser_pleno.application.services.report_templates import ServicoReportTemplate
        svc = ServicoReportTemplate(auth_service=getattr(self, '_auth_service', None))
        return svc.atualizar_template(id_template, dados)

    def deletar_template(self, id_template: int):
        """Deleta template de relatório."""
        from ser_pleno.application.services.report_templates import ServicoReportTemplate
        svc = ServicoReportTemplate(auth_service=getattr(self, '_auth_service', None))
        return svc.deletar_template(id_template)

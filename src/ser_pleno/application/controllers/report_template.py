# -*- coding: utf-8 -*-
"""Controller de Templates de Relatorio — mediacao entre View e Services."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.report_templates import ServicoReportTemplate


class ReportTemplateController(BaseController):
    """Coordena as requisicoes da View de Templates de Relatorio."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoReportTemplate, auth_service=auth_service)
        self.app = app
        self.usuario_logado_id = getattr(app, "usuario_logado_id", None) if app else None

    def get_service(self):
        return self._service

    def listar_templates(self, tipo: Optional[str] = None, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        return self._service.listar_templates(tipo, apenas_ativos)

    def obter_template(self, id_template: int) -> Dict[str, Any]:
        return self._service.obter_template(id_template)

    def criar_template(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        dados["created_by_id"] = dados.get("created_by_id") or self.usuario_logado_id or 1
        return self._service.criar_template(dados)

    def atualizar_template(self, id_template: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        return self._service.atualizar_template(id_template, dados)

    def deletar_template(self, id_template: int) -> Dict[str, Any]:
        return self._service.deletar_template(id_template)

    def gerar_preview(self, id_template: int, parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._service.gerar_preview(id_template, parametros)

    def aplicar_template_em_dados(self, id_template: int, parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._service.aplicar_template_em_dados(id_template, parametros)

    def listar_tipos_disponiveis(self) -> List[str]:
        return self._service.listar_tipos_disponiveis()

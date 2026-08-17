# -*- coding: utf-8 -*-
"""Servico de templates de relatorio com fallback para API web e repositorio local."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ser_pleno.features.report_template.repo import ReportTemplateRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.utils.api_fallback import api_fallback

logger = logging.getLogger(__name__)


class ServicoReportTemplate:
    def __init__(self, auth_service=None):
        self.repo = ReportTemplateRepository()
        self._auth_service = auth_service
        self._api = ClienteAPI(auth_service=auth_service)
        self._operation_config = None

    def _get_operation_config(self):
        if self._operation_config is None:
            try:
                from ser_pleno.config.operation_mode import get_operation_config
                self._operation_config = get_operation_config()
            except Exception:
                pass
        return self._operation_config

    def _should_use_api(self) -> bool:
        config = self._get_operation_config()
        if config is None:
            return True
        return config.should_use_api()

    @api_fallback("_fallback_listar_templates")
    def listar_templates(self, tipo: Optional[str] = None, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        if not self._should_use_api():
            return self._local_listar_templates(tipo, apenas_ativos)

        def _api_call():
            params: Dict[str, Any] = {}
            if tipo:
                params["report_type"] = tipo
            if not apenas_ativos:
                params["is_active"] = "false"
            resp = self._api.get("desktop/reports/templates/", params=params if params else None)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_listar_templates(self, tipo=None, apenas_ativos=True):
        rows = self.repo.listar_templates(tipo, apenas_ativos)
        return {"success": True, "data": rows}

    @api_fallback("_fallback_obter_template")
    def obter_template(self, id_template: int) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_obter_template(id_template)

        def _api_call():
            resp = self._api.get(f"desktop/reports/templates/{id_template}/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_obter_template(self, id_template=None):
        row = self.repo.obter_template_por_id(id_template)
        if row:
            return {"success": True, "data": row}
        return {"success": False, "message": "Template não encontrado"}

    @api_fallback("_fallback_criar_template")
    def criar_template(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        nome = dados.get("name", "")
        report_type = dados.get("report_type", "geral")
        template_config = dados.get("template_config", {})
        default_parameters = dados.get("default_parameters", {})
        is_active = dados.get("is_active", True)
        created_by_id = dados.get("created_by_id") or 1

        if not nome:
            return {"success": False, "message": "Nome do template é obrigatório."}

        if not self._should_use_api():
            return self._local_criar_template(nome, report_type, template_config, default_parameters, is_active, created_by_id)

        def _api_call():
            payload = {
                "name": nome,
                "report_type": report_type,
                "template_config": template_config,
                "default_parameters": default_parameters,
                "is_active": is_active,
                "created_by_id": created_by_id,
            }
            resp = self._api.post("desktop/reports/templates/create/", json=payload)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_criar_template(self, dados):
        nome = dados.get("name", "")
        report_type = dados.get("report_type", "geral")
        template_config = dados.get("template_config", {})
        default_parameters = dados.get("default_parameters", {})
        is_active = dados.get("is_active", True)
        created_by_id = dados.get("created_by_id") or 1
        last_id = self.repo.criar_template(
            nome, report_type, template_config, default_parameters, is_active, created_by_id
        )
        row = self.repo.obter_template_por_id(last_id)
        return {"success": True, "data": row}

    @api_fallback("_fallback_atualizar_template")
    def atualizar_template(self, id_template: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        nome = dados.get("name")
        report_type = dados.get("report_type")
        template_config = dados.get("template_config")
        default_parameters = dados.get("default_parameters")
        is_active = dados.get("is_active")

        if not self._should_use_api():
            return self._local_atualizar_template(id_template, nome, report_type, template_config, default_parameters, is_active)

        def _api_call():
            payload = {}
            if nome is not None:
                payload["name"] = nome
            if report_type is not None:
                payload["report_type"] = report_type
            if template_config is not None:
                payload["template_config"] = template_config
            if default_parameters is not None:
                payload["default_parameters"] = default_parameters
            if is_active is not None:
                payload["is_active"] = is_active
            resp = self._api.post(f"desktop/reports/templates/{id_template}/update/", json=payload)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_atualizar_template(self, id_template, dados):
        nome = dados.get("name")
        report_type = dados.get("report_type")
        template_config = dados.get("template_config")
        default_parameters = dados.get("default_parameters")
        is_active = dados.get("is_active")
        ok = self.repo.atualizar_template(
            id_template, nome, report_type, template_config, default_parameters, is_active
        )
        if ok:
            row = self.repo.obter_template_por_id(id_template)
            return {"success": True, "data": row}
        return {"success": False, "message": "Template não encontrado"}

    @api_fallback("_fallback_deletar_template")
    def deletar_template(self, id_template: int) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_deletar_template(id_template)

        def _api_call():
            resp = self._api.delete(f"desktop/reports/templates/{id_template}/delete/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_deletar_template(self, id_template=None):
        ok = self.repo.deletar_template(id_template)
        if ok:
            return {"success": True, "message": "Template excluído com sucesso"}
        return {"success": False, "message": "Template não encontrado"}

    def gerar_preview(self, id_template: int, parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        row = self.repo.obter_template_por_id(id_template)
        if not row:
            return {"success": False, "message": "Template não encontrado"}

        params = dict(row.get("default_parameters") or {})
        if parametros:
            params.update(parametros)

        report_type = row.get("report_type", "geral")
        try:
            from ser_pleno.features.relatorio.service import ServicoRelatorio
            servico_rel = ServicoRelatorio(auth_service=self._auth_service)
            if report_type == "estudante":
                res = servico_rel.exportar_estudantes(params)
            elif report_type == "agendamentos":
                res = servico_rel.exportar_agendamentos(params)
            elif report_type == "triagens":
                res = servico_rel.exportar_triagens(params)
            elif report_type == "intervencoes":
                res = servico_rel.exportar_intervencoes(params)
            elif report_type in ("geral", "estatisticas"):
                res = servico_rel.obter_estatisticas()
            else:
                res = servico_rel.listar_relatorios_filtrados(tipo=report_type, data_inicio=params.get("data_inicio"), data_fim=params.get("data_fim"))
            return res
        except Exception as exc:
            logger.warning("Falha ao gerar preview do template %s: %s", id_template, exc)
            return {"success": False, "message": str(exc)}

    def aplicar_template_em_dados(self, id_template: int, parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        row = self.repo.obter_template_por_id(id_template)
        if not row:
            return {"success": False, "message": "Template não encontrado"}

        params = dict(row.get("default_parameters") or {})
        if parametros:
            params.update(parametros)

        nome = row.get("name", "Template")
        report_type = row.get("report_type", "geral")
        return {
            "success": True,
            "data": {
                "name": nome,
                "report_type": report_type,
                "parameters": params,
                "template_config": row.get("template_config", {}),
            }
        }

    def listar_tipos_disponiveis(self) -> List[str]:
        return ["geral", "estudante", "agendamentos", "triagens", "estatisticas", "intervencoes"]

    # ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  Helpers locais (fallback)
    # ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

    def _local_listar_templates(self, tipo=None, apenas_ativos=True):
        rows = self.repo.listar_templates(tipo, apenas_ativos)
        return {"success": True, "data": rows}

    def _local_obter_template(self, id_template):
        row = self.repo.obter_template_por_id(id_template)
        if row:
            return {"success": True, "data": row}
        return {"success": False, "message": "Template não encontrado"}

    def _local_criar_template(self, nome, report_type, template_config, default_parameters, is_active, created_by_id):
        last_id = self.repo.criar_template(nome, report_type, template_config, default_parameters, is_active, created_by_id)
        row = self.repo.obter_template_por_id(last_id)
        return {"success": True, "data": row}

    def _local_atualizar_template(self, id_template, nome, report_type, template_config, default_parameters, is_active):
        ok = self.repo.atualizar_template(id_template, nome, report_type, template_config, default_parameters, is_active)
        if ok:
            row = self.repo.obter_template_por_id(id_template)
            return {"success": True, "data": row}
        return {"success": False, "message": "Template não encontrado"}

    def _local_deletar_template(self, id_template):
        ok = self.repo.deletar_template(id_template)
        if ok:
            return {"success": True, "message": "Template excluído com sucesso"}
        return {"success": False, "message": "Template não encontrado"}

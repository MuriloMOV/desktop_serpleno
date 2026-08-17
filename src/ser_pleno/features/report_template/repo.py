# -*- coding: utf-8 -*-
"""Repositorio de templates de relatorio."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
    generate_local_id,
)
from ser_pleno.infrastructure.local.local_cache import validate_table_name


class ReportTemplateRepository:
    @with_local_fallback("_local_listar_templates")
    def listar_templates(self, tipo: Optional[str] = None, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        query = "SELECT * FROM desktop_report_template WHERE 1=1"
        params = []
        if apenas_ativos:
            query += " AND is_active = TRUE"
        if tipo:
            query += " AND report_type = %s"
            params.append(tipo)
        query += " ORDER BY name ASC"
        return fetch_all(query, params)

    def _local_listar_templates(self, tipo: Optional[str] = None, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        rows = local_cache.list_report_templates()
        if tipo:
            rows = [r for r in rows if r.get("report_type") == tipo]
        if apenas_ativos:
            rows = [r for r in rows if r.get("is_active", True)]
        return rows

    @with_local_fallback("_local_obter_template_por_id")
    def obter_template_por_id(self, id_template: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM desktop_report_template WHERE id = %s"
        return fetch_one(query, (id_template,))

    def _local_obter_template_por_id(self, id_template: int) -> Optional[Dict[str, Any]]:
        rows = local_cache.list_report_templates()
        for r in rows:
            if r.get("id") == id_template:
                return r
        return None

    def criar_template(self, nome: str, report_type: str, template_config: Dict[str, Any],
                       default_parameters: Dict[str, Any], is_active: bool = True,
                       created_by_id: int = 1) -> int:
        template_config_json = json.dumps(template_config or {})
        default_parameters_json = json.dumps(default_parameters or {})
        query = """
            INSERT INTO desktop_report_template (
                name, report_type, template_config, default_parameters,
                is_active, created_by_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        params = (nome, report_type, template_config_json, default_parameters_json,
                  is_active, created_by_id)
        template_data = {
            "name": nome,
            "report_type": report_type,
            "template_config": template_config,
            "default_parameters": default_parameters,
            "is_active": is_active,
            "created_by_id": created_by_id,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            template_data["id"] = last_id
            local_cache.upsert_report_template(template_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            template_data["id"] = last_id
            return template_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="report_templates", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def atualizar_template(self, id_template: int, nome: Optional[str] = None,
                           report_type: Optional[str] = None,
                           template_config: Optional[Dict[str, Any]] = None,
                           default_parameters: Optional[Dict[str, Any]] = None,
                           is_active: Optional[bool] = None) -> bool:
        sets = []
        params = []
        if nome is not None:
            sets.append("name = %s")
            params.append(nome)
        if report_type is not None:
            sets.append("report_type = %s")
            params.append(report_type)
        if template_config is not None:
            sets.append("template_config = %s")
            params.append(json.dumps(template_config))
        if default_parameters is not None:
            sets.append("default_parameters = %s")
            params.append(json.dumps(default_parameters))
        if is_active is not None:
            sets.append("is_active = %s")
            params.append(is_active)
        if not sets:
            return False
        sets.append("updated_at = NOW()")
        params.append(id_template)
        query = f"UPDATE desktop_report_template SET {', '.join(sets)} WHERE id = %s"

        def _mysql():
            execute_non_query(query, tuple(params))
            return True

        def _local(mysql_result):
            row = self._local_obter_template_por_id(id_template)
            if not row:
                return False
            if nome is not None:
                row["name"] = nome
            if report_type is not None:
                row["report_type"] = report_type
            if template_config is not None:
                row["template_config"] = template_config
            if default_parameters is not None:
                row["default_parameters"] = default_parameters
            if is_active is not None:
                row["is_active"] = is_active
            local_cache.upsert_report_template(row)
            return True

        def _queue_data(mysql_result, entity_id):
            row = self._local_obter_template_por_id(id_template)
            if not row:
                return None
            if nome is not None:
                row["name"] = nome
            if report_type is not None:
                row["report_type"] = report_type
            if template_config is not None:
                row["template_config"] = template_config
            if default_parameters is not None:
                row["default_parameters"] = default_parameters
            if is_active is not None:
                row["is_active"] = is_active
            return row

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="report_templates", entity_id=id_template,
            queue_data_fn=_queue_data,
        )

    def deletar_template(self, id_template: int) -> bool:
        query = "DELETE FROM desktop_report_template WHERE id = %s"

        def _mysql():
            execute_non_query(query, (id_template,))
            return True

        def _local(mysql_result):
            validate_table_name("report_templates")
            local_cache.delete("report_templates", "id", id_template)
            return True

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="report_templates", entity_id=id_template,
            queue_data_fn=lambda r, eid: {"id": id_template},
        )

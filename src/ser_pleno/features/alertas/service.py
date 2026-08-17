# -*- coding: utf-8 -*-
"""Service de Alertas Avancados — orquestrador."""

from ser_pleno.features.alertas.repo import AlertasRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.config.operation_mode import get_operation_config
from ser_pleno.utils.cache import TTLCache
import logging

logger = logging.getLogger(__name__)


def _safe_str(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    return str(value)


def _safe_bool(value) -> bool:
    return bool(value)


def _map_alert(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "alert_type": row.get("alert_type"),
        "severity": row.get("severity"),
        "message": row.get("message"),
        "details": row.get("details"),
        "is_read": _safe_bool(row.get("is_read")),
        "is_resolved": _safe_bool(row.get("is_resolved")),
        "resolved_at": _safe_str(row.get("resolved_at")),
        "created_at": _safe_str(row.get("created_at")),
        "assigned_to_id": row.get("assigned_to_id"),
        "resolved_by_id": row.get("resolved_by_id"),
        "student_id": row.get("student_id"),
    }


class ServicoAlertas:
    def __init__(self, auth_service=None):
        self.repo = AlertasRepository()
        self._api = ClienteAPI(auth_service=auth_service)
        self._auth_service = auth_service
        self._critical_cache = TTLCache(ttl=60)

    def listar_alertas(self, filters=None):
        config = get_operation_config()
        if config.should_use_api():
            try:
                params = self._build_params(filters)
                response = self._api.get("alerts/", params=params if params else None)
                if response.get("success"):
                    return {"success": True, "data": [_map_alert(r) for r in response.get("data", [])]}
            except Exception as e:
                logger.error("Erro ao listar alertas via API: %s", e)

        rows = self.repo.listar_alertas(filters)
        return {"success": True, "data": [_map_alert(r) for r in rows]}

    def _build_params(self, filters):
        params = {}
        if not filters:
            return params
        mapping = {
            "alert_type": "alert_type",
            "severity": "severity",
            "is_read": "is_read",
            "is_resolved": "is_resolved",
            "data_inicio": "data_inicio",
            "data_fim": "data_fim",
        }
        for key, param_key in mapping.items():
            val = filters.get(key)
            if val is not None and val != "":
                params[param_key] = val
        return params

    def get_alertas_criticos(self):
        cached = self._critical_cache.get()
        if cached is not None:
            return cached

        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.get("alerts/critical/")
                if response.get("success"):
                    data = response.get("data", [])
                    self._critical_cache.set(data)
                    return data
            except Exception as e:
                logger.error("Erro ao obter alertas criticos via API: %s", e)

        rows = self.repo.listar_alertas({"severity": "critical", "is_read": False})
        data = [_map_alert(r) for r in rows]
        self._critical_cache.set(data)
        return data

    def marcar_alerta_lido(self, alert_id):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post(f"alerts/{alert_id}/read/")
                if response.get("success"):
                    return {"success": True, "message": "Alerta marcado como lido"}
            except Exception as e:
                logger.error("Erro ao marcar alerta como lido via API: %s", e)

        self.repo.marcar_alerta_lido(alert_id)
        return {"success": True, "message": "Alerta marcado como lido"}

    def dispensar_alerta(self, alert_id):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post(f"alerts/{alert_id}/dismiss/")
                if response.get("success"):
                    return {"success": True, "message": "Alerta dispensado"}
            except Exception as e:
                logger.error("Erro ao dispensar alerta via API: %s", e)

        self.repo.dispensar_alerta(alert_id)
        return {"success": True, "message": "Alerta dispensado"}

    def marcar_todos_lidos(self):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.post("alerts/read-all/")
                if response.get("success"):
                    return {"success": True, "message": "Todos os alertas marcados como lidos"}
            except Exception as e:
                logger.error("Erro ao marcar todos alertas como lidos via API: %s", e)

        self.repo.marcar_todos_lidos()
        return {"success": True, "message": "Todos os alertas marcados como lidos"}

    def contar_nao_lidos(self):
        config = get_operation_config()
        if config.should_use_api():
            try:
                response = self._api.get("alerts/", params={"is_read": False})
                if response.get("success"):
                    return len(response.get("data", []))
            except Exception as e:
                logger.error("Erro ao contar alertas nao lidos via API: %s", e)

        return self.repo.contar_nao_lidos()

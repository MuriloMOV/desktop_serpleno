from __future__ import annotations

import logging
from typing import Any

from ser_pleno.features.configuracoes.repo import ConfiguracoesRepository
from ser_pleno.repositories.autenticacao import AutenticacaoRepository

logger = logging.getLogger(__name__)

_GLOBAL_SETTINGS_CACHE: dict[str, Any] = {}
_USER_SETTINGS_CACHE: dict[int, dict[str, Any]] = {}


def get_global_settings() -> dict[str, Any]:
    repo = ConfiguracoesRepository()
    result = repo.obter_configuracoes()
    if isinstance(result, list) and result:
        merged: dict[str, Any] = {}
        for item in result:
            chave = item.get("chave") or item.get("key")
            valor = item.get("valor") or item.get("value")
            if chave is not None:
                merged[chave] = valor
        _GLOBAL_SETTINGS_CACHE.clear()
        _GLOBAL_SETTINGS_CACHE.update(merged)
        return dict(merged)
    if _GLOBAL_SETTINGS_CACHE:
        return dict(_GLOBAL_SETTINGS_CACHE)
    return {}


def update_global_settings(settings: dict[str, Any]) -> dict[str, Any]:
    repo = ConfiguracoesRepository()
    for chave, valor in settings.items():
        try:
            repo.atualizar_configuracao(chave, valor)
        except Exception:
            try:
                repo.atualizar_configuracoes({chave: valor})
            except Exception as exc:
                logger.error("Erro ao atualizar setting %s: %s", chave, exc)
    _GLOBAL_SETTINGS_CACHE.clear()
    return {"success": True, "updated": list(settings.keys())}


def get_user_profile_settings(user_id: int) -> dict[str, Any]:
    if user_id in _USER_SETTINGS_CACHE:
        return dict(_USER_SETTINGS_CACHE[user_id])
    repo = AutenticacaoRepository()
    try:
        user = repo.obter_usuario_por_id(user_id)
        if user:
            settings = {
                "email": user.get("email"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "role": user.get("role"),
                "is_staff": bool(user.get("is_staff")),
            }
            _USER_SETTINGS_CACHE[user_id] = settings
            return dict(settings)
    except Exception as exc:
        logger.error("Erro ao obter configurações do usuário %s: %s", user_id, exc)
    return {}


def update_user_profile_settings(user_id: int, settings: dict[str, Any]) -> dict[str, Any]:
    repo = AutenticacaoRepository()
    allowed_keys = {"email", "first_name", "last_name", "role", "is_staff"}
    update_data = {k: v for k, v in settings.items() if k in allowed_keys}
    if not update_data:
        return {"success": False, "message": "Nenhum campo permitido para atualização"}
    try:
        repo.atualizar_usuario(user_id, **update_data)
        _USER_SETTINGS_CACHE.pop(user_id, None)
        return {"success": True, "updated": update_data}
    except Exception as exc:
        logger.error("Erro ao atualizar perfil do usuário %s: %s", user_id, exc)
        return {"success": False, "message": str(exc)}

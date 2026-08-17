# -*- coding: utf-8 -*-
"""Decorator para fallback de API para repositório local."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


def api_fallback(fallback_fn_name: str):
    """Decorator que encapsula o padrão with_api_fallback.

    Uso:
        @api_fallback("_fallback_metodo")
        def metodo(self, ...):
            def _api_call():
                ...
            return _api_call()

    O decorator intercepta o resultado de _api_call() e, em caso de falha,
    chama o método de fallback pelo nome.
    """

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                result = method(self, *args, **kwargs)
                if (
                    result is not None
                    and isinstance(result, dict)
                    and result.get("success") is not False
                    and result.get("data") is not None
                ):
                    return result
            except Exception as e:
                logger.exception("Erro na API: %s", e)

            fallback_fn = getattr(self, fallback_fn_name, None)
            if fallback_fn is None:
                return {"success": False, "error": f"Fallback {fallback_fn_name} não encontrado"}
            return fallback_fn(*args, **kwargs)

        return wrapper

    return decorator

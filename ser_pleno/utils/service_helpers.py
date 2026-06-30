# -*- coding: utf-8 -*-
"""Helpers reutilizáveis para Services."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_api_fallback(api_call_fn: Callable[[], dict], fallback_fn: Callable[..., dict], *args, **kwargs):
    """Executa chamada de API com fallback para repositório/local em caso de falha."""
    try:
        resp = api_call_fn()
        if resp and resp.get("success") is not False and resp.get("data") is not None:
            return resp
    except Exception as e:
        logger.exception("Erro na API: %s", e)
    return fallback_fn(*args, **kwargs)

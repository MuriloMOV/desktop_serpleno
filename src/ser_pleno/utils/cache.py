"""
cache.py —” helper leve de cache em memória com TTL, usado para
reduzir queries repetidas de notificações e outros dados estáticos.
"""

from __future__ import annotations

import logging
import time
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)


class TTLCache:
    """Cache simples com time-to-live em segundos."""

    def __init__(self, ttl: int = 60):
        self._ttl = ttl
        self._ts: float = 0.0
        self._value: Any = None

    def get(self) -> Optional[Any]:
        """Retorna o valor em cache se ainda válido, senão None."""
        if self._value is not None and (time.perf_counter() - self._ts) < self._ttl:
            return self._value
        return None

    def set(self, value: Any) -> None:
        """Atualiza o cache."""
        self._value = value
        self._ts = time.perf_counter()

    def invalidate(self) -> None:
        """Invalida o cache imediatamente."""
        self._value = None
        self._ts = 0.0


class NotificationCache:
    """Cache específico para contagens de notificações do dashboard."""

    def __init__(self, ttl: int = 60):
        self._ajuda = TTLCache(ttl=ttl)
        self._alertas = TTLCache(ttl=ttl)

    def get_ajuda(self) -> Optional[Tuple[list, int]]:
        """Retorna (lista_ajuda, count_ajuda) ou None se cache expirado."""
        return self._ajuda.get()

    def set_ajuda(self, ajuda: list, count: int) -> None:
        self._ajuda.set((ajuda, count))

    def get_alertas(self) -> Optional[Tuple[list, int]]:
        """Retorna (lista_alertas, count_alertas) ou None se cache expirado."""
        return self._alertas.get()

    def set_alertas(self, alertas: list, count: int) -> None:
        self._alertas.set((alertas, count))

    def invalidate_all(self) -> None:
        self._ajuda.invalidate()
        self._alertas.invalidate()


__all__ = ["TTLCache", "NotificationCache"]

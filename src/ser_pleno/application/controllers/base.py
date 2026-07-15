# -*- coding: utf-8 -*-
"""Controller base — interface explícita entre Views e Services."""

from __future__ import annotations

import warnings


class BaseController:
    """Base para controllers com acesso explícito ao service.

    Uso:
        class DashboardController(BaseController):
            def __init__(self):
                super().__init__(ServicoDashboard)
    """

    def __init__(self, service_class, auth_service=None):
        self._service = service_class(auth_service=auth_service)

    def get_service(self):
        """Retorna a instância do service subjacente."""
        return self._service

    def __getattr__(self, name: str):
        """Fallback de compatibilidade (será removido em versão futura).

        Uso correto: controller.get_service().metodo()
        """
        warnings.warn(
            f"Acesso dinâmico a '{name}' no controller é deprecated. "
            f"Use controller.get_service().{name}().",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self._service, name)

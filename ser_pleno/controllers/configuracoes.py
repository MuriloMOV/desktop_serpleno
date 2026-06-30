# -*- coding: utf-8 -*-
"""Controller de Configurações — mediação entre View e Services."""

from controllers.base import BaseController
from services.configuracoes import ServicoConfiguracoes


class ConfiguracoesController(BaseController):
    """Coordena as requisições da View de Configurações."""

    def __init__(self):
        super().__init__(ServicoConfiguracoes)

    def get_service(self):
        return self._service

# -*- coding: utf-8 -*-
"""Controller de ConfiguraçÓµes — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.configuracoes import ServicoConfiguracoes


class ConfiguracoesController(BaseController):
    """Coordena as requisiçÓµes da View de ConfiguraçÓµes."""

    def __init__(self):
        super().__init__(ServicoConfiguracoes)

    def get_service(self):
        return self._service

# -*- coding: utf-8 -*-
"""Controller de Análise de Triagem — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.triagem import ServicoTriagem


class AnaliseTriagemController(BaseController):
    """Coordena as requisiçÓµes da View de Análise de Triagem."""

    def __init__(self):
        super().__init__(ServicoTriagem)

    def get_service(self):
        return self._service

# -*- coding: utf-8 -*-
"""Controller de Estudantes — mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.estudantes import ServicoEstudante


class EstudantesController(BaseController):
    """Coordena as requisiçÓµes da View de Estudantes."""

    def __init__(self):
        super().__init__(ServicoEstudante)

    def get_service(self):
        return self._service

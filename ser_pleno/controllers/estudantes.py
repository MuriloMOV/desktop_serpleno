# -*- coding: utf-8 -*-
"""Controller de Estudantes — mediação entre View e Services."""

from controllers.base import BaseController
from services.estudantes import ServicoEstudante


class EstudantesController(BaseController):
    """Coordena as requisições da View de Estudantes."""

    def __init__(self):
        super().__init__(ServicoEstudante)

    def get_service(self):
        return self._service

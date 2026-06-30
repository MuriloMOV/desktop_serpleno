# -*- coding: utf-8 -*-
"""Controller de Bem-Estar — mediação entre View e Services."""

from controllers.base import BaseController
from services.bem_estar import ServicoBemEstar


class BemEstarController(BaseController):
    """Coordena as requisições da View de Bem-Estar."""

    def __init__(self):
        super().__init__(ServicoBemEstar)

    def get_service(self):
        return self._service

# -*- coding: utf-8 -*-
"""Controller de Bem-Estar — mediação explícita entre View e Service."""

from ser_pleno.application.services.bem_estar import ServicoBemEstar
from ser_pleno.application.controllers.base import BaseController


class BemEstarController(BaseController):
    """Controller para a view de Bem-Estar."""

    def __init__(self):
        super().__init__(ServicoBemEstar)

    def obter_dashboard(self):
        return self.get_service().obter_dashboard()

    def listar_checkins(self):
        return self.get_service().listar_checkins()

    def listar_estudantes_risco(self):
        return self.get_service().listar_estudantes_risco()

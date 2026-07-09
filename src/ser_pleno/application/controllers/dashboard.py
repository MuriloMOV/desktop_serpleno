# -*- coding: utf-8 -*-
"""Controller de Dashboard —” mediação entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.dashboard import ServicoDashboard


class DashboardController(BaseController):
    """Coordena as requisições da View de Dashboard."""

    def __init__(self):
        super().__init__(ServicoDashboard)

    def get_service(self):
        return self._service


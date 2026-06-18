# -*- coding: utf-8 -*-
"""Controller de Dashboard — mediação entre View e Services."""

from services.dashboard import ServicoDashboard


class DashboardController:
    """Coordena as requisições da View de Dashboard."""

    def __init__(self, servico=None):
        self.servico = servico or ServicoDashboard()

    def obter_kpis(self):
        return self.servico.obter_kpis()

    def obter_notificacoes_ajuda(self):
        return self.servico.obter_notificacoes_ajuda()

    def obter_notificacoes_alertas(self):
        return self.servico.obter_notificacoes_alertas()

    def marcar_notificacao_como_lida(self, notificacao_id, tipo="alerta"):
        return self.servico.marcar_notificacao_como_lida(notificacao_id, tipo)

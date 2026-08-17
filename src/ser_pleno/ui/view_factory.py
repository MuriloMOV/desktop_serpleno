"""ViewFactory — responsável por instanciar views da aplicação."""

from __future__ import annotations

from ser_pleno.ui.views.dashboard import DashboardFrame
from ser_pleno.ui.views.estudantes import EstudantesFrame
from ser_pleno.ui.views.agenda import AgendaFrame
from ser_pleno.ui.views.bem_estar import BemEstarFrame
from ser_pleno.ui.views.triagem import TriagemFrame
from ser_pleno.ui.views.relatorio import RelatorioFrame
from ser_pleno.ui.views.comunicacao import ComunicacaoFrame
from ser_pleno.ui.views.orientacoes import OrientacoesFrame
from ser_pleno.ui.views.configuracoes import ConfiguracoesFrame
from ser_pleno.ui.views.metas import MetasFrame
from ser_pleno.ui.views.alertas import AlertasFrame
from ser_pleno.ui.views.analytics import AnalyticsFrame
from ser_pleno.ui.views.audit_logs import AuditLogsFrame
from ser_pleno.ui.views.compartilhamento import CompartilhamentoDadosFrame
from ser_pleno.ui.views.pedidos_ajuda import PedidosAjudaFrame
from ser_pleno.ui.views.login import LoginFrame
from ser_pleno.ui.views.avisos import AvisosFrame
from ser_pleno.ui.views.notificacoes import NotificacoesFrame
from ser_pleno.ui.views.report_template import ReportTemplateFrame


class ViewFactory:
    """Factory de views — mapeia chaves de navegação para classes de view."""

    def __init__(self, app):
        self.app = app
        self._views = {
            "dashboard": DashboardFrame,
            "estudantes": EstudantesFrame,
            "agenda": AgendaFrame,
            "bem_estar": BemEstarFrame,
            "analise": TriagemFrame,
            "relatorios": RelatorioFrame,
            "comunicacao": ComunicacaoFrame,
            "orientacoes": OrientacoesFrame,
            "avisos": AvisosFrame,
            "notificacoes": NotificacoesFrame,
            "configuracoes": ConfiguracoesFrame,
            "metas": MetasFrame,
            "alertas": AlertasFrame,
            "analytics": AnalyticsFrame,
            "audit_logs": AuditLogsFrame,
            "compartilhamento": CompartilhamentoDadosFrame,
            "pedidos_ajuda": PedidosAjudaFrame,
            "login": LoginFrame,
            "report_template": ReportTemplateFrame,
        }

    def create(self, key: str, parent, controller=None):
        """Instancia a view correspondente à chave de navegação."""
        frame_cls = self._views.get(key)
        if not frame_cls:
            return None

        if controller is not None:
            return frame_cls(parent, controller)

        return frame_cls(parent, self.app)

    @property
    def keys(self):
        return list(self._views.keys())

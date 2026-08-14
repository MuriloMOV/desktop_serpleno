"""ViewFactory — responsável por instanciar views da aplicação."""

from __future__ import annotations

from ser_pleno.application.controllers.dashboard import DashboardController
from ser_pleno.application.controllers.estudantes import EstudantesController
from ser_pleno.application.controllers.agenda import AgendaController
from ser_pleno.application.controllers.bem_estar import BemEstarController
from ser_pleno.application.controllers.triagem import TriagemController
from ser_pleno.application.controllers.relatorio import RelatorioController
from ser_pleno.application.controllers.comunicacao import ComunicacaoController
from ser_pleno.application.controllers.orientacoes import OrientacoesController
from ser_pleno.application.controllers.configuracoes import ConfiguracoesController
from ser_pleno.application.controllers.metas import MetasController
from ser_pleno.application.controllers.alertas import AlertasController
from ser_pleno.application.controllers.analytics import AnalyticsController
from ser_pleno.application.controllers.audit_logs import AuditLogsController
from ser_pleno.application.controllers.compartilhamento_dados import CompartilhamentoDadosController
from ser_pleno.application.controllers.pedidos_ajuda import PedidosAjudaController
from ser_pleno.application.controllers.autenticacao import AutenticacaoController
from ser_pleno.application.controllers.avisos import AvisosController
from ser_pleno.application.controllers.notificacoes import NotificacoesController
from ser_pleno.application.controllers.report_template import ReportTemplateController
from ser_pleno.presentation.views.dashboard import DashboardFrame
from ser_pleno.presentation.views.estudantes import EstudantesFrame
from ser_pleno.presentation.views.agenda import AgendaFrame
from ser_pleno.presentation.views.bem_estar import BemEstarFrame
from ser_pleno.presentation.views.triagem import TriagemFrame
from ser_pleno.presentation.views.relatorio import RelatorioFrame
from ser_pleno.presentation.views.comunicacao import ComunicacaoFrame
from ser_pleno.presentation.views.orientacoes import OrientacoesFrame
from ser_pleno.presentation.views.configuracoes import ConfiguracoesFrame
from ser_pleno.presentation.views.metas import MetasFrame
from ser_pleno.presentation.views.alertas import AlertasFrame
from ser_pleno.presentation.views.analytics import AnalyticsFrame
from ser_pleno.presentation.views.audit_logs import AuditLogsFrame
from ser_pleno.presentation.views.compartilhamento import CompartilhamentoDadosFrame
from ser_pleno.presentation.views.pedidos_ajuda import PedidosAjudaFrame
from ser_pleno.presentation.views.login import LoginFrame
from ser_pleno.presentation.views.avisos import AvisosFrame
from ser_pleno.presentation.views.notificacoes import NotificacoesFrame
from ser_pleno.presentation.views.report_template import ReportTemplateFrame


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
        self._controllers = {
            "dashboard": DashboardController,
            "estudantes": EstudantesController,
            "agenda": AgendaController,
            "bem_estar": BemEstarController,
            "analise": TriagemController,
            "relatorios": RelatorioController,
            "comunicacao": ComunicacaoController,
            "orientacoes": OrientacoesController,
            "avisos": AvisosController,
            "notificacoes": NotificacoesController,
            "configuracoes": ConfiguracoesController,
            "metas": MetasController,
            "alertas": AlertasController,
            "analytics": AnalyticsController,
            "audit_logs": AuditLogsController,
            "compartilhamento": CompartilhamentoDadosController,
            "pedidos_ajuda": PedidosAjudaController,
            "login": AutenticacaoController,
            "report_template": ReportTemplateController,
        }

    def _get_auth_service(self):
        return getattr(self.app, "auth_service", None)

    def _instantiate_controller(self, key):
        controller_cls = self._controllers.get(key)
        if not controller_cls:
            return None
        auth_service = self._get_auth_service()
        try:
            return controller_cls(app=self.app, auth_service=auth_service)
        except TypeError:
            try:
                return controller_cls(auth_service=auth_service)
            except TypeError:
                return controller_cls()

    def create(self, key: str, parent, controller=None):
        """Instancia a view correspondente à chave de navegação."""
        frame_cls = self._views.get(key)
        if not frame_cls:
            return None

        if controller is not None:
            return frame_cls(parent, controller)

        controller = self._instantiate_controller(key)
        if controller is not None:
            return frame_cls(parent, controller)

        return None

    @property
    def keys(self):
        return list(self._views.keys())

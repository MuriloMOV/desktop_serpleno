"""ViewFactory — responsável por instanciar views da aplicação."""

from __future__ import annotations

from ser_pleno.application.controllers.dashboard import DashboardController
from ser_pleno.application.controllers.estudantes import EstudantesController
from ser_pleno.application.controllers.agenda import AgendaController
from ser_pleno.application.controllers.bem_estar import BemEstarController
from ser_pleno.application.controllers.analise_triagem import AnaliseTriagemController
from ser_pleno.application.controllers.relatorio import RelatorioController
from ser_pleno.application.controllers.comunicacao import ComunicacaoController
from ser_pleno.application.controllers.orientacoes import OrientacoesController
from ser_pleno.application.controllers.configuracoes import ConfiguracoesController
from ser_pleno.presentation.views.dashboard import DashboardFrame
from ser_pleno.presentation.views.estudantes import EstudantesFrame
from ser_pleno.presentation.views.agenda import AgendaFrame
from ser_pleno.presentation.views.bem_estar import BemEstarFrame
from ser_pleno.presentation.views.analise_triagem import AnaliseTriagemFrame
from ser_pleno.presentation.views.relatorio import RelatorioFrame
from ser_pleno.presentation.views.comunicacao_interna import ComunicacaoInternaFrame
from ser_pleno.presentation.views.orientacoes import OrientacoesFrame
from ser_pleno.application.controllers.quadro_avisos import QuadroAvisosController
from ser_pleno.presentation.views.quadro_avisos import QuadroAvisosFrame
from ser_pleno.presentation.views.configuracoes import ConfiguracoesFrame


class ViewFactory:
    """Factory de views — mapeia chaves de navegação para classes de view."""

    def __init__(self, app):
        self.app = app
        self._views = {
            "dashboard": DashboardFrame,
            "estudantes": EstudantesFrame,
            "agenda": AgendaFrame,
            "bem_estar": BemEstarFrame,
            "analise": AnaliseTriagemFrame,
            "relatorios": RelatorioFrame,
            "comunicacao": ComunicacaoInternaFrame,
            "orientacoes": OrientacoesFrame,
            "avisos": QuadroAvisosFrame,
            "configuracoes": ConfiguracoesFrame,
        }
        self._controllers = {
            "dashboard": DashboardController,
            "estudantes": EstudantesController,
            "agenda": AgendaController,
            "bem_estar": BemEstarController,
            "analise": AnaliseTriagemController,
            "relatorios": RelatorioController,
            "comunicacao": ComunicacaoController,
            "orientacoes": OrientacoesController,
            "avisos": QuadroAvisosController,
            "configuracoes": ConfiguracoesController,
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

"""Controller de Notificacoes — medicao entre View e Services."""

from ser_pleno.application.controllers.base import BaseController
from ser_pleno.application.services.notificacoes import ServicoNotificacoes


class NotificacoesController(BaseController):
    """Coordena as requisicoes do sistema de notificacoes."""

    def __init__(self, app=None, auth_service=None):
        super().__init__(ServicoNotificacoes, auth_service=auth_service)
        self.app = app
        self.usuario_logado = (app.__dict__.get("usuario_logado") if app is not None else None)
        self.usuario_logado_id = (app.__dict__.get("usuario_logado_id") if app is not None else None)

    def get_service(self):
        return self._service

    def _sync_auth(self) -> None:
        if self.app and hasattr(self.app, "auth_service"):
            auth = self.app.auth_service
            if auth and hasattr(self._service, "_auth_service"):
                self._service._auth_service = auth
                if hasattr(self._service, "_api") and hasattr(self._service._api, "_auth_service"):
                    self._service._api._auth_service = auth

    def listar(self, unread_only: bool = False) -> dict:
        self._sync_auth()
        recipient_id = self.usuario_logado_id or 0
        return self._service.listar(recipient_id, unread_only=unread_only)

    def marcar_lida(self, notification_id: int) -> dict:
        self._sync_auth()
        recipient_id = self.usuario_logado_id or 0
        return self._service.marcar_lida(notification_id, recipient_id)

    def marcar_todas_lidas(self) -> dict:
        self._sync_auth()
        recipient_id = self.usuario_logado_id or 0
        return self._service.marcar_todas_lidas(recipient_id)

    def contar_nao_lidas(self) -> dict:
        self._sync_auth()
        recipient_id = self.usuario_logado_id or 0
        return self._service.contar_nao_lidas(recipient_id)

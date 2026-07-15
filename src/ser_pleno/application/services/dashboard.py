import logging

from ser_pleno.repositories.dashboard import DashboardRepository
from ser_pleno.repositories.comunicacao import ComunicacaoRepository
from ser_pleno.infrastructure.api.api import ClienteAPI

try:
    from ser_pleno.config.operation_mode import get_operation_config
except Exception:
    get_operation_config = None  # type: ignore

logger = logging.getLogger(__name__)


class ServicoDashboard:
    def __init__(self, auth_service=None):
        self.repo = DashboardRepository()
        self.repo_comunicacao = ComunicacaoRepository()
        self._auth_service = auth_service
        self._api = ClienteAPI(auth_service=auth_service)

    def obter_notificacoes_ajuda(self):
        """Obtém notificações de ajuda do serpleno_web."""
        config = get_operation_config()
        if not config.should_use_api():
            return []

        try:
            response = self._api.get("help/notifications/")
            if response.get("success"):
                return response.get("data", [])
        except Exception as e:
            logger.error("Erro ao obter notificações de ajuda: %s", e)
        return []

    def obter_notificacoes_alertas(self):
        """Obtém notificações de alertas do sistema."""
        return self.repo.obter_notificacoes_alertas()

    def marcar_notificacao_como_lida(self, notificacao_id, tipo="alerta"):
        """Marca uma notificação como lida."""
        if tipo == "alerta":
            self.repo.marcar_notificacao_como_lida(notificacao_id)
        elif tipo == "ajuda":
            config = get_operation_config()
            if not config.should_use_api():
                return
            try:
                self._api.put(f"help/notifications/{notificacao_id}/read/")
            except Exception as e:
                logger.error("Erro ao marcar notificação de ajuda como lida: %s", e)

    def obter_kpis(self):
        """Obtém estatísticas consolidadas do dashboard via repositório."""
        return self.repo.obter_kpis()

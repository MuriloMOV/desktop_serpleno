# -*- coding: utf-8 -*-
"""BootstrapService — tarefas de inicialização pós-login."""

import threading
import logging

from ser_pleno.infrastructure.local.seed_service import sync_critical_entities

logger = logging.getLogger(__name__)


class BootstrapService:
    """Coordena tarefas de inicialização assíncronas após login."""

    def run_post_login_seed(self) -> None:
        """Executa seed de entidades críticas em background."""
        def _seed_thread():
            try:
                result = sync_critical_entities()
                if result.get("failed"):
                    logger.warning("Seed pos-login parcial: %s", result)
                else:
                    logger.info("Seed pos-login concluido: %s", result)
            except Exception as exc:
                logger.warning("Seed pos-login falhou (nao-bloqueante): %s", exc)

        threading.Thread(target=_seed_thread, daemon=True).start()

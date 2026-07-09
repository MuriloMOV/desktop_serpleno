import logging
import os
import threading
import requests
from ser_pleno.config.operation_mode import get_operation_config

logger = logging.getLogger(__name__)


def _check_api_available(base_url: str, timeout: int = 3) -> bool:
    """
    Verifica conectividade com a API via health check.
    Retorna True se a API estiver acessível, False caso contrário.
    Nunca levanta exceção.
    """
    if not base_url or not requests:
        return False
    health_url = f"{base_url.rstrip('/')}/api/v1/desktop/health/"
    try:
        resp = requests.get(health_url, timeout=timeout)
        if resp.ok:
            try:
                data = resp.json()
                if data.get("status") == "ok":
                    return True
            except Exception:
                pass
            return True  # Respondeu 200 sem JSON específico = API acessível
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        pass
    except Exception:
        pass
    return False


def atualizar_disponibilidade_api_async(base_url: str = None):
    """
    Atualiza o estado de disponibilidade da API em background (não bloqueia a UI).
    Usa o health check. Armazena resultado em operation_config.
    """
    if base_url is None:
        try:
            from ser_pleno.config.config import DESKTOP_API_URL
            base_url = DESKTOP_API_URL
        except Exception:
            return

    def _worker():
        try:
            oc = get_operation_config()
            if oc is None:
                return
            # Evita consultar se já foi marcado como indisponível recentemente (debounce simples)
            if not oc.api_available:
                # Última checagem há menos de 10s? pula
                last = oc.last_sync
                import datetime
                if last and (datetime.datetime.now() - last).total_seconds() < 10:
                    return
            available = _check_api_available(base_url, timeout=3)
            if oc.api_available != available:
                oc.set_api_available(available)
                logger.info(f"Disponibilidade da API atualizada: {available}")
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def marcar_api_indisponivel(base_url: str = None):
    """
    Marca a API como indisponível imediatamente.
    Chamado sempre que uma requisição falhar com ConnectionError.
    """
    try:
        oc = get_operation_config()
        if oc is None:
            return
        if oc.api_available:
            oc.set_api_available(False)
            logger.warning("API marcada como indisponível após falha de conexão")
    except Exception:
        pass


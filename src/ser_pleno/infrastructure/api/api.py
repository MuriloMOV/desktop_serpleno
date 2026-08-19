import logging
import os
import time
import datetime
from typing import Dict, Any, Optional

from ser_pleno.config.config import DESKTOP_API_URL

try:
    import requests
except Exception:
    requests = None  # type: ignore

from ser_pleno.infrastructure.api.connectivity import marcar_api_indisponivel

class ClienteAPI:

    def __init__(self, auth_service=None):
        self.base_url = DESKTOP_API_URL
        self._operation_config = None
        self._sync_service = None
        self._auth_service = auth_service

    # ================= Helpers =================

    def _safe_json(self, response):
        """Garante que sempre retornamos um dict"""
        try:
            data = response.json()
            if isinstance(data, str):
                return {"success": False, "message": data}
            return data
        except Exception:
            logging.error("Resposta não é JSON válido")
            logging.error(f"Conteúdo bruto: {repr(getattr(response, 'text', response))}")
            return {
                "success": False,
                "message": "Resposta inválida do servidor",
                "raw": getattr(response, "text", "")
            }

    def _get_session(self):
        auth = self._auth_service
        if auth and hasattr(auth, 'get_session'):
            return auth.get_session()
        return requests

    def _build_url(self, endpoint: str) -> str:
        """Se endpoint for absoluto (http/https) usa ele; senão junta base_url + endpoint."""
        if not isinstance(endpoint, str):
            raise ValueError("endpoint deve ser string")
        ep = endpoint.strip()
        if ep.startswith("http://") or ep.startswith("https://"):
            return ep
        return f"{self.base_url.rstrip('/')}/{ep.lstrip('/')}"

    def _get_request_timeout(self, default: int) -> int:
        try:
            return int(os.environ.get("_request_timeout", default))
        except Exception:
            return default

    def _calculate_backoff(self, attempt: int, base: float = 0.5, cap: float = 4.0) -> float:
        return min(base * (2 ** (attempt - 1)), cap)

    def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        retries: int = 2,
        timeout: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if not requests:
            return {"success": False, "message": "Biblioteca requests não disponível"}

        if timeout is None:
            timeout = self._get_request_timeout(4)

        last_exception = None
        last_status_code = None
        for attempt in range(1, retries + 1):
            try:
                url = self._build_url(endpoint)
                session = self._get_session()
                response = session.request(method, url, timeout=timeout, **kwargs)
                last_status_code = response.status_code

                logging.getLogger('apps.desktop.api').debug(
                    f"[{method}] {url} -> {response.status_code} (attempt {attempt})"
                )

                if response.ok:
                    return self._safe_json(response)

                if 400 <= response.status_code < 500:
                    return {
                        "success": False,
                        "message": f"Erro na requisição: {response.status_code}",
                        "status_code": response.status_code,
                    }

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                marcar_api_indisponivel()
            except requests.exceptions.Timeout as e:
                last_exception = e
                marcar_api_indisponivel()
            except Exception as e:
                logging.getLogger('apps.desktop.api').error(
                    "Erro %s inesperado: %s: %s", method, type(e).__name__, e
                )
                return {"success": False, "message": "Erro de conexão inesperado"}

            if attempt < retries:
                backoff = self._calculate_backoff(attempt)
                logging.getLogger('apps.desktop.api').warning(
                    "Tentativa %d/%d falhou para %s %s; retry em %.1fs",
                    attempt, retries, method, endpoint, backoff,
                )
                time.sleep(backoff)

        msg = "Servidor indisponível no momento" if isinstance(last_exception, requests.exceptions.ConnectionError) else "Tempo de conexão esgotado"
        if last_status_code is not None:
            msg = f"Erro na requisição: {last_status_code}"
        return {"success": False, "message": msg, "status_code": last_status_code}

    # ================= GET =================

    def get(self, endpoint, params=None, retries: int = None, timeout: int = None):
        logging.getLogger('apps.desktop.api').debug(f"GET {endpoint} params={params}")
        result = self._request_with_retry(
            "GET", endpoint, retries=retries or 1, timeout=timeout, params=params
        )
        if result.get("success"):
            from ser_pleno.utils.logging_config import log_external_call
            log_external_call("GET", endpoint, status_code=result.get("status_code", 0))
        return result

    # ================= POST =================

    def post(self, endpoint, data=None, json=None, files=None, headers=None, retries: int = None, timeout: int = None):
        logging.getLogger('apps.desktop.api').debug(f"POST {endpoint}")
        result = self._request_with_retry(
            "POST", endpoint, retries=retries or 2, timeout=timeout,
            data=data, json=json, files=files, headers=headers,
        )
        if result.get("success"):
            from ser_pleno.utils.logging_config import log_external_call
            log_external_call("POST", endpoint, status_code=result.get("status_code", 0))
        return result

    # ================= PUT =================

    def put(self, endpoint, json=None, timeout: int = None, retries: int = 2):
        logging.getLogger('apps.desktop.api').debug(f"PUT {endpoint}")
        kwargs = {}
        if json is not None:
            kwargs["json"] = json
        result = self._request_with_retry("PUT", endpoint, retries=retries, timeout=timeout, **kwargs)
        if result.get("success"):
            from ser_pleno.utils.logging_config import log_external_call
            log_external_call("PUT", endpoint, status_code=result.get("status_code", 0))
        return result

    # ================= DELETE =================

    def delete(self, endpoint, timeout: int = None, retries: int = 2):
        logging.getLogger('apps.desktop.api').debug(f"DELETE {endpoint}")
        result = self._request_with_retry("DELETE", endpoint, retries=retries, timeout=timeout)
        if result.get("success"):
            from ser_pleno.utils.logging_config import log_external_call
            log_external_call("DELETE", endpoint, status_code=result.get("status_code", 0))
        return result




import logging
import os
import datetime
from typing import Dict, Any

from config.config import DESKTOP_API_URL

try:
    import requests
except Exception:
    requests = None  # type: ignore

from services.connectivity import marcar_api_indisponivel

_auth_service = None


def set_auth_service(auth_service):
    global _auth_service
    _auth_service = auth_service


def get_auth_service():
    return _auth_service


class ClienteAPI:

    def __init__(self):
        self.base_url = DESKTOP_API_URL
        self._operation_config = None
        self._sync_service = None

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
        auth = get_auth_service()
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
        # permite passar '/api/mural/' ou 'mural/' — removemos duplicação de slashes
        return f"{self.base_url.rstrip('/')}/{ep.lstrip('/')}"

    # ================= GET =================

    def get(self, endpoint, params=None, retries: int = 2, timeout: int = 6):
        logging.getLogger('apps.desktop.api').debug(f"GET {endpoint} params={params}")

        if not requests:
            return self._get_mock_response(endpoint, params)

        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                url = self._build_url(endpoint)
                session = self._get_session()
                response = session.get(url, params=params, timeout=timeout)

                logging.getLogger('apps.desktop.api').debug(f"[GET] {url} -> {response.status_code} (attempt {attempt})")

                if response.ok:
                    return self._safe_json(response)

                # Se for erro 4xx (cliente), não retry
                if 400 <= response.status_code < 500:
                    return {"success": False, "message": f"Erro na requisição: {response.status_code}", "status_code": response.status_code}

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                marcar_api_indisponivel()
            except requests.exceptions.Timeout as e:
                last_exception = e
                marcar_api_indisponivel()
            except Exception as e:
                logging.getLogger('apps.desktop.api').error(
                    "Erro GET inesperado: %s: %s", type(e).__name__, e
                )
                return {"success": False, "message": "Erro de conexão inesperado"}

        # Excedeu tentativas
        msg = "Servidor indisponível no momento" if isinstance(last_exception, requests.exceptions.ConnectionError) else "Tempo de conexão esgotado"
        return {"success": False, "message": msg}

    # ================= POST =================

    def post(self, endpoint, data=None, json=None, files=None, headers=None, retries: int = 2, timeout: int = 8):

        if not requests:
            return {"success": False, "message": "Requests não disponível"}

        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                url = self._build_url(endpoint)
                session = self._get_session()

                if files:
                    response = session.post(url, files=files, data=data, headers=headers, timeout=max(timeout, 15))
                else:
                    response = session.post(url, data=data, json=json, headers=headers, timeout=timeout)

                logging.getLogger('apps.desktop.api').debug(f"[POST] {url} -> {response.status_code} (attempt {attempt})")

                if response.ok:
                    return self._safe_json(response)

                if 400 <= response.status_code < 500:
                    return {"success": False, "message": f"Erro na requisição: {response.status_code}", "status_code": response.status_code}

            except Exception as e:
                last_exception = e
                logging.getLogger('apps.desktop.api').warning(f"Tentativa {attempt} falhou: {e}")

        logging.getLogger('apps.desktop.api').exception("Erro POST após retries")
        return {"success": False, "message": f"Erro de conexão: {str(last_exception)}"}

    # ================= MOCK =================

    def _get_mock_response(self, endpoint, params=None):
        if isinstance(endpoint, str) and endpoint.rstrip('/').endswith("help/notifications"):
            return {
                "success": True,
                "data": [
                    {
                        "id": 1,
                        "titulo": "Ajuda com agendamento",
                        "descricao": "Você tem 5 agendamentos pendentes",
                        "data": "2026-02-11",
                        "lida": False
                    }
                ]
            }

        return {"success": False, "message": "Endpoint não implementado (mock)"}

    # ================= PUT =================

    def put(self, endpoint, json=None):
        if not requests:
            return {"success": True, "message": "Dados atualizados com sucesso (mock)"}
        try:
            url = self._build_url(endpoint)
            session = self._get_session()
            response = session.put(url, json=json, timeout=8)
            logging.getLogger('apps.desktop.api').debug(f"[PUT] {url} -> {getattr(response,'status_code', None)}")
            if response.ok:
                return self._safe_json(response)
            return {"success": False, "message": f"Erro na requisição: {response.status_code}", "status_code": response.status_code}
        except Exception as e:
            logging.getLogger('apps.desktop.api').exception("Erro PUT")
            return {"success": False, "message": f"Erro de conexão: {str(e)}"}

    # ================= DELETE =================

    def delete(self, endpoint):
        if not requests:
            return {"success": True, "message": "Dados deletados com sucesso (mock)"}
        try:
            url = self._build_url(endpoint)
            session = self._get_session()
            response = session.delete(url, timeout=8)
            logging.getLogger('apps.desktop.api').debug(f"[DELETE] {url} -> {getattr(response,'status_code', None)}")
            if response.ok:
                # some servers return 204 with empty body
                try:
                    return self._safe_json(response)
                except Exception:
                    return {"success": True}
            return {"success": False, "message": f"Erro na requisição: {response.status_code}", "status_code": response.status_code}
        except Exception as e:
            logging.getLogger('apps.desktop.api').exception("Erro DELETE")
            return {"success": False, "message": f"Erro de conexão: {str(e)}"}


# Instância única
api = ClienteAPI()

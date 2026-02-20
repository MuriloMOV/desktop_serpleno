import logging
import os
import datetime
from typing import Optional, Dict, Any

try:
    import requests
except Exception:
    requests = None  # type: ignore

# Referência global ao serviço de autenticação
_auth_service = None

def set_auth_service(auth_service):
    """Define o serviço de autenticação global para usar nas requisições API"""
    global _auth_service
    _auth_service = auth_service

def get_auth_service():
    """Retorna o serviço de autenticação global"""
    return _auth_service


class ClienteAPI:
    """
    Cliente API para comunicação com serpleno_web.
    
    Funciona em dois modos:
    - Independente: Usa apenas dados locais/mockados
    - Híbrido/Conectado: Tenta API primeiro, fallback para local
    """
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1/desktop"
        self._operation_config = None
        self._sync_service = None
    
    def _get_operation_config(self):
        """Obtém configuração de operação (lazy loading)"""
        if self._operation_config is None:
            try:
                from config.operation_mode import get_operation_config
                self._operation_config = get_operation_config()
            except Exception:
                pass
        return self._operation_config
    
    def _get_sync_service(self):
        """Obtém serviço de sincronização (lazy loading)"""
        if self._sync_service is None:
            try:
                from services.sync_service import get_sync_service
                self._sync_service = get_sync_service()
            except Exception:
                pass
        return self._sync_service
    
    def _should_use_api(self) -> bool:
        """Verifica se deve tentar usar a API"""
        config = self._get_operation_config()
        if config is None:
            return True  # Comportamento padrão: tentar API
        return config.should_use_api()
    
    def _queue_sync(self, operation: str, entity: str, entity_id: int, data: Dict[str, Any]):
        """Adiciona operação à fila de sincronização"""
        sync = self._get_sync_service()
        if sync:
            sync.add_to_queue(operation, entity, entity_id, data)

    def _get_session(self):
        """Retorna a sessão HTTP do serviço de autenticação ou requests padrão"""
        auth = get_auth_service()
        if auth and hasattr(auth, 'get_session'):
            return auth.get_session()
        return requests

    def get(self, endpoint, params=None):
        logging.info(f"GET request to {endpoint} with params {params}")
        
        # Verifica se deve tentar API
        if not self._should_use_api():
            return self._get_mock_response(endpoint, params)
        
        # Verificar se requests está disponível e fazer chamada real
        if requests:
            try:
                url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
                session = self._get_session()
                response = session.get(url, params=params, timeout=5)
                logging.info(f"Resposta bruta do servidor: {repr(response.text)}")  # Log da resposta bruta
                if response.ok:
                    try:
                        return response.json()
                    except Exception as e:
                        logging.error(f"Erro ao decodificar JSON na resposta: {e}")
                        logging.error(f"Conteúdo da resposta: {repr(response.text)}")
                        return {"success": False, "message": "Resposta inválida do servidor"}
                return {"success": False, "message": f"Erro na requisição: {response.status_code}"}
            except Exception as e:
                logging.error(f"Erro na requisição: {e}")
                # Se a requisição real falhar, retornar dados mockados
                return self._get_mock_response(endpoint, params)
        
        # Se requests não está disponível, retornar dados mockados
        return self._get_mock_response(endpoint, params)
    
    def _get_mock_response(self, endpoint, params=None):
        """Retorna responses mockadas para testes e fallback"""
        if endpoint == "help/notifications/":
            return {
                "success": True,
                "data": [
                    {"id": 1, "titulo": "Ajuda com agendamento", "descricao": "Você tem 5 agendamentos pendentes de confirmação", "data": "2026-02-11", "lida": False},
                    {"id": 2, "titulo": "Orientação sobre relatórios", "descricao": "Novo template de relatório disponível", "data": "2026-02-10", "lida": True}
                ]
            }
        return {"success": False, "message": "Endpoint não implementado"}

    def post(self, endpoint, data=None, json=None, files=None, headers=None):
        """Generic POST. If `files` is provided and requests is available, perform a multipart upload.
        Files should be a dict compatible with requests' files parameter.
        """
        if files and requests:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            logging.info(f"Uploading files to {url}")
            try:
                session = self._get_session()
                resp = session.post(url, files=files, data=data, headers=headers, timeout=10)
                if resp.ok:
                    # try JSON response
                    try:
                        return resp.json()
                    except Exception:
                        return {"success": True, "message": "Upload successful"}
                return {"success": False, "message": f"Upload failed ({resp.status_code})", "status_code": resp.status_code}
            except Exception as e:
                logging.exception("Error during file upload")
                return {"success": False, "message": str(e)}

        # Verificar se requests está disponível e fazer chamada real
        if requests:
            try:
                url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
                session = self._get_session()
                response = session.post(url, data=data, json=json, headers=headers, timeout=5)
                logging.info(f"Resposta bruta do servidor: {repr(response.text)}")  # Log da resposta bruta
                if response.ok:
                    try:
                        return response.json()
                    except Exception as e:
                        logging.error(f"Erro ao decodificar JSON na resposta: {e}")
                        logging.error(f"Conteúdo da resposta: {repr(response.text)}")
                        return {"success": False, "message": "Resposta inválida do servidor"}
                return {"success": False, "message": f"Erro na requisição: {response.status_code}"}
            except Exception as e:
                logging.error(f"Erro na requisição: {e}")
                return {"success": False, "message": f"Erro de conexão: {str(e)}"}
        
        # Mock response for messages send
        if endpoint == "messages/send/" and json:
            return {
                "success": True,
                "message": "Mensagem enviada",
                "data": {
                    "id": 100 + len(json.get('text', '')),
                    "text": json.get('text', ''),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "sender_id": 1,
                    "read": False,
                    "self": True
                }
            }
        
        logging.info(f"Mock POST request to {endpoint} with data {data} and json {json}")
        return {"success": True, "message": "Dados enviados com sucesso"}

    def upload_file(self, endpoint, filepath, field_name='file'):
        """Convenience method to upload a local file via multipart/form-data.
        Returns parsed JSON response or a structure with url/name on success.
        """
        if not os.path.exists(filepath):
            return {"success": False, "message": "File not found"}

        if not requests:
            # Fallback mock behavior when requests is not available
            filename = os.path.basename(filepath)
            return {"success": True, "data": {"url": f"/media/{filename}", "name": filename}}

        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        logging.info(f"Uploading {filepath} to {url}")
        try:
            with open(filepath, 'rb') as f:
                files = {field_name: (os.path.basename(filepath), f)}
                session = self._get_session()
                resp = session.post(url, files=files, timeout=10)
                if resp.ok:
                    try:
                        return resp.json()
                    except Exception:
                        return {"success": True, "data": {"url": f"/media/{os.path.basename(filepath)}", "name": os.path.basename(filepath)}}
                return {"success": False, "message": f"Upload failed ({resp.status_code})", "status_code": resp.status_code}
        except Exception as e:
            logging.exception("Error during upload_file")
            return {"success": False, "message": str(e)}

    def put(self, endpoint, json=None):
        logging.info(f"Mock PUT request to {endpoint} with json {json}")
        return {"success": True, "message": "Dados atualizados com sucesso"}

    def delete(self, endpoint):
        logging.info(f"Mock DELETE request to {endpoint}")
        return {"success": True, "message": "Dados deletados com sucesso"}

# Instância única para fácil acesso
api = ClienteAPI()

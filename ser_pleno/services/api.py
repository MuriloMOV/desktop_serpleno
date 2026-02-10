import logging
import os
import datetime

try:
    import requests
except Exception:
    requests = None

class ClienteAPI:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1/desktop"  # ajuste conforme necessário

    def get(self, endpoint, params=None):
        logging.info(f"GET request to {endpoint} with params {params}")
        
        # Verificar se requests está disponível e fazer chamada real
        if requests:
            try:
                url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
                response = requests.get(url, params=params)
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
        return {"success": False, "message": "Endpoint não implementado"}

    def post(self, endpoint, data=None, json=None, files=None, headers=None):
        """Generic POST. If `files` is provided and requests is available, perform a multipart upload.
        Files should be a dict compatible with requests' files parameter.
        """
        if files and requests:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            logging.info(f"Uploading files to {url}")
            try:
                resp = requests.post(url, files=files, data=data, headers=headers)
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
                response = requests.post(url, data=data, json=json, headers=headers)
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
        if endpoint == "messages/send/":
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
                resp = requests.post(url, files=files)
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

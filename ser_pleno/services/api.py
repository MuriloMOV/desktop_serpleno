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
                return {"success": False, "message": f"Erro de conexão: {str(e)}"}
        
        # Mocked/simulated responses for views/services tests
        if endpoint == "messages/contacts/":
            return {"success": True, "results": [
                {
                    "id": 2,
                    "name": "Dra. Beatriz Clara",
                    "msg": "Online agora",
                    "active": True,
                    "unread": 2,
                    "img": "avatar-2.jpg",
                    "time": "2 min"
                },
                {
                    "id": 3,
                    "name": "Coordenação",
                    "msg": "Reunião Pedagógica",
                    "active": False,
                    "unread": 0,
                    "img": "avatar-3.jpg",
                    "time": "1h"
                },
                {
                    "id": 4,
                    "name": "Suporte Técnico",
                    "msg": "Chamado #442 aberto",
                    "active": True,
                    "unread": 0,
                    "img": "avatar-4.jpg",
                    "time": "3h"
                },
                {
                    "id": 5,
                    "name": "Carlos Eduardo",
                    "msg": "Vi seu relatório ontem",
                    "active": False,
                    "unread": 0,
                    "img": "avatar-5.jpg",
                    "time": "1d"
                },
                {
                    "id": 6,
                    "name": "Ana Luiza",
                    "msg": "Pode revisar a triagem?",
                    "active": True,
                    "unread": 1,
                    "img": "avatar-6.jpg",
                    "time": "4h"
                }
            ]}
        elif endpoint.startswith("messages/") and endpoint.endswith("/"):
            user_id = endpoint.strip("/").split("/")[1]
            return {"success": True, "results": [
                {
                    "id": 1,
                    "text": "Olá! Podemos revisar o relatório?",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=30)).isoformat(),
                    "sender_id": int(user_id),
                    "read": True,
                    "self": False
                },
                {
                    "id": 2,
                    "text": "Claro! Já estou com ele aberto aqui.",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=29)).isoformat(),
                    "sender_id": 1,
                    "read": True,
                    "self": True
                },
                {
                    "id": 3,
                    "text": "Perfeito. Notei que alguns dados de triagem precisam ser ajustados na seção de estudantes.",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=28)).isoformat(),
                    "sender_id": int(user_id),
                    "read": True,
                    "self": False
                },
                {
                    "id": 4,
                    "text": "Vou verificar agora mesmo.",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=27)).isoformat(),
                    "sender_id": 1,
                    "read": True,
                    "self": True
                }
            ]}
        elif endpoint == "wellness/dashboard/":
            return {"success": True, "data": {"message": "Mock dashboard data"}}
        elif endpoint == "wellness/mood/":
            return {"success": True, "data": {"mood": "happy"}}
        elif endpoint == "wellness/mood/averages/":
            return {"success": True, "data": {"average_mood": 4.5}}
        elif endpoint.startswith("wellness/mood/student/"):
            return {"success": True, "data": {"student_mood": "stressed"}}
        elif endpoint == "wellness/checkins/":
            return {"success": True, "data": {"checkins": ["checkin1", "checkin2"]}}
        elif endpoint == "wellness/risk-students/":
            return {"success": True, "data": {"students_at_risk": ["student1", "student2"]}}
        elif endpoint == "settings/preferences/":
            return {"success": True, "data": {"theme": "light", "notifications": True}}
        else:
            return {"success": False, "message": "Endpoint não encontrado"}

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

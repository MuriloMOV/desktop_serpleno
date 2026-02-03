import requests
import logging
from config import API_BASE_URL


class ClienteAPI:
    def __init__(self, base_url=None):
        self.base_url = (base_url or API_BASE_URL).rstrip('/')
        self.session = requests.Session()
        self.token = None
        
    def set_token(self, token):
        self.token = token
        self.session.headers.update({'Authorization': f'Token {token}'})
        # Ou Bearer se for JWT
        # self.session.headers.update({'Authorization': f'Bearer {token}'})

    def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição GET {endpoint}: {e}")
            return {'success': False, 'message': str(e)}

    def post(self, endpoint, data=None, json=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.post(url, data=data, json=json)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição POST {endpoint}: {e}")
            return {'success': False, 'message': str(e)}

    def put(self, endpoint, json=None):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.put(url, json=json)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição PUT {endpoint}: {e}")
            return {'success': False, 'message': str(e)}

    def delete(self, endpoint):
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição DELETE {endpoint}: {e}")
            return {'success': False, 'message': str(e)}

# Instância única para fácil acesso
api = ClienteAPI()

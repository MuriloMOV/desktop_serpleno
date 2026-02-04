from services import api

class AuthService:
    """Compat wrapper usado pelos testes e por código que espera uma API.
    Em tempo de execução o desktop usa serviços locais (services.autenticacao),
    mas essa classe facilita testes que mockam `services.auth.api`.
    """
    def login(self, username, password):
        try:
            response = api.session.post(f"{api.base_url}/login/", json={"username": username, "password": password})
            if response.status_code == 200:
                return response.json()
            return {"success": False}
        except Exception:
            return {"success": False}
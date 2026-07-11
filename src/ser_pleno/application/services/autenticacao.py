from ser_pleno.config.db_config import get_db_connection
from ser_pleno.config.config import API_ROOT_URL
from ser_pleno.repositories.autenticacao import AutenticacaoRepository
from passlib.hash import django_pbkdf2_sha256, django_pbkdf2_sha1, bcrypt_sha256, argon2
import logging
import re
from typing import Optional, Dict, Any

try:
    import requests
except Exception:
    requests = None  # type: ignore

logger = logging.getLogger(__name__)


class ServicoAutenticacao:
    """Serviço de autenticação que funciona de forma independente ou conectada"""
    
    # URL base da API (agora usa config oficial)
    API_BASE_URL = API_ROOT_URL
    
    def __init__(self):
        self.repo = AutenticacaoRepository()
        # Sessão para manter cookies de autenticação
        self.session = requests.Session() if requests else None
        self.user: Optional[Dict[str, Any]] = None
        self.csrf_token: Optional[str] = None
        self._operation_config = None
    
    def _get_operation_config(self):
        """Obtém configuração de operação (lazy loading)"""
        if self._operation_config is None:
            try:
                from ser_pleno.config.operation_mode import get_operation_config
                self._operation_config = get_operation_config()
            except Exception:
                pass
        return self._operation_config
    
    def _should_use_api(self) -> bool:
        """Verifica se deve tentar usar a API"""
        config = self._get_operation_config()
        if config is None:
            return True
        return config.should_use_api()
    
    def _extract_csrf_token(self, response):
        """Extrai o CSRF token dos cookies ou do corpo da resposta"""
        csrf_cookie = self.session.cookies.get('csrftoken', None)
        if csrf_cookie:
            return csrf_cookie
        
        if response.text:
            match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', response.text)
            if match:
                return match.group(1)
            
            try:
                data = response.json()
                if 'csrf_token' in data:
                    return data['csrf_token']
            except:
                pass
        
        return None
    
    def _get_csrf_token(self):
        """Obtém o CSRF token fazendo uma requisição para obter o cookie"""
        try:
            self._clear_duplicate_cookies()
            response = self.session.get(
                f"{self.API_BASE_URL}/api/v1/desktop/schedule/times/",
                timeout=5
            )
            self.csrf_token = self.session.cookies.get('csrftoken', None)
            if self.csrf_token:
                logging.info(f"CSRF token obtido: {self.csrf_token[:10]}...")
            return self.csrf_token
        except Exception as e:
            logging.warning(f"Erro ao obter CSRF token: {e}")
            return None
    
    def _clear_duplicate_cookies(self):
        """Remove cookies duplicados da sessão"""
        try:
            cookies_dict = {}
            for cookie in self.session.cookies:
                cookies_dict[cookie.name] = cookie.value
            self.session.cookies.clear()
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value)
        except Exception as e:
            logging.warning(f"Erro ao limpar cookies duplicados: {e}")
    
    def login(self, usuario, senha):
        """
        Realiza login via banco local (prioritário) com fallback para API.
        A API só é tentada se o login local falhar, evitando delays desnecessários.
        """
        try:
            result = self._login_local(usuario, senha)
            if result.get("success"):
                # Estabelece sessão Django em background sem bloquear o login.
                self._try_establish_session_async(usuario, senha)
                return result
            return result
        except Exception as e:
            logging.error(f"Erro no login local: {e}")
            return {'success': False, 'message': str(e)}
    
    def _login_api(self, usuario, senha):
        """Tenta login via API HTTP. Usado como fallback após DB local."""
        try:
            login_url = f"{self.API_BASE_URL}/api/v1/serpleno/auth/login/"
            response = self.session.post(
                login_url,
                json={"username": usuario, "password": senha},
                timeout=1.5,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    user_data = data.get('user', {})
                    if 'id' not in user_data and 'username' in user_data:
                        user_data['id'] = self._get_user_id_from_db(user_data['username'])
                    self.user = user_data
                    self._get_csrf_token()
                    return {'success': True, 'user': self.user}

            return {'success': False, 'message': f'API status {response.status_code}'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _try_establish_session_async(self, usuario, senha):
        """Estabelece sessão Django em background sem bloquear o login."""
        try:
            import threading
            threading.Thread(
                target=self._try_establish_session,
                args=(usuario, senha),
                daemon=True,
            ).start()
        except Exception:
            pass

    def _get_user_id_from_db(self, username):
        """Obtém o ID do usuário do banco de dados pelo username"""
        try:
            user = self.repo.obter_usuario_por_username(username)
            if user:
                return user['id']
        except Exception as e:
            logging.error(f"Erro ao obter ID do usuário: {e}")
        return None
    
    def _try_establish_session(self, usuario, senha):
        """
        Tenta estabelecer sessão Django via API após login local bem-sucedido.
        """
        try:
            login_url = f"{self.API_BASE_URL}/api/v1/serpleno/auth/login/"
            response = self.session.post(
                login_url,
                json={"username": usuario, "password": senha},
                timeout=1.5,
            )
            if response.status_code == 200:
                self._get_csrf_token()
                logging.info("Sessão Django estabelecida via API após login local")
            else:
                logging.warning(f"Não foi possível estabelecer sessão Django: status {response.status_code}")
        except Exception as e:
            logging.warning(f"Erro ao tentar estabelecer sessão Django: {e}")
    
    def _login_local(self, usuario, senha):
        """
        Realiza login consultando diretamente o banco MySQL (fallback).
        """
        try:
            user = self.repo.obter_usuario_por_username(usuario)
            if user:
                hash_value = user['password']
                if hash_value.startswith('pbkdf2_sha256$'):
                    valid = django_pbkdf2_sha256.verify(senha, hash_value)
                elif hash_value.startswith('pbkdf2_sha1$'):
                    valid = django_pbkdf2_sha1.verify(senha, hash_value)
                elif hash_value.startswith('bcrypt_sha256$'):
                    valid = bcrypt_sha256.verify(senha, hash_value)
                elif hash_value.startswith('argon2$'):
                    valid = argon2.verify(senha, hash_value)
                else:
                    valid = False
                if valid:
                    self.user = user
                    return {'success': True, 'user': user}
            return {'success': False, 'message': 'Credenciais inválidas'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_session(self):
        """Retorna a sessão HTTP para uso em outras requisições"""
        return self.session
    
    def get_headers(self):
        """Retorna headers com CSRF token para requisições POST/PUT/DELETE"""
        headers = {
            "Content-Type": "application/json",
        }
        if self.csrf_token:
            headers["X-CSRFToken"] = self.csrf_token
        return headers

    def alterar_senha(self, senha_atual: str, nova_senha: str) -> Dict[str, Any]:
        """Altera a senha do usuário logado no banco local."""
        if not self.user:
            return {"success": False, "message": "Nenhum usuário logado."}
        try:
            row = self.repo.obter_senha_usuario(self.user.get("id"))
            if not row:
                return {"success": False, "message": "Usuário não encontrado."}
            hash_value = row["password"]
            if hash_value.startswith("pbkdf2_sha256$"):
                valid = django_pbkdf2_sha256.verify(senha_atual, hash_value)
            elif hash_value.startswith("pbkdf2_sha1$"):
                valid = django_pbkdf2_sha1.verify(senha_atual, hash_value)
            elif hash_value.startswith("bcrypt_sha256$"):
                valid = bcrypt_sha256.verify(senha_atual, hash_value)
            elif hash_value.startswith("argon2$"):
                valid = argon2.verify(senha_atual, hash_value)
            else:
                valid = False
            if not valid:
                return {"success": False, "message": "Senha atual incorreta."}
            novo_hash = django_pbkdf2_sha256.hash(nova_senha)
            self.repo.atualizar_senha_usuario(self.user.get("id"), novo_hash)
            return {"success": True, "message": "Senha alterada com sucesso."}
        except Exception as e:
            logger.error(f"Erro ao alterar senha: {e}")
            return {"success": False, "message": str(e)}

    def logout(self):
        """Encerra a sessão"""
        try:
            logout_url = f"{self.API_BASE_URL}/api/v1/serpleno/auth/logout/"
            self.session.post(logout_url, timeout=5)
        except Exception:
            pass
        self.session = requests.Session()
        self.user = None
        self.csrf_token = None

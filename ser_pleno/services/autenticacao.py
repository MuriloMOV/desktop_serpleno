
from config.db_config import get_db_connection
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
    
    # URL base da API
    API_BASE_URL = "http://127.0.0.1:8000"
    
    def __init__(self):
        # Sessão para manter cookies de autenticação
        self.session = requests.Session() if requests else None
        self.user: Optional[Dict[str, Any]] = None
        self.csrf_token: Optional[str] = None
        self._operation_config = None
    
    def _get_operation_config(self):
        """Obtém configuração de operação (lazy loading)"""
        if self._operation_config is None:
            try:
                from config.operation_mode import get_operation_config
                self._operation_config = get_operation_config()
            except Exception:
                pass
        return self._operation_config
    
    def _should_use_api(self) -> bool:
        """Verifica se deve tentar usar a API"""
        config = self._get_operation_config()
        if config is None:
            return True  # Comportamento padrão: tentar API
        return config.should_use_api()
    
    def _extract_csrf_token(self, response):
        """Extrai o CSRF token dos cookies ou do corpo da resposta"""
        # Tenta obter do cookie
        csrf_cookie = self.session.cookies.get('csrftoken', None)
        if csrf_cookie:
            return csrf_cookie
        
        # Tenta obter do corpo da resposta (HTML ou JSON)
        if response.text:
            # Procura em meta tag HTML
            match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', response.text)
            if match:
                return match.group(1)
            
            # Procura em JSON
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
            # Limpa cookies duplicados antes de fazer a requisição
            self._clear_duplicate_cookies()
            
            # Faz uma requisição GET para obter o cookie CSRF
            response = self.session.get(
                f"{self.API_BASE_URL}/api/v1/desktop/schedule/times/",
                timeout=5
            )
            
            # Extrai o token do cookie
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
            # Obtém todos os cookies
            cookies_dict = {}
            for cookie in self.session.cookies:
                cookies_dict[cookie.name] = cookie.value
            
            # Limpa todos os cookies
            self.session.cookies.clear()
            
            # Re-adiciona cookies únicos
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value)
                
            logging.debug(f"Cookies limpos. Cookies únicos: {list(cookies_dict.keys())}")
        except Exception as e:
            logging.warning(f"Erro ao limpar cookies duplicados: {e}")
    
    def login(self, usuario, senha):
        """
        Realiza login via API Django para obter sessão.
        """
        try:
            # Tenta fazer login via API primeiro
            login_url = f"{self.API_BASE_URL}/api/v1/serpleno/auth/login/"
            response = self.session.post(
                login_url, 
                json={"username": usuario, "password": senha},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    user_data = data.get('user', {})
                    # Garante que o user_data tem o campo 'id'
                    if 'id' not in user_data and 'username' in user_data:
                        user_data['id'] = self._get_user_id_from_db(user_data['username'])
                    self.user = user_data
                    
                    # Obtém o CSRF token após o login
                    self._get_csrf_token()
                    
                    # Log para depuração
                    logging.info(f"Login via API realizado: {usuario}")
                    logging.info(f"Cookies após login: {dict(self.session.cookies)}")
                    
                    return {'success': True, 'user': self.user}
            
            # Fallback: login direto no banco MySQL
            logging.warning(f"Login via API falhou (status {response.status_code}), tentando banco local")
            result = self._login_local(usuario, senha)
            
            # Se o login local foi bem-sucedido, tenta estabelecer sessão via API
            if result.get('success'):
                self._try_establish_session(usuario, senha)
            
            return result
            
        except requests.exceptions.ConnectionError:
            logging.warning("API indisponível, usando banco local para login")
            result = self._login_local(usuario, senha)
            
            # Se o login local foi bem-sucedido, tenta estabelecer sessão via API
            if result.get('success'):
                self._try_establish_session(usuario, senha)
            
            return result
        except requests.exceptions.Timeout:
            logging.warning("Timeout na API, usando banco local para login")
            result = self._login_local(usuario, senha)
            
            # Se o login local foi bem-sucedido, tenta estabelecer sessão via API
            if result.get('success'):
                self._try_establish_session(usuario, senha)
            
            return result
        except Exception as e:
            logging.error(f"Erro no login: {e}")
            result = self._login_local(usuario, senha)
            
            # Se o login local foi bem-sucedido, tenta estabelecer sessão via API
            if result.get('success'):
                self._try_establish_session(usuario, senha)
            
            return result
    
    def _get_user_id_from_db(self, username):
        """Obtém o ID do usuário do banco de dados pelo username"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id FROM auth_user WHERE username = %s", (username,))
            user = cursor.fetchone()
            connection.close()
            if user:
                return user['id']
        except Exception as e:
            logging.error(f"Erro ao obter ID do usuário: {e}")
        return None
    
    def _try_establish_session(self, usuario, senha):
        """
        Tenta estabelecer sessão Django via API após login local bem-sucedido.
        Isso é necessário para que as requisições subsequentes funcionem com @login_required.
        """
        try:
            login_url = f"{self.API_BASE_URL}/api/v1/serpleno/auth/login/"
            response = self.session.post(
                login_url, 
                json={"username": usuario, "password": senha},
                timeout=5
            )
            if response.status_code == 200:
                # Obtém o CSRF token após estabelecer a sessão
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
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            # Consulta na tabela de usuários do Django (auth_user)
            cursor.execute("SELECT * FROM auth_user WHERE username = %s", (usuario,))
            user = cursor.fetchone()
            connection.close()
            if user:
                hash_value = user['password']
                # Detecta o algoritmo usado pelo Django
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

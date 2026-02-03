from .api import api

class ServicoAutenticacao:
    def login(self, usuario, senha):
        """
        Realiza login no sistema utilizando Autenticação de Sessão (Django padrão).
        """
        # O base_url é .../desktop/api, então queremos .../api/login/
        root_url = api.base_url.replace('/desktop/api', '')
        login_url = f"{root_url}/api/login/"

        try:
            # Enviando JSON conforme esperado pela view api_login
            response = api.session.post(login_url, json={
                'username': usuario,
                'password': senha
            })
            
            # 200 OK
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Sessão gravada automaticamente no api.session (cookies)
                    return {'success': True, 'user': data.get('user')}
            
            # Retorna msg do erro se houver
            try:
                msg = response.json().get('message', 'Credenciais inválidas')
            except:
                msg = 'Erro na autenticação'
                
            return {'success': False, 'message': msg}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def logout(self):
        api.token = None
        if 'Authorization' in api.session.headers:
            del api.session.headers['Authorization']

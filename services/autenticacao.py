
from config.db_config import get_db_connection
from passlib.hash import django_pbkdf2_sha256, django_pbkdf2_sha1, bcrypt_sha256, argon2

class ServicoAutenticacao:
    def login(self, usuario, senha):
        """
        Realiza login consultando diretamente o banco MySQL.
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            # Consulta na tabela de usuários do Django (auth_user)
            cursor.execute("SELECT * FROM auth_user WHERE username = %s", (usuario,))
            user = cursor.fetchone()
            connection.close()
            if user:
                hash = user['password']
                # Detecta o algoritmo usado pelo Django
                if hash.startswith('pbkdf2_sha256$'):
                    valid = django_pbkdf2_sha256.verify(senha, hash)
                elif hash.startswith('pbkdf2_sha1$'):
                    valid = django_pbkdf2_sha1.verify(senha, hash)
                elif hash.startswith('bcrypt_sha256$'):
                    valid = bcrypt_sha256.verify(senha, hash)
                elif hash.startswith('argon2$'):
                    valid = argon2.verify(senha, hash)
                else:
                    valid = False
                if valid:
                    return {'success': True, 'user': user}
            return {'success': False, 'message': 'Credenciais inválidas'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def logout(self):
        pass

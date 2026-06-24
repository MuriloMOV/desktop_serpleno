from config.db_config import get_db_connection


class ServicoComunicacao:
    def _fechar_conexao(self, connection):
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    def _mapear_alerta(self, row):
        return {
            'id': row.get('id'),
            'alert_type': row.get('alert_type'),
            'severity': row.get('severity'),
            'message': row.get('message'),
            'details': row.get('details'),
            'is_read': bool(row.get('is_read')),
            'is_resolved': bool(row.get('is_resolved')),
            'resolved_at': str(row.get('resolved_at')) if row.get('resolved_at') else None,
            'created_at': str(row.get('created_at')),
            'assigned_to_id': row.get('assigned_to_id'),
            'resolved_by_id': row.get('resolved_by_id'),
            'student_id': row.get('student_id')
        }

    def _mapear_pedido(self, row):
        return {
            'id': row.get('id'),
            'tipo': row.get('tipo'),
            'mensagem': row.get('mensagem'),
            'prioridade': row.get('prioridade'),
            'status': row.get('status'),
            'localizacao': row.get('localizacao'),
            'dados_extras': row.get('dados_extras'),
            'created_at': str(row.get('created_at')),
            'viewed_at': str(row.get('viewed_at')) if row.get('viewed_at') else None,
            'resolved_at': str(row.get('resolved_at')) if row.get('resolved_at') else None,
            'aluno_id': row.get('aluno_id')
        }

    def _mapear_contato(self, row, id_usuario_logado=None):
        nome_completo = f"{row.get('first_name')} {row.get('last_name')}".strip()
        if not nome_completo:
            nome_completo = row.get('username', 'Usuário')

        return {
            'id': row.get('id'),
            'name': nome_completo,
            'email': row.get('email'),
            'student_name': row.get('student_name'),
            'role': row.get('role'),
            'is_staff': bool(row.get('is_staff') or row.get('is_superuser'))
        }

    def _mapear_mensagem(self, row):
        mensagem = {
            'id': row.get('id'),
            'sender_id': row.get('sender_id'),
            'recipient_id': row.get('recipient_id'),
            'text': row.get('text'),
            'timestamp': str(row.get('timestamp')),
            'read': bool(row.get('read'))
        }
        if row.get('caminho_arquivo'):
            mensagem['caminho_arquivo'] = row.get('caminho_arquivo')
            mensagem['tipo_arquivo'] = row.get('tipo_arquivo')
        return mensagem

    def listar_alertas(self):
        connection = get_db_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM desktop_alert ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return {"success": True, "data": [self._mapear_alerta(r) for r in rows]}
        finally:
            self._fechar_conexao(connection)

    def marcar_alerta_lido(self, id_alerta):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE desktop_alert SET is_read = 1 WHERE id = %s", (id_alerta,))
            connection.commit()
            return {"success": True, "message": "Alerta marcado como lido"}
        finally:
            self._fechar_conexao(connection)

    def marcar_todos_lidos(self):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE desktop_alert SET is_read = 1 WHERE is_read = 0")
            connection.commit()
            return {"success": True, "message": "Todos os alertas marcados como lidos"}
        finally:
            self._fechar_conexao(connection)

    def listar_pedidos_ajuda(self):
        connection = get_db_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM help_requests ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return {"success": True, "data": [self._mapear_pedido(r) for r in rows]}
        finally:
            self._fechar_conexao(connection)

    def listar_contatos(self, id_usuario_logado=None):
        """
        Lista contatos com permissões admin/staff (admin, analista, coordenador, suporte)
        Exclui o usuário logado da lista para evitar confusão.
        """
        connection = get_db_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.id, u.first_name, u.last_name, u.username, u.email, a.nome AS student_name,
                       u.is_superuser, u.is_staff,
                       CASE
                           WHEN u.is_superuser THEN 'admin'
                           WHEN EXISTS (SELECT 1 FROM auth_group g INNER JOIN auth_user_groups ug ON g.id = ug.group_id WHERE ug.user_id = u.id AND g.name = 'Gestores') THEN 'coordenador'
                           WHEN EXISTS (SELECT 1 FROM auth_group g INNER JOIN auth_user_groups ug ON g.id = ug.group_id WHERE ug.user_id = u.id AND g.name = 'Profissionais') THEN 'analista'
                           WHEN EXISTS (SELECT 1 FROM auth_group g INNER JOIN auth_user_groups ug ON g.id = ug.group_id WHERE ug.user_id = u.id AND g.name = 'Suporte') THEN 'suporte'
                           WHEN u.is_staff THEN 'analista'
                           ELSE 'aluno'
                       END AS role
                FROM auth_user u
                LEFT JOIN aluno a ON u.id = a.user_id
                WHERE
                    u.is_superuser = 1 OR
                    EXISTS (SELECT 1 FROM auth_group g INNER JOIN auth_user_groups ug ON g.id = ug.group_id WHERE ug.user_id = u.id AND g.name IN ('Gestores', 'Profissionais', 'Suporte')) OR
                    u.is_staff = 1
                ORDER BY u.first_name ASC
            """)
            rows = cursor.fetchall()

            contatos = []
            for row in rows:
                if row.get('role') not in ['admin', 'analista', 'coordenador', 'suporte']:
                    continue
                if id_usuario_logado and row.get('id') == id_usuario_logado:
                    continue
                contatos.append(self._mapear_contato(row, id_usuario_logado))

            return {"success": True, "data": contatos}
        finally:
            self._fechar_conexao(connection)

    def obter_mensagens(self, id_usuario_logado, id_usuario_destinatario):
        """
        Obtém mensagens entre o usuário logado e um destinatário específico.
        """
        connection = get_db_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM desktop_message
                WHERE (sender_id = %s AND recipient_id = %s) OR (sender_id = %s AND recipient_id = %s)
                ORDER BY timestamp ASC
            """, (id_usuario_logado, id_usuario_destinatario, id_usuario_destinatario, id_usuario_logado))
            rows = cursor.fetchall()

            mensagens = [self._mapear_mensagem(r) for r in rows]

            if id_usuario_destinatario != id_usuario_logado:
                cursor.execute("""
                    UPDATE desktop_message
                    SET `read` = 1
                    WHERE sender_id = %s AND recipient_id = %s AND `read` = 0
                """, (id_usuario_destinatario, id_usuario_logado))
                connection.commit()

            return {"success": True, "data": mensagens}
        finally:
            self._fechar_conexao(connection)

    def enviar_mensagem(self, id_usuario_logado, id_usuario_destinatario, conteudo, caminho_arquivo=None, tipo_arquivo=None):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, `read`, caminho_arquivo, tipo_arquivo)
                VALUES (%s, %s, %s, NOW(), 0, %s, %s)
            """, (id_usuario_logado, id_usuario_destinatario, conteudo, caminho_arquivo, tipo_arquivo))
            connection.commit()
            return {"success": True, "data": {"id": cursor.lastrowid}}
        finally:
            self._fechar_conexao(connection)

    def enviar_mensagem_grupo(self, id_usuario_logado, conteudo, caminho_arquivo=None, tipo_arquivo=None):
        """
        Envia uma mensagem para o chat em grupo (todos os usuários autorizados).
        """
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, `read`, caminho_arquivo, tipo_arquivo)
                VALUES (%s, NULL, %s, NOW(), 0, %s, %s)
            """, (id_usuario_logado, conteudo, caminho_arquivo, tipo_arquivo))
            connection.commit()
            return {"success": True, "data": {"id": cursor.lastrowid}}
        finally:
            self._fechar_conexao(connection)

    def obter_mensagens_grupo(self):
        """
        Obtém mensagens do chat em grupo (todas as mensagens com recipient_id NULL).
        """
        connection = get_db_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM desktop_message
                WHERE recipient_id IS NULL
                ORDER BY timestamp ASC
            """)
            rows = cursor.fetchall()
            return {"success": True, "data": [self._mapear_mensagem(r) for r in rows]}
        finally:
            self._fechar_conexao(connection)

    def marcar_mensagem_lida(self, id_mensagem):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("UPDATE desktop_message SET `read` = 1 WHERE id = %s", (id_mensagem,))
            connection.commit()
            return {"success": True, "message": "Mensagem marcada como lida"}
        finally:
            self._fechar_conexao(connection)

    def contar_mensagens_nao_lidas(self, id_usuario_logado):
        """
        Conta o número de mensagens não lidas por contato para o usuário logado.
        """
        connection = get_db_connection()
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    sender_id as contato_id,
                    COUNT(*) as total_nao_lidas
                FROM desktop_message
                WHERE recipient_id = %s AND `read` = 0
                GROUP BY sender_id
            """, (id_usuario_logado,))
            rows = cursor.fetchall()
            contador = {row['contato_id']: row['total_nao_lidas'] for row in rows}
            return {"success": True, "data": contador}
        finally:
            self._fechar_conexao(connection)

    def deletar_mensagem(self, id_mensagem):
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM desktop_message WHERE id = %s", (id_mensagem,))
            connection.commit()
            return {"success": True, "message": "Mensagem deletada com sucesso"}
        finally:
            self._fechar_conexao(connection)

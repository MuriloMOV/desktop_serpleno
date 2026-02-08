from config.db_config import get_db_connection

class ServicoComunicacao:
    def listar_alertas(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_alert ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        alertas = []
        for r in rows:
            alertas.append({
                'id': r.get('id'),
                'alert_type': r.get('alert_type'),
                'severity': r.get('severity'),
                'message': r.get('message'),
                'details': r.get('details'),
                'is_read': bool(r.get('is_read')),
                'is_resolved': bool(r.get('is_resolved')),
                'resolved_at': str(r.get('resolved_at')) if r.get('resolved_at') else None,
                'created_at': str(r.get('created_at')),
                'assigned_to_id': r.get('assigned_to_id'),
                'resolved_by_id': r.get('resolved_by_id'),
                'student_id': r.get('student_id')
            })
            
        connection.close()
        return {"success": True, "data": alertas}

    def marcar_alerta_lido(self, id_alerta):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE desktop_alert SET is_read = 1 WHERE id = %s", (id_alerta,))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Alerta marcado como lido"}

    def marcar_todos_lidos(self):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE desktop_alert SET is_read = 1 WHERE is_read = 0")
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Todos os alertas marcados como lidos"}
        
    def listar_pedidos_ajuda(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM help_requests ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        pedidos = []
        for r in rows:
            pedidos.append({
                'id': r.get('id'),
                'tipo': r.get('tipo'),
                'mensagem': r.get('mensagem'),
                'prioridade': r.get('prioridade'),
                'status': r.get('status'),
                'localizacao': r.get('localizacao'),
                'dados_extras': r.get('dados_extras'),
                'created_at': str(r.get('created_at')),
                'viewed_at': str(r.get('viewed_at')) if r.get('viewed_at') else None,
                'resolved_at': str(r.get('resolved_at')) if r.get('resolved_at') else None,
                'aluno_id': r.get('aluno_id')
            })
            
        connection.close()
        return {"success": True, "data": pedidos}

    def listar_contatos(self, id_usuario_logado=None):
        """
        Lista contatos com permissões admin/staff (admin, analista, coordenador, suporte)
        Exclui o usuário logado da lista para evitar confusão
        """
        connection = get_db_connection()
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
        for r in rows:
            # Filtra apenas roles permitidas (admin, analista, coordenador, suporte)
            if r.get('role') not in ['admin', 'analista', 'coordenador', 'suporte']:
                continue
                
            # Exclui o usuário logado da lista de contatos
            if id_usuario_logado and r.get('id') == id_usuario_logado:
                continue
                
            nome_completo = f"{r.get('first_name')} {r.get('last_name')}".strip()
            if not nome_completo:
                nome_completo = r.get('username', 'Usuário')
                
            contatos.append({
                'id': r.get('id'),
                'name': nome_completo,
                'email': r.get('email'),
                'student_name': r.get('student_name'),
                'role': r.get('role'),
                'is_staff': bool(r.get('is_staff') or r.get('is_superuser'))
            })
            
        connection.close()
        return {"success": True, "data": contatos}

    def obter_mensagens(self, id_usuario_logado, id_usuario_destinatario):
        """
        Obtém mensagens entre o usuário logado e um destinatário específico
        """
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM desktop_message
            WHERE (sender_id = %s AND recipient_id = %s) OR (sender_id = %s AND recipient_id = %s)
            ORDER BY timestamp ASC
        """, (id_usuario_logado, id_usuario_destinatario, id_usuario_destinatario, id_usuario_logado))
        rows = cursor.fetchall()
        
        mensagens = []
        for r in rows:
            mensagem = {
                'id': r.get('id'),
                'sender_id': r.get('sender_id'),
                'recipient_id': r.get('recipient_id'),
                'text': r.get('text'),
                'timestamp': str(r.get('timestamp')),
                'read': bool(r.get('read'))
            }
            if r.get('caminho_arquivo'):
                mensagem['caminho_arquivo'] = r.get('caminho_arquivo')
                mensagem['tipo_arquivo'] = r.get('tipo_arquivo')
            mensagens.append(mensagem)
            
        # Marca mensagens recebidas como lidas
        if id_usuario_destinatario != id_usuario_logado:
            cursor.execute("""
                UPDATE desktop_message 
                SET `read` = 1 
                WHERE sender_id = %s AND recipient_id = %s AND `read` = 0
            """, (id_usuario_destinatario, id_usuario_logado))
            connection.commit()
            
        connection.close()
        return {"success": True, "data": mensagens}

    def enviar_mensagem(self, id_usuario_logado, id_usuario_destinatario, conteudo, caminho_arquivo=None, tipo_arquivo=None):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, `read`, caminho_arquivo, tipo_arquivo)
            VALUES (%s, %s, %s, NOW(), 0, %s, %s)
        """, (id_usuario_logado, id_usuario_destinatario, conteudo, caminho_arquivo, tipo_arquivo))
        connection.commit()
        mensagem_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": mensagem_id}}

    def enviar_mensagem_grupo(self, id_usuario_logado, conteudo, caminho_arquivo=None, tipo_arquivo=None):
        """
        Envia uma mensagem para o chat em grupo (todos os usuários autorizados)
        """
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Para chat em grupo, usamos recipient_id NULL
        cursor.execute("""
            INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, `read`, caminho_arquivo, tipo_arquivo)
            VALUES (%s, NULL, %s, NOW(), 0, %s, %s)
        """, (id_usuario_logado, conteudo, caminho_arquivo, tipo_arquivo))
        connection.commit()
        mensagem_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": mensagem_id}}

    def obter_mensagens_grupo(self):
        """
        Obtém mensagens do chat em grupo (todas as mensagens com recipient_id NULL)
        """
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM desktop_message
            WHERE recipient_id IS NULL
            ORDER BY timestamp ASC
        """)
        rows = cursor.fetchall()
        
        mensagens = []
        for r in rows:
            mensagem = {
                'id': r.get('id'),
                'sender_id': r.get('sender_id'),
                'recipient_id': r.get('recipient_id'),
                'text': r.get('text'),
                'timestamp': str(r.get('timestamp')),
                'read': bool(r.get('read'))
            }
            if r.get('caminho_arquivo'):
                mensagem['caminho_arquivo'] = r.get('caminho_arquivo')
                mensagem['tipo_arquivo'] = r.get('tipo_arquivo')
            mensagens.append(mensagem)
            
        connection.close()
        return {"success": True, "data": mensagens}

    def marcar_mensagem_lida(self, id_mensagem):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE desktop_message SET read = 1 WHERE id = %s", (id_mensagem,))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Mensagem marcada como lida"}

    def deletar_mensagem(self, id_mensagem):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM desktop_message WHERE id = %s", (id_mensagem,))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Mensagem deletada com sucesso"}

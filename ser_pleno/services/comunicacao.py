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

    def listar_contatos(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id, u.first_name, u.last_name, u.email, a.nome AS student_name
            FROM auth_user u
            LEFT JOIN aluno a ON u.id = a.user_id
            ORDER BY u.first_name ASC
        """)
        rows = cursor.fetchall()
        
        contatos = []
        for r in rows:
            contatos.append({
                'id': r.get('id'),
                'name': f"{r.get('first_name')} {r.get('last_name')}",
                'email': r.get('email'),
                'student_name': r.get('student_name')
            })
            
        connection.close()
        return {"success": True, "data": contatos}

    def obter_mensagens(self, id_usuario):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM desktop_message
            WHERE sender_id = %s OR recipient_id = %s
            ORDER BY timestamp DESC
        """, (id_usuario, id_usuario))
        rows = cursor.fetchall()
        
        mensagens = []
        for r in rows:
            mensagens.append({
                'id': r.get('id'),
                'sender_id': r.get('sender_id'),
                'recipient_id': r.get('recipient_id'),
                'text': r.get('text'),
                'timestamp': str(r.get('timestamp')),
                'read': bool(r.get('read'))
            })
            
        connection.close()
        return {"success": True, "data": mensagens}

    def enviar_mensagem(self, id_usuario, conteudo):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO desktop_message (sender_id, recipient_id, text, timestamp, read)
            VALUES (%s, %s, %s, NOW(), 0)
        """, (1, id_usuario, conteudo))  # TODO: Obter sender_id do usuário logado
        connection.commit()
        mensagem_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": mensagem_id}}

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

from config.db_config import get_db_connection

class ServicoOrientacoes:
    def listar_orientacoes(self, busca=None, id_estudante=None, pagina=1):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT do.*, a.nome AS student_name, u.first_name || ' ' || u.last_name AS psychologist_name
            FROM desktop_orientation do
            LEFT JOIN aluno a ON do.student_id = a.id_aluno
            LEFT JOIN auth_user u ON do.psychologist_id = u.id
            WHERE 1=1
        """
        params = []
        
        if busca:
            query += " AND (a.nome LIKE %s OR do.title LIKE %s OR do.theme LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%"])
        if id_estudante:
            query += " AND do.student_id = %s"
            params.append(id_estudante)
            
        offset = (pagina - 1) * 10
        query += " ORDER BY do.created_at DESC LIMIT 10 OFFSET %s"
        params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        orientacoes = []
        for r in rows:
            orientacoes.append({
                'id': r.get('id'),
                'student_id': r.get('student_id'),
                'student_name': r.get('student_name') or 'Estudante',
                'psychologist_id': r.get('psychologist_id'),
                'psychologist_name': r.get('psychologist_name') or 'Psicólogo',
                'title': r.get('title'),
                'theme': r.get('theme'),
                'session_date': str(r.get('session_date')) if r.get('session_date') else None,
                'content': r.get('content'),
                'is_markdown': bool(r.get('is_markdown')),
                'motivational_message': r.get('motivational_message'),
                'action_plan': r.get('action_plan'),
                'created_at': str(r.get('created_at')),
                'updated_at': str(r.get('updated_at'))
            })
            
        connection.close()
        return {"success": True, "data": orientacoes}

    def criar_orientacao(self, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO desktop_orientation (
                student_id, psychologist_id, title, theme, session_date,
                content, is_markdown, motivational_message, action_plan,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        cursor.execute(query, (
            dados['student_id'], dados.get('psychologist_id'), dados['title'],
            dados.get('theme', ''), dados.get('session_date'), dados['content'],
            dados.get('is_markdown', False), dados.get('motivational_message', ''),
            dados.get('action_plan', '{}')
        ))
        connection.commit()
        orientacao_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": orientacao_id}}

    def obter_orientacao(self, id_orientacao):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT do.*, a.nome AS student_name, u.first_name || ' ' || u.last_name AS psychologist_name
            FROM desktop_orientation do
            LEFT JOIN aluno a ON do.student_id = a.id_aluno
            LEFT JOIN auth_user u ON do.psychologist_id = u.id
            WHERE do.id = %s
        """
        cursor.execute(query, (id_orientacao,))
        r = cursor.fetchone()
        
        if not r:
            connection.close()
            return {"success": False, "message": "Orientação não encontrada"}
            
        orientacao = {
            'id': r.get('id'),
            'student_id': r.get('student_id'),
            'student_name': r.get('student_name') or 'Estudante',
            'psychologist_id': r.get('psychologist_id'),
            'psychologist_name': r.get('psychologist_name') or 'Psicólogo',
            'title': r.get('title'),
            'theme': r.get('theme'),
            'session_date': str(r.get('session_date')) if r.get('session_date') else None,
            'content': r.get('content'),
            'is_markdown': bool(r.get('is_markdown')),
            'motivational_message': r.get('motivational_message'),
            'action_plan': r.get('action_plan'),
            'created_at': str(r.get('created_at')),
            'updated_at': str(r.get('updated_at'))
        }
        
        # Buscar anexos
        cursor.execute("SELECT * FROM desktop_orientationattachment WHERE orientation_id = %s", (id_orientacao,))
        attachments = cursor.fetchall()
        orientacao['attachments'] = []
        for att in attachments:
            orientacao['attachments'].append({
                'id': att.get('id'),
                'file': att.get('file'),
                'file_name': att.get('file_name'),
                'mime_type': att.get('mime_type'),
                'uploaded_by_id': att.get('uploaded_by_id')
            })
            
        connection.close()
        return {"success": True, "data": orientacao}

    def deletar_orientacao(self, id_orientacao):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM desktop_orientationattachment WHERE orientation_id = %s", (id_orientacao,))
        cursor.execute("DELETE FROM desktop_orientation WHERE id = %s", (id_orientacao,))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Orientação deletada com sucesso"}

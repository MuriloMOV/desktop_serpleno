from config.db_config import get_db_connection

class ServicoTriagem:
    def listar_triagens(self, busca=None, status=None, prioridade=None, id_estudante=None, pagina=1):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT ds.*, a.nome AS student_name, df.name AS form_name
            FROM desktop_screening ds
            LEFT JOIN aluno a ON ds.student_id = a.id_aluno
            LEFT JOIN desktop_screeningform df ON ds.form_id = df.id
            WHERE 1=1
        """
        params = []
        
        if busca:
            query += " AND (a.nome LIKE %s OR df.name LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%"])
        if status:
            query += " AND ds.status = %s"
            params.append(status)
        if prioridade:
            query += " AND ds.priority = %s"
            params.append(prioridade)
        if id_estudante:
            query += " AND ds.student_id = %s"
            params.append(id_estudante)
            
        offset = (pagina - 1) * 10
        query += " ORDER BY ds.created_at DESC LIMIT 10 OFFSET %s"
        params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        triagens = []
        for r in rows:
            triagens.append({
                'id': r.get('id'),
                'student_id': r.get('student_id'),
                'student_name': r.get('student_name') or 'Estudante',
                'form_id': r.get('form_id'),
                'form_name': r.get('form_name') or 'Formulário',
                'status': r.get('status'),
                'priority': r.get('priority'),
                'scheduled_date': str(r.get('scheduled_date')) if r.get('scheduled_date') else None,
                'completed_date': str(r.get('completed_date')) if r.get('completed_date') else None,
                'score': r.get('score'),
                'created_at': str(r.get('created_at'))
            })
            
        connection.close()
        return {"success": True, "data": triagens}

    def obter_triagem(self, id_triagem):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT ds.*, a.nome AS student_name, df.name AS form_name, df.questions
            FROM desktop_screening ds
            LEFT JOIN aluno a ON ds.student_id = a.id_aluno
            LEFT JOIN desktop_screeningform df ON ds.form_id = df.id
            WHERE ds.id = %s
        """
        cursor.execute(query, (id_triagem,))
        r = cursor.fetchone()
        
        if not r:
            connection.close()
            return {"success": False, "message": "Triagem não encontrada"}
            
        triagem = {
            'id': r.get('id'),
            'student_id': r.get('student_id'),
            'student_name': r.get('student_name') or 'Estudante',
            'form_id': r.get('form_id'),
            'form_name': r.get('form_name') or 'Formulário',
            'status': r.get('status'),
            'priority': r.get('priority'),
            'scheduled_date': str(r.get('scheduled_date')) if r.get('scheduled_date') else None,
            'completed_date': str(r.get('completed_date')) if r.get('completed_date') else None,
            'score': r.get('score'),
            'responses': r.get('responses'),
            'observations': r.get('observations'),
            'recommendations': r.get('recommendations'),
            'requires_followup': bool(r.get('requires_followup')),
            'followup_date': str(r.get('followup_date')) if r.get('followup_date') else None,
            'created_at': str(r.get('created_at')),
            'questions': r.get('questions')
        }
        
        connection.close()
        return {"success": True, "data": triagem}

    def criar_triagem(self, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO desktop_screening (
                student_id, form_id, status, priority, scheduled_date,
                responses, observations, recommendations, requires_followup,
                followup_date, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        cursor.execute(query, (
            dados['student_id'], dados['form_id'], dados.get('status', 'pending'),
            dados.get('priority', 'medium'), dados.get('scheduled_date'),
            dados.get('responses', '{}'), dados.get('observations', ''),
            dados.get('recommendations', ''), dados.get('requires_followup', False),
            dados.get('followup_date')
        ))
        connection.commit()
        triagem_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": triagem_id}}

    def atualizar_triagem(self, id_triagem, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            UPDATE desktop_screening
            SET student_id = %s, form_id = %s, status = %s, priority = %s,
                scheduled_date = %s, responses = %s, observations = %s,
                recommendations = %s, requires_followup = %s, followup_date = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, (
            dados['student_id'], dados['form_id'], dados.get('status', 'pending'),
            dados.get('priority', 'medium'), dados.get('scheduled_date'),
            dados.get('responses', '{}'), dados.get('observations', ''),
            dados.get('recommendations', ''), dados.get('requires_followup', False),
            dados.get('followup_date'), id_triagem
        ))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Triagem atualizada com sucesso"}

    def deletar_triagem(self, id_triagem):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM desktop_screening WHERE id = %s", (id_triagem,))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Triagem deletada com sucesso"}

    def listar_formularios(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_screeningform WHERE is_active = 1 ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        formularios = []
        for r in rows:
            formularios.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'description': r.get('description'),
                'questions': r.get('questions'),
                'is_active': bool(r.get('is_active')),
                'created_at': str(r.get('created_at'))
            })
            
        connection.close()
        return {"success": True, "data": formularios}

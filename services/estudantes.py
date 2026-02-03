from config.db_config import get_db_connection

class ServicoEstudante:
    def listar_estudantes(self, busca=None, possui_laudo=None, requer_atencao=None, pagina=1):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Join com auth_user para obter e-mail de contato
        query = "SELECT a.*, u.email AS contact FROM aluno a LEFT JOIN auth_user u ON a.user_id = u.id WHERE 1=1"
        params = []

        if busca:
            query += " AND (a.nome LIKE %s OR u.email LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%"])

        if possui_laudo is not None:
            query += " AND a.has_medical_report = %s"
            params.append(possui_laudo)

        if requer_atencao is not None:
            query += " AND a.requires_attention = %s"
            params.append(requer_atencao)

        offset = (pagina - 1) * 10
        query += " LIMIT 10 OFFSET %s"
        params.append(offset)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        # Mapear colunas do banco para o formato esperado pela UI
        students = []
        for r in rows:
            students.append({
                'id': r.get('id_aluno'),
                'name': r.get('nome'),
                'course': r.get('curso'),
                'age': r.get('age') or r.get('idade'),
                'has_medical_report': bool(r.get('has_medical_report')),
                'requires_attention': bool(r.get('requires_attention')),
                'contact': r.get('contact') or r.get('email') or '',
                'priority_level': r.get('priority_level') or 0,
            })
        connection.close()
        return {"success": True, "data": students}

    def obter_estudante(self, id_estudante):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Buscar aluno com email (join em auth_user)
        cursor.execute("SELECT a.*, u.email AS contact FROM aluno a LEFT JOIN auth_user u ON a.user_id = u.id WHERE a.id_aluno = %s", (id_estudante,))
        r = cursor.fetchone()
        student = None
        if r:
            student = {
                'id': r.get('id_aluno'),
                'name': r.get('nome'),
                'course': r.get('curso'),
                'age': r.get('age') or r.get('idade'),
                'phone': r.get('phone') or '',
                'contact': r.get('contact') or '',
                'emergency_contact': r.get('emergency_contact') or '',
                'emergency_phone': r.get('emergency_phone') or '',
                'has_medical_report': bool(r.get('has_medical_report')),
                'requires_attention': bool(r.get('requires_attention')),
                'attention_reason': r.get('attention_reason') or r.get('attention_notes') or ''
            }
            # Buscar intervenções relacionadas (desktop_intervention)
            cursor.execute("SELECT id, date, intervention_notes as notes FROM desktop_intervention WHERE student_id = %s ORDER BY date DESC LIMIT 10", (id_estudante,))
            invs = cursor.fetchall()
            interventions = []
            for inv in invs:
                interventions.append({
                    'id': inv.get('id'),
                    'date': str(inv.get('date')),
                    'notes': inv.get('notes')
                })
            student['interventions'] = interventions
        connection.close()
        return {"success": True, "data": student}

    def obter_relatorio_estudante(self, id_estudante):
        """Retorna o detalhe do estudante junto com seus registros de humor."""
        # Reutiliza o método de detalhe já existente
        student_resp = self.obter_estudante(id_estudante)
        student = student_resp.get('data') if isinstance(student_resp, dict) else None

        # Import local para evitar dependências circulares em tempo de import
        from services.bem_estar import ServicoBemEstar
        moods_resp = ServicoBemEstar().obter_humor_estudante(id_estudante)
        moods = moods_resp.get('data') if isinstance(moods_resp, dict) else moods_resp

        return {"success": True, "data": {"student": student, "moods": moods}}

    def criar_estudante(self, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO aluno (nome, email, has_medical_report, requires_attention) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (dados['nome'], dados['email'], dados['has_medical_report'], dados['requires_attention']))
        connection.commit()
        connection.close()
        return {"success": True, "message": "Estudante criado com sucesso"}

    def atualizar_estudante(self, id_estudante, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "UPDATE aluno SET nome = %s, email = %s, has_medical_report = %s, requires_attention = %s WHERE id_aluno = %s"
        cursor.execute(query, (dados['nome'], dados['email'], dados['has_medical_report'], dados['requires_attention'], id_estudante))
        connection.commit()
        connection.close()
        return {"success": True, "message": "Estudante atualizado com sucesso"}

    def deletar_estudante(self, id_estudante):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM aluno WHERE id_aluno = %s", (id_estudante,))
        connection.commit()
        connection.close()
        return {"success": True, "message": "Estudante deletado com sucesso"}

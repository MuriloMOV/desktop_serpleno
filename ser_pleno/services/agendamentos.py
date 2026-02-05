from config.db_config import get_db_connection

class ServicoAgendamento:
    def listar_agendamentos(self, data=None, id_estudante=None, status=None, pagina=1):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT da.*, a.nome AS student_name, COALESCE(t.horario, '') AS time_horario
            FROM desktop_appointment da
            LEFT JOIN aluno a ON da.student_id = a.id_aluno
            LEFT JOIN disponibilidade t ON da.time = t.id_disponibilidade
            WHERE 1=1
        """
        params = []
        
        if data:
            query += " AND da.date = %s"
            params.append(data)
        if id_estudante:
            query += " AND da.student_id = %s"
            params.append(id_estudante)
        if status:
            query += " AND da.status = %s"
            params.append(status)
            
        offset = (pagina - 1) * 10
        query += " ORDER BY da.date DESC, t.horario ASC LIMIT 10 OFFSET %s"
        params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        agendamentos = []
        for r in rows:
            time_val = r.get('time_horario')
            time_str = time_val.strftime('%H:%M') if hasattr(time_val, 'strftime') else (str(time_val) if time_val else '--:--')
            agendamentos.append({
                'id': r.get('id'),
                'student_id': r.get('student_id'),
                'student_name': r.get('student_name') or 'Estudante',
                'date': str(r.get('date')),
                'time': time_str,
                'status': r.get('status'),
                'notes': r.get('notes')
            })
            
        connection.close()
        return {"success": True, "data": agendamentos}

    def criar_agendamento(self, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO desktop_appointment (
                date, time, student_id, status, notes, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """
        cursor.execute(query, (
            dados['date'], dados['time'], dados['student_id'],
            dados.get('status', 'pending'), dados.get('notes', '')
        ))
        connection.commit()
        agendamento_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": agendamento_id}}

    def atualizar_agendamento(self, id_agendamento, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            UPDATE desktop_appointment
            SET date = %s, time = %s, student_id = %s, status = %s, notes = %s, updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, (
            dados['date'], dados['time'], dados['student_id'],
            dados.get('status', 'pending'), dados.get('notes', ''), id_agendamento
        ))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Agendamento atualizado com sucesso"}

    def deletar_agendamento(self, id_agendamento):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM desktop_appointment WHERE id = %s", (id_agendamento,))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Agendamento deletado com sucesso"}

    def listar_horarios_disponiveis(self, data=None):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM disponibilidade WHERE is_active = 1"
        params = []
        
        if data:
            # Verificar horários já agendados para a data
            query += " AND id_disponibilidade NOT IN (SELECT time FROM desktop_appointment WHERE date = %s)"
            params.append(data)
            
        query += " ORDER BY horario ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        horarios = []
        for r in rows:
            horarios.append({
                'id': r.get('id_disponibilidade'),
                'time': r.get('horario').strftime('%H:%M') if hasattr(r.get('horario'), 'strftime') else str(r.get('horario'))
            })
            
        connection.close()
        return {"success": True, "data": horarios}
    
    def gerenciar_horario(self, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if dados.get('action') == 'add':
            query = "INSERT INTO disponibilidade (Dias, Horario, Analista_id_analista, is_active) VALUES (%s, %s, %s, 1)"
            cursor.execute(query, (dados['days'], dados['time'], dados.get('analyst_id')))
        elif dados.get('action') == 'remove':
            query = "UPDATE disponibilidade SET is_active = 0 WHERE id_disponibilidade = %s"
            cursor.execute(query, (dados['id'],))
            
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Horário gerenciado com sucesso"}

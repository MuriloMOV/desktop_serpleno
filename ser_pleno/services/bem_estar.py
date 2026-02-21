from config.db_config import get_db_connection

class ServicoBemEstar:
    def obter_dashboard(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Últimos registros de humor e checkins
        cursor.execute("SELECT * FROM desktop_moodentry ORDER BY entry_date DESC LIMIT 10")
        moods = cursor.fetchall()
        cursor.execute("SELECT * FROM desktop_wellnesscheckin ORDER BY check_in_date DESC LIMIT 10")
        checkins = cursor.fetchall()
        # Média geral do humor
        cursor.execute("SELECT AVG(mood_level) as average_mood FROM desktop_moodentry")
        avg = cursor.fetchone()
        connection.close()
        data = {
            'summary': {'average_mood': avg.get('average_mood') if avg else None},
            'moods': moods,
            'checkins': checkins
        }
        return {"success": True, "data": data}

    def listar_entradas_humor(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_moodentry")
        result = cursor.fetchall()
        connection.close()
        return {"success": True, "data": result}

    def obter_medias_humor(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT AVG(mood_level) as average_mood FROM desktop_moodentry")
        result = cursor.fetchone()
        connection.close()
        return {"success": True, "data": result}

    def obter_humor_estudante(self, id_estudante):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_moodentry WHERE student_id = %s", (id_estudante,))
        result = cursor.fetchall()
        connection.close()
        return {"success": True, "data": result}

    def listar_checkins(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_wellnesscheckin ORDER BY check_in_date DESC LIMIT 20")
        result = cursor.fetchall()
        connection.close()
        return {"success": True, "data": {"checkins": result}}

    def listar_estudantes_risco(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Buscar alunos com marcação de atenção e agrupar por prioridade
        # Conforme ser_pleno.sql, a PK da tabela aluno é 'id' (não 'id_aluno')
        cursor.execute("SELECT id, nome, priority_level, attention_reason, requires_attention FROM aluno WHERE requires_attention = 1")
        rows = cursor.fetchall()
        groups = {'critical': [], 'high': [], 'medium': [], 'low': []}
        for r in rows:
            priority = r.get('priority_level') or 0
            student = {'id': r.get('id'), 'name': r.get('nome'), 'reasons': [r.get('attention_reason') or 'Requer atenção']}
            if priority >= 4:
                groups['critical'].append(student)
            elif priority == 3:
                groups['high'].append(student)
            elif priority == 2:
                groups['medium'].append(student)
            else:
                groups['low'].append(student)
        connection.close()
        return {"success": True, "data": {"groups": groups}}

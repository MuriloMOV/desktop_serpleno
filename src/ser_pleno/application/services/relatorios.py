from ser_pleno.infrastructure.database import get_db_connection

class ServicoRelatorio:
    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM desktop_report WHERE 1=1"
        params = []
        
        if tipo:
            query += " AND report_type = %s"
            params.append(tipo)
        if data_inicio:
            query += " AND generated_at >= %s"
            params.append(data_inicio)
            
        offset = (pagina - 1) * 10
        query += " ORDER BY generated_at DESC LIMIT 10 OFFSET %s"
        params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        relatorios = []
        for r in rows:
            relatorios.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'report_type': r.get('report_type'),
                'format': r.get('format'),
                'generated_at': str(r.get('generated_at')),
                'file_path': r.get('file_path'),
                'file_size': r.get('file_size'),
                'is_public': bool(r.get('is_public')),
                'expires_at': str(r.get('expires_at')) if r.get('expires_at') else None
            })
            
        connection.close()
        return {"success": True, "data": relatorios}

    def obter_estatisticas(self, periodo='month'):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # EstatÍsticas básicas
        cursor.execute("SELECT COUNT(*) as total_students FROM aluno")
        total_students = cursor.fetchone()['total_students']
        
        cursor.execute("SELECT COUNT(*) as active_appointments FROM agendamento WHERE status = 'completed'")
        active_appointments = cursor.fetchone()['active_appointments']
        
        cursor.execute("SELECT COUNT(*) as pending_screenings FROM desktop_screening WHERE status = 'pending'")
        pending_screenings = cursor.fetchone()['pending_screenings']
        
        cursor.execute("SELECT AVG(score) as average_score FROM desktop_screening WHERE score IS NOT NULL")
        avg_score = cursor.fetchone()['average_score']
        
        connection.close()
        
        return {"success": True, "data": {
            'total_students': total_students,
            'active_appointments': active_appointments,
            'pending_screenings': pending_screenings,
            'average_score': round(avg_score, 1) if avg_score else 0
        }}

    def gerar_relatorio(self, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
            INSERT INTO desktop_report (
                name, report_type, format, generated_at, parameters, data,
                file_path, file_size, is_public, expires_at, generated_by_id
            ) VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            dados['name'], dados['report_type'], dados.get('format', 'pdf'),
            dados.get('parameters', '{}'), dados.get('data', '{}'),
            dados.get('file_path', ''), dados.get('file_size', 0),
            dados.get('is_public', False), dados.get('expires_at'),
            dados.get('generated_by_id')
        ))
        connection.commit()
        relatorio_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": relatorio_id}}

    def baixar_relatorio(self, id_relatorio):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT file_path, file_name FROM desktop_report WHERE id = %s", (id_relatorio,))
        row = cursor.fetchone()
        connection.close()
        
        if row:
            return {"success": True, "data": {"file_path": row['file_path']}}
        return {"success": False, "message": "Relatório não encontrado"}

    def deletar_relatorio(self, id_relatorio):
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM desktop_report WHERE id = %s", (id_relatorio,))
        connection.commit()
        connection.close()
        
        return {"success": True, "message": "Relatório deletado com sucesso"}

    def exportar_estudantes(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM aluno ORDER BY nome ASC")
        rows = cursor.fetchall()
        connection.close()
        
        return {"success": True, "data": list(rows)}

    def exportar_agendamentos(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM agendamento ORDER BY data_hora DESC")
        rows = cursor.fetchall()
        connection.close()
        
        return {"success": True, "data": list(rows)}

    def exportar_triagens(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM desktop_screening ORDER BY created_at DESC")
        rows = cursor.fetchall()
        connection.close()
        
        return {"success": True, "data": list(rows)}

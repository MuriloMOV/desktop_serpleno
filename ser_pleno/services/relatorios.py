import json
from config.db_config import get_db_connection

class ServicoRelatorio:
    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Corrigindo para retornar no formato que o Controller espera: {"reports": [...]}
        query = "SELECT * FROM desktop_report WHERE 1=1"
        params = []
        
        if tipo and tipo != "Todos os tipos":
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
                'type': r.get('report_type'), # 'type' para a View
                'format': r.get('format'),
                'generated_at': str(r.get('generated_at')),
                'file_path': r.get('file_path')
            })
            
        connection.close()
        # Envolvendo em 'reports' para o update_view do Controller ler corretamente
        return {"success": True, "data": {"reports": relatorios}}

    def obter_estatisticas(self, periodo='month'):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Mapeando os nomes das colunas exatamente como a View espera no dicionário 'summary'
        stats_query = {
            'students_total': "SELECT COUNT(*) as total FROM aluno",
            'appointments_total': "SELECT COUNT(*) as total FROM agendamento WHERE status = 'completed'",
            'interventions_total': "SELECT COUNT(*) as total FROM agendamento WHERE status = 'scheduled'", # Exemplo
            'screenings_total': "SELECT COUNT(*) as total FROM desktop_screening"
        }
        
        resumo = {}
        for key, sql in stats_query.items():
            cursor.execute(sql)
            resumo[key] = cursor.fetchone()['total']
        
        connection.close()
        
        return {"success": True, "data": {"summary": resumo}}

    def criar_relatorio(self, dados):
        """
        Renomeado para criar_relatorio para bater com o Controller.
        Insere no banco seguindo a estrutura do Django.
        """
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Preparando JSONs (Django armazena como JSON no banco)
        parameters = json.dumps(dados.get('parameters', {}))
        report_data = json.dumps(dados.get('data', {}))

        query = """
            INSERT INTO desktop_report (
                name, report_type, format, generated_at, parameters, data,
                file_path, file_size, is_public, generated_by_id
            ) VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
        """
        
        # generated_by_id pode ser None se não houver login no desktop ainda
        user_id = dados.get('generated_by_id', None) 

        cursor.execute(query, (
            dados['name'], 
            dados['report_type'], 
            dados.get('format', 'pdf'),
            parameters, 
            report_data,
            dados.get('file_path', ''), 
            dados.get('file_size', 0),
            dados.get('is_public', False), 
            user_id
        ))
        
        connection.commit()
        relatorio_id = cursor.lastrowid
        connection.close()
        
        return {"success": True, "data": {"id": relatorio_id}}

    # --- Métodos de Exportação (Mantidos iguais, apenas garantindo o retorno) ---
    def exportar_estudantes(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM aluno ORDER BY nome ASC")
        rows = cursor.fetchall()
        connection.close()
        # Aqui você pode adicionar a lógica de gerar o Excel/CSV fisicamente
        print("Exportando estudantes...")
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

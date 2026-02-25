import json
import pandas as pd
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from tkinter import filedialog
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

    # --- Métodos de Exportação  ---
    def exportar_estudantes(self, formato):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT nome, sala, curso, professor_responsavel FROM aluno ORDER BY nome ASC")
        dados = cursor.fetchall()
        connection.close()
        
        return self._gerar_arquivo_fisico(dados, "Relatorio_Estudantes", formato)

    def exportar_agendamentos(self, formato):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        # Ajuste as colunas conforme seu banco
        cursor.execute("SELECT id, data_hora, status, aluno_id FROM agendamento ORDER BY data_hora DESC")
        dados = cursor.fetchall()
        connection.close()
        
        return self._gerar_arquivo_fisico(dados, "Relatorio_Agenda", formato)

    def exportar_triagens(self, formato):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT status, priority, completed_date, observations FROM desktop_screening ORDER BY created_at DESC")
        dados = cursor.fetchall()
        connection.close()
        
        return self._gerar_arquivo_fisico(dados, "Relatorio_Triagens", formato)

    def _gerar_arquivo_fisico(self, dados, nome_sugerido, formato):
        """Método interno auxiliar para processar a criação dos arquivos"""
        if not dados:
            return False

        # 1. Escolher local de salvamento
        extensoes = {
            "excel": (".xlsx", [("Excel files", "*.xlsx")]),
            "pdf": (".pdf", [("PDF files", "*.pdf")]),
            "word": (".docx", [("Word files", "*.docx")])
        }
        
        ext, ft = extensoes.get(formato)
        caminho = filedialog.asksaveasfilename(
            initialfile=nome_sugerido + ext,
            defaultextension=ext,
            filetypes=ft
        )

        if not caminho:
            return False # Usuário cancelou

        try:
            # 2. Lógica por Formato
            if formato == "excel":
                df = pd.DataFrame(dados)
                df.to_excel(caminho, index=False)

            elif formato == "word":
                doc = Document()
                doc.add_heading(nome_sugerido.replace("_", " "), 0)
                
                # Criar uma tabela simples no Word
                if dados:
                    table = doc.add_table(rows=1, cols=len(dados[0]))
                    hdr_cells = table.rows[0].cells
                    for i, col_name in enumerate(dados[0].keys()):
                        hdr_cells[i].text = str(col_name).upper()
                    
                    for item in dados:
                        row_cells = table.add_row().cells
                        for i, value in enumerate(item.values()):
                            row_cells[i].text = str(value)
                doc.save(caminho)

            elif formato == "pdf":
                c = canvas.Canvas(caminho, pagesize=A4)
                width, height = A4
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, nome_sugerido.replace("_", " "))
                
                c.setFont("Helvetica", 10)
                y = height - 80
                for item in dados:
                    texto = " | ".join([f"{k}: {v}" for k, v in item.items()])
                    c.drawString(50, y, texto)
                    y -= 20
                    if y < 50: # Nova página se acabar o espaço
                        c.showPage()
                        y = height - 50
                c.save()

            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return False
    
    
# -*- coding: utf-8 -*-
"""Repositório de relatórios."""

from ser_pleno.repositories.base import fetch_all, fetch_one, execute_non_query


class RelatorioRepository:
    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1):
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
        
        return fetch_all(query, params)

    def obter_estatisticas(self):
        """Obtém estatísticas básicas do sistema."""
        total_students = fetch_one("SELECT COUNT(*) as total_students FROM aluno")
        active_appointments = fetch_one("SELECT COUNT(*) as active_appointments FROM agendamento WHERE status = 'completed'")
        pending_screenings = fetch_one("SELECT COUNT(*) as pending_screenings FROM desktop_screening WHERE status = 'pending'")
        avg_score = fetch_one("SELECT AVG(score) as average_score FROM desktop_screening WHERE score IS NOT NULL")
        
        return {
            "total_students": total_students.get("total_students") if total_students else 0,
            "active_appointments": active_appointments.get("active_appointments") if active_appointments else 0,
            "pending_screenings": pending_screenings.get("pending_screenings") if pending_screenings else 0,
            "average_score": round(avg_score.get("average_score"), 1) if avg_score and avg_score.get("average_score") else 0
        }

    def criar_relatorio(self, name, report_type, format, parameters, data, file_path, file_size, is_public, expires_at, generated_by_id):
        """Cria um novo relatório."""
        query = """
            INSERT INTO desktop_report (
                name, report_type, format, generated_at, parameters, data,
                file_path, file_size, is_public, expires_at, generated_by_id
            ) VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_non_query(query, (
            name, report_type, format, parameters, data,
            file_path, file_size, is_public, expires_at, generated_by_id
        ))

    def obter_relatorio_por_id(self, id_relatorio):
        """Obtém um relatório pelo ID."""
        query = "SELECT file_path, file_name FROM desktop_report WHERE id = %s"
        return fetch_one(query, (id_relatorio,))

    def deletar_relatorio(self, id_relatorio):
        """Deleta um relatório pelo ID."""
        query = "DELETE FROM desktop_report WHERE id = %s"
        return execute_non_query(query, (id_relatorio,))

    def exportar_estudantes(self):
        """Exporta todos os estudantes."""
        query = "SELECT * FROM aluno ORDER BY nome ASC"
        return fetch_all(query)

    def exportar_agendamentos(self):
        """Exporta todos os agendamentos."""
        query = "SELECT * FROM agendamento ORDER BY data_hora DESC"
        return fetch_all(query)

    def exportar_triagens(self):
        """Exporta todas as triagens."""
        query = "SELECT * FROM desktop_screening ORDER BY created_at DESC"
        return fetch_all(query)

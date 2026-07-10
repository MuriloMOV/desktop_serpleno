# -*- coding: utf-8 -*-
"""Repositório de agendamentos."""

from ser_pleno.repositories.base import fetch_all, fetch_one, execute_non_query
from datetime import date, datetime, time


class AgendamentoRepository:
    def listar_proximos(self, limite=5):
        query = """
            SELECT a.id, a.data_hora, a.status, al.nome AS student_name, al.curso
            FROM agendamento a
            LEFT JOIN aluno al ON a.student_id = al.id_aluno
            WHERE a.data_hora > NOW() AND a.status != 'cancelled'
            ORDER BY a.data_hora ASC
            LIMIT %s
        """
        return fetch_all(query, (limite,))

    def contar_por_status(self, status):
        query = "SELECT COUNT(*) as total FROM agendamento WHERE status = %s"
        return fetch_one(query, (status,))

    def contar_hoje(self):
        query = "SELECT COUNT(*) as total FROM agendamento WHERE DATE(data_hora) = CURDATE()"
        return fetch_one(query)

    def contar_hoje_ativos(self):
        query = "SELECT COUNT(*) as total FROM agendamento WHERE DATE(data_hora) = CURDATE() AND status != 'canceled'"
        return fetch_one(query)

    def total_disponibilidade(self):
        query = "SELECT COUNT(*) as total FROM disponibilidade WHERE is_active = 1"
        return fetch_one(query)

    def taxa_presenca_ultimos_30_dias(self):
        query = """
            SELECT COUNT(*) as total, SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM agendamento WHERE DATE(data_hora) >= CURDATE() - INTERVAL 30 DAY
        """
        return fetch_one(query)

    def verificar_disponibilidade(self, data, time_str):
        """Verifica se um horário está disponível."""
        data_hora_str = f"{data} {time_str}"
        data_hora = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
        query = """
            SELECT id FROM agendamento 
            WHERE data_hora BETWEEN %s AND %s
        """
        return fetch_one(query, (data_hora, data_hora + timedelta(minutes=59)))

    def obter_nome_aluno(self, id_aluno):
        """Obtém o nome do aluno pelo ID."""
        query = "SELECT nome FROM aluno WHERE id_aluno = %s"
        return fetch_one(query, (id_aluno,))

    def obter_time_id(self, hora_str):
        """Obtém o ID do horário na tabela disponibilidade."""
        time_obj = datetime.strptime(hora_str, "%H:%M").time()
        query = "SELECT id_disponibilidade FROM disponibilidade WHERE Horario = %s"
        return fetch_one(query, (time_obj,))

    def criar_agendamento(self, id_aluno, data_hora, nome_agendamento, motivo, status, local, profissional, laudo, origem):
        """Cria um novo agendamento no banco local."""
        query = """
            INSERT INTO agendamento (student_id, data_hora, nome, motivo, status, local, profissional, laudo, origem)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return execute_non_query(query, (
            id_aluno, data_hora, nome_agendamento, motivo, status, local, profissional, laudo, origem
        ))

    def listar_agendamentos(self, data=None):
        """Lista agendamentos com filtro opcional por data."""
        query = """
            SELECT a.id, al.nome, al.id_aluno, a.data_hora, a.motivo, a.status, a.local, a.profissional, a.laudo, a.origem
            FROM agendamento a
            INNER JOIN aluno al ON a.student_id = al.id_aluno
        """
        params = []
        if data:
            query += " WHERE DATE(a.data_hora) = %s"
            params.append(data)
        query += " ORDER BY a.data_hora"
        return fetch_all(query, params)

    def atualizar_agendamento(self, id_agendamento, id_aluno, data_hora, motivo, status, local, profissional, laudo, origem):
        """Atualiza um agendamento existente."""
        query = """
            UPDATE agendamento 
            SET student_id = %s, data_hora = %s, motivo = %s, status = %s, local = %s, profissional = %s, laudo = %s, origem = %s
            WHERE id = %s
        """
        return execute_non_query(query, (
            id_aluno, data_hora, motivo, status, local, profissional, laudo, origem, id_agendamento
        ))

    def deletar_agendamento(self, id_agendamento):
        """Deleta um agendamento pelo ID."""
        query = "DELETE FROM agendamento WHERE id = %s"
        return execute_non_query(query, (id_agendamento,))

    def adicionar_horario_disponibilidade(self, horario):
        """Adiciona um novo horário na tabela de disponibilidade."""
        time_obj = datetime.strptime(horario, "%H:%M").time()
        query = """
            INSERT INTO disponibilidade (Horario, is_active, Dias)
            VALUES (%s, 1, 'segunda-terca-quarta-quinta-sexta')
        """
        return execute_non_query(query, (time_obj,))

    def verificar_horario_existe(self, horario):
        """Verifica se um horário já existe na tabela de disponibilidade."""
        time_obj = datetime.strptime(horario, "%H:%M").time()
        query = "SELECT id_disponibilidade FROM disponibilidade WHERE Horario = %s"
        return fetch_one(query, (time_obj,))

    def remover_horario_disponibilidade(self, horario):
        """Remove um horário da tabela de disponibilidade."""
        time_obj = datetime.strptime(horario, "%H:%M").time()
        # Verifica se há agendamentos usando este horário
        query_uso = "SELECT id FROM agendamento WHERE TIME(data_hora) = %s"
        uso = fetch_one(query_uso, (time_obj,))
        if uso:
            return {"success": False, "message": "Não é possível remover horário com agendamentos associados"}
        
        # Remove o horário
        query_delete = "DELETE FROM disponibilidade WHERE Horario = %s"
        return execute_non_query(query_delete, (time_obj,))

    def obter_agendamento_para_sincronizacao(self, appointment_id):
        """Obtém os dados de um agendamento para sincronização com a API."""
        query = """
            SELECT a.id, a.student_id, a.data_hora, a.motivo, a.status, a.local, a.profissional, a.laudo, a.origem,
                   al.nome as nome_aluno
            FROM agendamento a
            INNER JOIN aluno al ON a.student_id = al.id_aluno
            WHERE a.id = %s
        """
        return fetch_one(query, (appointment_id,))

    def obter_ultimo_id_inserido(self):
        """Obtém o último ID inserido no banco de dados."""
        return fetch_one("SELECT LAST_INSERT_ID() as id", ()).get("id")

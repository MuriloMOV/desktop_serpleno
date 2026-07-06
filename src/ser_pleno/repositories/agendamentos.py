# -*- coding: utf-8 -*-
"""Repositório de agendamentos."""

from ser_pleno.repositories.base import fetch_all, fetch_one, execute_non_query
from datetime import date


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

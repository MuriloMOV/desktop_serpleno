# -*- coding: utf-8 -*-
"""Repositório de triagens."""

from repositories.base import fetch_all, fetch_one, execute_non_query


class TriagemRepository:
    def listar(self, busca=None, status=None, prioridade=None, id_estudante=None, pagina=1):
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

        return fetch_all(query, params)

    def obter(self, id_triagem):
        query = """
            SELECT ds.*, a.nome AS student_name, df.name AS form_name, df.questions
            FROM desktop_screening ds
            LEFT JOIN aluno a ON ds.student_id = a.id_aluno
            LEFT JOIN desktop_screeningform df ON ds.form_id = df.id
            WHERE ds.id = %s
        """
        return fetch_one(query, (id_triagem,))

    def criar(self, dados):
        query = """
            INSERT INTO desktop_screening (
                student_id, form_id, status, priority, scheduled_date,
                responses, observations, recommendations, requires_followup,
                followup_date, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        return execute_non_query(query, (
            dados['student_id'], dados['form_id'], dados.get('status', 'pending'),
            dados.get('priority', 'medium'), dados.get('scheduled_date'),
            dados.get('responses', '{}'), dados.get('observations', ''),
            dados.get('recommendations', ''), dados.get('requires_followup', False),
            dados.get('followup_date')
        ))

    def atualizar(self, id_triagem, dados):
        query = """
            UPDATE desktop_screening
            SET student_id = %s, form_id = %s, status = %s, priority = %s,
                scheduled_date = %s, responses = %s, observations = %s,
                recommendations = %s, requires_followup = %s, followup_date = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        return execute_non_query(query, (
            dados['student_id'], dados['form_id'], dados.get('status', 'pending'),
            dados.get('priority', 'medium'), dados.get('scheduled_date'),
            dados.get('responses', '{}'), dados.get('observations', ''),
            dados.get('recommendations', ''), dados.get('requires_followup', False),
            dados.get('followup_date'), id_triagem
        ))

    def deletar(self, id_triagem):
        query = "DELETE FROM desktop_screening WHERE id = %s"
        return execute_non_query(query, (id_triagem,))

    def listar_formularios(self):
        query = "SELECT * FROM desktop_screeningform WHERE is_active = 1 ORDER BY created_at DESC"
        return fetch_all(query)

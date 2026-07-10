# -*- coding: utf-8 -*-
"""Repositório de orientações."""

from ser_pleno.repositories.base import fetch_all, fetch_one, execute_non_query
import json


class OrientacaoRepository:
    def listar_orientacoes(self, id_estudante=None):
        """Lista orientações com filtro opcional por estudante."""
        query = """
            SELECT o.*, a.nome as student_name, a.id_aluno as student_id
            FROM desktop_orientation o
            LEFT JOIN aluno a ON o.student_id = a.id_aluno
            WHERE 1=1
        """
        params = []
        
        if id_estudante:
            query += " AND o.student_id = %s"
            params.append(id_estudante)
        
        query += " ORDER BY o.session_date DESC"
        return fetch_all(query, params)

    def obter_orientacao(self, id_orientacao):
        """Obtém uma orientação específica pelo ID."""
        query = """
            SELECT o.*, a.nome as student_name, a.id_aluno as student_id
            FROM desktop_orientation o
            LEFT JOIN aluno a ON o.student_id = a.id_aluno
            WHERE o.id = %s
        """
        return fetch_one(query, (id_orientacao,))

    def criar_orientacao(self, student_id, title, theme, session_date, content, is_markdown, motivational_message, action_plan, psychologist):
        """Cria uma nova orientação."""
        query = """
            INSERT INTO desktop_orientation (
                student_id, title, theme, session_date, content, 
                is_markdown, motivational_message, action_plan, 
                psychologist, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        action_plan_json = json.dumps(action_plan) if action_plan else "[]"
        return execute_non_query(query, (
            student_id, title, theme, session_date, content,
            is_markdown, motivational_message, action_plan_json, psychologist
        ))

    def atualizar_orientacao(self, id_orientacao, title, theme, session_date, content, is_markdown, motivational_message, action_plan, psychologist):
        """Atualiza uma orientação existente."""
        action_plan_json = json.dumps(action_plan) if action_plan else "[]"
        query = """
            UPDATE desktop_orientation 
            SET title = %s, theme = %s, session_date = %s, content = %s,
                is_markdown = %s, motivational_message = %s, action_plan = %s,
                psychologist = %s, updated_at = NOW()
            WHERE id = %s
        """
        return execute_non_query(query, (
            title, theme, session_date, content, is_markdown,
            motivational_message, action_plan_json, psychologist, id_orientacao
        ))

    def deletar_orientacao(self, id_orientacao):
        """Deleta uma orientação pelo ID."""
        query = "DELETE FROM desktop_orientation WHERE id = %s"
        return execute_non_query(query, (id_orientacao,))

    def obter_estatisticas(self):
        """Obtém estatísticas das orientações."""
        total = fetch_one("SELECT COUNT(*) as total FROM desktop_orientation")
        by_theme = fetch_all("""
            SELECT theme, COUNT(*) as count 
            FROM desktop_orientation 
            GROUP BY theme 
            ORDER BY count DESC
        """)
        by_month = fetch_all("""
            SELECT DATE_FORMAT(session_date, '%Y-%m-01') as month, COUNT(*) as count 
            FROM desktop_orientation 
            GROUP BY DATE_FORMAT(session_date, '%Y-%m-01')
            ORDER BY month DESC
            LIMIT 12
        """)
        
        return {
            "total": total.get("total") if total else 0,
            "by_theme": [
                {"theme": r["theme"] or "Sem tema", "count": r["count"]}
                for r in by_theme
            ],
            "by_month": [
                {"month": r["month"], "count": r["count"]} for r in by_month
            ]
        }

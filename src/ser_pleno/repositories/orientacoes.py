# -*- coding: utf-8 -*-
"""Repositorio de orientacoes."""

import json
from datetime import datetime

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
    generate_local_id,
)
from ser_pleno.infrastructure.api.sync_service import queue_sync


class OrientacaoRepository:
    @with_local_fallback("_local_listar_orientacoes")
    def listar_orientacoes(self, id_estudante=None):
        """Lista orientacoes com filtro opcional por estudante."""
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

    def _local_listar_orientacoes(self, id_estudante=None):
        rows = local_cache.list_orientations(student_id=id_estudante)
        name_map = local_cache.get_student_name_map()
        resultado = []
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "student_id": r.get("student_id"),
                "title": r.get("title"),
                "theme": r.get("theme"),
                "session_date": r.get("session_date"),
                "content": r.get("content"),
                "is_markdown": r.get("is_markdown", 0),
                "motivational_message": r.get("motivational_message"),
                "action_plan": r.get("action_plan"),
                "psychologist": r.get("psychologist"),
                "student_name": name_map.get(r.get("student_id"), "Estudante"),
                "student_id": r.get("student_id"),
            })
        return resultado

    @with_local_fallback("_local_obter_orientacao")
    def obter_orientacao(self, id_orientacao):
        """Obtem uma orientacao especifica pelo ID."""
        query = """
            SELECT o.*, a.nome as student_name, a.id_aluno as student_id
            FROM desktop_orientation o
            LEFT JOIN aluno a ON o.student_id = a.id_aluno
            WHERE o.id = %s
        """
        return fetch_one(query, (id_orientacao,))

    def _local_obter_orientacao(self, id_orientacao):
        rows = local_cache.list_all("orientations", where_clause="id=?", params=(id_orientacao,))
        if not rows:
            return None
        r = rows[0]
        name_map = local_cache.get_student_name_map()
        return {
            "id": r.get("id"),
            "student_id": r.get("student_id"),
            "title": r.get("title"),
            "theme": r.get("theme"),
            "session_date": r.get("session_date"),
            "content": r.get("content"),
            "is_markdown": r.get("is_markdown", 0),
            "motivational_message": r.get("motivational_message"),
            "action_plan": r.get("action_plan"),
            "psychologist": r.get("psychologist"),
            "student_name": name_map.get(r.get("student_id"), "Estudante"),
            "student_id": r.get("student_id"),
        }

    def criar_orientacao(self, student_id, title, theme, session_date, content, is_markdown, motivational_message, action_plan, psychologist):
        """Cria uma nova orientacao."""
        query = """
            INSERT INTO desktop_orientation (
                student_id, title, theme, session_date, content,
                is_markdown, motivational_message, action_plan,
                psychologist_id, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        action_plan_json = json.dumps(action_plan) if action_plan else "[]"
        params = (
            student_id, title, theme, session_date, content,
            is_markdown, motivational_message, action_plan_json, psychologist
        )
        orientation_data = {
            "student_id": student_id,
            "title": title,
            "theme": theme,
            "session_date": str(session_date),
            "content": content,
            "is_markdown": int(is_markdown),
            "motivational_message": motivational_message,
            "action_plan": action_plan_json,
            "psychologist": psychologist,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            orientation_data["id"] = last_id
            local_cache.upsert_orientation(orientation_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            orientation_data["id"] = last_id
            return orientation_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="orientations", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def atualizar_orientacao(self, id_orientacao, title, theme, session_date, content, is_markdown, motivational_message, action_plan, psychologist):
        """Atualiza uma orientacao existente."""
        action_plan_json = json.dumps(action_plan) if action_plan else "[]"
        query = """
            UPDATE desktop_orientation
            SET title = %s, theme = %s, session_date = %s, content = %s,
                is_markdown = %s, motivational_message = %s, action_plan = %s,
                psychologist_id = %s, updated_at = NOW()
            WHERE id = %s
        """
        params = (
            title, theme, session_date, content, is_markdown,
            motivational_message, action_plan_json, psychologist, id_orientacao
        )
        orientation_data = {
            "id": id_orientacao,
            "student_id": None,
            "title": title,
            "theme": theme,
            "session_date": str(session_date),
            "content": content,
            "is_markdown": int(is_markdown),
            "motivational_message": motivational_message,
            "action_plan": action_plan_json,
            "psychologist": psychologist,
        }

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.upsert_orientation(orientation_data)
            return 1

        def _queue_data(mysql_result, entity_id):
            return orientation_data

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="orientations", entity_id=id_orientacao,
            queue_data_fn=_queue_data,
        )

    def deletar_orientacao(self, id_orientacao):
        """Deleta uma orientacao pelo ID."""
        query = "DELETE FROM desktop_orientation WHERE id = %s"

        def _mysql():
            execute_non_query(query, (id_orientacao,))
            return 1

        def _local(mysql_result):
            local_cache.delete("orientations", "id", id_orientacao)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="orientations", entity_id=id_orientacao,
            queue_data_fn=lambda r, eid: {"id": id_orientacao},
        )

    @with_local_fallback("_local_obter_estatisticas")
    def obter_estatisticas(self):
        """Obtem estatisticas das orientacoes."""
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

    def _local_obter_estatisticas(self):
        rows = local_cache.list_all("orientations")
        total = len(rows)
        by_theme: dict = {}
        for r in rows:
            theme = r.get("theme") or "Sem tema"
            by_theme[theme] = by_theme.get(theme, 0) + 1
        by_month: dict = {}
        for r in rows:
            session_date = r.get("session_date") or ""
            month = session_date[:7] if len(session_date) >= 7 else "desconhecido"
            by_month[month] = by_month.get(month, 0) + 1

        return {
            "total": total,
            "by_theme": [{"theme": k, "count": v} for k, v in sorted(by_theme.items(), key=lambda x: x[1], reverse=True)],
            "by_month": [{"month": k, "count": v} for k, v in sorted(by_month.items(), reverse=True)[:12]],
        }

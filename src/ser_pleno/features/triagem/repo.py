# -*- coding: utf-8 -*-
"""Repositorio de triagens."""

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


class TriagemRepository:
    @with_local_fallback("_local_listar")
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

    def _local_listar(self, busca=None, status=None, prioridade=None, id_estudante=None, pagina=1):
        rows = local_cache.list_screenings(student_id=id_estudante)
        resultado = []
        for r in rows:
            if status and r.get("status") != status:
                continue
            if prioridade and r.get("priority") != prioridade:
                continue
            resultado.append({
                "id": r.get("id"),
                "student_id": r.get("student_id"),
                "form_id": r.get("form_id"),
                "status": r.get("status"),
                "priority": r.get("priority"),
                "scheduled_date": r.get("scheduled_date"),
                "responses": r.get("responses"),
                "observations": r.get("observations"),
                "recommendations": r.get("recommendations"),
                "requires_followup": r.get("requires_followup", 0),
                "followup_date": r.get("followup_date"),
                "student_name": "Estudante",
                "form_name": "Formulario",
            })
        return resultado

    @with_local_fallback("_local_obter")
    def obter(self, id_triagem):
        query = """
            SELECT ds.*, a.nome AS student_name, df.name AS form_name, df.questions
            FROM desktop_screening ds
            LEFT JOIN aluno a ON ds.student_id = a.id_aluno
            LEFT JOIN desktop_screeningform df ON ds.form_id = df.id
            WHERE ds.id = %s
        """
        return fetch_one(query, (id_triagem,))

    def _local_obter(self, id_triagem):
        rows = local_cache.list_all("screenings", where_clause="id=?", params=(id_triagem,))
        if not rows:
            return None
        r = rows[0]
        return {
            "id": r.get("id"),
            "student_id": r.get("student_id"),
            "form_id": r.get("form_id"),
            "status": r.get("status"),
            "priority": r.get("priority"),
            "scheduled_date": r.get("scheduled_date"),
            "responses": r.get("responses"),
            "observations": r.get("observations"),
            "recommendations": r.get("recommendations"),
            "requires_followup": r.get("requires_followup", 0),
            "followup_date": r.get("followup_date"),
            "student_name": "Estudante",
            "form_name": "Formulario",
            "questions": None,
        }

    def criar(self, dados):
        query = """
            INSERT INTO desktop_screening (
                student_id, form_id, status, priority, scheduled_date,
                responses, observations, recommendations, requires_followup,
                followup_date, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (
            dados['student_id'], dados['form_id'], dados.get('status', 'pending'),
            dados.get('priority', 'medium'), dados.get('scheduled_date'),
            dados.get('responses', '{}'), dados.get('observations', ''),
            dados.get('recommendations', ''), dados.get('requires_followup', False),
            dados.get('followup_date')
        )
        screening_data = {
            "student_id": dados.get('student_id'),
            "form_id": dados.get('form_id'),
            "status": dados.get('status', 'pending'),
            "priority": dados.get('priority', 'medium'),
            "scheduled_date": dados.get('scheduled_date'),
            "responses": dados.get('responses', '{}'),
            "observations": dados.get('observations', ''),
            "recommendations": dados.get('recommendations', ''),
            "requires_followup": int(dados.get('requires_followup', False)),
            "followup_date": dados.get('followup_date'),
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            screening_data["id"] = last_id
            local_cache.upsert_screening(screening_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            screening_data["id"] = last_id
            return screening_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="screenings", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def atualizar(self, id_triagem, dados):
        query = """
            UPDATE desktop_screening
            SET student_id = %s, form_id = %s, status = %s, priority = %s,
                scheduled_date = %s, responses = %s, observations = %s,
                recommendations = %s, requires_followup = %s, followup_date = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        params = (
            dados['student_id'], dados['form_id'], dados.get('status', 'pending'),
            dados.get('priority', 'medium'), dados.get('scheduled_date'),
            dados.get('responses', '{}'), dados.get('observations', ''),
            dados.get('recommendations', ''), dados.get('requires_followup', False),
            dados.get('followup_date'), id_triagem
        )
        screening_data = {
            "id": id_triagem,
            "student_id": dados.get('student_id'),
            "form_id": dados.get('form_id'),
            "status": dados.get('status', 'pending'),
            "priority": dados.get('priority', 'medium'),
            "scheduled_date": dados.get('scheduled_date'),
            "responses": dados.get('responses', '{}'),
            "observations": dados.get('observations', ''),
            "recommendations": dados.get('recommendations', ''),
            "requires_followup": int(dados.get('requires_followup', False)),
            "followup_date": dados.get('followup_date'),
        }

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.upsert_screening(screening_data)
            return 1

        def _queue_data(mysql_result, entity_id):
            return screening_data

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="screenings", entity_id=id_triagem,
            queue_data_fn=_queue_data,
        )

    def deletar(self, id_triagem):
        query = "DELETE FROM desktop_screening WHERE id = %s"

        def _mysql():
            execute_non_query(query, (id_triagem,))
            return 1

        def _local(mysql_result):
            local_cache.delete("screenings", "id", id_triagem)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="screenings", entity_id=id_triagem,
            queue_data_fn=lambda r, eid: {"id": id_triagem},
        )

    @with_local_fallback("_local_listar_formularios")
    def listar_formularios(self):
        query = "SELECT * FROM desktop_screeningform WHERE is_active = 1 ORDER BY created_at DESC"
        return fetch_all(query)

    def _local_listar_formularios(self):
        # Formularios de triagem nao sao sincronizados no cache local
        return []

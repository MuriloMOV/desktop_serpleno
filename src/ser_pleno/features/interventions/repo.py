# -*- coding: utf-8 -*-
"""Repositorio de intervencoes."""

import json
from typing import Any, Dict, List, Optional

from ser_pleno.infrastructure.api.sync_service import queue_sync
from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
    generate_local_id,
)


class IntervencaoRepository:
    @with_local_fallback("_local_listar_intervencoes")
    def listar_intervencoes(
        self,
        student_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT i.*, a.nome as student_name
            FROM desktop_intervention i
            LEFT JOIN aluno a ON i.student_id = a.id_aluno
            WHERE 1=1
        """
        params = []

        if student_id:
            query += " AND i.student_id = %s"
            params.append(student_id)
        if date_from:
            query += " AND i.date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND i.date <= %s"
            params.append(date_to)

        query += " ORDER BY i.date DESC, i.id DESC"
        return fetch_all(query, params)

    def _local_listar_intervencoes(
        self,
        student_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        rows = local_cache.list_interventions(
            student_id=student_id, date_from=date_from, date_to=date_to
        )
        name_map = local_cache.get_student_name_map()
        resultado = []
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "student_id": r.get("student_id"),
                "student_name": name_map.get(r.get("student_id"), "Estudante"),
                "date": r.get("date"),
                "intervention_type": r.get("intervention_type"),
                "duration_minutes": r.get("duration_minutes"),
                "intervention_notes": r.get("intervention_notes"),
                "outcome": r.get("outcome"),
                "outcome_notes": r.get("outcome_notes"),
                "follow_up_required": r.get("follow_up_required", 0),
                "follow_up_date": r.get("follow_up_date"),
                "follow_up_completed": r.get("follow_up_completed", 0),
                "is_confidential": r.get("is_confidential", 0),
                "tags": r.get("tags"),
            })
        return resultado

    @with_local_fallback("_local_obter_intervencao")
    def obter_intervencao(self, id_intervencao: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT i.*, a.nome as student_name
            FROM desktop_intervention i
            LEFT JOIN aluno a ON i.student_id = a.id_aluno
            WHERE i.id = %s
        """
        return fetch_one(query, (id_intervencao,))

    def _local_obter_intervencao(self, id_intervencao: int) -> Optional[Dict[str, Any]]:
        rows = local_cache.list_all("interventions", where_clause="id=?", params=(id_intervencao,))
        if not rows:
            return None
        r = rows[0]
        name_map = local_cache.get_student_name_map()
        return {
            "id": r.get("id"),
            "student_id": r.get("student_id"),
            "student_name": name_map.get(r.get("student_id"), "Estudante"),
            "date": r.get("date"),
            "intervention_type": r.get("intervention_type"),
            "duration_minutes": r.get("duration_minutes"),
            "intervention_notes": r.get("intervention_notes"),
            "outcome": r.get("outcome"),
            "outcome_notes": r.get("outcome_notes"),
            "follow_up_required": r.get("follow_up_required", 0),
            "follow_up_date": r.get("follow_up_date"),
            "follow_up_completed": r.get("follow_up_completed", 0),
            "is_confidential": r.get("is_confidential", 0),
            "tags": r.get("tags"),
        }

    def criar_intervencao(
        self,
        student_id: int,
        date: str,
        intervention_type: str = "counseling",
        duration_minutes: Optional[int] = None,
        intervention_notes: str = "",
        outcome: str = "pending",
        outcome_notes: str = "",
        follow_up_required: bool = False,
        follow_up_date: Optional[str] = None,
        follow_up_completed: bool = False,
        is_confidential: bool = False,
        tags: Optional[list] = None,
        conducted_by_id: Optional[int] = None,
    ) -> int:
        query = """
            INSERT INTO desktop_intervention (
                student_id, conducted_by_id, date, intervention_type,
                duration_minutes, intervention_notes, outcome, outcome_notes,
                follow_up_required, follow_up_date, follow_up_completed,
                is_confidential, tags, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (
            student_id,
            conducted_by_id,
            date,
            intervention_type,
            duration_minutes,
            intervention_notes,
            outcome,
            outcome_notes,
            int(follow_up_required),
            follow_up_date,
            int(follow_up_completed),
            int(is_confidential),
            json.dumps(tags) if tags else "[]",
        )
        intervention_data = {
            "student_id": student_id,
            "conducted_by_id": conducted_by_id,
            "date": date,
            "intervention_type": intervention_type,
            "duration_minutes": duration_minutes,
            "intervention_notes": intervention_notes,
            "outcome": outcome,
            "outcome_notes": outcome_notes,
            "follow_up_required": int(follow_up_required),
            "follow_up_date": follow_up_date,
            "follow_up_completed": int(follow_up_completed),
            "is_confidential": int(is_confidential),
            "tags": json.dumps(tags) if tags else "[]",
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            lid = generate_local_id(mysql_result)
            intervention_data["id"] = lid
            local_cache.upsert_intervention(intervention_data)
            return lid

        def _queue_data(mysql_result, entity_id):
            lid = generate_local_id(mysql_result)
            intervention_data["id"] = lid
            return intervention_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="interventions", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def atualizar_intervencao(
        self,
        id_intervencao: int,
        student_id: Optional[int] = None,
        date: Optional[str] = None,
        intervention_type: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        intervention_notes: Optional[str] = None,
        outcome: Optional[str] = None,
        outcome_notes: Optional[str] = None,
        follow_up_required: Optional[bool] = None,
        follow_up_date: Optional[str] = None,
        follow_up_completed: Optional[bool] = None,
        is_confidential: Optional[bool] = None,
        tags: Optional[list] = None,
    ) -> int:
        campos = {}
        if student_id is not None:
            campos["student_id"] = student_id
        if date is not None:
            campos["date"] = date
        if intervention_type is not None:
            campos["intervention_type"] = intervention_type
        if duration_minutes is not None:
            campos["duration_minutes"] = duration_minutes
        if intervention_notes is not None:
            campos["intervention_notes"] = intervention_notes
        if outcome is not None:
            campos["outcome"] = outcome
        if outcome_notes is not None:
            campos["outcome_notes"] = outcome_notes
        if follow_up_required is not None:
            campos["follow_up_required"] = int(follow_up_required)
        if follow_up_date is not None:
            campos["follow_up_date"] = follow_up_date
        if follow_up_completed is not None:
            campos["follow_up_completed"] = int(follow_up_completed)
        if is_confidential is not None:
            campos["is_confidential"] = int(is_confidential)
        if tags is not None:
            campos["tags"] = json.dumps(tags)

        if not campos:
            return 0

        set_clause = ", ".join(f"{k} = %s" for k in campos.keys())
        params = list(campos.values()) + [id_intervencao]
        query = f"UPDATE desktop_intervention SET {set_clause} WHERE id = %s"

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.update("interventions", campos, "id", id_intervencao)
            return 1

        def _queue_data(mysql_result, entity_id):
            data = dict(campos)
            data["id"] = id_intervencao
            return data

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="interventions", entity_id=id_intervencao,
            queue_data_fn=_queue_data,
        )

    def deletar_intervencao(self, id_intervencao: int) -> int:
        query = "DELETE FROM desktop_intervention WHERE id = %s"

        def _mysql():
            execute_non_query(query, (id_intervencao,))
            return 1

        def _local(mysql_result):
            local_cache.delete("interventions", "id", id_intervencao)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="interventions", entity_id=id_intervencao,
            queue_data_fn=lambda r, eid: {"id": id_intervencao},
        )

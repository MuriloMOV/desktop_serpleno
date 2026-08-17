# -*- coding: utf-8 -*-
"""Repositorio de metas."""

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
from ser_pleno.infrastructure.local.local_cache import validate_table_name


class MetaRepository:
    @with_local_fallback("_local_listar_metas")
    def listar_metas(self, student_id=None, status=None, category=None, priority=None):
        """Lista metas com filtros opcionais."""
        query = """
            SELECT g.*, a.nome as student_name
            FROM desktop_goal g
            LEFT JOIN aluno a ON g.student_id = a.id_aluno
            WHERE 1=1
        """
        params = []

        if student_id is not None:
            query += " AND g.student_id = %s"
            params.append(student_id)
        if status:
            query += " AND g.status = %s"
            params.append(status)
        if category:
            query += " AND g.category = %s"
            params.append(category)
        if priority:
            query += " AND g.priority = %s"
            params.append(priority)

        query += " ORDER BY g.target_date ASC, g.created_at DESC"
        return fetch_all(query, params)

    def _local_listar_metas(self, student_id=None, status=None, category=None, priority=None):
        rows = local_cache.list_goals(
            student_id=student_id,
            status=status,
            category=category,
            priority=priority,
        )
        resultado = []
        name_map = local_cache.get_student_name_map()
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "student_id": r.get("student_id"),
                "student_name": name_map.get(r.get("student_id"), "Estudante"),
                "title": r.get("title"),
                "description": r.get("description"),
                "category": r.get("category"),
                "priority": r.get("priority"),
                "status": r.get("status"),
                "target_date": r.get("target_date"),
                "completed_date": r.get("completed_date"),
                "progress_percentage": r.get("progress_percentage", 0),
                "notes": r.get("notes"),
                "success_criteria": r.get("success_criteria"),
                "created_by_id": r.get("created_by_id"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
            })
        return resultado

    @with_local_fallback("_local_obter_meta")
    def obter_meta(self, id_meta):
        """Obtém uma meta especifica pelo ID."""
        query = """
            SELECT g.*, a.nome as student_name
            FROM desktop_goal g
            LEFT JOIN aluno a ON g.student_id = a.id_aluno
            WHERE g.id = %s
        """
        return fetch_one(query, (id_meta,))

    def _local_obter_meta(self, id_meta):
        validate_table_name("goals")
        rows = local_cache.list_all("goals", where_clause="id=?", params=(id_meta,))
        if not rows:
            return None
        r = rows[0]
        name_map = local_cache.get_student_name_map()
        return {
            "id": r.get("id"),
            "student_id": r.get("student_id"),
            "student_name": name_map.get(r.get("student_id"), "Estudante"),
            "title": r.get("title"),
            "description": r.get("description"),
            "category": r.get("category"),
            "priority": r.get("priority"),
            "status": r.get("status"),
            "target_date": r.get("target_date"),
            "completed_date": r.get("completed_date"),
            "progress_percentage": r.get("progress_percentage", 0),
            "notes": r.get("notes"),
            "success_criteria": r.get("success_criteria"),
            "created_by_id": r.get("created_by_id"),
            "created_at": r.get("created_at"),
            "updated_at": r.get("updated_at"),
        }

    @with_local_fallback("_local_listar_progresso")
    def listar_progresso(self, id_meta):
        """Lista o historico de progresso de uma meta."""
        query = """
            SELECT gp.*, u.first_name as recorded_by_name
            FROM desktop_goalprogress gp
            LEFT JOIN auth_user u ON gp.recorded_by_id = u.id
            WHERE gp.goal_id = %s
            ORDER BY gp.recorded_at DESC
        """
        return fetch_all(query, (id_meta,))

    def _local_listar_progresso(self, id_meta):
        rows = local_cache.list_goal_progress(id_meta)
        resultado = []
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "goal_id": r.get("goal_id"),
                "percentage": r.get("percentage"),
                "notes": r.get("notes"),
                "recorded_at": r.get("recorded_at"),
                "recorded_by_id": r.get("recorded_by_id"),
                "recorded_by_name": "",
            })
        return resultado

    @with_local_fallback("_local_listar_metas_atrasadas")
    def listar_metas_atrasadas(self):
        """Lista metas atrasadas (nao concluidas e com prazo vencido)."""
        query = """
            SELECT g.*, a.nome as student_name
            FROM desktop_goal g
            LEFT JOIN aluno a ON g.student_id = a.id_aluno
            WHERE g.status != 'completed'
              AND g.target_date IS NOT NULL
              AND g.target_date < CURDATE()
            ORDER BY g.target_date ASC
        """
        return fetch_all(query)

    def _local_listar_metas_atrasadas(self):
        rows = local_cache.list_overdue_goals()
        name_map = local_cache.get_student_name_map()
        resultado = []
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "student_id": r.get("student_id"),
                "student_name": name_map.get(r.get("student_id"), "Estudante"),
                "title": r.get("title"),
                "category": r.get("category"),
                "priority": r.get("priority"),
                "status": r.get("status"),
                "target_date": r.get("target_date"),
                "progress_percentage": r.get("progress_percentage", 0),
            })
        return resultado

    @with_local_fallback("_local_obter_estatisticas")
    def obter_estatisticas(self):
        """Obtém estatísticas das metas."""
        total = fetch_one("SELECT COUNT(*) as total FROM desktop_goal")
        by_status = fetch_all("""
            SELECT status, COUNT(*) as count
            FROM desktop_goal
            GROUP BY status
            ORDER BY count DESC
        """)
        by_category = fetch_all("""
            SELECT category, COUNT(*) as count
            FROM desktop_goal
            GROUP BY category
            ORDER BY count DESC
        """)
        by_priority = fetch_all("""
            SELECT priority, COUNT(*) as count
            FROM desktop_goal
            GROUP BY priority
            ORDER BY count DESC
        """)
        overdue = fetch_one("""
            SELECT COUNT(*) as total
            FROM desktop_goal
            WHERE status != 'completed'
              AND target_date IS NOT NULL
              AND target_date < CURDATE()
        """)

        return {
            "total": total.get("total") if total else 0,
            "by_status": [
                {"status": r["status"] or "Sem status", "count": r["count"]}
                for r in by_status
            ],
            "by_category": [
                {"category": r["category"] or "Sem categoria", "count": r["count"]}
                for r in by_category
            ],
            "by_priority": [
                {"priority": r["priority"] or "Sem prioridade", "count": r["count"]}
                for r in by_priority
            ],
            "overdue": overdue.get("total") if overdue else 0,
        }

    def _local_obter_estatisticas(self):
        validate_table_name("goals")
        rows = local_cache.list_all("goals")
        total = len(rows)
        by_status: dict = {}
        by_category: dict = {}
        by_priority: dict = {}
        overdue = 0
        today = datetime.now().strftime("%Y-%m-%d")

        for r in rows:
            status = r.get("status") or "Sem status"
            by_status[status] = by_status.get(status, 0) + 1
            category = r.get("category") or "Sem categoria"
            by_category[category] = by_category.get(category, 0) + 1
            priority = r.get("priority") or "Sem prioridade"
            by_priority[priority] = by_priority.get(priority, 0) + 1
            if r.get("status") != "completed" and r.get("target_date") and r.get("target_date") < today:
                overdue += 1

        return {
            "total": total,
            "by_status": [{"status": k, "count": v} for k, v in sorted(by_status.items(), key=lambda x: x[1], reverse=True)],
            "by_category": [{"category": k, "count": v} for k, v in sorted(by_category.items(), key=lambda x: x[1], reverse=True)],
            "by_priority": [{"priority": k, "count": v} for k, v in sorted(by_priority.items(), key=lambda x: x[1], reverse=True)],
            "overdue": overdue,
        }

    def criar_meta(self, student_id, title, category, priority, target_date=None,
                   description="", notes="", success_criteria="", created_by_id=None, status="not_started", progress_percentage=0):
        """Cria uma nova meta."""
        query = """
            INSERT INTO desktop_goal (
                student_id, title, description, category, priority, status,
                target_date, completed_date, progress_percentage, notes,
                success_criteria, created_by_id, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (
            student_id, title, description, category, priority, status,
            target_date, progress_percentage, notes, success_criteria, created_by_id
        )
        goal_data = {
            "student_id": student_id,
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "status": status,
            "target_date": target_date,
            "progress_percentage": progress_percentage,
            "notes": notes,
            "success_criteria": success_criteria,
            "created_by_id": created_by_id,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            goal_data["id"] = last_id
            local_cache.upsert_goal(goal_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            goal_data["id"] = last_id
            return goal_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="goals", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def atualizar_meta(self, id_meta, **dados):
        """Atualiza uma meta existente."""
        campos_permitidos = {
            "title", "description", "category", "priority", "status",
            "target_date", "completed_date", "progress_percentage",
            "notes", "success_criteria", "student_id",
        }
        invalidos = set(dados) - campos_permitidos
        if invalidos:
            raise ValueError(f"Campos nao permitidos: {sorted(invalidos)}")

        if not dados:
            return 0

        set_clause = ", ".join(f"{k} = %s" for k in dados)
        params = list(dados.values()) + [id_meta]
        query = f"UPDATE desktop_goal SET {set_clause}, updated_at = NOW() WHERE id = %s"

        goal_data = {k: v for k, v in dados.items()}
        goal_data["id"] = id_meta

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.upsert_goal(goal_data)
            return 1

        def _queue_data(mysql_result, entity_id):
            return goal_data

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="goals", entity_id=id_meta,
            queue_data_fn=_queue_data,
        )

    def deletar_meta(self, id_meta):
        """Deleta uma meta pelo ID."""
        query = "DELETE FROM desktop_goal WHERE id = %s"

        def _mysql():
            execute_non_query(query, (id_meta,))
            return 1

        def _local(mysql_result):
            local_cache.delete_goal(id_meta)
            local_cache.delete_goal_progress(id_meta)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="goals", entity_id=id_meta,
            queue_data_fn=lambda r, eid: {"id": id_meta},
        )

    def registrar_progresso(self, id_meta, percentage, notes, recorded_by_id):
        """Registra um novo progresso para a meta e atualiza a porcentagem."""
        query = """
            INSERT INTO desktop_goalprogress (
                goal_id, percentage, notes, recorded_by_id, recorded_at
            ) VALUES (%s, %s, %s, %s, NOW())
        """
        params = (id_meta, percentage, notes, recorded_by_id)
        progress_data = {
            "goal_id": id_meta,
            "percentage": percentage,
            "notes": notes,
            "recorded_by_id": recorded_by_id,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            progress_data["id"] = last_id
            local_cache.upsert_goal_progress(progress_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            progress_data["id"] = last_id
            return progress_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="goal_progress", entity_id="novo",
            queue_data_fn=_queue_data,
        )

        self.atualizar_meta(id_meta, progress_percentage=percentage)

        return last_id

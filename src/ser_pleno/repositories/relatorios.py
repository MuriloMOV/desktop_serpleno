# -*- coding: utf-8 -*-
"""Repositorio de relatorios."""

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


class RelatorioRepository:
    @with_local_fallback("_local_listar_relatorios")
    def listar_relatorios(self, tipo=None, data_inicio=None, pagina=1, search=None, data_fim=None):
        query = "SELECT * FROM desktop_report WHERE 1=1"
        params = []

        if tipo:
            query += " AND report_type = %s"
            params.append(tipo)
        if data_inicio:
            query += " AND generated_at >= %s"
            params.append(data_inicio)
        if data_fim:
            query += " AND generated_at <= %s"
            params.append(data_fim)
        if search:
            query += " AND name LIKE %s"
            params.append(f"%{search}%")

        offset = (pagina - 1) * 10
        query += " ORDER BY generated_at DESC LIMIT 10 OFFSET %s"
        params.append(offset)

        return fetch_all(query, params)

    def _local_listar_relatorios(self, tipo=None, data_inicio=None, pagina=1, search=None, data_fim=None):
        rows = local_cache.list_reports()
        if tipo:
            rows = [r for r in rows if r.get("report_type") == tipo]
        if data_inicio:
            rows = [r for r in rows if (r.get("generated_at") or "") >= data_inicio]
        if data_fim:
            rows = [r for r in rows if (r.get("generated_at") or "") <= data_fim]
        if search:
            search_lower = search.lower()
            rows = [r for r in rows if search_lower in (r.get("name") or "").lower()]
        offset = (pagina - 1) * 10
        return rows[offset:offset + 10]

    @with_local_fallback("_local_listar_relatorios_filtrados")
    def listar_relatorios_filtrados(self, tipo=None, data_inicio=None, data_fim=None, search=None, pagina=1):
        query = "SELECT * FROM desktop_report WHERE 1=1"
        params = []

        if tipo:
            query += " AND report_type = %s"
            params.append(tipo)
        if data_inicio:
            query += " AND generated_at >= %s"
            params.append(data_inicio)
        if data_fim:
            query += " AND generated_at <= %s"
            params.append(data_fim)
        if search:
            query += " AND name LIKE %s"
            params.append(f"%{search}%")

        query += " ORDER BY generated_at DESC"
        return fetch_all(query, params)

    def _local_listar_relatorios_filtrados(self, tipo=None, data_inicio=None, data_fim=None, search=None, pagina=1):
        rows = local_cache.list_reports()
        if tipo:
            rows = [r for r in rows if r.get("report_type") == tipo]
        if data_inicio:
            rows = [r for r in rows if (r.get("generated_at") or "") >= data_inicio]
        if data_fim:
            rows = [r for r in rows if (r.get("generated_at") or "") <= data_fim]
        if search:
            search_lower = search.lower()
            rows = [r for r in rows if search_lower in (r.get("name") or "").lower()]
        return rows

    @with_local_fallback("_local_obter_estatisticas")
    def obter_estatisticas(self):
        """Obtem estatisticas basicas do sistema."""
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

    def _local_obter_estatisticas(self):
        students = local_cache.list_students()
        appointments = local_cache.list_all("appointments")
        screenings = local_cache.list_screenings()
        active_appointments = sum(1 for a in appointments if a.get("status") == "completed")
        pending_screenings = sum(1 for s in screenings if s.get("status") == "pending")
        return {
            "total_students": len(students),
            "active_appointments": active_appointments,
            "pending_screenings": pending_screenings,
            "average_score": 0,
        }

    def criar_relatorio(self, name, report_type, format, parameters, data, file_path, file_size, is_public, expires_at, generated_by_id):
        """Cria um novo relatorio."""
        query = """
            INSERT INTO desktop_report (
                name, report_type, format, generated_at, parameters, data,
                file_path, file_size, is_public, expires_at, generated_by_id
            ) VALUES (%s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            name, report_type, format, parameters, data,
            file_path, file_size, is_public, expires_at, generated_by_id
        )
        report_data = {
            "name": name,
            "report_type": report_type,
            "format": format,
            "generated_at": datetime.now().isoformat(),
            "parameters": parameters,
            "data": data,
            "file_path": file_path,
            "file_size": file_size,
            "is_public": int(is_public),
            "expires_at": str(expires_at) if expires_at else None,
            "generated_by_id": generated_by_id,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            report_data["id"] = last_id
            local_cache.upsert_report(report_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            report_data["id"] = last_id
            return report_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="reports", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    @with_local_fallback("_local_obter_relatorio_por_id")
    def obter_relatorio_por_id(self, id_relatorio):
        """Obtem um relatorio pelo ID."""
        query = "SELECT file_path, file_name FROM desktop_report WHERE id = %s"
        return fetch_one(query, (id_relatorio,))

    def _local_obter_relatorio_por_id(self, id_relatorio):
        rows = local_cache.list_all("reports", where_clause="id=?", params=(id_relatorio,))
        if rows:
            r = rows[0]
            return {"file_path": r.get("file_path"), "file_name": r.get("name")}
        return None

    def deletar_relatorio(self, id_relatorio):
        """Deleta um relatorio pelo ID."""
        query = "DELETE FROM desktop_report WHERE id = %s"

        def _mysql():
            execute_non_query(query, (id_relatorio,))
            return 1

        def _local(mysql_result):
            local_cache.delete("reports", "id", id_relatorio)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="reports", entity_id=id_relatorio,
            queue_data_fn=lambda r, eid: {"id": id_relatorio},
        )

    @with_local_fallback("_local_exportar_estudantes")
    def exportar_estudantes(self):
        """Exporta todos os estudantes."""
        query = "SELECT * FROM aluno ORDER BY nome ASC"
        return fetch_all(query)

    def _local_exportar_estudantes(self):
        return local_cache.list_students()

    @with_local_fallback("_local_exportar_agendamentos")
    def exportar_agendamentos(self):
        """Exporta todos os agendamentos."""
        query = "SELECT * FROM agendamento ORDER BY data_hora DESC"
        return fetch_all(query)

    def _local_exportar_agendamentos(self):
        return local_cache.list_all("appointments")

    @with_local_fallback("_local_exportar_triagens")
    def exportar_triagens(self):
        """Exporta todas as triagens."""
        query = "SELECT * FROM desktop_screening ORDER BY created_at DESC"
        return fetch_all(query)

    def _local_exportar_triagens(self):
        return local_cache.list_screenings()

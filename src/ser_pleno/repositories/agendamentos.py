# -*- coding: utf-8 -*-
"""Repositorio de agendamentos."""

from datetime import date, datetime, time, timedelta

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


class AgendamentoRepository:
    @with_local_fallback("_local_listar_proximos")
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

    def _local_listar_proximos(self, limite=5):
        rows = local_cache.list_all(
            "appointments",
            where_clause="status != ?",
            params=("cancelled",),
        )
        name_map = local_cache.get_student_name_map()
        resultado = []
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "data_hora": r.get("data_hora"),
                "status": r.get("status"),
                "student_name": name_map.get(r.get("student_id"), "Estudante"),
                "curso": "Curso nao informado",
            })
        resultado.sort(key=lambda x: x.get("data_hora") or "")
        return resultado[:limite]

    @with_local_fallback("_local_contar_por_status")
    def contar_por_status(self, status):
        query = "SELECT COUNT(*) as total FROM agendamento WHERE status = %s"
        return fetch_one(query, (status,))

    def _local_contar_por_status(self, status):
        rows = local_cache.list_all(
            "appointments",
            where_clause="status=?",
            params=(status,),
        )
        return {"total": len(rows)}

    @with_local_fallback("_local_contar_hoje")
    def contar_hoje(self):
        query = "SELECT COUNT(*) as total FROM agendamento WHERE DATE(data_hora) = CURDATE()"
        return fetch_one(query)

    def _local_contar_hoje(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        rows = local_cache.list_appointments(data=hoje)
        return {"total": len(rows)}

    @with_local_fallback("_local_contar_hoje_ativos")
    def contar_hoje_ativos(self):
        query = "SELECT COUNT(*) as total FROM agendamento WHERE DATE(data_hora) = CURDATE() AND status != 'canceled'"
        return fetch_one(query)

    def _local_contar_hoje_ativos(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        rows = local_cache.list_appointments(data=hoje)
        ativos = [r for r in rows if r.get("status") != "canceled"]
        return {"total": len(ativos)}

    @with_local_fallback("_local_total_disponibilidade")
    def total_disponibilidade(self):
        query = "SELECT COUNT(*) as total FROM disponibilidade WHERE is_active = 1"
        return fetch_one(query)

    def _local_total_disponibilidade(self):
        # Disponibilidade nao esta no LocalCache; retorna 0 como fallback seguro
        return {"total": 0}

    @with_local_fallback("_local_listar_horarios_base")
    def listar_horarios_base(self):
        """Retorna os horarios base ativos da grade."""
        query = "SELECT Horario FROM disponibilidade WHERE is_active = 1 ORDER BY Horario"
        rows = fetch_all(query)
        horarios = []
        for row in rows:
            horario = row.get("Horario") if isinstance(row, dict) else row[0]
            if hasattr(horario, "strftime"):
                horarios.append(horario.strftime("%H:%M"))
            else:
                horario_str = str(horario)
                horarios.append(horario_str[:5] if len(horario_str) > 5 else horario_str)
        return horarios

    def _local_listar_horarios_base(self):
        # Horarios base nao sao sincronizados; retorna lista vazia
        return []

    @with_local_fallback("_local_taxa_presenca_ultimos_30_dias")
    def taxa_presenca_ultimos_30_dias(self):
        query = """
            SELECT COUNT(*) as total, SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM agendamento WHERE DATE(data_hora) >= CURDATE() - INTERVAL 30 DAY
        """
        return fetch_one(query)

    def _local_taxa_presenca_ultimos_30_dias(self):
        rows = local_cache.list_all("appointments")
        total = len(rows)
        completed = sum(1 for r in rows if r.get("status") == "completed")
        return {"total": total, "completed": completed}

    @with_local_fallback("_local_verificar_disponibilidade")
    def verificar_disponibilidade(self, data, time_str):
        """Verifica se um horario esta disponivel."""
        data_hora_str = f"{data} {time_str}"
        data_hora = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
        query = """
            SELECT id FROM agendamento
            WHERE data_hora BETWEEN %s AND %s
        """
        return fetch_one(query, (data_hora, data_hora + timedelta(minutes=59)))

    def _local_verificar_disponibilidade(self, data, time_str):
        data_hora_str = f"{data} {time_str}:00"
        rows = local_cache.list_all(
            "appointments",
            where_clause="data_hora=?",
            params=(data_hora_str,),
        )
        return rows[0] if rows else None

    @with_local_fallback("_local_obter_nome_aluno")
    def obter_nome_aluno(self, id_aluno):
        """Obtem o nome do aluno pelo ID."""
        query = "SELECT nome FROM aluno WHERE id_aluno = %s"
        return fetch_one(query, (id_aluno,))

    def _local_obter_nome_aluno(self, id_aluno):
        rows = local_cache.list_all("students", where_clause="id=?", params=(id_aluno,))
        if rows:
            return {"nome": rows[0].get("nome")}
        return None

    @with_local_fallback("_local_obter_time_id")
    def obter_time_id(self, hora_str):
        """Obtem o ID do horario na tabela disponibilidade."""
        time_obj = datetime.strptime(hora_str, "%H:%M").time()
        query = "SELECT id_disponibilidade FROM disponibilidade WHERE Horario = %s"
        return fetch_one(query, (time_obj,))

    def _local_obter_time_id(self, hora_str):
        # Disponibilidade nao e sincronizada no cache local
        return None

    @with_local_fallback("_local_obter_agendamento_para_sincronizacao")
    def obter_agendamento_para_sincronizacao(self, appointment_id):
        """Obtem os dados de um agendamento para sincronizacao com a API."""
        query = """
            SELECT a.id, a.student_id, a.data_hora, a.motivo, a.status, a.local, a.profissional, a.laudo, a.origem,
                   al.nome as nome_aluno
            FROM agendamento a
            INNER JOIN aluno al ON a.student_id = al.id_aluno
            WHERE a.id = %s
        """
        return fetch_one(query, (appointment_id,))

    def _local_obter_agendamento_para_sincronizacao(self, appointment_id):
        rows = local_cache.list_all("appointments", where_clause="id=?", params=(appointment_id,))
        if rows:
            r = rows[0]
            name_map = local_cache.get_student_name_map()
            return {
                "id": r.get("id"),
                "student_id": r.get("student_id"),
                "data_hora": r.get("data_hora"),
                "motivo": r.get("motivo"),
                "status": r.get("status"),
                "local": r.get("local"),
                "profissional": r.get("profissional"),
                "laudo": r.get("laudo"),
                "origem": r.get("origem"),
                "nome_aluno": name_map.get(r.get("student_id"), "Estudante"),
            }
        return None

    def criar_agendamento(self, id_aluno, data_hora, nome_agendamento, motivo, status, local, profissional, laudo, origem):
        """Cria um novo agendamento."""
        query = """
            INSERT INTO agendamento (student_id, data_hora, nome, motivo, status, local, profissional, laudo, origem)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            id_aluno, data_hora, nome_agendamento, motivo, status, local, profissional, laudo, origem
        )
        appointment_data = {
            "student_id": id_aluno,
            "data_hora": str(data_hora),
            "motivo": motivo,
            "status": status,
            "local": local,
            "profissional": profissional,
            "laudo": laudo,
            "origem": origem,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            appointment_data["id"] = last_id
            local_cache.upsert_appointment(appointment_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            appointment_data["id"] = last_id
            return appointment_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="appointments", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    @with_local_fallback("_local_listar_agendamentos")
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

    def _local_listar_agendamentos(self, data=None):
        rows = local_cache.list_appointments(data=data)
        name_map = local_cache.get_student_name_map()
        resultado = []
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "nome": name_map.get(r.get("student_id"), "Estudante"),
                "id_aluno": r.get("student_id"),
                "data_hora": r.get("data_hora"),
                "motivo": r.get("motivo"),
                "status": r.get("status"),
                "local": r.get("local"),
                "profissional": r.get("profissional"),
                "laudo": r.get("laudo"),
                "origem": r.get("origem"),
            })
        return resultado

    def atualizar_agendamento(self, id_agendamento, id_aluno, data_hora, motivo, status, local, profissional, laudo, origem):
        """Atualiza um agendamento existente."""
        query = """
            UPDATE agendamento
            SET student_id = %s, data_hora = %s, motivo = %s, status = %s, local = %s, profissional = %s, laudo = %s, origem = %s
            WHERE id = %s
        """
        params = (
            id_aluno, data_hora, motivo, status, local, profissional, laudo, origem, id_agendamento
        )
        appointment_data = {
            "id": id_agendamento,
            "student_id": id_aluno,
            "data_hora": str(data_hora),
            "motivo": motivo,
            "status": status,
            "local": local,
            "profissional": profissional,
            "laudo": laudo,
            "origem": origem,
        }

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.upsert_appointment(appointment_data)
            return 1

        def _queue_data(mysql_result, entity_id):
            return appointment_data

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="appointments", entity_id=id_agendamento,
            queue_data_fn=_queue_data,
        )

    def deletar_agendamento(self, id_agendamento):
        """Deleta um agendamento pelo ID."""
        query = "DELETE FROM agendamento WHERE id = %s"

        def _mysql():
            execute_non_query(query, (id_agendamento,))
            return 1

        def _local(mysql_result):
            local_cache.delete("appointments", "id", id_agendamento)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="appointments", entity_id=id_agendamento,
            queue_data_fn=lambda r, eid: {"id": id_agendamento},
        )

    def adicionar_horario_disponibilidade(self, horario):
        """Adiciona um novo horario na tabela de disponibilidade."""
        time_obj = datetime.strptime(horario, "%H:%M").time()
        query = """
            INSERT INTO disponibilidade (Horario, is_active, Dias)
            VALUES (%s, 1, 'segunda-terca-quarta-quinta-sexta')
        """
        return execute_non_query(query, (time_obj,))

    @with_local_fallback("_local_verificar_horario_existe")
    def verificar_horario_existe(self, horario):
        """Verifica se um horario ja existe na tabela de disponibilidade."""
        time_obj = datetime.strptime(horario, "%H:%M").time()
        query = "SELECT id_disponibilidade FROM disponibilidade WHERE Horario = %s"
        return fetch_one(query, (time_obj,))

    def _local_verificar_horario_existe(self, horario):
        # Disponibilidade nao e sincronizada no cache local
        return None

    def remover_horario_disponibilidade(self, horario):
        """Remove um horario da tabela de disponibilidade."""
        time_obj = datetime.strptime(horario, "%H:%M").time()
        # Verifica se ha agendamentos usando este horario
        query_uso = "SELECT id FROM agendamento WHERE TIME(data_hora) = %s"
        uso = fetch_one(query_uso, (time_obj,))
        if uso:
            return {"success": False, "message": "Nao e possivel remover horario com agendamentos associados"}

        # Remove o horario
        query_delete = "DELETE FROM disponibilidade WHERE Horario = %s"
        return execute_non_query(query_delete, (time_obj,))

    def obter_ultimo_id_inserido(self):
        """Obtem o ultimo ID inserido no banco de dados."""
        return fetch_one("SELECT LAST_INSERT_ID() as id", ()).get("id")

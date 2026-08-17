# -*- coding: utf-8 -*-
"""Repositorio de compartilhamento de dados clínicos."""

from typing import Any, Dict, List, Optional

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
    generate_local_id,
)


class CompartilhamentoDadosRepository:
    """Repositorio para gerenciar compartilhamento de dados clínicos."""

    @with_local_fallback("_local_listar")
    def listar(
        self,
        busca: Optional[str] = None,
        data_type: Optional[str] = None,
        student_id: Optional[int] = None,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Lista compartilhamentos com filtros opcionais."""
        query = (
            "SELECT scd.*, "
            "a.nome AS student_name, "
            "u1.username AS shared_by_name, "
            "u2.username AS shared_with_user_name "
            "FROM shared_clinical_data scd "
            "JOIN aluno a ON scd.student_id = a.id_aluno "
            "LEFT JOIN auth_user u1 ON scd.shared_by_id = u1.id "
            "LEFT JOIN auth_user u2 ON scd.shared_with_user_id = u2.id "
            "WHERE 1=1"
        )
        params = []

        if busca:
            query += " AND (a.nome LIKE %s OR u2.username LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%"])
        if data_type:
            query += " AND scd.data_type = %s"
            params.append(data_type)
        if student_id:
            query += " AND scd.student_id = %s"
            params.append(student_id)

        query += " ORDER BY scd.created_at DESC"
        return fetch_all(query, params)

    def _local_listar(
        self,
        busca: Optional[str] = None,
        data_type: Optional[str] = None,
        student_id: Optional[int] = None,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """Fallback para listar compartilhamentos do cache local."""
        try:
            rows = local_cache.list_shared_data(
                busca=busca, data_type=data_type, student_id=student_id
            )
            resultado = []
            for r in rows:
                item = {
                    "id": r.get("id"),
                    "student_id": r.get("student_id"),
                    "student_name": r.get("student_name", ""),
                    "shared_by_id": r.get("shared_by_id"),
                    "shared_by_name": r.get("shared_by_name", ""),
                    "shared_with_user_id": r.get("shared_with_user_id"),
                    "shared_with_user_name": r.get("shared_with_user_name", ""),
                    "shared_with_role": r.get("shared_with_role", ""),
                    "data_type": r.get("data_type", ""),
                    "created_at": r.get("created_at", ""),
                }
                if data_type and item["data_type"] != data_type:
                    continue
                if student_id and item["student_id"] != student_id:
                    continue
                if busca:
                    termo = busca.lower()
                    if termo not in item.get("student_name", "").lower():
                        continue
                resultado.append(item)
            return resultado
        except Exception:
            return []

    @with_local_fallback("_local_compartilhar")
    def compartilhar(
        self,
        student_id: int,
        shared_with_user_id: int,
        shared_with_role: str,
        data_type: str,
        shared_by_id: int,
    ) -> Optional[int]:
        """Compartilha dados clínicos com outro usuário."""
        query = (
            "INSERT INTO shared_clinical_data "
            "(student_id, shared_by_id, shared_with_user_id, shared_with_role, data_type, created_at) "
            "VALUES (%s, %s, %s, %s, %s, NOW())"
        )
        params = (student_id, shared_by_id, shared_with_user_id, shared_with_role, data_type)
        shared_data = {
            "student_id": student_id,
            "shared_by_id": shared_by_id,
            "shared_with_user_id": shared_with_user_id,
            "shared_with_role": shared_with_role,
            "data_type": data_type,
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            shared_data["id"] = last_id
            local_cache.upsert_shared_data(shared_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            shared_data["id"] = last_id
            return shared_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="shared_clinical_data", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def _local_compartilhar(
        self,
        student_id: int,
        shared_with_user_id: int,
        shared_with_role: str,
        data_type: str,
        shared_by_id: int,
    ) -> Optional[int]:
        shared_data = {
            "student_id": student_id,
            "shared_by_id": shared_by_id,
            "shared_with_user_id": shared_with_user_id,
            "shared_with_role": shared_with_role,
            "data_type": data_type,
        }
        rows = local_cache.list_all("shared_clinical_data")
        max_id = 0
        for r in rows:
            if r.get("id") and r["id"] > max_id:
                max_id = r["id"]
        last_id = max_id + 1 if max_id >= 0 else -1
        shared_data["id"] = last_id
        local_cache.upsert_shared_data(shared_data)
        return last_id

    @with_local_fallback("_local_descompartilhar")
    def descompartilhar(
        self,
        student_id: int,
        shared_with_user_id: int,
        data_type: str,
    ) -> Optional[int]:
        """Descompartilha dados clínicos."""
        query = (
            "DELETE FROM shared_clinical_data "
            "WHERE student_id = %s AND shared_with_user_id = %s AND data_type = %s"
        )
        params = (student_id, shared_with_user_id, data_type)

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            local_cache.delete("shared_clinical_data", "student_id", student_id)
            local_cache.delete("shared_clinical_data", "shared_with_user_id", shared_with_user_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="shared_clinical_data", entity_id=student_id,
            queue_data_fn=lambda r, eid: {"student_id": student_id, "shared_with_user_id": shared_with_user_id, "data_type": data_type},
        )

    def _local_descompartilhar(
        self,
        student_id: int,
        shared_with_user_id: int,
        data_type: str,
    ) -> Optional[int]:
        rows = local_cache.list_all(
            "shared_clinical_data",
            where_clause="student_id=? AND shared_with_user_id=? AND data_type=?",
            params=(student_id, shared_with_user_id, data_type),
        )
        for r in rows:
            local_cache.delete("shared_clinical_data", "id", r.get("id"))
        return len(rows)

    def listar_estudantes_compartilhados(self) -> List[Dict[str, Any]]:
        """Lista estudantes compartilhados com o usuário atual."""
        query = (
            "SELECT DISTINCT scd.student_id, a.nome AS student_name, a.curso AS course, "
            "GROUP_CONCAT(scd.data_type SEPARATOR ',') AS shared_data_types "
            "FROM shared_clinical_data scd "
            "JOIN aluno a ON scd.student_id = a.id_aluno "
            "GROUP BY scd.student_id, a.nome, a.curso"
        )
        return fetch_all(query)

    def _local_listar_estudantes_compartilhados(self) -> List[Dict[str, Any]]:
        """Fallback para listar estudantes compartilhados do cache local."""
        try:
            rows = local_cache.list_all("shared_clinical_data")
            seen = {}
            for r in rows:
                sid = r.get("student_id")
                if sid not in seen:
                    seen[sid] = {
                        "student_id": sid,
                        "student_name": r.get("student_name", ""),
                        "course": r.get("course", ""),
                        "shared_data_types": [],
                    }
                dt = r.get("data_type", "")
                if dt and dt not in seen[sid]["shared_data_types"]:
                    seen[sid]["shared_data_types"].append(dt)
            return list(seen.values())
        except Exception:
            return []

    @with_local_fallback("_local_obter_historico")
    def obter_historico(self, student_id: int) -> List[Dict[str, Any]]:
        """Obtém histórico de compartilhamento por estudante."""
        query = (
            "SELECT scd.*, "
            "u1.username AS shared_by_name, "
            "u2.username AS shared_with_user_name "
            "FROM shared_clinical_data scd "
            "LEFT JOIN auth_user u1 ON scd.shared_by_id = u1.id "
            "LEFT JOIN auth_user u2 ON scd.shared_with_user_id = u2.id "
            "WHERE scd.student_id = %s "
            "ORDER BY scd.created_at DESC"
        )
        params = (student_id,)
        return fetch_all(query, params)

    def _local_obter_historico(self, student_id: int) -> List[Dict[str, Any]]:
        """Fallback para obter histórico do cache local."""
        try:
            rows = local_cache.list_all(
                "shared_clinical_data", where_clause="student_id=?", params=(student_id,)
            )
            return rows
        except Exception:
            return []

    @with_local_fallback("_local_obter_relatorio")
    def obter_relatorio(self) -> Dict[str, Any]:
        """Obtém relatório de compartilhamento."""
        query = (
            "SELECT "
            "COUNT(*) AS total_compartilhamentos, "
            "COUNT(DISTINCT student_id) AS total_estudantes, "
            "COUNT(DISTINCT shared_with_user_id) AS total_usuarios_compartilhados, "
            "data_type, "
            "COUNT(*) AS total_por_tipo "
            "FROM shared_clinical_data "
            "GROUP BY data_type"
        )
        rows = fetch_all(query)

        total_compartilhamentos = 0
        total_estudantes = set()
        total_usuarios_compartilhados = set()
        por_tipo = {}

        for r in rows:
            total_compartilhamentos += r.get("total_por_tipo", 0)
            total_estudantes.add(r.get("student_id"))
            total_usuarios_compartilhados.add(r.get("shared_with_user_id"))
            por_tipo[r.get("data_type", "")] = r.get("total_por_tipo", 0)

        return {
            "total_compartilhamentos": total_compartilhamentos,
            "total_estudantes": len(total_estudantes),
            "total_usuarios_compartilhados": len(total_usuarios_compartilhados),
            "por_tipo": por_tipo,
            "detalhes": rows,
        }

    def _local_obter_relatorio(self) -> Dict[str, Any]:
        """Fallback para obter relatório do cache local."""
        try:
            rows = local_cache.list_all("shared_clinical_data")
            total_compartilhamentos = len(rows)
            total_estudantes = set()
            total_usuarios_compartilhados = set()
            por_tipo = {}
            for r in rows:
                total_estudantes.add(r.get("student_id"))
                total_usuarios_compartilhados.add(r.get("shared_with_user_id"))
                dt = r.get("data_type", "")
                por_tipo[dt] = por_tipo.get(dt, 0) + 1
            return {
                "total_compartilhamentos": total_compartilhamentos,
                "total_estudantes": len(total_estudantes),
                "total_usuarios_compartilhados": len(total_usuarios_compartilhados),
                "por_tipo": por_tipo,
                "detalhes": rows,
            }
        except Exception:
            return {
                "total_compartilhamentos": 0,
                "total_estudantes": 0,
                "total_usuarios_compartilhados": 0,
                "por_tipo": {},
                "detalhes": [],
            }

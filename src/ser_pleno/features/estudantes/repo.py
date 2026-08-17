# -*- coding: utf-8 -*-
"""Repositorio de estudantes."""

import json
from typing import Any

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


# Whitelist de colunas que podem ser atualizadas via DML.
# Qualquer campo fora desta lista e rejeitado antes de atingir o banco.
_CAMPOS_ATUALIZAVEIS = {
    "nome",
    "curso",
    "age",
    "professor_responsavel",
    "has_medical_report",
    "requires_attention",
    "status",
    "priority_level",
    "tags",
    "avatar",
    "dark_mode",
    "notifications_enabled",
    "phone",
    "emergency_contact",
    "emergency_phone",
    "attention_reason",
    "general_notes",
}


def _shorten_avatar(value: Any) -> str:
    if not value:
        return "a"
    text = str(value)
    if "/" in text or "\\" in text:
        text = text.replace("\\", "/").split("/")[-1]
    if not text:
        text = "avatar"
    if "." in text:
        text = text.split(".")[0]
    return text[:1]


def _student_data(nome, email, has_medical_report, requires_attention, professor_responsavel='Não informado', status='ativo', priority_level=0, tags=None, avatar='/default_avatar.png', dark_mode=0, notifications_enabled=1, curso=None, age=None, phone=None, emergency_contact=None, emergency_phone=None, attention_reason=None, general_notes=None):
    data = {
        "nome": nome,
        "email": email,
        "has_medical_report": int(has_medical_report),
        "requires_attention": int(requires_attention),
        "professor_responsavel": professor_responsavel,
        "status": status,
        "priority_level": int(priority_level),
        "tags": json.dumps(tags) if tags else "[]",
        "avatar": _shorten_avatar(avatar),
        "dark_mode": int(dark_mode),
        "notifications_enabled": int(notifications_enabled),
        "curso": curso,
        "age": age,
        "phone": phone,
        "emergency_contact": emergency_contact,
        "emergency_phone": emergency_phone,
        "attention_reason": attention_reason,
        "general_notes": general_notes,
    }
    return data


class EstudanteRepository:
    @with_local_fallback("_local_listar")
    def listar(self, busca=None, possui_laudo=None, requer_atencao=None):
        query = (
            "SELECT a.*, u.email AS contact "
            "FROM aluno a "
            "LEFT JOIN auth_user u ON a.user_id = u.id "
            "WHERE 1=1"
        )
        params = []
        if busca:
            query += " AND (a.nome LIKE %s OR u.email LIKE %s)"
            params.extend([f"%{busca}%", f"%{busca}%"])
        if possui_laudo is not None:
            query += " AND a.has_medical_report = %s"
            params.append(possui_laudo)
        if requer_atencao is not None:
            query += " AND a.requires_attention = %s"
            params.append(requer_atencao)
        query += " ORDER BY a.nome ASC"
        return fetch_all(query, params)

    def _local_listar(self, busca=None, possui_laudo=None, requer_atencao=None):
        rows = local_cache.list_students(busca=busca)
        resultado = []
        for r in rows:
            item = {
                "id_aluno": r.get("id"),
                "nome": r.get("nome"),
                "email": r.get("email"),
                "has_medical_report": r.get("has_medical_report", 0),
                "requires_attention": r.get("requires_attention", 0),
                "contact": r.get("email"),
            }
            if possui_laudo is not None:
                if item["has_medical_report"] != int(possui_laudo):
                    continue
            if requer_atencao is not None:
                if item["requires_attention"] != int(requer_atencao):
                    continue
            resultado.append(item)
        return resultado

    @with_local_fallback("_local_obter")
    def obter(self, id_estudante):
        query = (
            "SELECT a.*, u.email AS contact "
            "FROM aluno a "
            "LEFT JOIN auth_user u ON a.user_id = u.id "
            "WHERE a.id_aluno = %s"
        )
        return fetch_one(query, (id_estudante,))

    def _local_obter(self, id_estudante):
        validate_table_name("students")
        rows = local_cache.list_all("students", where_clause="id=?", params=(id_estudante,))
        if not rows:
            return None
        r = rows[0]
        return {
            "id_aluno": r.get("id"),
            "nome": r.get("nome"),
            "email": r.get("email"),
            "curso": r.get("curso"),
            "age": r.get("age"),
            "phone": r.get("phone"),
            "professor_responsavel": r.get("professor_responsavel"),
            "emergency_contact": r.get("emergency_contact"),
            "emergency_phone": r.get("emergency_phone"),
            "attention_reason": r.get("attention_reason"),
            "general_notes": r.get("general_notes"),
            "has_medical_report": r.get("has_medical_report", 0),
            "requires_attention": r.get("requires_attention", 0),
            "status": r.get("status", "ativo"),
            "priority_level": r.get("priority_level", 0),
            "contact": r.get("email"),
            "minigames_blocked": r.get("minigames_blocked", 0),
            "minigame_block_reason": r.get("minigame_block_reason"),
        }

    def criar(self, nome, email, has_medical_report=False, requires_attention=False, professor_responsavel='Não informado', status='ativo', priority_level=0, tags=None, avatar='/default_avatar.png', dark_mode=0, notifications_enabled=1, curso=None, age=None, phone=None, emergency_contact=None, emergency_phone=None, attention_reason=None, general_notes=None):
        query = (
            "INSERT INTO aluno "
            "(nome, professor_responsavel, status, priority_level, tags, avatar, dark_mode, notifications_enabled, has_medical_report, requires_attention, curso, age, phone, emergency_contact, emergency_phone, attention_reason, general_notes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )
        avatar_value = _shorten_avatar(avatar)
        params = (nome, professor_responsavel, status, int(priority_level), json.dumps(tags) if tags else "[]", avatar_value, int(dark_mode), int(notifications_enabled), int(has_medical_report), int(requires_attention), curso, age, phone, emergency_contact, emergency_phone, attention_reason, general_notes)
        student_data = _student_data(
            nome, email, has_medical_report, requires_attention,
            professor_responsavel=professor_responsavel,
            status=status,
            priority_level=priority_level,
            tags=tags,
            avatar=avatar_value,
            dark_mode=dark_mode,
            notifications_enabled=notifications_enabled,
            curso=curso,
            age=age,
            phone=phone,
            emergency_contact=emergency_contact,
            emergency_phone=emergency_phone,
            attention_reason=attention_reason,
            general_notes=general_notes,
        )

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            lid = generate_local_id(mysql_result)
            student_data["id"] = lid
            local_cache.upsert_student(student_data)
            return lid

        def _queue_data(mysql_result, entity_id):
            lid = generate_local_id(mysql_result)
            student_data["id"] = lid
            return student_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="students", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def atualizar(self, id_estudante, **dados):
        invalidos = set(dados) - _CAMPOS_ATUALIZAVEIS
        if invalidos:
            raise ValueError(
                f"Campos nao permitidos para atualizacao: {sorted(invalidos)}"
            )

        if not dados:
            return 0

        mysql_dados = {k: v for k, v in dados.items() if k != "email"}
        set_clause = ", ".join(f"{k} = %s" for k in mysql_dados)
        params = list(mysql_dados.values()) + [id_estudante]
        query = f"UPDATE aluno SET {set_clause} WHERE id_aluno = %s"
        student_data = _student_data(
            dados.get("nome", ""),
            dados.get("email", ""),
            dados.get("has_medical_report", 0),
            dados.get("requires_attention", 0),
            professor_responsavel=dados.get("professor_responsavel", "Não informado"),
            status=dados.get("status", "ativo"),
            priority_level=dados.get("priority_level", 0),
            tags=dados.get("tags"),
            avatar=dados.get("avatar", "/default_avatar.png"),
            dark_mode=dados.get("dark_mode", 0),
            notifications_enabled=dados.get("notifications_enabled", 1),
            curso=dados.get("curso"),
            age=dados.get("age"),
            phone=dados.get("phone"),
            emergency_contact=dados.get("emergency_contact"),
            emergency_phone=dados.get("emergency_phone"),
            attention_reason=dados.get("attention_reason"),
            general_notes=dados.get("general_notes"),
        )
        student_data["id"] = id_estudante

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.upsert_student(student_data)
            return 1

        def _queue_data(mysql_result, entity_id):
            return student_data

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="students", entity_id=id_estudante,
            queue_data_fn=_queue_data,
        )

    def deletar(self, id_estudante):
        query = "DELETE FROM aluno WHERE id_aluno = %s"

        def _mysql():
            execute_non_query(query, (id_estudante,))
            return 1

        def _local(mysql_result):
            validate_table_name("students")
            local_cache.delete("students", "id", id_estudante)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="students", entity_id=id_estudante,
            queue_data_fn=lambda r, eid: {"id": id_estudante},
        )

    def bloquear_minigames(self, id_estudante, motivo=""):
        query = "UPDATE aluno SET minigames_blocked = 1, minigames_block_reason = %s WHERE id_aluno = %s"
        execute_non_query(query, (motivo, id_estudante))
        queue_sync("update", "students", id_estudante, {"minigames_blocked": 1, "minigames_block_reason": motivo})
        return 1

    def desbloquear_minigames(self, id_estudante):
        query = "UPDATE aluno SET minigames_blocked = 0, minigames_block_reason = NULL WHERE id_aluno = %s"
        execute_non_query(query, (id_estudante,))
        queue_sync("update", "students", id_estudante, {"minigames_blocked": 0})
        return 1

    def verificar_comportamento_suspeito(self, id_estudante):
        query = "SELECT * FROM aluno WHERE id_aluno = %s"
        student = fetch_one(query, (id_estudante,))
        if not student:
            return {"suspicious": False, "reasons": ["Estudante não encontrado"]}
        reasons = []
        if student.get("priority_level", 0) >= 4:
            reasons.append("Alto nível de prioridade")
        if student.get("requires_attention"):
            reasons.append("Requer atenção")
        suspicious = len(reasons) > 0
        return {"suspicious": suspicious, "reasons": reasons, "student_id": id_estudante}

    def obter_log_bloqueio(self, id_estudante):
        query = "SELECT * FROM minigame_block_log WHERE student_id = %s ORDER BY blocked_at DESC"
        return fetch_all(query, (id_estudante,))

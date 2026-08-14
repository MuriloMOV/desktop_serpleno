# -*- coding: utf-8 -*-
"""Repositorio de orientacoes."""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime
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

logger = logging.getLogger(__name__)


from ser_pleno.config.paths import get_project_root

base_dir = get_project_root()
_UPLOAD_DIR = os.path.join(base_dir, "uploads", "orientations")


class OrientacaoRepository:
    @with_local_fallback("_local_listar_orientacoes")
    def listar_orientacoes(self, id_estudante: Optional[str] = None) -> List[Dict[str, Any]]:
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

    def _local_listar_orientacoes(self, id_estudante: Optional[str] = None) -> List[Dict[str, Any]]:
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
            })
        return resultado

    @with_local_fallback("_local_listar_estudantes")
    def listar_estudantes(self) -> List[Dict[str, Any]]:
        """Lista todos os estudantes cadastrados."""
        query = """
            SELECT a.id_aluno as id, a.nome as name, a.email as contact
            FROM aluno a
            ORDER BY a.nome ASC
        """
        return fetch_all(query)

    def _local_listar_estudantes(self) -> List[Dict[str, Any]]:
        rows = local_cache.list_students()
        resultado = []
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "name": r.get("nome"),
                "contact": r.get("email"),
            })
        return resultado

    @with_local_fallback("_local_obter_orientacao")
    def obter_orientacao(self, id_orientacao: int) -> Optional[Dict[str, Any]]:
        """Obtem uma orientacao especifica pelo ID."""
        query = """
            SELECT o.*, a.nome as student_name, a.id_aluno as student_id
            FROM desktop_orientation o
            LEFT JOIN aluno a ON o.student_id = a.id_aluno
            WHERE o.id = %s
        """
        return fetch_one(query, (id_orientacao,))

    def _local_obter_orientacao(self, id_orientacao: int) -> Optional[Dict[str, Any]]:
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
        }

    def criar_orientacao(
        self,
        student_id: int,
        title: str,
        theme: str,
        session_date: Any,
        content: str,
        is_markdown: int,
        motivational_message: Optional[str],
        action_plan: Any,
        psychologist: int,
    ) -> int:
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

    def atualizar_orientacao(
        self,
        id_orientacao: int,
        student_id: int,
        title: str,
        theme: str,
        session_date: Any,
        content: str,
        is_markdown: int,
        motivational_message: Optional[str],
        action_plan: Any,
        psychologist: int,
    ) -> int:
        """Atualiza uma orientacao existente."""
        action_plan_json = json.dumps(action_plan) if action_plan else "[]"
        query = """
            UPDATE desktop_orientation
            SET student_id = %s, title = %s, theme = %s, session_date = %s, content = %s,
                is_markdown = %s, motivational_message = %s, action_plan = %s,
                psychologist_id = %s, updated_at = NOW()
            WHERE id = %s
        """
        params = (
            student_id, title, theme, session_date, content, is_markdown,
            motivational_message, action_plan_json, psychologist, id_orientacao
        )
        orientation_data = {
            "id": id_orientacao,
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

    def deletar_orientacao(self, id_orientacao: int) -> int:
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

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Anexos de orientações
    # ••••••••••••••••••••••••••••••••••••••••••
    def _salvar_arquivo_local(self, src_path: str, orientation_id: int) -> str:
        nome = f"{uuid.uuid4().hex}{os.path.splitext(src_path)[1]}"
        dest_dir = os.path.join(_UPLOAD_DIR, str(orientation_id))
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, nome)
        shutil.copy2(src_path, dest_path)
        return dest_path

    @with_local_fallback("_local_listar_anexos")
    def listar_anexos(self, orientation_id: int) -> List[Dict[str, Any]]:
        """Lista anexos de uma orientação."""
        query = """
            SELECT id, orientation_id, uploaded_by_id, file, file_name, mime_type, created_at
            FROM desktop_orientation_attachment
            WHERE orientation_id = %s
            ORDER BY created_at ASC
        """
        return fetch_all(query, (orientation_id,))

    def _local_listar_anexos(self, orientation_id: int) -> List[Dict[str, Any]]:
        rows = local_cache.list_orientation_attachments(orientation_id)
        resultado = []
        for r in rows:
            resultado.append({
                "id": r.get("id"),
                "orientation_id": r.get("orientation_id"),
                "uploaded_by_id": r.get("uploaded_by_id"),
                "file": r.get("file"),
                "file_name": r.get("file_name"),
                "mime_type": r.get("mime_type"),
                "created_at": r.get("created_at"),
            })
        return resultado

    @with_local_fallback("_local_obter_anexo")
    def obter_anexo(self, attachment_id: int) -> Optional[Dict[str, Any]]:
        """Obtém um anexo específico."""
        query = """
            SELECT id, orientation_id, uploaded_by_id, file, file_name, mime_type, created_at
            FROM desktop_orientation_attachment
            WHERE id = %s
        """
        return fetch_one(query, (attachment_id,))

    def _local_obter_anexo(self, attachment_id: int) -> Optional[Dict[str, Any]]:
        rows = local_cache.list_all("orientation_attachments", where_clause="id=?", params=(attachment_id,))
        if not rows:
            return None
        return rows[0]

    def criar_anexo(self, orientation_id: int, uploaded_by_id: int, file_path: str, file_name: str, mime_type: str) -> int:
        """Cria um novo anexo para uma orientação."""
        saved_path = self._salvar_arquivo_local(file_path, orientation_id)
        query = """
            INSERT INTO desktop_orientation_attachment
            (orientation_id, uploaded_by_id, file, file_name, mime_type, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        params = (orientation_id, uploaded_by_id, saved_path, file_name, mime_type)

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            attachment_data = {
                "id": generate_local_id(mysql_result),
                "orientation_id": orientation_id,
                "uploaded_by_id": uploaded_by_id,
                "file": saved_path,
                "file_name": file_name,
                "mime_type": mime_type,
            }
            local_cache.upsert_orientation_attachment(attachment_data)
            return mysql_result

        def _queue_data(mysql_result, entity_id):
            return {
                "orientation_id": orientation_id,
                "uploaded_by_id": uploaded_by_id,
                "file": saved_path,
                "file_name": file_name,
                "mime_type": mime_type,
            }

        return write_with_fallback(
            _mysql, _local,
            operation="create", entity="orientation_attachments", entity_id="novo",
            queue_data_fn=_queue_data,
        )

    def deletar_anexo(self, attachment_id: int) -> int:
        """Deleta um anexo."""
        anexo = self.obter_anexo(attachment_id)
        if anexo and os.path.exists(anexo.get("file", "")):
            try:
                os.remove(anexo["file"])
            except Exception as exc:
                logger.exception("Falha ao remover anexo %s: %s", anexo.get("file"), exc)

        query = "DELETE FROM desktop_orientation_attachment WHERE id = %s"

        def _mysql():
            execute_non_query(query, (attachment_id,))
            return 1

        def _local(mysql_result):
            local_cache.delete("orientation_attachments", "id", attachment_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="orientation_attachments", entity_id=attachment_id,
            queue_data_fn=lambda r, eid: {"id": attachment_id},
        )

    @with_local_fallback("_local_obter_estatisticas")
    def obter_estatisticas(self, id_estudante: Optional[str] = None) -> Dict[str, Any]:
        """Obtem estatisticas das orientacoes."""
        total = fetch_one("SELECT COUNT(*) as total FROM desktop_orientation")
        by_theme = fetch_all("""
            SELECT theme, COUNT(*) as count
            FROM desktop_orientation
            WHERE 1=1
        """)
        by_month = fetch_all("""
            SELECT DATE_FORMAT(session_date, '%Y-%m-01') as month, COUNT(*) as count
            FROM desktop_orientation
            WHERE 1=1
            GROUP BY DATE_FORMAT(session_date, '%Y-%m-01')
            ORDER BY month DESC
            LIMIT 12
        """)
        params = []
        if id_estudante:
            by_theme = fetch_all("""
                SELECT theme, COUNT(*) as count
                FROM desktop_orientation
                WHERE student_id = %s
                GROUP BY theme
                ORDER BY count DESC
            """, (id_estudante,))
            by_month = fetch_all("""
                SELECT DATE_FORMAT(session_date, '%Y-%m-01') as month, COUNT(*) as count
                FROM desktop_orientation
                WHERE student_id = %s
                GROUP BY DATE_FORMAT(session_date, '%Y-%m-01')
                ORDER BY month DESC
                LIMIT 12
            """, (id_estudante,))
            total = fetch_one("SELECT COUNT(*) as total FROM desktop_orientation WHERE student_id = %s", (id_estudante,))

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

    def _local_obter_estatisticas(self) -> Dict[str, Any]:
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

    def obter_temas(self) -> List[Dict[str, str]]:
        temas = [
            {"value": "Geral", "label": "Geral"},
            {"value": "Acadêmico", "label": "Acadêmico"},
            {"value": "Emocional", "label": "Emocional"},
            {"value": "Social", "label": "Social"},
            {"value": "Familiar", "label": "Familiar"},
            {"value": "Vocacional", "label": "Vocacional"},
        ]
        return temas

    def obter_templates(self) -> List[Dict[str, str]]:
        templates = [
            {"id": "study_support", "label": "Apoio Pedagógico"},
            {"id": "emotional_support", "label": "Apoio Emocional"},
            {"id": "career_guidance", "label": "Orientação Profissional"},
        ]
        return templates

    def usar_template(self, template_id: str, student_id: int) -> Optional[Dict[str, str]]:
        preset = {
            "study_support": {
                "label": "Apoio Pedagógico",
                "content": "Conteúdo/Dificuldade\n\nEstratégias de Apoio\n\nEncaminhar para Tutoria",
            },
            "emotional_support": {
                "label": "Apoio Emocional",
                "content": "Sintomas/Observações\n\nEncaminhar para Atendimento\n\nSugestões de Autocuidado",
            },
            "career_guidance": {
                "label": "Orientação Profissional",
                "content": "Área de Interesse\n\nPlano de Carreira\n\nAgendar follow-up",
            },
        }
        p = preset.get(template_id)
        if not p:
            return None
        return {
            "title": p.get("label", "Orientação"),
            "content": p.get("content", ""),
            "theme": "Geral",
            "student_id": student_id,
        }

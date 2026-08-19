# -*- coding: utf-8 -*-
"""Repositorio de documentos."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ser_pleno.repositories.base import (
    execute_non_query,
    fetch_all,
    fetch_one,
    with_local_fallback,
    local_cache,
    write_with_fallback,
    generate_local_id,
)
from ser_pleno.infrastructure.api.sync_service import queue_sync

logger = logging.getLogger(__name__)


class DocumentRepository:
    @with_local_fallback("_local_listar_documentos")
    def listar_documentos(self, student_id=None, expiring=False, search=None):
        query = "SELECT * FROM desktop_document WHERE 1=1"
        params = []

        if student_id is not None:
            query += " AND student_id = %s"
            params.append(student_id)
        if expiring:
            query += " AND expires_at <= DATE_ADD(NOW(), INTERVAL 30 DAY)"
        if search:
            query += " AND (name LIKE %s OR description LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY uploaded_at DESC"
        return fetch_all(query, params)

    def _local_listar_documentos(self, student_id=None, expiring=False, search=None):
        rows = local_cache.list_documents(student_id=student_id)
        if expiring:
            rows = [r for r in rows if r.get("expires_at")]
        if search:
            search_lower = search.lower()
            rows = [
                r
                for r in rows
                if search_lower in (r.get("name") or "").lower()
                or search_lower in (r.get("description") or "").lower()
            ]
        return rows

    @with_local_fallback("_local_obter_documento")
    def obter_documento(self, document_id):
        query = "SELECT * FROM desktop_document WHERE id = %s"
        return fetch_one(query, (document_id,))

    def _local_obter_documento(self, document_id):
        rows = local_cache.list_all(
            "documents", where_clause="id=?", params=(document_id,)
        )
        if rows:
            return rows[0]
        return None

    def criar_documento(
        self,
        name,
        document_type,
        file_path,
        file_size,
        uploaded_by_id,
        student_id=None,
        description=None,
        expires_at=None,
        is_public=False,
    ):
        query = """
            INSERT INTO desktop_document (
                name, document_type, file_path, file_size, uploaded_by_id,
                student_id, description, expires_at, is_public, uploaded_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        params = (
            name,
            document_type,
            file_path,
            file_size,
            uploaded_by_id,
            student_id,
            description,
            expires_at,
            int(is_public),
        )
        document_data = {
            "name": name,
            "document_type": document_type,
            "file_path": file_path,
            "file_size": file_size,
            "uploaded_by_id": uploaded_by_id,
            "student_id": student_id,
            "description": description,
            "expires_at": str(expires_at) if expires_at else None,
            "is_public": int(is_public),
            "uploaded_at": datetime.now().isoformat(),
        }

        def _mysql():
            return execute_non_query(query, params)

        def _local(mysql_result):
            lid = generate_local_id(mysql_result)
            document_data["id"] = lid
            local_cache.upsert_document(document_data)
            return lid

        def _queue_data(mysql_result, entity_id):
            lid = generate_local_id(mysql_result)
            document_data["id"] = lid
            return document_data

        last_id = write_with_fallback(
            _mysql,
            _local,
            operation="create",
            entity="documents",
            entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def atualizar_documento(self, document_id, **dados):
        if not dados:
            return 0

        set_clause = ", ".join(f"{k} = %s" for k in dados)
        params = list(dados.values()) + [document_id]
        query = f"UPDATE desktop_document SET {set_clause} WHERE id = %s"

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.update("documents", dados, "id", document_id)
            return 1

        def _queue_data(mysql_result, entity_id):
            return {"id": document_id, **dados}

        return write_with_fallback(
            _mysql,
            _local,
            operation="update",
            entity="documents",
            entity_id=document_id,
            queue_data_fn=_queue_data,
        )

    def deletar_documento(self, document_id):
        query = "DELETE FROM desktop_document WHERE id = %s"

        def _mysql():
            execute_non_query(query, (document_id,))
            return 1

        def _local(mysql_result):
            local_cache.delete("documents", "id", document_id)
            return 1

        return write_with_fallback(
            _mysql,
            _local,
            operation="delete",
            entity="documents",
            entity_id=document_id,
            queue_data_fn=lambda r, eid: {"id": document_id},
        )

    @with_local_fallback("_local_listar_documentos_expirados")
    def listar_documentos_expirados(self):
        query = """
            SELECT * FROM desktop_document
            WHERE expires_at IS NOT NULL
              AND expires_at <= NOW()
            ORDER BY expires_at ASC
        """
        return fetch_all(query)

    def _local_listar_documentos_expirados(self):
        rows = local_cache.list_documents()
        result = []
        for r in rows:
            expires_at = r.get("expires_at")
            if expires_at and expires_at <= datetime.now().isoformat():
                result.append(r)
        return result

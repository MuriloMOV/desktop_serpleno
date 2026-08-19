# -*- coding: utf-8 -*-
"""Service de Documents."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ser_pleno.features.documents.repo import DocumentRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.utils.api_fallback import api_fallback

logger = logging.getLogger(__name__)


class ServicoDocuments:
    def __init__(self, auth_service=None):
        self.repo: DocumentRepository = DocumentRepository()
        self._auth_service = auth_service
        self._api: ClienteAPI = ClienteAPI(auth_service=auth_service)
        self._operation_config = None

    def _get_operation_config(self):
        if self._operation_config is None:
            try:
                from ser_pleno.config.operation_mode import get_operation_config
                self._operation_config = get_operation_config()
            except Exception:
                pass
        return self._operation_config

    def _should_use_api(self) -> bool:
        config = self._get_operation_config()
        if config is None:
            return True
        return config.should_use_api()

    @api_fallback("_fallback_listar_documentos")
    def listar_documentos(self, student_id=None, expiring=False, search=None):
        if not self._should_use_api():
            return self._fallback_listar_documentos(student_id, expiring, search)

        def _api_call():
            params: Dict[str, Any] = {}
            if student_id is not None:
                params["student_id"] = student_id
            if expiring:
                params["expiring"] = "true"
            if search:
                params["search"] = search
            resp = self._api.get("documents/", params=params if params else None)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_listar_documentos(self, student_id=None, expiring=False, search=None):
        try:
            rows = self.repo.listar_documentos(student_id=student_id, expiring=expiring, search=search)
            documentos = []
            for r in rows:
                documentos.append({
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "document_type": r.get("document_type"),
                    "file_path": r.get("file_path"),
                    "file_size": r.get("file_size"),
                    "uploaded_by_id": r.get("uploaded_by_id"),
                    "student_id": r.get("student_id"),
                    "description": r.get("description"),
                    "expires_at": r.get("expires_at"),
                    "is_public": bool(r.get("is_public")),
                    "uploaded_at": r.get("uploaded_at"),
                })
            return {"success": True, "data": documentos}
        except Exception as e:
            logger.error(f"Erro ao listar documentos locais: {e}")
            return {"success": True, "data": []}

    @api_fallback("_fallback_obter_documento")
    def obter_documento(self, document_id):
        if not self._should_use_api():
            return self._fallback_obter_documento(document_id)

        def _api_call():
            resp = self._api.get(f"documents/{document_id}/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_obter_documento(self, document_id):
        try:
            r = self.repo.obter_documento(document_id)
            if not r:
                return {"success": False, "message": "Documento não encontrado"}
            return {"success": True, "data": r}
        except Exception as e:
            logger.error(f"Erro ao obter documento local: {e}")
            return {"success": False, "message": str(e)}

    @api_fallback("_fallback_criar_documento")
    def criar_documento(self, dados):
        if not self._should_use_api():
            return self._fallback_criar_documento(dados)

        def _api_call():
            resp = self._api.post("documents/upload/", json=dados)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_criar_documento(self, dados):
        try:
            document_id = self.repo.criar_documento(
                name=dados.get("name"),
                document_type=dados.get("document_type"),
                file_path=dados.get("file_path", ""),
                file_size=dados.get("file_size", 0),
                uploaded_by_id=dados.get("uploaded_by_id", 1),
                student_id=dados.get("student_id"),
                description=dados.get("description", ""),
                expires_at=dados.get("expires_at"),
                is_public=dados.get("is_public", False),
            )
            return {"success": True, "message": "Documento criado com sucesso", "data": {"id": document_id}}
        except Exception as e:
            logger.error(f"Erro ao criar documento local: {e}")
            return {"success": False, "message": str(e)}

    @api_fallback("_fallback_deletar_documento")
    def deletar_documento(self, document_id):
        if not self._should_use_api():
            return self._fallback_deletar_documento(document_id)

        def _api_call():
            resp = self._api.delete(f"documents/{document_id}/delete/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_deletar_documento(self, document_id):
        try:
            self.repo.deletar_documento(document_id)
            return {"success": True, "message": "Documento deletado com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao deletar documento local: {e}")
            return {"success": False, "message": str(e)}

    @api_fallback("_fallback_atualizar_documento")
    def atualizar_documento(self, document_id, **dados):
        if not self._should_use_api():
            return self._fallback_atualizar_documento(document_id, **dados)

        def _api_call():
            resp = self._api.put(f"documents/{document_id}/", json=dados)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_atualizar_documento(self, document_id, **dados):
        try:
            self.repo.atualizar_documento(document_id, **dados)
            return {"success": True, "message": "Documento atualizado com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao atualizar documento local: {e}")
            return {"success": False, "message": str(e)}

    @api_fallback("_fallback_listar_documentos_expirados")
    def listar_documentos_expirados(self):
        if not self._should_use_api():
            return self._fallback_listar_documentos_expirados()

        def _api_call():
            resp = self._api.get("documents/expiring/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_listar_documentos_expirados(self):
        try:
            rows = self.repo.listar_documentos_expirados()
            documentos = []
            for r in rows:
                documentos.append({
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "document_type": r.get("document_type"),
                    "expires_at": r.get("expires_at"),
                    "student_id": r.get("student_id"),
                })
            return {"success": True, "data": documentos}
        except Exception as e:
            logger.error(f"Erro ao listar documentos expirados locais: {e}")
            return {"success": True, "data": []}

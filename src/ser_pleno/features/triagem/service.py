"""Service de Triagem — orquestrador, sem SQL inline."""

import logging

from ser_pleno.features.triagem.repo import TriagemRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.utils.api_fallback import api_fallback
from ser_pleno.utils.mappers import safe_str

logger = logging.getLogger(__name__)


class ServicoTriagem:
    def __init__(self, auth_service=None):
        self.repo = TriagemRepository()
        self._operation_config = None
        self._auth_service = auth_service
        self._api = ClienteAPI(auth_service=auth_service)

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

    def listar_triagens(self, busca=None, status=None, prioridade=None, id_estudante=None, pagina=1):
        rows = self.repo.listar(busca=busca, status=status, prioridade=prioridade,
                                id_estudante=id_estudante, pagina=pagina)
        triagens = []
        for r in rows:
            triagens.append({
                "id": r.get("id"),
                "student_id": r.get("student_id"),
                "student_name": safe_str(r.get("student_name"), "Estudante"),
                "form_id": r.get("form_id"),
                "form_name": safe_str(r.get("form_name"), "Formulário"),
                "status": r.get("status"),
                "priority": r.get("priority"),
                "scheduled_date": safe_str(r.get("scheduled_date")),
                "completed_date": safe_str(r.get("completed_date")),
                "score": r.get("score"),
                "created_at": safe_str(r.get("created_at")),
            })
        return {"success": True, "data": triagens}

    def obter_triagem(self, id_triagem):
        r = self.repo.obter(id_triagem)
        if not r:
            return {"success": False, "message": "Triagem não encontrada"}
        triagem = {
            "id": r.get("id"),
            "student_id": r.get("student_id"),
            "student_name": safe_str(r.get("student_name"), "Estudante"),
            "form_id": r.get("form_id"),
            "form_name": safe_str(r.get("form_name"), "Formulário"),
            "status": r.get("status"),
            "priority": r.get("priority"),
            "scheduled_date": safe_str(r.get("scheduled_date")),
            "completed_date": safe_str(r.get("completed_date")),
            "score": r.get("score"),
            "responses": r.get("responses"),
            "observations": r.get("observations"),
            "recommendations": r.get("recommendations"),
            "requires_followup": bool(r.get("requires_followup")),
            "followup_date": safe_str(r.get("followup_date")),
            "created_at": safe_str(r.get("created_at")),
            "questions": r.get("questions"),
        }
        return {"success": True, "data": triagem}

    def criar_triagem(self, dados):
        triagem_id = self.repo.criar(dados)
        return {"success": True, "data": {"id": triagem_id}}

    def atualizar_triagem(self, id_triagem, dados):
        self.repo.atualizar(id_triagem, dados)
        return {"success": True, "message": "Triagem atualizada com sucesso"}

    def deletar_triagem(self, id_triagem):
        self.repo.deletar(id_triagem)
        return {"success": True, "message": "Triagem deletada com sucesso"}

    @api_fallback("_local_listar_formularios")
    def listar_formularios(self):
        if not self._should_use_api():
            logger.info("Modo offline: usando repositório local para formulários")
            return self._local_listar_formularios()

        def _api_call():
            resp = self._api.get("screenings/forms/")
            if resp and resp.get("success") is not False and resp.get("data") is not None:
                logger.info("Formulários carregados via API")
                return resp
            logger.debug("API não retornou dados válidos para formulários, usando repositório local")
            return None

        return _api_call()

    def _local_listar_formularios(self):
        rows = self.repo.listar_formularios()
        formularios = []
        for r in rows:
            formularios.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "description": r.get("description"),
                "questions": r.get("questions"),
                "is_active": bool(r.get("is_active")),
                "created_at": safe_str(r.get("created_at")),
            })
        return {"success": True, "data": formularios}


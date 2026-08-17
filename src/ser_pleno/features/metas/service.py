# -*- coding: utf-8 -*-
"""
Servico de Metas para o Desktop CustomTkinter
Funciona de forma independente com sincronizacao opcional com a API do SerPleno Web
"""

import logging
from typing import Optional, Dict, Any, List

from ser_pleno.features.metas.repo import MetaRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.utils.api_fallback import api_fallback

logger = logging.getLogger(__name__)

CATEGORY_CHOICES = [
    "Academico",
    "Emocional",
    "Social",
    "Familiar",
    "Vocacional",
    "Comportamental",
    "Geral",
]

PRIORITY_CHOICES = [
    "low",
    "medium",
    "high",
    "urgent",
]

STATUS_CHOICES = [
    "not_started",
    "in_progress",
    "completed",
    "paused",
    "cancelled",
]

STATUS_LABELS = {
    "not_started": "Nao iniciada",
    "in_progress": "Em andamento",
    "completed": "Concluida",
    "paused": "Pausada",
    "cancelled": "Cancelada",
}

PRIORITY_LABELS = {
    "low": "Baixa",
    "medium": "Media",
    "high": "Alta",
    "urgent": "Urgente",
}

CATEGORY_COLORS = {
    "Academico": ("#2563EB", "#DBEAFE"),
    "Emocional": ("#DB2777", "#FCE7F3"),
    "Social": ("#0891B2", "#CCFBF1"),
    "Familiar": ("#EA580C", "#FFEDD5"),
    "Vocacional": ("#7C3AED", "#EDE9FE"),
    "Comportamental": ("#059669", "#D1FAE5"),
    "Geral": ("#4F46E5", "#EEF2FF"),
}


class ServicoMetas:
    """Servico para gerenciar metas via API do SerPleno Web."""

    def __init__(self, auth_service=None):
        self.repo = MetaRepository()
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

    def _get_session(self):
        auth = self._auth_service
        if auth and hasattr(auth, "get_session"):
            return auth.get_session()
        return None

    def _get_headers(self):
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        auth = self._auth_service
        if auth:
            if hasattr(auth, "get_headers"):
                return auth.get_headers()
            if hasattr(auth, "csrf_token") and auth.csrf_token:
                headers["X-CSRFToken"] = auth.csrf_token
        return headers

    @api_fallback("_listar_metas_local")
    def listar_metas(self, student_id=None, status=None, category=None, priority=None, pagina=1):
        """Lista metas com filtros opcionais."""
        if not self._should_use_api():
            return self._listar_metas_local(student_id, status, category, priority)

        def _api_call():
            params: Dict[str, Any] = {"page": pagina}
            if student_id is not None:
                params["student_id"] = student_id
            if status:
                params["status"] = status
            if category:
                params["category"] = category
            if priority:
                params["priority"] = priority

            resp = self._api.get("desktop/goals/", params=params)
            if resp and resp.get("success") is not False and resp.get("data") is not None:
                return resp
            return None

        return _api_call()

    def _listar_metas_local(self, student_id=None, status=None, category=None, priority=None):
        try:
            rows = self.repo.listar_metas(student_id, status, category, priority)
            metas = []
            for r in rows:
                metas.append({
                    "id": r.get("id"),
                    "student_id": r.get("student_id"),
                    "student_name": r.get("student_name") or "Estudante",
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

            total = len(metas)
            return {
                "success": True,
                "data": {
                    "goals": metas,
                    "pagination": {"page": 1, "total": total, "total_pages": 1},
                },
            }
        except Exception as e:
            logger.error(f"Erro ao listar metas locais: {e}")
            return {
                "success": True,
                "data": {"goals": [], "pagination": {"page": 1, "total": 0}},
            }

    @api_fallback("_fallback_obter_meta")
    def obter_meta(self, id_meta):
        """Obtém detalhes de uma meta específica."""
        def _api_call():
            resp = self._api.get(f"desktop/goals/{id_meta}/")
            if resp and resp.get("success") is not False and resp.get("data") is not None:
                return resp
            return None

        return _api_call()

    def _fallback_obter_meta(self, id_meta):
        try:
            r = self.repo.obter_meta(id_meta)
            if not r:
                return {"success": False, "message": "Meta não encontrada"}
            return {"success": True, "data": r}
        except Exception as e:
            logger.error(f"Erro ao obter meta local: {e}")
            return {"success": False, "message": str(e)}

    @api_fallback("_fallback_criar_meta")
    def criar_meta(self, dados):
        """Cria uma nova meta."""
        def _api_call():
            resp = self._api.post("desktop/goals/create/", json=dados)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_criar_meta(self, dados):
        try:
            meta_id = self.repo.criar_meta(
                student_id=dados.get("student_id"),
                title=dados.get("title"),
                category=dados.get("category"),
                priority=dados.get("priority"),
                target_date=dados.get("target_date"),
                description=dados.get("description", ""),
                notes=dados.get("notes", ""),
                success_criteria=dados.get("success_criteria", ""),
                created_by_id=dados.get("created_by_id"),
                status=dados.get("status", "not_started"),
                progress_percentage=dados.get("progress_percentage", 0),
            )
            logger.info(f"Meta criada localmente: {meta_id}")
            return {"success": True, "message": "Meta criada com sucesso", "data": {"id": meta_id}}
        except Exception as e:
            logger.error(f"Erro ao criar meta local: {e}")
            return {"success": False, "message": str(e)}

    @api_fallback("_fallback_atualizar_meta")
    def atualizar_meta(self, id_meta, dados):
        """Atualiza uma meta existente."""
        def _api_call():
            resp = self._api.put(f"desktop/goals/{id_meta}/update/", json=dados)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_atualizar_meta(self, id_meta, dados):
        try:
            self.repo.atualizar_meta(id_meta, **dados)
            return {"success": True, "message": "Meta atualizada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao atualizar meta local: {e}")
            return {"success": False, "message": str(e)}

    @api_fallback("_fallback_deletar_meta")
    def deletar_meta(self, id_meta):
        """Deleta uma meta."""
        def _api_call():
            resp = self._api.delete(f"desktop/goals/{id_meta}/delete/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_deletar_meta(self, id_meta):
        try:
            self.repo.deletar_meta(id_meta)
            return {"success": True, "message": "Meta deletada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao deletar meta local: {e}")
            return {"success": False, "message": str(e)}

    @api_fallback("_fallback_registrar_progresso")
    def registrar_progresso(self, id_meta, percentage, notes, recorded_by_id):
        """Registra progresso em uma meta."""
        def _api_call():
            resp = self._api.post(
                f"desktop/goals/{id_meta}/progress/",
                json={
                    "percentage": percentage,
                    "notes": notes,
                    "recorded_by_id": recorded_by_id,
                },
            )
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_registrar_progresso(self, id_meta, percentage, notes, recorded_by_id):
        try:
            progress_id = self.repo.registrar_progresso(
                id_meta, percentage, notes, recorded_by_id
            )
            return {
                "success": True,
                "message": "Progresso registrado com sucesso",
                "data": {"id": progress_id},
            }
        except Exception as e:
            logger.error(f"Erro ao registrar progresso local: {e}")
            return {"success": False, "message": str(e)}

    def listar_progresso(self, id_meta):
        """Lista historico de progresso de uma meta."""
        try:
            rows = self.repo.listar_progresso(id_meta)
            progresso = []
            for r in rows:
                progresso.append({
                    "id": r.get("id"),
                    "goal_id": r.get("goal_id"),
                    "percentage": r.get("percentage"),
                    "notes": r.get("notes"),
                    "recorded_at": r.get("recorded_at"),
                    "recorded_by_id": r.get("recorded_by_id"),
                    "recorded_by_name": r.get("recorded_by_name") or "Usuario",
                })
            return {"success": True, "data": progresso}
        except Exception as e:
            logger.error(f"Erro ao listar progresso: {e}")
            return {"success": True, "data": []}

    def listar_metas_atrasadas(self):
        """Lista metas atrasadas."""
        try:
            rows = self.repo.listar_metas_atrasadas()
            metas = []
            for r in rows:
                metas.append({
                    "id": r.get("id"),
                    "student_id": r.get("student_id"),
                    "student_name": r.get("student_name") or "Estudante",
                    "title": r.get("title"),
                    "category": r.get("category"),
                    "priority": r.get("priority"),
                    "status": r.get("status"),
                    "target_date": r.get("target_date"),
                    "progress_percentage": r.get("progress_percentage", 0),
                })
            return {"success": True, "data": metas}
        except Exception as e:
            logger.error(f"Erro ao listar metas atrasadas: {e}")
            return {"success": True, "data": []}

    def obter_estatisticas(self):
        """Obtém estatísticas das metas."""
        try:
            stats = self.repo.obter_estatisticas()
            return {"success": True, "data": stats}
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                "success": True,
                "data": {
                    "total": 0,
                    "by_status": [],
                    "by_category": [],
                    "by_priority": [],
                    "overdue": 0,
                },
            }

    def listar_estudantes(self):
        """Lista estudantes para selecao."""
        try:
            from ser_pleno.features.estudantes.repo import EstudanteRepository
            repo = EstudanteRepository()
            rows = repo.listar()
            estudantes = [
                {
                    "id": r.get("id_aluno"),
                    "name": r.get("nome") or "Estudante",
                }
                for r in rows
            ]
            return {"success": True, "data": estudantes}
        except Exception as e:
            logger.error(f"Erro ao listar estudantes: {e}")
            return {"success": True, "data": []}


# Instancia global para facil acesso
servico_metas = ServicoMetas()

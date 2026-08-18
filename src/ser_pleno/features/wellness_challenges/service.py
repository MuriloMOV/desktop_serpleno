# -*- coding: utf-8 -*-
"""Servico de Wellness Challenges com fallback para API web e repositorio local."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ser_pleno.features.wellness_challenges.repo import WellnessChallengeRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.utils.api_fallback import api_fallback

logger = logging.getLogger(__name__)


class ServicoWellnessChallenges:
    def __init__(self, auth_service=None):
        self.repo = WellnessChallengeRepository()
        self._auth_service = auth_service
        self._api = ClienteAPI(auth_service=auth_service)
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

    @api_fallback("_fallback_listar_desafios")
    def listar_desafios(self, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        if not self._should_use_api():
            return self._local_listar_desafios(apenas_ativos)

        def _api_call():
            params = {}
            if not apenas_ativos:
                params["is_active"] = "false"
            resp = self._api.get("wellness/challenges/", params=params if params else None)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_listar_desafios(self, apenas_ativos=True):
        rows = self.repo.listar_desafios(apenas_ativos=apenas_ativos)
        return {"success": True, "data": rows}

    def _local_listar_desafios(self, apenas_ativos=True):
        rows = self.repo.listar_desafios(apenas_ativos=apenas_ativos)
        return {"success": True, "data": rows}

    @api_fallback("_fallback_obter_desafio")
    def obter_desafio(self, challenge_id: int) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_obter_desafio(challenge_id)

        def _api_call():
            resp = self._api.get(f"wellness/challenges/{challenge_id}/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_obter_desafio(self, challenge_id=None):
        row = self.repo.obter_desafio(challenge_id)
        if row:
            return {"success": True, "data": row}
        return {"success": False, "message": "Desafio não encontrado"}

    def _local_obter_desafio(self, challenge_id):
        row = self.repo.obter_desafio(challenge_id)
        if row:
            return {"success": True, "data": row}
        return {"success": False, "message": "Desafio não encontrado"}

    @api_fallback("_fallback_criar_desafio")
    def criar_desafio(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        title = dados.get("title", "")
        description = dados.get("description", "")
        category = dados.get("category", "other")
        difficulty = dados.get("difficulty", "medium")
        points = dados.get("points", 0)
        is_active = dados.get("is_active", True)

        if not title:
            return {"success": False, "message": "Título do desafio é obrigatório."}

        if not self._should_use_api():
            return self._local_criar_desafio(title, description, category, difficulty, points, is_active)

        def _api_call():
            payload = {
                "title": title,
                "description": description,
                "category": category,
                "difficulty": difficulty,
                "points": points,
                "is_active": is_active,
            }
            resp = self._api.post("wellness/challenges/create/", json=payload)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_criar_desafio(self, dados):
        title = dados.get("title", "")
        description = dados.get("description", "")
        category = dados.get("category", "other")
        difficulty = dados.get("difficulty", "medium")
        points = dados.get("points", 0)
        is_active = dados.get("is_active", True)
        last_id = self.repo.criar_desafio(title, description, category, difficulty, points, is_active)
        row = self.repo.obter_desafio(last_id)
        return {"success": True, "data": row}

    def _local_criar_desafio(self, title, description, category, difficulty, points, is_active):
        last_id = self.repo.criar_desafio(title, description, category, difficulty, points, is_active)
        row = self.repo.obter_desafio(last_id)
        return {"success": True, "data": row}

    @api_fallback("_fallback_atualizar_desafio")
    def atualizar_desafio(self, challenge_id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_atualizar_desafio(challenge_id, dados)

        def _api_call():
            payload = {k: v for k, v in dados.items() if v is not None}
            resp = self._api.post(f"wellness/challenges/{challenge_id}/update/", json=payload)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_atualizar_desafio(self, challenge_id, dados):
        ok = self.repo.atualizar_desafio(challenge_id, **dados)
        if ok:
            row = self.repo.obter_desafio(challenge_id)
            return {"success": True, "data": row}
        return {"success": False, "message": "Desafio não encontrado"}

    def _local_atualizar_desafio(self, challenge_id, dados):
        ok = self.repo.atualizar_desafio(challenge_id, **dados)
        if ok:
            row = self.repo.obter_desafio(challenge_id)
            return {"success": True, "data": row}
        return {"success": False, "message": "Desafio não encontrado"}

    @api_fallback("_fallback_deletar_desafio")
    def deletar_desafio(self, challenge_id: int) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_deletar_desafio(challenge_id)

        def _api_call():
            resp = self._api.post(f"wellness/challenges/{challenge_id}/delete/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_deletar_desafio(self, challenge_id=None):
        ok = self.repo.deletar_desafio(challenge_id)
        if ok:
            return {"success": True, "message": "Desafio excluído com sucesso"}
        return {"success": False, "message": "Desafio não encontrado"}

    def _local_deletar_desafio(self, challenge_id):
        ok = self.repo.deletar_desafio(challenge_id)
        if ok:
            return {"success": True, "message": "Desafio excluído com sucesso"}
        return {"success": False, "message": "Desafio não encontrado"}

    @api_fallback("_fallback_atribuir_desafio")
    def atribuir_desafio(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        challenge_id = dados.get("challenge_id")
        student_id = dados.get("student_id")
        assigned_by_id = dados.get("assigned_by_id") or 1

        if not challenge_id or not student_id:
            return {"success": False, "message": "Desafio e estudante são obrigatórios."}

        if not self._should_use_api():
            return self._local_atribuir_desafio(challenge_id, student_id, assigned_by_id)

        def _api_call():
            payload = {
                "challenge_id": challenge_id,
                "student_id": student_id,
                "assigned_by_id": assigned_by_id,
            }
            resp = self._api.post("wellness/challenges/assign/", json=payload)
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_atribuir_desafio(self, challenge_id, student_id, assigned_by_id):
        last_id = self.repo.atribuir_desafio(challenge_id, student_id, assigned_by_id)
        row = self.repo.obter_atribuicao(last_id)
        return {"success": True, "data": row}

    def _local_atribuir_desafio(self, challenge_id, student_id, assigned_by_id):
        last_id = self.repo.atribuir_desafio(challenge_id, student_id, assigned_by_id)
        row = self.repo.obter_atribuicao(last_id)
        return {"success": True, "data": row}

    @api_fallback("_fallback_desatribuir_desafio")
    def desatribuir_desafio(self, assignment_id: int) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_desatribuir_desafio(assignment_id)

        def _api_call():
            resp = self._api.post(f"wellness/challenges/assignments/{assignment_id}/unassign/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_desatribuir_desafio(self, assignment_id):
        ok = self.repo.desatribuir_desafio(assignment_id)
        if ok:
            return {"success": True, "message": "Atribuição removida"}
        return {"success": False, "message": "Atribuição não encontrada"}

    def _local_desatribuir_desafio(self, assignment_id):
        ok = self.repo.desatribuir_desafio(assignment_id)
        if ok:
            return {"success": True, "message": "Atribuição removida"}
        return {"success": False, "message": "Atribuição não encontrada"}

    @api_fallback("_fallback_completar_desafio")
    def completar_desafio(self, assignment_id: int) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_completar_desafio(assignment_id)

        def _api_call():
            resp = self._api.post(f"wellness/challenges/assignments/{assignment_id}/complete/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_completar_desafio(self, assignment_id):
        ok = self.repo.completar_desafio(assignment_id)
        if ok:
            row = self.repo.obter_atribuicao(assignment_id)
            return {"success": True, "data": row}
        return {"success": False, "message": "Atribuição não encontrada"}

    def _local_completar_desafio(self, assignment_id):
        ok = self.repo.completar_desafio(assignment_id)
        if ok:
            row = self.repo.obter_atribuicao(assignment_id)
            return {"success": True, "data": row}
        return {"success": False, "message": "Atribuição não encontrada"}

    @api_fallback("_fallback_listar_desafios_estudante")
    def listar_desafios_estudante(self, student_id: int) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_listar_desafios_estudante(student_id)

        def _api_call():
            resp = self._api.get(f"wellness/challenges/student/{student_id}/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_listar_desafios_estudante(self, student_id):
        rows = self.repo.obter_desafios_estudante(student_id)
        return {"success": True, "data": rows}

    def _local_listar_desafios_estudante(self, student_id):
        rows = self.repo.obter_desafios_estudante(student_id)
        return {"success": True, "data": rows}

    @api_fallback("_fallback_obter_dashboard")
    def obter_dashboard(self) -> Dict[str, Any]:
        if not self._should_use_api():
            return self._local_obter_dashboard()

        def _api_call():
            resp = self._api.get("wellness/challenges/dashboard/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return _api_call()

    def _fallback_obter_dashboard(self):
        data = self.repo.obter_dashboard()
        return {"success": True, "data": data}

    def _local_obter_dashboard(self):
        data = self.repo.obter_dashboard()
        return {"success": True, "data": data}

"""
Servico de Intervencoes para o Desktop CustomTkinter
Funciona de forma independente com sincronizacao opcional com a API do SerPleno Web
"""

import logging
from typing import Optional, Dict, Any, List

from ser_pleno.features.interventions.repo import IntervencaoRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.config.config import DESKTOP_API_URL

logger = logging.getLogger(__name__)

INTERVENTION_TYPES = [
    ("counseling", "Aconselhamento"),
    ("academic_support", "Apoio Academico"),
    ("emotional_support", "Apoio Emocional"),
    ("crisis_intervention", "Intervencao em Crise"),
    ("family_meeting", "Reuniao com Familia"),
    ("referral", "Encaminhamento"),
    ("follow_up", "Acompanhamento"),
    ("group_session", "Sessao em Grupo"),
    ("phone_call", "Ligacao Telefonica"),
    ("other", "Outro"),
]

OUTCOME_CHOICES = [
    ("positive", "Positivo"),
    ("neutral", "Neutro"),
    ("needs_followup", "Precisa Acompanhamento"),
    ("escalation", "Escalacao Necessaria"),
    ("pending", "Pendente"),
]


class ServicoIntervencoes:
    """Servico para gerenciar intervencoes via API do SerPleno Web ou repositório local."""

    def __init__(self, auth_service=None):
        self.base_url = DESKTOP_API_URL
        self.repo = IntervencaoRepository()
        self._operation_config = None
        self._auth_service = auth_service

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
        try:
            import requests
            return requests
        except Exception:
            return None

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        auth = self._auth_service
        if auth:
            if hasattr(auth, "get_headers"):
                return auth.get_headers()
            if hasattr(auth, "csrf_token") and auth.csrf_token:
                headers["X-CSRFToken"] = auth.csrf_token
        return headers

    def listar_intervencoes(
        self,
        student_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        intervention_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self._should_use_api():
            logger.info("Modo independente: usando repositório local")
            return self._listar_intervencoes_local(
                student_id=student_id,
                date_from=date_from,
                date_to=date_to,
                intervention_type=intervention_type,
                search=search,
            )

        def _api_call():
            params: Dict[str, Any] = {}
            if student_id:
                params["student_id"] = student_id
            if date_from:
                params["date_from"] = date_from
            if date_to:
                params["date_to"] = date_to
            if intervention_type:
                params["type"] = intervention_type
            if search:
                params["search"] = search

            session = self._get_session()
            if not session:
                return None
            url = f"{self.base_url.rstrip('/')}/interventions/"
            response = session.get(url, params=params, headers=self._get_headers(), timeout=10)
            if response.ok:
                data = response.json()
                if data.get("success") is not False:
                    return data
            return None

        result = _api_call()
        if result is not None:
            return result

        logger.debug("API nao retornou dados validos, usando repositorio local")
        return self._listar_intervencoes_local(
            student_id=student_id,
            date_from=date_from,
            date_to=date_to,
            intervention_type=intervention_type,
            search=search,
        )

    def _listar_intervencoes_local(
        self,
        student_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        intervention_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            rows = self.repo.listar_intervencoes(
                student_id=student_id, date_from=date_from, date_to=date_to
            )
            intervencoes = []
            for r in rows:
                itype = r.get("intervention_type") or ""
                notes = r.get("intervention_notes") or ""
                if intervention_type and itype != intervention_type:
                    continue
                if search:
                    term = search.lower()
                    if term not in itype.lower() and term not in notes.lower():
                        continue
                intervencoes.append({
                    "id": r.get("id"),
                    "student_id": r.get("student_id"),
                    "student_name": r.get("student_name") or "Estudante",
                    "date": r.get("date"),
                    "intervention_type": itype,
                    "duration_minutes": r.get("duration_minutes"),
                    "notes": notes,
                    "outcome": r.get("outcome"),
                    "outcome_notes": r.get("outcome_notes"),
                    "follow_up_required": bool(r.get("follow_up_required")),
                    "follow_up_date": r.get("follow_up_date"),
                    "follow_up_completed": bool(r.get("follow_up_completed")),
                    "is_confidential": bool(r.get("is_confidential")),
                    "tags": r.get("tags"),
                })

            total = len(intervencoes)
            return {
                "success": True,
                "data": {
                    "interventions": intervencoes,
                    "pagination": {"page": 1, "per_page": total, "total": total, "total_pages": 1},
                },
            }
        except Exception as e:
            logger.error(f"Erro ao listar intervencoes locais: {e}")
            return {"success": False, "error": str(e), "data": {"interventions": [], "pagination": {"page": 1, "total": 0}}}

    def obter_intervencao(self, id_intervencao: int) -> Dict[str, Any]:
        try:
            r = self.repo.obter_intervencao(id_intervencao)
            if not r:
                return {"success": False, "message": "Intervencao nao encontrada"}
            return {
                "success": True,
                "data": {
                    "id": r.get("id"),
                    "student_id": r.get("student_id"),
                    "student_name": r.get("student_name") or "Estudante",
                    "date": r.get("date"),
                    "intervention_type": r.get("intervention_type"),
                    "duration_minutes": r.get("duration_minutes"),
                    "notes": r.get("intervention_notes"),
                    "outcome": r.get("outcome"),
                    "outcome_notes": r.get("outcome_notes"),
                    "follow_up_required": bool(r.get("follow_up_required")),
                    "follow_up_date": r.get("follow_up_date"),
                    "follow_up_completed": bool(r.get("follow_up_completed")),
                    "is_confidential": bool(r.get("is_confidential")),
                    "tags": r.get("tags"),
                },
            }
        except Exception as e:
            logger.error(f"Erro ao obter intervencao: {e}")
            return {"success": False, "message": str(e)}

    def adicionar_intervencao(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        student_id = dados.get("student_id")
        date = dados.get("date")
        notes = dados.get("notes", "")

        if not student_id or not date:
            return {"success": False, "error": "student_id e date sao obrigatorios"}

        if not self._should_use_api():
            try:
                iid = self.repo.criar_intervencao(
                    student_id=int(student_id),
                    date=str(date),
                    intervention_type=dados.get("intervention_type", "counseling"),
                    duration_minutes=dados.get("duration_minutes"),
                    intervention_notes=str(notes),
                    outcome=dados.get("outcome", "pending"),
                    outcome_notes=dados.get("outcome_notes", ""),
                    follow_up_required=bool(dados.get("follow_up_required", False)),
                    follow_up_date=dados.get("follow_up_date"),
                    follow_up_completed=bool(dados.get("follow_up_completed", False)),
                    is_confidential=bool(dados.get("is_confidential", False)),
                    tags=dados.get("tags"),
                )
                return {"success": True, "message": "Intervencao criada com sucesso", "data": {"id": iid}}
            except Exception as e:
                logger.error(f"Erro ao criar intervencao local: {e}")
                return {"success": False, "error": str(e)}

        def _api_call():
            session = self._get_session()
            if not session:
                return None
            url = f"{self.base_url.rstrip('/')}/interventions/add/"
            payload = {
                "student_id": int(student_id),
                "date": str(date),
                "notes": str(notes),
            }
            response = session.post(url, json=payload, headers=self._get_headers(), timeout=10)
            if response.ok:
                data = response.json()
                if data.get("success") is not False:
                    return data
            return None

        result = _api_call()
        if result is not None:
            return result

        try:
            iid = self.repo.criar_intervencao(
                student_id=int(student_id),
                date=str(date),
                intervention_type=dados.get("intervention_type", "counseling"),
                duration_minutes=dados.get("duration_minutes"),
                intervention_notes=str(notes),
                outcome=dados.get("outcome", "pending"),
                outcome_notes=dados.get("outcome_notes", ""),
                follow_up_required=bool(dados.get("follow_up_required", False)),
                follow_up_date=dados.get("follow_up_date"),
                follow_up_completed=bool(dados.get("follow_up_completed", False)),
                is_confidential=bool(dados.get("is_confidential", False)),
                tags=dados.get("tags"),
            )
            return {"success": True, "message": "Intervencao criada com sucesso", "data": {"id": iid}}
        except Exception as e:
            logger.error(f"Erro ao criar intervencao: {e}")
            return {"success": False, "error": str(e)}

    def deletar_intervencao(self, id_intervencao: int) -> Dict[str, Any]:
        if not self._should_use_api():
            try:
                self.repo.deletar_intervencao(id_intervencao)
                return {"success": True, "message": "Intervencao deletada com sucesso"}
            except Exception as e:
                logger.error(f"Erro ao deletar intervencao local: {e}")
                return {"success": False, "error": str(e)}

        def _api_call():
            session = self._get_session()
            if not session:
                return None
            url = f"{self.base_url.rstrip('/')}/interventions/{id_intervencao}/delete/"
            response = session.delete(url, headers=self._get_headers(), timeout=10)
            if response.ok:
                try:
                    return response.json()
                except Exception:
                    return {"success": True}
            return None

        result = _api_call()
        if result is not None and result.get("success") is not False:
            return result

        try:
            self.repo.deletar_intervencao(id_intervencao)
            return {"success": True, "message": "Intervencao deletada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao deletar intervencao: {e}")
            return {"success": False, "error": str(e)}

    def get_tipos_intervencao(self) -> List[Dict[str, str]]:
        return [{"value": k, "label": v} for k, v in INTERVENTION_TYPES]

    def get_resultados_intervencao(self) -> List[Dict[str, str]]:
        return [{"value": k, "label": v} for k, v in OUTCOME_CHOICES]


servico_intervencoes = ServicoIntervencoes()

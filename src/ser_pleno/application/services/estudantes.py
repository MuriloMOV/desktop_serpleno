# -*- coding: utf-8 -*-
"""
Serviço de Estudantes para o Desktop CustomTkinter
Funciona de forma independente com sincronização opcional com a API do SerPleno Web
"""

import logging
from typing import Optional, Dict, Any, List, Callable

from ser_pleno.repositories.estudantes import EstudanteRepository
from ser_pleno.repositories.bem_estar import BemEstarRepository
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.utils.service_helpers import with_api_fallback

logger = logging.getLogger(__name__)


def _invalidate_dashboard_cache() -> None:
    try:
        from ser_pleno.repositories.dashboard import invalidate_dashboard_cache
        invalidate_dashboard_cache()
    except Exception:
        pass


class ServicoEstudante:
    """Serviço para gerenciar estudantes - usa o cliente API central quando disponível
    e faz fallback para o repositório local quando necessário.
    """

    def __init__(self, auth_service=None):
        self.repo = EstudanteRepository()
        self.repo_bem_estar = BemEstarRepository()
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

    def listar_estudantes(
        self,
        busca: Optional[str] = None,
        possui_laudo: Optional[bool] = None,
        requer_atencao: Optional[bool] = None,
        pagina: int = 1,
    ) -> Dict[str, Any]:
        """Lista estudantes com filtros opcionais"""
        if not self._should_use_api():
            logger.info("Modo independente: usando repositório local")
            return self._listar_estudantes_local(
                busca, possui_laudo, requer_atencao, pagina
            )

        def _api_call():
            params: Dict[str, Any] = {"page": pagina}
            if busca:
                params["search"] = busca
            if possui_laudo is not None:
                params["has_medical_report"] = possui_laudo
            if requer_atencao is not None:
                params["requires_attention"] = requer_atencao

            resp = self._api.get("students/", params=params)
            if (
                resp
                and resp.get("success") is not False
                and resp.get("data") is not None
            ):
                logger.info(
                    f"Estudantes carregados via API: {len(resp.get('data', []))} registros"
                )
                return resp

            logger.debug("API não retornou dados válidos, usando repositório local")
            return None

        return with_api_fallback(
            _api_call,
            self._listar_estudantes_local,
            busca,
            possui_laudo,
            requer_atencao,
            pagina,
        )

    def _listar_estudantes_local(
        self,
        busca: Optional[str] = None,
        possui_laudo: Optional[bool] = None,
        requer_atencao: Optional[bool] = None,
        pagina: int = 1,
    ) -> Dict[str, Any]:
        """Busca estudantes diretamente do repositório local"""
        try:
            logger.info("Tentando conectar ao repositório de estudantes...")
            rows = self.repo.listar(
                busca=busca, possui_laudo=possui_laudo, requer_atencao=requer_atencao
            )
            total = len(rows)
            logger.info(f"Encontrados {total} estudantes no repositório local")

            students = []
            for r in rows:
                students.append(
                    {
                        "id": r.get("id_aluno"),
                        "name": r.get("nome"),
                        "course": r.get("curso"),
                        "age": r.get("age") or r.get("idade"),
                        "has_medical_report": bool(r.get("has_medical_report")),
                        "requires_attention": bool(r.get("requires_attention")),
                        "contact": r.get("contact") or r.get("email") or "",
                        "priority_level": r.get("priority_level") or 0,
                    }
                )

            return {
                "success": True,
                "data": students,
                "pagination": {
                    "page": 1,
                    "per_page": total,
                    "total": total,
                    "total_pages": 1,
                },
            }
        except Exception as e:
            logger.error(f"Erro ao listar estudantes locais: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e), "data": []}

    def obter_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Obtém detalhes de um estudante específico via API ou repositório local"""
        def _api_call():
            resp = self._api.get(f"students/{id_estudante}/")
            if (
                resp
                and resp.get("success") is not False
                and resp.get("data") is not None
            ):
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_obter_estudante,
            id_estudante,
        )

    def _fallback_obter_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Fallback para obter estudante do repositório local"""
        try:
            r = self.repo.obter(id_estudante)
            student = None
            if r:
                student = {
                    "id": r.get("id_aluno"),
                    "name": r.get("nome"),
                    "course": r.get("curso"),
                    "age": r.get("age") or r.get("idade"),
                    "phone": r.get("phone") or "",
                    "contact": r.get("contact") or "",
                    "emergency_contact": r.get("emergency_contact") or "",
                    "emergency_phone": r.get("emergency_phone") or "",
                    "has_medical_report": bool(r.get("has_medical_report")),
                    "requires_attention": bool(r.get("requires_attention")),
                    "attention_reason": r.get("attention_reason")
                    or r.get("attention_notes")
                    or "",
                    "professor_responsavel": r.get("professor_responsavel") or "Não informado",
                    "status": r.get("status") or "ativo",
                    "priority_level": r.get("priority_level") or 0,
                    "general_notes": r.get("general_notes") or "",
                    "minigame_blocked": bool(r.get("minigames_blocked") or r.get("minigame_blocked") or False),
                    "minigame_block_reason": r.get("minigames_block_reason") or r.get("minigame_block_reason") or "",
                }
            return {"success": True, "data": student}
        except Exception as e:
            logger.error(f"Erro no fallback ao obter estudante: {e}")
            return {"success": False, "error": str(e), "data": None}

    def obter_relatorio_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Obtém relatório completo do estudante via API ou repositório local"""
        def _api_call():
            resp = self._api.get(f"students/{id_estudante}/report/")
            if (
                resp
                and resp.get("success") is not False
                and resp.get("data") is not None
            ):
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_obter_relatorio_estudante,
            id_estudante,
        )

    def _fallback_obter_relatorio_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Fallback para obter relatório do estudante do repositório local"""
        student_resp = self._fallback_obter_estudante(id_estudante)
        student = student_resp.get("data") if isinstance(student_resp, dict) else None

        moods_resp = self.repo_bem_estar.obter_humor_estudante(id_estudante)
        moods = moods_resp if isinstance(moods_resp, list) else []

        return {"success": True, "data": {"student": student, "moods": moods}}

    def criar_estudante(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um novo estudante via API ou repositório local"""
        def _api_call():
            resp = self._api.post("students/add/", json=dados)
            if resp and resp.get("success") is not False:
                logger.info(f"Estudante criado via API: {resp}")
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_criar_estudante,
            dados,
        )

    def _fallback_criar_estudante(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para criar estudante no repositório local"""
        try:
            nome = dados.get("name") or dados.get("nome")
            email = dados.get("contact") or dados.get("email")
            self.repo.criar(
                nome=nome,
                email=email,
                has_medical_report=bool(dados.get("has_medical_report", False)),
                requires_attention=bool(dados.get("requires_attention", False)),
                professor_responsavel=dados.get("professor_responsavel", "Não informado"),
                status=dados.get("status", "ativo"),
                priority_level=int(dados.get("priority_level", 0)),
                tags=dados.get("tags"),
                curso=dados.get("course"),
                age=dados.get("age"),
                phone=dados.get("phone"),
                emergency_contact=dados.get("emergency_contact"),
                emergency_phone=dados.get("emergency_phone"),
                attention_reason=dados.get("attention_reason"),
                general_notes=dados.get("general_notes"),
            )
            _invalidate_dashboard_cache()
            return {"success": True, "message": "Estudante criado com sucesso"}
        except Exception as e:
            logger.error(f"Erro no fallback ao criar estudante: {e}")
            return {"success": False, "error": str(e)}

    def atualizar_estudante(
        self, id_estudante: int, dados: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Atualiza um estudante existente via API ou repositório local"""
        def _api_call():
            resp = self._api.put(f"students/{id_estudante}/update/", json=dados)
            if resp and resp.get("success") is not False:
                logger.info(f"Estudante atualizado via API: {resp}")
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_atualizar_estudante,
            id_estudante,
            dados,
        )

    def _fallback_atualizar_estudante(
        self, id_estudante: int, dados: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback para atualizar estudante no repositório local"""
        try:
            nome = dados.get("name") or dados.get("nome")
            email = dados.get("contact") or dados.get("email")
            self.repo.atualizar(
                id_estudante,
                nome=nome,
                email=email,
                has_medical_report=bool(dados.get("has_medical_report", False)),
                requires_attention=bool(dados.get("requires_attention", False)),
                professor_responsavel=dados.get("professor_responsavel", "Não informado"),
                status=dados.get("status", "ativo"),
                priority_level=int(dados.get("priority_level", 0)),
                tags=dados.get("tags"),
                curso=dados.get("course"),
                age=dados.get("age"),
                phone=dados.get("phone"),
                emergency_contact=dados.get("emergency_contact"),
                emergency_phone=dados.get("emergency_phone"),
                attention_reason=dados.get("attention_reason"),
                general_notes=dados.get("general_notes"),
            )
            _invalidate_dashboard_cache()
            return {"success": True, "message": "Estudante atualizado com sucesso"}
        except Exception as e:
            logger.error(f"Erro no fallback ao atualizar estudante: {e}")
            return {"success": False, "error": str(e)}

    def deletar_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Deleta um estudante via API ou repositório local"""
        def _api_call():
            resp = self._api.delete(f"students/{id_estudante}/delete/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_deletar_estudante,
            id_estudante,
        )

    def _fallback_deletar_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Fallback para deletar estudante no repositório local"""
        try:
            self.repo.deletar(id_estudante)
            _invalidate_dashboard_cache()
            return {"success": True, "message": "Estudante deletado com sucesso"}
        except Exception as e:
            logger.error(f"Erro no fallback ao deletar estudante: {e}")
            return {"success": False, "error": str(e)}

    def bloquear_minigames(self, id_estudante: int, motivo: str = "") -> Dict[str, Any]:
        """Bloqueia o acesso do estudante aos minigames."""
        def _api_call():
            resp = self._api.post(f"students/{id_estudante}/block-minigames/", json={"reason": motivo})
            if resp and resp.get("success") is not False:
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_bloquear_minigames,
            id_estudante,
            motivo,
        )

    def _fallback_bloquear_minigames(self, id_estudante: int, motivo: str) -> Dict[str, Any]:
        try:
            self.repo.bloquear_minigames(id_estudante, motivo)
            _invalidate_dashboard_cache()
            return {"success": True, "message": "Minigames bloqueados com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao bloquear minigames: {e}")
            return {"success": False, "error": str(e)}

    def desbloquear_minigames(self, id_estudante: int) -> Dict[str, Any]:
        """Desbloqueia o acesso do estudante aos minigames."""
        def _api_call():
            resp = self._api.post(f"students/{id_estudante}/unblock-minigames/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_desbloquear_minigames,
            id_estudante,
        )

    def _fallback_desbloquear_minigames(self, id_estudante: int) -> Dict[str, Any]:
        try:
            self.repo.desbloquear_minigames(id_estudante)
            _invalidate_dashboard_cache()
            return {"success": True, "message": "Minigames desbloqueados com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao desbloquear minigames: {e}")
            return {"success": False, "error": str(e)}

    def verificar_comportamento_suspeito(self, id_estudante: int) -> Dict[str, Any]:
        """Verifica comportamento suspeito de gamificação."""
        def _api_call():
            resp = self._api.post(f"students/{id_estudante}/check-suspicious-behavior/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_verificar_comportamento_suspeito,
            id_estudante,
        )

    def _fallback_verificar_comportamento_suspeito(self, id_estudante: int) -> Dict[str, Any]:
        try:
            result = self.repo.verificar_comportamento_suspeito(id_estudante)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Erro ao verificar comportamento suspeito: {e}")
            return {"success": False, "error": str(e)}

    def obter_log_bloqueio(self, id_estudante: int) -> Dict[str, Any]:
        """Retorna histórico de bloqueios de minigames do estudante."""
        def _api_call():
            resp = self._api.get(f"students/{id_estudante}/block-log/")
            if resp and resp.get("success") is not False:
                return resp
            return None

        return with_api_fallback(
            _api_call,
            self._fallback_obter_log_bloqueio,
            id_estudante,
        )

    def _fallback_obter_log_bloqueio(self, id_estudante: int) -> Dict[str, Any]:
        try:
            rows = self.repo.obter_log_bloqueio(id_estudante)
            return {"success": True, "data": rows}
        except Exception as e:
            logger.error(f"Erro ao obter log de bloqueio: {e}")
            return {"success": False, "error": str(e), "data": []}


# Instância global para fácil acesso
servico_estudante = ServicoEstudante()

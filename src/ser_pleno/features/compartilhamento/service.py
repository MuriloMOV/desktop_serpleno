# -*- coding: utf-8 -*-
"""
Serviço de Compartilhamento de Dados Clínicos para o Desktop CustomTkinter.
Funciona de forma independente com sincronização opcional com a API do SerPleno Web.
"""

import logging
from typing import Optional, Dict, Any, List, Callable

from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.utils.api_fallback import api_fallback

logger = logging.getLogger(__name__)


class ServicoCompartilhamentoDadosClinicos:
    """Serviço para gerenciar compartilhamento de dados clínicos."""

    def __init__(self, auth_service=None):
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

    @api_fallback("_listar_compartilhamentos_local")
    def listar_compartilhamentos(
        self,
        busca: Optional[str] = None,
        data_type: Optional[str] = None,
        student_id: Optional[int] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """Lista compartilhamentos com filtros opcionais."""
        if not self._should_use_api():
            logger.info("Modo independente: usando repositório local")
            return self._listar_compartilhamentos_local(
                busca, data_type, student_id, page
            )

        def _api_call():
            params: Dict[str, Any] = {"page": page}
            if busca:
                params["search"] = busca
            if data_type:
                params["data_type"] = data_type
            if student_id:
                params["student"] = student_id

            resp = self._api.get("desktop/shared-data/", params=params)
            if (
                resp
                and resp.get("success") is not False
                and resp.get("data") is not None
            ):
                logger.info(
                    f"Compartilhamentos carregados via API: {len(resp.get('data', []))} registros"
                )
                return resp

            logger.debug("API não retornou dados válidos, usando repositório local")
            return None

        return _api_call()

    def _listar_compartilhamentos_local(
        self,
        busca: Optional[str] = None,
        data_type: Optional[str] = None,
        student_id: Optional[int] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """Busca compartilhamentos diretamente do repositório local."""
        try:
            logger.info("Tentando conectar ao repositório de compartilhamentos...")
            rows = self._repo.listar(
                busca=busca, data_type=data_type, student_id=student_id, page=page
            )
            total = len(rows)
            logger.info(f"Encontrados {total} compartilhamentos no repositório local")

            data = []
            for r in rows:
                data.append({
                    "id": r.get("id"),
                    "student": {
                        "id": r.get("student_id"),
                        "name": r.get("student_name", ""),
                    },
                    "shared_by": {
                        "id": r.get("shared_by_id"),
                        "name": r.get("shared_by_name", ""),
                    },
                    "shared_with_user": {
                        "id": r.get("shared_with_user_id"),
                        "name": r.get("shared_with_user_name", ""),
                        "role": r.get("shared_with_role", ""),
                    },
                    "data_type": r.get("data_type", ""),
                    "created_at": r.get("created_at", ""),
                })

            return {
                "success": True,
                "data": data,
                "pagination": {
                    "page": page,
                    "per_page": len(data),
                    "total": total,
                    "total_pages": 1,
                },
            }
        except Exception as e:
            logger.error(f"Erro ao listar compartilhamentos locais: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e), "data": []}

    @api_fallback("_fallback_compartilhar")
    def compartilhar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Compartilha dados clínicos com outro usuário via API ou repositório local."""
        if not self._should_use_api():
            logger.info("Modo independente: usando fallback local")
            return self._fallback_compartilhar(dados)

        def _api_call():
            resp = self._api.post("desktop/shared-data/share/", json=dados)
            if resp and resp.get("success") is not False:
                logger.info(f"Dados compartilhados via API: {resp}")
                return resp
            return None

        return _api_call()

    def _fallback_compartilhar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para compartilhar no repositório local."""
        try:
            self._repo.compartilhar(
                student_id=dados.get("student_id"),
                shared_with_user_id=dados.get("shared_with_user_id"),
                shared_with_role=dados.get("shared_with_role", ""),
                data_type=dados.get("data_type", ""),
                shared_by_id=dados.get("shared_by_id"),
            )
            return {"success": True, "message": "Dados compartilhados com sucesso"}
        except Exception as e:
            logger.error(f"Erro no fallback ao compartilhar: {e}")
            return {"success": False, "error": str(e)}

    @api_fallback("_fallback_descompartilhar")
    def descompartilhar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Descompartilha dados clínicos via API ou repositório local."""
        if not self._should_use_api():
            logger.info("Modo independente: usando fallback local")
            return self._fallback_descompartilhar(dados)

        def _api_call():
            resp = self._api.post("desktop/shared-data/unshare/", json=dados)
            if resp and resp.get("success") is not False:
                logger.info(f"Dados descompartilhados via API: {resp}")
                return resp
            return None

        return _api_call()

    def _fallback_descompartilhar(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para descompartilhar no repositório local."""
        try:
            self._repo.descompartilhar(
                student_id=dados.get("student_id"),
                shared_with_user_id=dados.get("shared_with_user_id"),
                data_type=dados.get("data_type", ""),
            )
            return {"success": True, "message": "Compartilhamento removido com sucesso"}
        except Exception as e:
            logger.error(f"Erro no fallback ao descompartilhar: {e}")
            return {"success": False, "error": str(e)}

    @api_fallback("_fallback_bulk_share")
    def bulk_share(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Compartilhamento em massa via API ou repositório local."""
        if not self._should_use_api():
            logger.info("Modo independente: usando fallback local")
            return self._fallback_bulk_share(dados)

        def _api_call():
            resp = self._api.post("desktop/shared-data/bulk/share/", json=dados)
            if resp and resp.get("success") is not False:
                logger.info(f"Bulk share realizado via API: {resp}")
                return resp
            return None

        return _api_call()

    def _fallback_bulk_share(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para bulk share no repositório local."""
        try:
            student_ids = dados.get("student_ids", [])
            shared_with_user_id = dados.get("shared_with_user_id")
            shared_with_role = dados.get("shared_with_role", "")
            data_type = dados.get("data_type", "")
            shared_by_id = dados.get("shared_by_id")

            count = 0
            for student_id in student_ids:
                self._repo.compartilhar(
                    student_id=student_id,
                    shared_with_user_id=shared_with_user_id,
                    shared_with_role=shared_with_role,
                    data_type=data_type,
                    shared_by_id=shared_by_id,
                )
                count += 1

            return {
                "success": True,
                "message": f"{count} compartilhamento(s) realizado(s) com sucesso",
            }
        except Exception as e:
            logger.error(f"Erro no fallback ao realizar bulk share: {e}")
            return {"success": False, "error": str(e)}

    @api_fallback("_fallback_bulk_unshare")
    def bulk_unshare(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Descompartilhamento em massa via API ou repositório local."""
        if not self._should_use_api():
            logger.info("Modo independente: usando fallback local")
            return self._fallback_bulk_unshare(dados)

        def _api_call():
            resp = self._api.post("desktop/shared-data/bulk/unshare/", json=dados)
            if resp and resp.get("success") is not False:
                logger.info(f"Bulk unshare realizado via API: {resp}")
                return resp
            return None

        return _api_call()

    def _fallback_bulk_unshare(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para bulk unshare no repositório local."""
        try:
            student_ids = dados.get("student_ids", [])
            shared_with_user_id = dados.get("shared_with_user_id")
            data_type = dados.get("data_type", "")

            count = 0
            for student_id in student_ids:
                self._repo.descompartilhar(
                    student_id=student_id,
                    shared_with_user_id=shared_with_user_id,
                    data_type=data_type,
                )
                count += 1

            return {
                "success": True,
                "message": f"{count} compartilhamento(s) removido(s) com sucesso",
            }
        except Exception as e:
            logger.error(f"Erro no fallback ao realizar bulk unshare: {e}")
            return {"success": False, "error": str(e)}

    @api_fallback("_listar_estudantes_compartilhados_local")
    def listar_estudantes_compartilhados(self) -> Dict[str, Any]:
        """Lista estudantes compartilhados com o usuário atual."""
        if not self._should_use_api():
            logger.info("Modo independente: usando repositório local")
            return self._listar_estudantes_compartilhados()

        def _api_call():
            resp = self._api.get("desktop/shared-data/students/")
            if (
                resp
                and resp.get("success") is not False
                and resp.get("data") is not None
            ):
                logger.info(
                    f"Estudantes compartilhados carregados via API: {len(resp.get('data', []))} registros"
                )
                return resp
            return None

        return _api_call()

    def _listar_estudantes_compartilhados_local(self) -> Dict[str, Any]:
        """Busca estudantes compartilhados do repositório local."""
        try:
            logger.info("Tentando conectar ao repositório de estudantes compartilhados...")
            rows = self._repo.listar_estudantes_compartilhados()
            total = len(rows)
            logger.info(f"Encontrados {total} estudantes compartilhados no repositório local")

            students = []
            for r in rows:
                students.append({
                    "id": r.get("student_id"),
                    "name": r.get("student_name", ""),
                    "course": r.get("course", ""),
                    "shared_data_types": r.get("shared_data_types", []),
                })

            return {
                "success": True,
                "data": students,
            }
        except Exception as e:
            logger.error(f"Erro ao listar estudantes compartilhados locais: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e), "data": []}

    @api_fallback("_fallback_obter_historico_compartilhamento")
    def obter_historico_compartilhamento(self, student_id: int) -> Dict[str, Any]:
        """Obtém histórico de compartilhamento por estudante."""
        if not self._should_use_api():
            logger.info("Modo independente: usando fallback local")
            return self._fallback_obter_historico_compartilhamento(student_id)

        def _api_call():
            resp = self._api.get(f"desktop/shared-data/history/{student_id}/")
            if (
                resp
                and resp.get("success") is not False
                and resp.get("data") is not None
            ):
                logger.info(
                    f"Histórico carregado via API: {len(resp.get('data', []))} registros"
                )
                return resp
            return None

        return _api_call()

    def _fallback_obter_historico_compartilhamento(self, student_id: int) -> Dict[str, Any]:
        """Fallback para obter histórico do repositório local."""
        try:
            logger.info(f"Tentando obter histórico do estudante {student_id} do repositório local...")
            rows = self._repo.obter_historico(student_id)
            total = len(rows)
            logger.info(f"Encontrados {total} registros no histórico local")

            history = []
            for r in rows:
                history.append({
                    "id": r.get("id"),
                    "action": r.get("action", ""),
                    "data_type": r.get("data_type", ""),
                    "shared_by": {
                        "id": r.get("shared_by_id"),
                        "name": r.get("shared_by_name", ""),
                    },
                    "shared_with_user": {
                        "id": r.get("shared_with_user_id"),
                        "name": r.get("shared_with_user_name", ""),
                        "role": r.get("shared_with_role", ""),
                    },
                    "created_at": r.get("created_at", ""),
                })

            return {
                "success": True,
                "data": history,
            }
        except Exception as e:
            logger.error(f"Erro ao obter histórico local: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e), "data": []}

    @api_fallback("_fallback_obter_relatorio_compartilhamento")
    def obter_relatorio_compartilhamento(self) -> Dict[str, Any]:
        """Obtém relatório de compartilhamento."""
        if not self._should_use_api():
            logger.info("Modo independente: usando fallback local")
            return self._fallback_obter_relatorio_compartilhamento()

        def _api_call():
            resp = self._api.get("desktop/shared-data/report/")
            if (
                resp
                and resp.get("success") is not False
                and resp.get("data") is not None
            ):
                logger.info("Relatório carregado via API")
                return resp
            return None

        return _api_call()

    def _fallback_obter_relatorio_compartilhamento(self) -> Dict[str, Any]:
        """Fallback para obter relatório do repositório local."""
        try:
            logger.info("Tentando obter relatório do repositório local...")
            report = self._repo.obter_relatorio()
            logger.info("Relatório carregado do repositório local")

            return {
                "success": True,
                "data": report,
            }
        except Exception as e:
            logger.error(f"Erro ao obter relatório local: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e), "data": {}}

    def obter_relatorio(self) -> Dict[str, Any]:
        """Obtém relatório de compartilhamento."""
        return self.obter_relatorio_compartilhamento()

    def compartilhamento_massa(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Compartilhamento em massa."""
        return self.bulk_share(dados)

    def descompartilhamento_massa(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Descompartilhamento em massa."""
        return self.bulk_unshare(dados)

    def obter_historico(self, student_id: int) -> Dict[str, Any]:
        """Obtém histórico de compartilhamento por estudante."""
        return self.obter_historico_compartilhamento(student_id)

    @property
    def _repo(self):
        from ser_pleno.features.compartilhamento.repo import CompartilhamentoDadosRepository
        return CompartilhamentoDadosRepository()


# Instância global para fácil acesso
servico_compartilhamento_dados = ServicoCompartilhamentoDadosClinicos()

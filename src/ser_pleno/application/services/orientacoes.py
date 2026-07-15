"""
Serviço de Orientações para o Desktop CustomTkinter
Funciona de forma independente com sincronização opcional com a API do SerPleno Web
"""

import logging
import json
import datetime
from typing import Optional, List, Dict, Any

try:
    import requests
except Exception:
    requests = None  # type: ignore

from ser_pleno.config.config import DESKTOP_API_URL
from ser_pleno.repositories.orientacoes import OrientacaoRepository

logger = logging.getLogger(__name__)


class ServicoOrientacoes:
    """Serviço para gerenciar orientações via API do SerPleno Web"""

    # Presets de modelos rápidos (mesmos do web)
    PRESETS = {
        "study_support": {
            "label": "Apoio Pedagógico",
            "components": [
                {"id": "p1", "type": "text", "label": "Conteúdo/Dificuldade"},
                {"id": "p2", "type": "textarea", "label": "Estratégias de Apoio"},
                {"id": "p3", "type": "checkbox", "label": "Encaminhar para Tutoria"},
            ],
        },
        "emotional_support": {
            "label": "Apoio Emocional",
            "components": [
                {"id": "p4", "type": "text", "label": "Sintomas/Observações"},
                {"id": "p5", "type": "checkbox", "label": "Encaminhar para Atendimento"},
                {"id": "p6", "type": "textarea", "label": "Sugestões de Autocuidado"},
            ],
        },
        "career_guidance": {
            "label": "Orientação Profissional",
            "components": [
                {"id": "p7", "type": "text", "label": "Área de Interesse"},
                {"id": "p8", "type": "textarea", "label": "Plano de Carreira"},
                {"id": "p9", "type": "checkbox", "label": "Agendar follow-up"},
            ],
        },
    }

    def __init__(self, auth_service=None):
        self.base_url = DESKTOP_API_URL
        self.repo = OrientacaoRepository()
        self._operation_config = None
        self._auth_service = auth_service
    
    def _get_operation_config(self):
        """Obtém configuração de operação (lazy loading)"""
        if self._operation_config is None:
            try:
                from ser_pleno.config.operation_mode import get_operation_config
                self._operation_config = get_operation_config()
            except Exception:
                pass
        return self._operation_config
    
    def _should_use_api(self) -> bool:
        """Verifica se deve tentar usar a API"""
        config = self._get_operation_config()
        if config is None:
            return True
        return config.should_use_api()
    
    def _get_session(self):
        """Retorna a sessão HTTP autenticada"""
        auth = self._auth_service
        if auth and hasattr(auth, "get_session"):
            return auth.get_session()
        return requests
    
    def _get_headers(self):
        """Retorna headers com CSRF token se disponível"""
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        auth = self._auth_service
        if auth:
            if hasattr(auth, "get_headers"):
                return auth.get_headers()
            if hasattr(auth, "csrf_token") and auth.csrf_token:
                headers["X-CSRFToken"] = auth.csrf_token
        return headers
    
    def listar_orientacoes(
        self,
        id_estudante: Optional[int] = None,
        tema: Optional[str] = None,
        pagina: int = 1,
    ) -> Dict[str, Any]:
        """Lista orientações com filtros opcionais."""
        try:
            rows = self.repo.listar_orientacoes(id_estudante)
            orientacoes = []
            for r in rows:
                orientacoes.append({
                    "id": r.get("id"),
                    "title": r.get("title"),
                    "theme": r.get("theme"),
                    "session_date": str(r.get("session_date")) if r.get("session_date") else None,
                    "student": {
                        "id": r.get("student_id"),
                        "name": r.get("student_name") or "Estudante",
                    },
                    "psychologist": r.get("psychologist"),
                    "content": r.get("content"),
                    "motivational_message": r.get("motivational_message"),
                    "created_at": str(r.get("created_at")) if r.get("created_at") else None,
                    "action_plan": json.loads(r.get("action_plan", "[]")) if r.get("action_plan") else [],
                })
            
            total = len(orientacoes)
            logger.info(f"Encontradas {total} orientações no repositório")
            return {
                "success": True,
                "data": {
                    "orientations": orientacoes,
                    "pagination": {"page": 1, "total": total, "total_pages": 1},
                },
            }
        except Exception as e:
            logger.error(f"Erro ao listar orientações: {e}")
            return {
                "success": True,
                "data": {"orientations": [], "pagination": {"page": 1, "total": 0}},
            }

    def obter_orientacao(self, id_orientacao: int) -> Dict[str, Any]:
        """Obtém detalhes de uma orientação específica."""
        try:
            r = self.repo.obter_orientacao(id_orientacao)
            if not r:
                return {"success": False, "message": "Orientação não encontrada"}
            
            orientacao = {
                "id": r.get("id"),
                "title": r.get("title"),
                "theme": r.get("theme"),
                "session_date": str(r.get("session_date")) if r.get("session_date") else None,
                "student": {
                    "id": r.get("student_id"),
                    "name": r.get("student_name") or "Estudante",
                },
                "psychologist": r.get("psychologist"),
                "content": r.get("content"),
                "is_markdown": bool(r.get("is_markdown")),
                "motivational_message": r.get("motivational_message"),
                "created_at": str(r.get("created_at")) if r.get("created_at") else None,
                "updated_at": str(r.get("updated_at")) if r.get("updated_at") else None,
                "action_plan": json.loads(r.get("action_plan", "[]")) if r.get("action_plan") else [],
            }
            return {"success": True, "data": orientacao}
        except Exception as e:
            logger.error(f"Erro ao obter orientação: {e}")
            return {"success": False, "message": str(e)}

    def criar_orientacao(
        self, dados: Dict[str, Any], arquivos: Optional[List] = None
    ) -> Dict[str, Any]:
        """Cria uma nova orientação."""
        try:
            orientacao_id = self.repo.criar_orientacao(
                student_id=dados.get("student_id"),
                title=dados.get("title"),
                theme=dados.get("theme"),
                session_date=dados.get("session_date"),
                content=dados.get("content"),
                is_markdown=dados.get("is_markdown", False),
                motivational_message=dados.get("motivational_message"),
                action_plan=dados.get("action_plan", []),
                psychologist=dados.get("psychologist", "Equipe SerPleno")
            )
            logger.info(f"Orientação criada no repositório: {orientacao_id}")
            return {"success": True, "message": "Orientação criada com sucesso", "data": {"id": orientacao_id}}
        except Exception as e:
            logger.error(f"Erro ao criar orientação: {e}")
            return {"success": False, "message": str(e)}

    def atualizar_orientacao(
        self, id_orientacao: int, dados: Dict[str, Any], arquivos: Optional[List] = None
    ) -> Dict[str, Any]:
        """Atualiza uma orientação existente."""
        try:
            self.repo.atualizar_orientacao(
                id_orientacao=id_orientacao,
                title=dados.get("title"),
                theme=dados.get("theme"),
                session_date=dados.get("session_date"),
                content=dados.get("content"),
                is_markdown=dados.get("is_markdown", False),
                motivational_message=dados.get("motivational_message"),
                action_plan=dados.get("action_plan", []),
                psychologist=dados.get("psychologist")
            )
            return {"success": True, "message": "Orientação atualizada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao atualizar orientação: {e}")
            return {"success": False, "message": str(e)}

    def deletar_orientacao(self, id_orientacao: int) -> Dict[str, Any]:
        """Deleta uma orientação."""
        try:
            self.repo.deletar_orientacao(id_orientacao)
            return {"success": True, "message": "Orientação deletada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao deletar orientação: {e}")
            return {"success": False, "message": str(e)}

    def get_preset(self, chave: str) -> Optional[Dict]:
        """Retorna um preset específico"""
        return self.PRESETS.get(chave)

    def get_presets(self) -> Dict[str, Dict]:
        """Retorna todos os presets disponíveis"""
        return self.PRESETS

    def duplicar_orientacao(
        self, id_orientacao: int, id_estudante: Optional[int] = None
    ) -> Dict[str, Any]:
        """Duplica uma orientação existente."""
        try:
            orientacao_resp = self.obter_orientacao(id_orientacao)
            if not orientacao_resp.get("success"):
                return {"success": False, "message": "Orientação original não encontrada"}
            
            orientacao = orientacao_resp.get("data", {})
            novos_dados = {
                "student_id": id_estudante or orientacao.get("student", {}).get("id"),
                "title": f"Cópia - {orientacao.get('title', 'Orientação')}",
                "theme": orientacao.get("theme"),
                "session_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                "content": orientacao.get("content"),
                "is_markdown": orientacao.get("is_markdown", False),
                "motivational_message": orientacao.get("motivational_message"),
                "action_plan": orientacao.get("action_plan", []),
                "psychologist": orientacao.get("psychologist", "Equipe SerPleno"),
            }
            return self.criar_orientacao(novos_dados)
        except Exception as e:
            logger.error(f"Erro ao duplicar orientação: {e}")
            return {"success": False, "message": str(e)}

    def obter_estatisticas(self, id_estudante: Optional[int] = None) -> Dict[str, Any]:
        """Obtém estatísticas das orientações."""
        try:
            stats = self.repo.obter_estatisticas()
            return {"success": True, "data": stats}
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"success": True, "data": {"total": 0, "by_theme": [], "by_month": []}}


# Instância global para fácil acesso
servico_orientacoes = ServicoOrientacoes()

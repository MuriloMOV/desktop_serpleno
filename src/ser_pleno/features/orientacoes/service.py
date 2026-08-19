"""
Serviço de Orientações para o Desktop CustomTkinter
Funciona de forma independente com sincronização opcional com a API do SerPleno Web
"""

import datetime
import json
import logging
import os

try:
    import requests
except Exception:
    requests = None  # type: ignore

from ser_pleno.config.config import DESKTOP_API_URL
from ser_pleno.features.orientacoes.repo import OrientacaoRepository
from ser_pleno.utils.dates import normalize_date

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
        headers = {"Content-Type": "application/json"}
        auth = self._auth_service
        if auth:
            if hasattr(auth, "get_headers"):
                return auth.get_headers()
            if hasattr(auth, "csrf_token") and auth.csrf_token:
                headers["X-CSRFToken"] = auth.csrf_token
        return headers
    
    def listar_orientacoes(
        self,
        id_estudante=None,
        tema=None,
        pagina=1,
        date_from=None,
        date_to=None,
        search=None,
    ):
        """Lista orientações com filtros opcionais."""
        try:
            rows = self.repo.listar_orientacoes(id_estudante)
            orientacoes = []
            for r in rows:
                o = {
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
                }
                if tema and o["theme"] != tema:
                    continue
                if search:
                    term = search.lower()
                    if term not in (o.get("title") or "").lower():
                        continue
                if date_from:
                    sd = o.get("session_date") or ""
                    if sd < date_from:
                        continue
                if date_to:
                    sd = o.get("session_date") or ""
                    if sd > date_to:
                        continue
                orientacoes.append(o)

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

    def obter_orientacao(self, id_orientacao: int):
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

    def criar_orientacao(self, dados, arquivos=None):
        """Cria uma nova orientação."""
        try:
            dados = dict(dados)
            session_date = dados.get("session_date")
            if session_date:
                dados["session_date"] = normalize_date(session_date)
            orientacao_id = self.repo.criar_orientacao(
                student_id=dados.get("student_id"),
                title=dados.get("title"),
                theme=dados.get("theme"),
                session_date=dados.get("session_date"),
                content=dados.get("content"),
                is_markdown=dados.get("is_markdown", False),
                motivational_message=dados.get("motivational_message", ""),
                action_plan=dados.get("action_plan", []),
                psychologist=dados.get("psychologist", "Equipe SerPleno")
            )
            logger.info(f"Orientação criada no repositório: {orientacao_id}")
            return {"success": True, "message": "Orientação criada com sucesso", "data": {"id": orientacao_id}}
        except Exception as e:
            logger.error(f"Erro ao criar orientação: {e}")
            return {"success": False, "message": str(e)}

    def atualizar_orientacao(self, id_orientacao: int, dados, arquivos=None):
        """Atualiza uma orientação existente."""
        try:
            dados = dict(dados)
            session_date = dados.get("session_date")
            if session_date:
                dados["session_date"] = normalize_date(session_date)
            self.repo.atualizar_orientacao(
                id_orientacao=id_orientacao,
                student_id=dados.get("student_id"),
                title=dados.get("title"),
                theme=dados.get("theme"),
                session_date=dados.get("session_date"),
                content=dados.get("content"),
                is_markdown=dados.get("is_markdown", False),
                motivational_message=dados.get("motivational_message", ""),
                action_plan=dados.get("action_plan", []),
                psychologist=dados.get("psychologist")
            )
            return {"success": True, "message": "Orientação atualizada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao atualizar orientação: {e}")
            return {"success": False, "message": str(e)}

    def deletar_orientacao(self, id_orientacao: int):
        """Deleta uma orientação."""
        try:
            self.repo.deletar_orientacao(id_orientacao)
            return {"success": True, "message": "Orientação deletada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao deletar orientação: {e}")
            return {"success": False, "message": str(e)}

    def get_preset(self, chave: str):
        """Retorna um preset específico"""
        return self.PRESETS.get(chave)

    def get_presets(self):
        """Retorna todos os presets disponíveis"""
        return self.PRESETS

    def duplicar_orientacao(self, id_orientacao: int, id_estudante: int | None = None):
        """Duplica uma orientação existente."""
        try:
            if self._should_use_api():
                api_result = self._duplicar_orientacao_api(id_orientacao, id_estudante)
                if api_result.get("success"):
                    return api_result
                logger.warning("Falha ao duplicar via API, usando repositório local")

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

    def _duplicar_orientacao_api(self, id_orientacao: int, id_estudante: int | None = None):
        try:
            session = self._get_session()
            endpoint = f"{self.base_url.rstrip('/')}/orientations/{id_orientacao}/duplicate/"
            payload = {}
            if id_estudante is not None:
                payload["student_id"] = id_estudante
            response = session.post(endpoint, json=payload, headers=self._get_headers(), timeout=15)
            if response.ok:
                data = response.json()
                return {"success": True, "data": data.get("data", data), "message": "Orientação duplicada com sucesso"}
            return {"success": False, "message": f"Erro na API: {response.status_code}"}
        except Exception as e:
            logger.warning(f"Erro ao duplicar via API: {e}")
            return {"success": False, "message": str(e)}

    def obter_estatisticas(self, id_estudante: int | None = None):
        """Obtém estatísticas das orientações."""
        try:
            stats = self.repo.obter_estatisticas()
            return {"success": True, "data": stats}
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"success": True, "data": {"total": 0, "by_theme": [], "by_month": []}}

    def listar_estudantes(self):
        """Lista todos os estudantes cadastrados."""
        try:
            rows = self.repo.listar_estudantes()
            estudantes = [
                {
                    "id": r.get("id"),
                    "name": r.get("name") or "Estudante",
                    "contact": r.get("contact", ""),
                }
                for r in rows
            ]
            return {"success": True, "data": estudantes}
        except Exception as e:
            logger.error(f"Erro ao listar estudantes: {e}")
            return {"success": True, "data": []}

    def listar_anexos(self, orientation_id: int):
        """Lista anexos de uma orientação."""
        try:
            if self._should_use_api():
                api_result = self._listar_anexos_api(orientation_id)
                if api_result.get("success"):
                    return api_result
                logger.warning("Falha ao listar anexos via API, usando repositório local")
            rows = self.repo.listar_anexos(orientation_id)
            anexos = [
                {
                    "id": r.get("id"),
                    "orientation_id": r.get("orientation_id"),
                    "uploaded_by_id": r.get("uploaded_by_id"),
                    "file": r.get("file"),
                    "file_name": r.get("file_name"),
                    "mime_type": r.get("mime_type"),
                    "created_at": r.get("created_at"),
                }
                for r in rows
            ]
            return {"success": True, "data": anexos}
        except Exception as e:
            logger.error(f"Erro ao listar anexos: {e}")
            return {"success": True, "data": []}

    def _listar_anexos_api(self, orientation_id: int):
        try:
            session = self._get_session()
            endpoint = f"{self.base_url.rstrip('/')}/orientations/{orientation_id}/attachments/"
            response = session.get(endpoint, headers=self._get_headers(), timeout=10)
            if response.ok:
                data = response.json()
                return {"success": True, "data": data.get("data", data)}
            return {"success": False, "message": f"Erro na API: {response.status_code}"}
        except Exception as e:
            logger.warning(f"Erro ao listar anexos via API: {e}")
            return {"success": False, "message": str(e)}

    def adicionar_anexo(self, orientation_id: int, arquivo_path: str, uploaded_by_id: int):
        """Adiciona um anexo a uma orientação."""
        try:
            file_name = os.path.basename(arquivo_path)
            mime_type = self._detectar_mime_type(arquivo_path)

            if self._should_use_api():
                api_result = self._adicionar_anexo_api(orientation_id, arquivo_path, file_name, mime_type, uploaded_by_id)
                if api_result.get("success"):
                    return api_result
                logger.warning("Falha ao adicionar anexo via API, usando repositório local")

            attachment_id = self.repo.criar_anexo(orientation_id, uploaded_by_id, arquivo_path, file_name, mime_type)
            logger.info(f"Anexo criado localmente: {attachment_id}")
            return {"success": True, "message": "Anexo adicionado com sucesso", "data": {"id": attachment_id}}
        except Exception as e:
            logger.error(f"Erro ao adicionar anexo: {e}")
            return {"success": False, "message": str(e)}

    def _adicionar_anexo_api(self, orientation_id: int, arquivo_path: str, file_name: str, mime_type: str, uploaded_by_id: int):
        try:
            session = self._get_session()
            endpoint = f"{self.base_url.rstrip('/')}/orientations/{orientation_id}/attachments/"
            with open(arquivo_path, "rb") as f:
                files = {"file": (file_name, f, mime_type)}
                data = {"uploaded_by_id": uploaded_by_id}
                response = session.post(endpoint, files=files, data=data, headers=self._get_headers(), timeout=15)
            if response.ok:
                result = response.json()
                logger.info(f"Anexo adicionado via API: {result}")
                return result
            return {"success": False, "message": f"Erro na API: {response.status_code}"}
        except Exception as e:
            logger.warning(f"Erro ao adicionar anexo via API: {e}")
            return {"success": False, "message": str(e)}

    def deletar_anexo(self, attachment_id: int):
        """Deleta um anexo."""
        try:
            if self._should_use_api():
                api_result = self._deletar_anexo_api(attachment_id)
                if api_result.get("success"):
                    return api_result
                logger.warning("Falha ao deletar anexo via API, usando repositório local")

            self.repo.deletar_anexo(attachment_id)
            return {"success": True, "message": "Anexo deletado com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao deletar anexo: {e}")
            return {"success": False, "message": str(e)}

    def _deletar_anexo_api(self, attachment_id: int):
        try:
            session = self._get_session()
            endpoint = f"{self.base_url.rstrip('/')}/orientations/attachments/{attachment_id}/delete/"
            response = session.delete(endpoint, headers=self._get_headers(), timeout=10)
            if response.ok:
                return {"success": True, "message": "Anexo deletado via API"}
            return {"success": False, "message": f"Erro na API: {response.status_code}"}
        except Exception as e:
            logger.warning(f"Erro ao deletar anexo via API: {e}")
            return {"success": False, "message": str(e)}

    def obter_temas(self):
        """Obtém lista de temas disponíveis para orientações."""
        try:
            if self._should_use_api():
                session = self._get_session()
                endpoint = f"{self.base_url.rstrip('/')}/orientations/themes/"
                response = session.get(endpoint, headers=self._get_headers(), timeout=10)
                if response.ok:
                    data = response.json()
                    return {"success": True, "data": data.get("data", data)}
            temas = [
                {"value": "Geral", "label": "Geral"},
                {"value": "Acadêmico", "label": "Acadêmico"},
                {"value": "Emocional", "label": "Emocional"},
                {"value": "Social", "label": "Social"},
                {"value": "Familiar", "label": "Familiar"},
                {"value": "Vocacional", "label": "Vocacional"},
            ]
            return {"success": True, "data": temas}
        except Exception as e:
            logger.error(f"Erro ao obter temas: {e}")
            return {"success": True, "data": [
                {"value": "Geral", "label": "Geral"},
                {"value": "Acadêmico", "label": "Acadêmico"},
                {"value": "Emocional", "label": "Emocional"},
                {"value": "Social", "label": "Social"},
                {"value": "Familiar", "label": "Familiar"},
                {"value": "Vocacional", "label": "Vocacional"},
            ]}

    def obter_templates(self):
        """Obtém lista de templates de orientação."""
        try:
            if self._should_use_api():
                session = self._get_session()
                endpoint = f"{self.base_url.rstrip('/')}/orientations/templates/"
                response = session.get(endpoint, headers=self._get_headers(), timeout=10)
                if response.ok:
                    data = response.json()
                    return {"success": True, "data": data.get("data", data)}
            templates = [
                {"id": "study_support", "label": "Apoio Pedagógico"},
                {"id": "emotional_support", "label": "Apoio Emocional"},
                {"id": "career_guidance", "label": "Orientação Profissional"},
            ]
            return {"success": True, "data": templates}
        except Exception as e:
            logger.error(f"Erro ao obter templates: {e}")
            return {"success": True, "data": [
                {"id": "study_support", "label": "Apoio Pedagógico"},
                {"id": "emotional_support", "label": "Apoio Emocional"},
                {"id": "career_guidance", "label": "Orientação Profissional"},
            ]}

    def listar_templates(self):
        """Lista templates de orientação disponíveis."""
        try:
            if self._should_use_api():
                session = self._get_session()
                endpoint = f"{self.base_url.rstrip('/')}/orientations/templates/"
                response = session.get(endpoint, headers=self._get_headers(), timeout=10)
                if response.ok:
                    data = response.json()
                    return {"success": True, "data": data.get("data", data)}
            return {"success": True, "data": self.repo.obter_templates()}
        except Exception as e:
            logger.error(f"Erro ao listar templates: {e}")
            return {"success": True, "data": self.repo.obter_templates()}

    def listar_themes(self):
        """Lista temas de orientação disponíveis."""
        try:
            if self._should_use_api():
                session = self._get_session()
                endpoint = f"{self.base_url.rstrip('/')}/orientations/themes/"
                response = session.get(endpoint, headers=self._get_headers(), timeout=10)
                if response.ok:
                    data = response.json()
                    return {"success": True, "data": data.get("data", data)}
            return {"success": True, "data": self.repo.obter_temas()}
        except Exception as e:
            logger.error(f"Erro ao listar themes: {e}")
            return {"success": True, "data": self.repo.obter_temas()}

    def usar_template(self, template_id, student_id=None):
        """Usa um template para preencher campos da orientação."""
        try:
            if self._should_use_api():
                session = self._get_session()
                endpoint = f"{self.base_url.rstrip('/')}/orientations/templates/use/"
                payload = {"template_id": template_id}
                if student_id is not None:
                    payload["student_id"] = student_id
                response = session.post(endpoint, json=payload, headers=self._get_headers(), timeout=15)
                if response.ok:
                    data = response.json()
                    return {"success": True, "data": data.get("data", data)}
                logger.warning(f"Falha ao usar template via API: {response.status_code}")
            return {"success": True, "data": self.repo.usar_template(template_id, student_id)}
        except Exception as e:
            logger.error(f"Erro ao usar template: {e}")
            return {"success": False, "message": str(e)}

    def _detectar_mime_type(self, file_path: str) -> str:
        import mimetypes
        mime, _ = mimetypes.guess_type(file_path)
        return mime or "application/octet-stream"


# Instância global para fácil acesso
servico_orientacoes = ServicoOrientacoes()

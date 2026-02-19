"""
Serviço de Orientações para o Desktop CustomTkinter
Integração com a API do SerPleno Web
"""
import logging
import json
import datetime
from typing import Optional, List, Dict, Any

try:
    import requests
except Exception:
    requests = None  # type: ignore

from services.api import api, get_auth_service

logger = logging.getLogger(__name__)


class ServicoOrientacoes:
    """Serviço para gerenciar orientações via API do SerPleno Web"""
    
    # Presets de modelos rápidos (mesmos do web)
    PRESETS = {
        'study_routine': {
            'label': 'Rotina de Estudo',
            'components': [
                {'id': 'p1', 'type': 'text', 'label': 'Objetivo da Sessão'},
                {'id': 'p2', 'type': 'textarea', 'label': 'Passos/Recomendações'},
                {'id': 'p3', 'type': 'date', 'label': 'Data para Revisão'}
            ]
        },
        'emotional_support': {
            'label': 'Apoio Emocional',
            'components': [
                {'id': 'p4', 'type': 'text', 'label': 'Sintomas/Observações'},
                {'id': 'p5', 'type': 'checkbox', 'label': 'Encaminhar para Atendimento'},
                {'id': 'p6', 'type': 'textarea', 'label': 'Sugestões de Autocuidado'}
            ]
        },
        'follow_up': {
            'label': 'Plano de Acompanhamento',
            'components': [
                {'id': 'p7', 'type': 'text', 'label': 'Meta'},
                {'id': 'p8', 'type': 'date', 'label': 'Prazo'},
                {'id': 'p9', 'type': 'textarea', 'label': 'Responsáveis/Notas'}
            ]
        }
    }
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1/desktop"
    
    def _get_session(self):
        """Retorna a sessão HTTP autenticada"""
        auth = get_auth_service()
        if auth and hasattr(auth, 'get_session'):
            return auth.get_session()
        return requests
    
    def _get_headers(self):
        """Retorna headers com CSRF token se disponível"""
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        auth = get_auth_service()
        if auth:
            # Tenta obter headers do serviço de autenticação
            if hasattr(auth, 'get_headers'):
                return auth.get_headers()
            # Fallback: tenta obter CSRF token diretamente
            if hasattr(auth, 'csrf_token') and auth.csrf_token:
                headers['X-CSRFToken'] = auth.csrf_token
        return headers
    
    def listar_orientacoes(self, id_estudante: Optional[int] = None, tema: Optional[str] = None, pagina: int = 1) -> Dict[str, Any]:
        """
        Lista orientações com filtros opcionais
        
        Args:
            id_estudante: ID do estudante para filtrar
            tema: Tema para buscar
            pagina: Número da página
            
        Returns:
            Dict com success, data (orientations, pagination)
        """
        try:
            params: Dict[str, Any] = {'page': pagina}
            if id_estudante:
                params['student_id'] = id_estudante
            if tema:
                params['theme'] = tema
            
            url = f"{self.base_url}/orientations/"
            session = self._get_session()
            
            if session and requests:
                response = session.get(url, params=params, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        logger.debug(f"Conteúdo da resposta: {response.text[:500] if response.text else 'vazio'}")
                        return self._mock_list_orientacoes(id_estudante)
                else:
                    logger.debug(f"API retornou status {response.status_code}, usando dados mock")
                    return self._mock_list_orientacoes(id_estudante)
            
            return self._mock_list_orientacoes(id_estudante)
            
        except Exception as e:
            logger.exception(f"Erro ao listar orientações: {e}")
            return self._mock_list_orientacoes(id_estudante)
    
    def obter_orientacao(self, id_orientacao: int) -> Dict[str, Any]:
        """
        Obtém detalhes de uma orientação específica
        
        Args:
            id_orientacao: ID da orientação
            
        Returns:
            Dict com success, data (orientação completa)
        """
        try:
            url = f"{self.base_url}/orientations/{id_orientacao}/"
            session = self._get_session()
            
            if session and requests:
                response = session.get(url, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return {"success": False, "message": "Resposta inválida do servidor"}
                else:
                    logger.warning(f"Erro ao obter orientação: {response.status_code}")
                    return {"success": False, "message": "Orientação não encontrada"}
            
            return {"success": False, "message": "Serviço não disponível"}
            
        except Exception as e:
            logger.exception(f"Erro ao obter orientação: {e}")
            return {"success": False, "message": str(e)}
    
    def criar_orientacao(self, dados: Dict[str, Any], arquivos: Optional[List] = None) -> Dict[str, Any]:
        """
        Cria uma nova orientação
        
        Args:
            dados: Dict com os dados da orientação:
                - student_id: ID do estudante (obrigatório)
                - title: Título da orientação
                - theme: Tema/categoria
                - session_date: Data da sessão (YYYY-MM-DD)
                - content: Conteúdo em texto/markdown
                - is_markdown: Se o conteúdo é markdown
                - motivational_message: Mensagem motivacional
                - action_plan: Lista de tarefas (JSON)
            arquivos: Lista de arquivos para anexar
            
        Returns:
            Dict com success, message, data (id da orientação criada)
        """
        try:
            url = f"{self.base_url}/orientations/create/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                # Preparar dados para envio
                if arquivos:
                    # Multipart/form-data para upload de arquivos
                    files: Dict[str, tuple] = {}
                    for i, arquivo in enumerate(arquivos):
                        if hasattr(arquivo, 'read'):
                            files[f'file_{i}'] = (arquivo.name, arquivo.read(), 'application/octet-stream')
                    
                    response = session.post(
                        url, 
                        data=dados, 
                        files=files if files else None,
                        headers=headers,
                        timeout=15
                    )
                else:
                    # JSON simples
                    response = session.post(
                        url, 
                        json=dados,
                        headers=headers,
                        timeout=10
                    )
                
                if response.ok:
                    try:
                        result = response.json()
                        logger.info(f"Orientação criada com sucesso: {result}")
                        return result
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return {"success": False, "message": "Resposta inválida do servidor"}
                else:
                    logger.warning(f"Erro ao criar orientação: {response.status_code} - {response.text}")
                    return {"success": False, "message": f"Erro ao salvar: {response.status_code}"}
            
            # Mock response
            return {
                "success": True, 
                "message": "Orientação criada com sucesso (mock)",
                "data": {"id": 999}
            }
            
        except Exception as e:
            logger.exception(f"Erro ao criar orientação: {e}")
            return {"success": False, "message": f"Erro de conexão: {str(e)}"}
    
    def atualizar_orientacao(self, id_orientacao: int, dados: Dict[str, Any], arquivos: Optional[List] = None) -> Dict[str, Any]:
        """
        Atualiza uma orientação existente
        
        Args:
            id_orientacao: ID da orientação a ser atualizada
            dados: Dict com os dados da orientação:
                - title: Título da orientação
                - theme: Tema/categoria
                - session_date: Data da sessão (YYYY-MM-DD)
                - content: Conteúdo em texto/markdown
                - is_markdown: Se o conteúdo é markdown
                - motivational_message: Mensagem motivacional
                - action_plan: Lista de tarefas (JSON)
            arquivos: Lista de arquivos para anexar
            
        Returns:
            Dict com success, message, data (orientação atualizada)
        """
        try:
            url = f"{self.base_url}/orientations/{id_orientacao}/update/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                # Preparar dados para envio
                if arquivos:
                    # Multipart/form-data para upload de arquivos
                    files: Dict[str, tuple] = {}
                    for i, arquivo in enumerate(arquivos):
                        if hasattr(arquivo, 'read'):
                            files[f'file_{i}'] = (arquivo.name, arquivo.read(), 'application/octet-stream')
                    
                    response = session.put(
                        url, 
                        data=dados, 
                        files=files if files else None,
                        headers=headers,
                        timeout=15
                    )
                else:
                    # JSON simples
                    response = session.put(
                        url, 
                        json=dados,
                        headers=headers,
                        timeout=10
                    )
                
                if response.ok:
                    try:
                        result = response.json()
                        logger.info(f"Orientação atualizada com sucesso: {result}")
                        return result
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return {"success": False, "message": "Resposta inválida do servidor"}
                else:
                    logger.warning(f"Erro ao atualizar orientação: {response.status_code} - {response.text}")
                    return {"success": False, "message": f"Erro ao atualizar: {response.status_code}"}
            
            # Mock response
            return {
                "success": True, 
                "message": "Orientação atualizada com sucesso (mock)",
                "data": {"id": id_orientacao, **dados}
            }
            
        except Exception as e:
            logger.exception(f"Erro ao atualizar orientação: {e}")
            return {"success": False, "message": f"Erro de conexão: {str(e)}"}
    
    def deletar_orientacao(self, id_orientacao: int) -> Dict[str, Any]:
        """
        Deleta uma orientação
        
        Args:
            id_orientacao: ID da orientação
            
        Returns:
            Dict com success, message
        """
        try:
            url = f"{self.base_url}/orientations/{id_orientacao}/delete/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                response = session.delete(url, headers=headers, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.warning(f"Resposta não é JSON válido: {json_err}")
                        return {"success": True, "message": "Orientação deletada"}
                else:
                    logger.warning(f"Erro ao deletar orientação: {response.status_code}")
                    return {"success": False, "message": "Erro ao deletar"}
            
            return {"success": True, "message": "Orientação deletada (mock)"}
            
        except Exception as e:
            logger.exception(f"Erro ao deletar orientação: {e}")
            return {"success": False, "message": str(e)}
    
    def get_preset(self, chave: str) -> Optional[Dict]:
        """Retorna um preset específico"""
        return self.PRESETS.get(chave)
    
    def get_presets(self) -> Dict[str, Dict]:
        """Retorna todos os presets disponíveis"""
        return self.PRESETS
    
    def duplicar_orientacao(self, id_orientacao: int, id_estudante: Optional[int] = None) -> Dict[str, Any]:
        """
        Duplica uma orientação existente
        
        Args:
            id_orientacao: ID da orientação a duplicar
            id_estudante: ID do estudante destino (opcional, usa o mesmo se não informado)
            
        Returns:
            Dict com success, message, data (id da nova orientação)
        """
        try:
            url = f"{self.base_url}/orientations/{id_orientacao}/duplicate/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                data = {}
                if id_estudante:
                    data['student_id'] = id_estudante
                
                response = session.post(url, json=data, headers=headers, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return {"success": False, "message": "Resposta inválida do servidor"}
                else:
                    logger.warning(f"Erro ao duplicar orientação: {response.status_code}")
                    return {"success": False, "message": "Erro ao duplicar"}
            
            return {"success": True, "message": "Orientação duplicada (mock)", "data": {"id": 999}}
            
        except Exception as e:
            logger.exception(f"Erro ao duplicar orientação: {e}")
            return {"success": False, "message": str(e)}
    
    def obter_estatisticas(self, id_estudante: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém estatísticas das orientações
        
        Args:
            id_estudante: ID do estudante para filtrar (opcional)
            
        Returns:
            Dict com success, data (total, by_theme, by_month)
        """
        try:
            url = f"{self.base_url}/orientations/stats/"
            session = self._get_session()
            
            params = {}
            if id_estudante:
                params['student_id'] = id_estudante
            
            if session and requests:
                response = session.get(url, params=params, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.warning(f"Resposta não é JSON válido: {json_err}")
                        return self._mock_stats()
                else:
                    logger.warning(f"Erro ao obter estatísticas: {response.status_code}")
                    return self._mock_stats()
            
            return self._mock_stats()
            
        except Exception as e:
            logger.exception(f"Erro ao obter estatísticas: {e}")
            return self._mock_stats()
    
    def _mock_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas mockadas para testes"""
        return {
            'success': True,
            'data': {
                'total': 15,
                'by_theme': [
                    {'theme': 'Organização', 'count': 5},
                    {'theme': 'Ansiedade', 'count': 4},
                    {'theme': 'Motivação', 'count': 3},
                    {'theme': 'Gestão do Tempo', 'count': 2},
                    {'theme': 'Autoestima', 'count': 1}
                ],
                'by_month': [
                    {'month': '2026-02-01', 'count': 5},
                    {'month': '2026-01-01', 'count': 4},
                    {'month': '2025-12-01', 'count': 3},
                    {'month': '2025-11-01', 'count': 2},
                    {'month': '2025-10-01', 'count': 1}
                ]
            }
        }
    
    def _mock_list_orientacoes(self, id_estudante: Optional[int] = None) -> Dict[str, Any]:
        """Retorna dados mockados para testes"""
        mock_orientacoes: List[Dict[str, Any]] = [
            {
                'id': 1,
                'title': 'Planejamento de Estudos Semanal',
                'theme': 'Organização',
                'session_date': '2026-02-15',
                'student': {'id': 1, 'name': 'João Silva'},
                'psychologist': 'Dra. Maria',
                'content': 'Definição de rotina de estudos com foco em matemática',
                'motivational_message': 'Você é capaz de alcançar seus objetivos!',
                'created_at': '2026-02-15T10:30:00',
                'action_plan': [
                    {'text': 'Estudar 2h por dia', 'done': False},
                    {'text': 'Fazer exercícios de revisão', 'done': True}
                ]
            },
            {
                'id': 2,
                'title': 'Técnicas de Controle de Ansiedade',
                'theme': 'Ansiedade',
                'session_date': '2026-02-10',
                'student': {'id': 2, 'name': 'Maria Santos'},
                'psychologist': 'Dra. Maria',
                'content': 'Prática de exercícios de respiração e mindfulness',
                'motivational_message': 'Respire fundo, você está no caminho certo!',
                'created_at': '2026-02-10T14:00:00',
                'action_plan': []
            }
        ]
        
        if id_estudante:
            mock_orientacoes = [o for o in mock_orientacoes if isinstance(o.get('student'), dict) and o['student'].get('id') == id_estudante]
        
        return {
            'success': True,
            'data': {
                'orientations': mock_orientacoes,
                'pagination': {'page': 1, 'total': len(mock_orientacoes)}
            }
        }


# Instância global para fácil acesso
servico_orientacoes = ServicoOrientacoes()

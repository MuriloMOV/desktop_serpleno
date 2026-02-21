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

from config.db_config import get_db_connection
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
        self._operation_config = None
    
    def _get_operation_config(self):
        """Obtém configuração de operação (lazy loading)"""
        if self._operation_config is None:
            try:
                from config.operation_mode import get_operation_config
                self._operation_config = get_operation_config()
            except Exception:
                pass
        return self._operation_config
    
    def _should_use_api(self) -> bool:
        """Verifica se deve tentar usar a API"""
        config = self._get_operation_config()
        if config is None:
            return True  # Comportamento padrão: tentar API
        return config.should_use_api()
    
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
        # Em modo independente, usa diretamente o banco local
        if not self._should_use_api():
            logger.info("Modo independente: usando banco local diretamente para orientações")
            return self._mock_list_orientacoes(id_estudante)
        
        try:
            params: Dict[str, Any] = {'page': pagina}
            if id_estudante:
                params['student_id'] = id_estudante
            if tema:
                params['theme'] = tema
            
            url = f"{self.base_url}/orientations/"
            session = self._get_session()
            
            if session and requests:
                try:
                    response = session.get(url, params=params, timeout=10)
                    if response.ok:
                        try:
                            return response.json()
                        except Exception as json_err:
                            logger.debug(f"Resposta não é JSON válido: {json_err}")
                            logger.debug(f"Conteúdo da resposta: {response.text[:500] if response.text else 'vazio'}")
                            return self._mock_list_orientacoes(id_estudante)
                    else:
                        logger.debug(f"API retornou status {response.status_code}, usando banco local")
                        return self._mock_list_orientacoes(id_estudante)
                except Exception as conn_err:
                    logger.warning(f"Erro de conexão com API: {conn_err}, usando banco local")
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
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_obter_orientacao(id_orientacao)
        
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
                        # Fallback para banco local
                        return self._local_obter_orientacao(id_orientacao)
                else:
                    logger.warning(f"Erro ao obter orientação via API: {response.status_code}")
                    # Fallback para banco local
                    return self._local_obter_orientacao(id_orientacao)
            
            # Fallback para banco local
            return self._local_obter_orientacao(id_orientacao)
            
        except Exception as e:
            logger.exception(f"Erro ao obter orientação: {e}")
            # Fallback para banco local
            return self._local_obter_orientacao(id_orientacao)
    
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
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_criar_orientacao(dados)
        
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
                        logger.info(f"Orientação criada com sucesso via API: {result}")
                        return result
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        # Fallback para banco local
                        return self._local_criar_orientacao(dados)
                else:
                    logger.warning(f"Erro ao criar orientação via API: {response.status_code} - {response.text}")
                    # Fallback para banco local
                    return self._local_criar_orientacao(dados)
            
            # Fallback para banco local
            return self._local_criar_orientacao(dados)
            
        except Exception as e:
            logger.exception(f"Erro ao criar orientação: {e}")
            # Fallback para banco local
            return self._local_criar_orientacao(dados)
    
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
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_atualizar_orientacao(id_orientacao, dados)
        
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
                        logger.info(f"Orientação atualizada com sucesso via API: {result}")
                        return result
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        # Fallback para banco local
                        return self._local_atualizar_orientacao(id_orientacao, dados)
                else:
                    logger.warning(f"Erro ao atualizar orientação via API: {response.status_code} - {response.text}")
                    # Fallback para banco local
                    return self._local_atualizar_orientacao(id_orientacao, dados)
            
            # Fallback para banco local
            return self._local_atualizar_orientacao(id_orientacao, dados)
            
        except Exception as e:
            logger.exception(f"Erro ao atualizar orientação: {e}")
            # Fallback para banco local
            return self._local_atualizar_orientacao(id_orientacao, dados)
    
    def deletar_orientacao(self, id_orientacao: int) -> Dict[str, Any]:
        """
        Deleta uma orientação
        
        Args:
            id_orientacao: ID da orientação
            
        Returns:
            Dict com success, message
        """
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_deletar_orientacao(id_orientacao)
        
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
                        # Fallback para banco local
                        return self._local_deletar_orientacao(id_orientacao)
                else:
                    logger.warning(f"Erro ao deletar orientação via API: {response.status_code}")
                    # Fallback para banco local
                    return self._local_deletar_orientacao(id_orientacao)
            
            # Fallback para banco local
            return self._local_deletar_orientacao(id_orientacao)
            
        except Exception as e:
            logger.exception(f"Erro ao deletar orientação: {e}")
            # Fallback para banco local
            return self._local_deletar_orientacao(id_orientacao)
    
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
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_duplicar_orientacao(id_orientacao, id_estudante)
        
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
                        # Fallback para banco local
                        return self._local_duplicar_orientacao(id_orientacao, id_estudante)
                else:
                    logger.warning(f"Erro ao duplicar orientação via API: {response.status_code}")
                    # Fallback para banco local
                    return self._local_duplicar_orientacao(id_orientacao, id_estudante)
            
            # Fallback para banco local
            return self._local_duplicar_orientacao(id_orientacao, id_estudante)
            
        except Exception as e:
            logger.exception(f"Erro ao duplicar orientação: {e}")
            # Fallback para banco local
            return self._local_duplicar_orientacao(id_orientacao, id_estudante)
    
    def obter_estatisticas(self, id_estudante: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém estatísticas das orientações
        
        Args:
            id_estudante: ID do estudante para filtrar (opcional)
            
        Returns:
            Dict com success, data (total, by_theme, by_month)
        """
        # Em modo independente, usa diretamente o banco local
        if not self._should_use_api():
            logger.info("Modo independente: usando banco local para estatísticas de orientações")
            return self._mock_stats()
        
        try:
            url = f"{self.base_url}/orientations/stats/"
            session = self._get_session()
            
            params = {}
            if id_estudante:
                params['student_id'] = id_estudante
            
            if session and requests:
                try:
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
                except Exception as conn_err:
                    logger.warning(f"Erro de conexão com API: {conn_err}, usando banco local")
                    return self._mock_stats()
            
            return self._mock_stats()
            
        except Exception as e:
            logger.exception(f"Erro ao obter estatísticas: {e}")
            return self._mock_stats()
    
    def _mock_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Total de orientações
            cursor.execute("SELECT COUNT(*) as total FROM desktop_orientation")
            total = cursor.fetchone()['total']
            
            # Por tema
            cursor.execute("""
                SELECT theme, COUNT(*) as count 
                FROM desktop_orientation 
                GROUP BY theme 
                ORDER BY count DESC
            """)
            by_theme = [{'theme': r['theme'] or 'Sem tema', 'count': r['count']} for r in cursor.fetchall()]
            
            # Por mês
            cursor.execute("""
                SELECT DATE_FORMAT(session_date, '%Y-%m-01') as month, COUNT(*) as count 
                FROM desktop_orientation 
                GROUP BY DATE_FORMAT(session_date, '%Y-%m-01')
                ORDER BY month DESC
                LIMIT 12
            """)
            by_month = [{'month': r['month'], 'count': r['count']} for r in cursor.fetchall()]
            
            connection.close()
            
            return {
                'success': True,
                'data': {
                    'total': total,
                    'by_theme': by_theme,
                    'by_month': by_month
                }
            }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas locais: {e}")
            return {
                'success': True,
                'data': {
                    'total': 0,
                    'by_theme': [],
                    'by_month': []
                }
            }
    
    def _mock_list_orientacoes(self, id_estudante: Optional[int] = None) -> Dict[str, Any]:
        """Retorna dados do banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT o.*, a.nome as student_name, a.id as student_id
                FROM desktop_orientation o
                LEFT JOIN aluno a ON o.student_id = a.id
                WHERE 1=1
            """
            params = []
            
            if id_estudante:
                query += " AND o.student_id = %s"
                params.append(id_estudante)
            
            # Ordenar por data decrescente, sem limite
            query += " ORDER BY o.session_date DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            orientacoes = []
            for r in rows:
                orientacoes.append({
                    'id': r.get('id'),
                    'title': r.get('title'),
                    'theme': r.get('theme'),
                    'session_date': str(r.get('session_date')) if r.get('session_date') else None,
                    'student': {'id': r.get('student_id'), 'name': r.get('student_name') or 'Estudante'},
                    'psychologist': r.get('psychologist'),
                    'content': r.get('content'),
                    'motivational_message': r.get('motivational_message'),
                    'created_at': str(r.get('created_at')) if r.get('created_at') else None,
                    'action_plan': json.loads(r.get('action_plan', '[]')) if r.get('action_plan') else []
                })
            
            total = len(orientacoes)
            logger.info(f"Encontradas {total} orientações no banco de dados local")
            connection.close()
            
            return {
                'success': True,
                'data': {
                    'orientations': orientacoes,
                    'pagination': {'page': 1, 'total': total, 'total_pages': 1}
                }
            }
        except Exception as e:
            logger.error(f"Erro ao listar orientações locais: {e}")
            return {
                'success': True,
                'data': {
                    'orientations': [],
                    'pagination': {'page': 1, 'total': 0}
                }
            }
    
    def _local_criar_orientacao(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Cria orientação no banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = """
                INSERT INTO desktop_orientation (
                    student_id, title, theme, session_date, content, 
                    is_markdown, motivational_message, action_plan, 
                    psychologist, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            
            action_plan_json = json.dumps(dados.get('action_plan', [])) if dados.get('action_plan') else '[]'
            
            cursor.execute(query, (
                dados.get('student_id'),
                dados.get('title'),
                dados.get('theme'),
                dados.get('session_date'),
                dados.get('content'),
                dados.get('is_markdown', False),
                dados.get('motivational_message'),
                action_plan_json,
                dados.get('psychologist', 'Equipe SerPleno')
            ))
            
            connection.commit()
            orientacao_id = cursor.lastrowid
            connection.close()
            
            # Adiciona à fila de sincronização
            try:
                from services.sync_service import queue_sync
                queue_sync('create', 'orientations', orientacao_id, dados)
            except Exception:
                pass
            
            return {"success": True, "message": "Orientação criada com sucesso", "data": {"id": orientacao_id}}
        except Exception as e:
            logger.error(f"Erro ao criar orientação local: {e}")
            return {"success": False, "message": str(e)}
    
    def _local_atualizar_orientacao(self, id_orientacao: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza orientação no banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            action_plan_json = json.dumps(dados.get('action_plan', [])) if dados.get('action_plan') else '[]'
            
            query = """
                UPDATE desktop_orientation 
                SET title = %s, theme = %s, session_date = %s, content = %s,
                    is_markdown = %s, motivational_message = %s, action_plan = %s,
                    psychologist = %s, updated_at = NOW()
                WHERE id = %s
            """
            
            cursor.execute(query, (
                dados.get('title'),
                dados.get('theme'),
                dados.get('session_date'),
                dados.get('content'),
                dados.get('is_markdown', False),
                dados.get('motivational_message'),
                action_plan_json,
                dados.get('psychologist'),
                id_orientacao
            ))
            
            connection.commit()
            connection.close()
            
            # Adiciona à fila de sincronização
            try:
                from services.sync_service import queue_sync
                queue_sync('update', 'orientations', id_orientacao, dados)
            except Exception:
                pass
            
            return {"success": True, "message": "Orientação atualizada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao atualizar orientação local: {e}")
            return {"success": False, "message": str(e)}
    
    def _local_deletar_orientacao(self, id_orientacao: int) -> Dict[str, Any]:
        """Deleta orientação no banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM desktop_orientation WHERE id = %s", (id_orientacao,))
            connection.commit()
            connection.close()
            
            # Adiciona à fila de sincronização
            try:
                from services.sync_service import queue_sync
                queue_sync('delete', 'orientations', id_orientacao, {})
            except Exception:
                pass
            
            return {"success": True, "message": "Orientação deletada com sucesso"}
        except Exception as e:
            logger.error(f"Erro ao deletar orientação local: {e}")
            return {"success": False, "message": str(e)}
    
    def _local_duplicar_orientacao(self, id_orientacao: int, id_estudante: Optional[int] = None) -> Dict[str, Any]:
        """Duplica orientação no banco local"""
        try:
            # Primeiro, obtém a orientação original
            orientacao_resp = self._local_obter_orientacao(id_orientacao)
            if not orientacao_resp.get('success'):
                return {"success": False, "message": "Orientação original não encontrada"}
            
            orientacao = orientacao_resp.get('data', {})
            
            # Cria uma nova orientação com os mesmos dados
            novos_dados = {
                'student_id': id_estudante or orientacao.get('student', {}).get('id'),
                'title': f"Cópia - {orientacao.get('title', 'Orientação')}",
                'theme': orientacao.get('theme'),
                'session_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'content': orientacao.get('content'),
                'is_markdown': orientacao.get('is_markdown', False),
                'motivational_message': orientacao.get('motivational_message'),
                'action_plan': orientacao.get('action_plan', [])
            }
            
            return self._local_criar_orientacao(novos_dados)
        except Exception as e:
            logger.error(f"Erro ao duplicar orientação local: {e}")
            return {"success": False, "message": str(e)}
    
    def _local_obter_orientacao(self, id_orientacao: int) -> Dict[str, Any]:
        """Obtém orientação do banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT o.*, a.nome as student_name, a.id as student_id
                FROM desktop_orientation o
                LEFT JOIN aluno a ON o.student_id = a.id
                WHERE o.id = %s
            """
            cursor.execute(query, (id_orientacao,))
            r = cursor.fetchone()
            connection.close()
            
            if not r:
                return {"success": False, "message": "Orientação não encontrada"}
            
            orientacao = {
                'id': r.get('id'),
                'title': r.get('title'),
                'theme': r.get('theme'),
                'session_date': str(r.get('session_date')) if r.get('session_date') else None,
                'student': {'id': r.get('student_id'), 'name': r.get('student_name') or 'Estudante'},
                'psychologist': r.get('psychologist'),
                'content': r.get('content'),
                'is_markdown': bool(r.get('is_markdown')),
                'motivational_message': r.get('motivational_message'),
                'created_at': str(r.get('created_at')) if r.get('created_at') else None,
                'updated_at': str(r.get('updated_at')) if r.get('updated_at') else None,
                'action_plan': json.loads(r.get('action_plan', '[]')) if r.get('action_plan') else []
            }
            
            return {"success": True, "data": orientacao}
        except Exception as e:
            logger.error(f"Erro ao obter orientação local: {e}")
            return {"success": False, "message": str(e)}


# Instância global para fácil acesso
servico_orientacoes = ServicoOrientacoes()

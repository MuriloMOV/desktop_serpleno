"""
Serviço de Mural para o Desktop CustomTkinter
Funciona de forma independente com sincronização opcional com a API do SerPleno Web
"""
import os
import json
import logging
import datetime
from typing import Optional, List, Dict, Any

try:
    import requests
except Exception:
    requests = None  # type: ignore

from config.db_config import get_db_connection
from config.config import MURAL_API_URL

logger = logging.getLogger(__name__)


class ServicoMural:
    """Serviço para gerenciar mural de avisos via API do SerPleno Web ou banco local"""
    
    def __init__(self):
        self.base_url = MURAL_API_URL
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
        try:
            from services.api import get_auth_service
            auth = get_auth_service()
            if auth and hasattr(auth, 'get_session'):
                return auth.get_session()
        except Exception:
            pass
        return requests
    
    def _get_headers(self):
        """Retorna headers com CSRF token se disponível"""
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        try:
            from services.api import get_auth_service
            auth = get_auth_service()
            if auth:
                if hasattr(auth, 'get_headers'):
                    return auth.get_headers()
                if hasattr(auth, 'csrf_token') and auth.csrf_token:
                    headers['X-CSRFToken'] = auth.csrf_token
        except Exception:
            pass
        return headers

    def listar_mensagens(self, busca: Optional[str] = None, pagina: int = 1) -> Dict[str, Any]:
        """
        Lista mensagens do mural com filtros opcionais
        
        Args:
            busca: Termo para buscar nos campos título, conteúdo e autor
            pagina: Número da página
            
        Returns:
            Dict com success, data (mensagens)
        """
        # Em modo independente, usa diretamente o banco local
        if not self._should_use_api():
            logger.info("Modo independente: usando banco local diretamente para mural")
            return self._local_listar_mensagens(busca, pagina)
        
        try:
            url = f"{self.base_url}/"
            session = self._get_session()
            
            params: Dict[str, Any] = {'page': pagina}
            if busca:
                params['search'] = busca
            
            if session and requests:
                try:
                    response = session.get(url, params=params, timeout=10)
                    if response.ok:
                        try:
                            return response.json()
                        except Exception as json_err:
                            logger.debug(f"Resposta não é JSON válido: {json_err}")
                            return self._local_listar_mensagens(busca, pagina)
                    else:
                        logger.debug(f"API retornou status {response.status_code}, usando banco local")
                        return self._local_listar_mensagens(busca, pagina)
                except Exception as conn_err:
                    logger.warning(f"Erro de conexão com API: {conn_err}, usando banco local")
                    return self._local_listar_mensagens(busca, pagina)
            
            return self._local_listar_mensagens(busca, pagina)
            
        except Exception as e:
            logger.exception(f"Erro ao listar mensagens: {e}")
            return self._local_listar_mensagens(busca, pagina)
    
    def obter_mensagem(self, mensagem_id: int) -> Dict[str, Any]:
        """
        Obtém detalhes de uma mensagem específica
        
        Args:
            mensagem_id: ID da mensagem
            
        Returns:
            Dict com success, data (mensagem completa)
        """
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_obter_mensagem(mensagem_id)
        
        try:
            url = f"{self.base_url}/{mensagem_id}/"
            session = self._get_session()
            
            if session and requests:
                response = session.get(url, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return self._local_obter_mensagem(mensagem_id)
                else:
                    logger.warning(f"Erro ao obter mensagem via API: {response.status_code}")
                    return self._local_obter_mensagem(mensagem_id)
            
            return self._local_obter_mensagem(mensagem_id)
            
        except Exception as e:
            logger.exception(f"Erro ao obter mensagem: {e}")
            return self._local_obter_mensagem(mensagem_id)
    
    def criar_mensagem(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma nova mensagem no mural
        
        Args:
            dados: Dict com os dados da mensagem:
                - titulo: Título da mensagem (obrigatório)
                - conteudo: Conteúdo da mensagem
                - autor: Autor da mensagem
                - categoria: Categoria (informativo, aviso, aula, urgente, evento)
                - local_fisico: Local físico (opcional)
                - link_externo: Link externo (opcional)
                - data_agendamento: Data de agendamento (opcional)
                - horario_evento: Horário do evento (opcional)
                - layout: Layout (single, grid-2, grid-3, grid-4)
                - blocos: Lista de blocos (para layouts grid)
                - ativo: Se está ativo
                
        Returns:
            Dict com success, message, data (id da mensagem criada)
        """
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_criar_mensagem(dados)
        
        try:
            url = f"{self.base_url}/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                response = session.post(url, json=dados, headers=headers, timeout=10)
                
                if response.ok:
                    try:
                        result = response.json()
                        logger.info(f"Mensagem criada com sucesso via API: {result}")
                        return result
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return self._local_criar_mensagem(dados)
                else:
                    logger.warning(f"Erro ao criar mensagem via API: {response.status_code} - {response.text}")
                    return self._local_criar_mensagem(dados)
            
            return self._local_criar_mensagem(dados)
            
        except Exception as e:
            logger.exception(f"Erro ao criar mensagem: {e}")
            return self._local_criar_mensagem(dados)
    
    def atualizar_mensagem(self, mensagem_id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza uma mensagem existente
        
        Args:
            mensagem_id: ID da mensagem a ser atualizada
            dados: Dict com os dados da mensagem
                
        Returns:
            Dict com success, message, data (mensagem atualizada)
        """
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_atualizar_mensagem(mensagem_id, dados)
        
        try:
            url = f"{self.base_url}/{mensagem_id}/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                response = session.put(url, json=dados, headers=headers, timeout=10)
                
                if response.ok:
                    try:
                        result = response.json()
                        logger.info(f"Mensagem atualizada com sucesso via API: {result}")
                        return result
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return self._local_atualizar_mensagem(mensagem_id, dados)
                else:
                    logger.warning(f"Erro ao atualizar mensagem via API: {response.status_code} - {response.text}")
                    return self._local_atualizar_mensagem(mensagem_id, dados)
            
            return self._local_atualizar_mensagem(mensagem_id, dados)
            
        except Exception as e:
            logger.exception(f"Erro ao atualizar mensagem: {e}")
            return self._local_atualizar_mensagem(mensagem_id, dados)
    
    def deletar_mensagem(self, mensagem_id: int) -> Dict[str, Any]:
        """
        Deleta uma mensagem
        
        Args:
            mensagem_id: ID da mensagem
            
        Returns:
            Dict com success, message
        """
        # Verificar se deve usar o banco local
        if not self._should_use_api():
            return self._local_deletar_mensagem(mensagem_id)
        
        try:
            url = f"{self.base_url}/{mensagem_id}/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                response = session.delete(url, headers=headers, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.warning(f"Resposta não é JSON válido: {json_err}")
                        return self._local_deletar_mensagem(mensagem_id)
                else:
                    logger.warning(f"Erro ao deletar mensagem via API: {response.status_code}")
                    return self._local_deletar_mensagem(mensagem_id)
            
            return self._local_deletar_mensagem(mensagem_id)
            
        except Exception as e:
            logger.exception(f"Erro ao deletar mensagem: {e}")
            return self._local_deletar_mensagem(mensagem_id)
    
    def upload_attachment(self, filepath: str) -> Dict[str, Any]:
        """Upload de arquivo - para desktop, retorna caminho local"""
        filename = os.path.basename(filepath)
        return {'url': filepath, 'name': filename}
    
    # ----------------------- Métodos locais (banco de dados) -----------------------
    
    def _local_listar_mensagens(self, busca: Optional[str] = None, pagina: int = 1) -> Dict[str, Any]:
        """Retorna mensagens do banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT * FROM mural_posts WHERE ativo = 1"
            params = []
            
            if busca:
                query += " AND (titulo LIKE %s OR conteudo LIKE %s OR autor LIKE %s)"
                params.extend([f"%{busca}%", f"%{busca}%", f"%{busca}%"])
                
            offset = (pagina - 1) * 10
            query += " ORDER BY publicado_em DESC LIMIT 10 OFFSET %s"
            params.append(offset)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            mensagens = []
            for r in rows:
                mensagens.append(self._formatar_mensagem(r))
                
            connection.close()
            return {"success": True, "data": mensagens}
            
        except Exception as e:
            logger.error(f"Erro ao listar mensagens locais: {e}")
            return {"success": True, "data": []}
    
    def _local_obter_mensagem(self, mensagem_id: int) -> Dict[str, Any]:
        """Obtém mensagem do banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("SELECT * FROM mural_posts WHERE id = %s", (mensagem_id,))
            r = cursor.fetchone()
            connection.close()
            
            if not r:
                return {"success": False, "message": "Mensagem não encontrada"}
            
            return {"success": True, "data": self._formatar_mensagem(r)}
            
        except Exception as e:
            logger.error(f"Erro ao obter mensagem local: {e}")
            return {"success": False, "message": str(e)}
    
    def _local_criar_mensagem(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Cria mensagem no banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = """
                INSERT INTO mural_posts (
                    titulo, conteudo, autor, publicado_em, ativo, categoria,
                    data_agendamento, link_externo, blocos, layout, horario_evento, local_fisico,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, NOW(), 1, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            cursor.execute(query, (
                dados.get('titulo', ''),
                dados.get('conteudo', ''),
                dados.get('autor', 'Admin'),
                dados.get('categoria', 'informativo'),
                dados.get('data_agendamento'),
                dados.get('link_externo'),
                json.dumps(dados.get('blocos', [])),
                dados.get('layout', 'single'),
                dados.get('horario_evento'),
                dados.get('local_fisico')
            ))
            connection.commit()
            mensagem_id = cursor.lastrowid
            connection.close()
            
            # Adiciona à fila de sincronização
            try:
                from services.sync_service import queue_sync
                queue_sync('create', 'mural', mensagem_id, dados)
            except Exception:
                pass
            
            return {"success": True, "message": "Mensagem criada com sucesso", "data": {"id": mensagem_id}}
            
        except Exception as e:
            logger.error(f"Erro ao criar mensagem local: {e}")
            return {"success": False, "message": str(e)}
    
    def _local_atualizar_mensagem(self, mensagem_id: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza mensagem no banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            query = """
                UPDATE mural_posts 
                SET titulo = %s, conteudo = %s, autor = %s, categoria = %s,
                    data_agendamento = %s, link_externo = %s, blocos = %s,
                    layout = %s, horario_evento = %s, local_fisico = %s,
                    ativo = %s, updated_at = NOW()
                WHERE id = %s
            """
            cursor.execute(query, (
                dados.get('titulo'),
                dados.get('conteudo'),
                dados.get('autor'),
                dados.get('categoria', 'informativo'),
                dados.get('data_agendamento'),
                dados.get('link_externo'),
                json.dumps(dados.get('blocos', [])),
                dados.get('layout', 'single'),
                dados.get('horario_evento'),
                dados.get('local_fisico'),
                dados.get('ativo', True),
                mensagem_id
            ))
            
            connection.commit()
            connection.close()
            
            # Adiciona à fila de sincronização
            try:
                from services.sync_service import queue_sync
                queue_sync('update', 'mural', mensagem_id, dados)
            except Exception:
                pass
            
            return {"success": True, "message": "Mensagem atualizada com sucesso"}
            
        except Exception as e:
            logger.error(f"Erro ao atualizar mensagem local: {e}")
            return {"success": False, "message": str(e)}
    
    def _local_deletar_mensagem(self, mensagem_id: int) -> Dict[str, Any]:
        """Deleta mensagem no banco local"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            # Em vez de deletar, marca como inativo
            cursor.execute("UPDATE mural_posts SET ativo = 0 WHERE id = %s", (mensagem_id,))
            connection.commit()
            connection.close()
            
            # Adiciona à fila de sincronização
            try:
                from services.sync_service import queue_sync
                queue_sync('delete', 'mural', mensagem_id, {})
            except Exception:
                pass
            
            return {"success": True, "message": "Mensagem deletada com sucesso"}
            
        except Exception as e:
            logger.error(f"Erro ao deletar mensagem local: {e}")
            return {"success": False, "message": str(e)}
    
    def _formatar_mensagem(self, r: Dict) -> Dict[str, Any]:
        """Formata uma linha do banco em formato de mensagem"""
        return {
            'id': r.get('id'),
            'titulo': r.get('titulo'),
            'conteudo': r.get('conteudo'),
            'autor': r.get('autor'),
            'publicado_em': str(r.get('publicado_em')) if r.get('publicado_em') else None,
            'ativo': bool(r.get('ativo')),
            'categoria': r.get('categoria'),
            'data_agendamento': str(r.get('data_agendamento')) if r.get('data_agendamento') else None,
            'link_externo': r.get('link_externo'),
            'blocos': json.loads(r.get('blocos', '[]')) if r.get('blocos') else [],
            'layout': r.get('layout'),
            'horario_evento': str(r.get('horario_evento')) if r.get('horario_evento') else None,
            'local_fisico': r.get('local_fisico')
        }


# Instância global para fácil acesso
servico_mural = ServicoMural()

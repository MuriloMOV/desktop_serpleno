"""
Serviço de Configurações do Sistema
Gerencia preferências do usuário, teste de conexão e sincronização.
"""
import os
import json
import threading
from datetime import datetime
from typing import Optional, Dict, Any, Callable
import requests

from config.db_config import get_db_connection
from config.settings import settings


class ServicoConfiguracoes:
    """Serviço para gerenciar configurações do sistema."""
    
    def __init__(self):
        self.base_url = settings.api.base_url
        self.timeout = settings.api.timeout
        self._config_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # 5 minutos
    
    def obter_configuracoes(self, usuario_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtém configurações do sistema e preferências do usuário.
        
        Args:
            usuario_id: ID do usuário para buscar preferências específicas
            
        Returns:
            Dict com configurações e preferências
        """
        # Verificar cache
        if self._config_cache and self._cache_timestamp:
            elapsed = (datetime.now() - self._cache_timestamp).total_seconds()
            if elapsed < self._cache_ttl:
                return self._config_cache
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Buscar configurações globais
            cursor.execute("SELECT * FROM system_config LIMIT 1")
            config_global = cursor.fetchone()
            
            # Buscar preferências do usuário
            preferencias = {}
            if usuario_id:
                cursor.execute(
                    "SELECT * FROM user_preferences WHERE user_id = %s",
                    (usuario_id,)
                )
                preferencias = cursor.fetchone() or {}
            
            connection.close()
            
            result = {
                "success": True,
                "data": {
                    "global": config_global or {},
                    "preferencias": preferencias
                }
            }
            
            # Atualizar cache
            self._config_cache = result
            self._cache_timestamp = datetime.now()
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {"global": {}, "preferencias": {}}
            }
    
    def atualizar_configuracoes(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza configurações do usuário.
        
        Args:
            dados: Dicionário com theme, notifications, user_id, etc.
            
        Returns:
            Dict com resultado da operação
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Verificar se já existe registro
            cursor.execute(
                "SELECT id FROM user_preferences WHERE user_id = %s",
                (dados['user_id'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                query = """
                    UPDATE user_preferences 
                    SET theme = %s, notifications = %s, updated_at = NOW()
                    WHERE user_id = %s
                """
                cursor.execute(query, (
                    dados.get('theme', 'light'),
                    json.dumps(dados.get('notifications', {})),
                    dados['user_id']
                ))
            else:
                query = """
                    INSERT INTO user_preferences (user_id, theme, notifications, created_at)
                    VALUES (%s, %s, %s, NOW())
                """
                cursor.execute(query, (
                    dados['user_id'],
                    dados.get('theme', 'light'),
                    json.dumps(dados.get('notifications', {}))
                ))
            
            connection.commit()
            connection.close()
            
            # Invalidar cache
            self._config_cache = None
            
            return {"success": True, "message": "Configurações atualizadas com sucesso"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def testar_conexao_api(self) -> Dict[str, Any]:
        """
        Testa conexão com a API do servidor.
        
        Returns:
            Dict com status da conexão
        """
        try:
            start_time = datetime.now()
            response = requests.get(
                f"{self.base_url}/health/",
                timeout=self.timeout
            )
            end_time = datetime.now()
            
            latency_ms = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": "online",
                    "latency_ms": round(latency_ms, 2),
                    "server_info": data.get("info", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "status_code": response.status_code,
                    "message": f"Servidor retornou status {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "status": "timeout",
                "message": "Tempo de conexão esgotado"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "status": "offline",
                "message": "Não foi possível conectar ao servidor"
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": str(e)
            }
    
    def testar_conexao_banco(self) -> Dict[str, Any]:
        """
        Testa conexão com o banco de dados.
        
        Returns:
            Dict com status da conexão
        """
        try:
            start_time = datetime.now()
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            end_time = datetime.now()
            
            latency_ms = (end_time - start_time).total_seconds() * 1000
            connection.close()
            
            return {
                "success": True,
                "status": "online",
                "latency_ms": round(latency_ms, 2),
                "message": "Conexão com banco de dados estabelecida"
            }
            
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"Erro ao conectar ao banco: {str(e)}"
            }
    
    def obter_status_sincronizacao(self) -> Dict[str, Any]:
        """
        Obtém status atual da sincronização.
        
        Returns:
            Dict com informações de sincronização
        """
        try:
            # Buscar informações de sincronização do arquivo local
            sync_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "sync_status.json"
            )
            
            if os.path.exists(sync_file):
                with open(sync_file, "r") as f:
                    sync_data = json.load(f)
            else:
                sync_data = {
                    "last_sync": None,
                    "pending_items": 0,
                    "conflicts": 0,
                    "status": "never_synced"
                }
            
            return {
                "success": True,
                "data": sync_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {
                    "last_sync": None,
                    "pending_items": 0,
                    "conflicts": 0,
                    "status": "error"
                }
            }
    
    def sincronizar(
        self,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[Dict], None]] = None
    ) -> None:
        """
        Executa sincronização com o servidor em background.
        
        Args:
            on_progress: Callback para progresso (atual, total)
            on_complete: Callback para conclusão com resultado
        """
        def _sync_thread():
            try:
                # Importar serviço de sincronização
                from services.sync_service import get_sync_service
                
                sync_service = get_sync_service()
                result = sync_service.sync_now()
                
                # Atualizar arquivo de status
                sync_file = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "sync_status.json"
                )
                
                sync_data = {
                    "last_sync": datetime.now().isoformat(),
                    "pending_items": result.get("items_pending", 0),
                    "items_synced": result.get("items_synced", 0),
                    "conflicts": 0,
                    "status": "synced" if result.get("success") else "error",
                    "api_available": result.get("api_available", False),
                    "last_error": result.get("error")
                }
                
                with open(sync_file, "w") as f:
                    json.dump(sync_data, f, indent=2)
                
                if on_complete:
                    on_complete(result)
                    
            except Exception as e:
                if on_complete:
                    on_complete({
                        "success": False,
                        "error": str(e)
                    })
        
        thread = threading.Thread(target=_sync_thread, daemon=True)
        thread.start()
    
    def resolver_conflitos(self, conflitos: list) -> Dict[str, Any]:
        """
        Resolve conflitos de sincronização.
        
        Args:
            conflitos: Lista de conflitos com resolução escolhida
            
        Returns:
            Dict com resultado da operação
        """
        try:
            # Por enquanto, apenas marca conflitos como resolvidos
            # Em uma implementação completa, integraria com o SyncService
            sync_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "sync_status.json"
            )
            
            if os.path.exists(sync_file):
                with open(sync_file, "r") as f:
                    sync_data = json.load(f)
                sync_data["conflicts"] = 0
                with open(sync_file, "w") as f:
                    json.dump(sync_data, f, indent=2)
            
            return {
                "success": True,
                "message": f"{len(conflitos)} conflitos resolvidos"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def obter_notificacoes_config(self, usuario_id: int) -> Dict[str, Any]:
        """
        Obtém configurações de notificação do usuário.
        
        Args:
            usuario_id: ID do usuário
            
        Returns:
            Dict com configurações de notificação
        """
        # Configurações padrão
        default_notifications = {
            "mensagens_diretas": True,
            "pedidos_ajuda": True,
            "feedback_alunos": True,
            "efeitos_sonoros": False
        }
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(
                "SELECT notifications FROM user_preferences WHERE user_id = %s",
                (usuario_id,)
            )
            result = cursor.fetchone()
            connection.close()
            
            if result:
                # Acessar o valor de forma segura usando get
                try:
                    # mypy/pylance: O cursor com dictionary=True retorna um dict
                    result_dict: Dict[str, Any] = result  # type: ignore
                    notifications_raw = result_dict.get('notifications')
                    
                    if notifications_raw:
                        notifications = json.loads(str(notifications_raw))
                    else:
                        notifications = default_notifications
                except (KeyError, TypeError, json.JSONDecodeError):
                    notifications = default_notifications
            else:
                notifications = default_notifications
            
            return {
                "success": True,
                "data": notifications
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": default_notifications
            }
    
    def atualizar_notificacoes(
        self, 
        usuario_id: int, 
        notificacoes: Dict[str, bool]
    ) -> Dict[str, Any]:
        """
        Atualiza configurações de notificação.
        
        Args:
            usuario_id: ID do usuário
            notificacoes: Dict com tipo -> habilitado
            
        Returns:
            Dict com resultado da operação
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Verificar se já existe registro
            cursor.execute(
                "SELECT id FROM user_preferences WHERE user_id = %s",
                (usuario_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                query = """
                    UPDATE user_preferences 
                    SET notifications = %s, updated_at = NOW()
                    WHERE user_id = %s
                """
                cursor.execute(query, (
                    json.dumps(notificacoes),
                    usuario_id
                ))
            else:
                query = """
                    INSERT INTO user_preferences (user_id, notifications, created_at)
                    VALUES (%s, %s, NOW())
                """
                cursor.execute(query, (
                    usuario_id,
                    json.dumps(notificacoes)
                ))
            
            connection.commit()
            connection.close()
            
            return {"success": True, "message": "Notificações atualizadas"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def obter_info_sistema(self) -> Dict[str, Any]:
        """
        Obtém informações do sistema.
        
        Returns:
            Dict com informações do sistema
        """
        import platform
        import sys
        
        return {
            "success": True,
            "data": {
                "sistema": platform.system(),
                "versao_sistema": platform.version(),
                "arquitetura": platform.architecture()[0],
                "python_versao": sys.version,
                "app_versao": "1.0.0",
                "data_atual": datetime.now().isoformat()
            }
        }
    
    def exportar_configuracoes(self, usuario_id: int) -> Dict[str, Any]:
        """
        Exporta todas as configurações do usuário para backup.
        
        Args:
            usuario_id: ID do usuário
            
        Returns:
            Dict com configurações exportadas
        """
        try:
            config = self.obter_configuracoes(usuario_id)
            notificacoes = self.obter_notificacoes_config(usuario_id)
            
            export_data = {
                "exportado_em": datetime.now().isoformat(),
                "usuario_id": usuario_id,
                "configuracoes": config.get("data", {}),
                "notificacoes": notificacoes.get("data", {})
            }
            
            return {
                "success": True,
                "data": export_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def importar_configuracoes(
        self, 
        usuario_id: int, 
        config_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Importa configurações de um backup.
        
        Args:
            usuario_id: ID do usuário
            config_data: Dados exportados anteriormente
            
        Returns:
            Dict com resultado da operação
        """
        try:
            # Importar preferências
            if "configuracoes" in config_data:
                prefs = config_data["configuracoes"].get("preferencias", {})
                if prefs:
                    self.atualizar_configuracoes({
                        "user_id": usuario_id,
                        "theme": prefs.get("theme", "light"),
                        "notifications": prefs.get("notifications", {})
                    })
            
            # Importar notificações
            if "notificacoes" in config_data:
                self.atualizar_notificacoes(
                    usuario_id,
                    config_data["notificacoes"]
                )
            
            return {
                "success": True,
                "message": "Configurações importadas com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Instância global do serviço
servico_configuracoes = ServicoConfiguracoes()

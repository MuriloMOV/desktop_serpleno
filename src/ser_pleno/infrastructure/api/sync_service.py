"""
Serviço de Sincronização para o Desktop SerPleno

Este módulo gerencia a sincronização de dados entre o desktop e o serpleno_web:
- Verifica disponibilidade da API
- Sincroniza dados quando disponível
- Mantém fila de operações pendentes
- Resolve conflitos de dados
"""
import logging
import json
import os
import threading
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from queue import Queue, Empty

try:
    import requests
except Exception:
    requests = None  # type: ignore

from ser_pleno.config.db_config import get_db_connection
from ser_pleno.config.operation_mode import (
    OperationConfig, OperationMode, get_operation_config, OperationMode
)

logger = logging.getLogger(__name__)


class SyncQueue:
    """Fila de operações pendentes para sincronização"""
    
    QUEUE_FILE = "sync_queue.json"
    
    def __init__(self):
        self._queue: List[Dict[str, Any]] = []
        self._load_queue()
    
    def _get_queue_path(self) -> str:
        """Retorna o caminho do arquivo da fila"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, self.QUEUE_FILE)
    
    def _load_queue(self):
        """Carrega fila do arquivo"""
        queue_path = self._get_queue_path()
        if os.path.exists(queue_path):
            try:
                with open(queue_path, 'r', encoding='utf-8') as f:
                    self._queue = json.load(f)
                logger.info(f"Fila de sincronização carregada: {len(self._queue)} itens")
            except Exception as e:
                logger.warning(f"Erro ao carregar fila de sincronização: {e}")
                self._queue = []
    
    def _save_queue(self):
        """Salva fila no arquivo"""
        queue_path = self._get_queue_path()
        try:
            with open(queue_path, 'w', encoding='utf-8') as f:
                json.dump(self._queue, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar fila de sincronização: {e}")
    
    def add(self, operation: str, entity: str, entity_id: int, data: Dict[str, Any]):
        """Adiciona operação A  fila"""
        item = {
            "id": f"{operation}_{entity}_{entity_id}_{datetime.now().timestamp()}",
            "operation": operation,
            "entity": entity,
            "entity_id": entity_id,
            "data": data,
            "created_at": datetime.now().isoformat(),
            "attempts": 0,
            "last_attempt": None
        }
        self._queue.append(item)
        self._save_queue()
        logger.debug(f"Operação adicionada A  fila: {operation} {entity}#{entity_id}")
    
    def get_pending(self) -> List[Dict[str, Any]]:
        """Retorna itens pendentes"""
        return self._queue.copy()
    
    def remove(self, item_id: str):
        """Remove item da fila"""
        self._queue = [item for item in self._queue if item.get('id') != item_id]
        self._save_queue()
    
    def increment_attempt(self, item_id: str):
        """Incrementa contador de tentativas"""
        for item in self._queue:
            if item.get('id') == item_id:
                item['attempts'] = item.get('attempts', 0) + 1
                item['last_attempt'] = datetime.now().isoformat()
                break
        self._save_queue()
    
    def clear_old(self, max_attempts: int = 5):
        """Remove itens antigos com muitas tentativas"""
        original_len = len(self._queue)
        self._queue = [item for item in self._queue if item.get('attempts', 0) < max_attempts]
        if len(self._queue) < original_len:
            self._save_queue()
            logger.info(f"Removidos {original_len - len(self._queue)} itens antigos da fila")


class SyncService:
    """Serviço de sincronização com serpleno_web"""
    
    # Endpoints de sincronização
    SYNC_ENDPOINTS = {
        'students': '/api/v1/desktop/students/',
        'appointments': '/api/v1/desktop/schedule/appointments/',
        'orientations': '/api/v1/desktop/orientations/',
        'screenings': '/api/v1/desktop/screenings/',
        'messages': '/api/v1/desktop/messages/',
    }
    
    _instance: Optional['SyncService'] = None
    _running: bool = False
    _thread: Optional[threading.Thread] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.config: OperationConfig = get_operation_config()
        self.queue: SyncQueue = SyncQueue()
        self._callbacks: Dict[str, List[Callable]] = {}
        self._session = requests.Session() if requests else None
    
    def check_api_availability(self) -> bool:
        """Verifica se a API do serpleno_web está disponível"""
        if not requests:
            return False
        
        try:
            url = f"{self.config.api_base_url}/api/v1/desktop/health/"
            response = self._session.get(url, timeout=self.config.api_timeout)
            available = response.status_code == 200
            self.config.set_api_available(available)
            return available
        except Exception as e:
            logger.debug(f"API indisponível: {e}")
            self.config.set_api_available(False)
            return False
    
    def start_background_sync(self):
        """Inicia sincronização em background"""
        if self._running:
            logger.warning("Sincronização já está rodando")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()
        logger.info("Sincronização em background iniciada")
    
    def stop_background_sync(self):
        """Para sincronização em background"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Sincronização em background parada")
    
    def _sync_loop(self):
        """Loop principal de sincronização"""
        while self._running:
            try:
                # Verifica disponibilidade da API
                if self.check_api_availability():
                    # Processa fila pendente
                    self._process_queue()
                    
                    # Sincroniza dados locais
                    if self.config.should_sync():
                        self._sync_local_data()
                
                # Aguarda próximo ciclo
                time.sleep(self.config.sync_interval)
                
            except Exception as e:
                logger.error(f"Erro no loop de sincronização: {e}")
                time.sleep(60)  # Aguarda 1 minuto em caso de erro
    
    def _process_queue(self):
        """Processa fila de operações pendentes"""
        pending = self.queue.get_pending()
        
        for item in pending:
            try:
                success = self._process_queue_item(item)
                if success:
                    self.queue.remove(item['id'])
                    self._notify_callbacks('sync_success', item)
                else:
                    self.queue.increment_attempt(item['id'])
                    self._notify_callbacks('sync_failed', item)
            except Exception as e:
                logger.error(f"Erro ao processar item da fila: {e}")
                self.queue.increment_attempt(item['id'])
        
        # Limpa itens antigos
        self.queue.clear_old()
    
    def _process_queue_item(self, item: Dict[str, Any]) -> bool:
        """Processa um item da fila"""
        operation = item.get('operation')
        entity = item.get('entity')
        data = item.get('data', {})
        
        endpoint = self.SYNC_ENDPOINTS.get(entity)
        if not endpoint:
            logger.warning(f"Endpoint desconhecido para entidade: {entity}")
            return True  # Remove da fila
        
        url = f"{self.config.api_base_url}{endpoint}"
        
        try:
            if operation == 'create':
                response = self._session.post(url, json=data, timeout=self.config.api_timeout)
            elif operation == 'update':
                response = self._session.put(f"{url}{item.get('entity_id')}/", json=data, timeout=self.config.api_timeout)
            elif operation == 'delete':
                response = self._session.delete(f"{url}{item.get('entity_id')}/", timeout=self.config.api_timeout)
            else:
                logger.warning(f"Operação desconhecida: {operation}")
                return True
            
            return response.status_code in [200, 201, 204]
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar {operation} {entity}: {e}")
            return False
    
    def _sync_local_data(self):
        """Sincroniza dados locais com a API"""
        try:
            # Sincroniza estudantes
            self._sync_students()
            
            # Sincroniza agendamentos
            self._sync_appointments()
            
            # Atualiza timestamp de última sincronização
            self.config.update_last_sync()
            
            self._notify_callbacks('sync_complete', None)
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar dados locais: {e}")
    
    def _sync_students(self):
        """Sincroniza estudantes locais com a API"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Busca estudantes modificados após última sincronização
            last_sync = self.config.last_sync
            query = "SELECT * FROM aluno"
            if last_sync:
                query += " WHERE updated_at > %s"
                cursor.execute(query, (last_sync,))
            else:
                cursor.execute(query)
            
            students = cursor.fetchall()
            conn.close()
            
            if students:
                logger.info(f"Sincronizando {len(students)} estudantes")
                # Envia para a API em lote
                url = f"{self.config.api_base_url}/api/v1/desktop/students/sync/"
                self._session.post(url, json={'students': students}, timeout=30)
                
        except Exception as e:
            logger.error(f"Erro ao sincronizar estudantes: {e}")
    
    def _sync_appointments(self):
        """Sincroniza agendamentos locais com a API"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Busca agendamentos modificados após última sincronização
            last_sync = self.config.last_sync
            query = "SELECT * FROM agendamento"
            if last_sync:
                query += " WHERE updated_at > %s OR created_at > %s"
                cursor.execute(query, (last_sync, last_sync))
            else:
                cursor.execute(query)
            
            appointments = cursor.fetchall()
            conn.close()
            
            if appointments:
                logger.info(f"Sincronizando {len(appointments)} agendamentos")
                url = f"{self.config.api_base_url}/api/v1/desktop/schedule/appointments/sync/"
                self._session.post(url, json={'appointments': appointments}, timeout=30)
                
        except Exception as e:
            logger.error(f"Erro ao sincronizar agendamentos: {e}")
    
    def add_to_queue(self, operation: str, entity: str, entity_id: int, data: Dict[str, Any]):
        """Adiciona operação A  fila de sincronização"""
        if self.config.is_independent():
            return  # Não adiciona A  fila em modo independente
        
        self.queue.add(operation, entity, entity_id, data)
    
    def sync_now(self) -> Dict[str, Any]:
        """Executa sincronização imediata"""
        result = {
            'success': False,
            'api_available': False,
            'items_synced': 0,
            'items_pending': 0
        }
        
        if not self.check_api_availability():
            result['items_pending'] = len(self.queue.get_pending())
            return result
        
        result['api_available'] = True
        
        # Processa fila
        pending_before = len(self.queue.get_pending())
        self._process_queue()
        pending_after = len(self.queue.get_pending())
        result['items_synced'] = pending_before - pending_after
        result['items_pending'] = pending_after
        
        # Sincroniza dados locais
        self._sync_local_data()
        
        result['success'] = True
        return result
    
    def register_callback(self, event: str, callback: Callable):
        """Registra callback para eventos de sincronização"""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
    
    def _notify_callbacks(self, event: str, data: Any):
        """Notifica callbacks registrados"""
        callbacks = self._callbacks.get(event, [])
        for callback in callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Erro em callback {event}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do serviço de sincronização"""
        return {
            'mode': self.config.mode.value,
            'api_available': self.config.api_available,
            'api_url': self.config.api_base_url,
            'last_sync': self.config.last_sync.isoformat() if self.config.last_sync else None,
            'pending_items': len(self.queue.get_pending()),
            'auto_sync': self.config.auto_sync,
            'running': self._running
        }


# Instância global
sync_service = SyncService()


def get_sync_service() -> SyncService:
    """Retorna a instância global do serviço de sincronização"""
    return sync_service


def queue_sync(operation: str, entity: str, entity_id: int, data: Dict[str, Any]):
    """Adiciona operação A  fila de sincronização"""
    sync_service.add_to_queue(operation, entity, entity_id, data)


"""
Classe base para todos os Services do Desktop SerPleno
Implementa o padrão Template Method e fornece funcionalidades comuns
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, TypeVar, Generic
from contextlib import contextmanager

from config.db_config import get_db_connection
from config.settings import get_settings
from core.exceptions import DatabaseException, ApiException

T = TypeVar('T')
logger = logging.getLogger(__name__)


class BaseService(ABC, Generic[T]):
    """
    Classe base abstrata para serviços.
    
    Fornece:
    - Conexão com banco de dados
    - Cliente HTTP configurado
    - Tratamento de erros padronizado
    - Logging centralizado
    """
    
    def __init__(self):
        self._settings = get_settings()
        self._logger = logging.getLogger(self.__class__.__name__)
    
    @contextmanager
    def _get_db_cursor(self, dictionary: bool = True):
        """
        Context manager para cursor do banco de dados.
        
        Usage:
            with self._get_db_cursor() as cursor:
                cursor.execute("SELECT * FROM tabela")
                results = cursor.fetchall()
        """
        connection = None
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=dictionary)
            yield cursor
            connection.commit()
        except Exception as e:
            if connection:
                connection.rollback()
            self._logger.error(f"Erro no banco de dados: {e}")
            raise DatabaseException(
                message=f"Erro ao executar operação no banco: {str(e)}",
                details=e
            )
        finally:
            if connection:
                connection.close()
    
    def _execute_query(
        self, 
        query: str, 
        params: Optional[tuple] = None,
        fetch: bool = True,
        fetch_one: bool = False
    ) -> Optional[Any]:
        """
        Executa uma query no banco de dados.
        
        Args:
            query: SQL query
            params: Parâmetros da query
            fetch: Se deve retornar resultados
            fetch_one: Se deve retornar apenas um resultado
            
        Returns:
            Resultados da query ou None
        """
        with self._get_db_cursor() as cursor:
            cursor.execute(query, params or ())
            
            if fetch:
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()
            return None
    
    def _execute_insert(self, query: str, params: tuple) -> int:
        """
        Executa INSERT e retorna o ID inserido.
        """
        with self._get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def _execute_update(self, query: str, params: tuple) -> int:
        """
        Executa UPDATE/DELETE e retorna número de linhas afetadas.
        """
        with self._get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def _log_operation(self, operation: str, entity: str, entity_id: Optional[int] = None):
        """Registra operação no log"""
        msg = f"Operação: {operation} em {entity}"
        if entity_id:
            msg += f" #{entity_id}"
        self._logger.info(msg)
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Busca entidade por ID"""
        pass
    
    @abstractmethod
    def list_all(self, **filters) -> List[T]:
        """Lista todas as entidades com filtros opcionais"""
        pass


class ReadOnlyService(BaseService[T]):
    """
    Service apenas para leitura (sem operações de escrita).
    Útil para consultas e relatórios.
    """
    
    def create(self, entity: T) -> T:
        raise NotImplementedError("Este service é apenas para leitura")
    
    def update(self, entity: T) -> T:
        raise NotImplementedError("Este service é apenas para leitura")
    
    def delete(self, id: int) -> bool:
        raise NotImplementedError("Este service é apenas para leitura")


class CachedService(BaseService[T]):
    """
    Service com cache embutido.
    Útil para dados que não mudam frequentemente.
    """
    
    def __init__(self, cache_ttl: int = 300):
        super().__init__()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = cache_ttl
    
    def _get_cache_key(self, method: str, *args, **kwargs) -> str:
        """Gera chave de cache"""
        return f"{method}:{args}:{kwargs}"
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Recupera valor do cache"""
        import time
        cached = self._cache.get(key)
        if cached:
            if time.time() - cached['timestamp'] < self._cache_ttl:
                return cached['value']
            del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any):
        """Define valor no cache"""
        import time
        self._cache[key] = {
            'value': value,
            'timestamp': time.time()
        }
    
    def clear_cache(self):
        """Limpa todo o cache"""
        self._cache.clear()

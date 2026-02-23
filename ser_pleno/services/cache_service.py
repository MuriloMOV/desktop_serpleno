"""
Serviço de Cache Global para o Desktop SerPleno
Fornece cache em memória com TTL configurável e persistência opcional.
"""
import json
import os
import time
import hashlib
import threading
from typing import Optional, Dict, Any, Callable, TypeVar, Generic
from datetime import datetime
from functools import wraps

logger = __import__('logging').getLogger(__name__)

T = TypeVar('T')


class CacheEntry:
    """Representa uma entrada no cache."""
    
    def __init__(self, value: Any, ttl: int):
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """Verifica se a entrada expirou."""
        return time.time() - self.timestamp > self.ttl
    
    def access(self) -> Any:
        """Acessa o valor e incrementa contador."""
        self.access_count += 1
        return self.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            'value': self.value,
            'timestamp': self.timestamp,
            'ttl': self.ttl,
            'access_count': self.access_count
        }


class CacheService:
    """
    Serviço de cache global com suporte a TTL e persistência.
    
    Features:
    - Cache em memória com TTL configurável
    - Invalidação por chave ou padrão
    - Persistência em arquivo JSON
    - Estatísticas de uso
    - Thread-safe
    """
    
    _instance: Optional['CacheService'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = 300  # 5 minutos
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'sets': 0
        }
        self._cache_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'cache_data.json'
        )
        self._persistent_keys = set()  # Chaves que devem persistir
        
        # Carregar cache persistido
        self._load_persistent_cache()
    
    def _generate_key(self, key: str, namespace: Optional[str] = None) -> str:
        """Gera chave completa com namespace."""
        if namespace:
            return f"{namespace}:{key}"
        return key
    
    def _hash_key(self, key: str) -> str:
        """Gera hash para chaves longas."""
        if len(key) > 100:
            return hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()
        return key
    
    def get(
        self, 
        key: str, 
        default: Any = None,
        namespace: Optional[str] = None
    ) -> Any:
        """
        Recupera valor do cache.
        
        Args:
            key: Chave do cache
            default: Valor padrão se não encontrado
            namespace: Namespace opcional para agrupar chaves
            
        Returns:
            Valor cacheado ou default
        """
        full_key = self._hash_key(self._generate_key(key, namespace))
        
        with self._lock:
            entry = self._cache.get(full_key)
            
            if entry is None:
                self._stats['misses'] += 1
                return default
            
            if entry.is_expired():
                del self._cache[full_key]
                self._stats['evictions'] += 1
                self._stats['misses'] += 1
                return default
            
            self._stats['hits'] += 1
            return entry.access()
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        namespace: Optional[str] = None,
        persistent: bool = False
    ) -> None:
        """
        Define valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a ser cacheado
            ttl: Tempo de vida em segundos (usa default se não informado)
            namespace: Namespace opcional
            persistent: Se deve persistir em arquivo
        """
        full_key = self._hash_key(self._generate_key(key, namespace))
        ttl = ttl or self._default_ttl
        
        with self._lock:
            self._cache[full_key] = CacheEntry(value, ttl)
            self._stats['sets'] += 1
            
            if persistent:
                self._persistent_keys.add(full_key)
                self._save_persistent_cache()
    
    def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Remove valor do cache.
        
        Args:
            key: Chave do cache
            namespace: Namespace opcional
            
        Returns:
            True se removido, False se não existia
        """
        full_key = self._hash_key(self._generate_key(key, namespace))
        
        with self._lock:
            if full_key in self._cache:
                del self._cache[full_key]
                self._persistent_keys.discard(full_key)
                return True
            return False
    
    def clear_namespace(self, namespace: str) -> int:
        """
        Remove todas as chaves de um namespace.
        
        Args:
            namespace: Namespace a ser limpo
            
        Returns:
            Número de chaves removidas
        """
        prefix = f"{namespace}:"
        removed = 0
        
        with self._lock:
            keys_to_remove = [
                k for k in self._cache.keys() 
                if k.startswith(prefix)
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
                self._persistent_keys.discard(key)
                removed += 1
            
            self._stats['evictions'] += removed
        
        return removed
    
    def clear_all(self) -> None:
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
            self._persistent_keys.clear()
            self._save_persistent_cache()
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalida chaves que correspondem a um padrão.
        
        Args:
            pattern: Padrão a ser correspondido (ex: "students:*")
            
        Returns:
            Número de chaves removidas
        """
        import fnmatch
        
        removed = 0
        
        with self._lock:
            keys_to_remove = [
                k for k in self._cache.keys()
                if fnmatch.fnmatch(k, pattern)
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
                self._persistent_keys.discard(key)
                removed += 1
            
            self._stats['evictions'] += removed
        
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (
                self._stats['hits'] / total_requests * 100 
                if total_requests > 0 else 0
            )
            
            return {
                **self._stats,
                'total_entries': len(self._cache),
                'hit_rate': round(hit_rate, 2),
                'persistent_entries': len(self._persistent_keys)
            }
    
    def _save_persistent_cache(self) -> None:
        """Salva cache persistente em arquivo."""
        try:
            data = {}
            for key in self._persistent_keys:
                entry = self._cache.get(key)
                if entry and not entry.is_expired():
                    # Só salva valores serializáveis
                    try:
                        json.dumps(entry.value)
                        data[key] = entry.to_dict()
                    except (TypeError, ValueError):
                        pass
            
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar cache persistente: {e}")
    
    def _load_persistent_cache(self) -> None:
        """Carrega cache persistente do arquivo."""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for key, entry_data in data.items():
                    entry = CacheEntry(
                        entry_data['value'],
                        entry_data['ttl']
                    )
                    entry.timestamp = entry_data['timestamp']
                    entry.access_count = entry_data.get('access_count', 0)
                    
                    if not entry.is_expired():
                        self._cache[key] = entry
                        self._persistent_keys.add(key)
                
                logger.info(f"Cache persistente carregado: {len(self._cache)} entradas")
                
        except Exception as e:
            logger.warning(f"Erro ao carregar cache persistente: {e}")
    
    def cleanup_expired(self) -> int:
        """
        Remove todas as entradas expiradas.
        
        Returns:
            Número de entradas removidas
        """
        removed = 0
        
        with self._lock:
            keys_to_remove = [
                k for k, v in self._cache.items()
                if v.is_expired()
            ]
            
            for key in keys_to_remove:
                del self._cache[key]
                self._persistent_keys.discard(key)
                removed += 1
            
            self._stats['evictions'] += removed
        
        return removed


def cached(
    ttl: int = 300,
    namespace: Optional[str] = None,
    key_prefix: Optional[str] = None,
    persistent: bool = False
):
    """
    Decorator para cachear resultados de funções.
    
    Args:
        ttl: Tempo de vida em segundos
        namespace: Namespace do cache
        key_prefix: Prefixo para a chave
        persistent: Se deve persistir em arquivo
        
    Usage:
        @cached(ttl=60, namespace='students')
        def get_student(id):
            return fetch_student(id)
    """
    def decorator(func: Callable) -> Callable:
        cache = CacheService()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave baseada nos argumentos
            args_str = str(args) + str(sorted(kwargs.items()))
            args_hash = hashlib.md5(args_str.encode(), usedforsecurity=False).hexdigest()
            
            func_name = key_prefix or func.__name__
            cache_key = f"{func_name}:{args_hash}"
            
            # Tentar obter do cache
            result = cache.get(cache_key, namespace=namespace)
            
            if result is not None:
                return result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            
            if result is not None:
                cache.set(
                    cache_key, 
                    result, 
                    ttl=ttl, 
                    namespace=namespace,
                    persistent=persistent
                )
            
            return result
        
        # Adicionar método para invalidar cache
        wrapper.invalidate_cache = lambda: cache.clear_namespace(
            namespace or func.__name__
        )
        
        return wrapper
    
    return decorator


class CachedMethod:
    """
    Descriptor para cachear métodos de classe.
    
    Usage:
        class MeuServico:
            @CachedMethod(ttl=60)
            def buscar_dados(self, id):
                return fetch_data(id)
    """
    
    def __init__(self, ttl: int = 300, namespace: Optional[str] = None):
        self.ttl = ttl
        self.namespace = namespace
        self._cache = None
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        
        if self._cache is None:
            self._cache = CacheService()
        
        def cached_method(*args, **kwargs):
            # Gerar chave
            args_str = str(args) + str(sorted(kwargs.items()))
            args_hash = hashlib.md5(args_str.encode(), usedforsecurity=False).hexdigest()
            
            method_name = self.namespace or obj.__class__.__name__
            cache_key = f"{method_name}:{args_hash}"
            
            # Tentar cache
            result = self._cache.get(cache_key, namespace=method_name)
            
            if result is not None:
                return result
            
            # Executar método original
            method = obj.__dict__.get(self.__name__)
            if method is None:
                # Obter método original
                for name, value in obj.__class__.__dict__.items():
                    if value is self:
                        self.__name__ = name
                        break
                method = getattr(obj, self.__name__)
            
            result = method(*args, **kwargs)
            
            if result is not None:
                self._cache.set(
                    cache_key,
                    result,
                    ttl=self.ttl,
                    namespace=method_name
                )
            
            return result
        
        return cached_method


# Instância global
cache_service = CacheService()


def get_cache() -> CacheService:
    """Retorna a instância global do cache."""
    return cache_service

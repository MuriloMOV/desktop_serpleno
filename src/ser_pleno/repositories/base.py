# -*- coding: utf-8 -*-
"""Repositorio base — acesso compartilhado ao banco."""

from ser_pleno.config.db_config import get_db_connection
from ser_pleno.infrastructure.local.local_cache import LocalCache, local_cache
from ser_pleno.infrastructure.local.fallback_metrics import record_fallback
from ser_pleno.config.operation_mode import get_mode, should_use_db_first
import logging
from typing import Any
import threading

logger = logging.getLogger(__name__)

_local_id_counter = 0
_local_id_lock = threading.Lock()


def generate_local_id(mysql_result: Any) -> Any:
    """Retorna o ID do MySQL se válido; caso contrário gera um ID local negativo."""
    global _local_id_counter
    if mysql_result:
        return mysql_result
    with _local_id_lock:
        _local_id_counter -= 1
        return _local_id_counter


def is_local_id(entity_id: Any) -> bool:
    """Verifica se o ID é gerado localmente (offline)."""
    if not isinstance(entity_id, int):
        return False
    return entity_id < 0


# Cache local SQLite singleton para fallback offline.
# Reutiliza a instancia exportada por local_cache.py.


_FALLBACK_LOG_EXTRA = {
    "fallback": "read",
    "component": "repository",
    "db_mode": get_mode().value,
}


def _is_db_error(exc: Exception) -> bool:
    """Heuristica para detectar erros de conexao/banco que justificam fallback."""
    name = type(exc).__name__
    db_errors = {
        "InterfaceError",
        "DatabaseError",
        "OperationalError",
        "DisconnectedError",
        "ProgrammingError",
        "RuntimeError",
    }
    if name in db_errors:
        return True
    module = type(exc).__module__ or ""
    if "mysql" in module.lower() or "pymysql" in module.lower() or "mysql.connector" in module.lower():
        return True
    msg = str(exc).lower()
    connection_keywords = [
        "can't connect",
        "connection refused",
        "no connection",
        "server has gone away",
        "lost connection",
        "broken pipe",
        "network",
        "timeout",
        "pool de conex",
        "nao foi possivel inicializar",
        "could not",
    ]
    return any(kw in msg for kw in connection_keywords)


def with_local_fallback(local_fn_name: str):
    """Decorator que cai para o metodo _local_* quando MySQL falhar."""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if _is_db_error(e):
                    extra = {
                        **_FALLBACK_LOG_EXTRA,
                        "repository": type(self).__name__,
                        "method": func.__name__,
                        "exc_type": type(e).__name__,
                        "exc_message": str(e)[:200],
                    }
                    logger.warning(
                        "MySQL indisponivel, usando cache local para %s (repo=%s, exc=%s)",
                        func.__name__,
                        type(self).__name__,
                        type(e).__name__,
                        extra=extra,
                    )
                    record_fallback("read", type(self).__name__, func.__name__)
                    local_fn = getattr(self, local_fn_name)
                    return local_fn(*args, **kwargs)
                raise
        return wrapper
    return decorator


def write_with_fallback(
    mysql_fn,
    local_fn,
    operation: str,
    entity: str,
    entity_id: Any,
    queue_data_fn=None,
) -> Any:
    """MySQL-first write com fallback local + sync queue.

    Args:
        mysql_fn: callable que executa o write no MySQL e retorna o resultado.
        local_fn: callable que executa o write local, recebe mysql_result como argumento.
        operation: tipo de operacao (create/update/delete) para a sync queue.
        entity: nome da entidade para a sync queue.
        entity_id: ID da entidade para log e queue.
        queue_data_fn: callable(mysql_result, entity_id) -> dict para enfileirar (opcional).

    Returns:
        Resultado de mysql_fn se sucesso, resultado de local_fn se fallback.
    """
    try:
        mysql_result = mysql_fn()
    except Exception as exc:
        if _is_db_error(exc):
            extra = {
                "fallback": "write",
                "operation": operation,
                "entity": entity,
                "db_mode": get_mode().value,
                "entity_id": str(entity_id),
            }
            logger.warning(
                "MySQL indisponivel no write; cache local + queue para %s#%s",
                entity, entity_id,
                extra=extra,
            )
            record_fallback("write", entity, operation, str(entity_id))
            local_result = local_fn(None)
            if queue_data_fn is not None:
                try:
                    data = queue_data_fn(local_result, entity_id)
                    if data is not None:
                        qid = data.get("id") or entity_id
                        from ser_pleno.infrastructure.api.sync_service import queue_sync
                        queue_sync(operation, entity, qid, data)
                except Exception:
                    pass
            return local_result
        raise

    # MySQL success
    local_result = local_fn(mysql_result)
    if queue_data_fn is not None:
        try:
            data = queue_data_fn(mysql_result, entity_id)
            if data is not None:
                qid = data.get("id") or entity_id
                from ser_pleno.infrastructure.api.sync_service import queue_sync
                queue_sync(operation, entity, qid, data)
        except Exception:
            pass
    return mysql_result


def get_connection():
    return get_db_connection()


def execute_query(query, params=None, fetch=True, fetch_one=False, dictionary=True):
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        cursor.execute(query, params or ())
        if fetch_one:
            result = cursor.fetchone()
        elif fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        return result
    finally:
        cursor.close()
        conn.close()


def fetch_all(query, params=None):
    return execute_query(query, params=params, fetch=True, fetch_one=False, dictionary=True)


def fetch_one(query, params=None):
    return execute_query(query, params=params, fetch=True, fetch_one=True, dictionary=True)


def execute_non_query(query, params=None):
    return execute_query(query, params=params, fetch=False, dictionary=False)

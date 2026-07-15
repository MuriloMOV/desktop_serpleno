# -*- coding: utf-8 -*-
"""Repositorio base — helpers de ID local e re-exports para retrocompatibilidade.

.. deprecated::
    As funcionalidades foram movidas para modulos especificos:
    - ``ser_pleno.infrastructure.db.query_helpers`` (execute_query, fetch_all, etc.)
    - ``ser_pleno.repositories.fallback`` (with_local_fallback, write_with_fallback)
"""

from ser_pleno.infrastructure.db.query_helpers import (
    execute_query,
    fetch_all,
    fetch_one,
    execute_non_query,
)
from ser_pleno.repositories.fallback import (
    with_local_fallback,
    write_with_fallback,
    _is_db_error,
)
from ser_pleno.infrastructure.local.local_cache import LocalCache, local_cache

_local_id_counter = 0
import threading

_local_id_lock = threading.Lock()


def generate_local_id(mysql_result):
    """Retorna o ID do MySQL se válido; caso contrário gera um ID local negativo."""
    global _local_id_counter
    if mysql_result:
        return mysql_result
    with _local_id_lock:
        _local_id_counter -= 1
        return _local_id_counter


def is_local_id(entity_id):
    """Verifica se o ID é gerado localmente (offline)."""
    if not isinstance(entity_id, int):
        return False
    return entity_id < 0

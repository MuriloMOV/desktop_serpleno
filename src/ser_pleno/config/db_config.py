import os
from contextlib import contextmanager
from typing import Generator

import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector.pooling import MySQLConnectionPool


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


DB_CONFIG = {
    "host": os.getenv("SERPLENO_DB_HOST", "127.0.0.1"),
    "user": os.getenv("SERPLENO_DB_USER", "root"),
    "password": os.getenv("SERPLENO_DB_PASSWORD", ""),
    "database": os.getenv("SERPLENO_DB_NAME", "ser_pleno"),
    "port": _env_int("SERPLENO_DB_PORT", 3306),
}

_POOL_NAME = "ser_pleno_pool"
_POOL_SIZE = int(os.getenv("SERPLENO_DB_POOL_SIZE", "5"))

_pool: MySQLConnectionPool | None = None


def _get_pool() -> MySQLConnectionPool:
    global _pool
    if _pool is None:
        try:
            _pool = MySQLConnectionPool(
                pool_name=_POOL_NAME,
                pool_size=_POOL_SIZE,
                **DB_CONFIG,
            )
        except Exception:
            _pool = None
    if _pool is None:
        raise RuntimeError("Não foi possível inicializar o pool de conexões MySQL")
    return _pool


def get_db_connection() -> MySQLConnection:
    """
    Retorna uma conexão do pool com o banco de dados MySQL.
    Quem recebe a conexão é responsável por fechá-la para devolvê-la ao pool.
    """
    return _get_pool().get_connection()


@contextmanager
def connection() -> Generator[MySQLConnection, None, None]:
    """
    Context manager para conexões MySQL.

    Uso:
        with connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(...)
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

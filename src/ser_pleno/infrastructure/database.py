# -*- coding: utf-8 -*-
"""Infraestrutura de banco de dados — conexão MySQL."""

import os
from contextlib import contextmanager
from typing import Generator

import mysql.connector
from mysql.connector import MySQLConnection


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


def get_db_connection() -> MySQLConnection:
    """Retorna uma nova conexão com o banco de dados MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


@contextmanager
def connection() -> Generator[MySQLConnection, None, None]:
    """Context manager para conexões MySQL."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

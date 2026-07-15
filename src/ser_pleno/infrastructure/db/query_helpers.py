# -*- coding: utf-8 -*-
"""Helpers de acesso a banco — conexão, queries genéricas e execução."""

from ser_pleno.config.db_config import get_db_connection


def get_connection():
    """Retorna uma conexão com o banco."""
    return get_db_connection()


def execute_query(query, params=None, fetch=True, fetch_one=False, dictionary=True):
    """Executa uma query SQL e retorna o resultado."""
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
    """Executa query e retorna todas as linhas como lista de dicts."""
    return execute_query(query, params=params, fetch=True, fetch_one=False, dictionary=True)


def fetch_one(query, params=None):
    """Executa query e retorna uma única linha como dict."""
    return execute_query(query, params=params, fetch=True, fetch_one=True, dictionary=True)


def execute_non_query(query, params=None):
    """Executa query sem retorno (INSERT/UPDATE/DELETE). Retorna lastrowid."""
    return execute_query(query, params=params, fetch=False, dictionary=False)

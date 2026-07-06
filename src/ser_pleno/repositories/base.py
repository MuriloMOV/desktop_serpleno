# -*- coding: utf-8 -*-
"""Repositório base — acesso compartilhado ao banco."""

from ser_pleno.infrastructure.database import get_db_connection


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
    return execute_query(
        query, params=params, fetch=True, fetch_one=False, dictionary=True
    )


def fetch_one(query, params=None):
    return execute_query(
        query, params=params, fetch=True, fetch_one=True, dictionary=True
    )


def execute_non_query(query, params=None):
    return execute_query(query, params=params, fetch=False, dictionary=False)

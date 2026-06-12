import os

import mysql.connector


def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


DB_CONFIG = {
    'host': os.getenv('SERPLENO_DB_HOST', '127.0.0.1'),
    'user': os.getenv('SERPLENO_DB_USER', 'root'),
    'password': os.getenv('SERPLENO_DB_PASSWORD', ''),
    'database': os.getenv('SERPLENO_DB_NAME', 'ser_pleno'),
    'port': _env_int('SERPLENO_DB_PORT', 3306),
}

def get_db_connection():
    """
    Retorna uma conexão com o banco de dados MySQL.
    """
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port']
    )

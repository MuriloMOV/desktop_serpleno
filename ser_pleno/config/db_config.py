import mysql.connector

# Configurações do banco de dados
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'MySQL3691@26',
    'database': 'ser_pleno',
    'port': 3306
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
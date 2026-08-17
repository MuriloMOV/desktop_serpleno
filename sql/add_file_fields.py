from ser_pleno.config.db_config import get_db_connection

def add_file_fields():
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Verifica se os campos já existem antes de adicionar
        cursor.execute("SHOW COLUMNS FROM desktop_message LIKE 'caminho_arquivo'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE desktop_message ADD COLUMN caminho_arquivo VARCHAR(500) NULL AFTER `read`")
            print("Campo caminho_arquivo adicionado com sucesso")
        
        cursor.execute("SHOW COLUMNS FROM desktop_message LIKE 'tipo_arquivo'")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE desktop_message ADD COLUMN tipo_arquivo VARCHAR(50) NULL AFTER caminho_arquivo")
            print("Campo tipo_arquivo adicionado com sucesso")
        
        connection.commit()
        print("Campos para arquivo adicionados com sucesso")
    except Exception as e:
        print(f"Erro ao adicionar campos: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    add_file_fields()

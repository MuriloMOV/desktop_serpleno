from config.db_config import get_db_connection

class ServicoConfiguracoes:
    def obter_configuracoes(self):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_preferences")
        result = cursor.fetchall()
        connection.close()
        return {"success": True, "data": result}

    def atualizar_configuracoes(self, dados):
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "UPDATE user_preferences SET theme = %s, notifications = %s WHERE user_id = %s"
        cursor.execute(query, (dados['theme'], dados['notifications'], dados['user_id']))
        connection.commit()
        connection.close()
        return {"success": True, "message": "Configurações atualizadas com sucesso"}

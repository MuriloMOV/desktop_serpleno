from .api import api
from config.db_config import get_db_connection

class ServicoAgendamento:
    def verificar_disponibilidade(self, data_hora):
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM agendamentos WHERE data_hora = %s AND status != 'Cancelado'"
        cursor.execute(query, (data_hora,))
        existe = cursor.fetchone()[0] > 0
        cursor.close()
        conn.close()
        return not existe

    def criar_agendamento(self, dados):
        if not self.verificar_disponibilidade(dados['data_hora']):
            return {"success": False, "message": "Horário indisponível"}

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                INSERT INTO agendamentos 
                (nome, data_hora, motivo, status, laudo, Aluno_id_aluno, origem) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            valores = (
                dados['nome_aluno'], 
                dados['data_hora'], 
                dados.get('motivo', ''), 
                'Pendente', 
                dados.get('laudo', ''), 
                dados['id_aluno'], 
                'Desktop'
            )
            cursor.execute(query, valores)
            conn.commit()
            return {"success": True, "id": cursor.lastrowid}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            conn.close()

    def listar_agendamentos(self, data=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM agendamentos"
        params = []
        
        if data:
            query += " WHERE DATE(data_hora) = %s"
            params.append(data)
            
        cursor.execute(query, params)
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return resultados

    def atualizar_agendamento(self, id_agendamento, dados):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                UPDATE agendamentos 
                SET nome = %s, data_hora = %s, motivo = %s, status = %s, Aluno_id_aluno = %s
                WHERE id_agendamento = %s
            """
            valores = (
                dados['nome_aluno'], 
                dados['data_hora'], 
                dados.get('motivo', ''), 
                dados.get('status', 'Pendente'),
                dados['id_aluno'],
                id_agendamento
            )
            cursor.execute(query, valores)
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            conn.close()

    def deletar_agendamento(self, id_agendamento):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = "DELETE FROM agendamentos WHERE id_agendamento = %s"
            cursor.execute(query, (id_agendamento,))
            conn.commit()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            conn.close()
            
    def adicionar_horario_disponibilidade(self, horario):
        """Adiciona um novo horário à tabela de disponibilidade"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = "INSERT INTO disponibilidade (Horario, is_active) VALUES (%s, 1)"
            cursor.execute(query, (horario,))
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def remover_horario_disponibilidade(self, horario):
        """Remove um horário da tabela de disponibilidade"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = "DELETE FROM disponibilidade WHERE Horario = %s"
            cursor.execute(query, (horario,))
            conn.commit()
            return {"success": True}
        except Exception as e:
            conn.rollback()
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            conn.close()

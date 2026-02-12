from config.db_config import get_db_connection
import logging
import mysql.connector
from datetime import datetime
import requests

class ServicoAgendamento:
    # URL base da API do Serpleno Web (ajuste conforme necessário)
    API_BASE_URL = "http://127.0.0.1:8000"
    # Token para autenticação na API
    API_TOKEN = "serpleno-desktop-token-2024"
    
    def _get_headers(self):
        """Retorna os headers para as requisições API"""
        return {
            "Content-Type": "application/json",
            "X-Desktop-Token": self.API_TOKEN
        }
    
    def verificar_disponibilidade(self, data, time_str):
        """Verifica se um horário está disponível usando a API do Serpleno Web"""
        try:
            # Primeiro verifica disponibilidade no banco local (fallback)
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Converter data e horário para datetime
            data_hora_str = f"{data} {time_str}"
            data_hora = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
            
            # Verificar se já existe agendamento para essa data e horário
            cursor.execute("""
                SELECT id FROM agendamento 
                WHERE data_hora BETWEEN %s AND %s
            """, (data_hora, data_hora + datetime.timedelta(minutes=59)))
            
            if cursor.fetchone():
                logging.info(f"Horário {time_str} já agendado para {data}")
                cursor.close()
                conn.close()
                return False
            
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"Erro ao verificar disponibilidade: {e}")
            return False

    def criar_agendamento(self, dados):
        """Cria um agendamento usando a API do Serpleno Web"""
        try:
            # Primeiro cria no banco local (fallback)
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Converter data_hora para datetime
            data_hora = datetime.strptime(dados['data_hora'], "%Y-%m-%d %H:%M")
            
            # Preparar dados
            status = self._convert_status_frontend_to_backend(dados.get('status', 'Agendado'))
            
            # Garantir que id_aluno é um número inteiro
            id_aluno = int(dados['id_aluno'])
            
            # Inserir agendamento
            cursor.execute("""
                INSERT INTO agendamento (student_id, data_hora, motivo, status, local, profissional, laudo, origem)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_aluno,
                data_hora,
                dados.get('motivo', ''),
                status,
                dados.get('local', None),
                dados.get('profissional', None),
                dados.get('laudo', None),
                'desktop'
            ))
            
            conn.commit()
            appointment_id = cursor.lastrowid
            
            cursor.close()
            conn.close()
            
            # Tenta sincronizar com a API (não bloqueante)
            try:
                self._sync_with_api(appointment_id)
            except Exception as e:
                logging.warning(f"Erro ao sincronizar agendamento com API: {e}")
            
            return {"success": True, "id": appointment_id}
        except Exception as e:
            logging.error(f"Erro ao criar agendamento: {e}")
            return {"success": False, "message": str(e)}

    def listar_agendamentos(self, data=None):
        """Lista agendamentos usando o banco de dados"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT a.id, al.nome, al.id_aluno, a.data_hora, a.motivo, a.status, a.local, a.profissional, a.laudo, a.origem
                FROM agendamento a
                INNER JOIN aluno al ON a.student_id = al.id_aluno
            """
            
            params = []
            if data:
                query += " WHERE DATE(a.data_hora) = %s"
                params.append(data)
            
            query += " ORDER BY a.data_hora"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            agendamentos = []
            for row in results:
                agendamentos.append({
                    "id_agendamento": row["id"],
                    "nome": row["nome"],
                    "id_aluno": row["id_aluno"],
                    "data_hora": row["data_hora"],
                    "motivo": row["motivo"],
                    "status": self._convert_status_backend_to_frontend(row["status"]),
                    "local": row.get("local"),
                    "profissional": row.get("profissional"),
                    "laudo": row.get("laudo"),
                    "origem": row.get("origem")
                })
            
            cursor.close()
            conn.close()
            return agendamentos
        except Exception as e:
            logging.error(f"Erro ao listar agendamentos: {e}")
            return []

    def atualizar_agendamento(self, id_agendamento, dados):
        """Atualiza um agendamento usando o banco de dados"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Converter data_hora para datetime
            data_hora = datetime.strptime(dados['data_hora'], "%Y-%m-%d %H:%M")
            
            # Preparar dados
            status = self._convert_status_frontend_to_backend(dados.get('status', 'Agendado'))
            
            # Atualizar agendamento
            cursor.execute("""
                UPDATE agendamento 
                SET student_id = %s, data_hora = %s, motivo = %s, status = %s, local = %s, profissional = %s, laudo = %s, origem = %s
                WHERE id = %s
            """, (
                dados['id_aluno'],
                data_hora,
                dados.get('motivo', ''),
                status,
                dados.get('local', None),
                dados.get('profissional', None),
                dados.get('laudo', None),
                'desktop',
                id_agendamento
            ))
            
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Tenta sincronizar com a API (não bloqueante)
            try:
                self._sync_with_api(id_agendamento)
            except Exception as e:
                logging.warning(f"Erro ao sincronizar agendamento com API: {e}")
            
            return {"success": True}
        except Exception as e:
            logging.error(f"Erro ao atualizar agendamento: {e}")
            return {"success": False, "message": str(e)}

    def deletar_agendamento(self, id_agendamento):
        """Deleta um agendamento usando o banco de dados"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM agendamento WHERE id = %s", (id_agendamento,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Tenta cancelar o agendamento no SerPleno Web via desktop_appointment_id
            try:
                response = requests.delete(
                    f"{self.API_BASE_URL}/api/agendamentos/by-desktop-id/{id_agendamento}/",
                    headers=self._get_headers()
                )
                if response.status_code == 200:
                    logging.info(f"Agendamento {id_agendamento} cancelado no SerPleno Web via desktop_appointment_id")
                elif response.status_code == 404:
                    # Agendamento não existe no web, pode ter sido criado no web
                    logging.warning(f"Agendamento {id_agendamento} não encontrado no SerPleno Web para cancelamento")
                else:
                    response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logging.warning(f"Erro ao sincronizar cancelamento com API: {e}")
            
            return {"success": True}
        except Exception as e:
            logging.error(f"Erro ao deletar agendamento: {e}")
            return {"success": False, "message": str(e)}
            
    def adicionar_horario_disponibilidade(self, horario):
        """Adiciona um novo horário à tabela de disponibilidade usando a API do Serpleno Web"""
        try:
            # Validar formato HH:MM
            time_obj = datetime.strptime(horario, "%H:%M").time()
            
            # Tenta adicionar via API
            try:
                payload = {
                    "horario": horario,
                    "dias": "segunda-terca-quarta-quinta-sexta",
                    "is_active": True
                }
                response = requests.post(f"{self.API_BASE_URL}/api/disponibilidade/", json=payload)
                response.raise_for_status()
                
                logging.info(f"Horário {horario} adicionado via API")
                return {"success": True}
            except Exception as api_error:
                logging.warning(f"Erro ao adicionar horário via API: {api_error}")
                # Fallback para banco local
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Verificar se horário já existe
                cursor.execute("SELECT id_disponibilidade FROM disponibilidade WHERE Horario = %s", (time_obj,))
                if cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return {"success": False, "message": "Este horário já existe"}
                
                # Inserir horário
                cursor.execute("""
                    INSERT INTO disponibilidade (Horario, is_active, Dias)
                    VALUES (%s, 1, 'segunda-terca-quarta-quinta-sexta')
                """, (time_obj,))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                logging.info(f"Horário {horario} adicionado via banco local")
                return {"success": True}
        except ValueError:
            return {"success": False, "message": "Formato de horário inválido. Use HH:MM"}
        except Exception as e:
            logging.error(f"Erro ao adicionar horário: {e}")
            return {"success": False, "message": str(e)}
    
    def remover_horario_disponibilidade(self, horario):
        """Remove um horário da tabela de disponibilidade usando a API do Serpleno Web"""
        try:
            # Validar formato HH:MM
            time_obj = datetime.strptime(horario, "%H:%M").time()
            
            # Tenta remover via API
            try:
                response = requests.get(f"{self.API_BASE_URL}/api/disponibilidade/?horario={horario}")
                response.raise_for_status()
                disponibilidades = response.json()
                
                if disponibilidades:
                    disponibilidade_id = disponibilidades[0]['id_disponibilidade']
                    response = requests.delete(f"{self.API_BASE_URL}/api/disponibilidade/{disponibilidade_id}/")
                    response.raise_for_status()
                    
                    logging.info(f"Horário {horario} removido via API")
                    return {"success": True}
                else:
                    return {"success": False, "message": "Horário não encontrado"}
            except Exception as api_error:
                logging.warning(f"Erro ao remover horário via API: {api_error}")
                # Fallback para banco local
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Obter o time_id correspondente ao horário
                cursor.execute("SELECT id_disponibilidade FROM disponibilidade WHERE Horario = %s", (time_obj,))
                time_result = cursor.fetchone()
                if not time_result:
                    cursor.close()
                    conn.close()
                    return {"success": False, "message": "Horário não encontrado"}
                time_id = time_result[0]
                
                # Verificar se há agendamentos usando este horário (agora usando a tabela agendamento)
                cursor.execute("""
                    SELECT id FROM agendamento 
                    WHERE TIME(data_hora) = %s
                """, (time_obj,))
                
                if cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return {"success": False, "message": "Não é possível remover horário com agendamentos associados"}
                
                # Remover horário
                cursor.execute("DELETE FROM disponibilidade WHERE id_disponibilidade = %s", (time_id,))
                conn.commit()
                
                cursor.close()
                conn.close()
                
                logging.info(f"Horário {horario} removido via banco local")
                return {"success": True}
        except ValueError:
            return {"success": False, "message": "Formato de horário inválido. Use HH:MM"}
        except Exception as e:
            logging.error(f"Erro ao remover horário: {e}")
            return {"success": False, "message": str(e)}
    
    def _sync_with_api(self, appointment_id):
        """Sincroniza um agendamento com a API do Serpleno Web"""
        try:
            # Obtém os dados do agendamento do banco local
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT a.id, a.student_id, a.data_hora, a.motivo, a.status, a.local, a.profissional, a.laudo, a.origem,
                       al.nome as nome_aluno
                FROM agendamento a
                INNER JOIN aluno al ON a.student_id = al.id_aluno
                WHERE a.id = %s
            """, (appointment_id,))
            
            agendamento = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not agendamento:
                raise Exception(f"Agendamento {appointment_id} não encontrado")
            
            # Converte dados para formato da API
            payload = {
                "nome": f"Atendimento - {agendamento['nome_aluno']}",
                "data_hora": agendamento['data_hora'].isoformat(),
                "motivo": agendamento['motivo'],
                "status": self._convert_status_backend_to_frontend(agendamento['status']),
                "laudo": agendamento['laudo'] or "N/A",
                "student": agendamento['student_id'],
                "origem": "desktop",
                "desktop_appointment_id": agendamento['id'],
                "profissional": agendamento['profissional'] or "Equipe SerPleno",
                "local": agendamento['local'] or "Sala de Atendimento Psicológico"
            }
            
            # Verifica se o agendamento já existe na API
            response = requests.get(
                f"{self.API_BASE_URL}/api/agendamentos/?desktop_appointment_id={appointment_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            if response.json():
                # Atualiza agendamento existente
                agendamento_api_id = response.json()[0]['id_agendamentos']
                response = requests.put(
                    f"{self.API_BASE_URL}/api/agendamentos/{agendamento_api_id}/",
                    json=payload,
                    headers=self._get_headers()
                )
            else:
                # Cria novo agendamento
                response = requests.post(
                    f"{self.API_BASE_URL}/api/agendamentos/",
                    json=payload,
                    headers=self._get_headers()
                )
            
            response.raise_for_status()
            logging.info(f"Agendamento {appointment_id} sincronizado com API")
        except Exception as e:
            logging.error(f"Erro ao sincronizar agendamento {appointment_id} com API: {e}")
            raise
    
    def _convert_status_frontend_to_backend(self, status):
        """Converte status do frontend para o formato do backend"""
        status_map = {
            "Agendado": "scheduled",
            "Realizado": "completed",
            "Cancelado": "cancelled",
            "Faltou": "missed"
        }
        return status_map.get(status, "scheduled")
    
    def _convert_status_backend_to_frontend(self, status):
        """Converte status do backend para o formato do frontend"""
        status_map = {
            "scheduled": "Agendado",
            "completed": "Realizado",
            "cancelled": "Cancelado",
            "missed": "Faltou"
        }
        return status_map.get(status, "Agendado")

from config.db_config import get_db_connection
import logging
import mysql.connector
from datetime import datetime, timedelta
import requests

# Instância global do serviço de autenticação
_auth_service = None

def set_auth_service(auth_service):
    """Define o serviço de autenticação global para usar nas requisições API"""
    global _auth_service
    _auth_service = auth_service

def get_auth_service():
    """Retorna o serviço de autenticação global"""
    return _auth_service

class ServicoAgendamento:
    # URL base da API do Serpleno Web (ajuste conforme necessário)
    API_BASE_URL = "http://127.0.0.1:8000"
    # URL base da API Desktop
    API_DESKTOP_URL = "http://127.0.0.1:8000/api/v1/desktop"
    # Token para autenticação na API
    API_TOKEN = "serpleno-desktop-token-2024"
    
    def _get_session(self):
        """Retorna a sessão HTTP do serviço de autenticação"""
        auth = get_auth_service()
        if auth and hasattr(auth, 'get_session'):
            session = auth.get_session()
            # Log para depuração
            logging.debug(f"Sessão obtida: cookies = {dict(session.cookies)}")
            return session
        logging.warning("Nenhum serviço de autenticação disponível, usando requests sem sessão")
        return requests
    
    def _get_headers(self):
        """Retorna os headers para as requisições API, incluindo CSRF token"""
        headers = {
            "Content-Type": "application/json",
            "X-Desktop-Token": self.API_TOKEN
        }
        # Adiciona o CSRF token se disponível
        auth = get_auth_service()
        if auth and hasattr(auth, 'csrf_token') and auth.csrf_token:
            headers["X-CSRFToken"] = auth.csrf_token
        return headers
    
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
            """, (data_hora, data_hora + timedelta(minutes=59)))
            
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
        """Cria um agendamento usando banco de dados local primeiro, API como fallback"""
        try:
            # Extrair data e hora
            data_hora = datetime.strptime(dados['data_hora'], "%Y-%m-%d %H:%M")
            data_str = data_hora.strftime("%Y-%m-%d")
            hora_str = data_hora.strftime("%H:%M")
            
            # Garantir que id_aluno é um número inteiro
            id_aluno = int(dados['id_aluno'])
            
            # Primeiro, tenta criar no banco local (mais rápido)
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Preparar dados
                status = self._convert_status_frontend_to_backend(dados.get('status', 'Agendado'))
                
                # Obter nome do aluno para o campo obrigatório 'nome'
                cursor.execute("SELECT nome FROM aluno WHERE id_aluno = %s", (id_aluno,))
                aluno_result = cursor.fetchone()
                nome_aluno = aluno_result[0] if aluno_result else f"Aluno {id_aluno}"
                
                # Campo nome é obrigatório - formato: "Atendimento - Nome do Aluno"
                nome_agendamento = f"Atendimento - {nome_aluno}"
                
                # Inserir agendamento com todos os campos obrigatórios
                # IMPORTANTE: Usar status 'agendado' que é o status padrão esperado pelo Serpleno Web
                cursor.execute("""
                    INSERT INTO agendamento (student_id, data_hora, nome, motivo, status, local, profissional, laudo, origem)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    id_aluno,
                    data_hora,
                    nome_agendamento,
                    dados.get('motivo', ''),
                    'agendado',  # Status padrão para o Serpleno Web
                    dados.get('local', 'Sala de Atendimento Psicológico'),
                    dados.get('profissional', None),
                    dados.get('laudo', 'N/A'),
                    'desktop'
                ))
                
                conn.commit()
                appointment_id = cursor.lastrowid
                
                cursor.close()
                conn.close()
                
                logging.info(f"Agendamento criado via banco local: {appointment_id}")
                
                # Tenta sincronizar com o Serpleno Web em background (não bloqueante)
                try:
                    self._sync_with_serpleno_web(appointment_id, id_aluno, data_hora, nome_agendamento, dados)
                except Exception as sync_error:
                    logging.warning(f"Erro ao sincronizar com Serpleno Web (não bloqueante): {sync_error}")
                
                return {"success": True, "id": appointment_id}
                
            except Exception as db_error:
                logging.error(f"Erro ao criar agendamento no banco local: {db_error}")
            
            # Fallback para API Desktop
            try:
                # Primeiro, obter o timeId correspondente ao horário
                time_id = self._get_time_id(hora_str)
                
                payload = {
                    "studentId": id_aluno,
                    "date": data_str,
                    "notes": dados.get('motivo', ''),
                    "local": dados.get('local', 'Sala de Atendimento Psicológico'),
                }
                
                # Se temos o timeId, usa ele; caso contrário, usa o time string
                if time_id:
                    payload["timeId"] = time_id
                else:
                    payload["time"] = hora_str
                
                session = self._get_session()
                response = session.post(
                    f"{self.API_DESKTOP_URL}/schedule/appointments/add/",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=5
                )
                
                if response.status_code == 201:
                    data = response.json()
                    appointment_id = data.get('data', {}).get('id')
                    logging.info(f"Agendamento criado via API Desktop: {appointment_id}")
                    return {"success": True, "id": appointment_id}
                elif response.status_code == 403:
                    logging.error(f"Erro 403 ao criar agendamento: autenticação necessária")
                elif response.status_code == 409:
                    data = response.json() if response.text else {}
                    message = data.get('message', 'Conflito de horário')
                    return {"success": False, "message": message}
                else:
                    logging.warning(f"API Desktop retornou status {response.status_code}")
                    
            except requests.exceptions.ConnectionError as api_error:
                logging.warning(f"API Desktop indisponível: {api_error}")
            except requests.exceptions.Timeout as api_error:
                logging.warning(f"Timeout na API Desktop: {api_error}")
            except requests.exceptions.HTTPError as api_error:
                logging.warning(f"Erro HTTP ao criar agendamento via API Desktop: {api_error}")
            except Exception as api_error:
                logging.warning(f"Erro ao criar agendamento via API Desktop: {api_error}")
            
            return {"success": False, "message": "Falha ao criar agendamento"}
        except Exception as e:
            logging.error(f"Erro ao criar agendamento: {e}")
            return {"success": False, "message": str(e)}
    
    def _sync_with_serpleno_web(self, appointment_id, student_id, data_hora, nome, dados):
        """Sincroniza o agendamento com o Serpleno Web via API"""
        try:
            session = self._get_session()
            
            # Preparar payload para o endpoint de agendamentos do Serpleno
            payload = {
                "student": student_id,
                "data_hora": data_hora.isoformat() if hasattr(data_hora, 'isoformat') else str(data_hora),
                "nome": nome,
                "motivo": dados.get('motivo', ''),
                "status": "agendado",
                "local": dados.get('local', 'Sala de Atendimento Psicológico'),
                "profissional": dados.get('profissional', 'Equipe SerPleno'),
                "laudo": dados.get('laudo', 'N/A'),
                "origem": "desktop",
                "desktop_appointment_id": appointment_id
            }
            
            response = session.post(
                f"{self.API_BASE_URL}/api/agendamentos/",
                json=payload,
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logging.info(f"Agendamento {appointment_id} sincronizado com Serpleno Web")
            else:
                logging.warning(f"Falha ao sincronizar agendamento {appointment_id}: status {response.status_code}")
        except Exception as e:
            logging.error(f"Erro ao sincronizar com Serpleno Web: {e}")
            raise
    
    def _get_time_id(self, hora_str):
        """Obtém o ID do horário na tabela disponibilidade"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            time_obj = datetime.strptime(hora_str, "%H:%M").time()
            cursor.execute("SELECT id_disponibilidade FROM disponibilidade WHERE Horario = %s", (time_obj,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return result[0]
            return None
        except Exception as e:
            logging.error(f"Erro ao obter time_id: {e}")
            return None

    def listar_agendamentos(self, data=None):
        """Lista agendamentos usando banco de dados local primeiro, API como fallback"""
        # Primeiro, tenta buscar no banco local (mais rápido)
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
            
            if agendamentos:
                logging.info(f"Agendamentos obtidos via banco local: {len(agendamentos)}")
                return agendamentos
            
            # Se não há dados locais, tenta a API como fallback
            logging.info("Banco local vazio, tentando API como fallback")
            
        except Exception as e:
            logging.error(f"Erro ao listar agendamentos do banco local: {e}")
        
        # Fallback para API
        try:
            session = self._get_session()
            params = {}
            if data:
                params['date'] = data
            
            response = session.get(
                f"{self.API_DESKTOP_URL}/schedule/appointments/",
                params=params,
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('data', {}).get('appointments'):
                    agendamentos = []
                    for apt in result['data']['appointments']:
                        data_hora_str = apt.get('date', '')
                        time_str = apt.get('time', '')
                        if data_hora_str and time_str:
                            data_hora = datetime.strptime(f"{data_hora_str} {time_str}", "%Y-%m-%d %H:%M")
                        else:
                            data_hora = None
                        
                        agendamentos.append({
                            "id_agendamento": apt.get('id'),
                            "nome": apt.get('student', {}).get('name', ''),
                            "id_aluno": apt.get('student', {}).get('id'),
                            "data_hora": data_hora,
                            "motivo": apt.get('notes', ''),
                            "status": apt.get('status', 'agendado'),
                            "local": apt.get('local'),
                            "profissional": apt.get('profissional'),
                            "laudo": None,
                            "origem": 'desktop_web'
                        })
                    logging.info(f"Agendamentos obtidos via API Desktop: {len(agendamentos)}")
                    return agendamentos
        except Exception as e:
            logging.error(f"Erro ao buscar agendamentos via API: {e}")
        
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
        """Deleta um agendamento usando banco local primeiro, API como fallback"""
        # Primeiro, tenta deletar no banco local
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM agendamento WHERE id = %s", (id_agendamento,))
            conn.commit()
            affected = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            if affected > 0:
                logging.info(f"Agendamento {id_agendamento} deletado via banco local")
                return {"success": True}
            
            # Se não encontrou no banco local, tenta API
            logging.info("Agendamento não encontrado no banco local, tentando API")
            
        except Exception as e:
            logging.error(f"Erro ao deletar agendamento do banco local: {e}")
        
        # Fallback para API Desktop
        try:
            session = self._get_session()
            response = session.delete(
                f"{self.API_DESKTOP_URL}/schedule/appointments/delete/{id_agendamento}/",
                headers=self._get_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                logging.info(f"Agendamento {id_agendamento} deletado via API Desktop")
                return {"success": True}
            elif response.status_code == 404:
                logging.warning(f"Agendamento {id_agendamento} não encontrado na API Desktop")
            elif response.status_code == 403:
                logging.warning("Erro 403 ao deletar agendamento via API")
            else:
                logging.warning(f"API Desktop retornou status {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            logging.warning(f"API Desktop indisponível para deletar agendamento: {e}")
        except requests.exceptions.Timeout as e:
            logging.warning(f"Timeout ao deletar agendamento via API: {e}")
        except Exception as e:
            logging.warning(f"Erro ao deletar agendamento via API: {e}")
        
        return {"success": False, "message": "Agendamento não encontrado"}
            
    def adicionar_horario_disponibilidade(self, horario):
        """Adiciona um novo horário à tabela de disponibilidade usando a API do Serpleno Web"""
        try:
            # Validar formato HH:MM
            time_obj = datetime.strptime(horario, "%H:%M").time()
            
            # Tenta adicionar via API Desktop (endpoint correto)
            try:
                payload = {
                    "action": "add",
                    "time": horario
                }
                session = self._get_session()
                response = session.post(
                    f"{self.API_DESKTOP_URL}/schedule/times/manage/", 
                    json=payload, 
                    headers=self._get_headers(),
                    timeout=5
                )
                
                if response.status_code == 201:
                    logging.info(f"Horário {horario} adicionado via API Desktop")
                    return {"success": True}
                elif response.status_code == 409:
                    # Horário já existe
                    logging.warning(f"Horário {horario} já existe na API")
                    return {"success": False, "message": "Este horário já existe"}
                elif response.status_code == 403:
                    # Erro de autenticação - precisa fazer login
                    logging.error(f"Erro 403 ao adicionar horário: autenticação necessária")
                    return {"success": False, "message": "Erro de autenticação. Faça login novamente."}
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.ConnectionError as api_error:
                logging.warning(f"API Desktop indisponível, usando banco local: {api_error}")
            except requests.exceptions.Timeout as api_error:
                logging.warning(f"Timeout na API Desktop, usando banco local: {api_error}")
            except requests.exceptions.HTTPError as api_error:
                logging.warning(f"Erro HTTP ao adicionar horário via API Desktop: {api_error}")
            except Exception as api_error:
                logging.warning(f"Erro ao adicionar horário via API Desktop: {api_error}")
            
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
        """Remove a horário da tabela de disponibilidade usando a API do Serpleno Web"""
        try:
            # Validar formato HH:MM
            time_obj = datetime.strptime(horario, "%H:%M").time()
            
            # Tenta remover via API Desktop (endpoint correto)
            try:
                payload = {
                    "action": "remove",
                    "time": horario
                }
                session = self._get_session()
                response = session.post(
                    f"{self.API_DESKTOP_URL}/schedule/times/manage/",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=5
                )
                
                if response.status_code == 200:
                    logging.info(f"Horário {horario} removido via API Desktop")
                    return {"success": True}
                elif response.status_code == 403:
                    # Erro de autenticação - precisa fazer login
                    logging.error(f"Erro 403 ao remover horário: autenticação necessária")
                    return {"success": False, "message": "Erro de autenticação. Faça login novamente."}
                elif response.status_code == 404:
                    logging.warning(f"Horário {horario} não encontrado na API")
                    return {"success": False, "message": "Horário não encontrado"}
                elif response.status_code == 409:
                    # Existem agendamentos futuros
                    data = response.json() if response.text else {}
                    message = data.get('message', 'Existem agendamentos futuros')
                    logging.warning(f"Conflito ao remover horário: {message}")
                    return {"success": False, "message": message}
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.ConnectionError as api_error:
                logging.warning(f"API Desktop indisponível, usando banco local: {api_error}")
            except requests.exceptions.Timeout as api_error:
                logging.warning(f"Timeout na API Desktop, usando banco local: {api_error}")
            except requests.exceptions.HTTPError as api_error:
                logging.warning(f"Erro HTTP ao remover horário via API Desktop: {api_error}")
            except Exception as api_error:
                logging.warning(f"Erro ao remover horário via API Desktop: {api_error}")
            
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
            session = self._get_session()
            response = session.get(
                f"{self.API_BASE_URL}/api/agendamentos/?desktop_appointment_id={appointment_id}",
                headers=self._get_headers(),
                timeout=5
            )
            response.raise_for_status()
            
            if response.json():
                # Atualiza agendamento existente
                agendamento_api_id = response.json()[0]['id_agendamentos']
                response = session.put(
                    f"{self.API_BASE_URL}/api/agendamentos/{agendamento_api_id}/",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=5
                )
            else:
                # Cria novo agendamento
                response = session.post(
                    f"{self.API_BASE_URL}/api/agendamentos/",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=5
                )
            
            response.raise_for_status()
            logging.info(f"Agendamento {appointment_id} sincronizado com API")
        except requests.exceptions.ConnectionError as e:
            logging.warning(f"API indisponível para sincronização do agendamento {appointment_id}: {e}")
            # Não levanta exceção - o agendamento local já foi salvo
        except requests.exceptions.Timeout as e:
            logging.warning(f"Timeout ao sincronizar agendamento {appointment_id}: {e}")
            # Não levanta exceção - o agendamento local já foi salvo
        except requests.exceptions.HTTPError as e:
            logging.warning(f"Erro HTTP ao sincronizar agendamento {appointment_id}: {e}")
            # Não levanta exceção - o agendamento local já foi salvo
        except Exception as e:
            logging.error(f"Erro ao sincronizar agendamento {appointment_id} com API: {e}")
            # Não levanta exceção - o agendamento local já foi salvo
    
    def _convert_status_frontend_to_backend(self, status):
        """Converte status do frontend para o formato do banco de dados (Serpleno Web)"""
        # O Serpleno Web usa status em minúsculo: 'agendado', 'cancelado', 'concluido'
        # O banco MySQL compartilhado espera este formato
        status_map = {
            "Agendado": "agendado",
            "Realizado": "concluido",
            "Cancelado": "cancelado",
            "Faltou": "cancelado",
            "agendado": "agendado",
            "concluido": "concluido",
            "cancelado": "cancelado"
        }
        return status_map.get(status, "agendado")
    
    def _convert_status_backend_to_frontend(self, status):
        """Converte status do backend para o formato do frontend (Serpleno Web)"""
        # O Serpleno Web espera status em minúsculo: 'agendado', 'cancelado', 'concluido'
        status_map = {
            "scheduled": "agendado",
            "completed": "concluido",
            "cancelled": "cancelado",
            "missed": "cancelado",  # Mapeia "faltou" para "cancelado"
            "agendado": "agendado",
            "concluido": "concluido",
            "cancelado": "cancelado"
        }
        return status_map.get(status, "agendado")

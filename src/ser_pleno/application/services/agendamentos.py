from ser_pleno.config.config import API_ROOT_URL, DESKTOP_API_URL, DESKTOP_API_TOKEN
from ser_pleno.repositories.agendamentos import AgendamentoRepository
from ser_pleno.repositories.estudantes import EstudanteRepository
import logging
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


def _invalidate_dashboard_cache() -> None:
    try:
        from ser_pleno.repositories.dashboard import invalidate_dashboard_cache
        invalidate_dashboard_cache()
    except Exception:
        pass

class ServicoAgendamento:
    # URL base da API do Serpleno Web (agora usa config oficial)
    API_BASE_URL = API_ROOT_URL
    # URL base da API Desktop (agora usa config oficial)
    API_DESKTOP_URL = DESKTOP_API_URL
    # Token para autenticação na API
    API_TOKEN = DESKTOP_API_TOKEN or "serpleno-desktop-token-2024"
    
    def __init__(self):
        self.repo = AgendamentoRepository()
        self.repo_estudante = EstudanteRepository()
    
    def listar_estudantes(self):
        """Retorna estudantes disponíveis para agendamento."""
        try:
            return self.repo_estudante.listar() or []
        except Exception as e:
            logging.error(f"Erro ao listar estudantes: {e}")
            return []
    
    def listar_horarios_base(self):
        """Retorna horários ativos da grade."""
        try:
            return self.repo.listar_horarios_base()
        except Exception as e:
            logging.error(f"Erro ao listar horários base: {e}")
            return []
    
    def _get_session(self):
        """Retorna a sessão HTTP do serviço de autenticação"""
        auth = get_auth_service()
        if auth and hasattr(auth, 'get_session'):
            session = auth.get_session()
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
        auth = get_auth_service()
        if auth and hasattr(auth, 'csrf_token') and auth.csrf_token:
            headers["X-CSRFToken"] = auth.csrf_token
        return headers
    
    def _convert_status_frontend_to_backend(self, status):
        """Converte status do frontend para o formato do banco de dados (Serpleno Web)"""
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
        status_map = {
            "scheduled": "agendado",
            "completed": "concluido",
            "cancelled": "cancelado",
            "missed": "cancelado",
            "agendado": "agendado",
            "concluido": "concluido",
            "cancelado": "cancelado"
        }
        return status_map.get(status, "agendado")
    
    def verificar_disponibilidade(self, data, time_str):
        """Verifica se um horário está disponível usando o repositório local"""
        try:
            result = self.repo.verificar_disponibilidade(data, time_str)
            return result is None
        except Exception as e:
            logging.error(f"Erro ao verificar disponibilidade: {e}")
            return False
    
    def criar_agendamento(self, dados):
        """Cria um agendamento usando banco de dados local primeiro, API como fallback"""
        try:
            data_hora = datetime.strptime(dados['data_hora'], "%Y-%m-%d %H:%M")
            data_str = data_hora.strftime("%Y-%m-%d")
            hora_str = data_hora.strftime("%H:%M")
            id_aluno = int(dados['id_aluno'])
            status = self._convert_status_frontend_to_backend(dados.get('status', 'Agendado'))
            
            # Obter nome do aluno
            aluno_result = self.repo.obter_nome_aluno(id_aluno)
            nome_aluno = aluno_result.get("nome") if aluno_result else f"Aluno {id_aluno}"
            nome_agendamento = f"Atendimento - {nome_aluno}"
            
            # Criar no banco local
            try:
                self.repo.criar_agendamento(
                    id_aluno=id_aluno,
                    data_hora=data_hora,
                    nome_agendamento=nome_agendamento,
                    motivo=dados.get('motivo', ''),
                    status=status,
                    local=dados.get('local', 'Sala de Atendimento Psicológico'),
                    profissional=dados.get('profissional', None),
                    laudo=dados.get('laudo', 'N/A'),
                    origem='desktop'
                )
                appointment_id = self.repo.obter_ultimo_id_inserido()
                logging.info(f"Agendamento criado via banco local: {appointment_id}")
                _invalidate_dashboard_cache()

                # Tenta sincronizar com o Serpleno Web em background
                try:
                    self._sync_with_serpleno_web(appointment_id, id_aluno, data_hora, nome_agendamento, dados)
                except Exception as sync_error:
                    logging.warning(f"Erro ao sincronizar com Serpleno Web (não bloqueante): {sync_error}")
                
                return {"success": True, "id": appointment_id}
            except Exception as db_error:
                logging.error(f"Erro ao criar agendamento no banco local: {db_error}")
            
            # Fallback para API Desktop
            return self._criar_agendamento_api(id_aluno, data_str, hora_str, dados)
        except Exception as e:
            logging.error(f"Erro ao criar agendamento: {e}")
            return {"success": False, "message": str(e)}
    
    def _criar_agendamento_api(self, id_aluno, data_str, hora_str, dados):
        """Cria agendamento via API Desktop como fallback."""
        try:
            time_id = self.repo.obter_time_id(hora_str)
            payload = {
                "studentId": id_aluno,
                "date": data_str,
                "notes": dados.get('motivo', ''),
                "local": dados.get('local', 'Sala de Atendimento Psicológico'),
            }
            if time_id:
                payload["timeId"] = time_id.get("id_disponibilidade")
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
        except Exception as api_error:
            logging.warning(f"Erro ao criar agendamento via API Desktop: {api_error}")
        
        return {"success": False, "message": "Falha ao criar agendamento"}
    
    def _sync_with_serpleno_web(self, appointment_id, student_id, data_hora, nome, dados):
        """Sincroniza o agendamento com o Serpleno Web via API"""
        try:
            agendamento = self.repo.obter_agendamento_para_sincronizacao(appointment_id)
            if not agendamento:
                return
            
            payload = {
                "nome": f"Atendimento - {agendamento['nome_aluno']}",
                "data_hora": data_hora.isoformat() if hasattr(data_hora, 'isoformat') else str(data_hora),
                "motivo": dados.get('motivo', ''),
                "status": "agendado",
                "laudo": dados.get('laudo', 'N/A'),
                "student": student_id,
                "origem": "desktop",
                "desktop_appointment_id": appointment_id,
                "profissional": dados.get('profissional', 'Equipe SerPleno'),
                "local": dados.get('local', 'Sala de Atendimento Psicológico')
            }
            
            session = self._get_session()
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
    
    def listar_agendamentos(self, data=None):
        """Lista agendamentos usando banco de dados local primeiro, API como fallback"""
        try:
            rows = self.repo.listar_agendamentos(data)
            if rows:
                logging.info(f"Agendamentos obtidos via banco local: {len(rows)} registros")
                agendamentos = []
                for row in rows:
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
                return agendamentos
            logging.info("Banco local vazio, tentando API como fallback")
        except Exception as e:
            logging.error(f"Erro ao listar agendamentos do banco local: {e}")
        
        # Fallback para API
        return self._listar_agendamentos_api(data)
    
    def _listar_agendamentos_api(self, data=None):
        """Lista agendamentos via API Desktop como fallback."""
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
            logging.warning(f"Erro ao buscar agendamentos via API: {e}, usando banco local")
        
        return []
    
    def atualizar_agendamento(self, id_agendamento, dados):
        """Atualiza um agendamento usando o repositório local"""
        try:
            data_hora = datetime.strptime(dados['data_hora'], "%Y-%m-%d %H:%M")
            status = self._convert_status_frontend_to_backend(dados.get('status', 'Agendado'))
            
            self.repo.atualizar_agendamento(
                id_agendamento=id_agendamento,
                id_aluno=int(dados['id_aluno']),
                data_hora=data_hora,
                motivo=dados.get('motivo', ''),
                status=status,
                local=dados.get('local', None),
                profissional=dados.get('profissional', None),
                laudo=dados.get('laudo', None),
                origem='desktop'
            )
            _invalidate_dashboard_cache()

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
        try:
            affected = self.repo.deletar_agendamento(id_agendamento)
            if affected > 0:
                logging.info(f"Agendamento {id_agendamento} deletado via banco local")
                _invalidate_dashboard_cache()
                return {"success": True}
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
        except Exception as e:
            logging.warning(f"Erro ao deletar agendamento via API: {e}")
        
        return {"success": False, "message": "Agendamento não encontrado"}
    
    def adicionar_horario_disponibilidade(self, horario):
        """Adiciona um novo horário à tabela de disponibilidade"""
        try:
            # Tenta adicionar via API Desktop primeiro
            try:
                payload = {"action": "add", "time": horario}
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
                    logging.warning(f"Horário {horario} já existe na API")
                    return {"success": False, "message": "Este horário já existe"}
                elif response.status_code == 403:
                    logging.error(f"Erro 403 ao adicionar horário: autenticação necessária")
                    return {"success": False, "message": "Erro de autenticação. Faça login novamente."}
            except Exception as api_error:
                logging.warning(f"API Desktop indisponível, usando banco local: {api_error}")
            
            # Fallback para banco local
            result = self.repo.verificar_horario_existe(horario)
            if result:
                return {"success": False, "message": "Este horário já existe"}
            
            self.repo.adicionar_horario_disponibilidade(horario)
            logging.info(f"Horário {horario} adicionado via banco local")
            _invalidate_dashboard_cache()
            return {"success": True}
        except ValueError:
            return {"success": False, "message": "Formato de horário inválido. Use HH:MM"}
        except Exception as e:
            logging.error(f"Erro ao adicionar horário: {e}")
            return {"success": False, "message": str(e)}
    
    def remover_horario_disponibilidade(self, horario):
        """Remove um horário da tabela de disponibilidade"""
        try:
            # Tenta remover via API Desktop primeiro
            try:
                payload = {"action": "remove", "time": horario}
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
                    logging.error(f"Erro 403 ao remover horário: autenticação necessária")
                    return {"success": False, "message": "Erro de autenticação. Faça login novamente."}
                elif response.status_code == 404:
                    logging.warning(f"Horário {horario} não encontrado na API")
                    return {"success": False, "message": "Horário não encontrado"}
                elif response.status_code == 409:
                    data = response.json() if response.text else {}
                    message = data.get('message', 'Existem agendamentos futuros')
                    logging.warning(f"Conflito ao remover horário: {message}")
                    return {"success": False, "message": message}
            except Exception as api_error:
                logging.warning(f"API Desktop indisponível, usando banco local: {api_error}")
            
            # Fallback para banco local
            result = self.repo.remover_horario_disponibilidade(horario)
            if isinstance(result, dict) and not result.get("success"):
                return result
            logging.info(f"Horário {horario} removido via banco local")
            _invalidate_dashboard_cache()
            return {"success": True}
        except ValueError:
            return {"success": False, "message": "Formato de horário inválido. Use HH:MM"}
        except Exception as e:
            logging.error(f"Erro ao remover horário: {e}")
            return {"success": False, "message": str(e)}
    
    def _sync_with_api(self, appointment_id):
        """Sincroniza um agendamento com a API do Serpleno Web"""
        try:
            agendamento = self.repo.obter_agendamento_para_sincronizacao(appointment_id)
            if not agendamento:
                raise Exception(f"Agendamento {appointment_id} não encontrado")
            
            payload = {
                "nome": f"Atendimento - {agendamento['nome_aluno']}",
                "data_hora": agendamento['data_hora'].isoformat() if hasattr(agendamento['data_hora'], 'isoformat') else str(agendamento['data_hora']),
                "motivo": agendamento['motivo'],
                "status": self._convert_status_backend_to_frontend(agendamento['status']),
                "laudo": agendamento['laudo'] or "N/A",
                "student": agendamento['student_id'],
                "origem": "desktop",
                "desktop_appointment_id": agendamento['id'],
                "profissional": agendamento['profissional'] or "Equipe SerPleno",
                "local": agendamento['local'] or "Sala de Atendimento Psicológico"
            }
            
            session = self._get_session()
            response = session.get(
                f"{self.API_BASE_URL}/api/agendamentos/?desktop_appointment_id={appointment_id}",
                headers=self._get_headers(),
                timeout=5
            )
            response.raise_for_status()
            
            if response.json():
                agendamento_api_id = response.json()[0]['id_agendamentos']
                response = session.put(
                    f"{self.API_BASE_URL}/api/agendamentos/{agendamento_api_id}/",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=5
                )
            else:
                response = session.post(
                    f"{self.API_BASE_URL}/api/agendamentos/",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=5
                )
            
            response.raise_for_status()
            logging.info(f"Agendamento {appointment_id} sincronizado com API")
        except Exception as e:
            logging.warning(f"Erro ao sincronizar agendamento {appointment_id} com API: {e}")
            # Não levanta exceção - o agendamento local já foi salvo

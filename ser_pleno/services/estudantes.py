"""
Serviço de Estudantes para o Desktop CustomTkinter
Integração com a API do SerPleno Web
"""
import logging
from typing import Optional, Dict, Any, List

try:
    import requests
except Exception:
    requests = None  # type: ignore

from services.api import api, get_auth_service

logger = logging.getLogger(__name__)


class ServicoEstudante:
    """Serviço para gerenciar estudantes via API do SerPleno Web"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1/desktop"
    
    def _get_session(self):
        """Retorna a sessão HTTP autenticada"""
        auth = get_auth_service()
        if auth and hasattr(auth, 'get_session'):
            return auth.get_session()
        return requests
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers com CSRF token se disponível"""
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        auth = get_auth_service()
        if auth:
            # Tenta obter headers do serviço de autenticação
            if hasattr(auth, 'get_headers'):
                return auth.get_headers()
            # Fallback: tenta obter CSRF token diretamente
            if hasattr(auth, 'csrf_token') and auth.csrf_token:
                headers['X-CSRFToken'] = auth.csrf_token
        return headers
    
    def listar_estudantes(self, busca: Optional[str] = None, possui_laudo: Optional[bool] = None, 
                          requer_atencao: Optional[bool] = None, pagina: int = 1) -> Dict[str, Any]:
        """
        Lista estudantes com filtros opcionais via API
        
        Args:
            busca: Termo de busca para nome ou email
            possui_laudo: Filtrar por possuir laudo médico
            requer_atencao: Filtrar por requerer atenção
            pagina: Número da página
            
        Returns:
            Dict com success, data (lista de estudantes)
        """
        try:
            params: Dict[str, Any] = {'page': pagina}
            if busca:
                params['search'] = busca
            if possui_laudo is not None:
                params['has_medical_report'] = possui_laudo
            if requer_atencao is not None:
                params['requires_attention'] = requer_atencao
            
            url = f"{self.base_url}/students/"
            session = self._get_session()
            
            if session and requests:
                response = session.get(url, params=params, timeout=10)
                if response.ok:
                    try:
                        data = response.json()
                        logger.info(f"Estudantes carregados via API: {len(data.get('data', []))} registros")
                        return data
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        logger.debug(f"Conteúdo da resposta: {response.text[:500] if response.text else 'vazio'}")
                        return self._fallback_listar_estudantes(busca, possui_laudo, requer_atencao, pagina)
                else:
                    logger.debug(f"API retornou status {response.status_code}, usando fallback local")
                    return self._fallback_listar_estudantes(busca, possui_laudo, requer_atencao, pagina)
            
            return self._fallback_listar_estudantes(busca, possui_laudo, requer_atencao, pagina)
            
        except Exception as e:
            logger.exception(f"Erro ao listar estudantes: {e}")
            return self._fallback_listar_estudantes(busca, possui_laudo, requer_atencao, pagina)
    
    def _fallback_listar_estudantes(self, busca: Optional[str] = None, possui_laudo: Optional[bool] = None,
                                     requer_atencao: Optional[bool] = None, pagina: int = 1) -> Dict[str, Any]:
        """Fallback para buscar estudantes diretamente do banco local quando API indisponível"""
        try:
            from config.db_config import get_db_connection
            
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Join com auth_user para obter e-mail de contato
            query = "SELECT a.*, u.email AS contact FROM aluno a LEFT JOIN auth_user u ON a.user_id = u.id WHERE 1=1"
            params = []

            if busca:
                query += " AND (a.nome LIKE %s OR u.email LIKE %s)"
                params.extend([f"%{busca}%", f"%{busca}%"])

            if possui_laudo is not None:
                query += " AND a.has_medical_report = %s"
                params.append(possui_laudo)

            if requer_atencao is not None:
                query += " AND a.requires_attention = %s"
                params.append(requer_atencao)

            offset = (pagina - 1) * 10
            query += " LIMIT 10 OFFSET %s"
            params.append(offset)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            logger.info(f"Encontrados {len(rows)} estudantes no banco de dados local (fallback)")
            
            # Mapear colunas do banco para o formato esperado pela UI
            students = []
            for r in rows:
                students.append({
                    'id': r.get('id_aluno'),
                    'name': r.get('nome'),
                    'course': r.get('curso'),
                    'age': r.get('age') or r.get('idade'),
                    'has_medical_report': bool(r.get('has_medical_report')),
                    'requires_attention': bool(r.get('requires_attention')),
                    'contact': r.get('contact') or r.get('email') or '',
                    'priority_level': r.get('priority_level') or 0,
                })
            connection.close()
            return {"success": True, "data": students}
        except Exception as e:
            logger.error(f"Erro no fallback ao listar estudantes: {e}")
            return {"success": False, "error": str(e), "data": []}

    def obter_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """
        Obtém detalhes de um estudante específico via API
        
        Args:
            id_estudante: ID do estudante
            
        Returns:
            Dict com success, data (dados do estudante)
        """
        try:
            url = f"{self.base_url}/students/{id_estudante}/"
            session = self._get_session()
            
            if session and requests:
                response = session.get(url, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return self._fallback_obter_estudante(id_estudante)
                else:
                    logger.debug(f"API retornou status {response.status_code}, usando fallback local")
                    return self._fallback_obter_estudante(id_estudante)
            
            return self._fallback_obter_estudante(id_estudante)
            
        except Exception as e:
            logger.exception(f"Erro ao obter estudante: {e}")
            return self._fallback_obter_estudante(id_estudante)
    
    def _fallback_obter_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Fallback para obter estudante do banco local"""
        try:
            from config.db_config import get_db_connection
            
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            # Buscar aluno com email (join em auth_user)
            cursor.execute("SELECT a.*, u.email AS contact FROM aluno a LEFT JOIN auth_user u ON a.user_id = u.id WHERE a.id_aluno = %s", (id_estudante,))
            r = cursor.fetchone()
            student = None
            if r:
                student = {
                    'id': r.get('id_aluno'),
                    'name': r.get('nome'),
                    'course': r.get('curso'),
                    'age': r.get('age') or r.get('idade'),
                    'phone': r.get('phone') or '',
                    'contact': r.get('contact') or '',
                    'emergency_contact': r.get('emergency_contact') or '',
                    'emergency_phone': r.get('emergency_phone') or '',
                    'has_medical_report': bool(r.get('has_medical_report')),
                    'requires_attention': bool(r.get('requires_attention')),
                    'attention_reason': r.get('attention_reason') or r.get('attention_notes') or ''
                }
                # Buscar intervenções relacionadas (desktop_intervention)
                cursor.execute("SELECT id, date, intervention_notes as notes FROM desktop_intervention WHERE student_id = %s ORDER BY date DESC LIMIT 10", (id_estudante,))
                invs = cursor.fetchall()
                interventions = []
                for inv in invs:
                    interventions.append({
                        'id': inv.get('id'),
                        'date': str(inv.get('date')),
                        'notes': inv.get('notes')
                    })
                student['interventions'] = interventions
            connection.close()
            return {"success": True, "data": student}
        except Exception as e:
            logger.error(f"Erro no fallback ao obter estudante: {e}")
            return {"success": False, "error": str(e), "data": None}

    def obter_relatorio_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """
        Retorna o detalhe do estudante junto com seus registros de humor via API
        
        Args:
            id_estudante: ID do estudante
            
        Returns:
            Dict com success, data (student, moods)
        """
        try:
            url = f"{self.base_url}/students/{id_estudante}/report/"
            session = self._get_session()
            
            if session and requests:
                response = session.get(url, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return self._fallback_obter_relatorio_estudante(id_estudante)
                else:
                    logger.debug(f"API retornou status {response.status_code}, usando fallback local")
                    return self._fallback_obter_relatorio_estudante(id_estudante)
            
            return self._fallback_obter_relatorio_estudante(id_estudante)
            
        except Exception as e:
            logger.exception(f"Erro ao obter relatório do estudante: {e}")
            return self._fallback_obter_relatorio_estudante(id_estudante)
    
    def _fallback_obter_relatorio_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Fallback para obter relatório do estudante do banco local"""
        # Reutiliza o método de detalhe já existente
        student_resp = self._fallback_obter_estudante(id_estudante)
        student = student_resp.get('data') if isinstance(student_resp, dict) else None

        # Import local para evitar dependências circulares em tempo de import
        from services.bem_estar import ServicoBemEstar
        moods_resp = ServicoBemEstar().obter_humor_estudante(id_estudante)
        moods = moods_resp.get('data') if isinstance(moods_resp, dict) else moods_resp

        return {"success": True, "data": {"student": student, "moods": moods}}

    def criar_estudante(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um novo estudante via API
        
        Args:
            dados: Dict com os dados do estudante:
                - name: Nome do estudante
                - contact: Email de contato
                - has_medical_report: Se possui laudo médico
                - requires_attention: Se requer atenção
                - course: Curso (opcional)
                - age: Idade (opcional)
                
        Returns:
            Dict com success, message, data (id do estudante criado)
        """
        try:
            # Endpoint correto conforme api_urls.py: students/add/
            url = f"{self.base_url}/students/add/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                response = session.post(url, json=dados, headers=headers, timeout=10)
                if response.ok:
                    try:
                        result = response.json()
                        logger.info(f"Estudante criado via API: {result}")
                        return result
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return self._fallback_criar_estudante(dados)
                else:
                    logger.warning(f"Erro ao criar estudante via API: {response.status_code}")
                    return self._fallback_criar_estudante(dados)
            
            return self._fallback_criar_estudante(dados)
            
        except Exception as e:
            logger.exception(f"Erro ao criar estudante: {e}")
            return self._fallback_criar_estudante(dados)
    
    def _fallback_criar_estudante(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para criar estudante no banco local"""
        try:
            from config.db_config import get_db_connection
            
            connection = get_db_connection()
            cursor = connection.cursor()
            query = "INSERT INTO aluno (nome, email, has_medical_report, requires_attention) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (dados.get('name') or dados.get('nome'), dados.get('contact') or dados.get('email'), dados.get('has_medical_report', False), dados.get('requires_attention', False)))
            connection.commit()
            connection.close()
            return {"success": True, "message": "Estudante criado com sucesso"}
        except Exception as e:
            logger.error(f"Erro no fallback ao criar estudante: {e}")
            return {"success": False, "error": str(e)}

    def atualizar_estudante(self, id_estudante: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza um estudante existente via API
        
        Args:
            id_estudante: ID do estudante a ser atualizado
            dados: Dict com os dados do estudante
            
        Returns:
            Dict com success, message
        """
        try:
            url = f"{self.base_url}/students/{id_estudante}/update/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                response = session.put(url, json=dados, headers=headers, timeout=10)
                if response.ok:
                    try:
                        result = response.json()
                        logger.info(f"Estudante atualizado via API: {result}")
                        return result
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return self._fallback_atualizar_estudante(id_estudante, dados)
                else:
                    logger.warning(f"Erro ao atualizar estudante via API: {response.status_code}")
                    return self._fallback_atualizar_estudante(id_estudante, dados)
            
            return self._fallback_atualizar_estudante(id_estudante, dados)
            
        except Exception as e:
            logger.exception(f"Erro ao atualizar estudante: {e}")
            return self._fallback_atualizar_estudante(id_estudante, dados)
    
    def _fallback_atualizar_estudante(self, id_estudante: int, dados: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para atualizar estudante no banco local"""
        try:
            from config.db_config import get_db_connection
            
            connection = get_db_connection()
            cursor = connection.cursor()
            query = "UPDATE aluno SET nome = %s, email = %s, has_medical_report = %s, requires_attention = %s WHERE id_aluno = %s"
            cursor.execute(query, (dados.get('name') or dados.get('nome'), dados.get('contact') or dados.get('email'), dados.get('has_medical_report', False), dados.get('requires_attention', False), id_estudante))
            connection.commit()
            connection.close()
            return {"success": True, "message": "Estudante atualizado com sucesso"}
        except Exception as e:
            logger.error(f"Erro no fallback ao atualizar estudante: {e}")
            return {"success": False, "error": str(e)}

    def deletar_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """
        Deleta um estudante via API
        
        Args:
            id_estudante: ID do estudante
            
        Returns:
            Dict com success, message
        """
        try:
            url = f"{self.base_url}/students/{id_estudante}/delete/"
            session = self._get_session()
            headers = self._get_headers()
            
            if session and requests:
                response = session.delete(url, headers=headers, timeout=10)
                if response.ok:
                    try:
                        return response.json()
                    except Exception as json_err:
                        logger.debug(f"Resposta não é JSON válido: {json_err}")
                        return self._fallback_deletar_estudante(id_estudante)
                else:
                    logger.warning(f"Erro ao deletar estudante via API: {response.status_code}")
                    return self._fallback_deletar_estudante(id_estudante)
            
            return self._fallback_deletar_estudante(id_estudante)
            
        except Exception as e:
            logger.exception(f"Erro ao deletar estudante: {e}")
            return self._fallback_deletar_estudante(id_estudante)
    
    def _fallback_deletar_estudante(self, id_estudante: int) -> Dict[str, Any]:
        """Fallback para deletar estudante no banco local"""
        try:
            from config.db_config import get_db_connection
            
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM aluno WHERE id_aluno = %s", (id_estudante,))
            connection.commit()
            connection.close()
            return {"success": True, "message": "Estudante deletado com sucesso"}
        except Exception as e:
            logger.error(f"Erro no fallback ao deletar estudante: {e}")
            return {"success": False, "error": str(e)}


# Instância global para fácil acesso
servico_estudante = ServicoEstudante()

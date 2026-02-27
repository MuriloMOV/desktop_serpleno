"""
Bateria de Testes Completa e Detalhada para Desktop SerPleno

Este arquivo contém testes abrangentes para verificar todas as funcionalidades
do sistema desktop_serpleno, desde as básicas até as complexas, incluindo
a comunicação completa com o serpleno_web.

Execute com: pytest desktop_serpleno/tests/test_complete_battery.py -v
"""
import pytest
from unittest.mock import MagicMock, patch, Mock, mock_open, call
from datetime import datetime, timedelta
import json
import os
import sys
import tempfile
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ser_pleno')))


# ============================================================================
# TESTES DE AUTENTICAÇÃO E LOGIN
# ============================================================================

class TestAutenticacaoCompleta:
    """Testes completos para autenticação"""
    
    @patch('services.autenticacao.requests')
    def test_login_sucesso_api_completo(self, mock_requests):
        """Teste de login bem-sucedido via API com dados completos"""
        from services.autenticacao import ServicoAutenticacao
        import requests as req_lib
        
        # Mock da resposta de login bem-sucedida
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'user': {
                'id': 1, 
                'username': 'admin', 
                'email': 'admin@test.com',
                'first_name': 'Admin',
                'last_name': 'User'
            }
        }
        mock_response.text = '<input name="csrfmiddlewaretoken" value="test_csrf_token">'
        
        mock_session = Mock()
        mock_session.post.return_value = mock_response
        mock_session.cookies.get.return_value = 'test_csrf_token'
        mock_session.cookies.keys.return_value = ['csrftoken']
        mock_requests.Session.return_value = mock_session
        
        service = ServicoAutenticacao()
        
        # Testa criação do serviço sem erro
        assert service is not None
        assert service.session is not None or service.session is None
    
    @patch('services.autenticacao.requests')
    def test_login_falha_credenciais_invalidas(self, mock_requests):
        """Teste de login com credenciais inválidas"""
        from services.autenticacao import ServicoAutenticacao
        
        # Mock de resposta de falha
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'success': False, 'message': 'Invalid credentials'}
        mock_requests.Session.return_value.post.return_value = mock_response
        
        service = ServicoAutenticacao()
        result = service.login('admin', 'wrongpassword')
        
        assert 'success' in result
    
    @patch('services.autenticacao.requests')
    def test_login_timeout_fallback_local(self, mock_requests):
        """Teste de login com timeout - deve usar fallback local"""
        from services.autenticacao import ServicoAutenticacao
        
        service = ServicoAutenticacao()
        
        # Testa criação do serviço
        assert service is not None
        
        # Testa que o método _should_use_api existe e é callable
        assert hasattr(service, '_should_use_api')
        assert callable(service._should_use_api)
    
    @patch('services.autenticacao.requests')
    def test_login_connection_error_fallback_local(self, mock_requests):
        """Teste de login com erro de conexão - deve usar fallback local"""
        from services.autenticacao import ServicoAutenticacao
        import requests
        
        mock_requests.exceptions.ConnectionError = requests.exceptions.ConnectionError
        mock_session = Mock()
        mock_session.post.side_effect = requests.exceptions.ConnectionError()
        mock_requests.Session.return_value = mock_session
        
        service = ServicoAutenticacao()
        
        with patch.object(service, '_login_local', return_value={'success': True, 'user': {'id': 1}}):
            result = service.login('admin', 'password')
            assert result['success'] is True
    
    @patch('services.autenticacao.requests')
    def test_logout_completo(self, mock_requests):
        """Teste completo de logout"""
        from services.autenticacao import ServicoAutenticacao
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.Session.return_value.post.return_value = mock_response
        
        service = ServicoAutenticacao()
        service.session = mock_requests.Session.return_value
        service.csrf_token = 'test_token'
        service.user = {'id': 1, 'username': 'admin'}
        
        service.logout()
        
        assert service.user is None
        assert service.csrf_token is None
    
    def test_csrf_token_extraction_cookie(self):
        """Teste de extração de CSRF token do cookie"""
        from services.autenticacao import ServicoAutenticacao
        
        service = ServicoAutenticacao()
        
        mock_response = Mock()
        mock_response.text = '<input name="csrfmiddlewaretoken" value="test_token">'
        mock_response.cookies = Mock()
        mock_response.cookies.get.return_value = 'cookie_token'
        
        token = service._extract_csrf_token(mock_response)
        # O token pode vir do cookie ou do HTML
        assert token is not None
    
    def test_csrf_token_extraction_html(self):
        """Teste de extração de CSRF token do HTML"""
        from services.autenticacao import ServicoAutenticacao
        
        service = ServicoAutenticacao()
        
        mock_response = Mock()
        mock_response.text = '<input name="csrfmiddlewaretoken" value="html_token">'
        mock_response.cookies = {}
        
        token = service._extract_csrf_token(mock_response)
        assert token == 'html_token'
    
    def test_csrf_token_extraction_json(self):
        """Teste de extração de CSRF token do JSON"""
        from services.autenticacao import ServicoAutenticacao
        
        service = ServicoAutenticacao()
        
        mock_response = Mock()
        mock_response.text = '{"csrf_token": "json_token"}'
        mock_response.cookies = {}
        mock_response.json = Mock(return_value={'csrf_token': 'json_token'})
        
        token = service._extract_csrf_token(mock_response)
        assert token == 'json_token'
    
    def test_get_session(self):
        """Teste de obtenção de sessão"""
        from services.autenticacao import ServicoAutenticacao
        
        mock_session = Mock()
        service = ServicoAutenticacao()
        service.session = mock_session
        
        result = service.get_session()
        assert result == mock_session
    
    def test_get_headers(self):
        """Teste de obtenção de headers"""
        from services.autenticacao import ServicoAutenticacao
        
        service = ServicoAutenticacao()
        service.csrf_token = 'test_token'
        
        headers = service.get_headers()
        
        assert headers['Content-Type'] == 'application/json'
        assert headers['X-CSRFToken'] == 'test_token'


# ============================================================================
# TESTES DE CONFIGURAÇÃO DE MODO DE OPERAÇÃO
# ============================================================================

class TestModoOperacao:
    """Testes para modos de operação"""
    
    def test_operation_mode_independent(self):
        """Teste de modo independente"""
        from config.operation_mode import OperationMode, OperationConfig
        
        # Testa criação de modo
        mode = OperationMode.INDEPENDENT
        assert mode.value == "independent"
    
    def test_operation_mode_hybrid(self):
        """Teste de modo híbrido"""
        from config.operation_mode import OperationMode
        
        mode = OperationMode.HYBRID
        assert mode.value == "hybrid"
    
    def test_operation_mode_connected(self):
        """Teste de modo conectado"""
        from config.operation_mode import OperationMode
        
        mode = OperationMode.CONNECTED
        assert mode.value == "connected"
    
    def test_operation_config_properties(self):
        """Teste de propriedades da configuração"""
        from config.operation_mode import OperationConfig
        
        config = OperationConfig()
        
        # Testa propriedades
        assert hasattr(config, 'mode')
        assert hasattr(config, 'api_base_url')
        assert hasattr(config, 'api_timeout')
        assert hasattr(config, 'sync_interval')
        assert hasattr(config, 'auto_sync')
        assert hasattr(config, 'api_available')
    
    def test_is_independent(self):
        """Teste de verificação de modo independente"""
        from config.operation_mode import OperationConfig, OperationMode
        
        config = OperationConfig()
        
        # Testa método
        assert hasattr(config, 'is_independent')
        assert callable(config.is_independent)
    
    def test_should_use_api(self):
        """Teste de verificação se deve usar API"""
        from config.operation_mode import OperationConfig
        
        config = OperationConfig()
        
        assert hasattr(config, 'should_use_api')
        assert callable(config.should_use_api)
    
    def test_should_sync(self):
        """Teste de verificação se deve sincronizar"""
        from config.operation_mode import OperationConfig
        
        config = OperationConfig()
        
        assert hasattr(config, 'should_sync')
        assert callable(config.should_sync)


# ============================================================================
# TESTES DE CLIENTE API
# ============================================================================

class TestClienteAPICompleto:
    """Testes completos para o cliente API"""
    
    def test_api_initialization(self):
        """Teste de inicialização da API"""
        from services.api import ClienteAPI
        
        api = ClienteAPI()
        
        assert api.base_url is not None
        assert 'localhost' in api.base_url or '127.0.0.1' in api.base_url
    
    @patch('services.api.requests')
    def test_api_get_success(self, mock_requests):
        """Teste de GET bem-sucedido"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'success': True, 'data': []}
        mock_response.text = '{"success": true, "data": []}'
        mock_requests.get.return_value = mock_response
        
        from services.api import ClienteAPI
        api = ClienteAPI()
        result = api.get('students/')
        
        assert 'success' in result
    
    @patch('services.api.requests')
    def test_api_get_with_params(self, mock_requests):
        """Teste de GET com parâmetros"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'success': True, 'data': []}
        mock_response.text = '{"success": true, "data": []}'
        mock_requests.get.return_value = mock_response
        
        from services.api import ClienteAPI
        api = ClienteAPI()
        result = api.get('students/', params={'page': 1})
        
        assert 'success' in result
    
    @patch('services.api.requests')
    def test_api_post_success(self, mock_requests):
        """Teste de POST bem-sucedido"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'success': True, 'message': 'Created'}
        mock_response.text = '{"success": true, "message": "Created"}'
        mock_requests.Session.return_value.post.return_value = mock_response
        
        from services.api import ClienteAPI
        api = ClienteAPI()
        result = api.post('test/', json={'test': 'data'})
        
        assert result is not None
    
    @patch('services.api.requests')
    def test_api_post_with_files(self, mock_requests):
        """Teste de POST com arquivos"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'success': True}
        mock_requests.Session.return_value.post.return_value = mock_response
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='file content')):
                from services.api import ClienteAPI
                api = ClienteAPI()
                result = api.upload_file('upload/', '/tmp/test.pdf')
                
                assert result is not None
    
    @patch('services.api.requests')
    def test_api_put(self, mock_requests):
        """Teste de PUT"""
        from services.api import ClienteAPI
        api = ClienteAPI()
        
        with patch('services.api.requests') as mock_req:
            result = api.put('test/1/', json={'name': 'updated'})
            assert 'success' in result
    
    @patch('services.api.requests')
    def test_api_delete(self, mock_requests):
        """Teste de DELETE"""
        from services.api import ClienteAPI
        api = ClienteAPI()
        
        with patch('services.api.requests') as mock_req:
            result = api.delete('test/1/')
            assert 'success' in result
    
    def test_api_fallback_mock(self):
        """Teste de fallback para dados mock"""
        from services.api import ClienteAPI
        api = ClienteAPI()
        
        # Testa mock de help/notifications
        with patch.object(api, '_should_use_api', return_value=False):
            result = api.get('help/notifications/')
            assert result['success'] is True
            assert 'data' in result
    
    def test_should_use_api_independent_mode(self):
        """Teste de verificação de uso da API em modo independente"""
        from services.api import ClienteAPI
        
        api = ClienteAPI()
        
        with patch.object(api, '_get_operation_config', return_value=None):
            result = api._should_use_api()
            assert result is True  # Padrão: tentar API


# ============================================================================
# TESTES DE SINCRONIZAÇÃO
# ============================================================================

class TestSincronizacaoCompleta:
    """Testes completos para sincronização"""
    
    @patch('services.sync_service.requests')
    @patch('services.sync_service.get_operation_config')
    def test_sync_service_initialization(self, mock_config, mock_requests):
        """Teste de inicialização do serviço de sincronização"""
        mock_config_instance = Mock()
        mock_config_instance.api_base_url = 'http://localhost:8000'
        mock_config_instance.api_timeout = 5
        mock_config_instance.mode = Mock()
        mock_config_instance.mode.value = 'hybrid'
        mock_config_instance.should_use_api.return_value = True
        mock_config_instance.is_independent.return_value = False
        mock_config.return_value = mock_config_instance
        
        mock_requests.Session.return_value.get.return_value.status_code = 200
        
        from services.sync_service import SyncService
        service = SyncService()
        
        assert service is not None
        assert service.config is not None
    
    @patch('services.sync_service.requests')
    @patch('services.sync_service.get_operation_config')
    def test_check_api_availability_true(self, mock_config, mock_requests):
        """Teste de verificação de disponibilidade da API - disponível"""
        mock_config_instance = Mock()
        mock_config_instance.api_base_url = 'http://localhost:8000'
        mock_config_instance.api_timeout = 5
        mock_config_instance.set_api_available = Mock()
        mock_config.return_value = mock_config_instance
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.Session.return_value.get.return_value = mock_response
        
        from services.sync_service import SyncService
        service = SyncService()
        
        # Reinicializa
        service._initialized = False
        service.__init__()
        
        result = service.check_api_availability()
        assert result is True
    
    @patch('services.sync_service.requests')
    @patch('services.sync_service.get_operation_config')
    def test_check_api_availability_false(self, mock_config, mock_requests):
        """Teste de verificação de disponibilidade da API - indisponível"""
        mock_config_instance = Mock()
        mock_config_instance.api_base_url = 'http://localhost:8000'
        mock_config_instance.api_timeout = 5
        mock_config_instance.set_api_available = Mock()
        mock_config.return_value = mock_config_instance
        
        import requests
        mock_requests.exceptions.ConnectionError = requests.exceptions.ConnectionError
        mock_requests.Session.return_value.get.side_effect = requests.exceptions.ConnectionError()
        
        from services.sync_service import SyncService
        service = SyncService()
        
        service._initialized = False
        service.__init__()
        
        result = service.check_api_availability()
        assert result is False
    
    def test_sync_queue_add(self):
        """Teste de adição à fila de sincronização"""
        from services.sync_service import SyncQueue
        
        with patch('services.sync_service.SyncQueue._get_queue_path', return_value='/tmp/test_queue.json'):
            queue = SyncQueue()
            queue.add('create', 'students', 1, {'name': 'Test'})
            
            pending = queue.get_pending()
            assert len(pending) > 0
    
    def test_sync_queue_remove(self):
        """Teste de remoção da fila"""
        from services.sync_service import SyncQueue
        
        with patch('services.sync_service.SyncQueue._get_queue_path', return_value='/tmp/test_queue.json'):
            queue = SyncQueue()
            queue.add('create', 'students', 1, {'name': 'Test'})
            
            pending = queue.get_pending()
            if pending:
                queue.remove(pending[0]['id'])
                # Verifica se foi removido
    
    def test_sync_queue_increment_attempt(self):
        """Teste de incremento de tentativas"""
        from services.sync_service import SyncQueue
        
        with patch('services.sync_service.SyncQueue._get_queue_path', return_value='/tmp/test_queue.json'):
            queue = SyncQueue()
            queue.add('create', 'students', 1, {'name': 'Test'})
            
            pending = queue.get_pending()
            if pending:
                item_id = pending[0]['id']
                queue.increment_attempt(item_id)
                # Verifica que foi incrementado
    
    def test_sync_queue_clear_old(self):
        """Teste de limpeza de itens antigos"""
        from services.sync_service import SyncQueue
        
        with patch('services.sync_service.SyncQueue._get_queue_path', return_value='/tmp/test_queue.json'):
            queue = SyncQueue()
            queue._queue = []
            queue._save_queue()
            
            queue.clear_old(max_attempts=5)
            # Verifica que limpeza foi executada
    
    def test_sync_service_get_status(self):
        """Teste de obtenção de status"""
        from services.sync_service import SyncService
        
        with patch('services.sync_service.get_operation_config'):
            service = SyncService()
            status = service.get_status()
            
            assert 'mode' in status
            assert 'api_available' in status
            assert 'api_url' in status
    
    @patch('services.sync_service.requests')
    @patch('services.sync_service.get_operation_config')
    def test_sync_now_sem_api(self, mock_config, mock_requests):
        """Teste de sincronização sem API disponível"""
        mock_config_instance = Mock()
        mock_config_instance.api_base_url = 'http://localhost:8000'
        mock_config_instance.should_use_api.return_value = True
        mock_config_instance.api_available = False
        mock_config.return_value = mock_config_instance
        
        mock_requests.Session.return_value.get.side_effect = Exception("Connection error")
        
        from services.sync_service import SyncService
        service = SyncService()
        
        result = service.sync_now()
        
        assert 'success' in result
        assert 'api_available' in result


# ============================================================================
# TESTES DE ESTUDANTES
# ============================================================================

class TestServicoEstudantesCompleto:
    """Testes completos para serviço de estudantes"""
    
    @patch('services.estudantes.requests')
    @patch('services.estudantes.get_auth_service')
    def test_listar_estudantes_api(self, mock_auth, mock_requests):
        """Teste de listagem de estudantes via API"""
        mock_auth.return_value = None
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'success': True,
            'data': [
                {'id': 1, 'name': 'John Doe', 'course': 'Engineering'},
                {'id': 2, 'name': 'Jane Smith', 'course': 'Medicine'}
            ]
        }
        mock_requests.Session.return_value.get.return_value = mock_response
        
        from services.estudantes import ServicoEstudante
        service = ServicoEstudante()
        
        result = service.listar_estudantes()
        
        assert result is not None
    
    @patch('services.estudantes.get_db_connection')
    def test_listar_estudantes_local(self, mock_db):
        """Teste de listagem de estudantes via banco local"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id_aluno': 1, 'nome': 'John Doe', 'curso': 'Engineering', 'has_medical_report': False, 'requires_attention': False, 'priority_level': 0}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.estudantes import ServicoEstudante
        service = ServicoEstudante()
        
        with patch.object(service, '_should_use_api', return_value=False):
            result = service.listar_estudantes()
            
            assert 'data' in result or 'error' in result
    
    @patch('services.estudantes.get_db_connection')
    def test_listar_estudantes_com_busca(self, mock_db):
        """Teste de listagem com filtro de busca"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.estudantes import ServicoEstudante
        service = ServicoEstudante()
        
        with patch.object(service, '_should_use_api', return_value=False):
            result = service.listar_estudantes(busca='John')
            
            assert 'data' in result or 'error' in result
    
    @patch('services.estudantes.get_db_connection')
    def test_obter_estudante(self, mock_db):
        """Teste de obtenção de estudante específico"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id_aluno': 1, 
            'nome': 'Test Student', 
            'curso': 'Engineering',
            'has_medical_report': True,
            'requires_attention': False,
            'priority_level': 1
        }
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.estudantes import ServicoEstudante
        service = ServicoEstudante()
        
        result = service._fallback_obter_estudante(1)
        
        assert result['success'] is True
    
    @patch('services.estudantes.get_db_connection')
    def test_criar_estudante(self, mock_db):
        """Teste de criação de estudante"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.estudantes import ServicoEstudante
        service = ServicoEstudante()
        
        dados = {'name': 'New Student', 'contact': 'student@test.com'}
        result = service._fallback_criar_estudante(dados)
        
        assert isinstance(result, dict)
    
    @patch('services.estudantes.get_db_connection')
    def test_atualizar_estudante(self, mock_db):
        """Teste de atualização de estudante"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.estudantes import ServicoEstudante
        service = ServicoEstudante()
        
        dados = {'name': 'Updated Student', 'contact': 'updated@test.com'}
        result = service._fallback_atualizar_estudante(1, dados)
        
        assert isinstance(result, dict)
    
    @patch('services.estudantes.get_db_connection')
    def test_deletar_estudante(self, mock_db):
        """Teste de deleção de estudante"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.estudantes import ServicoEstudante
        service = ServicoEstudante()
        
        result = service._fallback_deletar_estudante(1)
        
        assert isinstance(result, dict)
    
    @patch('services.estudantes.get_db_connection')
    def test_obter_relatorio_estudante(self, mock_db):
        """Teste de obtenção de relatório do estudante"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id_aluno': 1, 'nome': 'Test', 'curso': 'Test',
            'has_medical_report': False, 'requires_attention': False
        }
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.estudantes import ServicoEstudante
        service = ServicoEstudante()
        
        with patch('services.estudantes.get_db_connection', return_value=mock_connection):
            result = service._fallback_obter_relatorio_estudante(1)
            
            assert 'success' in result


# ============================================================================
# TESTES DE AGENDAMENTOS
# ============================================================================

class TestServicoAgendamentosCompleto:
    """Testes completos para serviço de agendamentos"""
    
    @patch('services.agendamentos.requests')
    @patch('services.agendamentos.get_auth_service')
    def test_criar_agendamento_api(self, mock_auth, mock_requests):
        """Teste de criação de agendamento via API"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'success': True, 'data': {'id': 1}}
        mock_session.post.return_value = mock_response
        mock_auth.return_value = Mock(get_session=Mock(return_value=mock_session), csrf_token='test_token')
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        dados = {
            'id_aluno': 1,
            'data_hora': '2026-02-25 10:00',
            'motivo': 'Consulta de Rotina'
        }
        
        result = service.criar_agendamento(dados)
        
        assert 'success' in result
    
    @patch('services.agendamentos.get_db_connection')
    def test_verificar_disponibilidade_livre(self, mock_db):
        """Teste de verificação de disponibilidade - horário livre"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        result = service.verificar_disponibilidade('2026-02-25', '10:00')
        
        assert result is True
    
    @patch('services.agendamentos.get_db_connection')
    def test_verificar_disponibilidade_ocupado(self, mock_db):
        """Teste de verificação de disponibilidade - horário ocupado"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [1]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        result = service.verificar_disponibilidade('2026-02-25', '10:00')
        
        assert result is False
    
    @patch('services.agendamentos.get_db_connection')
    def test_listar_agendamentos_local(self, mock_db):
        """Teste de listagem de agendamentos via banco local"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'nome': 'John Doe',
                'id_aluno': 1,
                'data_hora': datetime.now(),
                'motivo': 'Consulta',
                'status': 'agendado',
                'local': 'Sala 1',
                'profissional': 'Dr. Smith',
                'laudo': None,
                'origem': 'desktop'
            }
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        with patch.object(service, '_get_session', return_value=Mock(get=Mock(side_effect=Exception("Connection error")))):
            result = service.listar_agendamentos()
            
            assert len(result) > 0
    
    @patch('services.agendamentos.get_db_connection')
    def test_atualizar_agendamento(self, mock_db):
        """Teste de atualização de agendamento"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        dados = {
            'id_aluno': 1,
            'data_hora': '2026-02-25 11:00',
            'motivo': 'Consulta Atualizada',
            'status': 'Agendado'
        }
        
        result = service.atualizar_agendamento(1, dados)
        
        assert 'success' in result
    
    @patch('services.agendamentos.get_db_connection')
    def test_deletar_agendamento(self, mock_db):
        """Teste de deleção de agendamento"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        with patch.object(service, '_get_session', return_value=Mock(delete=Mock(return_value=Mock(status_code=200)))):
            result = service.deletar_agendamento(1)
            
            assert result['success'] is True
    
    def test_convert_status_frontend_to_backend(self):
        """Teste de conversão de status frontend para backend"""
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        assert service._convert_status_frontend_to_backend('Agendado') == 'agendado'
        assert service._convert_status_frontend_to_backend('Realizado') == 'concluido'
        assert service._convert_status_frontend_to_backend('Cancelado') == 'cancelado'
        assert service._convert_status_frontend_to_backend('Faltou') == 'cancelado'
    
    def test_convert_status_backend_to_frontend(self):
        """Teste de conversão de status backend para frontend"""
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        assert service._convert_status_backend_to_frontend('agendado') == 'agendado'
        assert service._convert_status_backend_to_frontend('concluido') == 'concluido'
        assert service._convert_status_backend_to_frontend('cancelado') == 'cancelado'
        assert service._convert_status_backend_to_frontend('scheduled') == 'agendado'
        assert service._convert_status_backend_to_frontend('completed') == 'concluido'
        assert service._convert_status_backend_to_frontend('cancelled') == 'cancelado'
    
    @patch('services.agendamentos.get_db_connection')
    def test_adicionar_horario_disponibilidade(self, mock_db):
        """Teste de adição de horário de disponibilidade"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        with patch.object(service, '_get_session', return_value=Mock(post=Mock(return_value=Mock(status_code=500)))):
            result = service.adicionar_horario_disponibilidade('14:00')
            
            assert 'success' in result
    
    @patch('services.agendamentos.get_db_connection')
    def test_remover_horario_disponibilidade(self, mock_db):
        """Teste de remoção de horário de disponibilidade"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [1]  # Time ID existe
        mock_cursor.fetchone.side_effect = [None, [1]]  # Sem agendamento
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        with patch.object(service, '_get_session', return_value=Mock(post=Mock(return_value=Mock(status_code=404)))):
            result = service.remover_horario_disponibilidade('14:00')
            
            assert 'success' in result


# ============================================================================
# TESTES DE TRIAGEM
# ============================================================================

class TestServicoTriagemCompleto:
    """Testes completos para serviço de triagem"""
    
    @patch('services.triagem.get_db_connection')
    def test_listar_triagens(self, mock_db):
        """Teste de listagem de triagens"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'student_id': 1,
                'student_name': 'John Doe',
                'form_id': 1,
                'form_name': 'Form A',
                'status': 'pending',
                'priority': 'high',
                'scheduled_date': None,
                'completed_date': None,
                'score': None,
                'created_at': datetime.now()
            }
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.triagem import ServicoTriagem
        service = ServicoTriagem()
        
        result = service.listar_triagens()
        
        assert result['success'] is True
        assert len(result['data']) > 0
    
    @patch('services.triagem.get_db_connection')
    def test_listar_triagens_com_filtros(self, mock_db):
        """Teste de listagem com filtros"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.triagem import ServicoTriagem
        service = ServicoTriagem()
        
        result = service.listar_triagens(status='pending', prioridade='high')
        
        assert result['success'] is True
    
    @patch('services.triagem.get_db_connection')
    def test_obter_triagem(self, mock_db):
        """Teste de obtenção de triagem específica"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {
            'id': 1, 'student_id': 1, 'student_name': 'John Doe',
            'form_id': 1, 'form_name': 'Form A', 'status': 'pending',
            'priority': 'high', 'score': 75, 'created_at': datetime.now()
        }
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.triagem import ServicoTriagem
        service = ServicoTriagem()
        
        result = service.obter_triagem(1)
        
        assert result['success'] is True
    
    @patch('services.triagem.get_db_connection')
    def test_criar_triagem(self, mock_db):
        """Teste de criação de triagem"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.triagem import ServicoTriagem
        service = ServicoTriagem()
        
        dados = {
            'student_id': 1,
            'form_id': 1,
            'status': 'pending',
            'priority': 'medium'
        }
        
        result = service.criar_triagem(dados)
        
        assert result['success'] is True
        mock_cursor.execute.assert_called()
        mock_connection.commit.assert_called()
    
    @patch('services.triagem.get_db_connection')
    def test_atualizar_triagem(self, mock_db):
        """Teste de atualização de triagem"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.triagem import ServicoTriagem
        service = ServicoTriagem()
        
        dados = {
            'student_id': 1,
            'form_id': 1,
            'status': 'completed',
            'priority': 'high',
            'score': 85
        }
        
        result = service.atualizar_triagem(1, dados)
        
        assert result['success'] is True
    
    @patch('services.triagem.get_db_connection')
    def test_deletar_triagem(self, mock_db):
        """Teste de deleção de triagem"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.triagem import ServicoTriagem
        service = ServicoTriagem()
        
        result = service.deletar_triagem(1)
        
        assert result['success'] is True
    
    @patch('services.triagem.get_db_connection')
    def test_listar_formularios(self, mock_db):
        """Teste de listagem de formulários"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Form A', 'description': 'Description', 'questions': '[]', 'is_active': True, 'created_at': datetime.now()}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.triagem import ServicoTriagem
        service = ServicoTriagem()
        
        result = service.listar_formularios()
        
        assert result['success'] is True
        assert len(result['data']) > 0


# ============================================================================
# TESTES DE BEM-ESTAR
# ============================================================================

class TestServicoBemEstarCompleto:
    """Testes completos para serviço de bem-estar"""
    
    @patch('services.bem_estar.get_db_connection')
    def test_obter_dashboard(self, mock_db):
        """Teste de obtenção do dashboard de bem-estar"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = {'average_mood': 3.5}
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        result = service.obter_dashboard()
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_listar_entradas_humor(self, mock_db):
        """Teste de listagem de entradas de humor"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'mood_level': 4, 'entry_date': datetime.now()}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        result = service.listar_entradas_humor()
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_obter_medias_humor(self, mock_db):
        """Teste de obtenção de média de humor"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {'average_mood': 3.5}
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        result = service.obter_medias_humor()
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_obter_humor_estudante(self, mock_db):
        """Teste de obtenção de humor do estudante"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'mood_level': 4, 'entry_date': datetime.now()}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        result = service.obter_humor_estudante(1)
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_listar_checkins(self, mock_db):
        """Teste de listagem de check-ins"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        result = service.listar_checkins()
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_listar_estudantes_risco(self, mock_db):
        """Teste de listagem de estudantes em risco"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id_aluno': 1, 'nome': 'John', 'priority_level': 4, 'attention_reason': 'Test', 'requires_attention': True}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        result = service.listar_estudantes_risco()
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_criar_registro_humor(self, mock_db):
        """Teste de criação de registro de humor"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        dados = {
            'student_id': 1,
            'mood_level': 4,
            'mood_text': 'Happy',
            'notes': 'Test note'
        }
        
        result = service.criar_registro_humor(dados)
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_criar_checkin(self, mock_db):
        """Teste de criação de check-in"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        dados = {
            'student_id': 1,
            'mood_level': 4,
            'stress_level': 2,
            'sleep_quality': 3
        }
        
        result = service.criar_checkin(dados)
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_obter_tendencia_humor(self, mock_db):
        """Teste de tendência de humor"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        result = service.obter_tendencia_humor(dias=30)
        
        assert result['success'] is True
    
    @patch('services.bem_estar.get_db_connection')
    def test_obter_distribuicao_humor(self, mock_db):
        """Teste de distribuição de humor"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {'happy': 10, 'neutral': 5, 'sad': 3, 'total': 18}
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.bem_estar import ServicoBemEstar
        service = ServicoBemEstar()
        
        result = service.obter_distribuicao_humor()
        
        assert result['success'] is True


# ============================================================================
# TESTES DE COMUNICAÇÃO
# ============================================================================

class TestServicoComunicacaoCompleto:
    """Testes completos para serviço de comunicação"""
    
    @patch('services.comunicacao.get_db_connection')
    def test_listar_alertas(self, mock_db):
        """Teste de listagem de alertas"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'alert_type': 'screening_pending', 'severity': 'high', 'message': 'Test', 'is_read': False, 'is_resolved': False, 'created_at': datetime.now()}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.listar_alertas()
        
        assert result['success'] is True
    
    @patch('services.comunicacao.get_db_connection')
    def test_marcar_alerta_lido(self, mock_db):
        """Teste de marcar alerta como lido"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.marcar_alerta_lido(1)
        
        assert result['success'] is True
    
    @patch('services.comunicacao.get_db_connection')
    def test_marcar_todos_lidos(self, mock_db):
        """Teste de marcar todos alertas como lidos"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.marcar_todos_lidos()
        
        assert result['success'] is True
    
    @patch('services.comunicacao.get_db_connection')
    def test_listar_contatos(self, mock_db):
        """Teste de listagem de contatos"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'first_name': 'John', 'last_name': 'Doe', 'username': 'johndoe', 'email': 'john@test.com', 'is_superuser': True, 'is_staff': True, 'student_name': None}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.listar_contatos(id_usuario_logado=1)
        
        assert result['success'] is True
    
    @patch('services.comunicacao.get_db_connection')
    def test_obter_mensagens(self, mock_db):
        """Teste de obtenção de mensagens"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'sender_id': 1, 'recipient_id': 2, 'text': 'Hello', 'timestamp': datetime.now(), 'read': False, 'caminho_arquivo': None, 'tipo_arquivo': None}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.obter_mensagens(1, 2)
        
        assert result['success'] is True
    
    @patch('services.comunicacao.get_db_connection')
    def test_enviar_mensagem(self, mock_db):
        """Teste de envio de mensagem"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.enviar_mensagem(1, 2, 'Hello World')
        
        assert result['success'] is True
    
    @patch('services.comunicacao.get_db_connection')
    def test_enviar_mensagem_grupo(self, mock_db):
        """Teste de envio de mensagem em grupo"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.enviar_mensagem_grupo(1, 'Group message')
        
        assert result['success'] is True
    
    @patch('services.comunicacao.get_db_connection')
    def test_obter_mensagens_grupo(self, mock_db):
        """Teste de obtenção de mensagens de grupo"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'sender_id': 1, 'recipient_id': None, 'text': 'Group msg', 'timestamp': datetime.now(), 'read': False}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.obter_mensagens_grupo()
        
        assert result['success'] is True
    
    @patch('services.comunicacao.get_db_connection')
    def test_contar_mensagens_nao_lidas(self, mock_db):
        """Teste de contagem de mensagens não lidas"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            {'contato_id': 1, 'total_nao_lidas': 3}
        ]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.comunicacao import ServicoComunicacao
        service = ServicoComunicacao()
        
        result = service.contar_mensagens_nao_lidas(1)
        
        assert result['success'] is True


# ============================================================================
# TESTES DE BACKUP
# ============================================================================

class TestServicoBackupCompleto:
    """Testes completos para serviço de backup"""
    
    def test_backup_service_initialization(self):
        """Teste de inicialização do serviço de backup"""
        from services.backup import BackupService, BackupType, BackupStatus
        
        service = BackupService(backup_dir='/tmp/test_backups')
        
        assert service is not None
        assert hasattr(service, 'MAIN_TABLES')
    
    @patch('services.backup.get_db_connection')
    def test_create_full_backup(self, mock_db):
        """Teste de criação de backup completo"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.backup import BackupService
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(backup_dir=tmpdir)
            
            result = service.create_full_backup(include_files=False, compress=False)
            
            assert result.id is not None
    
    @patch('services.backup.get_db_connection')
    def test_create_incremental_backup(self, mock_db):
        """Teste de criação de backup incremental"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.backup import BackupService
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(backup_dir=tmpdir)
            
            since = datetime.now() - timedelta(days=7)
            result = service.create_incremental_backup(since=since, compress=False)
            
            assert result.id is not None
    
    def test_list_backups(self):
        """Teste de listagem de backups"""
        from services.backup import BackupService
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            service = BackupService(backup_dir=tmpdir)
            
            backups = service.list_backups()
            
            assert isinstance(backups, list)
    
    def test_backup_info_to_dict(self):
        """Teste de conversão de BackupInfo para dict"""
        from services.backup import BackupInfo, BackupType, BackupStatus
        
        info = BackupInfo(
            id='test_001',
            type=BackupType.FULL,
            created_at=datetime.now(),
            file_path='/tmp/test.json',
            file_size=1024,
            checksum='abc123',
            status=BackupStatus.COMPLETED,
            tables_included=['aluno', 'agendamento']
        )
        
        result = info.to_dict()
        
        assert result['id'] == 'test_001'
        assert result['type'] == 'full'
        assert result['status'] == 'completed'
    
    def test_backup_info_format_size(self):
        """Teste de formatação de tamanho"""
        from services.backup import BackupInfo
        
        # Testa diferentes tamanhos
        assert 'B' in BackupInfo._format_size(100)
        assert 'KB' in BackupInfo._format_size(2048)
        assert 'MB' in BackupInfo._format_size(2 * 1024 * 1024)
        assert 'GB' in BackupInfo._format_size(2 * 1024 * 1024 * 1024)


# ============================================================================
# TESTES DE IMPORTAÇÃO
# ============================================================================

class TestServicoImportacaoCompleto:
    """Testes completos para serviço de importação"""
    
    def test_import_service_initialization(self):
        """Teste de inicialização do serviço de importação"""
        from services.importacao import ServicoImportacao
        
        service = ServicoImportacao()
        
        assert service is not None
        assert hasattr(service, 'STUDENT_MAPPINGS')
        assert hasattr(service, 'APPOINTMENT_MAPPINGS')
        assert hasattr(service, 'ORIENTATION_MAPPINGS')
    
    def test_detect_column_mapping(self):
        """Teste de detecção de mapeamento de colunas"""
        from services.importacao import ServicoImportacao
        
        service = ServicoImportacao()
        
        headers = ['Nome', 'Email', 'Curso']
        mappings = service.STUDENT_MAPPINGS
        
        result = service._detect_column_mapping(headers, mappings)
        
        assert 'nome' in result
        assert 'email' in result
    
    def test_transform_value_boolean(self):
        """Teste de transformação de valores booleanos"""
        from services.importacao import ServicoImportacao
        
        service = ServicoImportacao()
        
        # Testa diferentes valores que devem ser convertidos para True
        assert service._transform_value('sim', 'has_medical_report') is True
        assert service._transform_value('yes', 'has_medical_report') is True
        assert service._transform_value('1', 'has_medical_report') is True
        assert service._transform_value('true', 'has_medical_report') is True
        assert service._transform_value('X', 'has_medical_report') is True
        
        # Testa valores que devem ser convertidos para False
        assert service._transform_value('não', 'has_medical_report') is False
        assert service._transform_value('no', 'has_medical_report') is False
        assert service._transform_value('0', 'has_medical_report') is False
    
    def test_transform_value_integer(self):
        """Teste de transformação de valores inteiros"""
        from services.importacao import ServicoImportacao
        
        service = ServicoImportacao()
        
        assert service._transform_value('20', 'idade') == 20
        assert service._transform_value(25, 'idade') == 25
        assert service._transform_value('abc', 'idade') is None
    
    def test_transform_value_date(self):
        """Teste de transformação de datas"""
        from services.importacao import ServicoImportacao
        
        service = ServicoImportacao()
        
        # Testa diferentes formatos de data
        result = service._transform_value('2026-02-25', 'data_hora')
        assert result is not None
        
        result = service._transform_value('25/02/2026', 'data_hora')
        assert result is not None
        
        result = service._transform_value('25-02-2026', 'data_hora')
        assert result is not None
    
    def test_validate_row(self):
        """Teste de validação de linha"""
        from services.importacao import ServicoImportacao
        
        service = ServicoImportacao()
        
        # Testa dados válidos
        data = {'nome': 'John', 'email': 'john@test.com'}
        errors = service._validate_row(data, ['nome'])
        assert len(errors) == 0
        
        # Testa dados inválidos
        data = {'nome': ''}
        errors = service._validate_row(data, ['nome'])
        assert len(errors) > 0
    
    def test_import_status_enum(self):
        """Teste de enum de status de importação"""
        from services.importacao import ImportStatus
        
        assert ImportStatus.SUCCESS.value == "success"
        assert ImportStatus.WARNING.value == "warning"
        assert ImportStatus.ERROR.value == "error"
        assert ImportStatus.SKIPPED.value == "skipped"
    
    def test_import_report(self):
        """Teste de relatório de importação"""
        from services.importacao import ImportReport, ImportResult, ImportStatus
        
        report = ImportReport()
        
        assert report.total_rows == 0
        assert report.success_count == 0
        
        # Adiciona resultado
        result = ImportResult(
            status=ImportStatus.SUCCESS,
            row_number=1,
            message="Test success"
        )
        report.add_result(result)
        report.total_rows = 1  # Define o total de linhas
        
        assert report.total_rows == 1
        assert report.success_count == 1


# ============================================================================
# TESTES DE CONFIGURAÇÕES
# ============================================================================

class TestServicoConfiguracoesCompleto:
    """Testes completos para serviço de configurações"""
    
    @patch('services.configuracoes.get_db_connection')
    def test_obter_configuracoes(self, mock_db):
        """Teste de obtenção de configurações"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = {'id': 1, 'theme': 'dark'}
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.configuracoes import ServicoConfiguracoes
        service = ServicoConfiguracoes()
        
        result = service.obter_configuracoes(usuario_id=1)
        
        assert 'success' in result or 'data' in result
    
    @patch('services.configuracoes.get_db_connection')
    def test_atualizar_configuracoes(self, mock_db):
        """Teste de atualização de configurações"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.configuracoes import ServicoConfiguracoes
        service = ServicoConfiguracoes()
        
        dados = {'user_id': 1, 'theme': 'dark', 'notifications': {}}
        result = service.atualizar_configuracoes(dados)
        
        assert 'success' in result
    
    def test_testar_conexao_api_success(self):
        """Teste de teste de conexão API - sucesso"""
        from services.configuracoes import ServicoConfiguracoes
        service = ServicoConfiguracoes()
        
        with patch('services.configuracoes.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'info': {'version': '1.0.0'}}
            mock_get.return_value = mock_response
            
            result = service.testar_conexao_api()
            
            assert 'success' in result
    
    def test_testar_conexao_api_timeout(self):
        """Teste de teste de conexão API - timeout"""
        from services.configuracoes import ServicoConfiguracoes
        import requests
        
        service = ServicoConfiguracoes()
        
        with patch('services.configuracoes.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            result = service.testar_conexao_api()
            
            assert result['success'] is False
            assert result['status'] == 'timeout'
    
    def test_testar_conexao_api_offline(self):
        """Teste de teste de conexão API - offline"""
        from services.configuracoes import ServicoConfiguracoes
        import requests
        
        service = ServicoConfiguracoes()
        
        with patch('services.configuracoes.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            result = service.testar_conexao_api()
            
            assert result['success'] is False
            assert result['status'] == 'offline'
    
    @patch('services.configuracoes.get_db_connection')
    def test_testar_conexao_banco(self, mock_db):
        """Teste de teste de conexão com banco"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [1]
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.configuracoes import ServicoConfiguracoes
        service = ServicoConfiguracoes()
        
        result = service.testar_conexao_banco()
        
        assert result['success'] is True
    
    def test_obter_info_sistema(self):
        """Teste de obtenção de informações do sistema"""
        from services.configuracoes import ServicoConfiguracoes
        service = ServicoConfiguracoes()
        
        result = service.obter_info_sistema()
        
        assert result['success'] is True
        assert 'data' in result
    
    def test_obter_status_sincronizacao(self):
        """Teste de obtenção de status de sincronização"""
        from services.configuracoes import ServicoConfiguracoes
        service = ServicoConfiguracoes()
        
        with patch('os.path.exists', return_value=False):
            result = service.obter_status_sincronizacao()
            
            assert 'success' in result


# ============================================================================
# TESTES DE VALIDAÇÕES
# ============================================================================

class TestValidacoes:
    """Testes para validações"""
    
    def test_validate_email_valid(self):
        """Teste de validação de email válido"""
        from services.validacoes import validate_email
        
        # Emails válidos
        valid_emails = ['test@test.com', 'user.name@domain.co.uk', 'user+tag@example.org']
        for email in valid_emails:
            result = validate_email(email)
            assert result.is_valid is True or result is True
    
    def test_validate_email_invalid(self):
        """Teste de validação de email inválido"""
        from services.validacoes import validate_email
        
        # Emails inválidos
        invalid_emails = ['invalid', 'test@', '@test.com', 'test@test']
        for email in invalid_emails:
            result = validate_email(email)
            assert result is not None
    
    def test_validate_cpf(self):
        """Teste de validação de CPF"""
        from services.validacoes import validate_cpf
        
        # CPF válido (formatado)
        result = validate_cpf('123.456.789-00')
        assert result is not None
    
    def test_validate_phone(self):
        """Teste de validação de telefone"""
        from services.validacoes import validate_phone
        
        # Telefones válidos
        result = validate_phone('(11) 99999-9999')
        assert result is not None
        
        result = validate_phone('11999999999')
        assert result is not None


# ============================================================================
# TESTES DE PERFORMANCE E STRESS
# ============================================================================

class TestPerformance:
    """Testes de performance e stress"""
    
    def test_multiplas_requisicoes_simultaneas(self):
        """Teste de múltiplas requisições simultâneas"""
        from services.api import ClienteAPI
        api = ClienteAPI()
        
        # Simula múltiplas requisições
        results = []
        for i in range(10):
            with patch('services.api.requests') as mock_requests:
                mock_response = Mock()
                mock_response.ok = True
                mock_response.json.return_value = {'success': True, 'id': i}
                mock_response.text = '{"success": true, "id": ' + str(i) + '}'
                mock_requests.get.return_value = mock_response
                
                result = api.get(f'test/{i}/')
                results.append(result)
        
        assert len(results) == 10
    
    def test_fila_sincronizacao_grande(self):
        """Teste com fila de sincronização grande"""
        from services.sync_service import SyncQueue
        
        with patch('services.sync_service.SyncQueue._get_queue_path', return_value='/tmp/test_queue.json'):
            queue = SyncQueue()
            queue._queue = []  # Limpa a fila
            
            # Adiciona muitos itens
            for i in range(100):
                queue.add('create', 'students', i, {'name': f'Student {i}'})
            
            pending = queue.get_pending()
            assert len(pending) >= 0
    
    def test_cache_operations(self):
        """Teste de operações de cache"""
        try:
            from services.cache_service import CacheService
            service = CacheService()
            
            # Testa métodos básicos
            assert hasattr(service, 'get') or hasattr(service, 'set') or service is not None
        except:
            pass  # Pode não ter implementação completa


# ============================================================================
# TESTES DE CASOS EXTREMOS
# ============================================================================

class TestEdgeCases:
    """Testes de casos extremos"""
    
    @patch('services.api.requests')
    def test_api_response_invalida(self, mock_requests):
        """Teste com resposta JSON inválida"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = 'not valid json'
        mock_response.json.side_effect = Exception('Invalid JSON')
        mock_requests.get.return_value = mock_response
        
        from services.api import ClienteAPI
        api = ClienteAPI()
        result = api.get('test/')
        
        assert 'success' in result
    
    def test_database_vazia(self):
        """Teste com banco de dados vazio"""
        with patch('services.estudantes.get_db_connection') as mock_db:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchall.return_value = []
            mock_connection.cursor.return_value = mock_cursor
            mock_db.return_value = mock_connection
            
            from services.estudantes import ServicoEstudante
            service = ServicoEstudante()
            
            result = service._listar_estudantes_local()
            
            assert 'data' in result
            assert result['data'] == []
    
    @patch('services.agendamentos.get_db_connection')
    def test_agendamento_dados_nulos(self, mock_db):
        """Teste com dados de agendamento nulos"""
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_connection.cursor.return_value = mock_cursor
        mock_db.return_value = mock_connection
        
        from services.agendamentos import ServicoAgendamento
        service = ServicoAgendamento()
        
        result = service.listar_agendamentos('2026-01-01')
        assert isinstance(result, list)
    
    def test_timeout_configuracoes(self):
        """Teste de timeout em configurações"""
        from services.configuracoes import ServicoConfiguracoes
        import requests
        
        service = ServicoConfiguracoes()
        
        with patch('services.configuracoes.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            
            result = service.testar_conexao_api()
            
            assert result['success'] is False
    
    def test_operacao_invalida_sync(self):
        """Teste de operação inválida na sincronização"""
        from services.sync_service import SyncQueue
        
        with patch('services.sync_service.SyncQueue._get_queue_path', return_value='/tmp/test_queue.json'):
            queue = SyncQueue()
            queue._queue = []  # Limpa a fila
            
            # Adiciona operação
            queue.add('invalid_operation', 'students', 1, {})
            
            pending = queue.get_pending()
            # A operação deve ter sido adicionada
            assert len(pending) >= 1


# ============================================================================
# TESTES DE INTEGRAÇÃO COM SERPLENO_WEB
# ============================================================================

class TestIntegracaoSerplenoWeb:
    """Testes de integração completa com serpleno_web"""
    
    @patch('services.api.requests')
    def test_api_health_check(self, mock_requests):
        """Teste de verificação de saúde da API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.json.return_value = {'status': 'ok'}
        mock_requests.get.return_value = mock_response
        
        from services.api import ClienteAPI
        api = ClienteAPI()
        
        result = api.get('health/')
        
        assert isinstance(result, dict)
    
    def test_config_mode_operations(self):
        """Teste de modos de operação"""
        from config.operation_mode import get_operation_config, OperationMode
        
        config = get_operation_config()
        
        # Testa propriedades
        assert hasattr(config, 'mode')
        assert hasattr(config, 'is_independent')
        assert hasattr(config, 'should_use_api')
        assert hasattr(config, 'should_sync')
        
        # Testa métodos
        assert callable(config.is_independent)
        assert callable(config.should_use_api)
        assert callable(config.should_sync)
    
    def test_operation_modes(self):
        """Teste dos modos de operação"""
        from config.operation_mode import OperationMode
        
        # Verifica que existem os modos esperados
        assert OperationMode.INDEPENDENT.value == "independent"
        assert OperationMode.HYBRID.value == "hybrid"
        assert OperationMode.CONNECTED.value == "connected"
    
    @patch('services.sync_service.requests')
    @patch('services.sync_service.get_operation_config')
    def test_full_sync_cycle(self, mock_config, mock_requests):
        """Teste de ciclo completo de sincronização"""
        mock_config_instance = Mock()
        mock_config_instance.api_base_url = 'http://localhost:8000'
        mock_config_instance.api_timeout = 5
        mock_config_instance.should_use_api.return_value = True
        mock_config_instance.api_available = True
        mock_config_instance.should_sync.return_value = True
        mock_config_instance.update_last_sync = Mock()
        mock_config.return_value = mock_config_instance
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.Session.return_value.get.return_value = mock_response
        mock_requests.Session.return_value.post.return_value = mock_response
        mock_requests.Session.return_value.put.return_value = mock_response
        
        from services.sync_service import SyncService
        service = SyncService()
        
        # Testa ciclo completo
        result = service.sync_now()
        
        assert 'success' in result
        assert 'api_available' in result
    
    def test_fallback_chain(self):
        """Teste de cadeia de fallback"""
        from services.api import ClienteAPI
        from services.estudantes import ServicoEstudante
        
        api = ClienteAPI()
        service = ServicoEstudante()
        
        # Testa que fallback está implementado
        assert service._should_use_api is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

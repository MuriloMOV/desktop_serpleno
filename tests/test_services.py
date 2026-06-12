import pytest
from unittest.mock import MagicMock, patch
from services.auth import AuthService
from services.dashboard import ServicoDashboard
from services.estudantes import ServicoEstudante
from services.agendamentos import ServicoAgendamento

class TestServices:
    
    @patch('services.auth.api')
    def test_auth_service(self, mock_api):
        service = AuthService()
        
        # Mock API Response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "token": "123", "user": "test"}
        
        # Configure session.post to return this response
        mock_api.session.post.return_value = mock_response
        
        # We need to mock base_url so the replace call works
        mock_api.base_url = "http://localhost:8000/desktop/api"
        
        resp = service.login("user", "pass")
        
        # Check success logic
        assert resp["success"] is True
        
        # Verify call arguments
        # Note: URL construction uses replace, so let's verify loosely or just that it was called
        mock_api.session.post.assert_called()
        args, kwargs = mock_api.session.post.call_args
        assert kwargs['json'] == {"username": "user", "password": "pass"}

    @patch('services.estudantes.api')
    def test_student_service(self, mock_api):
        service = ServicoEstudante()
        
        # Test that service was created
        assert service is not None

    @patch('services.dashboard.api')
    def test_dashboard_service(self, mock_api):
        service = ServicoDashboard()
        
        # Verify service was created
        assert service is not None

    def test_agendamento_service(self):
        service = ServicoAgendamento()
        
        # Verify service was created
        assert service is not None
        # Check that service has expected methods
        assert hasattr(service, 'criar_agendamento')
        assert hasattr(service, 'listar_agendamentos')
        assert hasattr(service, 'atualizar_agendamento')
        assert hasattr(service, 'deletar_agendamento')
    
    def test_auth_service_instantiation(self):
        # Test that service can be instantiated
        service = AuthService()
        assert service is not None
        # Check that service has expected methods
        assert hasattr(service, 'login')

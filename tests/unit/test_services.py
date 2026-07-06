import pytest
from unittest.mock import MagicMock, patch
from ser_pleno.application.services.autenticacao import ServicoAutenticacao
from ser_pleno.application.services.dashboard import ServicoDashboard
from ser_pleno.application.services.estudantes import ServicoEstudante
from ser_pleno.application.services.agendamentos import ServicoAgendamento

class TestServices:
    
    @patch('ser_pleno.application.services.autenticacao.requests')
    def test_auth_service(self, mock_requests):
        service = ServicoAutenticacao()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "token": "123", "user": "test"}
        mock_requests.Session.return_value.post.return_value = mock_response
        
        resp = service.login("user", "pass")
        
        assert resp["success"] is True
        mock_requests.Session.return_value.post.assert_called()

    @patch('ser_pleno.application.services.estudantes.api')
    def test_student_service(self, mock_api):
        service = ServicoEstudante()
        
        # Test that service was created
        assert service is not None

    @patch('ser_pleno.application.services.dashboard.api')
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
        service = ServicoAutenticacao()
        assert service is not None
        assert hasattr(service, 'login')

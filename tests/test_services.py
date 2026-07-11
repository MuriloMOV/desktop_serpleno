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
        mock_repo_instance = MagicMock()
        mock_user = {
            "id": 1,
            "username": "user",
            "password": "pbkdf2_sha256$29000$4Xbq4peWIk4u$F0vpVOIL9jogA4tdMQ/V2z44/vlbVBhCxO0GRg8qfuc=",
        }
        mock_repo_instance.obter_usuario_por_username.return_value = mock_user
        service.repo = mock_repo_instance

        resp = service.login("user", "pass")

        assert resp["success"] is True
        assert resp["user"]["username"] == "user"
        mock_repo_instance.obter_usuario_por_username.assert_called_with("user")

    @patch('ser_pleno.infrastructure.api.api.api')
    def test_student_service(self, mock_api):
        service = ServicoEstudante()
        
        # Test that service was created
        assert service is not None

    @patch('ser_pleno.infrastructure.api.api.api')
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


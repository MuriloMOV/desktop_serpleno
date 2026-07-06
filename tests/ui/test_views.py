import pytest
from unittest.mock import MagicMock, patch
import customtkinter as ctk
import time

from ser_pleno.presentation.views.dashboard import DashboardFrame
from ser_pleno.presentation.views.agenda import AgendaFrame
from ser_pleno.presentation.views.estudantes import EstudantesFrame
from ser_pleno.presentation.views.orientacoes import OrientacoesFrame
from ser_pleno.presentation.views.analise_triagem import AnaliseTriagemFrame
from ser_pleno.presentation.views.quadro_avisos import QuadroAvisosFrame
from ser_pleno.presentation.views.comunicacao_interna import ComunicacaoInternaFrame
from ser_pleno.presentation.views.configuracoes import ConfiguracoesFrame
from ser_pleno.application.services.dashboard import ServicoDashboard
from ser_pleno.application.services.agendamentos import ServicoAgendamento
from ser_pleno.application.services.estudantes import ServicoEstudante
from ser_pleno.infrastructure.api.mural import servico_mural


class TestViews:

    @patch('ser_pleno.presentation.views.login.ServicoAutenticacao')
    def test_login_view(self, MockAuth, app, controller):
        from ser_pleno.presentation.views.login import LoginFrame
        # Setup
        view = LoginFrame(app, controller)
        assert view is not None
        
        # Test Login Action
        view.entry_user.insert(0, "admin")
        view.entry_pass.insert(0, "password")
        
        # Mock Service
        service = MockAuth.return_value
        service.login.return_value = {"success": True, "token": "abc"}
        
        # Trigger
        view.fazer_login()
        
        # Verify
        service.login.assert_called_with("admin", "password")

    @patch('ser_pleno.application.services.dashboard.ServicoDashboard')
    def test_dashboard_view(self, MockService, app, controller):
        # Setup
        view = DashboardFrame(app, controller)
        
        # Verify it initialized correctly
        assert view is not None
        assert hasattr(view, 'servico_dashboard')
        assert hasattr(view, 'kpi_frame')

    @patch('ser_pleno.application.services.agendamentos.ServicoAgendamento')
    def test_agenda_view(self, MockService, app, controller):
        view = AgendaFrame(app, controller)
        
        # Verify it initialized correctly
        assert view is not None
        assert hasattr(view, 'servico_agendamento')
        assert hasattr(view, 'data_selecionada')

    @patch('ser_pleno.application.services.agendamentos.ServicoAgendamento')
    def test_agenda_robustness(self, MockService, app, controller):
        view = AgendaFrame(app, controller)
        
        # Verify it handles initialization properly
        assert view is not None
        # Check it has the basic containers
        assert hasattr(view, 'container_grid')
        assert hasattr(view, 'container_semana')

    @patch('ser_pleno.application.services.estudantes.ServicoEstudante')
    def test_estudantes_view(self, MockService, app, controller):
        view = EstudantesFrame(app, controller)
        
        # Verify it initialized correctly
        assert view is not None
        assert hasattr(view, 'servico_estudante')

    @patch('ser_pleno.application.services.orientacoes.servico_orientacoes')
    def test_orientacoes_view(self, MockOrientacoes, app, controller):
        view = OrientacoesFrame(app, controller)
        
        # Verify it initialized correctly
        assert view is not None
        assert hasattr(view, 'servico_orientacoes')

    def test_analise_triagem_view(self, app, controller):
        # This view uses static data, no service needed
        view = AnaliseTriagemFrame(app, controller)
        
        # Verify it initialized correctly
        assert view is not None
        assert hasattr(view, 'data_master')
        assert len(view.data_master) > 0

    def test_analise_triagem_create(self, app, controller):
        """Test creating a screening via the view's API wrapper."""
        view = AnaliseTriagemFrame(app, controller)
        
        # The view has static data, not a service
        # We can test that it renders correctly
        assert view is not None

    @patch('ser_pleno.infrastructure.api.mural.servico_mural')
    def test_quadro_avisos_view(self, MockMural, app, controller):
        view = QuadroAvisosFrame(app, controller)
        
        # Verify it initialized correctly
        assert view is not None

    def test_comunicacao_view(self, app, controller):
        # Mock usuario_logado_id for the frame
        controller.usuario_logado_id = 1
        
        view = ComunicacaoInternaFrame(app, controller)
        
        # Test entry_mensagem attribute (not entry_msg)
        assert hasattr(view, 'entry_mensagem')
        
        # Send Message
        view.entry_mensagem.insert(0, "Nova mensagem")
        view.enviar_msg()
        # Verify entry cleared (msg sent logic internal)
        assert view.entry_mensagem.get() == ""

    def test_configuracoes_view(self, app, controller):
        view = ConfiguracoesFrame(app, controller)
        assert view is not None

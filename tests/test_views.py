import pytest
from unittest.mock import MagicMock, patch
from views.login import LoginFrame
from views.dashboard import DashboardFrame
from views.agenda import AgendaFrame
from views.estudantes import EstudantesFrame
from views.orientacoes import OrientacoesFrame
from views.analise_triagem import AnaliseTriagemFrame
from views.quadro_avisos import QuadroAvisosFrame
from views.comunicacao_interna import ComunicacaoInternaFrame
from views.configuracoes import ConfiguracoesFrame

class TestViews:
    
    @patch('views.login.AuthService')
    def test_login_view(self, MockAuth, app, controller):
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

    @patch('views.dashboard.DashboardService')
    def test_dashboard_view(self, MockService, app, controller):
        # Setup
        view = DashboardFrame(app, controller)
        
        # Mock Data update
        data = {"appointments_today": 10, "students_attention": 5}
        view.update_kpis(data)
        
        # Verify widgets presence (indirectly via no error)
        assert len(view.kpi_container.winfo_children()) == 5

    @patch('views.agenda.AppointmentService')
    def test_agenda_view(self, MockService, app, controller):
        view = AgendaFrame(app, controller)
        
        # Mock rendering
        mock_data = [{"time": "08:00", "student": {"name": "Teste"}, "status": "Agendado"}]
        view.update_view({"success": True, "data": mock_data})
        
        assert len(view.grid_frame_dia.winfo_children()) > 0

    @patch('views.agenda.AppointmentService')
    def test_agenda_view_robustness(self, MockService, app, controller):
        view = AgendaFrame(app, controller)
        
        # Scenario 1: Data is a dict but no results (e.g. error message)
        view.update_view({"success": True, "data": {"message": "no data"}})
        assert len(view.appointments) == 0

        # Scenario 2: Data items are not dicts (The reported error)
        view.update_view({"success": True, "data": ["invalid_string_item"]})
        assert len(view.appointments) == 0

    @patch('views.estudantes.StudentService')
    def test_estudantes_view(self, MockService, app, controller):
        view = EstudantesFrame(app, controller)
        
        # Test List Population
        mock_data = [{"name": "Aluno Teste", "course": "TI", "id": 1}]
        view.render_list({"success": True, "data": mock_data})
        
        # Test Selection
        view.selecionar_estudante({"name": "João", "course": "TI", "age": 20, "email": "j@j.com"})
        
        # Verify labels updated
        assert view.lbl_nome_det.cget("text") == "João"

    @patch('views.orientacoes.StudentService')
    def test_orientacoes_view(self, MockService, app, controller):
        view = OrientacoesFrame(app, controller)
        
        # Render Students
        view.render_students({"success": True, "data": [{"name": "Aluno 1"}]})
        
        # Select
        view.selecionar_aluno({"name": "Aluno 1"})

    @patch('views.analise_triagem.ScreeningService')
    def test_analise_triagem_view(self, MockService, app, controller):
        view = AnaliseTriagemFrame(app, controller)
        
        # Render List
        view._populate_list({"data": [{"student": {"name": "Test"}, "status": "pending"}]})
        
        # Tab Change
        view.mudar_tab("Concluídas")

    @patch('views.quadro_avisos.BoardService')
    def test_quadro_avisos_view(self, MockService, app, controller):
        view = QuadroAvisosFrame(app, controller)
        
        # Render Messages
        view.render_messages({"success": True, "data": [{"title": "Aviso 1", "author": "Admin"}]})

    def test_comunicacao_view(self, app, controller):
        view = ComunicacaoInternaFrame(app, controller)
        
        # Send Message
        view.entry_msg.insert(0, "Nova mensagem")
        view.enviar_msg()
        # Verify entry cleared (msg sent logic internal)
        assert view.entry_msg.get() == ""

    def test_configuracoes_view(self, app, controller):
        view = ConfiguracoesFrame(app, controller)
        assert view is not None

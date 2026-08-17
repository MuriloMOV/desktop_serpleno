import pytest
from unittest.mock import MagicMock, patch
import customtkinter as ctk
import time
from ser_pleno.ui.views.login import LoginFrame
from ser_pleno.ui.views.dashboard import DashboardFrame
from ser_pleno.ui.views.agenda import AgendaFrame
from ser_pleno.ui.views.estudantes import EstudantesFrame
from ser_pleno.ui.views.orientacoes import OrientacoesFrame
from ser_pleno.ui.views.triagem import TriagemFrame
from ser_pleno.ui.views.avisos import AvisosFrame
from ser_pleno.ui.views.comunicacao import ComunicacaoFrame
from ser_pleno.ui.views.configuracoes import ConfiguracoesFrame
from ser_pleno.application.services.autenticacao import ServicoAutenticacao
from ser_pleno.features.dashboard.service import ServicoDashboard
from ser_pleno.features.agenda.service import ServicoAgendamento
from ser_pleno.features.estudantes.service import ServicoEstudante
from ser_pleno.features.orientacoes.service import ServicoOrientacoes
from ser_pleno.infrastructure.api.mural import servico_mural


class TestViews:
    @patch("ser_pleno.ui.views.login.ServicoAutenticacao")
    def test_login_view(self, MockAuthService, app, controller):
        view = LoginFrame(app, controller)
        assert view is not None

        view.entry_user.insert(0, "admin")
        view.entry_pass.insert(0, "password")

        svc = MockAuthService.return_value
        svc.login.return_value = {"success": True, "token": "abc"}

        view.fazer_login()

        svc.login.assert_called_with("admin", "password")

    @patch("ser_pleno.ui.views.dashboard.ServicoDashboard")
    @patch("ser_pleno.ui.views.dashboard.ServicoAnalytics")
    def test_dashboard_view(self, MockAnalytics, MockDashboard, app, controller):
        view = DashboardFrame(app, controller)

        assert view is not None
        assert hasattr(view, "servico_dashboard")
        assert hasattr(view, "kpi_frame")

    @patch("ser_pleno.ui.views.agenda.ServicoAgendamento")
    def test_agenda_view(self, MockService, app, controller):
        view = AgendaFrame(app, controller)

        assert view is not None
        assert hasattr(view, "servico_agenda")
        assert hasattr(view, "data_selecionada")

    @patch("ser_pleno.ui.views.agenda.ServicoAgendamento")
    def test_agenda_robustness(self, MockService, app, controller):
        view = AgendaFrame(app, controller)

        assert view is not None
        assert hasattr(view, "container_grid")
        assert hasattr(view, "container_semana")

    @patch("ser_pleno.ui.views.estudantes.ServicoEstudante")
    def test_estudantes_view(self, MockService, app, controller):
        view = EstudantesFrame(app, controller)

        assert view is not None
        assert hasattr(view, "servico_estudantes")

    @patch("ser_pleno.ui.views.orientacoes.ServicoOrientacoes")
    def test_orientacoes_view(self, MockService, app, controller):
        view = OrientacoesFrame(app, controller)

        assert view is not None
        assert hasattr(view, "servico_orientacoes")

    @patch("ser_pleno.ui.views.triagem.ServicoTriagem")
    def test_triagem_view(self, MockService, app, controller):
        mock_svc = MockService.return_value
        mock_svc.listar_triagens.return_value = {
            "success": True,
            "data": [
                {
                    "id": 1,
                    "student_name": "Test Student",
                    "scheduled_date": "2026-07-09",
                    "priority": "Alta",
                    "status": "Pendente",
                }
            ],
        }
        view = TriagemFrame(app, controller)

        assert view is not None
        assert hasattr(view, "data_master")

    def test_triagem_create(self, app, controller):
        view = TriagemFrame(app, controller)

        assert view is not None

    @patch("ser_pleno.application.services.mural.ServicoMural")
    def test_avisos_view(self, MockServicoMural, app, controller):
        view = AvisosFrame(app, controller)

        assert view is not None

    @patch("ser_pleno.ui.views.comunicacao.ServicoComunicacao")
    def test_comunicacao_view(self, MockService, app, controller):
        controller.usuario_logado_id = 1

        view = ComunicacaoFrame(app, controller)

        assert hasattr(view, "entry_mensagem")

        view.conversa_ativa = {"role": "group", "id": 1}

        view.entry_mensagem.insert(0, "Nova mensagem")
        view.enviar_msg()
        assert view.entry_mensagem.get() == ""

    def test_configuracoes_view(self, app, controller):
        view = ConfiguracoesFrame(app, controller)
        assert view is not None

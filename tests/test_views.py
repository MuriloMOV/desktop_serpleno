import pytest
from unittest.mock import MagicMock, patch
import customtkinter as ctk
from ser_pleno.ui.views.login import LoginFrame
from ser_pleno.ui.views.dashboard import DashboardFrame
from ser_pleno.ui.views.agenda import AgendaFrame
from ser_pleno.ui.views.estudantes import EstudantesFrame
from ser_pleno.ui.views.orientacoes import OrientacoesFrame
from ser_pleno.ui.views.triagem import TriagemFrame
from ser_pleno.ui.views.avisos import AvisosFrame
from ser_pleno.ui.views.comunicacao import ComunicacaoFrame
from ser_pleno.ui.views.configuracoes import ConfiguracoesFrame
from ser_pleno.ui.views.interventions import IntervencoesFrame
from ser_pleno.ui.views.metas import MetasFrame
from ser_pleno.ui.views.relatorio import RelatorioFrame
from ser_pleno.ui.views.report_template import ReportTemplateFrame


pytestmark = pytest.mark.ui_heavy


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
        view._build_chat_area_lazy()

        assert hasattr(view, "entry_mensagem")

        view.conversa_ativa = {"role": "group", "id": 1}

        view.entry_mensagem.insert(0, "Nova mensagem")
        view.enviar_msg()
        assert view.entry_mensagem.get() == ""

    def test_configuracoes_view(self, app, controller):
        view = ConfiguracoesFrame(app, controller)
        assert view is not None

    @patch("ser_pleno.ui.views.interventions.ServicoIntervencoes")
    def test_intervencoes_view(self, MockService, app, controller):
        mock_svc = MockService.return_value
        mock_svc.listar_intervencoes.return_value = {
            "success": True,
            "data": {"interventions": [], "pagination": {"page": 1, "total": 0}},
        }
        view = IntervencoesFrame(app, controller)
        assert view is not None
        assert hasattr(view, "servico_intervencoes")

        view._area_historico = MagicMock()
        view._renderizar({"success": True, "data": {"interventions": []}})
        assert view._area_historico is not None

        view._area_historico.winfo_children.return_value = []
        intervention = {
            "id": 1,
            "student_name": "Ana",
            "date": "2024-01-01",
            "intervention_type": "counseling",
            "notes": "Teste",
            "outcome": "positive",
        }
        view._renderizar({"success": True, "data": {"interventions": [intervention]}})
        assert view._area_historico is not None

    @patch("ser_pleno.ui.views.interventions.AsyncRunner.run")
    @patch("ser_pleno.ui.views.interventions.ServicoIntervencoes")
    def test_intervencoes_salvar_sem_estudante(self, MockService, MockAsync, app, controller):
        view = IntervencoesFrame(app, controller)
        view._form_built = True
        view.f_tipo = MagicMock()
        view.f_tipo.get.return_value = "Aconselhamento"
        view.f_tipo.winfo_exists.return_value = True
        view.f_data = MagicMock()
        view.f_data.get.return_value = "2024-01-01"
        view.f_data.winfo_exists.return_value = True
        view.f_duracao = MagicMock()
        view.f_duracao.get.return_value = "45"
        view.f_duracao.winfo_exists.return_value = True
        view.f_resultado = MagicMock()
        view.f_resultado.get.return_value = "Pendente"
        view.f_resultado.winfo_exists.return_value = True
        view.f_notas = MagicMock()
        view.f_notas.get.return_value = "Anotacoes"
        view.f_notas.winfo_exists.return_value = True
        view.f_obs_resultado = MagicMock()
        view.f_obs_resultado.get.return_value = "Obs"
        view.f_obs_resultado.winfo_exists.return_value = True
        view._selected_student = None
        view._show_error = MagicMock()

        view._salvar_intervencao()
        view._show_error.assert_called()

    @patch("ser_pleno.ui.views.metas.ServicoMetas")
    def test_metas_view(self, MockService, app, controller):
        mock_svc = MockService.return_value
        mock_svc.obter_stats.return_value = {
            "success": True,
            "data": {"total": 0, "by_status": [], "by_category": [], "by_priority": [], "overdue": 0},
        }
        mock_svc.listar_metas.return_value = {
            "success": True,
            "data": {"goals": [], "pagination": {"page": 1, "total": 0}},
        }
        mock_svc.obter_atrasadas.return_value = {"success": True, "data": []}
        view = MetasFrame(app, controller)
        assert view is not None
        assert hasattr(view, "servico_metas")

        view.scroll_list = MagicMock()
        view.lbl_count = MagicMock()
        view._mostrar_metas([])
        view.lbl_count.configure.assert_called_with(text="0 metas")

        metas = [
            {
                "id": 1,
                "title": "Meta 1",
                "status": "in_progress",
                "priority": "high",
                "target_date": "2024-12-31",
                "progress_percentage": 50,
                "student_name": "Ana",
            }
        ]
        view._mostrar_metas(metas)
        view.lbl_count.configure.assert_called_with(text="1 meta")

        view.scroll_atrasadas = MagicMock()
        view.lbl_count_atrasadas = MagicMock()
        view._mostrar_atrasadas([])
        view.lbl_count_atrasadas.configure.assert_called_with(text="0 metas atrasadas")

        view._todas_metas = [
            {
                "id": 1,
                "title": "Meta 1",
                "status": "in_progress",
                "priority": "high",
                "category": "Academico",
                "student_name": "Ana",
                "student_id": 1,
            }
        ]
        view._mostrar_metas = MagicMock()
        view._aplicar_filtros()
        view._mostrar_metas.assert_called_once()

        view._stats = {
            "total": 10,
            "by_status": [{"status": "in_progress", "count": 5}, {"status": "completed", "count": 3}],
            "by_priority": [{"priority": "high", "count": 2}, {"priority": "urgent", "count": 1}],
            "overdue": 2,
        }
        view._kpi_total = MagicMock()
        view._kpi_progresso = MagicMock()
        view._kpi_concluidas = MagicMock()
        view._kpi_atrasadas = MagicMock()
        view._kpi_urgentes = MagicMock()

        view._atualizar_kpis()
        view._kpi_total.set_value.assert_called_with("10")
        view._kpi_progresso.set_value.assert_called_with("5")
        view._kpi_concluidas.set_value.assert_called_with("3")
        view._kpi_atrasadas.set_value.assert_called_with("2")
        view._kpi_urgentes.set_value.assert_called_with("3")

    @patch("ser_pleno.ui.views.report_template.ServicoReportTemplate")
    def test_report_template_view(self, MockService, app, controller):
        mock_svc = MockService.return_value
        mock_svc.listar_templates.return_value = {"success": True, "data": []}
        view = ReportTemplateFrame(app, controller)
        assert view is not None
        assert hasattr(view, "servico_report_template")
        assert hasattr(view, "lista")

        assert view._parse([]) == []
        assert view._parse({"success": False}) == []
        assert view._parse({"data": [{"id": 1}]}) == [{"id": 1}]

        data = [{"id": 1, "name": "T1"}]
        assert view._parse({"success": True, "data": data}) == data

    @patch("ser_pleno.ui.views.relatorio.ServicoRelatorio")
    @patch("ser_pleno.ui.views.relatorio.ServicoReportTemplate")
    def test_relatorio_view(self, MockTemplateService, MockRelatorioService, app, controller):
        mock_rel = MockRelatorioService.return_value
        mock_rel.obter_estatisticas.return_value = {
            "success": True,
            "data": {"summary": {"students_total": 0, "appointments_total": 0, "interventions_total": 0, "screenings_total": 0}}
        }
        mock_rel.listar_relatorios.return_value = {"success": True, "data": []}
        view = RelatorioFrame(app, controller)
        assert view is not None
        assert hasattr(view, "servico_relatorio")
        assert hasattr(view, "servico_report_template")

        assert view._extract_items([{"id": 1}]) == [{"id": 1}]
        assert view._extract_items({"reports": [{"id": 1}]}) == [{"id": 1}]
        assert view._extract_items({}) == []

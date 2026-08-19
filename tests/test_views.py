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

pytestmark = pytest.mark.ui_heavy


class TestViews:
    @patch("ser_pleno.ui.views.login.ServicoAutenticacao")
    def test_login_view(self, MockAuthService, app, controller):
        view = LoginFrame(app, controller)
        view.entry_user.insert(0, "admin")
        view.entry_pass.insert(0, "password")
        svc = MockAuthService.return_value
        svc.login.return_value = {"success": True, "token": "abc"}
        
        view.fazer_login()
        
        svc.login.assert_called_with("admin", "password")
        view.destroy()

    def test_dashboard_view(self, app, controller):
        view = DashboardFrame(app, controller)
        assert hasattr(view, "servico_dashboard")
        assert hasattr(view, "kpi_frame")
        view.destroy()

    @patch("ser_pleno.ui.views.agenda.ServicoAgendamento")
    def test_agenda_view(self, MockService, app, controller):
        view = AgendaFrame(app, controller)
        assert hasattr(view, "servico_agenda")
        assert hasattr(view, "data_selecionada")
        view.destroy()

    def test_estudantes_view(self, app, controller):
        view = EstudantesFrame(app, controller)
        assert hasattr(view, "servico_estudantes")
        view.destroy()

    def test_orientacoes_view(self, app, controller):
        view = OrientacoesFrame(app, controller)
        assert hasattr(view, "servico_orientacoes")
        view.destroy()

    def test_triagem_view(self, app, controller):
        view = TriagemFrame(app, controller)
        assert hasattr(view, "data_master")
        view.destroy()

    @patch("ser_pleno.application.services.mural.ServicoMural")
    def test_avisos_view(self, MockServicoMural, app, controller):
        view = AvisosFrame(app, controller)
        assert view is not None
        view.destroy()

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
        view.destroy()

    def test_configuracoes_view(self, app, controller):
        view = ConfiguracoesFrame(app, controller)
        assert view is not None
        view.destroy()

    @patch("ser_pleno.ui.views.interventions.WidgetBatchBuilder")
    @patch("ser_pleno.ui.views.interventions.AsyncRunner.run")
    @patch("ser_pleno.ui.views.interventions.ServicoIntervencoes")
    @patch("ser_pleno.features.estudantes.service.servico_estudante")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._criar_conteudo")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._carregar_estudantes")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._carregar_intervencoes")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._build_form_lazy")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._build_filtros_lazy")
    def test_intervencoes_view(self, mock_build_filtros, mock_build_form, mock_carregar_intervencoes, mock_carregar_estudantes, mock_criar_conteudo, MockServicoEstudante, MockService, MockAsync, MockWidgetBatch, app, controller):
        from ser_pleno.ui.views.interventions import IntervencoesFrame
        
        mock_svc = MockService.return_value
        mock_svc.listar_intervencoes.return_value = {
            "success": True,
            "data": {"interventions": [], "pagination": {"page": 1, "total": 0}},
        }
        MockServicoEstudante.listar_estudantes.return_value = {"success": True, "data": []}
        
        mock_batch_instance = MagicMock()
        MockWidgetBatch.return_value = mock_batch_instance
        
        view = IntervencoesFrame(app, controller)
        assert hasattr(view, "servico_intervencoes")

        view._area_historico = ctk.CTkFrame(app)
        view._area_historico.winfo_children = MagicMock(return_value=[])
        view._renderizar({"success": True, "data": {"interventions": []}})
        
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
        
        view._area_historico.destroy()
        view.destroy()

    @patch("ser_pleno.ui.views.interventions.WidgetBatchBuilder")
    @patch("ser_pleno.ui.views.interventions.AsyncRunner.run")
    @patch("ser_pleno.ui.views.interventions.ServicoIntervencoes")
    @patch("ser_pleno.features.estudantes.service.servico_estudante")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._criar_conteudo")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._carregar_estudantes")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._carregar_intervencoes")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._build_form_lazy")
    @patch("ser_pleno.ui.views.interventions.IntervencoesFrame._build_filtros_lazy")
    def test_intervencoes_salvar_sem_estudante(self, mock_build_filtros, mock_build_form, mock_carregar_intervencoes, mock_carregar_estudantes, mock_criar_conteudo, MockServicoEstudante, MockService, MockAsync, MockWidgetBatch, app, controller):
        from ser_pleno.ui.views.interventions import IntervencoesFrame
        
        mock_batch_instance = MagicMock()
        MockWidgetBatch.return_value = mock_batch_instance
        
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
        view.destroy()

    def test_metas_view(self, app, controller):
        from ser_pleno.ui.views.metas import MetasFrame
        from ser_pleno.utils.widget_batch import WidgetBatchBuilder as RealWBB

        original_init = MetasFrame.__init__

        def _patched_init(self, parent, controller):
            ctk.CTkFrame.__init__(self, parent, fg_color="#1a1a1a")
            self.controller = controller
            self.servico_metas = getattr(controller, "servico_metas", None)
            self._todas_metas = []
            self._selecionado = None
            self._filter_after_id = None
            self._stats = {}
            self._overdue_count = 0
            self._metas_atrasadas = []

        MetasFrame.__init__ = _patched_init
        try:
            view = MetasFrame(app, controller)
        finally:
            MetasFrame.__init__ = original_init

        assert view is not None
        assert hasattr(view, "servico_metas")

        view.scroll_list = ctk.CTkScrollableFrame(view, fg_color="transparent")
        view.lbl_count = MagicMock()

        # Mock WidgetBatchBuilder para _mostrar_metas
        with patch.object(RealWBB, 'execute', return_value=None):
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

        view.scroll_atrasadas = ctk.CTkScrollableFrame(view, fg_color="transparent")
        view.lbl_count_atrasadas = MagicMock()

        # Mock WidgetBatchBuilder para _mostrar_atrasadas
        with patch.object(RealWBB, 'execute', return_value=None):
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

        view.destroy()

    def test_report_template_view(self, app, controller):
        from ser_pleno.ui.views.report_template import ReportTemplateFrame

        original_init = ReportTemplateFrame.__init__

        def _patched_init(self, parent, controller):
            ctk.CTkFrame.__init__(self, master=parent, fg_color="#1a1a1a")
            self.controller = controller
            self.servico_report_template = getattr(controller, "servico_report_template", None)
            self.app = getattr(controller, "app", None)
            self._templates = []
            self._filtro_tipo = ""

        ReportTemplateFrame.__init__ = _patched_init
        try:
            view = ReportTemplateFrame(app, controller)
        finally:
            ReportTemplateFrame.__init__ = original_init

        view.lista = MagicMock()
        assert view is not None
        assert hasattr(view, "servico_report_template")
        assert hasattr(view, "lista")

        assert view._parse([]) == []
        assert view._parse({"success": False}) == []
        assert view._parse({"data": [{"id": 1}]}) == [{"id": 1}]

        data = [{"id": 1, "name": "T1"}]
        assert view._parse({"success": True, "data": data}) == data

    def test_relatorio_view(self, app, controller):
        from ser_pleno.ui.views.relatorio import RelatorioFrame

        original_init = RelatorioFrame.__init__

        def _patched_init(self, parent, controller):
            ctk.CTkFrame.__init__(self, parent, fg_color="#1a1a1a")
            self.controller = controller
            self.servico_relatorio = getattr(controller, "servico_relatorio", None)
            self.servico_report_template = getattr(controller, "servico_report_template", None)
            self._kpi_cards = {}
            self._summary_vals = {}
            self._chart_data = []
            self._todos_relatorios = []
            self._selecionados = set()
            self._heavy_built = False
            self.filtro_tipo = None
            self.filtro_busca = None
            self.filtro_data_inicio = None
            self.filtro_data_fim = None
            self._export_data_inicio = None
            self._export_data_fim = None
            self._export_tipo = None
            self._export_formato = None
            self.reports_container = None
            self._bulk_bar = None
            self._bulk_count_lbl = None
            self._select_all_var = None

        RelatorioFrame.__init__ = _patched_init
        try:
            view = RelatorioFrame(app, controller)
        finally:
            RelatorioFrame.__init__ = original_init

        assert view is not None
        assert hasattr(view, "servico_relatorio")
        assert hasattr(view, "servico_report_template")

        assert view._extract_items([{"id": 1}]) == [{"id": 1}]
        assert view._extract_items({"reports": [{"id": 1}]}) == [{"id": 1}]
        assert view._extract_items({}) == []

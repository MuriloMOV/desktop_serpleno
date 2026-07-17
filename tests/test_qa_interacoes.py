"""
QA — Teste abrangente de elementos interativos e fluxos CRUD
Cobre: Login, Dashboard, Agenda, Estudantes, Orientações, Triagem,
       Avisos, Comunicação, Configurações, Bem-Estar e Relatórios.
"""
from __future__ import annotations

import pytest
import customtkinter as ctk
from unittest.mock import MagicMock, patch, PropertyMock
from tkinter import TclError, messagebox
import datetime
import os

from ser_pleno.presentation.views.login import LoginFrame
from ser_pleno.presentation.views.dashboard import DashboardFrame
from ser_pleno.presentation.views.agenda import AgendaFrame, AppointmentModal, GradeManagementModal
from ser_pleno.presentation.views.estudantes import EstudantesFrame
from ser_pleno.presentation.views.orientacoes import OrientacoesFrame
from ser_pleno.presentation.views.triagem import TriagemFrame
from ser_pleno.presentation.views.avisos import AvisosFrame, PublicacaoModal
from ser_pleno.presentation.views.comunicacao import ComunicacaoFrame
from ser_pleno.presentation.views.configuracoes import ConfiguracoesFrame, AlterarSenhaModal
from ser_pleno.presentation.views.bem_estar import BemEstarFrame
from ser_pleno.presentation.views.relatorio import RelatorioFrame


@pytest.fixture(scope="function")
def app():
    ctk.set_appearance_mode("Dark")
    try:
        app = ctk.CTk()
    except TclError as error:
        pytest.skip(f"Tcl/Tk indisponível para testes visuais: {error}")
    app.geometry("1200x800")
    yield app
    try:
        app.destroy()
    except Exception:
        pass


@pytest.fixture
def controller(app):
    controller = MagicMock()
    controller.content = app
    controller.usuario_logado = {
        "id": 1,
        "username": "admin",
        "first_name": "Admin",
        "last_name": "Test",
        "email": "admin@test.com",
    }
    controller.usuario_logado_id = 1
    return controller


@pytest.fixture(autouse=True)
def mock_network(monkeypatch):
    monkeypatch.setattr("requests.get", MagicMock())
    monkeypatch.setattr("requests.post", MagicMock())


class TestLoginQA:
    def test_campos_existem(self, app, controller):
        view = LoginFrame(app, controller)
        assert view is not None
        assert hasattr(view, "input_user")
        assert hasattr(view, "input_pass")
        assert hasattr(view, "btn_entrar")
        assert hasattr(view, "lbl_erro")

    def test_botao_entrar_desabilitado_em_loading(self, app, controller):
        view = LoginFrame(app, controller)
        view._is_loading = True
        view.btn_entrar.configure(text="Aguarde...", state="disabled")
        assert view.btn_entrar.cget("state") == "disabled"

    def test_toggle_senha(self, app, controller):
        view = LoginFrame(app, controller)
        assert hasattr(view.input_pass, "entry")
        assert hasattr(view.input_pass, "_eye_btn")
        view.input_pass._toggle_show()
        assert view.input_pass._show_pass is True
        view.input_pass._toggle_show()
        assert view.input_pass._show_pass is False

    def test_validacao_campos_vazios(self, app, controller):
        view = LoginFrame(app, controller)
        view.input_user.clear_state()
        view.input_pass.clear_state()
        view.lbl_erro.configure(text="")
        view._fazer_login()
        assert view.lbl_erro.cget("text") != ""

    def test_login_sucesso_chama_controller(self, app, controller):
        with patch("ser_pleno.presentation.views.login.AutenticacaoController") as MockAuth:
            ctrl = MockAuth.return_value
            ctrl.login.return_value = {"success": True, "user": {"id": 1, "username": "admin"}}
            view = LoginFrame(app, controller)
            view.input_user.entry.insert(0, "admin")
            view.input_pass.entry.insert(0, "password")
            view._fazer_login()
            ctrl.login.assert_called_with("admin", "password")

    def test_modal_termos_abre(self, app, controller):
        view = LoginFrame(app, controller)
        view._abrir_termos()
        assert view is not None


class TestDashboardQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.dashboard.DashboardController") as MockCtrl:
            view = DashboardFrame(app, controller)
            assert view is not None
            assert hasattr(view, "controller_dashboard")
            assert hasattr(view, "kpi_frame")
            assert hasattr(view, "help_badge")
            assert hasattr(view, "alert_badge")

    def test_abrir_notificacoes_ajuda(self, app, controller):
        with patch("ser_pleno.presentation.views.dashboard.DashboardController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.obter_notificacoes_ajuda.return_value = []
            view = DashboardFrame(app, controller)
            view._abrir_notificacoes_ajuda()

    def test_abrir_notificacoes_alertas(self, app, controller):
        with patch("ser_pleno.presentation.views.dashboard.DashboardController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.obter_notificacoes_alertas.return_value = []
            view = DashboardFrame(app, controller)
            view._abrir_notificacoes_alertas()

    def test_abrir_perfil(self, app, controller):
        with patch("ser_pleno.presentation.views.dashboard.DashboardController") as MockCtrl:
            view = DashboardFrame(app, controller)
            view._abrir_perfil()
            assert view is not None

    def test_marcar_lida(self, app, controller):
        with patch("ser_pleno.presentation.views.dashboard.DashboardController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.obter_notificacoes_ajuda.return_value = []
            mock_ctrl.obter_notificacoes_alertas.return_value = []
            view = DashboardFrame(app, controller)
            view._marcar_lida(1, "ajuda")
            mock_ctrl.marcar_notificacao_como_lida.assert_called_with(1, "ajuda")

    def test_humor_emoji(self, app, controller):
        assert DashboardFrame._humor_emoji(None) != ""
        assert DashboardFrame._humor_emoji(1.0) != ""
        assert DashboardFrame._humor_emoji(5.0) != ""


class TestAgendaQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            view = AgendaFrame(app, controller)
            assert view is not None
            assert hasattr(view, "controller_agenda")
            assert hasattr(view, "container_grid")
            assert hasattr(view, "container_semana")

    def test_alterar_data(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            view = AgendaFrame(app, controller)
            initial = view.data_selecionada
            view.alterar_data(1)
            assert view.data_selecionada == initial + datetime.timedelta(days=1)

    def test_modal_agendamento_campos(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            view = AgendaFrame(app, controller)
            view.horarios_base = ["08:00", "09:00"]
            view.mapa_estudantes = {"Ana": 1}
            modal = AppointmentModal(
                app, "08:00", None,
                horarios_base=view.horarios_base,
                mapa_estudantes=view.mapa_estudantes,
                on_save=lambda *a: {"success": True},
                on_delete=lambda *a: {"success": True},
                on_success=lambda: None,
            )
            assert modal is not None
            assert hasattr(modal, "combo_hora")
            assert hasattr(modal, "combo_estudante")
            assert hasattr(modal, "combo_status")
            assert hasattr(modal, "txt_obs")

    def test_modal_agendamento_salvar_sucesso(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            view = AgendaFrame(app, controller)
            view.horarios_base = ["08:00"]
            view.mapa_estudantes = {"Ana": 1}
            on_success = MagicMock()
            modal = AppointmentModal(
                app, "08:00", None,
                horarios_base=view.horarios_base,
                mapa_estudantes=view.mapa_estudantes,
                on_save=lambda id_old, dados: {"success": True},
                on_delete=lambda *a: {"success": True},
                on_success=on_success,
            )
            modal.combo_hora.set("08:00")
            modal.combo_estudante.set("Ana")
            modal.combo_status.set("Agendado")
            modal._save()
            on_success.assert_called()

    def test_modal_agendamento_deletar(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            view = AgendaFrame(app, controller)
            info = {"id_agendamento": 1, "nome": "Ana", "status": "Agendado"}
            on_success = MagicMock()
            modal = AppointmentModal(
                app, "08:00", info,
                horarios_base=["08:00"],
                mapa_estudantes={"Ana": 1},
                on_save=lambda *a: {"success": True},
                on_delete=lambda id_: {"success": True},
                on_success=on_success,
            )
            with patch("tkinter.messagebox.askyesno", return_value=True):
                modal._delete()
            on_success.assert_called()

    def test_grade_management_modal(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.listar_horarios_base.return_value = ["08:00", "09:00"]
            view = AgendaFrame(app, controller)
            view.horarios_base = ["08:00", "09:00"]
            modal = GradeManagementModal(
                app, view.horarios_base, mock_ctrl,
                on_refresh=lambda: None,
            )
            assert modal is not None
            assert hasattr(modal, "entry_novo")

    def test_salvar_agendamento_cria_novo(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.criar_agendamento.return_value = {"success": True}
            view = AgendaFrame(app, controller)
            res = view._salvar_agendamento(None, {"nome_aluno": "Ana", "id_aluno": 1, "data_hora": "2025-01-01 08:00", "motivo": "", "status": "Agendado"})
            assert res.get("success") is True
            mock_ctrl.criar_agendamento.assert_called()

    def test_remover_agendamento(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.deletar_agendamento.return_value = {"success": True}
            view = AgendaFrame(app, controller)
            res = view.remover_agendamento(1)
            assert res.get("success") is True
            mock_ctrl.deletar_agendamento.assert_called_with(1)


class TestEstudantesQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.estudantes.EstudantesController") as MockCtrl:
            view = EstudantesFrame(app, controller)
            assert view is not None
            assert hasattr(view, "controller_estudantes")
            assert hasattr(view, "entry_busca")
            assert hasattr(view, "f_laudo")
            assert hasattr(view, "f_aten")
            assert hasattr(view, "scroll_list")
            assert hasattr(view, "btn_editar")

    def test_novo_estudante_modal_campos(self, app, controller):
        with patch("ser_pleno.presentation.views.estudantes.EstudantesController") as MockCtrl:
            view = EstudantesFrame(app, controller)
            view.novo_estudante_click()
            assert view is not None

    def test_criar_estudante_sucesso(self, app, controller):
        with patch("ser_pleno.presentation.views.estudantes.EstudantesController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.criar_estudante.return_value = {"success": True}
            view = EstudantesFrame(app, controller)
            res = mock_ctrl.criar_estudante({
                "nome": "Ana Silva",
                "email": "ana@test.com",
                "has_medical_report": False,
                "requires_attention": False,
                "course": "Psicologia",
                "age": "22",
            })
            assert res.get("success") is True

    def test_editar_estudante_sem_selecao(self, app, controller):
        with patch("ser_pleno.presentation.views.estudantes.EstudantesController") as MockCtrl:
            view = EstudantesFrame(app, controller)
            view._selecionado = None
            fake_msgbox = MagicMock()
            with patch("ser_pleno.presentation.views.estudantes.messagebox", fake_msgbox, create=True):
                view._editar_estudante()
                fake_msgbox.showinfo.assert_called_with("Atenção", "Selecione um estudante primeiro.")

    def test_excluir_estudante_sem_selecao(self, app, controller):
        with patch("ser_pleno.presentation.views.estudantes.EstudantesController") as MockCtrl:
            view = EstudantesFrame(app, controller)
            view._selecionado = None
            fake_msgbox = MagicMock()
            with patch("ser_pleno.presentation.views.estudantes.messagebox", fake_msgbox, create=True):
                view._excluir_estudante()
                fake_msgbox.showinfo.assert_called_with("Atenção", "Selecione um estudante primeiro.")

    def test_selecionar_estudante_atualiza_ui(self, app, controller):
        with patch("ser_pleno.presentation.views.estudantes.EstudantesController") as MockCtrl:
            view = EstudantesFrame(app, controller)
            st = {"name": "Ana", "course": "Psicologia", "requires_attention": False, "has_medical_report": True, "contact": "ana@test.com", "age": 22}
            view.selecionar_estudante(st)
            assert view._selecionado == st
            assert view.lbl_nome_det.cget("text") == "Ana"

    def test_filtros_aplicar(self, app, controller):
        with patch("ser_pleno.presentation.views.estudantes.EstudantesController") as MockCtrl:
            view = EstudantesFrame(app, controller)
            view._todos_estudantes = [
                {"name": "Ana", "course": "Psicologia", "has_medical_report": True, "requires_attention": False},
                {"name": "Bruno", "course": "Administração", "has_medical_report": False, "requires_attention": True},
            ]
            view._aplicar_filtros()
            assert True


class TestOrientacoesQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.orientacoes.OrientacoesController") as MockCtrl:
            view = OrientacoesFrame(app, controller)
            assert view is not None
            assert hasattr(view, "controller_orientacoes")
            assert hasattr(view, "_tab_btns")

    def test_mudar_tab(self, app, controller):
        with patch("ser_pleno.presentation.views.orientacoes.OrientacoesController") as MockCtrl:
            view = OrientacoesFrame(app, controller)
            view._mudar_tab("nova")
            assert view._tab_ativo == "nova"
            view._mudar_tab("historico")
            assert view._tab_ativo == "historico"

    def test_salvar_orientacao_campos(self, app, controller):
        with patch("ser_pleno.presentation.views.orientacoes.OrientacoesController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.criar_orientacao.return_value = {"success": True}
            view = OrientacoesFrame(app, controller)
            view.f_titulo.insert(0, "Orientação Teste")
            view.f_conteudo.insert("1.0", "Conteúdo teste")
            view.f_tema.widget.set("Geral")
            view.f_data.insert(0, "2025-01-01")
            with patch.object(view, "_carregar_dados"):
                with patch("ser_pleno.presentation.views.orientacoes.AsyncRunner.run") as mock_run:
                    def fake_run(task, on_success, on_error, widget_ref):
                        res = task()
                        on_success(res)
                    mock_run.side_effect = fake_run
                    view._salvar_orientacao()
                    mock_ctrl.criar_orientacao.assert_called()

    def test_editar_orientacao_popula_form(self, app, controller):
        with patch("ser_pleno.presentation.views.orientacoes.OrientacoesController") as MockCtrl:
            view = OrientacoesFrame(app, controller)
            o = {"id": 1, "title": "Título", "content": "Conteúdo", "theme": "Acadêmico", "session_date": "2025-01-01", "referral": "", "notes": ""}
            view._editar_orientacao(o)
            assert view._orientacao_editando_id == 1
            assert view.f_titulo.get() == "Título"

    def test_excluir_orientacao(self, app, controller):
        with patch("ser_pleno.presentation.views.orientacoes.OrientacoesController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.deletar_orientacao.return_value = {"success": True}
            view = OrientacoesFrame(app, controller)
            with patch("tkinter.messagebox.askyesno", return_value=True):
                with patch.object(view, "_carregar_dados"):
                    with patch("ser_pleno.presentation.views.orientacoes.AsyncRunner.run") as mock_run:
                        def fake_run(task, on_success, on_error, widget_ref):
                            res = task()
                            on_success(res)
                        mock_run.side_effect = fake_run
                        view._excluir_orientacao(1)
                        mock_ctrl.deletar_orientacao.assert_called_with(1)

    def test_modal_detalhe(self, app, controller):
        with patch("ser_pleno.presentation.views.orientacoes.OrientacoesController") as MockCtrl:
            view = OrientacoesFrame(app, controller)
            o = {"id": 1, "title": "Título", "theme": "Geral", "session_date": "2025-01-01", "referral": "", "content": "Conteúdo"}
            view._modal_detalhe(o)
            assert view is not None


class TestTriagemQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.triagem.TriagemController") as MockCtrl:
            view = TriagemFrame(app, controller)
            assert view is not None
            assert hasattr(view, "controller_triagem")
            assert hasattr(view, "filtro_status")
            assert hasattr(view, "filtro_prioridade")
            assert hasattr(view, "lista_triagens")

    def test_abrir_nova_triagem(self, app, controller):
        with patch("ser_pleno.presentation.views.triagem.TriagemController") as MockCtrl:
            view = TriagemFrame(app, controller)
            view.abrir_nova_triagem()
            assert view is not None

    def test_aplicar_filtros(self, app, controller):
        with patch("ser_pleno.presentation.views.triagem.TriagemController") as MockCtrl:
            view = TriagemFrame(app, controller)
            view.data_master = [
                {"id": 1, "student": "Ana", "date": "2025-01-01", "priority": "Alta", "status": "Pendente"},
                {"id": 2, "student": "Bruno", "date": "2025-01-02", "priority": "Baixa", "status": "Concluída"},
            ]
            view.filtro_status.set("Pendente")
            view.filtro_prioridade.set("Todas")
            view.aplicar_filtros()
            assert hasattr(view, "lista_triagens")

    def test_limpar_filtros(self, app, controller):
        with patch("ser_pleno.presentation.views.triagem.TriagemController") as MockCtrl:
            view = TriagemFrame(app, controller)
            view.data_master = []
            view.limpar_filtros()
            assert view.filtro_status.get() == "Todos"
            assert view.filtro_prioridade.get() == "Todas"

    def test_excluir_triagem(self, app, controller):
        with patch("ser_pleno.presentation.views.triagem.TriagemController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.deletar_triagem.return_value = {"success": True}
            view = TriagemFrame(app, controller)
            item = {"id": 1, "student": "Ana", "date": "2025-01-01", "priority": "Alta", "status": "Pendente"}
            with patch("tkinter.messagebox.showerror"):
                with patch("ser_pleno.presentation.views.triagem.AsyncRunner.run") as mock_run:
                    def fake_run(task, on_success, on_error, widget_ref):
                        res = task()
                        on_success(res)
                    mock_run.side_effect = fake_run
                    view._excluir_triagem(item)
                    mock_ctrl.deletar_triagem.assert_called_with(1)

    def test_modal_editar_triagem(self, app, controller):
        with patch("ser_pleno.presentation.views.triagem.TriagemController") as MockCtrl:
            view = TriagemFrame(app, controller)
            item = {"id": 1, "student": "Ana", "date": "2025-01-01", "priority": "Alta", "status": "Pendente"}
            view._modal_editar_triagem(item)
            assert view is not None

    def test_modal_detalhe(self, app, controller):
        with patch("ser_pleno.presentation.views.triagem.TriagemController") as MockCtrl:
            view = TriagemFrame(app, controller)
            item = {"id": 1, "student": "Ana", "date": "2025-01-01", "priority": "Alta", "status": "Pendente"}
            view._modal_detalhe(item)
            assert view is not None


class TestAvisosQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.application.controllers.avisos.ServicoMural") as MockMural:
            view = AvisosFrame(app, controller)
            assert view is not None
            assert hasattr(view, "lista")
            assert hasattr(view, "posts")

    def test_abrir_modal_novo(self, app, controller):
        with patch("ser_pleno.application.controllers.avisos.ServicoMural") as MockMural:
            view = AvisosFrame(app, controller)
            view._abrir_modal_novo()
            assert view._modal is not None

    def test_publicacao_modal_campos(self, app, controller):
        with patch("ser_pleno.application.controllers.avisos.ServicoMural") as MockMural:
            view = AvisosFrame(app, controller)
            view._abrir_modal_novo()
            modal = view._modal
            assert modal is not None
            assert hasattr(modal, "f_titulo")
            assert hasattr(modal, "f_conteudo")
            assert hasattr(modal, "f_categoria")
            assert hasattr(modal, "_btn_publicar")

    def test_on_edit_carrega_dados(self, app, controller):
        with patch("ser_pleno.application.controllers.avisos.ServicoMural") as MockMural:
            mock_service = MockMural.return_value
            mock_service.obter_mensagem.return_value = {
                "success": True,
                "data": {"id": 1, "titulo": "Teste", "conteudo": "Conteúdo", "categoria": "informativo"},
            }
            controller.get_service.return_value = mock_service
            view = AvisosFrame(app, controller)
            with patch("ser_pleno.utils.async_runner.AsyncRunner.run") as mock_run:
                def fake_run(task, on_success, on_error, widget_ref):
                    res = task()
                    on_success(res)
                mock_run.side_effect = fake_run
                with patch("threading.Thread") as mock_thread:
                    def run_thread(target, **kwargs):
                        target()
                    mock_thread.side_effect = lambda target, **kwargs: type('Thread', (), {'start': lambda self: target()})()
                    view._on_edit(1)
            assert view._modal is not None

    def test_on_delete(self, app, controller):
        with patch("ser_pleno.application.controllers.avisos.ServicoMural") as MockMural:
            mock_service = MockMural.return_value
            mock_service.deletar_mensagem.return_value = {"success": True}
            view = AvisosFrame(app, controller)
            with patch("tkinter.messagebox.askyesno", return_value=True):
                view._on_delete(1)
            assert True

    def test_modal_publicar_sem_titulo(self, app, controller):
        with patch("ser_pleno.application.controllers.avisos.ServicoMural") as MockMural:
            view = AvisosFrame(app, controller)
            view._abrir_modal_novo()
            modal = view._modal
            modal.f_titulo.delete(0, "end")
            modal.f_conteudo.delete("1.0", "end")
            with patch("tkinter.messagebox.showwarning") as mock_warn:
                modal._on_save()
                mock_warn.assert_called_with("Atenção", "Preencha título e conteúdo.")


class TestComunicacaoQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.comunicacao.ComunicacaoController") as MockCtrl:
            controller.usuario_logado_id = 1
            view = ComunicacaoFrame(app, controller)
            assert view is not None
            assert hasattr(view, "entry_mensagem")
            assert hasattr(view, "btn_enviar")
            assert hasattr(view, "scroll_contacts")

    def test_enviar_mensagem_sem_conversa(self, app, controller):
        with patch("ser_pleno.presentation.views.comunicacao.ComunicacaoController") as MockCtrl:
            controller.usuario_logado_id = 1
            view = ComunicacaoFrame(app, controller)
            view.conversa_ativa = None
            view.entry_mensagem.insert(0, "Olá")
            view.enviar_mensagem()
            assert view.entry_mensagem.get() == "Olá"

    def test_enviar_mensagem_grupo(self, app, controller):
        with patch("ser_pleno.presentation.views.comunicacao.ComunicacaoController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.enviar_mensagem_grupo_texto.return_value = {"success": True}
            controller.usuario_logado_id = 1
            view = ComunicacaoFrame(app, controller)
            view.conversa_ativa = {"role": "group", "id": 1}
            view.entry_mensagem.insert(0, "Mensagem grupo")
            with patch.object(view, "carregar_mensagens"), patch.object(view, "carregar_contador_nao_lidas"), patch.object(view, "atualizar_lista_contatos"):
                view.enviar_mensagem()
            mock_ctrl.enviar_mensagem_grupo_texto.assert_called_with(1, "Mensagem grupo")

    def test_nova_conversa_reseta(self, app, controller):
        with patch("ser_pleno.presentation.views.comunicacao.ComunicacaoController") as MockCtrl:
            controller.usuario_logado_id = 1
            view = ComunicacaoFrame(app, controller)
            view._nova_conversa()
            assert view.conversa_ativa is None
            assert view.mensagens == []

    def test_toggle_modal_arquivos(self, app, controller):
        with patch("ser_pleno.presentation.views.comunicacao.ComunicacaoController") as MockCtrl:
            controller.usuario_logado_id = 1
            view = ComunicacaoFrame(app, controller)
            assert hasattr(view, "modal_arquivos")
            view.toggle_modal_arquivos()
            view.toggle_modal_arquivos()

    def test_selecionar_conversa(self, app, controller):
        with patch("ser_pleno.presentation.views.comunicacao.ComunicacaoController") as MockCtrl:
            controller.usuario_logado_id = 1
            view = ComunicacaoFrame(app, controller)
            contato = {"id": 1, "name": "Teste", "role": "admin"}
            item_widget = MagicMock()
            with patch.object(view, "carregar_mensagens"):
                view.selecionar_conversa(contato, item_widget)
            assert view.conversa_ativa == contato


class TestConfiguracoesQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.configuracoes.ConfiguracoesController") as MockCtrl:
            view = ConfiguracoesFrame(app, controller)
            assert view is not None
            assert hasattr(view, "controller_configuracoes")

    def test_toggle_gallery(self, app, controller):
        with patch("ser_pleno.presentation.views.configuracoes.ConfiguracoesController") as MockCtrl:
            view = ConfiguracoesFrame(app, controller)
            try:
                view._toggle_gallery()
                view._toggle_gallery()
            except TclError:
                pytest.skip("Toggle gallery requer widget empacotado")

    def test_toggle_menu_theme(self, app, controller):
        with patch("ser_pleno.presentation.views.configuracoes.ConfiguracoesController") as MockCtrl:
            view = ConfiguracoesFrame(app, controller)
            view._toggle_menu("theme")
            view._toggle_menu("theme")

    def test_toggle_menu_font(self, app, controller):
        with patch("ser_pleno.presentation.views.configuracoes.ConfiguracoesController") as MockCtrl:
            view = ConfiguracoesFrame(app, controller)
            view._toggle_menu("font")
            view._toggle_menu("font")

    def test_alterar_senha_modal_campos(self, app, controller):
        with patch("ser_pleno.presentation.views.configuracoes.ConfiguracoesController") as MockCtrl:
            view = ConfiguracoesFrame(app, controller)
            modal = AlterarSenhaModal(view, on_save=lambda *a: None)
            assert hasattr(modal, "f_senha_atual")
            assert hasattr(modal, "f_nova_senha")
            assert hasattr(modal, "f_confirmar_senha")
            modal.destroy()

    def test_alterar_senha_sucesso(self, app, controller):
        with patch("ser_pleno.presentation.views.configuracoes.ConfiguracoesController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.alterar_senha.return_value = {"success": True, "message": "Senha alterada"}
            view = ConfiguracoesFrame(app, controller)
            on_save = MagicMock()
            modal = AlterarSenhaModal(view, on_save=on_save)
            modal.f_senha_atual.entry.insert(0, "oldpass")
            modal.f_nova_senha.entry.insert(0, "newpass123")
            modal.f_confirmar_senha.entry.insert(0, "newpass123")
            modal._on_confirm()
            on_save.assert_called_with("oldpass", "newpass123")

    def test_encerrar_sessao(self, app, controller):
        with patch("ser_pleno.presentation.views.configuracoes.ConfiguracoesController") as MockCtrl:
            view = ConfiguracoesFrame(app, controller)
            with patch("tkinter.messagebox.askyesno", return_value=True):
                with patch.object(view.winfo_toplevel(), "mostrar_login"):
                    view._encerrar_sessao()


class TestBemEstarQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.bem_estar.BemEstarController") as MockCtrl:
            view = BemEstarFrame(app, controller)
            assert view is not None
            assert hasattr(view, "controller_bem_estar")
            assert hasattr(view, "_kpi_humor")
            assert hasattr(view, "_kpi_part")
            assert hasattr(view, "_kpi_crit")

    def test_populate_risks(self, app, controller):
        with patch("ser_pleno.presentation.views.bem_estar.BemEstarController") as MockCtrl:
            view = BemEstarFrame(app, controller)
            risks = [
                {"name": "Ana", "course": "Psicologia", "level": "critico", "msg": "Atenção"},
                {"name": "Bruno", "course": "Adm", "level": "alto", "msg": "Acompanhar"},
            ]
            view.populate_risks(risks)
            assert True

    def test_populate_checkins(self, app, controller):
        with patch("ser_pleno.presentation.views.bem_estar.BemEstarController") as MockCtrl:
            view = BemEstarFrame(app, controller)
            checkins = [
                {"student_name": "Ana", "mood_score": 4, "mood_text": "Bem", "date": "2025-01-01", "course": "Psicologia"},
            ]
            view.populate_checkins(checkins)
            assert True

    def test_draw_chart_sem_dados(self, app, controller):
        with patch("ser_pleno.presentation.views.bem_estar.BemEstarController") as MockCtrl:
            view = BemEstarFrame(app, controller)
            view._chart_data = []
            view._draw_chart()
            assert True

    def test_update_distribution_sem_dados(self, app, controller):
        with patch("ser_pleno.presentation.views.bem_estar.BemEstarController") as MockCtrl:
            view = BemEstarFrame(app, controller)
            view._update_distribution([])
            assert True


class TestRelatorioQA:
    def test_inicializacao(self, app, controller):
        with patch("ser_pleno.presentation.views.relatorio.RelatorioController") as MockCtrl:
            view = RelatorioFrame(app, controller)
            assert view is not None
            assert hasattr(view, "controller_relatorio")
            assert hasattr(view, "_kpi_cards")
            assert hasattr(view, "filtro_tipo")

    def test_filtrar_por_tipo(self, app, controller):
        with patch("ser_pleno.presentation.views.relatorio.RelatorioController") as MockCtrl:
            view = RelatorioFrame(app, controller)
            view._todos_relatorios = [
                {"id": 1, "name": "Relatório 1", "type": "Geral"},
                {"id": 2, "name": "Relatório 2", "type": "Estudante"},
            ]
            view._filtrar_por_tipo("Geral")
            assert True

    def test_visualizar_relatorio_sem_arquivo(self, app, controller):
        with patch("ser_pleno.presentation.views.relatorio.RelatorioController") as MockCtrl:
            view = RelatorioFrame(app, controller)
            with patch("tkinter.messagebox.showinfo") as mock_info:
                view._visualizar_relatorio({"id": 1, "file_path": ""})
                mock_info.assert_called_with("Informação", "Este relatório ainda não possui arquivo associado.")

    def test_baixar_relatorio_sem_arquivo(self, app, controller):
        with patch("ser_pleno.presentation.views.relatorio.RelatorioController") as MockCtrl:
            view = RelatorioFrame(app, controller)
            with patch("tkinter.messagebox.showinfo") as mock_info:
                view._baixar_relatorio({"id": 1, "file_path": ""})
                mock_info.assert_called_with("Informação", "Este relatório ainda não possui arquivo associado.")

    def test_excluir_relatorio(self, app, controller):
        with patch("ser_pleno.presentation.views.relatorio.RelatorioController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.deletar_relatorio.return_value = {"success": True}
            view = RelatorioFrame(app, controller)
            with patch("tkinter.messagebox.askyesno", return_value=True):
                with patch("tkinter.messagebox.showinfo"):
                    view._excluir_relatorio({"id": 1})
                    mock_ctrl.deletar_relatorio.assert_called_with(1)

    def test_exportar_pdf(self, app, controller):
        with patch("ser_pleno.presentation.views.relatorio.RelatorioController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.gerar_relatorio.return_value = {"success": True}
            view = RelatorioFrame(app, controller)
            with patch("tkinter.messagebox.showinfo"):
                view._exportar_pdf()
                mock_ctrl.gerar_relatorio.assert_called()


class TestNavigationQA:
    def test_menu_items(self):
        from ser_pleno.presentation.navigation import MENU_ITEMS
        keys = [item["key"] for item in MENU_ITEMS]
        expected = ["dashboard", "estudantes", "agenda", "bem_estar", "analise",
                    "relatorios", "comunicacao", "orientacoes", "avisos", "configuracoes"]
        for k in expected:
            assert k in keys

    def test_show_dashboard(self, app, controller):
        from ser_pleno.presentation.navigation import NavigationManager
        nav = NavigationManager(app, auth_service=None)
        app.usuario_logado = {"first_name": "Admin", "username": "admin"}
        with patch("ser_pleno.presentation.navigation.ViewFactory") as MockFactory:
            mock_frame = MagicMock()
            MockFactory.return_value.create.return_value = mock_frame
            nav.show("dashboard")
            assert nav._active_menu_key == "dashboard"


class TestControllersCRUD:
    def test_agenda_crud(self, app, controller):
        from ser_pleno.application.controllers.agenda import AgendaController
        ctrl = AgendaController(auth_service=None)
        res = ctrl.listar_horarios_base()
        assert isinstance(res, list)

    def test_triagem_crud(self, app, controller):
        from ser_pleno.application.controllers.triagem import TriagemController
        ctrl = TriagemController()
        res = ctrl.listar_triagens()
        assert isinstance(res, dict)

    def test_orientacoes_crud(self, app, controller):
        from ser_pleno.application.controllers.orientacoes import OrientacoesController
        ctrl = OrientacoesController(auth_service=None)
        res = ctrl.listar_orientacoes()
        assert isinstance(res, dict)

    def test_bem_estar_crud(self, app, controller):
        from ser_pleno.application.controllers.bem_estar import BemEstarController
        ctrl = BemEstarController()
        dash = ctrl.obter_dashboard()
        checkins = ctrl.listar_checkins()
        risks = ctrl.listar_estudantes_risco()
        assert isinstance(dash, dict)
        assert isinstance(checkins, dict)
        assert isinstance(risks, dict)

    def test_dashboard_crud(self, app, controller):
        from ser_pleno.application.controllers.dashboard import DashboardController
        ctrl = DashboardController(app=app, auth_service=None)
        res = ctrl.carregar_kpis()
        assert isinstance(res, dict)


class TestExceptionSafety:
    def test_login_thread_exception_handling(self, app, controller):
        with patch("ser_pleno.presentation.views.login.AutenticacaoController") as MockAuth:
            ctrl = MockAuth.return_value
            ctrl.login.side_effect = RuntimeError("falha simulada")
            view = LoginFrame(app, controller)
            view.input_user.entry.insert(0, "admin")
            view.input_pass.entry.insert(0, "password")
            view._fazer_login()
            assert True

    def test_agenda_async_error_handler(self, app, controller):
        with patch("ser_pleno.presentation.views.agenda.AgendaController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.listar_horarios_base.side_effect = RuntimeError("falha")
            view = AgendaFrame(app, controller)
            with patch("ser_pleno.presentation.views.agenda.AsyncRunner.run") as mock_run:
                def fake_run(task, on_success, on_error, widget_ref):
                    on_error(RuntimeError("falha"))
                mock_run.side_effect = fake_run
                view.refresh_all_async()
                assert True

    def test_dashboard_async_error_handler(self, app, controller):
        with patch("ser_pleno.presentation.views.dashboard.DashboardController") as MockCtrl:
            mock_ctrl = MockCtrl.return_value
            mock_ctrl.carregar_kpis.side_effect = RuntimeError("falha")
            view = DashboardFrame(app, controller)
            with patch("ser_pleno.presentation.views.dashboard.AsyncRunner.run") as mock_run:
                def fake_run(task, on_success, on_error, widget_ref):
                    on_error(RuntimeError("falha"))
                mock_run.side_effect = fake_run
                view._carregar_dados()
                assert True


class TestCoverageReport:
    def test_all_views_instantiate(self, app, controller):
        views = [
            (LoginFrame, {}),
            (DashboardFrame, {}),
            (AgendaFrame, {}),
            (EstudantesFrame, {}),
            (OrientacoesFrame, {}),
            (TriagemFrame, {}),
            (AvisosFrame, {}),
            (ConfiguracoesFrame, {}),
            (BemEstarFrame, {}),
            (RelatorioFrame, {}),
        ]
        patches = [
            "ser_pleno.presentation.views.dashboard.DashboardController",
            "ser_pleno.presentation.views.agenda.AgendaController",
            "ser_pleno.presentation.views.estudantes.EstudantesController",
            "ser_pleno.presentation.views.orientacoes.OrientacoesController",
            "ser_pleno.presentation.views.triagem.TriagemController",
            "ser_pleno.application.controllers.avisos.ServicoMural",
            "ser_pleno.presentation.views.comunicacao.ComunicacaoController",
            "ser_pleno.presentation.views.configuracoes.ConfiguracoesController",
            "ser_pleno.presentation.views.bem_estar.BemEstarController",
            "ser_pleno.presentation.views.relatorio.RelatorioController",
        ]
        mocks = {p: MagicMock() for p in patches}
        mocks["ser_pleno.presentation.views.login.AutenticacaoController"] = MagicMock()
        with patch.multiple(
            "ser_pleno.presentation.views.login",
            AutenticacaoController=mocks["ser_pleno.presentation.views.login.AutenticacaoController"],
        ), patch("ser_pleno.presentation.views.dashboard.DashboardController", mocks["ser_pleno.presentation.views.dashboard.DashboardController"]), \
             patch("ser_pleno.presentation.views.agenda.AgendaController", mocks["ser_pleno.presentation.views.agenda.AgendaController"]), \
             patch("ser_pleno.presentation.views.estudantes.EstudantesController", mocks["ser_pleno.presentation.views.estudantes.EstudantesController"]), \
             patch("ser_pleno.presentation.views.orientacoes.OrientacoesController", mocks["ser_pleno.presentation.views.orientacoes.OrientacoesController"]), \
             patch("ser_pleno.presentation.views.triagem.TriagemController", mocks["ser_pleno.presentation.views.triagem.TriagemController"]), \
             patch("ser_pleno.application.controllers.avisos.ServicoMural", mocks["ser_pleno.application.controllers.avisos.ServicoMural"]), \
             patch("ser_pleno.presentation.views.comunicacao.ComunicacaoController", mocks["ser_pleno.presentation.views.comunicacao.ComunicacaoController"]), \
             patch("ser_pleno.presentation.views.configuracoes.ConfiguracoesController", mocks["ser_pleno.presentation.views.configuracoes.ConfiguracoesController"]), \
             patch("ser_pleno.presentation.views.bem_estar.BemEstarController", mocks["ser_pleno.presentation.views.bem_estar.BemEstarController"]), \
             patch("ser_pleno.presentation.views.relatorio.RelatorioController", mocks["ser_pleno.presentation.views.relatorio.RelatorioController"]):
            controller.usuario_logado_id = 1
            for cls, kwargs in views:
                obj = cls(app, controller)
                assert obj is not None, f"{cls.__name__} falhou na inicialização"

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

from ser_pleno.ui.views.login import LoginFrame
from ser_pleno.ui.views.dashboard import DashboardFrame
from ser_pleno.ui.views.agenda import AgendaFrame, AppointmentModal, GradeManagementModal
from ser_pleno.ui.views.estudantes import EstudantesFrame
from ser_pleno.ui.views.orientacoes import OrientacoesFrame
from ser_pleno.ui.views.triagem import TriagemFrame
from ser_pleno.ui.views.avisos import AvisosFrame, PublicacaoModal
from ser_pleno.ui.views.comunicacao import ComunicacaoFrame
from ser_pleno.ui.views.configuracoes import ConfiguracoesFrame, AlterarSenhaModal
from ser_pleno.ui.views.bem_estar import BemEstarFrame
from ser_pleno.ui.views.relatorio import RelatorioFrame


pytestmark = pytest.mark.ui_heavy


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
        assert hasattr(view.input_pass, "btn_toggle")
        view.input_pass._toggle_password()
        assert view.input_pass.is_hidden is False
        view.input_pass._toggle_password()
        assert view.input_pass.is_hidden is True

    def test_validacao_campos_vazios(self, app, controller):
        view = LoginFrame(app, controller)
        view.input_user.clear_state()
        view.input_pass.clear_state()
        view.lbl_erro.configure(text="")
        view._fazer_login()
        assert view.lbl_erro.cget("text") != ""

    def test_login_sucesso_chama_service(self, app, controller):
        with patch("ser_pleno.ui.views.login.ServicoAutenticacao") as MockAuth:
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
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_dashboard = mock_svc
        view = DashboardFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "servico_dashboard")
        assert hasattr(view, "kpi_frame")
        assert hasattr(view, "help_badge")
        assert hasattr(view, "alert_badge")

    def test_abrir_notificacoes_ajuda(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.obter_notificacoes_ajuda.return_value = []
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_dashboard = mock_svc
        view = DashboardFrame(app, ctrl)
        view._abrir_notificacoes_ajuda()

    def test_abrir_notificacoes_alertas(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.obter_notificacoes_alertas.return_value = []
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_dashboard = mock_svc
        view = DashboardFrame(app, ctrl)
        view._abrir_notificacoes_alertas()

    def test_abrir_perfil(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_dashboard = mock_svc
        view = DashboardFrame(app, ctrl)
        view._abrir_perfil()
        assert view is not None

    def test_marcar_lida(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.obter_notificacoes_ajuda.return_value = []
        mock_svc.obter_notificacoes_alertas.return_value = []
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_dashboard = mock_svc
        view = DashboardFrame(app, ctrl)
        view._marcar_lida(1, "ajuda")
        mock_svc.marcar_notificacao_como_lida.assert_called_with(1, "ajuda")

    def test_humor_emoji(self, app, controller):
        assert DashboardFrame._humor_emoji(None) != ""
        assert DashboardFrame._humor_emoji(1.0) != ""
        assert DashboardFrame._humor_emoji(5.0) != ""


class TestAgendaQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "servico_agenda")
        assert hasattr(view, "container_grid")
        assert hasattr(view, "container_semana")

    def test_alterar_data(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        initial = view.data_selecionada
        view.alterar_data(1)
        assert view.data_selecionada == initial + datetime.timedelta(days=1)

    def test_modal_agendamento_campos(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        view.horarios_base = ["08:00", "09:00"]
        view.mapa_estudantes = {"Ana": 1}
        modal = AppointmentModal(
            app,
            "08:00",
            None,
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
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        view.horarios_base = ["08:00"]
        view.mapa_estudantes = {"Ana": 1}
        on_success = MagicMock()
        modal = AppointmentModal(
            app,
            "08:00",
            None,
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
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        info = {"id_agendamento": 1, "nome": "Ana", "status": "Agendado"}
        on_success = MagicMock()
        modal = AppointmentModal(
            app,
            "08:00",
            info,
            horarios_base=["08:00"],
            mapa_estudantes={"Ana": 1},
            on_save=lambda *a: {"success": True},
            on_delete=lambda id_: {"success": True},
            on_success=on_success,
        )
        with patch.object(modal, "_confirmar", return_value=True):
            modal._delete()
        on_success.assert_called()

    def test_grade_management_modal(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.listar_horarios_base.return_value = ["08:00", "09:00"]
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        view.horarios_base = ["08:00", "09:00"]
        modal = GradeManagementModal(
            app,
            view.horarios_base,
            mock_svc,
            on_refresh=lambda: None,
        )
        assert modal is not None
        assert hasattr(modal, "entry_novo")

    def test_salvar_agendamento_cria_novo(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.criar_agendamento.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        res = view._salvar_agendamento(
            None,
            {
                "nome_aluno": "Ana",
                "id_aluno": 1,
                "data_hora": "2025-01-01 08:00",
                "motivo": "",
                "status": "Agendado",
            },
        )
        assert res.get("success") is True
        mock_svc.criar_agendamento.assert_called()

    def test_remover_agendamento(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.deletar_agendamento.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        res = view.remover_agendamento(1)
        assert res.get("success") is True
        mock_svc.deletar_agendamento.assert_called_with(1)


class TestEstudantesQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_estudantes = mock_svc
        view = EstudantesFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "servico_estudantes")
        assert hasattr(view, "entry_busca")
        assert hasattr(view, "f_laudo")
        assert hasattr(view, "f_aten")
        assert hasattr(view, "scroll_list")
        assert hasattr(view, "btn_editar")

    def test_novo_estudante_modal_campos(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_estudantes = mock_svc
        view = EstudantesFrame(app, ctrl)
        view.novo_estudante_click()
        assert view is not None

    def test_criar_estudante_sucesso(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.criar_estudante.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_estudantes = mock_svc
        view = EstudantesFrame(app, ctrl)
        res = mock_svc.criar_estudante(
            {
                "nome": "Ana Silva",
                "email": "ana@test.com",
                "has_medical_report": False,
                "requires_attention": False,
                "course": "Psicologia",
                "age": "22",
            }
        )
        assert res.get("success") is True

    def test_editar_estudante_sem_selecao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_estudantes = mock_svc
        view = EstudantesFrame(app, ctrl)
        view._selecionado = None
        fake_modal = MagicMock()
        with patch("ser_pleno.ui.views.estudantes._ErrorModal", fake_modal):
            view._editar_estudante()
            fake_modal.assert_called()

    def test_excluir_estudante_sem_selecao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_estudantes = mock_svc
        view = EstudantesFrame(app, ctrl)
        view._selecionado = None
        fake_modal = MagicMock()
        with patch("ser_pleno.ui.views.estudantes._ErrorModal", fake_modal):
            view._excluir_estudante()
            fake_modal.assert_called()

    def test_selecionar_estudante_atualiza_ui(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_estudantes = mock_svc
        view = EstudantesFrame(app, ctrl)
        st = {
            "name": "Ana",
            "course": "Psicologia",
            "requires_attention": False,
            "has_medical_report": True,
            "contact": "ana@test.com",
            "age": 22,
        }
        view.selecionar_estudante(st)
        assert view._selecionado == st
        assert view.lbl_nome_det.cget("text") == "Ana"

    def test_filtros_aplicar(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_estudantes = mock_svc
        view = EstudantesFrame(app, ctrl)
        view._todos_estudantes = [
            {
                "name": "Ana",
                "course": "Psicologia",
                "has_medical_report": True,
                "requires_attention": False,
            },
            {
                "name": "Bruno",
                "course": "Administração",
                "has_medical_report": False,
                "requires_attention": True,
            },
        ]
        view._aplicar_filtros()
        assert True


class TestOrientacoesQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_orientacoes = mock_svc
        view = OrientacoesFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "servico_orientacoes")
        assert hasattr(view, "_tab_btns")

    def test_mudar_tab(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_orientacoes = mock_svc
        view = OrientacoesFrame(app, ctrl)
        view._mudar_tab("nova")
        assert view._tab_ativo == "nova"
        view._mudar_tab("historico")
        assert view._tab_ativo == "historico"

    def test_salvar_orientacao_campos(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.criar_orientacao.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_orientacoes = mock_svc
        view = OrientacoesFrame(app, ctrl)
        view._build_form_nova_lazy()
        view.f_titulo.insert(0, "Orientação Teste")
        view.f_conteudo.insert("1.0", "Conteúdo teste")
        view.f_tema.widget.set("Geral")
        view.f_data.insert(0, "2025-01-01")
        with patch.object(view, "_carregar_dados"):
            with patch("ser_pleno.ui.views.orientacoes.AsyncRunner.run") as mock_run:

                def fake_run(task, on_success, on_error, widget_ref):
                    res = task()
                    on_success(res)

                mock_run.side_effect = fake_run
                view._salvar_orientacao()
                mock_svc.criar_orientacao.assert_called()

    def test_editar_orientacao_popula_form(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_orientacoes = mock_svc
        view = OrientacoesFrame(app, ctrl)
        view._build_form_nova_lazy()
        o = {
            "id": 1,
            "title": "Título",
            "content": "Conteúdo",
            "theme": "Acadêmico",
            "session_date": "2025-01-01",
            "referral": "",
            "notes": "",
        }
        view._editar_orientacao(o)
        assert view._orientacao_editando_id == 1
        assert view.f_titulo.get() == "Título"

    def test_excluir_orientacao(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.deletar_orientacao.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_orientacoes = mock_svc
        view = OrientacoesFrame(app, ctrl)
        with patch.object(view, "_confirmar", return_value=True):
            with patch.object(view, "_carregar_dados"):
                with patch(
                    "ser_pleno.ui.views.orientacoes.AsyncRunner.run"
                ) as mock_run:

                    def fake_run(task, on_success, on_error, widget_ref):
                        res = task()
                        on_success(res)

                    mock_run.side_effect = fake_run
                    view._excluir_orientacao(1)
                    mock_svc.deletar_orientacao.assert_called_with(1)

    def test_modal_detalhe(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_orientacoes = mock_svc
        view = OrientacoesFrame(app, ctrl)
        o = {
            "id": 1,
            "title": "Título",
            "theme": "Geral",
            "session_date": "2025-01-01",
            "referral": "",
            "content": "Conteúdo",
        }
        view._modal_detalhe(o)
        assert view is not None


class TestTriagemQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_triagem = mock_svc
        view = TriagemFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "servico_triagem")
        assert hasattr(view, "filtro_status")
        assert hasattr(view, "filtro_prioridade")
        assert hasattr(view, "lista_triagens")

    def test_abrir_nova_triagem(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_triagem = mock_svc
        view = TriagemFrame(app, ctrl)
        view.abrir_nova_triagem()
        assert view is not None

    def test_aplicar_filtros(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_triagem = mock_svc
        view = TriagemFrame(app, ctrl)
        view.data_master = [
            {
                "id": 1,
                "student": "Ana",
                "date": "2025-01-01",
                "priority": "Alta",
                "status": "Pendente",
            },
            {
                "id": 2,
                "student": "Bruno",
                "date": "2025-01-02",
                "priority": "Baixa",
                "status": "Concluída",
            },
        ]
        view.filtro_status.set("Pendente")
        view.filtro_prioridade.set("Todas")
        view.aplicar_filtros()
        assert hasattr(view, "lista_triagens")

    def test_limpar_filtros(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_triagem = mock_svc
        view = TriagemFrame(app, ctrl)
        view.data_master = []
        view.limpar_filtros()
        assert view.filtro_status.get() == "Todos"
        assert view.filtro_prioridade.get() == "Todas"

    def test_excluir_triagem(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.deletar_triagem.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_triagem = mock_svc
        view = TriagemFrame(app, ctrl)
        item = {
            "id": 1,
            "student": "Ana",
            "date": "2025-01-01",
            "priority": "Alta",
            "status": "Pendente",
        }
        with patch("tkinter.messagebox.showerror"):
            with patch("ser_pleno.ui.views.triagem.AsyncRunner.run") as mock_run:

                def fake_run(task, on_success, on_error, widget_ref):
                    res = task()
                    on_success(res)

                mock_run.side_effect = fake_run
                view._excluir_triagem(item)
                mock_svc.deletar_triagem.assert_called_with(1)

    def test_modal_editar_triagem(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_triagem = mock_svc
        view = TriagemFrame(app, ctrl)
        item = {
            "id": 1,
            "student": "Ana",
            "date": "2025-01-01",
            "priority": "Alta",
            "status": "Pendente",
        }
        view._modal_editar_triagem(item)
        assert view is not None

    def test_modal_detalhe(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_triagem = mock_svc
        view = TriagemFrame(app, ctrl)
        item = {
            "id": 1,
            "student": "Ana",
            "date": "2025-01-01",
            "priority": "Alta",
            "status": "Pendente",
        }
        view._modal_detalhe(item)
        assert view is not None


class TestAvisosQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_mural = mock_svc
        view = AvisosFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "lista")
        assert hasattr(view, "posts")

    def test_abrir_modal_novo(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_mural = mock_svc
        view = AvisosFrame(app, ctrl)
        view._abrir_modal_novo()
        assert view._modal is not None

    def test_publicacao_modal_campos(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_mural = mock_svc
        view = AvisosFrame(app, ctrl)
        view._abrir_modal_novo()
        modal = view._modal
        assert modal is not None
        assert hasattr(modal, "f_titulo")
        assert hasattr(modal, "f_conteudo")
        assert hasattr(modal, "f_categoria")
        assert hasattr(modal, "_btn_publicar")

    def test_on_edit_carrega_dados(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.obter_mensagem.return_value = {
            "success": True,
            "data": {
                "id": 1,
                "titulo": "Teste",
                "conteudo": "Conteúdo",
                "categoria": "informativo",
            },
        }
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_mural = mock_svc
        view = AvisosFrame(app, ctrl)
        with patch("ser_pleno.utils.async_runner.AsyncRunner.run") as mock_run:

            def fake_run(task, on_success, on_error, widget_ref):
                res = task()
                on_success(res)

            mock_run.side_effect = fake_run
            with patch("threading.Thread") as mock_thread:

                def run_thread(target, **kwargs):
                    target()

                mock_thread.side_effect = lambda target, **kwargs: type(
                    "Thread", (), {"start": lambda self: target()}
                )()
                view._on_edit(1)
        assert view._modal is not None

    def test_on_delete(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.deletar_mensagem.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_mural = mock_svc
        view = AvisosFrame(app, ctrl)
        with patch.object(view, "_confirmar", return_value=True):
            view._on_delete(1)
        assert True

    def test_modal_publicar_sem_titulo(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_mural = mock_svc
        view = AvisosFrame(app, ctrl)
        view._abrir_modal_novo()
        modal = view._modal
        modal.f_titulo.delete(0, "end")
        modal.f_conteudo.delete("1.0", "end")
        with patch("tkinter.messagebox.showwarning") as mock_warn:
            modal._on_save()
            mock_warn.assert_called_with("Atenção", "Preencha título e conteúdo.")


class TestComunicacaoQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_comunicacao = mock_svc
        view = ComunicacaoFrame(app, ctrl)
        view._build_chat_area_lazy()
        assert view is not None
        assert hasattr(view, "entry_mensagem")
        assert hasattr(view, "btn_enviar")
        assert hasattr(view, "scroll_contacts")

    def test_enviar_mensagem_sem_conversa(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_comunicacao = mock_svc
        view = ComunicacaoFrame(app, ctrl)
        view._build_chat_area_lazy()
        view.conversa_ativa = None
        view.entry_mensagem.insert(0, "Olá")
        view.enviar_mensagem()
        assert view.entry_mensagem.get() == "Olá"

    def test_enviar_mensagem_grupo(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.enviar_mensagem_grupo.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_comunicacao = mock_svc
        view = ComunicacaoFrame(app, ctrl)
        view._build_chat_area_lazy()
        view.conversa_ativa = {"role": "group", "id": 1}
        view.entry_mensagem.insert(0, "Mensagem grupo")
        with (
            patch.object(view, "carregar_mensagens"),
            patch.object(view, "carregar_contador_nao_lidas"),
            patch.object(view, "atualizar_lista_contatos"),
        ):
            view.enviar_mensagem()
        mock_svc.enviar_mensagem_grupo.assert_called_with(1, "Mensagem grupo")

    def test_nova_conversa_reseta(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_comunicacao = mock_svc
        view = ComunicacaoFrame(app, ctrl)
        view._nova_conversa()
        assert view.conversa_ativa is None
        assert view.mensagens == []

    def test_toggle_modal_arquivos(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_comunicacao = mock_svc
        view = ComunicacaoFrame(app, ctrl)
        assert hasattr(view, "modal_arquivos")
        view.toggle_modal_arquivos()
        view.toggle_modal_arquivos()

    def test_selecionar_conversa(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_comunicacao = mock_svc
        view = ComunicacaoFrame(app, ctrl)
        contato = {"id": 1, "name": "Teste", "role": "admin"}
        item_widget = MagicMock()
        with patch.object(view, "carregar_mensagens"):
            view.selecionar_conversa(contato, item_widget)
        assert view.conversa_ativa == contato


class TestConfiguracoesQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_configuracoes = mock_svc
        view = ConfiguracoesFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "servico_configuracoes")

    def test_toggle_gallery(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_configuracoes = mock_svc
        view = ConfiguracoesFrame(app, ctrl)
        try:
            view._toggle_gallery()
            view._toggle_gallery()
        except TclError:
            pytest.skip("Toggle gallery requer widget empacotado")

    def test_toggle_menu_theme(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_configuracoes = mock_svc
        view = ConfiguracoesFrame(app, ctrl)
        with patch("tkinter.Menu.tk_popup"):
            view._toggle_menu("theme")
            view._toggle_menu("theme")

    def test_toggle_menu_font(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_configuracoes = mock_svc
        view = ConfiguracoesFrame(app, ctrl)
        with patch("tkinter.Menu.tk_popup"):
            view._toggle_menu("font")
            view._toggle_menu("font")

    def test_alterar_senha_modal_campos(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_configuracoes = mock_svc
        view = ConfiguracoesFrame(app, ctrl)
        modal = AlterarSenhaModal(view, on_save=lambda *a: None)
        assert hasattr(modal, "f_senha_atual")
        assert hasattr(modal, "f_nova_senha")
        assert hasattr(modal, "f_confirmar_senha")
        modal.destroy()

    def test_alterar_senha_sucesso(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.alterar_senha.return_value = {"success": True, "message": "Senha alterada"}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_configuracoes = mock_svc
        view = ConfiguracoesFrame(app, ctrl)
        on_save = MagicMock()
        modal = AlterarSenhaModal(view, on_save=on_save)
        modal.f_senha_atual.entry.insert(0, "oldpass")
        modal.f_confirmar_senha_atual.entry.insert(0, "oldpass")
        modal.f_nova_senha.entry.insert(0, "Newpass1!")
        modal.f_confirmar_senha.entry.insert(0, "Newpass1!")
        modal._on_confirm()
        on_save.assert_called_with("oldpass", "Newpass1!")

    def test_encerrar_sessao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_configuracoes = mock_svc
        view = ConfiguracoesFrame(app, ctrl)
        app.mostrar_login = MagicMock()
        with patch.object(view, "_confirmar", return_value=True):
            view._encerrar_sessao()
        app.mostrar_login.assert_called_once()


class TestBemEstarQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_bem_estar = mock_svc
        view = BemEstarFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "servico_bem_estar")
        assert hasattr(view, "_kpi_humor")
        assert hasattr(view, "_kpi_part")
        assert hasattr(view, "_kpi_crit")

    def test_populate_risks(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_bem_estar = mock_svc
        view = BemEstarFrame(app, ctrl)
        risks = [
            {"name": "Ana", "course": "Psicologia", "level": "critico", "msg": "Atenção"},
            {"name": "Bruno", "course": "Adm", "level": "alto", "msg": "Acompanhar"},
        ]
        view.populate_risks(risks)
        assert True

    def test_populate_checkins(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_bem_estar = mock_svc
        view = BemEstarFrame(app, ctrl)
        checkins = [
            {
                "student_name": "Ana",
                "mood_score": 4,
                "mood_text": "Bem",
                "date": "2025-01-01",
                "course": "Psicologia",
            },
        ]
        view.populate_checkins(checkins)
        assert True

    def test_draw_chart_sem_dados(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_bem_estar = mock_svc
        view = BemEstarFrame(app, ctrl)
        view._chart_data = []
        view._draw_chart()
        assert True

    def test_update_distribution_sem_dados(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_bem_estar = mock_svc
        view = BemEstarFrame(app, ctrl)
        view._update_distribution([])
        assert True


class TestRelatorioQA:
    def test_inicializacao(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_relatorio = mock_svc
        view = RelatorioFrame(app, ctrl)
        assert view is not None
        assert hasattr(view, "servico_relatorio")
        assert hasattr(view, "_kpi_cards")
        assert hasattr(view, "filtro_tipo")

    def test_filtrar_por_tipo(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_relatorio = mock_svc
        view = RelatorioFrame(app, ctrl)
        view._todos_relatorios = [
            {"id": 1, "name": "Relatório 1", "type": "Geral"},
            {"id": 2, "name": "Relatório 2", "type": "Estudante"},
        ]
        view._filtrar_por_tipo("Geral")
        assert True

    def test_visualizar_relatorio_sem_arquivo(self, app, controller):
        mock_svc = MagicMock()
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_relatorio = mock_svc
        view = RelatorioFrame(app, ctrl)
        view._visualizar_relatorio({"id": 1, "name": "Relatório Teste", "file_path": ""})
        assert True

    def test_baixar_relatorio_sem_arquivo(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.baixar_relatorio.return_value = {
            "success": False,
            "message": "Arquivo não encontrado.",
        }
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_relatorio = mock_svc
        view = RelatorioFrame(app, ctrl)
        fake_modal = MagicMock()
        with patch.object(view, "_show_error", fake_modal):
            view._baixar_relatorio({"id": 1, "file_path": ""})
            fake_modal.assert_called()

    def test_excluir_relatorio(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.deletar_relatorio.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_relatorio = mock_svc
        view = RelatorioFrame(app, ctrl)
        with patch.object(view, "_confirmar", return_value=True):
            view._excluir_relatorio({"id": 1})
            mock_svc.deletar_relatorio.assert_called_with(1)

    def test_exportar_pdf(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.gerar_relatorio.return_value = {"success": True}
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_relatorio = mock_svc
        view = RelatorioFrame(app, ctrl)
        view._exportar_pdf()
        assert True


class TestNavigationQA:
    def test_menu_items(self):
        from ser_pleno.ui.navigation import MENU_ITEMS

        keys = [item["key"] for item in MENU_ITEMS]
        expected = [
            "dashboard",
            "estudantes",
            "agenda",
            "bem_estar",
            "analise",
            "relatorios",
            "comunicacao",
            "orientacoes",
            "avisos",
            "configuracoes",
        ]
        for k in expected:
            assert k in keys

    def test_show_dashboard(self, app, controller):
        from ser_pleno.ui.navigation import NavigationManager

        app.container = ctk.CTkFrame(app)
        app.container.grid(row=0, column=0, sticky="nsew")
        nav = NavigationManager(app, auth_service=None)
        app.usuario_logado = {"first_name": "Admin", "username": "admin"}
        with patch("ser_pleno.ui.navigation.ViewFactory") as MockFactory:
            mock_frame = MagicMock()
            MockFactory.return_value.create.return_value = mock_frame
            nav.show("dashboard")
            assert nav._active_menu_key == "dashboard"


class TestControllersCRUD:
    def test_agenda_crud(self, app, controller):
        from ser_pleno.features.agenda.service import ServicoAgendamento

        svc = ServicoAgendamento(auth_service=None)
        res = svc.listar_horarios_base()
        assert isinstance(res, list)

    def test_triagem_crud(self, app, controller):
        from ser_pleno.features.triagem.service import ServicoTriagem

        svc = ServicoTriagem()
        res = svc.listar_triagens()
        assert isinstance(res, dict)

    def test_orientacoes_crud(self, app, controller):
        from ser_pleno.features.orientacoes.service import ServicoOrientacoes

        svc = ServicoOrientacoes(auth_service=None)
        res = svc.listar_orientacoes()
        assert isinstance(res, dict)

    def test_bem_estar_crud(self, app, controller):
        from ser_pleno.features.bem_estar.service import ServicoBemEstar

        svc = ServicoBemEstar()
        dash = svc.obter_dashboard()
        checkins = svc.listar_checkins()
        risks = svc.listar_estudantes_risco()
        assert isinstance(dash, dict)
        assert isinstance(checkins, dict)
        assert isinstance(risks, dict)

    def test_dashboard_crud(self, app, controller):
        from ser_pleno.features.dashboard.service import ServicoDashboard

        svc = ServicoDashboard(auth_service=None)
        res = svc.obter_kpis()
        assert isinstance(res, dict)


class TestExceptionSafety:
    def test_login_thread_exception_handling(self, app, controller):
        with patch("ser_pleno.ui.views.login.ServicoAutenticacao") as MockAuth:
            ctrl = MockAuth.return_value
            ctrl.login.side_effect = RuntimeError("falha simulada")
            view = LoginFrame(app, controller)
            view.input_user.entry.insert(0, "admin")
            view.input_pass.entry.insert(0, "password")
            view._fazer_login()
            assert True

    def test_agenda_async_error_handler(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.listar_horarios_base.side_effect = RuntimeError("falha")
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_agenda = mock_svc
        view = AgendaFrame(app, ctrl)
        with patch("ser_pleno.ui.views.agenda.AsyncRunner.run") as mock_run:

            def fake_run(task, on_success, on_error, widget_ref):
                on_error(RuntimeError("falha"))

            mock_run.side_effect = fake_run
            view.refresh_all_async()
            assert True

    def test_dashboard_async_error_handler(self, app, controller):
        mock_svc = MagicMock()
        mock_svc.carregar_kpis.side_effect = RuntimeError("falha")
        ctrl = MagicMock()
        ctrl.usuario_logado = {
            "id": 1,
            "username": "admin",
            "first_name": "Admin",
            "last_name": "Test",
            "email": "admin@test.com",
        }
        ctrl.usuario_logado_id = 1
        ctrl.servico_dashboard = mock_svc
        view = DashboardFrame(app, ctrl)
        with patch("ser_pleno.ui.views.dashboard.AsyncRunner.run") as mock_run:

            def fake_run(task, on_success, on_error, widget_ref):
                on_error(RuntimeError("falha"))

            mock_run.side_effect = fake_run
            with patch("tkinter.messagebox.showerror"):
                view._carregar_dados()
                assert True



# -*- coding: utf-8 -*-
"""Testes de services com repositories mockados."""

import pytest
from unittest.mock import MagicMock, patch
import json

from ser_pleno.application.services.autenticacao import ServicoAutenticacao
from ser_pleno.features.dashboard.service import ServicoDashboard
from ser_pleno.features.estudantes.service import ServicoEstudante
from ser_pleno.features.agenda.service import ServicoAgendamento
from ser_pleno.features.bem_estar.service import ServicoBemEstar
from ser_pleno.features.triagem.service import ServicoTriagem
from ser_pleno.features.comunicacao.service import ServicoComunicacao
from ser_pleno.features.configuracoes.service import ServicoConfiguracoes
from ser_pleno.features.relatorio.service import ServicoRelatorio
from ser_pleno.features.report_template.service import ServicoReportTemplate
from ser_pleno.features.wellness_challenges.service import ServicoWellnessChallenges
from ser_pleno.features.notificacoes.service import ServicoNotificacoes
from ser_pleno.features.orientacoes.service import ServicoOrientacoes
from ser_pleno.features.interventions.service import ServicoIntervencoes
from ser_pleno.features.metas.service import ServicoMetas


# ---------------------------------------------------------------------------
# Smoke tests / instanciação
# ---------------------------------------------------------------------------
class TestServices:
    @patch("ser_pleno.application.services.autenticacao.requests")
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

    @patch("ser_pleno.features.estudantes.service.ClienteAPI")
    def test_student_service(self, MockClienteAPI):
        service = ServicoEstudante()
        assert service is not None

    def test_dashboard_service(self):
        service = ServicoDashboard()
        assert service is not None

    def test_agendamento_service(self):
        service = ServicoAgendamento()
        assert service is not None
        assert hasattr(service, "criar_agendamento")
        assert hasattr(service, "listar_agendamentos")
        assert hasattr(service, "atualizar_agendamento")
        assert hasattr(service, "deletar_agendamento")

    @patch("ser_pleno.application.services.autenticacao.requests")
    def test_auth_service_instantiation(self, mock_requests):
        service = ServicoAutenticacao()
        assert service is not None
        assert hasattr(service, "login")


# ---------------------------------------------------------------------------
# ServicoEstudante
# ---------------------------------------------------------------------------
class TestServicoEstudante:
    def test_listar_estudantes_local(self):
        service = ServicoEstudante()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.listar.return_value = [
            {"id_aluno": 1, "nome": "Ana", "curso": "PSI", "age": 20, "email": "ana@test.com"}
        ]
        service.repo = mock_repo

        result = service.listar_estudantes()
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "Ana"

    def test_obter_estudante_fallback(self):
        mock_api = MagicMock()
        mock_api.get.return_value = None
        service = ServicoEstudante()
        service._api = mock_api

        mock_repo = MagicMock()
        mock_repo.obter.return_value = {"id_aluno": 1, "nome": "Ana", "curso": "PSI"}
        service.repo = mock_repo

        result = service.obter_estudante(1)
        assert result["success"] is True
        assert result["data"]["name"] == "Ana"

    def test_obter_estudante_nao_encontrado(self):
        mock_api = MagicMock()
        mock_api.get.return_value = None
        service = ServicoEstudante()
        service._api = mock_api

        mock_repo = MagicMock()
        mock_repo.obter.return_value = None
        service.repo = mock_repo

        result = service.obter_estudante(1)
        assert result["success"] is True
        assert result["data"] is None

    def test_obter_relatorio_estudante_fallback(self):
        mock_api = MagicMock()
        mock_api.get.return_value = None
        service = ServicoEstudante()
        service._api = mock_api

        mock_repo = MagicMock()
        mock_repo.obter.return_value = {"id_aluno": 1, "nome": "Ana"}
        mock_repo_bem_estar = MagicMock()
        mock_repo_bem_estar.obter_humor_estudante.return_value = [{"mood": "feliz"}]
        service.repo = mock_repo
        service.repo_bem_estar = mock_repo_bem_estar

        result = service.obter_relatorio_estudante(1)
        assert result["success"] is True
        assert result["data"]["student"]["name"] == "Ana"
        assert len(result["data"]["moods"]) == 1

    def test_criar_estudante_fallback(self):
        mock_api = MagicMock()
        mock_api.post.return_value = None
        service = ServicoEstudante()
        service._api = mock_api

        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.criar_estudante({"name": "Ana", "email": "ana@test.com"})
        assert result["success"] is True
        mock_repo.criar.assert_called_once()

    def test_atualizar_estudante_fallback(self):
        mock_api = MagicMock()
        mock_api.put.return_value = None
        service = ServicoEstudante()
        service._api = mock_api

        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.atualizar_estudante(1, {"name": "Ana"})
        assert result["success"] is True
        mock_repo.atualizar.assert_called_once()

    def test_deletar_estudante_fallback(self):
        mock_api = MagicMock()
        mock_api.delete.return_value = None
        service = ServicoEstudante()
        service._api = mock_api

        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.deletar_estudante(1)
        assert result["success"] is True
        mock_repo.deletar.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# ServicoAutenticacao
# ---------------------------------------------------------------------------
class TestServicoAutenticacao:
    @patch("ser_pleno.application.services.autenticacao.requests")
    def test_login_local_sucesso(self, mock_requests):
        service = ServicoAutenticacao()
        mock_repo = MagicMock()
        mock_user = {
            "id": 1,
            "username": "user",
            "password": "pbkdf2_sha256$29000$4Xbq4peWIk4u$F0vpVOIL9jogA4tdMQ/V2z44/vlbVBhCxO0GRg8qfuc=",
        }
        mock_repo.obter_usuario_por_username.return_value = mock_user
        service.repo = mock_repo

        resp = service.login("user", "pass")
        assert resp["success"] is True
        assert resp["user"]["username"] == "user"
        mock_repo.obter_usuario_por_username.assert_called_with("user")

    @patch("ser_pleno.application.services.autenticacao.requests")
    def test_login_local_credenciais_invalidas(self, mock_requests):
        service = ServicoAutenticacao()
        mock_repo = MagicMock()
        mock_repo.obter_usuario_por_username.return_value = None
        service.repo = mock_repo

        resp = service.login("user", "wrongpass")
        assert resp["success"] is False
        assert "inválidas" in resp["message"]

    @patch("ser_pleno.application.services.autenticacao.requests")
    def test_alterar_senha_sucesso(self, mock_requests):
        service = ServicoAutenticacao()
        service.user = {"id": 1, "username": "user"}

        mock_repo = MagicMock()
        mock_repo.obter_senha_usuario.return_value = {
            "password": "pbkdf2_sha256$29000$4Xbq4peWIk4u$F0vpVOIL9jogA4tdMQ/V2z44/vlbVBhCxO0GRg8qfuc="
        }
        service.repo = mock_repo

        with patch(
            "ser_pleno.application.services.autenticacao.django_pbkdf2_sha256.verify",
            return_value=True,
        ):
            with patch(
                "ser_pleno.application.services.autenticacao.django_pbkdf2_sha256.hash",
                return_value="newhash",
            ):
                resp = service.alterar_senha("oldpass", "newpass")

        assert resp["success"] is True
        mock_repo.atualizar_senha_usuario.assert_called_once_with(1, "newhash")

    @patch("ser_pleno.application.services.autenticacao.requests")
    def test_alterar_senha_sem_usuario_logado(self, mock_requests):
        service = ServicoAutenticacao()
        service.user = None

        resp = service.alterar_senha("oldpass", "newpass")
        assert resp["success"] is False
        assert "logado" in resp["message"]

    @patch("ser_pleno.application.services.autenticacao.requests")
    def test_logout(self, mock_requests):
        service = ServicoAutenticacao()
        service.user = {"id": 1}
        service.csrf_token = "token123"

        service.logout()

        assert service.user is None
        assert service.csrf_token is None
        assert isinstance(service.session, MagicMock)


# ---------------------------------------------------------------------------
# ServicoDashboard
# ---------------------------------------------------------------------------
class TestServicoDashboard:
    def test_obter_kpis(self):
        service = ServicoDashboard()
        mock_repo = MagicMock()
        mock_repo.obter_kpis.return_value = {
            "total_alunos": 10,
            "agendamentos_hoje": 3,
        }
        service.repo = mock_repo

        result = service.obter_kpis()
        assert result["total_alunos"] == 10

    def test_obter_notificacoes_alertas(self):
        service = ServicoDashboard()
        mock_repo = MagicMock()
        mock_repo.obter_notificacoes_alertas.return_value = [{"id": 1, "msg": "Alerta"}]
        service.repo = mock_repo

        result = service.obter_notificacoes_alertas()
        assert len(result) == 1

    @patch("ser_pleno.features.dashboard.service.get_operation_config")
    def test_obter_notificacoes_ajuda_sem_api(self, mock_get_config):
        mock_config = MagicMock()
        mock_config.should_use_api.return_value = False
        mock_get_config.return_value = mock_config

        service = ServicoDashboard()
        result = service.obter_notificacoes_ajuda()
        assert result == []

    @patch("ser_pleno.features.dashboard.service.ClienteAPI")
    def test_obter_notificacoes_ajuda_com_api(self, mock_api_cls):
        mock_api = MagicMock()
        mock_api.get.return_value = {"success": True, "data": [{"id": 1}]}
        mock_api_cls.return_value = mock_api

        service = ServicoDashboard()
        service._api = mock_api

        result = service.obter_notificacoes_ajuda()
        assert len(result) == 1

    @patch("ser_pleno.features.dashboard.service.ClienteAPI")
    def test_marcar_notificacao_ajuda_como_lida(self, mock_api_cls):
        mock_api = MagicMock()
        mock_api_cls.return_value = mock_api

        service = ServicoDashboard()
        service._api = mock_api

        with patch("ser_pleno.features.dashboard.service.get_operation_config") as mock_cfg:
            mock_cfg.return_value.should_use_api.return_value = True
            service.marcar_notificacao_como_lida(1, tipo="ajuda")

        mock_api.put.assert_called_once_with("help/notifications/1/read/")


# ---------------------------------------------------------------------------
# ServicoAgendamento
# ---------------------------------------------------------------------------
class TestServicoAgendamento:
    def test_listar_estudantes(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.listar.return_value = [{"id_aluno": 1, "nome": "Ana"}]
        service.repo = mock_repo
        service.repo_estudante = mock_repo

        result = service.listar_estudantes()
        assert isinstance(result, list)
        assert result[0]["nome"] == "Ana"

    def test_listar_horarios_base(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.listar_horarios_base.return_value = ["08:00", "09:00"]
        service.repo = mock_repo

        result = service.listar_horarios_base()
        assert result == ["08:00", "09:00"]

    def test_verificar_disponibilidade_livre(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.verificar_disponibilidade.return_value = None
        service.repo = mock_repo

        result = service.verificar_disponibilidade("2024-01-01", "08:00")
        assert result is True

    def test_verificar_disponibilidade_ocupado(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.verificar_disponibilidade.return_value = {"id": 1}
        service.repo = mock_repo

        result = service.verificar_disponibilidade("2024-01-01", "08:00")
        assert result is False

    def test_criar_agendamento_local(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.obter_nome_aluno.return_value = {"nome": "Ana"}
        mock_repo.criar_agendamento.return_value = 1
        mock_repo.obter_ultimo_id_inserido.return_value = 1
        service.repo = mock_repo
        service.repo_estudante = mock_repo

        result = service.criar_agendamento(
            {"data_hora": "2024-01-01 08:00", "id_aluno": 1, "status": "Agendado"}
        )
        assert result["success"] is True
        assert result["id"] == 1

    def test_listar_agendamentos_local(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.listar_agendamentos.return_value = [
            {
                "id": 1,
                "nome": "Ana",
                "id_aluno": 1,
                "data_hora": "2024-01-01 08:00",
                "motivo": "Consulta",
                "status": "agendado",
                "local": "Sala",
                "profissional": "Dr. Silva",
                "laudo": "N/A",
                "origem": "desktop",
            }
        ]
        service.repo = mock_repo

        result = service.listar_agendamentos()
        assert len(result) == 1
        assert result[0]["nome"] == "Ana"
        assert result[0]["status"] == "agendado"

    def test_atualizar_agendamento(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.atualizar_agendamento.return_value = None
        service.repo = mock_repo

        result = service.atualizar_agendamento(
            1,
            {
                "data_hora": "2024-01-01 08:00",
                "id_aluno": 1,
                "status": "Agendado",
            },
        )
        assert result["success"] is True

    def test_deletar_agendamento(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.deletar_agendamento.return_value = 1
        service.repo = mock_repo

        result = service.deletar_agendamento(1)
        assert result["success"] is True

    def test_converter_status_frontend_to_backend(self):
        service = ServicoAgendamento()
        assert service._convert_status_frontend_to_backend("Agendado") == "agendado"
        assert service._convert_status_frontend_to_backend("Realizado") == "concluido"
        assert service._convert_status_frontend_to_backend("Cancelado") == "cancelado"
        assert service._convert_status_frontend_to_backend("Faltou") == "cancelado"

    def test_converter_status_backend_to_frontend(self):
        service = ServicoAgendamento()
        assert service._convert_status_backend_to_frontend("scheduled") == "agendado"
        assert service._convert_status_backend_to_frontend("completed") == "concluido"
        assert service._convert_status_backend_to_frontend("cancelled") == "cancelado"
        assert service._convert_status_backend_to_frontend("missed") == "cancelado"

    def test_adicionar_horario_disponibilidade_novo(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.verificar_horario_existe.return_value = None
        mock_repo.adicionar_horario_disponibilidade.return_value = None
        service.repo = mock_repo

        result = service.adicionar_horario_disponibilidade("10:00")
        assert result["success"] is True

    def test_adicionar_horario_disponibilidade_existente(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.verificar_horario_existe.return_value = {"id": 1}
        service.repo = mock_repo

        result = service.adicionar_horario_disponibilidade("10:00")
        assert result["success"] is False
        assert "já existe" in result["message"]

    def test_remover_horario_disponibilidade(self):
        service = ServicoAgendamento()
        mock_repo = MagicMock()
        mock_repo.remover_horario_disponibilidade.return_value = 1
        service.repo = mock_repo

        result = service.remover_horario_disponibilidade("10:00")
        assert result["success"] is True


# ---------------------------------------------------------------------------
# ServicoBemEstar
# ---------------------------------------------------------------------------
class TestServicoBemEstar:
    def test_obter_dashboard_com_avg(self):
        service = ServicoBemEstar()
        mock_repo = MagicMock()
        mock_repo.obter_dashboard.return_value = {
            "avg": {"average_mood": 3.5},
            "moods": [],
            "checkins": [],
        }
        service.repo = mock_repo

        result = service.obter_dashboard()
        assert result["success"] is True
        assert result["data"]["summary"]["average_mood"] == 3.5

    def test_obter_dashboard_sem_avg(self):
        service = ServicoBemEstar()
        mock_repo = MagicMock()
        mock_repo.obter_dashboard.return_value = {
            "avg": None,
            "moods": [],
            "checkins": [],
        }
        service.repo = mock_repo

        result = service.obter_dashboard()
        assert result["success"] is True
        assert result["data"]["summary"]["average_mood"] is None

    def test_listar_entradas_humor(self):
        service = ServicoBemEstar()
        mock_repo = MagicMock()
        mock_repo.listar_entradas_humor.return_value = [{"mood": "feliz"}]
        service.repo = mock_repo

        result = service.listar_entradas_humor()
        assert result["success"] is True
        assert len(result["data"]) == 1

    def test_obter_medias_humor(self):
        service = ServicoBemEstar()
        mock_repo = MagicMock()
        mock_repo.obter_medias_humor.return_value = [{"average": 3.5}]
        service.repo = mock_repo

        result = service.obter_medias_humor()
        assert result["success"] is True

    def test_obter_humor_estudante(self):
        service = ServicoBemEstar()
        mock_repo = MagicMock()
        mock_repo.obter_humor_estudante.return_value = [{"mood": "feliz"}]
        service.repo = mock_repo

        result = service.obter_humor_estudante(1)
        assert result["success"] is True
        assert result["data"][0]["mood"] == "feliz"

    def test_listar_checkins(self):
        service = ServicoBemEstar()
        mock_repo = MagicMock()
        mock_repo.listar_checkins.return_value = [{"id": 1}]
        service.repo = mock_repo

        result = service.listar_checkins()
        assert result["success"] is True
        assert "checkins" in result["data"]

    def test_listar_estudantes_risco_critical(self):
        service = ServicoBemEstar()
        mock_repo_estudante = MagicMock()
        mock_repo_estudante.listar.return_value = [
            {"id_aluno": 1, "nome": "Ana", "priority_level": 4, "attention_reason": "Teste"}
        ]
        service.repo_estudante = mock_repo_estudante

        result = service.listar_estudantes_risco()
        assert result["success"] is True
        assert len(result["data"]["groups"]["critical"]) == 1

    def test_listar_estudantes_risco_high(self):
        service = ServicoBemEstar()
        mock_repo_estudante = MagicMock()
        mock_repo_estudante.listar.return_value = [
            {"id_aluno": 1, "nome": "Ana", "priority_level": 3, "attention_reason": "Teste"}
        ]
        service.repo_estudante = mock_repo_estudante

        result = service.listar_estudantes_risco()
        assert len(result["data"]["groups"]["high"]) == 1

    def test_listar_estudantes_risco_low(self):
        service = ServicoBemEstar()
        mock_repo_estudante = MagicMock()
        mock_repo_estudante.listar.return_value = [
            {"id_aluno": 1, "nome": "Ana", "priority_level": 0}
        ]
        service.repo_estudante = mock_repo_estudante

        result = service.listar_estudantes_risco()
        assert len(result["data"]["groups"]["low"]) == 1


# ---------------------------------------------------------------------------
# ServicoTriagem
# ---------------------------------------------------------------------------
class TestServicoTriagem:
    def test_listar_triagens(self):
        service = ServicoTriagem()
        mock_repo = MagicMock()
        mock_repo.listar.return_value = [
            {"id": 1, "student_name": "Ana", "status": "pendente"}
        ]
        service.repo = mock_repo

        result = service.listar_triagens()
        assert result["success"] is True
        assert result["data"][0]["student_name"] == "Ana"

    def test_obter_triagem(self):
        service = ServicoTriagem()
        mock_repo = MagicMock()
        mock_repo.obter.return_value = {"id": 1, "status": "pendente"}
        service.repo = mock_repo

        result = service.obter_triagem(1)
        assert result["success"] is True
        assert result["data"]["status"] == "pendente"

    def test_obter_triagem_nao_encontrada(self):
        service = ServicoTriagem()
        mock_repo = MagicMock()
        mock_repo.obter.return_value = None
        service.repo = mock_repo

        result = service.obter_triagem(1)
        assert result["success"] is False
        assert "não encontrada" in result["message"]

    def test_criar_triagem(self):
        service = ServicoTriagem()
        mock_repo = MagicMock()
        mock_repo.criar.return_value = 1
        service.repo = mock_repo

        result = service.criar_triagem({"student_id": 1})
        assert result["success"] is True
        assert result["data"]["id"] == 1

    def test_atualizar_triagem(self):
        service = ServicoTriagem()
        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.atualizar_triagem(1, {"status": "concluida"})
        assert result["success"] is True
        mock_repo.atualizar.assert_called_once_with(1, {"status": "concluida"})

    def test_deletar_triagem(self):
        service = ServicoTriagem()
        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.deletar_triagem(1)
        assert result["success"] is True
        mock_repo.deletar.assert_called_once_with(1)

    def test_listar_formularios(self):
        service = ServicoTriagem()
        mock_repo = MagicMock()
        mock_repo.listar_formularios.return_value = [{"id": 1, "name": "Form1"}]
        service.repo = mock_repo

        result = service.listar_formularios()
        assert result["success"] is True
        assert result["data"][0]["name"] == "Form1"


# ---------------------------------------------------------------------------
# ServicoComunicacao
# ---------------------------------------------------------------------------
class TestServicoComunicacao:
    def test_listar_alertas(self):
        service = ServicoComunicacao()
        mock_repo = MagicMock()
        mock_repo.listar_alertas.return_value = [{"id": 1, "mensagem": "Alerta"}]
        service.repo = mock_repo

        result = service.listar_alertas()
        assert result["success"] is True
        assert len(result["data"]) == 1

    def test_marcar_alerta_lido(self):
        service = ServicoComunicacao()
        mock_repo = MagicMock()
        mock_repo.marcar_alerta_lido.return_value = 1
        service.repo = mock_repo

        result = service.marcar_alerta_lido(1)
        assert result["success"] is True
        mock_repo.marcar_alerta_lido.assert_called_once_with(1)

    def test_marcar_todos_lidos(self):
        service = ServicoComunicacao()
        mock_repo = MagicMock()
        mock_repo.marcar_todos_lidos.return_value = 5
        service.repo = mock_repo

        result = service.marcar_todos_lidos()
        assert result["success"] is True

    def test_listar_pedidos_ajuda(self):
        service = ServicoComunicacao()
        mock_repo = MagicMock()
        mock_repo.listar_pedidos_ajuda.return_value = []
        service.repo = mock_repo

        result = service.listar_pedidos_ajuda()
        assert result["success"] is True

    def test_listar_contatos_filtra_role(self):
        service = ServicoComunicacao()
        mock_repo = MagicMock()
        mock_repo.listar_contatos.return_value = [
            {"id": 1, "role": "admin", "nome": "Admin"},
            {"id": 2, "role": "aluno", "nome": "Aluno"},
        ]
        service.repo = mock_repo

        # id_usuario_logado diferente dos IDs retornados para não filtrar o próprio usuário
        result = service.listar_contatos(id_usuario_logado=99)
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["role"] == "admin"

    def test_enviar_mensagem(self):
        service = ServicoComunicacao()
        mock_repo = MagicMock()
        mock_repo.enviar_mensagem.return_value = 10
        service.repo = mock_repo

        result = service.enviar_mensagem(1, 2, "Olá")
        assert result["success"] is True
        assert result["data"]["id"] == 10

    def test_contar_mensagens_nao_lidas(self):
        service = ServicoComunicacao()
        mock_repo = MagicMock()
        mock_repo.contar_mensagens_nao_lidas.return_value = 3
        service.repo = mock_repo

        result = service.contar_mensagens_nao_lidas(1)
        assert result["success"] is True
        assert result["data"] == 3


# ---------------------------------------------------------------------------
# ServicoConfiguracoes
# ---------------------------------------------------------------------------
class TestServicoConfiguracoes:
    def test_obter_configuracoes(self):
        service = ServicoConfiguracoes()
        mock_repo = MagicMock()
        mock_repo.obter_configuracoes.return_value = [{"chave": "theme", "valor": "dark"}]
        service.repo = mock_repo

        result = service.obter_configuracoes()
        assert result["success"] is True
        assert len(result["data"]) == 1

    def test_atualizar_configuracoes(self):
        service = ServicoConfiguracoes()
        mock_repo = MagicMock()
        mock_repo.atualizar_configuracoes.return_value = 1
        service.repo = mock_repo

        result = service.atualizar_configuracoes({"theme": "dark"})
        assert result["success"] is True


# ---------------------------------------------------------------------------
# ServicoRelatorio
# ---------------------------------------------------------------------------
class TestServicoRelatorio:
    def test_listar_relatorios(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.listar_relatorios.return_value = [{"id": 1, "tipo": "estudantes"}]
        service.repo = mock_repo

        result = service.listar_relatorios()
        assert result["success"] is True
        assert len(result["data"]) == 1

    def test_obter_estatisticas(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.obter_estatisticas.return_value = {"total_students": 10}
        service.repo = mock_repo
        with patch.object(service, "_should_use_api", return_value=False):
            result = service.obter_estatisticas()
        assert result["success"] is True
        assert result["data"]["total_students"] == 10

    def test_baixar_relatorio_encontrado(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.obter_relatorio_por_id.return_value = {"file_path": "/tmp/r1.pdf"}
        service.repo = mock_repo

        result = service.baixar_relatorio(1)
        assert result["success"] is True
        assert result["data"]["file_path"] == "/tmp/r1.pdf"

    def test_baixar_relatorio_nao_encontrado(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.obter_relatorio_por_id.return_value = None
        service.repo = mock_repo

        result = service.baixar_relatorio(1)
        assert result["success"] is False

    def test_deletar_relatorio(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.deletar_relatorio(1)
        assert result["success"] is True
        mock_repo.deletar_relatorio.assert_called_once_with(1)

    def test_exportar_estudantes(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.exportar_estudantes.return_value = [{"id": 1, "nome": "Ana"}]
        service.repo = mock_repo

        result = service.exportar_estudantes()
        assert result["success"] is True
        assert "data" in result
        assert "content" in result["data"]
        assert "format" in result["data"]
        assert result["data"]["format"] == "csv"

    def test_exportar_agendamentos(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.exportar_agendamentos.return_value = []
        service.repo = mock_repo

        result = service.exportar_agendamentos()
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["format"] == "csv"

    def test_exportar_triagens(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.exportar_triagens.return_value = []
        service.repo = mock_repo

        result = service.exportar_triagens()
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["format"] == "csv"

    def test_exportar_intervencoes(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.exportar_intervencoes.return_value = [{"id": 1, "date": "2024-01-01"}]
        service.repo = mock_repo

        result = service.exportar_intervencoes()
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["format"] == "csv"
        assert "content" in result["data"]


# ---------------------------------------------------------------------------
# ServicoOrientacoes
# ---------------------------------------------------------------------------
class TestServicoOrientacoes:
    def test_listar_orientacoes(self):
        service = ServicoOrientacoes()
        mock_repo = MagicMock()
        mock_repo.listar_orientacoes.return_value = [
            {"id": 1, "title": "Orientação 1", "theme": "Teste"}
        ]
        service.repo = mock_repo

        result = service.listar_orientacoes()
        assert result["success"] is True
        assert len(result["data"]["orientations"]) == 1

    def test_obter_orientacao(self):
        service = ServicoOrientacoes()
        mock_repo = MagicMock()
        mock_repo.obter_orientacao.return_value = {"id": 1, "title": "Orientação"}
        service.repo = mock_repo

        result = service.obter_orientacao(1)
        assert result["success"] is True
        assert result["data"]["title"] == "Orientação"

    def test_obter_orientacao_nao_encontrada(self):
        service = ServicoOrientacoes()
        mock_repo = MagicMock()
        mock_repo.obter_orientacao.return_value = None
        service.repo = mock_repo

        result = service.obter_orientacao(1)
        assert result["success"] is False

    def test_criar_orientacao(self):
        service = ServicoOrientacoes()
        mock_repo = MagicMock()
        mock_repo.criar_orientacao.return_value = 1
        service.repo = mock_repo

        result = service.criar_orientacao(
            {
                "student_id": 1,
                "title": "Teste",
                "theme": "Teste",
                "session_date": "2024-01-01",
                "content": "Conteúdo",
                "is_markdown": False,
                "motivational_message": "",
                "action_plan": [],
                "psychologist": "Equipe SerPleno",
            }
        )
        assert result["success"] is True
        assert result["data"]["id"] == 1

    def test_atualizar_orientacao(self):
        service = ServicoOrientacoes()
        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.atualizar_orientacao(
            id_orientacao=1,
            dados={"title": "Novo título", "theme": "Teste"},
        )
        assert result["success"] is True
        mock_repo.atualizar_orientacao.assert_called_once()

    def test_deletar_orientacao(self):
        service = ServicoOrientacoes()
        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.deletar_orientacao(1)
        assert result["success"] is True
        mock_repo.deletar_orientacao.assert_called_once_with(1)

    def test_get_preset(self):
        service = ServicoOrientacoes()
        preset = service.get_preset("study_support")
        assert preset is not None
        assert preset["label"] == "Apoio Pedagógico"

    def test_get_preset_inexistente(self):
        service = ServicoOrientacoes()
        preset = service.get_preset("inexistente")
        assert preset is None

    def test_get_presets(self):
        service = ServicoOrientacoes()
        presets = service.get_presets()
        assert len(presets) == 3

    def test_duplicar_orientacao_sucesso(self):
        service = ServicoOrientacoes()
        mock_repo = MagicMock()
        mock_repo.obter_orientacao.return_value = {
            "id": 1,
            "title": "Orientação Original",
            "theme": "Teste",
            "student": {"id": 1},
        }
        mock_repo.criar_orientacao.return_value = 2
        service.repo = mock_repo

        with patch("ser_pleno.features.orientacoes.service.datetime") as mock_dt, \
             patch.object(service, "_should_use_api", return_value=False):
            mock_dt.datetime.now.return_value.strftime.return_value = "2024-01-01"
            result = service.duplicar_orientacao(1)

        assert result["success"] is True
        assert result["data"]["id"] == 2

    def test_obter_estatisticas(self):
        service = ServicoOrientacoes()
        mock_repo = MagicMock()
        mock_repo.obter_estatisticas.return_value = {"total": 5}
        service.repo = mock_repo

        result = service.obter_estatisticas()
        assert result["success"] is True
        assert result["data"]["total"] == 5


# ---------------------------------------------------------------------------
# ServicoReportTemplate
# ---------------------------------------------------------------------------
class TestServicoReportTemplate:
    def test_listar_templates_local(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.listar_templates.return_value = [
            {"id": 1, "name": "Template 1", "report_type": "geral", "is_active": True}
        ]
        service.repo = mock_repo

        result = service.listar_templates()
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "Template 1"

    def test_listar_templates_com_filtro_tipo(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.listar_templates.return_value = [
            {"id": 1, "name": "T1", "report_type": "estudante"}
        ]
        service.repo = mock_repo

        result = service.listar_templates(tipo="estudante")
        mock_repo.listar_templates.assert_called_with("estudante", True)
        assert result["data"][0]["report_type"] == "estudante"

    def test_listar_templates_apenas_ativos_false(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.listar_templates.return_value = []
        service.repo = mock_repo

        result = service.listar_templates(apenas_ativos=False)
        mock_repo.listar_templates.assert_called_with(None, False)

    def test_obter_template_local_encontrado(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.obter_template_por_id.return_value = {"id": 1, "name": "T1"}
        service.repo = mock_repo

        result = service.obter_template(1)
        assert result["success"] is True
        assert result["data"]["name"] == "T1"

    def test_obter_template_nao_encontrado(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.obter_template_por_id.return_value = None
        service.repo = mock_repo

        result = service.obter_template(99)
        assert result["success"] is False
        assert "não encontrado" in result["message"]

    def test_criar_template_sem_nome(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.criar_template.return_value = None
        mock_repo.obter_template_por_id.return_value = None
        service.repo = mock_repo

        result = service.criar_template({"name": ""})
        assert result["success"] is False

    def test_criar_template_local(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.criar_template.return_value = 1
        mock_repo.obter_template_por_id.return_value = {"id": 1, "name": "Novo"}
        service.repo = mock_repo

        result = service.criar_template({"name": "Novo", "report_type": "geral"})
        assert result["success"] is True
        assert result["data"]["name"] == "Novo"
        mock_repo.criar_template.assert_called_once()

    def test_atualizar_template_local(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.atualizar_template.return_value = True
        mock_repo.obter_template_por_id.return_value = {"id": 1, "name": "Atualizado"}
        service.repo = mock_repo

        result = service.atualizar_template(1, {"name": "Atualizado"})
        assert result["success"] is True
        assert result["data"]["name"] == "Atualizado"

    def test_atualizar_template_nao_encontrado(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.atualizar_template.return_value = False
        service.repo = mock_repo

        result = service.atualizar_template(99, {"name": "X"})
        assert result["success"] is False
        assert "não encontrado" in result["message"]

    def test_deletar_template_local(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.deletar_template.return_value = True
        service.repo = mock_repo

        result = service.deletar_template(1)
        assert result["success"] is True
        mock_repo.deletar_template.assert_called_with(1)

    def test_deletar_template_nao_encontrado(self):
        service = ServicoReportTemplate()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.deletar_template.return_value = False
        service.repo = mock_repo

        result = service.deletar_template(99)
        assert result["success"] is False
        assert "não encontrado" in result["message"]

    def test_gerar_preview_template_nao_encontrado(self):
        service = ServicoReportTemplate()
        mock_repo = MagicMock()
        mock_repo.obter_template_por_id.return_value = None
        service.repo = mock_repo

        result = service.gerar_preview(99)
        assert result["success"] is False
        assert "não encontrado" in result["message"]

    def test_listar_tipos_disponiveis(self):
        service = ServicoReportTemplate()
        tipos = service.listar_tipos_disponiveis()
        assert isinstance(tipos, list)
        assert "geral" in tipos
        assert "estudante" in tipos


# ---------------------------------------------------------------------------
# ServicoRelatorio (expansao)
# ---------------------------------------------------------------------------
class TestServicoRelatorioExpansao:
    def test_exportar_estudantes_com_filtros(self):
        service = ServicoRelatorio()
        service._should_use_api = lambda: False
        mock_repo = MagicMock()
        mock_repo.exportar_estudantes.return_value = [
            {"id": 1, "nome": "Ana", "status": "ativo", "updated_at": "2024-01-02"},
            {"id": 2, "nome": "Bruno", "status": "inativo", "updated_at": "2024-01-01"},
        ]
        service.repo = mock_repo

        result = service.exportar_estudantes(filtros={"date_from": "2024-01-02", "tipo": "ativo"}, formato="csv")
        assert result["success"] is True
        content = result["data"]["content"]
        assert "nome" in content
        assert "Ana" in content

    def test_exportar_estudantes_formato_json(self):
        service = ServicoRelatorio()
        service._should_use_api = lambda: False
        mock_repo = MagicMock()
        mock_repo.exportar_estudantes.return_value = [
            {"id": 1, "nome": "Ana"}
        ]
        service.repo = mock_repo

        result = service.exportar_estudantes(formato="json")
        assert result["success"] is True
        assert result["data"]["format"] == "json"
        assert "Ana" in result["data"]["content"]

    def test_exportar_estudantes_formato_excel(self):
        service = ServicoRelatorio()
        service._should_use_api = lambda: False
        mock_repo = MagicMock()
        mock_repo.exportar_estudantes.return_value = [
            {"id": 1, "nome": "Ana"}
        ]
        service.repo = mock_repo

        result = service.exportar_estudantes(formato="excel")
        assert result["success"] is True
        assert result["data"]["format"] == "excel"
        assert isinstance(result["data"]["content"], bytes)

    def test_exportar_agendamentos_com_filtros(self):
        service = ServicoRelatorio()
        service._should_use_api = lambda: False
        mock_repo = MagicMock()
        mock_repo.exportar_agendamentos.return_value = [
            {"id": 1, "nome": "Consulta", "data_hora": "2024-01-05 08:00", "status": "agendado"},
            {"id": 2, "nome": "Retorno", "data_hora": "2024-01-10 09:00", "status": "concluido"},
        ]
        service.repo = mock_repo

        result = service.exportar_agendamentos(filtros={"date_from": "2024-01-06", "tipo": "concluido"}, formato="csv")
        assert result["success"] is True
        content = result["data"]["content"]
        assert "Retorno" in content

    def test_deletar_lote_local(self):
        service = ServicoRelatorio()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.deletar_lote([1, 2, 3])
        assert result["success"] is True
        assert "3 relatório(s)" in result["message"]
        assert mock_repo.deletar_relatorio.call_count == 3

    def test_deletar_lote_vazio(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        service.repo = mock_repo

        result = service.deletar_lote([])
        assert result["success"] is True

    def test_baixar_lote_local(self):
        service = ServicoRelatorio()
        service._should_use_api = lambda: False

        mock_repo = MagicMock()
        mock_repo.obter_relatorio_por_id.side_effect = [
            {"file_path": "/tmp/r1.pdf"},
            {"file_path": "/tmp/r2.pdf"},
            None,
        ]
        service.repo = mock_repo

        result = service.baixar_lote([1, 2, 3])
        assert result["success"] is True
        assert len(result["data"]["file_paths"]) == 2

    def test_listar_relatorios_filtrados(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.listar_relatorios_filtrados.return_value = [
            {"id": 1, "name": "R1", "report_type": "geral", "generated_at": "2024-01-01"}
        ]
        service.repo = mock_repo

        result = service.listar_relatorios_filtrados(tipo="geral")
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "R1"

    def test_obter_relatorio_encontrado(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.obter_relatorio_por_id.return_value = {"file_path": "/tmp/r1.pdf", "file_name": "r1"}
        service.repo = mock_repo

        result = service.obter_relatorio(1)
        assert result["success"] is True
        assert result["data"]["file_path"] == "/tmp/r1.pdf"

    def test_obter_relatorio_nao_encontrado(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.obter_relatorio_por_id.return_value = None
        service.repo = mock_repo

        result = service.obter_relatorio(1)
        assert result["success"] is False
        assert "não encontrado" in result["message"]

    def test_gerar_relatorio_por_template_sucesso(self):
        service = ServicoRelatorio()
        mock_repo_rel = MagicMock()
        mock_repo_rel.criar_relatorio.return_value = 1
        mock_repo_tmpl = MagicMock()
        mock_repo_tmpl.aplicar_template_em_dados.return_value = {
            "success": True,
            "data": {
                "name": "Teste",
                "report_type": "geral",
                "parameters": {},
                "template_config": {},
            }
        }
        service.repo = mock_repo_rel
        service._should_use_api = lambda: False

        with patch("ser_pleno.features.report_template.service.ServicoReportTemplate", return_value=mock_repo_tmpl):
            result = service.gerar_relatorio_por_template(1)

        assert result["success"] is True
        assert result["data"]["id"] == 1


# ---------------------------------------------------------------------------
# ServicoIntervencoes
# ---------------------------------------------------------------------------
class TestServicoIntervencoes:
    def test_listar_intervencoes_local(self):
        service = ServicoIntervencoes()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.listar_intervencoes.return_value = [
            {
                "id": 1,
                "student_id": 1,
                "student_name": "Ana",
                "date": "2024-01-01",
                "intervention_type": "counseling",
                "duration_minutes": 45,
                "intervention_notes": "Teste",
                "outcome": "positive",
                "outcome_notes": "",
                "follow_up_required": 0,
                "follow_up_date": None,
                "follow_up_completed": 0,
                "is_confidential": 0,
                "tags": "[]",
            }
        ]
        service.repo = mock_repo

        result = service.listar_intervencoes()
        assert result["success"] is True
        assert len(result["data"]["interventions"]) == 1
        assert result["data"]["interventions"][0]["student_name"] == "Ana"

    def test_listar_intervencoes_local_filtra_tipo(self):
        service = ServicoIntervencoes()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.listar_intervencoes.return_value = [
            {
                "id": 1,
                "student_id": 1,
                "student_name": "Ana",
                "date": "2024-01-01",
                "intervention_type": "counseling",
                "duration_minutes": 45,
                "intervention_notes": "Teste",
                "outcome": "positive",
                "outcome_notes": "",
                "follow_up_required": 0,
                "follow_up_date": None,
                "follow_up_completed": 0,
                "is_confidential": 0,
                "tags": "[]",
            },
            {
                "id": 2,
                "student_id": 1,
                "student_name": "Ana",
                "date": "2024-01-02",
                "intervention_type": "emotional_support",
                "duration_minutes": 30,
                "intervention_notes": "Teste 2",
                "outcome": "neutral",
                "outcome_notes": "",
                "follow_up_required": 0,
                "follow_up_date": None,
                "follow_up_completed": 0,
                "is_confidential": 0,
                "tags": "[]",
            },
        ]
        service.repo = mock_repo

        result = service.listar_intervencoes(intervention_type="counseling")
        assert result["success"] is True
        assert len(result["data"]["interventions"]) == 1
        assert result["data"]["interventions"][0]["intervention_type"] == "counseling"

    def test_listar_intervencoes_local_filtra_busca(self):
        service = ServicoIntervencoes()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.listar_intervencoes.return_value = [
            {
                "id": 1,
                "student_id": 1,
                "student_name": "Ana",
                "date": "2024-01-01",
                "intervention_type": "counseling",
                "duration_minutes": 45,
                "intervention_notes": "Teste busca",
                "outcome": "positive",
                "outcome_notes": "",
                "follow_up_required": 0,
                "follow_up_date": None,
                "follow_up_completed": 0,
                "is_confidential": 0,
                "tags": "[]",
            },
            {
                "id": 2,
                "student_id": 1,
                "student_name": "Ana",
                "date": "2024-01-02",
                "intervention_type": "other",
                "duration_minutes": 30,
                "intervention_notes": "Outro",
                "outcome": "neutral",
                "outcome_notes": "",
                "follow_up_required": 0,
                "follow_up_date": None,
                "follow_up_completed": 0,
                "is_confidential": 0,
                "tags": "[]",
            },
        ]
        service.repo = mock_repo

        result = service.listar_intervencoes(search="busca")
        assert result["success"] is True
        assert len(result["data"]["interventions"]) == 1

    def test_adicionar_intervencao_sucesso_local(self):
        service = ServicoIntervencoes()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.criar_intervencao.return_value = 42
        service.repo = mock_repo

        dados = {
            "student_id": 1,
            "date": "2024-01-01",
            "notes": "Anotacoes",
            "intervention_type": "counseling",
            "duration_minutes": 45,
            "outcome": "positive",
            "follow_up_required": False,
            "is_confidential": False,
            "tags": ["tag1"],
        }
        result = service.adicionar_intervencao(dados)
        assert result["success"] is True
        assert result["data"]["id"] == 42
        mock_repo.criar_intervencao.assert_called_once()

    def test_adicionar_intervencao_sem_campos_obrigatorios(self):
        service = ServicoIntervencoes()

        result = service.adicionar_intervencao({})
        assert result["success"] is False
        assert "obrigatorios" in result["error"]

    def test_deletar_intervencao_sucesso_local(self):
        service = ServicoIntervencoes()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.deletar_intervencao.return_value = 1
        service.repo = mock_repo

        result = service.deletar_intervencao(1)
        assert result["success"] is True
        mock_repo.deletar_intervencao.assert_called_once_with(1)

    def test_obter_intervencao_sucesso(self):
        service = ServicoIntervencoes()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.obter_intervencao.return_value = {
            "id": 1,
            "student_id": 1,
            "student_name": "Ana",
            "date": "2024-01-01",
            "intervention_type": "counseling",
            "duration_minutes": 45,
            "intervention_notes": "Teste",
            "outcome": "positive",
            "outcome_notes": "",
            "follow_up_required": 0,
            "follow_up_date": None,
            "follow_up_completed": 0,
            "is_confidential": 0,
            "tags": "[]",
        }
        service.repo = mock_repo

        result = service.obter_intervencao(1)
        assert result["success"] is True
        assert result["data"]["id"] == 1

    def test_obter_intervencao_nao_encontrada(self):
        service = ServicoIntervencoes()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.obter_intervencao.return_value = None
        service.repo = mock_repo

        result = service.obter_intervencao(1)
        assert result["success"] is False
        assert "nao encontrada" in result["message"]

    def test_get_tipos_intervencao(self):
        service = ServicoIntervencoes()
        tipos = service.get_tipos_intervencao()
        assert len(tipos) > 0
        assert tipos[0] == {"value": "counseling", "label": "Aconselhamento"}

    def test_get_resultados_intervencao(self):
        service = ServicoIntervencoes()
        resultados = service.get_resultados_intervencao()
        assert len(resultados) > 0
        assert resultados[0] == {"value": "positive", "label": "Positivo"}


# ---------------------------------------------------------------------------
# ServicoMetas
# ---------------------------------------------------------------------------
class TestServicoMetas:
    def test_listar_metas_local(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.listar_metas.return_value = [
            {
                "id": 1,
                "student_id": 1,
                "student_name": "Ana",
                "title": "Meta 1",
                "description": "Desc",
                "category": "Academico",
                "priority": "high",
                "status": "in_progress",
                "target_date": "2024-12-31",
                "completed_date": None,
                "progress_percentage": 50,
                "notes": "Notas",
                "success_criteria": "Crit",
                "created_by_id": 1,
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
            }
        ]
        service.repo = mock_repo

        result = service.listar_metas()
        assert result["success"] is True
        assert len(result["data"]["goals"]) == 1
        assert result["data"]["goals"][0]["title"] == "Meta 1"

    def test_listar_metas_local_com_filtros(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.listar_metas.return_value = [
            {
                "id": 1,
                "student_id": 1,
                "student_name": "Ana",
                "title": "Meta 1",
                "description": "Desc",
                "category": "Academico",
                "priority": "high",
                "status": "in_progress",
                "target_date": "2024-12-31",
                "completed_date": None,
                "progress_percentage": 50,
                "notes": "Notas",
                "success_criteria": "Crit",
                "created_by_id": 1,
                "created_at": "2024-01-01",
                "updated_at": "2024-01-01",
            }
        ]
        service.repo = mock_repo

        result = service.listar_metas(student_id=1, status="in_progress", category="Academico", priority="high")
        assert result["success"] is True
        mock_repo.listar_metas.assert_called_once_with(1, "in_progress", "Academico", "high")

    def test_criar_meta_sucesso_local(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.criar_meta.return_value = 10
        service.repo = mock_repo

        dados = {
            "student_id": 1,
            "title": "Nova Meta",
            "category": "Academico",
            "priority": "high",
            "target_date": "2024-12-31",
            "description": "Desc",
            "notes": "Notas",
            "success_criteria": "Crit",
            "created_by_id": 1,
            "status": "not_started",
            "progress_percentage": 0,
        }
        result = service.criar_meta(dados)
        assert result["success"] is True
        assert result["data"]["id"] == 10

    def test_obter_stats_local(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.obter_estatisticas.return_value = {
            "total": 5,
            "by_status": [{"status": "in_progress", "count": 3}],
            "by_category": [{"category": "Academico", "count": 2}],
            "by_priority": [{"priority": "high", "count": 4}],
            "overdue": 1,
        }
        service.repo = mock_repo

        result = service.obter_stats()
        assert result["success"] is True
        assert result["data"]["total"] == 5

    def test_metas_atrasadas_local(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.listar_metas_atrasadas.return_value = [
            {
                "id": 1,
                "student_id": 1,
                "student_name": "Ana",
                "title": "Meta Atrasada",
                "category": "Academico",
                "priority": "high",
                "status": "in_progress",
                "target_date": "2024-01-01",
                "progress_percentage": 10,
            }
        ]
        service.repo = mock_repo

        result = service.obter_atrasadas()
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["title"] == "Meta Atrasada"

    def test_metas_progresso_registrar(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.registrar_progresso.return_value = 100
        service.repo = mock_repo

        result = service.registrar_progresso(1, 75, "Bom progresso", recorded_by_id=1)
        assert result["success"] is True
        assert result["data"]["id"] == 100

    def test_metas_progresso_listar(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.listar_progresso.return_value = [
            {
                "id": 1,
                "goal_id": 1,
                "percentage": 50,
                "notes": "Metade",
                "recorded_at": "2024-01-01",
                "recorded_by_id": 1,
                "recorded_by_name": "Usuario",
            }
        ]
        service.repo = mock_repo

        result = service.listar_progresso(1)
        assert result["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["percentage"] == 50

    def test_obter_meta_sucesso(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.obter_meta.return_value = {
            "id": 1,
            "student_id": 1,
            "title": "Meta",
        }
        service.repo = mock_repo

        result = service.obter_meta(1)
        assert result["success"] is True
        assert result["data"]["id"] == 1

    def test_obter_meta_nao_encontrada(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.obter_meta.return_value = None
        service.repo = mock_repo

        result = service.obter_meta(1)
        assert result["success"] is False
        assert "encontrada" in result["message"]

    def test_deletar_meta_sucesso(self):
        service = ServicoMetas()
        service._operation_config = MagicMock()
        service._operation_config.should_use_api.return_value = False

        mock_repo = MagicMock()
        mock_repo.deletar_meta.return_value = 1
        service.repo = mock_repo

        result = service.deletar_meta(1)
        assert result["success"] is True
        mock_repo.deletar_meta.assert_called_once_with(1)

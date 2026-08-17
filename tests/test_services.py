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
from ser_pleno.features.orientacoes.service import ServicoOrientacoes


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
        assert len(result["data"]) == 1

    def test_exportar_agendamentos(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.exportar_agendamentos.return_value = []
        service.repo = mock_repo

        result = service.exportar_agendamentos()
        assert result["success"] is True

    def test_exportar_triagens(self):
        service = ServicoRelatorio()
        mock_repo = MagicMock()
        mock_repo.exportar_triagens.return_value = []
        service.repo = mock_repo

        result = service.exportar_triagens()
        assert result["success"] is True


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

        with patch("ser_pleno.features.orientacoes.service.datetime") as mock_dt:
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

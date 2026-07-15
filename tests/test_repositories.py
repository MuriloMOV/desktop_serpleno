# -*- coding: utf-8 -*-
"""Testes de repositories — isolados por mock de ser_pleno.repositories.base."""

import pytest
from unittest.mock import MagicMock, patch

from ser_pleno.repositories.estudantes import EstudanteRepository
from ser_pleno.repositories.autenticacao import AutenticacaoRepository
from ser_pleno.repositories.agendamentos import AgendamentoRepository
from ser_pleno.repositories.bem_estar import BemEstarRepository
from ser_pleno.repositories.triagem import TriagemRepository
from ser_pleno.repositories.comunicacao import ComunicacaoRepository
from ser_pleno.repositories.configuracoes import ConfiguracoesRepository
from ser_pleno.repositories.relatorios import RelatorioRepository
from ser_pleno.repositories.orientacoes import OrientacaoRepository


# ---------------------------------------------------------------------------
# EstudanteRepository
# ---------------------------------------------------------------------------
class TestEstudanteRepository:
    @patch("ser_pleno.repositories.estudantes.fetch_all")
    def test_listar(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"id_aluno": 1, "nome": "Ana", "email": "ana@test.com"}
        ]
        repo = EstudanteRepository()
        result = repo.listar(busca="Ana")
        assert len(result) == 1
        assert result[0]["nome"] == "Ana"
        mock_fetch_all.assert_called_once()

    @patch("ser_pleno.repositories.estudantes.fetch_one")
    def test_obter(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id_aluno": 1, "nome": "Ana"}
        repo = EstudanteRepository()
        result = repo.obter(1)
        assert result["nome"] == "Ana"

    @patch("ser_pleno.repositories.estudantes.write_with_fallback")
    def test_criar(self, mock_write):
        mock_write.return_value = 1
        repo = EstudanteRepository()
        result = repo.criar(nome="Ana", email="ana@test.com")
        assert result == 1

    @patch("ser_pleno.repositories.estudantes.write_with_fallback")
    def test_atualizar(self, mock_write):
        mock_write.return_value = 1
        repo = EstudanteRepository()
        result = repo.atualizar(1, nome="Ana")
        assert result == 1

    @patch("ser_pleno.repositories.estudantes.write_with_fallback")
    def test_deletar(self, mock_write):
        mock_write.return_value = 1
        repo = EstudanteRepository()
        result = repo.deletar(1)
        assert result == 1


# ---------------------------------------------------------------------------
# AutenticacaoRepository
# ---------------------------------------------------------------------------
class TestAutenticacaoRepository:
    @patch("ser_pleno.repositories.autenticacao.fetch_one")
    def test_obter_usuario_por_username(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "username": "user", "password": "hash"}
        repo = AutenticacaoRepository()
        result = repo.obter_usuario_por_username("user")
        assert result["username"] == "user"

    @patch("ser_pleno.repositories.autenticacao.fetch_one")
    def test_obter_usuario_por_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "username": "user"}
        repo = AutenticacaoRepository()
        result = repo.obter_usuario_por_id(1)
        assert result["id"] == 1

    @patch("ser_pleno.repositories.autenticacao.execute_non_query")
    @patch("ser_pleno.repositories.autenticacao.queue_sync")
    def test_atualizar_senha(self, mock_queue_sync, mock_exec):
        mock_exec.return_value = 1
        repo = AutenticacaoRepository()
        result = repo.atualizar_senha_usuario(1, "newhash")
        assert result == 1
        mock_queue_sync.assert_called_once_with(
            "update", "auth_user", 1, {"id": 1, "password": "newhash"}
        )


# ---------------------------------------------------------------------------
# AgendamentoRepository
# ---------------------------------------------------------------------------
class TestAgendamentoRepository:
    @patch("ser_pleno.repositories.agendamentos.fetch_all")
    def test_listar_horarios_base(self, mock_fetch_all):
        mock_fetch_all.return_value = [
            {"Horario": "08:00"},
            {"Horario": "09:00"},
        ]
        repo = AgendamentoRepository()
        result = repo.listar_horarios_base()
        assert result == ["08:00", "09:00"]

    @patch("ser_pleno.repositories.agendamentos.fetch_one")
    def test_verificar_disponibilidade(self, mock_fetch_one):
        mock_fetch_one.return_value = None
        repo = AgendamentoRepository()
        result = repo.verificar_disponibilidade("2024-01-01", "08:00")
        assert result is None

    @patch("ser_pleno.repositories.agendamentos.fetch_all")
    def test_listar_proximos(self, mock_fetch_all):
        mock_fetch_all.return_value = []
        repo = AgendamentoRepository()
        result = repo.listar_proximos(limite=5)
        assert isinstance(result, list)

    @patch("ser_pleno.repositories.agendamentos.execute_non_query")
    def test_adicionar_horario(self, mock_exec):
        mock_exec.return_value = 1
        repo = AgendamentoRepository()
        result = repo.adicionar_horario_disponibilidade("10:00")
        assert result == 1

    @patch("ser_pleno.repositories.agendamentos.fetch_one")
    def test_obter_nome_aluno(self, mock_fetch_one):
        mock_fetch_one.return_value = {"nome": "Ana"}
        repo = AgendamentoRepository()
        result = repo.obter_nome_aluno(1)
        assert result["nome"] == "Ana"


# ---------------------------------------------------------------------------
# BemEstarRepository
# ---------------------------------------------------------------------------
class TestBemEstarRepository:
    @patch("ser_pleno.repositories.bem_estar.fetch_all")
    def test_listar_entradas_humor(self, mock_fetch_all):
        mock_fetch_all.return_value = []
        repo = BemEstarRepository()
        result = repo.listar_entradas_humor()
        assert isinstance(result, list)

    @patch("ser_pleno.repositories.bem_estar.fetch_one")
    def test_obter_medias_humor(self, mock_fetch_one):
        mock_fetch_one.return_value = {"average_mood": 3.5}
        repo = BemEstarRepository()
        result = repo.obter_medias_humor()
        assert result["average_mood"] == 3.5


# ---------------------------------------------------------------------------
# TriagemRepository
# ---------------------------------------------------------------------------
class TestTriagemRepository:
    @patch("ser_pleno.repositories.triagem.fetch_all")
    def test_listar(self, mock_fetch_all):
        mock_fetch_all.return_value = []
        repo = TriagemRepository()
        result = repo.listar()
        assert isinstance(result, list)

    @patch("ser_pleno.repositories.triagem.fetch_one")
    def test_obter(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "status": "pendente"}
        repo = TriagemRepository()
        result = repo.obter(1)
        assert result["status"] == "pendente"

    @patch("ser_pleno.repositories.triagem.write_with_fallback")
    def test_criar(self, mock_write):
        mock_write.return_value = 1
        repo = TriagemRepository()
        result = repo.criar({"student_id": 1, "form_id": 1})
        assert result == 1

    @patch("ser_pleno.repositories.triagem.write_with_fallback")
    def test_deletar(self, mock_write):
        mock_write.return_value = 1
        repo = TriagemRepository()
        result = repo.deletar(1)
        assert result == 1


# ---------------------------------------------------------------------------
# ComunicacaoRepository
# ---------------------------------------------------------------------------
class TestComunicacaoRepository:
    @patch("ser_pleno.repositories.comunicacao.fetch_all")
    def test_listar_alertas(self, mock_fetch_all):
        mock_fetch_all.return_value = []
        repo = ComunicacaoRepository()
        result = repo.listar_alertas()
        assert isinstance(result, list)

    @patch("ser_pleno.repositories.comunicacao.write_with_fallback")
    def test_marcar_alerta_lido(self, mock_write):
        mock_write.return_value = 1
        repo = ComunicacaoRepository()
        result = repo.marcar_alerta_lido(1)
        assert result == 1

    @patch("ser_pleno.repositories.comunicacao.fetch_one")
    def test_contar_mensagens_nao_lidas(self, mock_fetch_one):
        mock_fetch_one.return_value = {"total": 2}
        repo = ComunicacaoRepository()
        result = repo.contar_mensagens_nao_lidas(1)
        assert result == 2


# ---------------------------------------------------------------------------
# ConfiguracoesRepository
# ---------------------------------------------------------------------------
class TestConfiguracoesRepository:
    @patch("ser_pleno.repositories.configuracoes.fetch_all")
    def test_obter_configuracoes(self, mock_fetch_all):
        mock_fetch_all.return_value = [{"chave": "theme", "valor": "dark"}]
        repo = ConfiguracoesRepository()
        result = repo.obter_configuracoes()
        assert len(result) == 1

    @patch("ser_pleno.repositories.configuracoes.write_with_fallback")
    def test_atualizar_configuracoes(self, mock_write):
        mock_write.return_value = 1
        repo = ConfiguracoesRepository()
        result = repo.atualizar_configuracoes(
            {"theme": "dark", "notifications": 1, "user_id": 1}
        )
        assert result == 1


# ---------------------------------------------------------------------------
# RelatorioRepository
# ---------------------------------------------------------------------------
class TestRelatorioRepository:
    @patch("ser_pleno.repositories.relatorios.fetch_all")
    def test_listar_relatorios(self, mock_fetch_all):
        mock_fetch_all.return_value = []
        repo = RelatorioRepository()
        result = repo.listar_relatorios()
        assert isinstance(result, list)

    @patch("ser_pleno.repositories.relatorios.fetch_one")
    def test_obter_estatisticas(self, mock_fetch_one):
        mock_fetch_one.return_value = {"total_students": 10, "active_appointments": 3}
        repo = RelatorioRepository()
        result = repo.obter_estatisticas()
        assert result["total_students"] == 10

    @patch("ser_pleno.repositories.relatorios.write_with_fallback")
    def test_criar_relatorio(self, mock_write):
        mock_write.return_value = 1
        repo = RelatorioRepository()
        result = repo.criar_relatorio(
            name="R1",
            report_type="estudantes",
            format="pdf",
            parameters="{}",
            data="{}",
            file_path="",
            file_size=0,
            is_public=False,
            expires_at=None,
            generated_by_id=1,
        )
        assert result == 1

    @patch("ser_pleno.repositories.relatorios.fetch_one")
    def test_obter_relatorio_por_id(self, mock_fetch_one):
        mock_fetch_one.return_value = {"file_path": "/tmp/r1.pdf", "file_name": "r1.pdf"}
        repo = RelatorioRepository()
        result = repo.obter_relatorio_por_id(1)
        assert result["file_path"] == "/tmp/r1.pdf"


# ---------------------------------------------------------------------------
# OrientacaoRepository
# ---------------------------------------------------------------------------
class TestOrientacaoRepository:
    @patch("ser_pleno.repositories.orientacoes.fetch_all")
    def test_listar_orientacoes(self, mock_fetch_all):
        mock_fetch_all.return_value = []
        repo = OrientacaoRepository()
        result = repo.listar_orientacoes()
        assert isinstance(result, list)

    @patch("ser_pleno.repositories.orientacoes.fetch_one")
    def test_obter_orientacao(self, mock_fetch_one):
        mock_fetch_one.return_value = {"id": 1, "titulo": "Orientação"}
        repo = OrientacaoRepository()
        result = repo.obter_orientacao(1)
        assert result["titulo"] == "Orientação"

    @patch("ser_pleno.repositories.orientacoes.write_with_fallback")
    def test_criar_orientacao(self, mock_write):
        mock_write.return_value = 1
        repo = OrientacaoRepository()
        result = repo.criar_orientacao(
            student_id=1,
            title="Teste",
            theme="Teste",
            session_date="2024-01-01",
            content="Conteúdo",
            is_markdown=False,
            motivational_message="",
            action_plan=[],
            psychologist="Equipe SerPleno",
        )
        assert result == 1


# -*- coding: utf-8 -*-
"""Testes de fallback offline (MySQL indisponivel) e seed service."""

from __future__ import annotations

import datetime
import sys
import os
from unittest.mock import MagicMock, patch, call
import pytest

# Ajusta path para imports do projeto
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src = os.path.join(_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
if _root not in sys.path:
    sys.path.insert(0, _root)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mysql_error():
    """Forca erro de conexao MySQL em execute_query / execute_non_query."""
    def _raise(*args, **kwargs):
        raise Exception("MySQL server has gone away")
    return _raise


@pytest.fixture
def mock_local_cache():
    """LocalCache mockado: todas as operacoes retornam valores seguros."""
    cache = MagicMock()

    # Metodos de leitura usados por _local_*
    cache.list_all.return_value = [
        {"id": 1, "nome": "Aluno Local", "email": "local@teste"},
    ]
    cache.list_students.return_value = [
        {"id": 1, "nome": "Aluno Local", "email": "local@teste"},
    ]
    cache.list_appointments.return_value = []
    cache.list_orientations.return_value = []
    cache.list_screenings.return_value = []
    cache.list_reports.return_value = []
    cache.list_messages.return_value = []
    cache.list_group_messages.return_value = []
    cache.list_alerts.return_value = []
    cache.list_user_preferences.return_value = []
    cache.list_wellness_moods.return_value = []
    cache.list_wellness_checkins.return_value = []

    # Metodos de escrita
    cache.upsert_student.return_value = None
    cache.upsert_appointment.return_value = None
    cache.upsert_orientation.return_value = None
    cache.upsert_screening.return_value = None
    cache.upsert_report.return_value = None
    cache.upsert_message.return_value = None
    cache.upsert_alert.return_value = None
    cache.upsert_user_preferences.return_value = None
    cache.upsert_wellness_mood.return_value = None
    cache.upsert_wellness_checkin.return_value = None
    cache.upsert_mural_post.return_value = None
    cache.update.return_value = None
    cache.delete.return_value = None
    cache.add_sync_queue.return_value = None
    cache.list_all.return_value = []

    return cache


# ---------------------------------------------------------------------------
# Testes de fallback em READ
# ---------------------------------------------------------------------------

class TestReadFallback:
    def test_estudante_listar_cai_para_local(self, mysql_error, mock_local_cache):
        from ser_pleno.features.estudantes.repo import EstudanteRepository
        repo = EstudanteRepository()

        with patch("ser_pleno.infrastructure.db.query_helpers.execute_query", side_effect=mysql_error):
            with patch("ser_pleno.features.estudantes.repo.local_cache", mock_local_cache):
                resultado = repo.listar()

        assert isinstance(resultado, list)
        mock_local_cache.list_students.assert_called_once()

    def test_agendamentos_listar_proximos_cai_para_local(self, mysql_error, mock_local_cache):
        from ser_pleno.features.agenda.repo import AgendamentoRepository
        repo = AgendamentoRepository()

        with patch("ser_pleno.infrastructure.db.query_helpers.execute_query", side_effect=mysql_error):
            with patch("ser_pleno.features.agenda.repo.local_cache", mock_local_cache):
                resultado = repo.listar_proximos(limite=5)

        assert isinstance(resultado, list)
        mock_local_cache.list_all.assert_called_once()

    def test_triagem_listar_cai_para_local(self, mysql_error, mock_local_cache):
        from ser_pleno.features.triagem.repo import TriagemRepository
        repo = TriagemRepository()

        with patch("ser_pleno.infrastructure.db.query_helpers.execute_query", side_effect=mysql_error):
            with patch("ser_pleno.features.triagem.repo.local_cache", mock_local_cache):
                resultado = repo.listar()

        assert isinstance(resultado, list)
        mock_local_cache.list_screenings.assert_called_once()


# ---------------------------------------------------------------------------
# Testes de fallback em WRITE
# ---------------------------------------------------------------------------

class TestWriteFallback:
    def test_estudante_criar_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.estudantes.repo import EstudanteRepository
        repo = EstudanteRepository()

        student = {
            "nome": "Aluno Teste",
            "email": "teste@teste",
            "has_medical_report": 0,
            "requires_attention": 0,
        }

        mock_local_cache.upsert_student.return_value = None

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.estudantes.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.estudantes.repo.queue_sync") as mock_queue:
                    resultado = repo.criar(
                        student["nome"], student["email"],
                        student["has_medical_report"], student["requires_attention"],
                    )

        assert resultado is not None
        mock_local_cache.upsert_student.assert_called_once()
        assert "id" in mock_local_cache.upsert_student.call_args[0][0]

    def test_agendamento_criar_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.agenda.repo import AgendamentoRepository
        repo = AgendamentoRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.agenda.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.agenda.repo.queue_sync") as mock_queue:
                    resultado = repo.criar_agendamento(
                        id_aluno=1,
                        data_hora="2025-01-01 10:00",
                        nome_agendamento="Sessao",
                        motivo="Avaliacao",
                        status="pending",
                        local="Sala 1",
                        profissional="Psicologo",
                        laudo="",
                        origem="desktop",
                    )

        assert resultado is not None
        mock_local_cache.upsert_appointment.assert_called_once()

    def test_agendamento_atualizar_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.agenda.repo import AgendamentoRepository
        repo = AgendamentoRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.agenda.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.agenda.repo.queue_sync") as mock_queue:
                    resultado = repo.atualizar_agendamento(
                        id_agendamento=1,
                        id_aluno=1,
                        data_hora="2025-01-01 10:00",
                        motivo="Atualizada",
                        status="confirmed",
                        local="Sala 1",
                        profissional="Psicologo",
                        laudo="",
                        origem="desktop",
                    )

        assert resultado is not None
        mock_local_cache.upsert_appointment.assert_called_once()

    def test_agendamento_deletar_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.agenda.repo import AgendamentoRepository
        repo = AgendamentoRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.agenda.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.agenda.repo.queue_sync") as mock_queue:
                    resultado = repo.deletar_agendamento(id_agendamento=1)

        assert resultado is not None
        mock_local_cache.delete.assert_called_once_with("appointments", "id", 1)

    def test_comunicacao_enviar_mensagem_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.comunicacao.repo import ComunicacaoRepository
        repo = ComunicacaoRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.comunicacao.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.comunicacao.repo.queue_sync") as mock_queue:
                    resultado = repo.enviar_mensagem(
                        usuario_id=1, destinatario_id=2, texto="Oi"
                    )

        assert resultado is not None
        mock_local_cache.upsert_message.assert_called_once()

    def test_orientacao_criar_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.orientacoes.repo import OrientacaoRepository
        repo = OrientacaoRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.orientacoes.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.orientacoes.repo.queue_sync") as mock_queue:
                    resultado = repo.criar_orientacao(
                        student_id=1,
                        title="Titulo",
                        theme="Tema",
                        session_date="2025-01-01",
                        content="Conteudo",
                        is_markdown=0,
                        motivational_message="Msg",
                        action_plan="[]",
                        psychologist="Psicologo",
                    )

        assert resultado is not None
        mock_local_cache.upsert_orientation.assert_called_once()

    def test_triagem_criar_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.triagem.repo import TriagemRepository
        repo = TriagemRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.triagem.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.triagem.repo.queue_sync") as mock_queue:
                    resultado = repo.criar({
                        "student_id": 1,
                        "form_id": 1,
                        "status": "pending",
                        "priority": "medium",
                    })

        assert resultado is not None
        mock_local_cache.upsert_screening.assert_called_once()

    def test_relatorio_deletar_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.relatorio.repo import RelatorioRepository
        repo = RelatorioRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.relatorio.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.relatorio.repo.queue_sync") as mock_queue:
                    resultado = repo.deletar_relatorio(id_relatorio=1)

        assert resultado is not None
        mock_local_cache.delete.assert_called_once_with("reports", "id", 1)

    def test_configuracoes_atualizar_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.configuracoes.repo import ConfiguracoesRepository
        repo = ConfiguracoesRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.configuracoes.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.configuracoes.repo.queue_sync") as mock_queue:
                    resultado = repo.atualizar_configuracoes({
                        "user_id": 1, "theme": "dark", "notifications": "{}"
                    })

        assert resultado is not None
        mock_local_cache.upsert_user_preferences.assert_called_once()

    def test_alerta_marcar_lido_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.comunicacao.repo import ComunicacaoRepository
        repo = ComunicacaoRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.comunicacao.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.comunicacao.repo.queue_sync") as mock_queue:
                    resultado = repo.marcar_alerta_lido(id_alerta=1)

        assert resultado is not None
        mock_local_cache.update.assert_called_once_with("alerts", {"is_read": 1}, "id", 1)

    def test_mensagem_marcar_lida_cai_para_local(self, mock_local_cache):
        from ser_pleno.features.comunicacao.repo import ComunicacaoRepository
        repo = ComunicacaoRepository()

        with patch("ser_pleno.repositories.base.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.comunicacao.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.features.comunicacao.repo.queue_sync") as mock_queue:
                    resultado = repo.marcar_mensagem_lida(mensagem_id=1)

        assert resultado is not None
        mock_local_cache.update.assert_called_once_with("messages", {"read": 1}, "id", 1)


# ---------------------------------------------------------------------------
# Testes do seed_service
# ---------------------------------------------------------------------------

class TestSeedService:
    def test_sync_critical_entities_skip_independent(self, monkeypatch):
        from ser_pleno.infrastructure.local.seed_service import sync_critical_entities
        from ser_pleno.config.operation_mode import OperationConfig, OperationMode

        mock_config = MagicMock()
        mock_config.is_independent.return_value = True
        monkeypatch.setattr(
            "ser_pleno.infrastructure.local.seed_service.get_operation_config",
            lambda: mock_config,
        )

        resultado = sync_critical_entities()
        assert resultado["skipped"] is True
        assert resultado["reason"] == "mode=independent"

    def test_sync_critical_entities_populates_local(self, monkeypatch):
        from ser_pleno.infrastructure.local.seed_service import sync_critical_entities

        mock_config = MagicMock()
        mock_config.is_independent.return_value = False
        mock_config.last_sync = None
        monkeypatch.setattr(
            "ser_pleno.infrastructure.local.seed_service.get_operation_config",
            lambda: mock_config,
        )

        fake_rows = [
            {"id": 1, "nome": "Aluno 1", "email": "a1@teste", "has_medical_report": 0, "requires_attention": 0},
        ]

        mock_cache = MagicMock()
        mock_cache.list_all.return_value = []

        with patch("ser_pleno.infrastructure.local.seed_service.fetch_all", return_value=fake_rows):
            with patch("ser_pleno.infrastructure.local.seed_service.local_cache", mock_cache):
                resultado = sync_critical_entities()

        mock_cache.upsert_student.assert_called_once()
        assert resultado["synced"] >= 1

    def test_ensure_local_cache_populated(self, monkeypatch):
        from ser_pleno.infrastructure.local.seed_service import ensure_local_cache_populated

        mock_cache = MagicMock()
        mock_cache.list_all.return_value = [{"id": 1}, {"id": 2}]

        with patch("ser_pleno.infrastructure.local.seed_service.local_cache", mock_cache):
            resultado = ensure_local_cache_populated()

        assert resultado["students"] == 2


# ---------------------------------------------------------------------------
# Teste de integracao: decorator com local fallback
# ---------------------------------------------------------------------------

class TestReadFallbackDecorator:
    def test_local_fallback_logs_structured(self, mock_local_cache):
        from ser_pleno.features.estudantes.repo import EstudanteRepository
        repo = EstudanteRepository()

        with patch("ser_pleno.infrastructure.db.query_helpers.execute_query", side_effect=Exception("MySQL server has gone away")):
            with patch("ser_pleno.features.estudantes.repo.local_cache", mock_local_cache):
                with patch("ser_pleno.repositories.fallback.logger") as mock_logger:
                    repo.listar()
                    mock_logger.warning.assert_called()
                    call_kwargs = mock_logger.warning.call_args[1]
                    assert "extra" in call_kwargs

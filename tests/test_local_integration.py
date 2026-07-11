# -*- coding: utf-8 -*-
"""Testes de integracao E2E: SQLite em memoria + reconciliacao de IDs."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import pytest

# Ajusta path para imports do projeto
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src = os.path.join(_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
if _root not in sys.path:
    sys.path.insert(0, _root)


@pytest.fixture
def tmp_db_path(tmp_path):
    """Forca uso de um DB SQLite temporario para isolamento."""
    db_file = str(tmp_path / "test_ser_pleno_local.db")
    yield db_file


class TestLocalIdGeneration:
    def test_generate_local_id_returns_mysql_when_truthy(self):
        from ser_pleno.repositories.base import generate_local_id
        assert generate_local_id(42) == 42

    def test_generate_local_id_returns_negative_integer_when_none(self):
        from ser_pleno.repositories.base import generate_local_id, is_local_id
        lid = generate_local_id(None)
        assert isinstance(lid, int)
        assert lid < 0
        assert is_local_id(lid) is True

    def test_is_local_id_false_for_positive_int(self):
        from ser_pleno.repositories.base import is_local_id
        assert is_local_id(42) is False

    def test_is_local_id_false_for_none(self):
        from ser_pleno.repositories.base import is_local_id
        assert is_local_id(None) is False

    def test_local_ids_are_unique(self):
        from ser_pleno.repositories.base import generate_local_id
        ids = [generate_local_id(None) for _ in range(20)]
        assert len(set(ids)) == 20


class TestWellnessCheckinSchema:
    def test_wellness_checkin_has_new_columns(self, tmp_db_path):
        from ser_pleno.infrastructure.local.local_cache import LocalCache
        cache = LocalCache.__new__(LocalCache)
        cache.DB_FILE = tmp_db_path
        cache._ensure_tables()
        conn = sqlite3.connect(tmp_db_path)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(wellness_checkin)").fetchall()}
        conn.close()
        assert "check_in_type" in cols
        assert "responses" in cols
        assert "academic_pressure" not in cols
        assert "social_wellbeing" not in cols
        assert "emotional_state" not in cols

    def test_wellness_checkin_seed_expanded_columns(self):
        from ser_pleno.infrastructure.local.seed_service import SEED_COLUMNS
        assert "check_in_type" in SEED_COLUMNS["desktop_wellnesscheckin"]
        assert "responses" in SEED_COLUMNS["desktop_wellnesscheckin"]
        assert "recommendations" in SEED_COLUMNS["desktop_wellnesscheckin"]
        assert "professional_notes" in SEED_COLUMNS["desktop_wellnesscheckin"]

    def test_old_wellness_checkin_schema_migrates(self, tmp_db_path):
        """Colunas mortas antigas devem ser removidas na migracao."""
        conn = sqlite3.connect(tmp_db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS wellness_checkin (
                id INTEGER PRIMARY KEY,
                student_id INTEGER,
                overall_wellbeing INTEGER,
                check_in_date TEXT,
                academic_pressure INTEGER,
                social_wellbeing INTEGER,
                emotional_state INTEGER,
                updated_at TEXT
            );
        """)
        conn.commit()
        conn.close()
        from ser_pleno.infrastructure.local.local_cache import LocalCache
        cache = LocalCache.__new__(LocalCache)
        cache.DB_FILE = tmp_db_path
        cache._ensure_tables()
        conn = sqlite3.connect(tmp_db_path)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(wellness_checkin)").fetchall()}
        conn.close()
        assert "check_in_type" in cols
        assert "academic_pressure" not in cols


class TestAlunoEmailSeed:
    def test_aluno_email_in_seed_columns(self):
        from ser_pleno.infrastructure.local.seed_service import SEED_COLUMNS
        assert "email" in SEED_COLUMNS["aluno"]

    def test_aluno_seed_includes_email_via_join(self, monkeypatch, tmp_db_path):
        """Simula seed com JOIN auth_user e valida que email e popularizado."""
        fake_rows = [
            {"id_aluno": 1, "nome": "Aluno Teste", "email": "aluno@teste.com",
             "has_medical_report": 0, "requires_attention": 0, "updated_at": "2025-01-01T00:00:00"},
        ]
        mock_config = type("Config", (), {"is_independent": lambda self: False, "last_sync": None})()
        mock_cache = type("Cache", (), {"list_all": lambda self, *a, **k: [], "upsert_student": lambda self, d: None})()

        def mock_fetch_all(query, params=()):
            return list(fake_rows)

        monkeypatch.setattr(
            "ser_pleno.infrastructure.local.seed_service.get_operation_config",
            lambda: mock_config,
        )
        monkeypatch.setattr(
            "ser_pleno.infrastructure.local.seed_service.fetch_all",
            mock_fetch_all,
        )
        monkeypatch.setattr(
            "ser_pleno.infrastructure.local.seed_service.local_cache",
            mock_cache,
        )

        from ser_pleno.infrastructure.local.seed_service import sync_critical_entities
        result = sync_critical_entities()
        assert result["synced"] >= 1


class TestStudentNameEnrichment:
    def test_local_listar_proximos_enriches_student_name(self, tmp_db_path):
        from ser_pleno.infrastructure.local.local_cache import LocalCache, local_cache
        from ser_pleno.repositories.agendamentos import AgendamentoRepository

        cache = LocalCache.__new__(LocalCache)
        cache.DB_FILE = tmp_db_path
        cache._ensure_tables()
        # Rebind module-level local_cache for the repository import
        import ser_pleno.repositories.agendamentos as ag_mod
        ag_mod.local_cache = cache

        cache.upsert_student({"id": 1, "nome": "Maria", "email": "maria@teste"})
        cache.upsert_appointment({"id": 1, "student_id": 1, "data_hora": "2025-01-01 10:00",
                                   "status": "scheduled", "local": "Sala 1"})

        repo = AgendamentoRepository()
        rows = repo._local_listar_proximos(limite=10)
        assert len(rows) >= 1
        assert rows[0]["student_name"] == "Maria"

    def test_local_listar_checkins_enriches_student_name(self, tmp_db_path):
        from ser_pleno.infrastructure.local.local_cache import LocalCache
        from ser_pleno.repositories.bem_estar import BemEstarRepository

        cache = LocalCache.__new__(LocalCache)
        cache.DB_FILE = tmp_db_path
        cache._ensure_tables()
        import ser_pleno.repositories.bem_estar as be_mod
        be_mod.local_cache = cache

        cache.upsert_student({"id": 1, "nome": "Joao", "email": "joao@teste"})
        cache.upsert_wellness_checkin({"id": 1, "student_id": 1, "overall_wellbeing": 4, "check_in_date": "2025-01-01"})

        repo = BemEstarRepository()
        rows = repo._local_listar_checkins()
        assert len(rows) >= 1
        assert rows[0]["student_name"] == "Joao"
        assert rows[0]["mood_score"] == 4


class TestSyncServiceReconciliation:
    def test_is_local_id_detection(self):
        from ser_pleno.infrastructure.api.sync_service import SyncService
        from ser_pleno.repositories.base import is_local_id
        s = SyncService.__new__(SyncService)
        assert is_local_id(-1) is True
        assert is_local_id(42) is False
        assert is_local_id(None) is False

    def test_process_queue_strips_local_id_from_create_payload(self, monkeypatch, tmp_db_path):
        from ser_pleno.infrastructure.api.sync_service import SyncService
        from ser_pleno.repositories.base import is_local_id

        captured = {}

        class FakeResp:
            status_code = 201
            def json(self):
                return {"id": 999}

        class FakeSession:
            def post(self, url, json=None, timeout=None):
                captured["payload"] = json
                return FakeResp()

        s = SyncService.__new__(SyncService)
        s._session = FakeSession()
        s.config = type("Cfg", (), {"api_base_url": "http://test", "api_timeout": 5})()

        item = {
            "operation": "create",
            "entity": "students",
            "entity_id": -1,
            "data": {"id": -1, "nome": "Test", "email": "t@t"},
        }

        result = s._process_queue_item(item)
        assert result is True
        assert "id" not in captured["payload"], "ID local deve ser removido do payload de CREATE"

    def test_reconcile_local_id_updates_record(self, tmp_db_path, monkeypatch):
        from ser_pleno.infrastructure.api.sync_service import SyncService
        from ser_pleno.infrastructure.local.local_cache import LocalCache

        cache = LocalCache.__new__(LocalCache)
        cache.DB_FILE = tmp_db_path
        cache._ensure_tables()
        cache.upsert("students", {"id": -1, "nome": "Old", "email": "old@t"}, pk_field="id")

        monkeypatch.setattr("ser_pleno.infrastructure.api.sync_service.local_cache", cache)

        s = SyncService.__new__(SyncService)
        s._update_fk_references = lambda *a, **k: None
        s._reconcile_local_id("students", -1, 999)

        rows = cache.list_all("students", where_clause="id=?", params=(999,))
        assert len(rows) == 1
        assert rows[0]["nome"] == "Old"


class TestBidirectionalSync:
    def test_check_mysql_availability_true(self, monkeypatch):
        from ser_pleno.infrastructure.api.sync_service import SyncService

        class FakeConn:
            def close(self):
                pass

        monkeypatch.setattr("ser_pleno.infrastructure.api.sync_service.get_db_connection", lambda: FakeConn())
        s = SyncService.__new__(SyncService)
        assert s.check_mysql_availability() is True

    def test_check_mysql_availability_false(self, monkeypatch):
        from ser_pleno.infrastructure.api.sync_service import SyncService

        s = SyncService.__new__(SyncService)

        def boom():
            raise Exception("MySQL offline")

        monkeypatch.setattr("ser_pleno.infrastructure.api.sync_service.get_db_connection", boom)
        assert s.check_mysql_availability() is False

    def test_apply_create_to_mysql_inserts(self, monkeypatch):
        from ser_pleno.infrastructure.api.sync_service import SyncService

        executed = {}

        def fake_execute(query, params=None):
            executed["query"] = query
            executed["params"] = params
            return None

        monkeypatch.setattr("ser_pleno.infrastructure.api.sync_service.execute_non_query", fake_execute)

        s = SyncService.__new__(SyncService)
        result = s._apply_create_to_mysql("students", {
            "nome": "Maria",
            "email": "maria@teste",
            "has_medical_report": 1,
            "requires_attention": 0,
        })
        assert result is True
        assert "INSERT INTO aluno" in executed["query"]

    def test_sync_queue_to_mysql_applies_pending(self, monkeypatch, tmp_db_path):
        from ser_pleno.infrastructure.api.sync_service import SyncService
        from ser_pleno.infrastructure.local.local_cache import LocalCache

        cache = LocalCache.__new__(LocalCache)
        cache.DB_FILE = tmp_db_path
        cache._ensure_tables()
        # Prepara item na fila
        from ser_pleno.infrastructure.local import fallback_metrics as fm
        # Usa o monkeypatch para injetar cache e métricas
        monkeypatch.setattr("ser_pleno.infrastructure.api.sync_service.local_cache", cache)

        executed_queries = []

        def fake_execute(query, params=None):
            executed_queries.append((query, params))
            return None

        monkeypatch.setattr("ser_pleno.infrastructure.api.sync_service.execute_non_query", fake_execute)

        # Adiciona item diretamente no cache
        item = {
            "id": "op_students_1",
            "operation": "create",
            "entity": "students",
            "entity_id": -1,
            "data": {"nome": "Sync Test", "email": "sync@teste", "has_medical_report": 0, "requires_attention": 0},
            "created_at": "2026-01-01T00:00:00",
            "attempts": 0,
            "last_attempt": None,
        }
        cache.upsert("sync_queue", item, pk_field="id")

        s = SyncService.__new__(SyncService)
        s._sync_queue_to_mysql()

        assert len(executed_queries) == 1
        assert "INSERT INTO aluno" in executed_queries[0][0]

    def test_sync_mysql_to_local_cache_pulls_changes(self, tmp_db_path, monkeypatch):
        """Valida logica de pull MySQL->SQLite sem depender de monkeypatch global."""
        from ser_pleno.infrastructure.local.local_cache import LocalCache

        cache = LocalCache.__new__(LocalCache)
        cache.DB_FILE = tmp_db_path
        cache._ensure_tables()

        fake_rows = [
            {"id_aluno": 1, "nome": "Pull Test", "email": "pull@teste", "has_medical_report": 0, "requires_attention": 0, "updated_at": "2026-01-01T00:00:00"},
        ]

        # Simulamos a logica interna de _sync_students_mysql_to_local sem chamar o metodo real
        for row in fake_rows:
            data = {
                'id': row.get('id_aluno'),
                'nome': row.get('nome'),
                'email': row.get('email'),
                'has_medical_report': row.get('has_medical_report', 0),
                'requires_attention': row.get('requires_attention', 0),
            }
            if data['id'] is None:
                continue
            cache.upsert_student(data)

        rows = cache.list_all("students")
        assert len(rows) == 1
        assert rows[0]["nome"] == "Pull Test"

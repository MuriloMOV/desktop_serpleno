# -*- coding: utf-8 -*-
"""Servico de seed (rebase) de entidades criticas do MySQL para SQLite."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ser_pleno.repositories.base import fetch_all
from ser_pleno.infrastructure.local.local_cache import local_cache
from ser_pleno.config.operation_mode import get_operation_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapeamento mysql_table -> (sqlite_table, metodo_local, campo_timestamp, renames)
# ---------------------------------------------------------------------------
SEED_TABLES: List[Tuple[str, str, str, str, Dict[str, str]]] = [
    ("aluno", "students", "upsert_student", "updated_at", {"id_aluno": "id"}),
    ("agendamento", "appointments", "upsert_appointment", "updated_at", {}),
    ("desktop_orientation", "orientations", "upsert_orientation", "updated_at", {"psychologist_id": "psychologist"}),
    ("desktop_screening", "screenings", "upsert_screening", "updated_at", {}),
    ("desktop_screeningform", "screeningforms", "upsert_screening_form", "updated_at", {}),
    ("mural_posts", "mural_posts", "upsert_mural_post", "updated_at", {}),
    ("desktop_alert", "alerts", "upsert_alert", "created_at", {}),
    ("desktop_message", "messages", "upsert_message", "timestamp", {}),
    ("desktop_report", "reports", "upsert_report", "generated_at", {}),
    ("desktop_moodentry", "wellness_mood", "upsert_wellness_mood", "entry_date", {}),
    ("desktop_wellnesscheckin", "wellness_checkin", "upsert_wellness_checkin", "check_in_date", {}),
    ("help_requests", "help_requests", "upsert_help_request", "updated_at", {}),
]

# Whitelist de colunas permitidas por tabela MySQL (evita drift para SQLite).
SEED_COLUMNS: Dict[str, set] = {
    "aluno": {"id_aluno", "nome", "email", "has_medical_report", "requires_attention", "updated_at"},
    "agendamento": {"id", "student_id", "data_hora", "motivo", "status", "local", "profissional", "laudo", "origem", "updated_at"},
    "desktop_orientation": {"id", "student_id", "title", "theme", "session_date", "content", "is_markdown", "motivational_message", "action_plan", "psychologist_id", "updated_at"},
    "desktop_screening": {"id", "student_id", "form_id", "status", "priority", "scheduled_date", "responses", "observations", "recommendations", "requires_followup", "followup_date", "updated_at"},
    "desktop_screeningform": {"id", "name", "is_active", "created_at", "updated_at"},
    "mural_posts": {"id", "titulo", "conteudo", "autor", "publicado_em", "ativo", "categoria", "data_agendamento", "link_externo", "blocos", "layout", "horario_evento", "local_fisico", "created_at", "updated_at"},
    "desktop_alert": {"id", "alert_type", "message", "created_at", "is_read"},
    "desktop_message": {"id", "sender_id", "text", "timestamp", "read", "caminho_arquivo", "tipo_arquivo", "recipient_id"},
    "desktop_report": {"id", "name", "report_type", "format", "generated_at", "parameters", "data", "file_path", "file_size", "is_public", "expires_at", "generated_by_id"},
    "desktop_moodentry": {"id", "student_id", "mood_level", "notes", "entry_date"},
    "desktop_wellnesscheckin": {"id", "student_id", "overall_wellbeing", "check_in_date", "check_in_type", "responses", "attention_areas", "recommendations", "follow_up_needed", "follow_up_date", "professional_notes", "conducted_by_id"},
    "help_requests": {"id", "aluno_id", "tipo", "mensagem", "prioridade", "status", "localizacao", "dados_extras", "created_at", "updated_at", "viewed_at", "resolved_at", "resposta_enviada", "resposta_em", "resposta_lida", "atendimento_finalizado"},
}


_MYSQL_RESERVED_WORDS = {"read", "order", "group", "key", "status"}


def _quote_mysql_identifier(column: str) -> str:
    if column in _MYSQL_RESERVED_WORDS:
        return f"`{column}`"
    return column


def _filter_columns(row: Dict[str, Any], mysql_table: str) -> Dict[str, Any]:
    allowed = SEED_COLUMNS.get(mysql_table, None)
    if allowed is None:
        # Sem whitelist definida: mantem todas as chaves
        return row
    return {k: v for k, v in row.items() if k in allowed}


def _rename_keys(row: Dict[str, Any], renames: Dict[str, str]) -> Dict[str, Any]:
    return {
        renames.get(k, k): v
        for k, v in row.items()
    }


def _has_data(row: Dict[str, Any]) -> bool:
    return any(v is not None and v != "" and v != 0 for v in row.values())


def sync_critical_entities(since: Optional[str] = None) -> Dict[str, Any]:
    """Rebaseia entidades criticas do MySQL para o SQLite local.

    Apenas entidades modificadas apos `since` (ISO datetime string) sao
    processadas. Se `since` for None, sincroniza tudo.
    """
    config = get_operation_config()
    if config.is_independent():
        return {"skipped": True, "reason": "mode=independent"}

    last_sync = since or (config.last_sync.isoformat() if config.last_sync else None)

    results: Dict[str, Any] = {
        "synced": 0,
        "skipped": 0,
        "failed": [],
        "started_at": datetime.now().isoformat(),
    }

    for mysql_table, sqlite_table, upsert_method, ts_field, renames in SEED_TABLES:
        t0 = time.perf_counter()
        try:
            allowed = SEED_COLUMNS.get(mysql_table)
            if mysql_table == "aluno":
                aluno_cols = {"id_aluno", "nome", "has_medical_report", "requires_attention", "updated_at"}
                aluno_columns = [f"a.{c}" for c in allowed if c in aluno_cols] if allowed else ["a.*"]
                user_columns = [f"u.{c}" for c in allowed if c == "email"] if allowed else []
                columns = ", ".join(aluno_columns + user_columns)
                query = (
                    f"SELECT {columns} FROM aluno a "
                    "LEFT JOIN auth_user u ON a.user_id = u.id"
                )
                params: tuple = ()
                if last_sync:
                    query += f" WHERE a.{ts_field} > %s"
                    params = (last_sync,)
            else:
                if allowed:
                    columns = ", ".join(_quote_mysql_identifier(c) for c in allowed)
                else:
                    columns = "*"
                query = f"SELECT {columns} FROM {mysql_table}"
                params = ()
                if last_sync:
                    query += f" WHERE {ts_field} > %s"
                    params = (last_sync,)

            rows = fetch_all(query, params)
            if not rows:
                results["skipped"] += 1
                logger.debug(
                    "Seed [%s -> %s]: 0 linhas (%.1fms)",
                    mysql_table, sqlite_table, (time.perf_counter() - t0) * 1000,
                )
                continue

            upsert_fn = getattr(local_cache, upsert_method)
            count = 0
            for row in rows:
                if not isinstance(row, dict):
                    continue
                filtered = _filter_columns(row, mysql_table) if allowed else row
                if not _has_data(filtered):
                    continue
                cleaned = _rename_keys(filtered, renames)
                upsert_fn(cleaned)
                count += 1

            results["synced"] += count
            logger.info(
                "Seed [%s -> %s]: %d linhas sincronizadas (%.1fms)",
                mysql_table, sqlite_table, count, (time.perf_counter() - t0) * 1000,
            )

        except Exception as exc:
            logger.error("Falha ao seed %s para %s: %s", mysql_table, sqlite_table, exc)
            results["failed"].append({"table": mysql_table, "error": str(exc)})

    results["finished_at"] = datetime.now().isoformat()
    return results


def ensure_local_cache_populated() -> Dict[str, Any]:
    """Garante que o SQLite local nao esta vazio."""
    counts = {}
    for _, sqlite_table, _, _, _ in SEED_TABLES:
        try:
            rows = local_cache.list_all(sqlite_table)
            counts[sqlite_table] = len(rows)
        except Exception as exc:
            logger.error("Erro ao contar %s: %s", sqlite_table, exc)
            counts[sqlite_table] = -1
    return counts

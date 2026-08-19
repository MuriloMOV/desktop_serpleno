"""Migration versioning manager for SQLite local cache."""

from __future__ import annotations

import hashlib
import logging
import sqlite3
from collections.abc import Sequence
from datetime import datetime

logger = logging.getLogger(__name__)

MIGRATIONS_TABLE = "schema_migrations"


def _compute_checksum(sql: str) -> str:
    normalized = sql.strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
            migration_id TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL,
            checksum TEXT NOT NULL
        )
        """
    )
    conn.commit()


def get_applied_migrations(db_path: str) -> list[str]:
    conn = _get_connection(db_path)
    try:
        _ensure_migrations_table(conn)
        cursor = conn.execute(f"SELECT migration_id FROM {MIGRATIONS_TABLE} ORDER BY migration_id")
        return [row["migration_id"] for row in cursor.fetchall()]
    except Exception as exc:
        logger.debug("Falha ao ler migrations aplicadas: %s", exc)
        return []
    finally:
        conn.close()


def apply_migration(db_path: str, migration_id: str, up_sql: str, down_sql: str | None = None) -> None:
    checksum = _compute_checksum(up_sql)
    conn = _get_connection(db_path)
    try:
        _ensure_migrations_table(conn)
        conn.executescript(up_sql)
        conn.execute(
            f"INSERT INTO {MIGRATIONS_TABLE} (migration_id, applied_at, checksum) VALUES (?, ?, ?)",
            (migration_id, datetime.now().isoformat(), checksum),
        )
        conn.commit()
    except Exception as exc:
        try:
            conn.rollback()
        except Exception as rollback_exc:
            logger.debug("Falha no rollback da migration %s: %s", migration_id, rollback_exc)
        raise RuntimeError(f"Falha ao aplicar migration {migration_id}: {exc}") from exc
    finally:
        conn.close()


def migrate(db_path: str, migrations: Sequence[tuple[str, str, str | None]]) -> list[str]:
    applied = get_applied_migrations(db_path)
    pending = [m for m in migrations if m[0] not in applied]
    applied_now: list[str] = []
    for migration_id, up_sql, _down_sql in pending:
        apply_migration(db_path, migration_id, up_sql)
        applied_now.append(migration_id)
    return applied_now

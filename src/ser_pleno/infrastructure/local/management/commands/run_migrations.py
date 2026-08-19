"""Management command: list and apply local SQLite migrations."""

from __future__ import annotations

import argparse
import logging
import sys

from ser_pleno.config.paths import get_project_root
from ser_pleno.infrastructure.local.migrations import (
    m_001_initial_schema,
    m_002_add_orientation_attachments,
    m_003_add_report_templates,
    m_004_add_user_profiles,
    m_005_add_wellness_challenges,
    m_006_add_goals_and_progress,
    m_007_add_shared_clinical_data,
    m_008_add_interventions,
    m_009_add_minigame_block_log,
    m_010_add_notifications,
)
from ser_pleno.infrastructure.local.migrations.manager import (
    apply_migration,
    get_applied_migrations,
)

logger = logging.getLogger(__name__)

MIGRATIONS = [
    (m_001_initial_schema.MIGRATION_ID, m_001_initial_schema.UP_SQL, m_001_initial_schema.DOWN_SQL),
    (m_002_add_orientation_attachments.MIGRATION_ID, m_002_add_orientation_attachments.UP_SQL, m_002_add_orientation_attachments.DOWN_SQL),
    (m_003_add_report_templates.MIGRATION_ID, m_003_add_report_templates.UP_SQL, m_003_add_report_templates.DOWN_SQL),
    (m_004_add_user_profiles.MIGRATION_ID, m_004_add_user_profiles.UP_SQL, m_004_add_user_profiles.DOWN_SQL),
    (m_005_add_wellness_challenges.MIGRATION_ID, m_005_add_wellness_challenges.UP_SQL, m_005_add_wellness_challenges.DOWN_SQL),
    (m_006_add_goals_and_progress.MIGRATION_ID, m_006_add_goals_and_progress.UP_SQL, m_006_add_goals_and_progress.DOWN_SQL),
    (m_007_add_shared_clinical_data.MIGRATION_ID, m_007_add_shared_clinical_data.UP_SQL, m_007_add_shared_clinical_data.DOWN_SQL),
    (m_008_add_interventions.MIGRATION_ID, m_008_add_interventions.UP_SQL, m_008_add_interventions.DOWN_SQL),
    (m_009_add_minigame_block_log.MIGRATION_ID, m_009_add_minigame_block_log.UP_SQL, m_009_add_minigame_block_log.DOWN_SQL),
    (m_010_add_notifications.MIGRATION_ID, m_010_add_notifications.UP_SQL, m_010_add_notifications.DOWN_SQL),
]


def get_db_path() -> str:
    base_dir = get_project_root()
    return f"{base_dir}/config/ser_pleno_local.db"


def list_migrations(db_path: str) -> None:
    applied = get_applied_migrations(db_path)
    all_ids = [m[0] for m in MIGRATIONS]
    pending = [m for m in MIGRATIONS if m[0] not in applied]
    print(f"Applied migrations ({len(applied)}):")
    for migration_id in applied:
        status = "OK" if migration_id in all_ids else "UNKNOWN"
        print(f"  {migration_id} [{status}]")
    print(f"\nPending migrations ({len(pending)}):")
    for migration_id, _up_sql, _down_sql in pending:
        print(f"  {migration_id}")


def apply_pending(db_path: str) -> None:
    applied = get_applied_migrations(db_path)
    pending = [m for m in MIGRATIONS if m[0] not in applied]
    if not pending:
        print("No pending migrations.")
        return
    print(f"Applying {len(pending)} migration(s)...")
    for migration_id, up_sql, _down_sql in pending:
        apply_migration(db_path, migration_id, up_sql)
        print(f"  Applied {migration_id}")
    print("Done.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage local SQLite migrations.")
    parser.add_argument("--apply", action="store_true", help="Apply pending migrations")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db_path = get_db_path()
    if args.apply:
        apply_pending(db_path)
    else:
        list_migrations(db_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Add shared_clinical_data table."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS shared_clinical_data (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    shared_by_id INTEGER,
    shared_with_user_id INTEGER,
    shared_with_role TEXT,
    data_type TEXT,
    created_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS shared_clinical_data;
"""

MIGRATION_ID = "007_add_shared_clinical_data"

"""Add orientation_attachments table."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS orientation_attachments (
    id INTEGER PRIMARY KEY,
    orientation_id INTEGER,
    file_name TEXT,
    file_path TEXT,
    file_type TEXT,
    file_size INTEGER,
    created_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS orientation_attachments;
"""

MIGRATION_ID = "002_add_orientation_attachments"

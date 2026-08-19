"""Add documents table."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    name TEXT,
    document_type TEXT,
    file_path TEXT,
    file_size INTEGER,
    uploaded_by_id INTEGER,
    student_id INTEGER,
    description TEXT,
    expires_at TEXT,
    is_public INTEGER DEFAULT 0,
    uploaded_at TEXT,
    updated_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS documents;
"""

MIGRATION_ID = "011_add_documents"

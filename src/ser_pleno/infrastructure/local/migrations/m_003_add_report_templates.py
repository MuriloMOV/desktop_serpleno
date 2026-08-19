"""Add report_templates table."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS report_templates (
    id INTEGER PRIMARY KEY,
    name TEXT,
    report_type TEXT,
    template_config TEXT,
    default_parameters TEXT,
    is_active INTEGER DEFAULT 1,
    created_by_id INTEGER,
    created_at TEXT,
    updated_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS report_templates;
"""

MIGRATION_ID = "003_add_report_templates"

"""Add interventions table."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    conducted_by_id INTEGER,
    date TEXT,
    intervention_type TEXT,
    duration_minutes INTEGER,
    intervention_notes TEXT,
    outcome TEXT DEFAULT 'pending',
    outcome_notes TEXT,
    follow_up_required INTEGER DEFAULT 0,
    follow_up_date TEXT,
    follow_up_completed INTEGER DEFAULT 0,
    is_confidential INTEGER DEFAULT 0,
    tags TEXT DEFAULT '[]',
    updated_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS interventions;
"""

MIGRATION_ID = "008_add_interventions"

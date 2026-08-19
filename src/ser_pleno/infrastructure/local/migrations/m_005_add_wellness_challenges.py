"""Add wellness_challenges and wellness_challenge_assignments tables."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS wellness_challenges (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    category TEXT,
    difficulty TEXT,
    points INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS wellness_challenge_assignments (
    id INTEGER PRIMARY KEY,
    challenge_id INTEGER,
    student_id INTEGER,
    assigned_by_id INTEGER,
    status TEXT DEFAULT 'assigned',
    assigned_at TEXT,
    completed_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS wellness_challenge_assignments;
DROP TABLE IF EXISTS wellness_challenges;
"""

MIGRATION_ID = "005_add_wellness_challenges"

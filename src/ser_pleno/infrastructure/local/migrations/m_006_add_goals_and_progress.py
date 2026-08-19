"""Add goals and goal_progress tables."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    title TEXT,
    description TEXT,
    category TEXT,
    target_value REAL,
    current_value REAL DEFAULT 0,
    unit TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT DEFAULT 'active',
    created_by_id INTEGER,
    created_at TEXT,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS goal_progress (
    id INTEGER PRIMARY KEY,
    goal_id INTEGER,
    student_id INTEGER,
    value REAL,
    notes TEXT,
    recorded_by_id INTEGER,
    recorded_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS goal_progress;
DROP TABLE IF EXISTS goals;
"""

MIGRATION_ID = "006_add_goals_and_progress"

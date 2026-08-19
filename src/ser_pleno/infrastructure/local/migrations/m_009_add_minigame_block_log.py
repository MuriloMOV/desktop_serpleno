"""Add minigame_block_logs table."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS minigame_block_logs (
    id INTEGER PRIMARY KEY,
    student_id INTEGER,
    block_type TEXT,
    reason TEXT,
    blocked_by_id INTEGER,
    blocked_at TEXT,
    unblocked_at TEXT,
    notes TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS minigame_block_logs;
"""

MIGRATION_ID = "009_add_minigame_block_log"

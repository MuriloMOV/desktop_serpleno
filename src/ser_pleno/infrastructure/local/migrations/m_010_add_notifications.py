"""Add notifications table."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    message TEXT,
    notification_type TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TEXT,
    read_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS notifications;
"""

MIGRATION_ID = "010_add_notifications"

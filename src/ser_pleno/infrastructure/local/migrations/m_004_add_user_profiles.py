"""Add user_profiles table."""

from __future__ import annotations

UP_SQL = """
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY,
    role TEXT DEFAULT 'visitante',
    permissions TEXT DEFAULT '[]',
    is_active_profile INTEGER DEFAULT 1,
    updated_at TEXT
);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS user_profiles;
"""

MIGRATION_ID = "004_add_user_profiles"

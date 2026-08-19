# -*- coding: utf-8 -*-
"""Management command: remove old audit logs."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from ser_pleno.repositories.base import fetch_all, execute_non_query

logger = logging.getLogger(__name__)


def cleanup_audit_logs(days: int = 90, dry_run: bool = False) -> dict:
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    rows = fetch_all(
        "SELECT id, created_at FROM audit_log WHERE created_at < %s",
        (cutoff_str,),
    )
    if not rows:
        return {"deleted": 0, "dry_run": dry_run}

    ids = [r.get("id") for r in rows if r.get("id") is not None]
    if not ids:
        return {"deleted": 0, "dry_run": dry_run}

    if dry_run:
        return {"deleted": len(ids), "dry_run": dry_run}

    placeholders = ",".join(["%s"] * len(ids))
    execute_non_query(
        f"DELETE FROM audit_log WHERE id IN ({placeholders})",
        tuple(ids),
    )
    return {"deleted": len(ids), "dry_run": dry_run}

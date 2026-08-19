# -*- coding: utf-8 -*-
"""Management command: remove orphan files from filesystem."""

from __future__ import annotations

import logging
import os
from typing import List, Set

from ser_pleno.config.paths import get_project_root
from ser_pleno.repositories.base import fetch_all

logger = logging.getLogger(__name__)


def _collect_referenced_paths() -> Set[str]:
    referenced: Set[str] = set()

    rows = fetch_all("SELECT file FROM desktop_orientation_attachment WHERE file IS NOT NULL")
    for r in rows:
        path = r.get("file")
        if path:
            referenced.add(os.path.normpath(path))

    rows = fetch_all("SELECT caminho_arquivo FROM desktop_message WHERE caminho_arquivo IS NOT NULL")
    for r in rows:
        path = r.get("caminho_arquivo")
        if path:
            referenced.add(os.path.normpath(path))

    rows = fetch_all("SELECT file_path FROM desktop_report WHERE file_path IS NOT NULL")
    for r in rows:
        path = r.get("file_path")
        if path:
            referenced.add(os.path.normpath(path))

    return referenced


def cleanup_orphan_files(dry_run: bool = False) -> dict:
    base_dir = get_project_root()
    uploads_dir = os.path.join(base_dir, "uploads")
    if not os.path.isdir(uploads_dir):
        return {"scanned": 0, "removed": 0, "dry_run": dry_run}

    referenced = _collect_referenced_paths()
    orphan_paths: List[str] = []

    for root, _, files in os.walk(uploads_dir):
        for name in files:
            abs_path = os.path.normpath(os.path.join(root, name))
            if abs_path not in referenced:
                orphan_paths.append(abs_path)

    if dry_run:
        return {"scanned": len(orphan_paths), "removed": 0, "dry_run": dry_run}

    removed = 0
    for path in orphan_paths:
        try:
            os.remove(path)
            removed += 1
        except Exception as exc:
            logger.error("Falha ao remover arquivo orfao %s: %s", path, exc)

    return {"scanned": len(orphan_paths), "removed": removed, "dry_run": dry_run}

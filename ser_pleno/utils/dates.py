# -*- coding: utf-8 -*-
"""Conversão e formatação de datas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional


def parse_datetime(value) -> Optional[datetime]:
    if hasattr(value, "strftime"):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def format_date(value, fmt: str = "%Y-%m-%d") -> Optional[str]:
    dt = parse_datetime(value)
    return dt.strftime(fmt) if dt else None


def format_br_date(value) -> Optional[str]:
    return format_date(value, "%d/%m/%Y")

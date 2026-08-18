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


def parse_br_date(value: str) -> Optional[str]:
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value:
        return None
    parts = value.split("/")
    if len(parts) != 3:
        return None
    try:
        d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        date(y, m, d)
        return f"{y:04d}-{m:02d}-{d:02d}"
    except (ValueError, TypeError):
        return None


def normalize_date(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Data inválida")
    value = value.strip()
    if not value:
        raise ValueError("Data inválida")
    if len(value) == 10 and value[4] == "-" and value[7] == "-":
        try:
            date.fromisoformat(value)
            return value
        except ValueError:
            raise ValueError("Data inválida")
    result = parse_br_date(value)
    if result is None:
        raise ValueError("Data inválida")
    return result


def format_date(value, fmt: str = "%Y-%m-%d") -> Optional[str]:
    dt = parse_datetime(value)
    return dt.strftime(fmt) if dt else None


def format_br_date(value) -> Optional[str]:
    return format_date(value, "%d/%m/%Y")

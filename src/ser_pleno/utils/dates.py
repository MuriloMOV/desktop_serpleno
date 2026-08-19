"""Conversão e formatação de datas."""

from __future__ import annotations

from datetime import date, datetime


def parse_datetime(value) -> datetime | None:
    if hasattr(value, "strftime"):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None


def parse_br_date(value: str) -> str | None:
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


def normalize_datetime(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Data/hora inválida")
    value = value.strip()
    if not value:
        raise ValueError("Data/hora inválida")
    if len(value) >= 16 and value[4] == "-" and value[7] == "-":
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                datetime.strptime(value, fmt)
                return value[:16] if fmt == "%Y-%m-%d %H:%M:%S" else value
            except ValueError:
                continue
    parts = value.split(" ")
    if len(parts) == 2:
        date_part, time_part = parts
        normalized_date = parse_br_date(date_part)
        if normalized_date:
            return f"{normalized_date} {time_part}"
    normalized_date = parse_br_date(value)
    if normalized_date:
        return f"{normalized_date} 00:00"
    raise ValueError("Data/hora inválida")


def format_date(value, fmt: str = "%Y-%m-%d") -> str | None:
    dt = parse_datetime(value)
    return dt.strftime(fmt) if dt else None


def format_br_date(value) -> str | None:
    return format_date(value, "%d/%m/%Y")

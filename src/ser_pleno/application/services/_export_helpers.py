from __future__ import annotations

import re
from datetime import date, datetime

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
_MULTIPLE_UNDERSCORES = re.compile(r"_+")


def format_date_for_export(date_value: date | datetime | str | None) -> str:
    if date_value is None:
        return ""
    if isinstance(date_value, str):
        return date_value
    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d %H:%M:%S")
    return date_value.strftime("%Y-%m-%d")


def format_number_for_export(number: int | float | None, decimals: int = 2) -> str:
    if number is None:
        return ""
    return f"{float(number):.{decimals}f}"


def sanitize_filename(filename: str) -> str:
    base = _UNSAFE_FILENAME_CHARS.sub("_", filename)
    base = _MULTIPLE_UNDERSCORES.sub("_", base).strip("_")
    return base or "arquivo"

# -*- coding: utf-8 -*-
"""Utils de mapeamento genéricos — sem domínio específico."""

from __future__ import annotations


def safe_str(value, fallback: str = "") -> str:
    """Converte valor para string com fallback."""
    if value is None:
        return fallback
    return str(value)


def safe_bool(value) -> bool:
    """Converte valor para boolean de forma segura."""
    return bool(value)


def map_row(row: dict, mapping: dict) -> dict:
    """Mapeia um row do banco para dict usando {dest: (src, transform_fn | None)}."""
    result = {}
    for dest, spec in mapping.items():
        if isinstance(spec, tuple):
            src, transform = spec
            val = row.get(src)
            result[dest] = transform(val) if transform else val
        else:
            result[dest] = row.get(spec)
    return result

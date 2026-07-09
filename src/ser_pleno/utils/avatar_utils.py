# -*- coding: utf-8 -*-
"""Utilitários centralizados para avatares —” elimina duplicação de palette e hash."""

from __future__ import annotations

from ser_pleno.ui.theme import THEME

# Palette baseada em tokens do tema para consistência visual entre views.
_AVATAR_PALETTE = [
    THEME["kpi_blue"],
    THEME["kpi_violet"],
    THEME["kpi_green"],
    THEME["kpi_amber"],
    THEME["kpi_red"],
    THEME["info"],
]


def get_avatar_color(name: str) -> str:
    """Retorna cor de avatar consistente para um nome, usando palette do tema."""
    idx = sum(ord(c) for c in (name or "")) % len(_AVATAR_PALETTE)
    return _AVATAR_PALETTE[idx]


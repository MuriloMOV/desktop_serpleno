# -*- coding: utf-8 -*-
"""Cores semânticas e utilitários de manipulação de cor."""

from __future__ import annotations

import colorsys
from typing import Tuple


def _hex_to_rgb(hex_c: str) -> Tuple[int, int, int]:
    hex_c = hex_c.lstrip("#")
    return int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def blend_color(hex_c: str, alpha: float, base: str | None = None) -> str:
    """Mistura hex_c sobre `base` (padrão: fundo de superfície do tema ativo)
    com a opacidade `alpha`.
    """
    from ser_pleno.ui.theme import get_theme
    base = base or get_theme()["surface"]
    r, g, b = _hex_to_rgb(hex_c)
    br, bg, bb = _hex_to_rgb(base)
    return _rgb_to_hex(
        int(r * alpha + br * (1 - alpha)),
        int(g * alpha + bg * (1 - alpha)),
        int(b * alpha + bb * (1 - alpha)),
    )


def darken(hex_c: str, amount: float = 0.15) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    return _rgb_to_hex(int(r * (1 - amount)), int(g * (1 - amount)), int(b * (1 - amount)))


def lighten(hex_c: str, amount: float = 0.15) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    return _rgb_to_hex(
        int(r + (255 - r) * amount),
        int(g + (255 - g) * amount),
        int(b + (255 - b) * amount),
    )


def shift_hue(hex_c: str, degrees: float) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + degrees / 360) % 1.0
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
    return _rgb_to_hex(int(r2 * 255), int(g2 * 255), int(b2 * 255))


def readable_text_color(bg_hex: str) -> str:
    """Retorna preto ou branco, o que tiver melhor contraste sobre bg_hex."""
    r, g, b = _hex_to_rgb(bg_hex)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#14162B" if luminance > 0.6 else "#FFFFFF"


# ——————————————————————————————————————————————————————————————————————————
#  Constantes semânticas usadas pelas views
# ——————————————————————————————————————————————————————————————————————————
SEMANTIC_COLORS = {
    "positive": "#10B981",
    "negative": "#EF4444",
    "neutral":  "#6366F1",
    "caution":  "#F59E0B",
    "info":     "#3B82F6",
}

STATUS_COLORS = {
    "active":   "#10B981",
    "inactive": "#94A3B8",
    "pending":  "#F59E0B",
    "blocked":  "#EF4444",
    "review":   "#6366F1",
}

PRIORITY_COLORS = {
    "Urgente": ("critico", "critico_soft"),
    "Alta":    ("alto",    "alto_soft"),
    "Média":   ("medio",   "medio_soft"),
    "Baixa":   ("normal",  "normal_soft"),
}

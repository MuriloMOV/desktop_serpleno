# -*- coding: utf-8 -*-
"""Tipografia e animações do SerPleno."""

from __future__ import annotations

import platform
from typing import Literal

import customtkinter as ctk

# ——————————————————————————————————————————————————————————————————————————
#  Família de fonte
# ——————————————————————————————————————————————————————————————————————————
_PLATFORM = platform.system()
if _PLATFORM == "Windows":
    FONT_FAMILY = "Segoe UI"
elif _PLATFORM == "Darwin":
    FONT_FAMILY = "Helvetica Neue"
else:
    FONT_FAMILY = "Inter"

FONT_FAMILY_MONO = "JetBrains Mono"


# ——————————————————————————————————————————————————————————————————————————
#  Tamanhos de fonte (escala tipográfica)
# ——————————————————————————————————————————————————————————————————————————
TYPO = {
    "display": 36,
    "h1": 30,
    "h2": 24,
    "h3": 18,
    "h4": 16,
    "body": 14,
    "body_sm": 13,
    "caption": 12,
    "overline": 10,
    "button": 14,
}


# ——————————————————————————————————————————————————————————————————————————
#  Animações
# ——————————————————————————————————————————————————————————————————————————
ANIMATION = {
    "duration_fast": 150,
    "duration_normal": 250,
    "duration_slow": 400,
    "easing": "ease-in-out",
}


# ——————————————————————————————————————————————————————————————————————————
#  Cache de fontes
# ——————————————————————————————————————————————————————————————————————————
_FONT_CACHE: dict[tuple[str, int, str], ctk.CTkFont] = {}


def _clear_font_cache(_mode: str) -> None:
    """Limpa cache de fontes quando o tema muda."""
    _FONT_CACHE.clear()


def _register_font_cache_clear() -> None:
    """Registra limpeza de cache de fontes nos listeners de tema."""
    try:
        from ser_pleno.ui.theme import on_theme_change
        on_theme_change(_clear_font_cache)
    except Exception:
        pass


_register_font_cache_clear()


# ——————————————————————————————————————————————————————————————————————————
#  Helpers de fonte
# ——————————————————————————————————————————————————————————————————————————
def font(
    size: int = 14,
    weight: Literal["normal", "bold"] = "normal",
    family: str = FONT_FAMILY,
) -> ctk.CTkFont:
    key = (family, size, weight)
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached
    fnt = ctk.CTkFont(family=family, size=size, weight=weight)
    _FONT_CACHE[key] = fnt
    return fnt


def themed_font(
    role: Literal["display", "h1", "h2", "h3", "h4", "body", "body_sm", "caption", "overline", "button"],
    weight: Literal["normal", "bold"] = "normal",
) -> ctk.CTkFont:
    key = (FONT_FAMILY, TYPO[role], weight)
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached
    fnt = ctk.CTkFont(family=FONT_FAMILY, size=TYPO[role], weight=weight)
    _FONT_CACHE[key] = fnt
    return fnt


def mono_font(size: int = 12) -> ctk.CTkFont:
    key = (FONT_FAMILY_MONO, size, "normal")
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached
    fnt = ctk.CTkFont(family=FONT_FAMILY_MONO, size=size)
    _FONT_CACHE[key] = fnt
    return fnt

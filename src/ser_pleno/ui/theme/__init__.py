# -*- coding: utf-8 -*-
"""Design System do SerPleno — ponto de entrada único.

Mantém 100% de compatibilidade de chaves com o restante da aplicação
(nenhuma chave de THEME/SPACING/RADIUS/TYPO foi removida ou renomeada).

Nova estrutura modular:
- ``ser_pleno.ui.theme.palette`` — LIGHT_THEME e DARK_THEME
- ``ser_pleno.ui.theme.typography`` — FONT_FAMILY, TYPO, font(), themed_font()
- ``ser_pleno.ui.theme.spacing`` — SPACING, RADIUS, ELEVATION
- ``ser_pleno.ui.theme.colors`` — utilitários de cor e constantes semânticas
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Literal

import customtkinter as ctk

from ser_pleno.ui.theme.palette import DARK_THEME, LIGHT_THEME
from ser_pleno.ui.theme.typography import (
    ANIMATION,
    FONT_FAMILY,
    FONT_FAMILY_MONO,
    TYPO,
    font,
    mono_font,
    themed_font,
)
from ser_pleno.ui.theme.spacing import ELEVATION, RADIUS, SPACING
from ser_pleno.ui.theme.colors import (
    PRIORITY_COLORS,
    SEMANTIC_COLORS,
    STATUS_COLORS,
    blend_color,
    darken,
    lighten,
    readable_text_color,
    shift_hue,
)

__all__ = [
    "LIGHT_THEME",
    "DARK_THEME",
    "THEME",
    "FONT_FAMILY",
    "FONT_FAMILY_MONO",
    "TYPO",
    "ANIMATION",
    "SPACING",
    "RADIUS",
    "ELEVATION",
    "SEMANTIC_COLORS",
    "STATUS_COLORS",
    "PRIORITY_COLORS",
    "font",
    "themed_font",
    "mono_font",
    "blend_color",
    "darken",
    "lighten",
    "shift_hue",
    "readable_text_color",
    "get_theme",
    "current",
    "get_mode",
    "on_theme_change",
    "off_theme_change",
    "set_mode",
    "toggle_mode",
    "apply_global_style",
]

logger = logging.getLogger(__name__)

# ——————————————————————————————————————————————————————————————————————————
#  Estado do tema ativo + listeners
# ——————————————————————————————————————————————————————————————————————————
THEME = LIGHT_THEME.copy()
_current_mode: Literal["light", "dark"] = "light"
_LISTENERS: list[Callable[[str], None]] = []
_listeners_lock = threading.Lock()


def get_theme() -> dict:
    """Retorna o dicionário do tema ativo (mesma referência de THEME)."""
    return THEME


def current() -> dict:
    """Alias explícito de get_theme(), preferível em código novo:
    sempre lê o tema *atual*, mesmo se chamado bem depois de um toggle.
    """
    return THEME


def get_mode() -> str:
    return _current_mode


def on_theme_change(callback: Callable[[str], None]) -> None:
    """Registra um callback chamado com o novo modo ('light'/'dark')
    sempre que o tema mudar.
    """
    with _listeners_lock:
        if callback not in _LISTENERS:
            _LISTENERS.append(callback)


def off_theme_change(callback: Callable[[str], None]) -> None:
    with _listeners_lock:
        if callback in _LISTENERS:
            _LISTENERS.remove(callback)


def set_mode(mode: Literal["light", "dark"]) -> None:
    global _current_mode, THEME
    if mode not in ("light", "dark"):
        mode = "light"
    _current_mode = mode
    THEME.clear()
    THEME.update(LIGHT_THEME if mode == "light" else DARK_THEME)
    try:
        ctk.set_appearance_mode(mode)
    except Exception:
        pass
    with _listeners_lock:
        listeners = list(_LISTENERS)
    for cb in listeners:
        try:
            cb(mode)
        except Exception:
            pass


def toggle_mode() -> str:
    new_mode = "dark" if _current_mode == "light" else "light"
    set_mode(new_mode)
    return new_mode


def apply_global_style(mode: Literal["light", "dark"] = "light", color_theme: str = "blue") -> None:
    """Aplica aparência global e valores padrão sensatos para o app."""
    try:
        ctk.set_default_color_theme(color_theme)
    except Exception:
        pass
    set_mode(mode)

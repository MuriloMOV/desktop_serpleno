"""
Theme extensions —” permite que features tenham tokens específicos
herdando do THEME global, sem redefinir dicionários completos.

Usage:
    from ser_pleno.ui.theme_extensions import extend_theme, sp
    from ser_pleno.ui.theme import THEME

    MY_TOKENS = extend_theme(THEME, {
        "card_bg":    "#FFFFFF",
        "card_radius": 16,
        # apenas o que difere do global
    })

    # Usar:
    bg = MY_TOKENS["card_bg"]   # -> "#FFFFFF"
    # fallback automático para THEME["card_bg"] se não definido
"""

from __future__ import annotations

from ser_pleno.ui.theme import SPACING as _SPACING, THEME as _GLOBAL_THEME


def extend_theme(base: dict, overrides: dict) -> dict:
    """Retorna novo dict mesclando base + overrides, sem mutar o original."""
    merged = dict(base)
    merged.update(overrides)
    return merged


def sp(key: str, delta: int = 0) -> int:
    """Atalho para valores de SPACING com delta opcional."""
    return max(0, _SPACING.get(key, 0) + delta)


# Agrupamentos comuns para reduzir magic numbers em views
_SPACING_HELPERS = {
    "page": lambda: sp("page_x"),
    "page_y": lambda: sp("page_y"),
    "section": lambda: sp("section_gap"),
    "card": lambda: sp("card_pad"),
    "item_gap": lambda: sp("item_gap"),
    "item": lambda: sp("item_gap"),
    "grid": lambda: sp("grid_gap"),
    "icon": lambda: sp("icon_gap"),
    "input": lambda: sp("input_y"),
    "label": lambda: sp("label_gap"),
    "button_x": lambda: sp("button_pad_x"),
    "button_y": lambda: sp("button_pad_y"),
    "xs": lambda: 4,
    "sm": lambda: 8,
    "md": lambda: 12,
    "lg": lambda: 16,
    "xl": lambda: 20,
    "xxl": lambda: 24,
    "modal": lambda: 28,
    "half_grid": lambda: sp("grid_gap") // 2,
    "label_gap": lambda: sp("label_gap"),
    "icon_gap": lambda: sp("icon_gap"),
    "button_x": lambda: sp("button_pad_x"),
    "button_y": lambda: sp("button_pad_y"),
}


def spacing(name: str) -> int:
    """Retorna um atalho de espaçamento predefinido pelo nome."""
    fn = _SPACING_HELPERS.get(name)
    if fn is None:
        raise KeyError(f"Spacing '{name}' não encontrado em theme_extensions.spacing()")
    return fn()


"""
Theme extensions — permite que features tenham tokens específicos
herdando do THEME global, sem redefinir dicionários completos.

Usage:
    from ui_theme_extensions import extend_theme
    from ui_theme import THEME

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

from ui_theme import THEME as _GLOBAL_THEME


def extend_theme(base: dict, overrides: dict) -> dict:
    """Retorna novo dict mesclando base + overrides, sem mutar o original."""
    merged = dict(base)
    merged.update(overrides)
    return merged

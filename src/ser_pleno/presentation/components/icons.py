"""Centralized icon definitions and reusable icon widgets.

All icons used across the application should be referenced from ``ICONS``
instead of hardcoding emoji strings in view files. This makes it trivial to
swap emoji → SVG/PNG later without touching every view.

Esta camada é uma ponte de compatibilidade: o dicionário ``ICONS`` e os
helpers ``MOOD_*`` são reexportados de ``ser_pleno.ui.components.icons``,
que é a fonte única da verdade. As classes de widget permanecem aqui para
não quebrar importações existentes nas views.
"""

from __future__ import annotations

from typing import Optional, Literal

import customtkinter as ctk

from ser_pleno.ui.components.icons import (
    ICONS,
    MOOD_EMOJIS,
    MOOD_COLORS,
    MOOD_LABELS,
    get_icon,
    icon_text,
    IconBadge,
    IconButton,
)
from ser_pleno.ui.theme import themed_font, RADIUS, THEME, blend_color, font


# ---------------------------------------------------------------------------
# Compatibility: keep IconLabel available for existing imports.
# Note: previous IconLabel was a CTkFrame with a background; now it is a
# CTkLabel for true inline behavior. Views can migrate to IconLabel from
# ui.components.icons when convenient.
# ---------------------------------------------------------------------------
class IconLabel(ctk.CTkFrame):
    """Icon rendered inside a rounded/circular background frame (legacy API).

    Prefer ``ser_pleno.ui.components.icons.IconLabel`` for new code — it is a
    true ``CTkLabel`` for inline icon+text composition.
    """

    def __init__(
        self,
        parent,
        icon: str,
        size: int = 28,
        fg_color: Optional[str] = None,
        text_color: str = "white",
        corner_radius: Optional[int] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._size = size
        cr = corner_radius if corner_radius is not None else size // 2
        bg = ctk.CTkFrame(
            self,
            width=size,
            height=size,
            corner_radius=cr,
            fg_color=fg_color or "#E5E7EB",
        )
        bg.pack_propagate(False)
        bg.pack()
        ctk.CTkLabel(
            bg,
            text=icon,
            font=themed_font("body"),
            text_color=text_color,
        ).place(relx=0.5, rely=0.5, anchor="center")


__all__ = [
    "ICONS",
    "MOOD_EMOJIS",
    "MOOD_COLORS",
    "MOOD_LABELS",
    "get_icon",
    "icon_text",
    "IconLabel",
    "IconBadge",
    "IconButton",
]

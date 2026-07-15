"""Compatibility module for legacy IconLabel import.

This module exists only to preserve backward compatibility for views that
import ``IconLabel`` from ``ser_pleno.presentation.components.icons``.

The canonical source for icons and icon widgets is now ``ser_pleno.ui.components.icons``.

.. deprecated::
    Import ``IconLabel`` from ``ser_pleno.ui.components.icons`` for new code.
    This module will be removed in a future version after all views migrate.
"""

from __future__ import annotations

import customtkinter as ctk

from ser_pleno.ui.theme import themed_font, font


class IconLabel(ctk.CTkFrame):
    """Icon rendered inside a rounded/circular background frame (legacy API).

    Prefer ``ser_pleno.ui.components.icons.IconLabel`` for new code.
    """

    def __init__(
        self,
        parent,
        icon: str = "",
        size: int = 28,
        fg_color: str | None = None,
        text_color: str = "white",
        corner_radius: int | None = None,
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


__all__ = ["IconLabel"]

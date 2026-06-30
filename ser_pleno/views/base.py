# -*- coding: utf-8 -*-
"""Base reutilizável para Views — elimina boilerplate de header e AsyncRunner."""

from __future__ import annotations

import customtkinter as ctk
from typing import Callable, Optional

from utils.async_runner import AsyncRunner
from ui_theme import THEME, SPACING, RADIUS, FONT_FAMILY, font, themed_font
from components.ui_components import PageHeader, Divider, PrimaryButton


class BaseViewFrame(ctk.CTkScrollableFrame):
    """Frame base com header padronizado e helper _load_async."""

    def __init__(
        self,
        parent,
        controller,
        title: str = "",
        subtitle: str = "",
        actions: Optional[list[ctk.CTkButton]] = None,
        show_breadcrumb: bool = False,
        breadcrumb_parts: Optional[list[str]] = None,
        auto_header: bool = True,
        **scroll_kwargs,
    ):
        super().__init__(
            parent,
            fg_color=THEME["bg"],
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
            **scroll_kwargs,
        )
        self.controller = controller
        if auto_header and title:
            self._build_header(title, subtitle, actions, show_breadcrumb, breadcrumb_parts)
        # load_data() deve ser chamado pela view no final de seu __init__
        # para garantir que todos os atributos de instância estejam prontos.

    # ──────────────────────────────────────────────────────────────────────
    #  Header
    # ──────────────────────────────────────────────────────────────────────
    def _build_header(self, title, subtitle, actions, show_breadcrumb, breadcrumb_parts):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 4))

        PageHeader(
            container,
            title=title,
            subtitle=subtitle,
            actions=actions or [],
            show_breadcrumb=show_breadcrumb,
            breadcrumb_parts=breadcrumb_parts,
        ).pack(fill="x")

        Divider(self).pack(
            fill="x", padx=SPACING["page_x"], pady=(SPACING["item_gap"], 0)
        )

    # ──────────────────────────────────────────────────────────────────────
    #  Async loading helper
    # ──────────────────────────────────────────────────────────────────────
    def _load_async(
        self,
        fetch_fn: Callable,
        on_success: Callable,
        on_error: Optional[Callable] = None,
        loading_hook: Optional[Callable] = None,
    ):
        if loading_hook:
            loading_hook()

        def _task():
            return fetch_fn()

        def _ok(result):
            on_success(result)

        def _fail(exc):
            import tkinter.messagebox as mb
            mb.showerror("Erro", f"Não foi possível carregar os dados.\n{exc}")
            if on_error:
                on_error(exc)

        AsyncRunner.run(
            task=_task,
            on_success=_ok,
            on_error=_fail,
            widget_ref=self,
        )

    # ──────────────────────────────────────────────────────────────────────
    #  Stub — views devem implementar
    # ──────────────────────────────────────────────────────────────────────
    def load_data(self):
        raise NotImplementedError

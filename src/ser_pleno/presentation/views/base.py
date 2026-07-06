# -*- coding: utf-8 -*-
"""Base reutilizável para Views — elimina boilerplate de header e carregamento assíncrono."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ser_pleno.utils.async_runner import AsyncRunner
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, FONT_FAMILY, font, themed_font
from ser_pleno.presentation.components.ui_components import PageHeader, Divider, PrimaryButton, GhostButton, BaseModal


class _ErrorModal(BaseModal):
    """Modal de erro tematizado — substitui o tkinter.messagebox nativo,
    que renderiza fora do estilo visual do SerPleno (título do SO, fontes
    do sistema, sem paleta de cores da marca)."""

    def __init__(self, parent, message: str, title: str = "Não foi possível concluir"):
        super().__init__(parent, title="Erro", width=420, height=220)
        self.configure(fg_color=THEME["surface"])

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        icon_box = ctk.CTkFrame(wrapper, fg_color=THEME["danger_soft"], width=52, height=52,
                                 corner_radius=RADIUS["lg"])
        icon_box.pack(pady=(0, 14))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="⚠", font=themed_font("h2"),
                     text_color=THEME["danger"]).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(wrapper, text=title, font=themed_font("h4", "bold"),
                     text_color=THEME["text"]).pack()
        ctk.CTkLabel(wrapper, text=message, font=themed_font("body_sm"),
                     text_color=THEME["text_muted"], wraplength=340, justify="center"
                     ).pack(pady=(6, 18))

        PrimaryButton(wrapper, text="Entendi", width=140, command=self.destroy).pack()
        self.bind("<Return>", lambda e: self.destroy())
        self.after(50, lambda: self.focus_force())


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
        scroll_kwargs.setdefault("fg_color", THEME["bg"])
        scroll_kwargs.setdefault("scrollbar_button_color", THEME["border_strong"])
        scroll_kwargs.setdefault("scrollbar_button_hover_color", THEME["text_muted"])
        super().__init__(parent, **scroll_kwargs)
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

        div = Divider(self)
        div.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["item_gap"], 0))

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
        """Executa `fetch_fn` em segundo plano e entrega o resultado na
        thread principal da UI. Em caso de erro, mostra um modal
        tematizado (em vez do messagebox nativo do sistema operacional)
        e, opcionalmente, delega tratamento adicional para `on_error`.
        """
        if loading_hook:
            loading_hook()

        def _task():
            return fetch_fn()

        def _ok(result):
            if self.winfo_exists():
                on_success(result)

        def _fail(exc):
            if self.winfo_exists():
                self._show_error(f"Não foi possível carregar os dados.\n{exc}")
            if on_error:
                on_error(exc)

        AsyncRunner.run(
            task=_task,
            on_success=_ok,
            on_error=_fail,
            widget_ref=self,
        )

    def _show_error(self, message: str, title: str = "Não foi possível concluir") -> None:
        """Exibe um modal de erro tematizado ancorado na janela principal."""
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            # Fallback defensivo — nunca deixa um erro silencioso nem
            # trava a aplicação caso o modal não possa ser criado.
            import tkinter.messagebox as mb
            mb.showerror("Erro", message)

    # ──────────────────────────────────────────────────────────────────────
    #  Stub — views devem implementar
    # ──────────────────────────────────────────────────────────────────────
    def load_data(self):
        raise NotImplementedError

from __future__ import annotations

import logging
import threading
import time

import customtkinter as ctk

from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font
from ser_pleno.ui.components.icons import ICONS

logger = logging.getLogger(__name__)


TYPE_LABELS = {
    "student": "Estudante",
    "appointment": "Agendamento",
    "screening": "Triagem",
}
TYPE_ICONS = {
    "student": ICONS["users"],
    "appointment": ICONS["calendar"],
    "screening": ICONS["document"],
}
TYPE_COLORS = {
    "student": THEME["primary"],
    "appointment": THEME["success"],
    "screening": THEME["kpi_violet"],
}
TYPE_SOFT = {
    "student": THEME["primary_soft"],
    "appointment": THEME["success_soft"],
    "screening": THEME["kpi_violet_soft"],
}
TYPE_TO_VIEW = {
    "student": "estudantes",
    "appointment": "agenda",
    "screening": "analise",
}


class SearchEntry(ctk.CTkFrame):
    def __init__(self, parent, on_search=None, on_focus=None, on_clear=None):
        super().__init__(parent, fg_color="transparent")
        self._on_search = on_search
        self._on_focus = on_focus
        self._on_clear = on_clear
        self._debounce_after = None
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", self._on_var_change)

        self._entry = ctk.CTkEntry(
            self,
            textvariable=self._search_var,
            placeholder_text="Buscar...",
            font=themed_font("body"),
            fg_color=THEME["surface"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=RADIUS["button"],
            height=40,
        )
        self._entry.pack(side="left", fill="x", expand=True)
        self._entry.bind("<FocusIn>", self._handle_focus_in)
        self._entry.bind("<Return>", self._handle_enter)

        icon_btn = ctk.CTkButton(
            self,
            text=ICONS["search"],
            width=40,
            height=40,
            corner_radius=RADIUS["button"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color="white",
            command=self._trigger_search,
        )
        icon_btn.pack(side="left", padx=(8, 0))

        self._clear_btn = ctk.CTkButton(
            self,
            text=ICONS["close"],
            width=28,
            height=28,
            corner_radius=RADIUS["button"],
            fg_color="transparent",
            hover_color=THEME["bg_alt"],
            text_color=THEME["text_muted"],
            command=self._clear,
        )
        self._clear_btn.place(relx=1.0, rely=0.5, anchor="e", x=-48, y=0)

    def _handle_focus_in(self, event=None):
        if self._on_focus:
            self._on_focus()

    def _handle_enter(self, event=None):
        self._trigger_search()

    def _on_var_change(self, *args):
        value = self._search_var.get()
        if self._clear_btn.winfo_exists():
            if value:
                self._clear_btn.lift()
            else:
                self._clear_btn.lower()
        if self._debounce_after:
            try:
                self.after_cancel(self._debounce_after)
            except Exception:
                pass
        if value.strip():
            self._debounce_after = self.after(280, self._trigger_search)
        else:
            self._trigger_search()

    def _clear(self, event=None):
        self._search_var.set("")
        self._entry.focus_set()
        if self._on_clear:
            self._on_clear()

    def _trigger_search(self, event=None):
        query = self._search_var.get().strip()
        if self._on_search:
            self._on_search(query)

    def focus(self):
        self._entry.focus_set()

    def get_query(self):
        return self._search_var.get().strip()


class SearchDropdown(ctk.CTkFrame):
    def __init__(self, parent, on_select=None, on_close=None):
        super().__init__(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        self._on_select = on_select
        self._on_close = on_close
        self._groups = {}
        self._after_close = None
        self._current_items = []

        self.grid_columnconfigure(0, weight=1)

        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=360,
        )
        self._scroll.grid(row=0, column=0, sticky="nsew", padx=SPACING["card_pad"], pady=SPACING["card_pad"])
        self._scroll.bind("<MouseWheel>", self._on_scroll)

        self.bind("<FocusOut>", self._handle_focus_out)
        self.after(120, self._bind_focus_out)

    def _bind_focus_out(self):
        if self.winfo_exists():
            self.bind("<FocusOut>", self._handle_focus_out)

    def _handle_focus_out(self, event=None):
        if self._after_close:
            try:
                self.after_cancel(self._after_close)
            except Exception:
                pass
        self._after_close = self.after(120, self._close_if_needed)

    def _close_if_needed(self):
        if not self.winfo_exists():
            return
        try:
            focused = self.focus_get()
        except Exception:
            focused = None
        if focused is None or not str(focused).startswith(str(self.winfo_toplevel())):
            self.destroy()
            if self._on_close:
                self._on_close()

    def _on_scroll(self, event):
        return "break"

    def _render_group(self, title, icon, items, accent, soft):
        if not items:
            return
        group_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        group_frame.pack(fill="x", pady=(0, SPACING["item_gap"]))

        header = ctk.CTkFrame(group_frame, fg_color=soft, corner_radius=RADIUS["button"])
        header.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            header,
            text=f"{icon}  {title}",
            font=themed_font("caption", "bold"),
            text_color=accent,
        ).pack(anchor="w", padx=SPACING["card_pad"], pady=6)

        for item in items[:8]:
            row = ctk.CTkFrame(group_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            name = item.get("name") or item.get("student_name") or "(sem nome)"
            detail = item.get("detail") or item.get("status") or item.get("form_name") or ""
            text = name
            if detail:
                text = f"{name} — {detail}"

            lbl = ctk.CTkLabel(
                row,
                text=text,
                font=themed_font("body"),
                text_color=THEME["text"],
                anchor="w",
                wraplength=340,
            )
            lbl.pack(side="left", fill="x", expand=True, padx=(SPACING["card_pad"], 0), pady=4)

            bind_clickable(row, lambda item=item: self._select(item))
            bind_clickable(lbl, lambda item=item: self._select(item))

    def render(self, results: dict):
        for child in self._scroll.winfo_children():
            child.destroy()

        order = [
            ("students", "Estudantes", TYPE_ICONS["student"], TYPE_COLORS["student"], TYPE_SOFT["student"]),
            ("appointments", "Agendamentos", TYPE_ICONS["appointment"], TYPE_COLORS["appointment"], TYPE_SOFT["appointment"]),
            ("screenings", "Triagens", TYPE_ICONS["screening"], TYPE_COLORS["screening"], TYPE_SOFT["screening"]),
        ]
        for key, label, icon, accent, soft in order:
            items = results.get(key, []) if isinstance(results, dict) else []
            self._render_group(label, icon, items, accent, soft)

        total = sum(len(results.get(k, [])) for k in ("students", "appointments", "screenings")) if isinstance(results, dict) else 0
        if total == 0:
            ctk.CTkLabel(
                self._scroll,
                text="Nenhum resultado encontrado",
                font=themed_font("body"),
                text_color=THEME["text_muted"],
            ).pack(pady=20, padx=SPACING["card_pad"])

    def _select(self, item):
        if self._on_select:
            self._on_select(item)
        try:
            self.destroy()
        except Exception:
            pass


def bind_clickable(widget, callback):
    widget.bind("<Enter>", lambda e: widget.configure(cursor="hand2"))
    widget.bind("<Leave>", lambda e: widget.configure(cursor=""))
    widget.bind("<Button-1>", lambda e: callback())

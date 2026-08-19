# -*- coding: utf-8 -*-
"""View de Audit Logs."""

from __future__ import annotations

import csv
import io
import logging
import time
from datetime import date, datetime, timedelta

import customtkinter as ctk
from tkinter import filedialog

from ser_pleno.features.audit_logs.service import ServicoAuditLogs
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, themed_font, FONT_FAMILY
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.ui.components.ui_components import (
    Card, PrimaryButton, GhostButton, DangerButton,
    Divider, Badge, Pill, EmptyState, SkeletonLoader,
    SearchField, bind_clickable, BaseModal, PageHeader,
)
from ser_pleno.ui.views.base import BaseViewFrame, _ErrorModal
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger(__name__)

ACTION_COLORS = {
    "CREATE": THEME["success"],
    "UPDATE": THEME["info"],
    "DELETE": THEME["danger"],
    "LOGIN": THEME["primary"],
    "LOGOUT": THEME["text_muted"],
    "VIEW": THEME["text_secondary"],
    "EXPORT": THEME["warning"],
    "IMPORT": THEME["warning"],
}

ACTION_ICONS = {
    "CREATE": ICONS["add"],
    "UPDATE": ICONS["edit"],
    "DELETE": ICONS["delete"],
    "LOGIN": ICONS["lock"],
    "LOGOUT": ICONS["lock"],
    "VIEW": ICONS["view"],
    "EXPORT": ICONS["export"],
    "IMPORT": ICONS["import"],
}

CRITICAL_ACTIONS = {"DELETE", "EXPORT", "IMPORT", "LOGOUT"}


class _StatCard(ctk.CTkFrame):
    def __init__(self, parent, title: str, value: str, icon: str = "", accent: str | None = None):
        super().__init__(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
        )
        self.accent = accent or THEME["primary"]
        self._build(title, value, icon)

    def _build(self, title, value, icon):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["card_pad"])

        ctk.CTkLabel(content, text=title, font=themed_font("body_sm"),
                     text_color=THEME["text_muted"]).pack(anchor="w")

        value_frame = ctk.CTkFrame(content, fg_color="transparent")
        value_frame.pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(value_frame, text=value, font=themed_font("h2", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        if icon:
            icon_bg = ctk.CTkFrame(content, fg_color=THEME["primary_soft"],
                                   width=36, height=36, corner_radius=RADIUS["button"])
            icon_bg.place(relx=1.0, x=-SPACING["card_pad"], y=SPACING["card_pad"])
            icon_bg.pack_propagate(False)
            ctk.CTkLabel(icon_bg, text=icon, font=themed_font("h3"),
                         text_color=THEME["primary"]).place(relx=0.5, rely=0.5, anchor="center")


class _LogRow(ctk.CTkFrame):
    def __init__(self, parent, log: dict, on_click=None):
        super().__init__(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        self._log = log
        self._on_click = on_click
        self._build()

    def _build(self):
        action = (self._log.get("action") or "VIEW").upper()
        is_critical = action in CRITICAL_ACTIONS
        action_color = ACTION_COLORS.get(action, THEME["text_secondary"])
        action_icon = ACTION_ICONS.get(action, ICONS["info"])

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("md"), pady=spacing("sm"))
        inner.grid_columnconfigure(1, weight=1)

        icon_bg = ctk.CTkFrame(inner, fg_color=THEME["primary_soft"],
                               width=36, height=36, corner_radius=RADIUS["button"])
        icon_bg.grid(row=0, column=0, rowspan=2, padx=(0, spacing("md")), sticky="ns")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=action_icon, font=themed_font("body"),
                     text_color=action_color).place(relx=0.5, rely=0.5, anchor="center")

        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(title_frame, text=action,
                     font=themed_font("body", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        if is_critical:
            crit_badge = ctk.CTkFrame(inner, fg_color=THEME["danger_soft"],
                                      corner_radius=RADIUS["pill"], height=20)
            crit_badge.grid(row=0, column=2, padx=(spacing("sm"), 0), sticky="ns")
            crit_badge.pack_propagate(False)
            ctk.CTkLabel(crit_badge, text="Crítico", font=themed_font("overline", "bold"),
                         text_color=THEME["danger"]).pack(padx=8, pady=2)

        model = self._log.get("model_name") or "—"
        obj_id = self._log.get("object_id") or "—"
        detail = f"{model} #{obj_id}" if obj_id != "—" else model

        ctk.CTkLabel(inner, text=detail,
                     font=themed_font("caption"),
                     text_color=THEME["text_secondary"], anchor="w").grid(row=1, column=1, sticky="w", pady=(spacing("xs"), 0))

        meta_frame = ctk.CTkFrame(inner, fg_color="transparent")
        meta_frame.grid(row=0, column=3, rowspan=2, padx=(spacing("sm"), 0), sticky="e")

        user = self._log.get("user") or "—"
        ctk.CTkLabel(meta_frame, text=user, font=themed_font("caption"),
                     text_color=THEME["text_muted"]).pack(anchor="e")

        created = self._log.get("created_at") or ""
        ctk.CTkLabel(meta_frame, text=created, font=themed_font("overline"),
                     text_color=THEME["text_muted"]).pack(anchor="e", pady=(spacing("xs"), 0))

        if self._on_click:
            bind_clickable(self, self._on_click)


class AuditLogsFrame(BaseViewFrame):
    def __init__(self, parent, controller):
        self._t0 = time.perf_counter()
        super().__init__(
            parent,
            controller=controller,
            title="Audit Logs",
            subtitle="Rastreabilidade de ações no sistema",
            auto_header=False,
        )
        self.controller = controller
        self.servico_audit = getattr(controller, "servico_audit", None)
        self._logs: list[dict] = []
        self._stats: dict = {}
        self._filtro_after_id = None
        self._current_filters: dict = {}

        self._build_header()
        self._build_layout()
        self.load_data()
        log_view_init_ms("audit_logs", self._t0, widget_ref=self)

    def _build_header(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 4))

        PageHeader(
            container,
            title="Audit Logs",
            subtitle="Rastreabilidade de ações no sistema",
            actions=[
                PrimaryButton(
                    container, text=f"{ICONS['export']}  Exportar",
                    command=self._exportar_logs, height=36, width=140,
                ),
            ],
        ).pack(fill="x")

        Divider(self).pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["item_gap"], 0))

    def _build_layout(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["section_gap"])
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_rowconfigure(1, weight=1)

        self._build_filtros(wrap)
        self._build_estatisticas(wrap)
        self._build_lista(wrap)

    def _build_filtros(self, parent):
        filtro_card = Card(parent, auto_body=False)
        filtro_card.grid(row=0, column=0, sticky="ew", pady=(0, SPACING["item_gap"]))

        header = ctk.CTkFrame(filtro_card, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 0))
        ctk.CTkLabel(header, text=f"{ICONS['search']}  Filtros",
                     font=themed_font("body", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        btn_row = ctk.CTkFrame(filtro_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=SPACING["card_pad"], pady=(spacing("xs"), SPACING["card_pad"]))

        GhostButton(btn_row, text="Limpar filtros", command=self._limpar_filtros,
                    height=32, width=120).pack(side="right")

        body = ctk.CTkFrame(filtro_card, fg_color="transparent")
        body.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        body.grid_columnconfigure((0, 1, 2, 3), weight=1)

        opt_style = dict(
            fg_color=THEME["bg_alt"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["text"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=32, corner_radius=RADIUS["button"],
            font=themed_font("caption"),
        )

        ctk.CTkLabel(body, text="Usuário", font=themed_font("overline", "bold"),
                     text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.f_usuario = ctk.CTkEntry(body, placeholder_text="ID ou nome do usuário",
                                       fg_color=THEME["bg_alt"], border_width=1,
                                       border_color=THEME["border"], font=themed_font("caption"),
                                       height=32)
        self.f_usuario.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkLabel(body, text="Ação", font=themed_font("overline", "bold"),
                     text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.f_acao = ctk.CTkOptionMenu(
            body,
            values=["Todas", "CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "VIEW", "EXPORT", "IMPORT"],
            **opt_style,
        )
        self.f_acao.set("Todas")
        self.f_acao.grid(row=1, column=1, sticky="ew", padx=6)

        ctk.CTkLabel(body, text="Modelo", font=themed_font("overline", "bold"),
                     text_color=THEME["text_secondary"]).grid(row=0, column=2, sticky="w", pady=(0, 4))
        self.f_modelo = ctk.CTkEntry(body, placeholder_text="Nome do modelo",
                                      fg_color=THEME["bg_alt"], border_width=1,
                                      border_color=THEME["border"], font=themed_font("caption"),
                                      height=32)
        self.f_modelo.grid(row=1, column=2, sticky="ew", padx=6)

        ctk.CTkLabel(body, text="Data", font=themed_font("overline", "bold"),
                     text_color=THEME["text_secondary"]).grid(row=0, column=3, sticky="w", pady=(0, 4))
        date_frame = ctk.CTkFrame(body, fg_color="transparent")
        date_frame.grid(row=1, column=3, sticky="ew", padx=(6, 0))
        date_frame.grid_columnconfigure(1, weight=1)

        self.f_data_inicio = ctk.CTkEntry(date_frame, placeholder_text="De",
                                           fg_color=THEME["bg_alt"], border_width=1,
                                           border_color=THEME["border"], font=themed_font("caption"),
                                           height=32)
        self.f_data_inicio.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.f_data_fim = ctk.CTkEntry(date_frame, placeholder_text="Até",
                                        fg_color=THEME["bg_alt"], border_width=1,
                                        border_color=THEME["border"], font=themed_font("caption"),
                                        height=32)
        self.f_data_fim.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.f_usuario.bind("<KeyRelease>", self._on_filtro_change)
        self.f_modelo.bind("<KeyRelease>", self._on_filtro_change)
        self.f_acao.configure(command=lambda _: self._aplicar_filtros())
        self.f_data_inicio.bind("<KeyRelease>", self._on_filtro_change)
        self.f_data_fim.bind("<KeyRelease>", self._on_filtro_change)

    def _build_estatisticas(self, parent):
        self.stats_card = Card(parent, auto_body=False)
        self.stats_card.grid(row=2, column=0, sticky="ew", pady=(0, SPACING["item_gap"]))

        header = ctk.CTkFrame(self.stats_card, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 0))
        ctk.CTkLabel(header, text=f"{ICONS['chart']}  Estatísticas",
                     font=themed_font("body", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        self._stats_body = ctk.CTkFrame(self.stats_card, fg_color="transparent")
        self._stats_body.pack(fill="x", padx=SPACING["card_pad"], pady=(spacing("xs"), SPACING["card_pad"]))

    def _build_lista(self, parent):
        list_card = Card(parent, auto_body=False)
        list_card.grid(row=3, column=0, sticky="nsew")
        parent.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(list_card, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 0))
        ctk.CTkLabel(header, text="Registros",
                     font=themed_font("body", "bold"),
                     text_color=THEME["text"]).pack(side="left")
        self.lbl_count = ctk.CTkLabel(header, text="",
                                      font=themed_font("caption"),
                                      text_color=THEME["text_muted"])
        self.lbl_count.pack(side="right")

        self.scroll_list = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.scroll_list.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=(spacing("xs"), SPACING["card_pad"]))

        self._empty = EmptyState(
            self.scroll_list, icon=ICONS["empty"], title="Sem logs",
            subtitle="Nenhum registro de auditoria encontrado",
        )
        self._empty.pack_forget()

    def load_data(self):
        self._mostrar_skeletons_lista()

        def fetch():
            filtros = self._extrair_filtros()
            logs_data = self.servico_audit.listar_logs(filtros)
            stats_data = self.servico_audit.obter_estatisticas(filtros)
            return logs_data, stats_data

        def on_success(result):
            if not self.winfo_exists():
                return
            logs_data, stats_data = result
            self._stats = stats_data or {}
            if isinstance(logs_data, dict):
                results = logs_data.get("results", [])
                count = logs_data.get("count", len(results))
            elif isinstance(logs_data, list):
                results = logs_data
                count = len(results)
            else:
                results = []
                count = 0
            self._logs = results
            self._renderizar_estatisticas()
            self._renderizar_logs(results, count)

        def on_error(exc):
            if self.winfo_exists():
                self._show_error(f"Não foi possível carregar os logs.\n{exc}")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _extrair_filtros(self):
        filtros = {}
        usuario = self.f_usuario.get().strip() if hasattr(self, "f_usuario") else ""
        if usuario:
            filtros["user"] = usuario
        acao = self.f_acao.get() if hasattr(self, "f_acao") else "Todas"
        if acao and acao != "Todas":
            filtros["action"] = acao
        modelo = self.f_modelo.get().strip() if hasattr(self, "f_modelo") else ""
        if modelo:
            filtros["model_name"] = modelo
        data_inicio = self.f_data_inicio.get().strip() if hasattr(self, "f_data_inicio") else ""
        data_fim = self.f_data_fim.get().strip() if hasattr(self, "f_data_fim") else ""
        if data_inicio:
            filtros["date_from"] = data_inicio
        if data_fim:
            filtros["date_to"] = data_fim
        return filtros

    def _on_filtro_change(self, _=None):
        if self._filtro_after_id:
            self.after_cancel(self._filtro_after_id)
        self._filtro_after_id = self.after(300, self._aplicar_filtros)

    def _aplicar_filtros(self):
        self._current_filters = self._extrair_filtros()
        self.load_data()

    def _limpar_filtros(self):
        if hasattr(self, "f_usuario"):
            self.f_usuario.delete(0, "end")
        if hasattr(self, "f_acao"):
            self.f_acao.set("Todas")
        if hasattr(self, "f_modelo"):
            self.f_modelo.delete(0, "end")
        if hasattr(self, "f_data_inicio"):
            self.f_data_inicio.delete(0, "end")
        if hasattr(self, "f_data_fim"):
            self.f_data_fim.delete(0, "end")
        self._aplicar_filtros()

    def _mostrar_skeletons_lista(self):
        for w in self.scroll_list.winfo_children():
            w.destroy()
        if hasattr(self, "_empty"):
            self._empty.pack_forget()
        batch = WidgetBatchBuilder(parent=self.scroll_list, batch_size=20)
        for _ in range(6):
            batch.add(lambda: SkeletonLoader(self.scroll_list, width=600, height=52, variant="card").pack(
                fill="x", pady=4
            ))
        batch.execute()

    def _renderizar_logs(self, results: list, count: int):
        for w in self.scroll_list.winfo_children():
            w.destroy()
        if hasattr(self, "_empty"):
            self._empty.pack_forget()

        self.lbl_count.configure(text=f"{count} registro{'s' if count != 1 else ''}")

        if not results:
            self._empty = EmptyState(
                self.scroll_list, icon=ICONS["empty"], title="Sem logs",
                subtitle="Nenhum registro de auditoria encontrado para os filtros selecionados",
            )
            self._empty.pack(pady=24)
            return

        batch = WidgetBatchBuilder(parent=self.scroll_list, batch_size=40)
        for log in results:
            batch.add(lambda l=log: _LogRow(self.scroll_list, l, on_click=lambda entry=l: self._detalhar_log(entry)).pack(fill="x", pady=3))
        batch.execute()

    def _detalhar_log(self, log: dict):
        modal = ctk.CTkToplevel(self)
        modal.title("Detalhes do Log")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)
        w, h = 520, 420
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["page_y"])

        ctk.CTkLabel(body, text="Detalhes do Log",
                     font=themed_font("h3", "bold"),
                     text_color=THEME["text"]).pack(anchor="w", pady=(0, spacing("md")))

        fields = [
            ("ID", str(log.get("id") or "—")),
            ("Ação", log.get("action") or "—"),
            ("Modelo", log.get("model_name") or "—"),
            ("Objeto", str(log.get("object_id") or "—")),
            ("Usuário", str(log.get("user") or "—")),
            ("IP", log.get("ip_address") or "—"),
            ("Data", log.get("created_at") or "—"),
            ("User Agent", log.get("user_agent") or "—"),
        ]

        changes = log.get("changes")
        if changes:
            fields.append(("Alterações", str(changes)))

        for label, value in fields:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=spacing("xs"))

            ctk.CTkLabel(row, text=label, width=110, font=themed_font("body", "bold"),
                         text_color=THEME["text_secondary"], anchor="w").pack(side="left")

            ctk.CTkLabel(row, text=value, font=themed_font("body"),
                         text_color=THEME["text"], anchor="w",
                         wraplength=340, justify="left").pack(side="left", fill="x", expand=True)

        GhostButton(body, text="Fechar", command=modal.destroy,
                    width=120, height=36).pack(pady=(spacing("md"), 0), anchor="e")

    def _renderizar_estatisticas(self):
        for w in self._stats_body.winfo_children():
            w.destroy()

        stats = self._stats or {}
        total = stats.get("total", 0)
        today = stats.get("today", {})
        week = stats.get("week", {})
        by_model = stats.get("by_model", {})
        by_user = stats.get("by_user", {})

        total_today = sum(today.values()) if today else 0
        total_week = sum(week.values()) if week else 0

        top_models = sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:3] if by_model else []
        top_users = sorted(by_user.items(), key=lambda x: x[1], reverse=True)[:3] if by_user else []

        stats_row = ctk.CTkFrame(self._stats_body, fg_color="transparent")
        stats_row.pack(fill="x")
        stats_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        cards = [
            ("Total", str(total), ICONS["document"], THEME["primary"]),
            ("Hoje", str(total_today), ICONS["clock"], THEME["success"]),
            ("Semana", str(total_week), ICONS["calendar"], THEME["info"]),
        ]

        if top_models:
            model_label = top_models[0][0] if top_models else "—"
            cards.append(("Top Modelo", model_label, ICONS["layout"], THEME["warning"]))

        for i, (title, value, icon, accent) in enumerate(cards):
            card = _StatCard(stats_row, title=title, value=value, icon=icon, accent=accent)
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2)

        if top_models or top_users:
            detail_frame = ctk.CTkFrame(self._stats_body, fg_color="transparent")
            detail_frame.pack(fill="x", pady=(spacing("md"), 0))
            detail_frame.grid_columnconfigure((0, 1), weight=1)

            if top_models:
                model_card = Card(detail_frame, title="Por Modelo", auto_body=False)
                model_card.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["grid_gap"] // 2))
                model_body = ctk.CTkFrame(model_card, fg_color="transparent")
                model_body.pack(fill="x", padx=SPACING["card_pad"], pady=(spacing("xs"), SPACING["card_pad"]))
                for name, count in top_models:
                    row = ctk.CTkFrame(model_body, fg_color="transparent")
                    row.pack(fill="x", pady=spacing("xs"))
                    ctk.CTkLabel(row, text=name, font=themed_font("body"),
                                 text_color=THEME["text"]).pack(side="left")
                    ctk.CTkLabel(row, text=str(count), font=themed_font("body", "bold"),
                                 text_color=THEME["primary"]).pack(side="right")

            if top_users:
                user_card = Card(detail_frame, title="Por Usuário", auto_body=False)
                user_card.grid(row=0, column=1, sticky="ew", padx=(SPACING["grid_gap"] // 2, 0))
                user_body = ctk.CTkFrame(user_card, fg_color="transparent")
                user_body.pack(fill="x", padx=SPACING["card_pad"], pady=(spacing("xs"), SPACING["card_pad"]))
                for name, count in top_users:
                    row = ctk.CTkFrame(user_body, fg_color="transparent")
                    row.pack(fill="x", pady=spacing("xs"))
                    ctk.CTkLabel(row, text=str(name), font=themed_font("body"),
                                 text_color=THEME["text"]).pack(side="left")
                    ctk.CTkLabel(row, text=str(count), font=themed_font("body", "bold"),
                                 text_color=THEME["primary"]).pack(side="right")

    def _exportar_logs(self):
        if not self._logs:
            self._show_error("Nenhum log disponível para exportação.", title="Exportação indisponível")
            return

        try:
            file_path = filedialog.asksaveasfilename(
                parent=self.winfo_toplevel(),
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
                initialfile=f"audit_logs_{date.today().strftime('%Y%m%d')}.csv",
            )
            if not file_path:
                return

            def write():
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=["id", "user", "action", "model_name", "object_id", "ip_address", "user_agent", "created_at"])
                writer.writeheader()
                for log in self._logs:
                    writer.writerow({
                        "id": log.get("id", ""),
                        "user": log.get("user", ""),
                        "action": log.get("action", ""),
                        "model_name": log.get("model_name", ""),
                        "object_id": log.get("object_id", ""),
                        "ip_address": log.get("ip_address", ""),
                        "user_agent": log.get("user_agent", ""),
                        "created_at": log.get("created_at", ""),
                    })
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    f.write(output.getvalue())
                return file_path

            def on_success(result):
                if self.winfo_exists():
                    self._show_success(f"Exportação concluída:\n{result}")

            def on_error(exc):
                if self.winfo_exists():
                    self._show_error(f"Erro ao exportar logs.\n{exc}")

            AsyncRunner.run(task=write, on_success=on_success, on_error=on_error, widget_ref=self)
        except Exception as exc:
            self._show_error(f"Erro ao exportar logs.\n{exc}")

    def _show_success(self, message: str, title: str = "Sucesso"):
        try:
            _SuccessModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            try:
                if hasattr(self, "_toast") and self._toast and self._toast.winfo_exists():
                    self._toast.destroy()
                from ser_pleno.ui.components.ui_components import Toast
                self._toast = Toast(self.winfo_toplevel(), message=message, status="success", duration=3000)
            except Exception:
                pass

    def _show_error(self, message: str, title: str = "Não foi possível concluir") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _confirmar(self, mensagem: str) -> bool:
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)
        w, h = 420, 200
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        resultado = {"ok": False}
        ctk.CTkLabel(modal, text=mensagem,
                     font=themed_font("h4", "bold"),
                     text_color=THEME["text"],
                     wraplength=360, justify="center").pack(pady=(24, 16))
        botoes = ctk.CTkFrame(modal, fg_color="transparent")
        botoes.pack(pady=(0, 20))
        ctk.CTkButton(botoes, text="Cancelar", width=110, height=36,
                      fg_color=THEME["bg_alt"], hover_color=THEME["border"],
                      text_color=THEME["text"],
                      command=lambda: modal.destroy()).pack(side="left", padx=(0, 8))
        ctk.CTkButton(botoes, text="Confirmar", width=110, height=36,
                      fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                      text_color=THEME["text_on_primary"],
                      command=lambda: self._confirmar_callback(modal, resultado)).pack(side="right")
        modal.wait_window(modal)
        return resultado.get("ok", False)

    def _confirmar_callback(self, modal: ctk.CTkToplevel, resultado: dict):
        resultado["ok"] = True
        modal.destroy()


class _SuccessModal(BaseModal):
    def __init__(self, parent, message: str, title: str = "Sucesso"):
        super().__init__(parent, title=title, width=420, height=220)
        self.configure(fg_color=THEME["surface"])

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        icon_box = ctk.CTkFrame(wrapper, fg_color=THEME["success_soft"], width=52, height=52,
                                 corner_radius=RADIUS["lg"])
        icon_box.pack(pady=(0, 14))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=f"{ICONS['check']} ", font=themed_font("h2"),
                     text_color=THEME["success"]).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(wrapper, text=title, font=themed_font("h4", "bold"),
                     text_color=THEME["text"]).pack()
        ctk.CTkLabel(wrapper, text=message, font=themed_font("body_sm"),
                     text_color=THEME["text_muted"], wraplength=340, justify="center"
                     ).pack(pady=(6, 18))

        PrimaryButton(wrapper, text="Entendi", width=140, command=self.destroy).pack()
        self.bind("<Return>", lambda e: self.destroy())
        self.after(50, lambda: self.focus_force())

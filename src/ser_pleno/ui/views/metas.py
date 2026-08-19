# -*- coding: utf-8 -*-
"""View de Metas — lista, CRUD, progresso e estatisticas."""

import logging
import customtkinter as ctk
from datetime import datetime
from typing import Any, Dict, List, Optional

from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder
from ser_pleno.utils.dates import normalize_date
from ser_pleno.features.metas.service import ServicoMetas
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font, blend_color
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.components.icons import ICONS, IconLabel
from ser_pleno.ui.components.ui_components import (
    Card,
    PrimaryButton,
    GhostButton,
    DangerButton,
    Badge,
    EmptyState,
    Divider,
    bind_clickable,
    KPICard,
    SkeletonLoader,
    Tooltip,
    Toast,
    BaseModal,
)

logger = logging.getLogger("apps.desktop")


# ——————————————————————————————————————————————————————————————————————————————
#  Helpers
# ——————————————————————————————————————————————————————————————————————————————
def _status_color(status: str) -> str:
    colors = {
        "not_started": THEME["text_muted"],
        "in_progress": THEME["primary"],
        "completed": THEME["success"],
        "paused": THEME["warning"],
        "cancelled": THEME["danger"],
    }
    return colors.get(status, THEME["text_muted"])


def _priority_color(priority: str) -> str:
    colors = {
        "low": THEME["text_muted"],
        "medium": THEME["primary"],
        "high": THEME["warning"],
        "urgent": THEME["danger"],
    }
    return colors.get(priority, THEME["text_muted"])


def _category_color(category: str) -> tuple:
    from ser_pleno.features.metas.service import CATEGORY_COLORS

    return CATEGORY_COLORS.get(category, ("#4F46E5", "#EEF2FF"))


# ——————————————————————————————————————————————————————————————————————————————
#  GoalCard — card individual de meta na lista
# ——————————————————————————————————————————————————————————————————————————————
class GoalCard(ctk.CTkFrame):
    def __init__(self, parent, goal: dict, on_view, on_edit, on_delete, on_progress):
        from datetime import datetime as _dt

        g = goal
        status = g.get("status", "not_started")
        target_date = g.get("target_date", "")
        is_overdue = (
            target_date
            and status not in ("completed", "cancelled")
            and target_date < _dt.now().strftime("%Y-%m-%d")
        )
        border_c = THEME["danger"] if is_overdue else THEME["border"]
        super().__init__(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["card"],
            border_width=2 if is_overdue else 1,
            border_color=border_c,
        )
        self._goal = goal
        self._on_view = on_view
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._on_progress = on_progress
        self._is_overdue = is_overdue
        self._build()

    def _build(self):
        g = self._goal
        category = g.get("category", "Geral")
        color, soft = _category_color(category)

        # Barra lateral colorida
        ctk.CTkFrame(self, width=4, corner_radius=0, fg_color=color).pack(side="left", fill="y")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=spacing("md"), pady=spacing("md"))

        # —— Topo: info + ações ——————————————————————————————————————————————
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))

        # Círculo de categoria
        cat_bg = ctk.CTkFrame(top, width=36, height=36, corner_radius=10, fg_color=soft)
        cat_bg.pack(side="left", padx=(0, 12))
        cat_bg.pack_propagate(False)
        ctk.CTkLabel(
            cat_bg,
            text=category[0].upper(),
            font=font(size=14, weight="bold"),
            text_color=color,
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Meta info
        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        title = g.get("title", "Meta sem título")
        ctk.CTkLabel(
            info,
            text=title,
            font=font(size=13, weight="bold"),
            text_color=THEME["text"],
            anchor="w",
        ).pack(anchor="w")

        # Chips
        chips_frame = ctk.CTkFrame(info, fg_color="transparent")
        chips_frame.pack(anchor="w", pady=(4, 0))

        status = g.get("status", "not_started")
        priority = g.get("priority", "medium")
        student_name = g.get("student_name", "Estudante")

        for text, fg, txt in (
            [
                (
                    status.replace("_", " ").title(),
                    blend_color(_status_color(status), 0.12),
                    _status_color(status),
                ),
                (
                    f"Prioridade: {priority.title()}",
                    blend_color(_priority_color(priority), 0.12),
                    _priority_color(priority),
                ),
            ]
            + [
                (
                    "Atrasada",
                    THEME["danger_soft"],
                    THEME["danger"],
                )
            ]
            if self._is_overdue
            else []
        ):
            chip = ctk.CTkFrame(chips_frame, fg_color=fg, corner_radius=RADIUS["sm"])
            chip.pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                chip,
                text=text,
                font=font(size=10, weight="bold"),
                text_color=txt,
            ).pack(padx=spacing("sm"), pady=spacing("xs"))

        # Ações
        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.pack(side="right", anchor="n")

        for label, cmd, bg, txt in [
            (
                f"{ICONS['view']} Ver",
                lambda: self._on_view(self._goal),
                THEME["primary_soft"],
                THEME["primary"],
            ),
            (
                f"{ICONS['edit']} Editar",
                lambda: self._on_edit(self._goal),
                THEME["accent_soft"],
                THEME["accent"],
            ),
            (
                f"{ICONS['delete']} Excluir",
                lambda: self._on_delete(self._goal.get("id")),
                THEME["danger_soft"],
                THEME["danger"],
            ),
        ]:
            ctk.CTkButton(
                acts,
                text=label,
                command=cmd,
                height=28,
                width=80,
                corner_radius=8,
                fg_color=bg,
                hover_color=bg,
                text_color=txt,
                font=font(size=11, weight="bold"),
            ).pack(side="left", padx=(0, 4))

        # —— Progresso + prazo —————————————————————————————————————————————————
        target_date = g.get("target_date", "")
        progress = g.get("progress_percentage", 0)

        bottom = ctk.CTkFrame(body, fg_color="transparent")
        bottom.pack(fill="x", pady=(0, 0))

        # Barra de progresso
        prog_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        prog_frame.pack(fill="x", pady=(0, 6))
        prog_frame.grid_columnconfigure(0, weight=1)

        prog_bg = ctk.CTkFrame(prog_frame, fg_color=THEME["bg_alt"], corner_radius=999, height=8)
        prog_bg.grid(row=0, column=0, sticky="ew")
        prog_bg.grid_propagate(False)

        prog_color = THEME["warning"] if self._is_overdue else color
        prog_fill = ctk.CTkFrame(prog_bg, fg_color=prog_color, corner_radius=999, height=8)
        prog_fill.place(x=0, y=0, relwidth=progress / 100)

        ctk.CTkLabel(
            prog_frame,
            text=f"{progress}%",
            font=font(size=11, weight="bold"),
            text_color=prog_color,
        ).grid(row=0, column=1, padx=(8, 0))

        # Prazo + estudante
        meta_frame = ctk.CTkFrame(bottom, fg_color="transparent")
        meta_frame.pack(fill="x")

        target_txt = (
            f"{ICONS['calendar']} Prazo: {target_date}"
            if target_date
            else f"{ICONS['calendar']} Sem prazo"
        )
        ctk.CTkLabel(
            meta_frame,
            text=target_txt,
            font=font(size=11),
            text_color=THEME["text_muted"],
        ).pack(side="left")

        ctk.CTkLabel(
            meta_frame,
            text=f"{ICONS['user']} {student_name}",
            font=font(size=11),
            text_color=THEME["text_muted"],
        ).pack(side="right")


# ——————————————————————————————————————————————————————————————————————————————
#  MetasFrame — frame principal
# ——————————————————————————————————————————————————————————————————————————————
class MetasFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        import time as _time

        self._t0 = _time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_metas = getattr(controller, "servico_metas", None)
        self._todas_metas: list = []
        self._selecionado: dict | None = None
        self._filter_after_id = None
        self._stats: dict = {}
        self._overdue_count = 0
        self._metas_atrasadas: list = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._criar_kpis()
        self._criar_tabs()
        self.load_data()
        log_view_init_ms("metas", self._t0, widget_ref=self)

    # ——————————————————————————————————————————————————————————————————————
    #  KPIs
    # ——————————————————————————————————————————————————————————————————————
    def _criar_kpis(self):
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.grid(
            row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 4)
        )
        kpi_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self._kpi_total = KPICard(
            kpi_frame,
            title="Total",
            value="0",
            icon=ICONS["chart"],
            size="sm",
        )
        self._kpi_total.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        self._kpi_progresso = KPICard(
            kpi_frame,
            title="Em andamento",
            value="0",
            icon=ICONS["hourglass"],
            size="sm",
        )
        self._kpi_progresso.grid(row=0, column=1, padx=6, sticky="nsew")

        self._kpi_concluidas = KPICard(
            kpi_frame,
            title="Concluídas",
            value="0",
            icon=ICONS["check_circle"],
            size="sm",
        )
        self._kpi_concluidas.grid(row=0, column=2, padx=6, sticky="nsew")

        self._kpi_atrasadas = KPICard(
            kpi_frame,
            title="Atrasadas",
            value="0",
            icon=ICONS["alert"],
            size="sm",
        )
        self._kpi_atrasadas.grid(row=0, column=3, padx=6, sticky="nsew")

        self._kpi_urgentes = KPICard(
            kpi_frame,
            title="Urgentes",
            value="0",
            icon=ICONS["priority_high"],
            size="sm",
        )
        self._kpi_urgentes.grid(row=0, column=4, padx=(6, 0), sticky="nsew")

    # ——————————————————————————————————————————————————————————————————————
    #  Tabs
    # ——————————————————————————————————————————————————————————————————————
    def _criar_tabs(self):
        self.tabs = ctk.CTkTabview(
            self,
            fg_color="transparent",
            segmented_button_fg_color=THEME["bg_alt"],
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            text_color=THEME["text_secondary"],
            text_color_disabled=THEME["text_muted"],
            corner_radius=RADIUS["lg"],
        )
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))

        self.tab_metas = self.tabs.add("Metas")
        self.tab_atrasadas = self.tabs.add("Atrasadas")

        self._criar_filtros()
        self._criar_lista_metas()
        self._criar_lista_atrasadas()

    # ——————————————————————————————————————————————————————————————————————
    #  Filtros
    # ——————————————————————————————————————————————————————————————————————
    def _criar_filtros(self):
        filter_frame = ctk.CTkFrame(self.tab_metas, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 4))
        filter_frame.grid_columnconfigure(0, weight=1)

        right = ctk.CTkFrame(filter_frame, fg_color="transparent")
        right.pack(side="right")

        PrimaryButton(
            right,
            text=f"{ICONS['add']} Nova Meta",
            command=self._abrir_modal_criar,
            height=36,
            width=140,
        ).pack(side="left", padx=(0, 8))

        opt_style = dict(
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=32,
            corner_radius=RADIUS["button"],
            font=themed_font("caption"),
        )

        self.f_estudante = ctk.CTkOptionMenu(
            right,
            values=["Todos os estudantes"],
            command=lambda _: self._aplicar_filtros(),
            **opt_style,
        )
        self.f_estudante.pack(side="left", padx=(0, 6))

        self.f_status = ctk.CTkOptionMenu(
            right,
            values=["Todos", "Nao iniciada", "Em andamento", "Concluida", "Pausada", "Cancelada"],
            command=lambda _: self._aplicar_filtros(),
            **opt_style,
        )
        self.f_status.pack(side="left", padx=(0, 6))

        self.f_prioridade = ctk.CTkOptionMenu(
            right,
            values=["Todas", "Baixa", "Media", "Alta", "Urgente"],
            command=lambda _: self._aplicar_filtros(),
            **opt_style,
        )
        self.f_prioridade.pack(side="left", padx=(0, 6))

        self.f_categoria = ctk.CTkOptionMenu(
            right,
            values=["Todas"]
            + [
                "Academico",
                "Emocional",
                "Social",
                "Familiar",
                "Vocacional",
                "Comportamental",
                "Geral",
            ],
            command=lambda _: self._aplicar_filtros(),
            **opt_style,
        )
        self.f_categoria.pack(side="left", padx=(0, 6))

        # Busca
        search_wrap = ctk.CTkFrame(
            filter_frame, fg_color=THEME["bg_alt"], corner_radius=RADIUS["input"]
        )
        search_wrap.pack(side="left", fill="x", expand=True, padx=(0, 12))

        ctk.CTkLabel(
            search_wrap,
            text=ICONS["search"],
            font=font(size=13),
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(10, 0))

        self.entry_busca = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Buscar meta...",
            fg_color=THEME["bg_alt"],
            border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=themed_font("body"),
            height=32,
        )
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.entry_busca.bind("<KeyRelease>", self._filtrar)

        self._carregar_estudantes_filtro()

    # ——————————————————————————————————————————————————————————————————————
    #  Lista
    # ——————————————————————————————————————————————————————————————————————
    def _criar_lista_metas(self):
        self.scroll_list = ctk.CTkScrollableFrame(
            self.tab_metas,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.scroll_list.pack(fill="both", expand=True)

        self.lbl_count = ctk.CTkLabel(
            self.tab_metas,
            text="0 metas",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        )
        self.lbl_count.pack(anchor="w", pady=(0, 4))

    def _criar_lista_atrasadas(self):
        self.scroll_atrasadas = ctk.CTkScrollableFrame(
            self.tab_atrasadas,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.scroll_atrasadas.pack(fill="both", expand=True)

        self.lbl_count_atrasadas = ctk.CTkLabel(
            self.tab_atrasadas,
            text="0 metas atrasadas",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        )
        self.lbl_count_atrasadas.pack(anchor="w", pady=(0, 4))

    # ——————————————————————————————————————————————————————————————————————
    #  Dados
    # ——————————————————————————————————————————————————————————————————————
    def load_data(self):
        self._carregar_estatisticas()
        self._carregar_metas()
        self._carregar_atrasadas()

    def _carregar_estatisticas(self):
        def fetch():
            return self.servico_metas.obter_stats()

        def on_success(result):
            if result.get("success"):
                self._stats = result.get("data", {})
                self._atualizar_kpis()

        AsyncRunner.run(task=fetch, on_success=on_success, widget_ref=self)

    def _atualizar_kpis(self):
        if not self.winfo_exists():
            return
        total = self._stats.get("total", 0)
        by_status = self._stats.get("by_status", [])
        by_priority = self._stats.get("by_priority", [])
        overdue = self._stats.get("overdue", 0)

        in_progress = 0
        completed = 0
        urgent = 0
        for item in by_status:
            s = item.get("status", "")
            if s == "in_progress":
                in_progress = item.get("count", 0)
            elif s == "completed":
                completed = item.get("count", 0)

        for item in by_priority:
            p = item.get("priority", "")
            if p in ("high", "urgent"):
                urgent += item.get("count", 0)

        self._kpi_total.set_value(str(total))
        self._kpi_progresso.set_value(str(in_progress))
        self._kpi_concluidas.set_value(str(completed))
        self._kpi_atrasadas.set_value(str(overdue))
        self._kpi_urgentes.set_value(str(urgent))
        self._overdue_count = overdue

    def _carregar_metas(self):
        def fetch():
            return self.servico_metas.listar_metas()

        def on_success(resultado):
            self._renderizar(resultado)

        def on_error(exc):
            logger.error("Erro ao carregar metas: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _renderizar(self, resultado):
        if not self.winfo_exists():
            return
        self._mostrar_skeletons()

        def apply():
            if not self.winfo_exists():
                return
            metas = []
            if resultado.get("success"):
                data = resultado.get("data") or {}
                metas = data.get("goals") or []

            self._todas_metas = metas
            self._mostrar_metas(metas)

        self.after(60, apply)

    def _mostrar_skeletons(self):
        for w in self.scroll_list.winfo_children():
            w.destroy()
        batch = WidgetBatchBuilder(parent=self.scroll_list, batch_size=20)
        for _ in range(6):
            batch.add(
                lambda: SkeletonLoader(self.scroll_list, width=260, height=80, variant="card").pack(
                    fill="x", pady=4, padx=4
                )
            )
        batch.execute()

    def _mostrar_metas(self, metas: list):
        for w in self.scroll_list.winfo_children():
            w.destroy()

        if not metas:
            EmptyState(
                self.scroll_list,
                icon=ICONS["chart"],
                title="Nenhuma meta registrada",
                subtitle="Clique em Nova Meta para comecar",
            ).pack(pady=30)
            self.lbl_count.configure(text="0 metas")
            return

        self.lbl_count.configure(text=f"{len(metas)} meta{'s' if len(metas) != 1 else ''}")

        batch = WidgetBatchBuilder(parent=self.scroll_list, batch_size=20)
        for m in metas:
            batch.add(
                lambda m=m: GoalCard(
                    self.scroll_list,
                    goal=m,
                    on_view=self._ver_meta,
                    on_edit=self._editar_meta,
                    on_delete=self._excluir_meta,
                    on_progress=self._abrir_modal_progresso,
                ).pack(fill="both", expand=True, pady=(0, 10))
            )
        batch.execute()

    def _carregar_atrasadas(self):
        def fetch():
            return self.servico_metas.obter_atrasadas()

        def on_success(result):
            if not self.winfo_exists():
                return
            metas = []
            if result.get("success"):
                metas = result.get("data") or []
            self._metas_atrasadas = metas
            self._mostrar_atrasadas(metas)

        def on_error(exc):
            logger.error("Erro ao carregar metas atrasadas: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _mostrar_atrasadas(self, metas: list):
        for w in self.scroll_atrasadas.winfo_children():
            w.destroy()

        if not metas:
            EmptyState(
                self.scroll_atrasadas,
                icon=ICONS["check_circle"],
                title="Nenhuma meta atrasada",
                subtitle="Todas as metas estao em dia",
            ).pack(pady=30)
            self.lbl_count_atrasadas.configure(text="0 metas atrasadas")
            return

        self.lbl_count_atrasadas.configure(text=f"{len(metas)} meta{'s' if len(metas) != 1 else ''} atrasada{'s' if len(metas) != 1 else ''}")

        batch = WidgetBatchBuilder(parent=self.scroll_atrasadas, batch_size=20)
        for m in metas:
            batch.add(
                lambda m=m: GoalCard(
                    self.scroll_atrasadas,
                    goal=m,
                    on_view=self._ver_meta,
                    on_edit=self._editar_meta,
                    on_delete=self._excluir_meta,
                    on_progress=self._abrir_modal_progresso,
                ).pack(fill="both", expand=True, pady=(0, 10))
            )
        batch.execute()

    # ——————————————————————————————————————————————————————————————————————
    #  Filtros
    # ——————————————————————————————————————————————————————————————————————
    def _carregar_estudantes_filtro(self):
        def fetch():
            return self.servico_metas.listar_estudantes()

        def on_success(result):
            if not self.winfo_exists():
                return
            estudantes = []
            if result.get("success"):
                estudantes = result.get("data", [])
            values = ["Todos os estudantes"] + [e.get("name", "") for e in estudantes]
            self.f_estudante.configure(values=values)
            self._student_ids = {e.get("name", ""): e.get("id") for e in estudantes}

        def on_error(exc):
            logger.error("Erro ao carregar estudantes para filtro: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _aplicar_filtros(self):
        termo = self.entry_busca.get().lower().strip() if hasattr(self, "entry_busca") else ""
        estudante_raw = (
            self.f_estudante.get() if hasattr(self, "f_estudante") else "Todos os estudantes"
        )
        status_raw = self.f_status.get() if hasattr(self, "f_status") else "Todos"
        prioridade_raw = self.f_prioridade.get() if hasattr(self, "f_prioridade") else "Todas"
        categoria_raw = self.f_categoria.get() if hasattr(self, "f_categoria") else "Todas"

        student_id = None
        if estudante_raw != "Todos os estudantes":
            student_id = getattr(self, "_student_ids", {}).get(estudante_raw)

        status_map = {
            "Todos": "",
            "Nao iniciada": "not_started",
            "Em andamento": "in_progress",
            "Concluida": "completed",
            "Pausada": "paused",
            "Cancelada": "cancelled",
        }
        priority_map = {
            "Todas": "",
            "Baixa": "low",
            "Media": "medium",
            "Alta": "high",
            "Urgente": "urgent",
        }
        category_map = {
            "Todas": "",
            "Academico": "Academico",
            "Emocional": "Emocional",
            "Social": "Social",
            "Familiar": "Familiar",
            "Vocacional": "Vocacional",
            "Comportamental": "Comportamental",
            "Geral": "Geral",
        }

        status = status_map.get(status_raw, "")
        priority = priority_map.get(prioridade_raw, "")
        category = category_map.get(categoria_raw, "")

        def ok(meta):
            titulo = meta.get("title", "").lower()
            student = meta.get("student_name", "").lower()
            termo_ok = termo in titulo or termo in student or not termo
            student_ok = student_id is None or meta.get("student_id") == student_id
            status_ok = not status or meta.get("status") == status
            priority_ok = not priority or meta.get("priority") == priority
            category_ok = not category or meta.get("category") == category
            return termo_ok and student_ok and status_ok and priority_ok and category_ok

        filtrados = [m for m in self._todas_metas if ok(m)]
        self._mostrar_metas(filtrados)

    def _filtrar(self, _=None):
        if self._filter_after_id:
            self.after_cancel(self._filter_after_id)
        self._filter_after_id = self.after(180, self._aplicar_filtros)

    # ——————————————————————————————————————————————————————————————————————
    #  Acoes
    # ——————————————————————————————————————————————————————————————————————
    def _ver_meta(self, meta):
        self._modal_detalhe(meta)

    def _editar_meta(self, meta):
        self._abrir_modal_editar(meta)

    def _excluir_meta(self, meta_id):
        if not meta_id:
            return
        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirmar exclusao")
        confirm.configure(fg_color=THEME["surface"])
        confirm.resizable(False, False)
        w, h = 400, 200
        sx = confirm.winfo_screenwidth() // 2 - w // 2
        sy = confirm.winfo_screenheight() // 2 - h // 2
        confirm.geometry(f"{w}x{h}+{sx}+{sy}")
        confirm.transient(self.winfo_toplevel())
        confirm.grab_set()

        ctk.CTkLabel(
            confirm,
            text="Excluir meta?",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(pady=(24, 8))
        ctk.CTkLabel(
            confirm,
            text="Esta acao nao pode ser desfeita.",
            font=themed_font("body"),
            text_color=THEME["text_muted"],
        ).pack(pady=(0, 20))

        btn_frame = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 24))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=confirm.destroy,
            height=36,
            corner_radius=10,
            width=120,
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        def confirmar():
            confirm.destroy()

            def delete():
                return self.servico_metas.deletar_meta(meta_id)

            def on_ok(_):
                self._carregar_metas()
                self._carregar_estatisticas()

            def on_err(e):
                self._show_error(str(e))

            AsyncRunner.run(task=delete, on_success=on_ok, on_error=on_err, widget_ref=self)

        ctk.CTkButton(
            btn_frame,
            text="Excluir",
            command=confirmar,
            height=36,
            corner_radius=10,
            width=120,
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            text_color="white",
            font=themed_font("button", "bold"),
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    # ——————————————————————————————————————————————————————————————————————
    #  Modal: Criar / Editar meta
    # ——————————————————————————————————————————————————————————————————————
    def _abrir_modal_criar(self):
        self._modal_meta()

    def _abrir_modal_editar(self, meta):
        self._modal_meta(meta)

    def _modal_meta(self, meta=None):
        is_edit = meta is not None
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Meta" if is_edit else "Nova Meta")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 600, 720 if is_edit else 620
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"])
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card,
            text="Editar Meta" if is_edit else "Nova Meta",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 16))

        # Estudante
        estudantes = []
        try:
            resp = self.servico_metas.listar_estudantes()
            if resp.get("success"):
                estudantes = resp.get("data", [])
        except Exception:
            pass

        student_values = [f"{e.get('name', '')}" for e in estudantes]
        student_ids = [e.get("id") for e in estudantes]

        f_estudante = ctk.CTkOptionMenu(
            card,
            values=student_values if student_values else ["Nenhum estudante"],
            fg_color=THEME["bg_alt"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
            corner_radius=RADIUS["input"],
        )
        f_estudante.pack(fill="x", pady=(0, 10))

        if is_edit and meta.get("student_id") in student_ids:
            idx = student_ids.index(meta.get("student_id"))
            f_estudante.set(student_values[idx])

        f_titulo = ctk.CTkEntry(
            card,
            placeholder_text="Título da meta",
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text"],
            font=themed_font("body"),
            height=40,
        )
        f_titulo.pack(fill="x", pady=(0, 10))

        f_descricao = ctk.CTkTextbox(
            card,
            height=80,
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            font=themed_font("body"),
            corner_radius=RADIUS["input"],
        )
        f_descricao.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        row.grid_columnconfigure((0, 1), weight=1)

        f_categoria = ctk.CTkOptionMenu(
            row,
            values=[
                "Academico",
                "Emocional",
                "Social",
                "Familiar",
                "Vocacional",
                "Comportamental",
                "Geral",
            ],
            fg_color=THEME["bg_alt"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
            corner_radius=RADIUS["input"],
        )
        f_categoria.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        f_prioridade = ctk.CTkOptionMenu(
            row,
            values=["low", "medium", "high", "urgent"],
            fg_color=THEME["bg_alt"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
            corner_radius=RADIUS["input"],
        )
        f_prioridade.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))
        row2.grid_columnconfigure((0, 1), weight=1)

        f_status = ctk.CTkOptionMenu(
            row2,
            values=["not_started", "in_progress", "completed", "paused", "cancelled"],
            fg_color=THEME["bg_alt"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
            corner_radius=RADIUS["input"],
        )
        f_status.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        f_prazo = ctk.CTkEntry(
            row2,
            placeholder_text="Prazo (YYYY-MM-DD)",
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
        )
        f_prazo.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        f_criterios = ctk.CTkTextbox(
            card,
            height=80,
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            font=themed_font("body"),
            corner_radius=RADIUS["input"],
        )
        f_criterios.pack(fill="x", pady=(0, 10))

        f_notas = ctk.CTkTextbox(
            card,
            height=60,
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            font=themed_font("body"),
            corner_radius=RADIUS["input"],
        )
        f_notas.pack(fill="x", pady=(0, 16))

        if is_edit:
            f_titulo.insert(0, meta.get("title", ""))
            f_descricao.insert("1.0", meta.get("description", "") or "")
            f_categoria.set(meta.get("category", "Geral"))
            f_prioridade.set(meta.get("priority", "medium"))
            f_status.set(meta.get("status", "not_started"))
            f_prazo.insert(0, meta.get("target_date", "") or "")
            f_criterios.insert("1.0", meta.get("success_criteria", "") or "")
            f_notas.insert("1.0", meta.get("notes", "") or "")

        def salvar():
            titulo = f_titulo.get().strip()
            if not titulo:
                self._show_error("Título é obrigatório")
                return

            estudante_idx = (
                student_values.index(f_estudante.get())
                if f_estudante.get() in student_values
                else 0
            )
            student_id = student_ids[estudante_idx] if student_ids else None

            target_date = f_prazo.get().strip()
            if target_date:
                try:
                    target_date = normalize_date(target_date)
                except ValueError as e:
                    self._show_error(str(e), title="Data inválida")
                    return

            dados = {
                "student_id": student_id,
                "title": titulo,
                "description": f_descricao.get("1.0", "end").strip(),
                "category": f_categoria.get(),
                "priority": f_prioridade.get(),
                "status": f_status.get(),
                "target_date": target_date or None,
                "success_criteria": f_criterios.get("1.0", "end").strip(),
                "notes": f_notas.get("1.0", "end").strip(),
            }

            if is_edit and meta.get("status") == "completed" and dados.get("status") != "completed":
                dados["completed_date"] = None
            elif dados.get("status") == "completed" and not meta.get("completed_date"):
                dados["completed_date"] = datetime.now().strftime("%Y-%m-%d")

            def save():
                if is_edit:
                    return self.servico_metas.atualizar_meta(meta.get("id"), dados)
                return self.servico_metas.criar_meta(dados)

            def on_ok(_):
                modal.destroy()
                self._carregar_metas()
                self._carregar_estatisticas()

            def on_err(e):
                self._show_error(str(e))

            AsyncRunner.run(task=save, on_success=on_ok, on_error=on_err, widget_ref=self)

        ctk.CTkFrame(card, height=1, fg_color=THEME["divider"]).pack(fill="x")

        footer = ctk.CTkFrame(card, fg_color="transparent", height=56)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            height=36,
            width=110,
            corner_radius=10,
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="left", pady=10)

        ctk.CTkButton(
            footer,
            text=f"{ICONS['check']} Salvar",
            command=salvar,
            height=36,
            width=150,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color="white",
            font=themed_font("button", "bold"),
        ).pack(side="right", pady=10)

    # ——————————————————————————————————————————————————————————————————————
    #  Modal: Detalhe da meta
    # ——————————————————————————————————————————————————————————————————————
    def _modal_detalhe(self, meta):
        modal = ctk.CTkToplevel(self)
        modal.title("Detalhe da Meta")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 600, 700
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        category = meta.get("category", "Geral")
        color, soft = _category_color(category)

        banner = ctk.CTkFrame(scroll, fg_color=soft, corner_radius=RADIUS["lg"], height=70)
        banner.pack(fill="x", pady=(0, 16))
        banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=spacing("xl"))

        ib = ctk.CTkFrame(bi, width=42, height=42, corner_radius=12, fg_color=color)
        ib.pack(side="left", padx=(0, 12))
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text=category[0].upper(), font=font(size=18)).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            ts,
            text=meta.get("title", "Meta"),
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")

        chip = ctk.CTkFrame(ts, fg_color=color, corner_radius=6, height=24)
        chip.pack(anchor="w", pady=(3, 0))
        chip.pack_propagate(False)
        ctk.CTkLabel(
            chip,
            text=category,
            font=font(size=10, weight="bold"),
            text_color="white",
        ).pack(padx=spacing("sm"), pady=spacing("xs"))

        # Info grid
        info_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        info_frame.pack(fill="x", pady=(0, 12))
        info_frame.grid_columnconfigure((0, 1), weight=1)

        fields = [
            (f"{ICONS['user']} Estudante", meta.get("student_name", "—")),
            (f"{ICONS['pin']} Prioridade", (meta.get("priority", "—") or "—").title()),
            (
                f"{ICONS['status_dot']} Status",
                (meta.get("status", "—") or "—").replace("_", " ").title(),
            ),
            (f"{ICONS['calendar']} Prazo", meta.get("target_date", "—") or "—"),
            (f"{ICONS['chart']} Progresso", f"{meta.get('progress_percentage', 0)}%"),
        ]
        for i, (label, value) in enumerate(fields):
            r, c = divmod(i, 2)
            box = ctk.CTkFrame(info_frame, fg_color=THEME["bg_alt"], corner_radius=RADIUS["lg"])
            box.grid(
                row=r,
                column=c,
                padx=(0 if c == 0 else 6, 6 if c == 0 else 0),
                pady=4,
                sticky="nsew",
            )
            ctk.CTkLabel(
                box,
                text=label,
                font=themed_font("overline"),
                text_color=THEME["text_muted"],
            ).pack(anchor="w", padx=spacing("md"), pady=(spacing("md"), 0))
            ctk.CTkLabel(
                box,
                text=value,
                font=themed_font("body", "bold"),
                text_color=THEME["text"],
            ).pack(anchor="w", padx=spacing("md"), pady=(0, spacing("md")))

        # Descricao
        if meta.get("description"):
            ctk.CTkLabel(
                scroll,
                text="Descricao",
                font=themed_font("caption", "bold"),
                text_color=THEME["text_muted"],
            ).pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(
                scroll,
                text=meta.get("description", ""),
                font=themed_font("body"),
                text_color=THEME["text"],
                wraplength=540,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(0, 12))

        # Criterios de sucesso
        if meta.get("success_criteria"):
            ctk.CTkLabel(
                scroll,
                text="Criterios de Sucesso",
                font=themed_font("caption", "bold"),
                text_color=THEME["text_muted"],
            ).pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(
                scroll,
                text=meta.get("success_criteria", ""),
                font=themed_font("body"),
                text_color=THEME["text"],
                wraplength=540,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(0, 12))

        # Notas
        if meta.get("notes"):
            ctk.CTkLabel(
                scroll,
                text="Notas",
                font=themed_font("caption", "bold"),
                text_color=THEME["text_muted"],
            ).pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(
                scroll,
                text=meta.get("notes", ""),
                font=themed_font("body"),
                text_color=THEME["text"],
                wraplength=540,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(0, 12))

        # Historico de progresso
        ctk.CTkLabel(
            scroll,
            text="Historico de Progresso",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, 4))

        self._progresso_list = ctk.CTkScrollableFrame(
            scroll,
            fg_color="transparent",
            height=200,
            scrollbar_button_color=THEME["border_strong"],
        )
        self._progresso_list.pack(fill="x", pady=(0, 12))

        def carregar_progresso():
            def fetch():
                return self.servico_metas.listar_progresso(meta.get("id"))

            def on_success(result):
                if not self.winfo_exists():
                    return
                self._renderizar_progresso(result)

            AsyncRunner.run(task=fetch, on_success=on_success, widget_ref=self)

        carregar_progresso()

        # Botoes
        ctk.CTkFrame(scroll, height=1, fg_color=THEME["divider"]).pack(fill="x", pady=(0, 12))

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame,
            text=f"{ICONS['edit']} Editar",
            command=lambda: (modal.destroy(), self._editar_meta(meta)),
            height=36,
            width=120,
            corner_radius=10,
            fg_color=THEME["primary_soft"],
            hover_color=THEME["primary"],
            text_color=THEME["primary"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text=f"{ICONS['clock']} Registrar Progresso",
            command=lambda: (modal.destroy(), self._abrir_modal_progresso(meta)),
            height=36,
            width=180,
            corner_radius=10,
            fg_color=THEME["accent_soft"],
            hover_color=THEME["accent"],
            text_color=THEME["accent"],
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="Fechar",
            command=modal.destroy,
            height=36,
            width=100,
            corner_radius=10,
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="right")

    def _renderizar_progresso(self, result):
        for w in self._progresso_list.winfo_children():
            w.destroy()

        progressos = []
        if result.get("success"):
            progressos = result.get("data") or []

        if not progressos:
            ctk.CTkLabel(
                self._progresso_list,
                text="Nenhum progresso registrado",
                font=themed_font("body"),
                text_color=THEME["text_muted"],
            ).pack(pady=20)
            return

        for p in progressos:
            row = ctk.CTkFrame(
                self._progresso_list, fg_color=THEME["bg_alt"], corner_radius=RADIUS["lg"]
            )
            row.pack(fill="x", pady=4)

            ctk.CTkLabel(
                row,
                text=f"{p.get('percentage', 0)}%",
                font=font(size=14, weight="bold"),
                text_color=THEME["primary"],
            ).pack(side="left", padx=(spacing("md"), 0), pady=spacing("md"))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=spacing("md"))

            ctk.CTkLabel(
                info,
                text=p.get("notes", "") or "Sem notas",
                font=themed_font("body"),
                text_color=THEME["text"],
                anchor="w",
            ).pack(anchor="w")

            recorded_at = p.get("recorded_at", "")
            date_txt = recorded_at[:10] if recorded_at else ""
            ctk.CTkLabel(
                info,
                text=date_txt,
                font=themed_font("caption"),
                text_color=THEME["text_muted"],
                anchor="w",
            ).pack(anchor="w")

    # ——————————————————————————————————————————————————————————————————————
    #  Modal: Registrar progresso
    # ——————————————————————————————————————————————————————————————————————
    def _abrir_modal_progresso(self, meta):
        modal = ctk.CTkToplevel(self)
        modal.title("Registrar Progresso")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 420, 320
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"])
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card,
            text=f"Progresso: {meta.get('title', 'Meta')}",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 16))

        current = meta.get("progress_percentage", 0)
        ctk.CTkLabel(
            card,
            text=f"Progresso atual: {current}%",
            font=themed_font("body"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, 8))

        f_percentage = ctk.CTkSlider(
            card,
            from_=0,
            to=100,
            number_of_steps=100,
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            progress_color=THEME["primary"],
        )
        f_percentage.set(current)
        f_percentage.pack(fill="x", pady=(0, 8))

        self.lbl_percentage = ctk.CTkLabel(
            card,
            text=f"{int(current)}%",
            font=font(size=14, weight="bold"),
            text_color=THEME["primary"],
        )
        self.lbl_percentage.pack(anchor="e", pady=(0, 8))

        def on_slide(value):
            self.lbl_percentage.configure(text=f"{int(value)}%")

        f_percentage.configure(command=on_slide)

        f_notas = ctk.CTkTextbox(
            card,
            height=80,
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            font=themed_font("body"),
            corner_radius=RADIUS["input"],
        )
        f_notas.pack(fill="x", pady=(0, 16))

        ctk.CTkFrame(card, height=1, fg_color=THEME["divider"]).pack(fill="x")

        footer = ctk.CTkFrame(card, fg_color="transparent", height=56)
        footer.pack(fill="x")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            height=36,
            width=110,
            corner_radius=10,
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="left", pady=10)

        def salvar():
            percentage = int(f_percentage.get())
            notes = f_notas.get("1.0", "end").strip()

            def save():
                return self.servico_metas.registrar_progresso(meta.get("id"), percentage, notes)

            def on_ok(_):
                modal.destroy()
                self._carregar_metas()
                self._carregar_estatisticas()

            def on_err(e):
                self._show_error(str(e))

            AsyncRunner.run(task=save, on_success=on_ok, on_error=on_err, widget_ref=self)

        ctk.CTkButton(
            footer,
            text=f"{ICONS['check']} Registrar",
            command=salvar,
            height=36,
            width=150,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color="white",
            font=themed_font("button", "bold"),
        ).pack(side="right", pady=10)

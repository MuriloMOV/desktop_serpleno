import logging
import customtkinter as ctk
from ser_pleno.presentation.components.ui_components import (
    Card, EmptyState, PrimaryButton, Divider, KPICard, SearchField, Tabs, bind_clickable, BaseModal, SkeletonLoader
)
from ser_pleno.ui.components.icons import ICONS, IconLabel
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, themed_font, FONT_FAMILY
from ser_pleno.ui.theme_extensions import spacing

logger = logging.getLogger(__name__)


class _SearchResultRow(ctk.CTkFrame):
    _TYPE_COLORS = {
        "student": (THEME["primary"], THEME["primary_soft"]),
        "appointment": (THEME["success"], THEME["success_soft"]),
        "screening": (THEME["warning"], THEME["warning_soft"]),
    }
    _TYPE_LABELS = {
        "student": "Estudante",
        "appointment": "Agendamento",
        "screening": "Triagem",
    }

    def __init__(self, parent, item: dict, on_click=None):
        super().__init__(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        self._build(item, on_click)

    def _build(self, item, on_click):
        tipo = item.get("type", "student")
        accent, soft = self._TYPE_COLORS.get(tipo, (THEME["primary"], THEME["primary_soft"]))
        tipo_label = self._TYPE_LABELS.get(tipo, tipo)

        chip = ctk.CTkFrame(self, fg_color=soft, corner_radius=RADIUS["pill"])
        chip.pack(side="right", padx=spacing("md"), pady=spacing("md"))
        ctk.CTkLabel(
            chip, text=tipo_label,
            font=themed_font("caption", "bold"),
            text_color=accent,
        ).pack(padx=spacing("sm"), pady=spacing("xs"))

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", pady=spacing("md"), fill="x", expand=True)

        ctk.CTkLabel(
            info, text=item.get("name", "?"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(anchor="w")

        detail = item.get("detail") or item.get("status") or ""
        if detail:
            ctk.CTkLabel(
                info, text=detail,
                font=themed_font("caption"),
                text_color=THEME["text_secondary"], anchor="w",
            ).pack(anchor="w", pady=(spacing("xs"), 0))

        if on_click:
            bind_clickable(self, lambda: on_click(item))


class _QuickActionRow(ctk.CTkFrame):
    def __init__(self, parent, action: dict, on_click=None):
        super().__init__(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        self._build(action, on_click)

    def _build(self, action, on_click):
        ctk.CTkLabel(
            self, text=action.get("icon", ""),
            font=themed_font("h3"),
            text_color=THEME["primary"],
        ).pack(side="left", padx=(spacing("md"), spacing("sm")), pady=spacing("md"))

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", pady=spacing("md"), fill="x", expand=True)

        ctk.CTkLabel(
            info, text=action.get("label", ""),
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(anchor="w")

        desc = action.get("description", "")
        if desc:
            ctk.CTkLabel(
                info, text=desc,
                font=themed_font("caption"),
                text_color=THEME["text_secondary"], anchor="w",
            ).pack(anchor="w", pady=(spacing("xs"), 0))

        ctk.CTkLabel(
            self, text=ICONS["arrow_forward"],
            font=themed_font("h3"),
            text_color=THEME["text_muted"],
        ).pack(side="right", padx=spacing("md"), pady=spacing("md"))

        if on_click:
            bind_clickable(self, lambda: on_click(action))


class TrendChart(ctk.CTkFrame):
    def __init__(self, parent, title: str = "", unit: str = ""):
        super().__init__(parent, fg_color="transparent")
        self._title = title
        self._unit = unit
        self._pending_data = None
        self._chart_after_id = None
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x")

        if self._title:
            ctk.CTkLabel(
                header, text=f"{ICONS['chart']}  {self._title}",
                font=themed_font("body", "bold"),
                text_color=THEME["text"], anchor="w",
            ).pack(side="left")

        self.unit_label = ctk.CTkLabel(
            header, text=self._unit,
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        )
        self.unit_label.pack(side="right")

        self.canvas = ctk.CTkCanvas(
            self, bg=THEME["surface"],
            height=220, highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=spacing("xs"), pady=(spacing("xs"), spacing("md")))
        self.canvas.bind("<Configure>", self._schedule_draw)

        self._empty = EmptyState(
            self, icon=ICONS["chart"],
            title="Sem dados de tendencia",
            subtitle="Os registros aparecerao aqui quando houver entradas",
        )
        self._empty.pack(expand=True, fill="both", padx=24, pady=24)
        self._empty.pack_forget()

    def _schedule_draw(self, event=None):
        if self._chart_after_id:
            try:
                self.after_cancel(self._chart_after_id)
            except Exception:
                pass
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self._chart_after_id = self.after(80, lambda: self._draw(self._pending_data))

    def set_data(self, data: list, metric_name: str = "", unit: str = ""):
        self._pending_data = data
        if metric_name:
            self._title = metric_name
            for child in self.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for c in child.winfo_children():
                        if isinstance(c, ctk.CTkLabel) and c.cget("text").startswith(ICONS.get("chart", "")):
                            c.configure(text=f"{ICONS['chart']}  {metric_name}")
        if unit:
            self.unit_label.configure(text=unit)
        self._schedule_draw()

    def _draw(self, data=None):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 80 or ch < 80:
            return

        if not data or len(data) < 2:
            self.canvas.pack_forget()
            if hasattr(self, "_empty") and self._empty.winfo_exists():
                self._empty.pack(expand=True, fill="both", padx=24, pady=24)
            return

        if hasattr(self, "_empty") and self._empty.winfo_exists():
            self._empty.pack_forget()
        if not self.canvas.winfo_ismapped():
            self.canvas.pack(fill="both", expand=True, padx=spacing("xs"), pady=(spacing("xs"), spacing("md")))

        vals = [item.get("value", 0) or 0 for item in data]
        labels = [item.get("date", "") or "" for item in data]
        n = len(vals)

        mx, my = 44, 24
        cw2 = cw - 2 * mx
        ch2 = ch - 2 * my

        self.canvas.create_rectangle(
            mx, my, cw - mx, ch - my,
            fill=THEME["surface"], outline=THEME["chart_grid"], width=1,
        )

        y_min = min(vals)
        y_max = max(vals)
        rng = y_max - y_min if y_max != y_min else 1.0
        y_pad = rng * 0.1
        y_min_eff = max(0, y_min - y_pad)
        y_max_eff = y_max + y_pad
        rng_eff = y_max_eff - y_min_eff if y_max_eff != y_min_eff else 1.0

        coords = [
            (mx + i * cw2 / (n - 1), (ch - my) - ((v - y_min_eff) / rng_eff) * ch2)
            for i, v in enumerate(vals)
        ]

        poly_pts = []
        for x, y in coords:
            poly_pts += [x, y]
        poly_pts += [coords[-1][0], ch - my, coords[0][0], ch - my]
        self.canvas.create_polygon(poly_pts, fill=THEME["chart_fill"], outline="")

        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=THEME["chart_line"], width=2,
                capstyle="round", joinstyle="round",
            )

        for i, (x, y) in enumerate(coords):
            dot = (THEME["dot_bad"] if vals[i] < (y_min_eff + rng_eff * 0.33) else
                   THEME["dot_mid"] if vals[i] < (y_min_eff + rng_eff * 0.66) else
                   THEME["dot_good"])
            self.canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill=dot, outline=THEME["surface"], width=2,
            )

        step = max(1, n // 7)
        for i, (x, _) in enumerate(coords):
            if i % step == 0:
                label_text = labels[i][5:] if len(labels[i]) > 5 else labels[i]
                self.canvas.create_text(
                    x, ch - 8, text=label_text,
                    font=(FONT_FAMILY, 8), fill=THEME["text_muted"],
                )


class SearchDetailModal(BaseModal):
    def __init__(self, parent, item: dict, on_navigate=None):
        tipo = item.get("type", "item")
        title_map = {"student": "Detalhes do Estudante", "appointment": "Detalhes do Agendamento", "screening": "Detalhes da Triagem"}
        super().__init__(parent, title=title_map.get(tipo, "Detalhes"), width=420, height=320)
        self._item = item
        self._on_navigate = on_navigate
        self._build()

    def _build(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["card_pad"])

        ctk.CTkLabel(
            inner, text=self._item.get("name", ""),
            font=themed_font("h3", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(anchor="w", pady=(0, 12))

        for label, value in [
            ("Tipo", self._item.get("type", "").title()),
            ("Detalhe", self._item.get("detail") or self._item.get("status") or "—"),
            ("ID", str(self._item.get("id", ""))),
        ]:
            row = ctk.CTkFrame(inner, fg_color="transparent")
            row.pack(fill="x", pady=spacing("xs"))
            ctk.CTkLabel(row, text=label, width=80,
                         font=themed_font("body"), text_color=THEME["text_secondary"], anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value,
                         font=themed_font("body", "bold"), text_color=THEME["text"], anchor="w").pack(side="left")

        Divider(inner).pack(fill="x", pady=spacing("md"))

        PrimaryButton(
            self, text="Abrir no modulo",
            command=self._navigate,
            width=180, height=38,
        ).pack(pady=(spacing("xs"), spacing("md")))

    def _navigate(self):
        if self._on_navigate:
            self._on_navigate(self._item)
        self.destroy()


class AnalyticsFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        import time as _time
        self._t0 = _time.perf_counter()
        super().__init__(
            parent,
            fg_color=THEME["bg"],
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.controller = controller
        self._active_tab = 0
        self._trend_data = None
        self._search_results = None
        self._quick_actions = None

        self._criar_cabecalho()
        self._criar_abas()
        self._criar_conteudo_abas()
        self._carregar_dados()
        log_view_init_ms("analytics", self._t0, widget_ref=self)

    def _carregar_dados(self):
        self._mostrar_skeletons()

        def fetch() -> tuple:
            stats = self.controller.carregar_estatisticas()
            trends = self.controller.carregar_tendencias(metric="mood", days=30)
            performance = self.controller.carregar_performance()
            actions = self.controller.carregar_quick_actions()
            return stats, trends, performance, actions

        def on_success(result: tuple) -> None:
            stats, trends, performance, actions = result
            self._trend_data = trends
            self._quick_actions = actions
            self._atualizar_aba_overview(stats, trends, performance)
            self._atualizar_aba_tendencias(trends)
            self._atualizar_aba_performance(performance)
            self._atualizar_aba_quick_actions(actions)

        def on_error(exc: Exception) -> None:
            self._show_error(f"Nao foi possivel carregar analytics.\n{exc}")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _mostrar_skeletons(self) -> None:
        for tab_name, attr in [
            ("overview", "_overview_container"),
            ("trends", "_trends_container"),
            ("performance", "_performance_container"),
            ("actions", "_actions_container"),
        ]:
            container = getattr(self, attr, None)
            if container and container.winfo_exists():
                for child in container.winfo_children():
                    child.destroy()
                SkeletonLoader(container, width=200, height=16, variant="text").pack(pady=4)

    def _criar_cabecalho(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 4))

        ctk.CTkLabel(
            header, text=f"{ICONS['analytics']}  Analytics e Tendências",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(side="left")

    def _criar_abas(self) -> None:
        self._tabs = Tabs(
            self,
            tabs=["Visao Geral", "Tendencias", "Performance", "Acoes Rapidas"],
            on_select=self._on_tab_select,
            initial=0,
        )
        self._tabs.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["section_gap"]))

    def _criar_conteudo_abas(self) -> None:
        self._overview_container = ctk.CTkFrame(self, fg_color="transparent")
        self._overview_container.pack(fill="both", expand=True, padx=SPACING["page_x"])

        self._trends_container = ctk.CTkFrame(self, fg_color="transparent")
        self._trends_container.pack(fill="both", expand=True, padx=SPACING["page_x"])
        self._trends_container.pack_forget()

        self._performance_container = ctk.CTkFrame(self, fg_color="transparent")
        self._performance_container.pack(fill="both", expand=True, padx=SPACING["page_x"])
        self._performance_container.pack_forget()

        self._actions_container = ctk.CTkFrame(self, fg_color="transparent")
        self._actions_container.pack(fill="both", expand=True, padx=SPACING["page_x"])
        self._actions_container.pack_forget()

        self._containers = [
            self._overview_container,
            self._trends_container,
            self._performance_container,
            self._actions_container,
        ]

    def _on_tab_select(self, idx: int) -> None:
        self._active_tab = idx
        for i, container in enumerate(self._containers):
            if i == idx:
                container.pack(fill="both", expand=True, padx=SPACING["page_x"])
            else:
                container.pack_forget()

    def _atualizar_aba_overview(self, stats, trends, performance) -> None:
        container = self._overview_container
        for child in container.winfo_children():
            child.destroy()

        kpi_frame = ctk.CTkFrame(container, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, spacing("md")))
        kpi_frame.grid_columnconfigure(0, weight=1)
        kpi_frame.grid_columnconfigure(1, weight=1)
        kpi_frame.grid_columnconfigure(2, weight=1)
        kpi_frame.grid_columnconfigure(3, weight=1)

        kpis = [
            ("Estudantes", str(stats.get("total_students", 0)), ICONS["users"], THEME["kpi_violet"], THEME["kpi_violet_soft"]),
            ("Atendimentos Hoje", str(stats.get("appointments_today", 0)), ICONS["calendar"], THEME["kpi_blue"], THEME["kpi_blue_soft"]),
            ("Triagens Pendentes", str(stats.get("screenings_pending", 0)), ICONS["search"], THEME["kpi_amber"], THEME["kpi_amber_soft"]),
            ("Alertas Ativos", str(stats.get("alerts", 0)), ICONS["bell"], THEME["kpi_red"], THEME["kpi_red_soft"]),
        ]
        for i, (title, value, icon, accent, soft) in enumerate(kpis):
            card = KPICard(
                kpi_frame, title=title, value=value, icon=icon,
                accent=accent, trend="", unit="", size="md",
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=(0, spacing("md")))

        search_card = Card(container, title=f"{ICONS['search']}  Busca Global")
        search_card.pack(fill="x", pady=(0, spacing("md")))

        search_frame = ctk.CTkFrame(search_card.body, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, spacing("sm")))

        self._search_field = SearchField(
            search_frame,
            placeholder="Buscar estudantes, agendamentos, triagens...",
            command=self._on_search,
            debounce_ms=400,
        )
        self._search_field.pack(fill="x")

        self._search_results_frame = ctk.CTkFrame(search_card.body, fg_color="transparent")
        self._search_results_frame.pack(fill="x")

        chart_card = Card(container, title=f"{ICONS['chart']}  Tendencia de Humor (30 dias)")
        chart_card.pack(fill="x", pady=(0, spacing("md")))

        self._mini_chart = TrendChart(chart_card.body, title="", unit="")
        trend_data = trends.get("data", []) if trends else []
        self._mini_chart.set_data(trend_data, "Humor medio", "/5")

    def _atualizar_aba_tendencias(self, trends) -> None:
        container = self._trends_container
        for child in container.winfo_children():
            child.destroy()

        if not trends:
            EmptyState(
                container, icon=ICONS["chart"],
                title="Sem dados de tendencia",
                subtitle="Nao ha dados suficientes para exibir graficos",
            ).pack(pady=spacing("xl"))
            return

        sel_frame = ctk.CTkFrame(container, fg_color="transparent")
        sel_frame.pack(fill="x", pady=(0, spacing("md")))

        ctk.CTkLabel(
            sel_frame, text="Metrica:",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left", padx=(0, spacing("sm")))

        self._metric_var = ctk.StringVar(value="mood")
        for label, val in [("Humor", "mood"), ("Bem-estar", "wellbeing"), ("Atendimentos", "appointments")]:
            ctk.CTkRadioButton(
                sel_frame, text=label, variable=self._metric_var, value=val,
                font=themed_font("body"), fg_color=THEME["primary"],
                hover_color=THEME["primary_hover"],
                command=self._on_metric_change,
            ).pack(side="left", padx=(0, spacing("md")))

        self._trend_chart = TrendChart(container, title="Tendencia", unit="")
        self._trend_chart.pack(fill="both", expand=True, pady=(0, spacing("md")))

        data = trends.get("data", [])
        self._trend_chart.set_data(data, trends.get("metric", "Tendencia"), trends.get("unit", ""))

    def _on_metric_change(self) -> None:
        metric = self._metric_var.get()
        def fetch() -> dict:
            return self.controller.carregar_tendencias(metric=metric, days=30)

        def on_success(data: dict) -> None:
            self._trend_data = data
            trend_data = data.get("data", [])
            self._trend_chart.set_data(trend_data, data.get("metric", ""), data.get("unit", ""))

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao carregar tendencia: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _atualizar_aba_performance(self, performance) -> None:
        container = self._performance_container
        for child in container.winfo_children():
            child.destroy()

        if not performance:
            EmptyState(
                container, icon=ICONS["chart"],
                title="Sem dados de performance",
                subtitle="Nao ha dados de performance disponiveis no momento",
            ).pack(pady=spacing("xl"))
            return

        grid = ctk.CTkFrame(container, fg_color="transparent")
        grid.pack(fill="x", pady=(0, spacing("md")))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_columnconfigure(2, weight=1)

        perf_items = [
            ("Taxa de conclusao", f"{performance.get('completion_rate', 0):.0f}%", THEME["success"]),
            ("Duracao media (min)", str(performance.get("avg_session_duration", 0)), THEME["primary"]),
            ("Estudantes ativos", str(performance.get("total_students", 0)), THEME["kpi_violet"]),
            ("Atendimentos hoje", str(performance.get("appointments_today", 0)), THEME["kpi_blue"]),
            ("Triagens pendentes", str(performance.get("screenings_pending", 0)), THEME["kpi_amber"]),
            ("Alertas nao lidos", str(performance.get("alerts_unread", 0)), THEME["kpi_red"]),
        ]
        for i, (title, value, accent) in enumerate(perf_items):
            row = i // 3
            col = i % 3
            card = Card(grid, title=title, elevated=False)
            inner = ctk.CTkFrame(card.body, fg_color="transparent")
            inner.pack(fill="both", expand=True)
            ctk.CTkLabel(
                inner, text=value,
                font=themed_font("h1", "bold"),
                text_color=accent,
            ).pack(pady=(spacing("sm"), 0))
            card.grid(row=row, column=col, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=(0, spacing("md")))

        secondary = ctk.CTkFrame(container, fg_color="transparent")
        secondary.pack(fill="x", pady=(0, spacing("md")))
        secondary.grid_columnconfigure(0, weight=1)
        secondary.grid_columnconfigure(1, weight=1)

        mood_val = performance.get("avg_mood")
        wellness_val = performance.get("avg_wellbeing")

        mood_card = Card(secondary, title=f"{ICONS['mood_good']}  Humor Medio")
        ctk.CTkLabel(
            mood_card.body, text=f"{mood_val:.1f}/5" if mood_val else "—",
            font=themed_font("h1", "bold"),
            text_color=THEME["kpi_amber"],
        ).pack(pady=spacing("sm"))
        mood_card.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["grid_gap"] // 2), pady=(0, spacing("md")))

        wellness_card = Card(secondary, title=f"{ICONS['heart']}  Bem-estar Medio")
        ctk.CTkLabel(
            wellness_card.body, text=f"{wellness_val:.1f}/5" if wellness_val else "—",
            font=themed_font("h1", "bold"),
            text_color=THEME["kpi_green"],
        ).pack(pady=spacing("sm"))
        wellness_card.grid(row=0, column=1, sticky="ew", padx=(SPACING["grid_gap"] // 2, 0), pady=(0, spacing("md")))

    def _atualizar_aba_quick_actions(self, actions) -> None:
        container = self._actions_container
        for child in container.winfo_children():
            child.destroy()

        if not actions:
            EmptyState(
                container, icon=ICONS["check_circle"],
                title="Tudo em dia",
                subtitle="Nenhuma acao rapida sugerida no momento",
            ).pack(pady=spacing("xl"))
            return

        for action in actions:
            _QuickActionRow(
                container, action,
                on_click=self._on_quick_action_click,
            ).pack(fill="x", pady=(0, spacing("xs")))

    def _on_quick_action_click(self, action: dict) -> None:
        target = action.get("target", "")
        if target and hasattr(self.controller, "app"):
            app = self.controller.app
            nav = getattr(app, "navigation", None)
            if nav:
                nav.show(target)

    def _on_search(self, query: str) -> None:
        container = self._search_results_frame
        for child in container.winfo_children():
            child.destroy()

        if not query or not query.strip():
            return

        self._search_results = None

        def fetch() -> dict:
            return self.controller.buscar_global(query)

        def on_success(result: dict) -> None:
            self._search_results = result
            self._render_search_results(result)

        def on_error(exc: Exception) -> None:
            logger.error("Erro na busca global: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _render_search_results(self, result) -> None:
        container = self._search_results_frame
        for child in container.winfo_children():
            child.destroy()

        if not result:
            EmptyState(
                container, icon=ICONS["search"],
                title="Sem resultados",
                subtitle="Nenhum resultado encontrado para a busca",
            ).pack(pady=spacing("md"))
            return

        students = result.get("students", [])
        appointments = result.get("appointments", [])
        screenings = result.get("screenings", [])

        total = len(students) + len(appointments) + len(screenings)
        if total == 0:
            EmptyState(
                container, icon=ICONS["search"],
                title="Sem resultados",
                subtitle="Nenhum resultado encontrado para a busca",
            ).pack(pady=spacing("md"))
            return

        ctk.CTkLabel(
            container, text=f"{total} resultado(s) encontrado(s)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, spacing("xs")))

        for s in students:
            _SearchResultRow(
                container, s,
                on_click=self._abrir_detalhe_busca,
            ).pack(fill="x", pady=(0, spacing("xs")))

        for ap in appointments:
            _SearchResultRow(
                container, ap,
                on_click=self._abrir_detalhe_busca,
            ).pack(fill="x", pady=(0, spacing("xs")))

        for t in screenings:
            _SearchResultRow(
                container, t,
                on_click=self._abrir_detalhe_busca,
            ).pack(fill="x", pady=(0, spacing("xs")))

    def _abrir_detalhe_busca(self, item: dict) -> None:
        SearchDetailModal(
            self, item,
            on_navigate=self._on_quick_action_click,
        )

    @staticmethod
    def _limpar(widget) -> None:
        for child in widget.winfo_children():
            child.destroy()

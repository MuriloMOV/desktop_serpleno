import logging
import time
from datetime import date, timedelta

import customtkinter as ctk

from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.components.ui_components import (
    BaseModal,
    Card,
    Divider,
    EmptyState,
    KPICard,
    ListRow,
    PrimaryButton,
    SearchField,
    SkeletonLoader,
    Tabs,
    bind_clickable,
)
from ser_pleno.ui.theme import FONT_FAMILY, RADIUS, SPACING, THEME, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms

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
        self._t0 = time.perf_counter()
        super().__init__(
            parent,
            fg_color=THEME["bg"],
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.controller = controller
        self._active_tab = 0
        self.servico_analytics = getattr(controller, "servico_analytics", None)
        self._trend_data = None
        self._search_results = None
        self._quick_actions = None
        self._retention_data = None
        self._conversion_data = None
        self._journey_data = None
        self._peak_hours_data = None
        self._workload_data = None
        self._prediction_data = None
        self._journey_student_id = None

        self._criar_cabecalho()
        self._criar_abas()
        self._criar_conteudo_abas()
        self._carregar_dados()
        log_view_init_ms("analytics", self._t0, widget_ref=self)

    def _carregar_dados(self):
        self._mostrar_skeletons()

        def fetch() -> tuple:
            stats = self.servico_analytics.obter_estatisticas_dashboard()
            trends = self.servico_analytics.obter_tendencias(metric="mood", days=30)
            performance = self.servico_analytics.obter_performance()
            actions = self.servico_analytics.obter_quick_actions()
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            retention = self.servico_analytics.calculate_retention_rate(start_date, end_date)
            conversion = self.servico_analytics.calculate_conversion_rate("scheduled", "completed", (start_date, end_date))
            peak_hours = self.servico_analytics.get_peak_hours()
            workload = self.servico_analytics.get_psychologist_workload()
            return stats, trends, performance, actions, retention, conversion, peak_hours, workload

        def on_success(result: tuple) -> None:
            stats, trends, performance, actions, retention, conversion, peak_hours, workload = result
            self._trend_data = trends
            self._quick_actions = actions
            self._retention_data = retention
            self._conversion_data = conversion
            self._peak_hours_data = peak_hours
            self._workload_data = workload
            self._atualizar_aba_overview(stats, trends, performance)
            self._atualizar_aba_tendencias(trends)
            self._atualizar_aba_performance(performance)
            self._atualizar_aba_quick_actions(actions)
            self._atualizar_aba_retention(retention)
            self._atualizar_aba_conversion(conversion)
            self._atualizar_aba_peak_hours(peak_hours)
            self._atualizar_aba_workload(workload)

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao carregar analytics: %s", exc)

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
            ("retention", "_retention_container"),
            ("conversion", "_conversion_container"),
            ("journey", "_journey_container"),
            ("peak_hours", "_peak_hours_container"),
            ("workload", "_workload_container"),
            ("prediction", "_prediction_container"),
            ("actions", "_actions_container"),
        ]:
            container = getattr(self, attr, None)
            if container and container.winfo_exists():
                self._limpar(container)
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
            tabs=["Visao Geral", "Tendencias", "Performance", "Taxa Retencao", "Taxa Conversao", "Jornada", "Horarios Pico", "Carga Psicologos", "Predicao Falta", "Acoes Rapidas"],
            on_select=self._on_tab_select,
            initial=0,
        )
        self._tabs.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["section_gap"]))

    def _criar_conteudo_abas(self) -> None:
        self._overview_container = ctk.CTkFrame(self, fg_color="transparent")
        self._trends_container = ctk.CTkFrame(self, fg_color="transparent")
        self._performance_container = ctk.CTkFrame(self, fg_color="transparent")
        self._retention_container = ctk.CTkFrame(self, fg_color="transparent")
        self._conversion_container = ctk.CTkFrame(self, fg_color="transparent")
        self._journey_container = ctk.CTkFrame(self, fg_color="transparent")
        self._peak_hours_container = ctk.CTkFrame(self, fg_color="transparent")
        self._workload_container = ctk.CTkFrame(self, fg_color="transparent")
        self._prediction_container = ctk.CTkFrame(self, fg_color="transparent")
        self._actions_container = ctk.CTkFrame(self, fg_color="transparent")

        self._containers = [
            self._overview_container,
            self._trends_container,
            self._performance_container,
            self._retention_container,
            self._conversion_container,
            self._journey_container,
            self._peak_hours_container,
            self._workload_container,
            self._prediction_container,
            self._actions_container,
        ]

        for i, container in enumerate(self._containers):
            container.pack(fill="both", expand=True, padx=SPACING["page_x"])
            if i != 0:
                container.pack_forget()

    def _on_tab_select(self, idx: int) -> None:
        self._active_tab = idx
        for i, container in enumerate(self._containers):
            if i == idx:
                container.pack(fill="both", expand=True, padx=SPACING["page_x"])
            else:
                container.pack_forget()

        if idx == 5 and not self._journey_data:
            self._atualizar_aba_journey(None)
        elif idx == 8 and not self._prediction_data:
            self._atualizar_aba_prediction(None)

    def _atualizar_aba_overview(self, stats, trends, performance) -> None:
        container = self._overview_container
        self._limpar(container)

        kpi_frame = ctk.CTkFrame(container, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, spacing("md")))
        for col in range(4):
            kpi_frame.grid_columnconfigure(col, weight=1)

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
        self._limpar(container)

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
            return self.servico_analytics.obter_tendencias(metric=metric, days=30)

        def on_success(data: dict) -> None:
            self._trend_data = data
            trend_data = data.get("data", [])
            self._trend_chart.set_data(trend_data, data.get("metric", ""), data.get("unit", ""))

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao carregar tendencia: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _atualizar_aba_performance(self, performance) -> None:
        container = self._performance_container
        self._limpar(container)

        if not performance:
            EmptyState(
                container, icon=ICONS["chart"],
                title="Sem dados de performance",
                subtitle="Nao ha dados de performance disponiveis no momento",
            ).pack(pady=spacing("xl"))
            return

        grid = ctk.CTkFrame(container, fg_color="transparent")
        grid.pack(fill="x", pady=(0, spacing("md")))
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)

        perf_items = [
            ("Taxa de conclusao", f"{performance.get('completion_rate', 0):.0f}%", THEME["success"]),
            ("Duracao media (min)", str(performance.get("avg_session_duration", 0)), THEME["primary"]),
            ("Estudantes ativos", str(performance.get("total_students", 0)), THEME["kpi_violet"]),
            ("Atendimentos hoje", str(performance.get("appointments_today", 0)), THEME["kpi_blue"]),
            ("Triagens pendentes", str(performance.get("screenings_pending", 0)), THEME["kpi_amber"]),
            ("Alertas nao lidos", str(performance.get("alerts_unread", 0)), THEME["kpi_red"]),
        ]
        for i, (title, value, accent) in enumerate(perf_items):
            card = Card(grid, title=title, elevated=False)
            inner = ctk.CTkFrame(card.body, fg_color="transparent")
            inner.pack(fill="both", expand=True)
            ctk.CTkLabel(
                inner, text=value,
                font=themed_font("h1", "bold"),
                text_color=accent,
            ).pack(pady=(spacing("sm"), 0))
            card.grid(row=i // 3, column=i % 3, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=(0, spacing("md")))

        secondary = ctk.CTkFrame(container, fg_color="transparent")
        secondary.pack(fill="x", pady=(0, spacing("md")))
        secondary.grid_columnconfigure(0, weight=1)
        secondary.grid_columnconfigure(1, weight=1)

        metrics = [
            ("Humor Medio", performance.get("avg_mood"), ICONS["mood_good"], THEME["kpi_amber"], 0, (0, SPACING["grid_gap"] // 2)),
            ("Bem-estar Medio", performance.get("avg_wellbeing"), ICONS["heart"], THEME["kpi_green"], 1, (SPACING["grid_gap"] // 2, 0)),
        ]

        for title, val, icon, color, col, padx in metrics:
            card = Card(secondary, title=f"{icon}  {title}")
            ctk.CTkLabel(
                card.body, text=f"{val:.1f}/5" if val else "—",
                font=themed_font("h1", "bold"),
                text_color=color,
            ).pack(pady=spacing("sm"))
            card.grid(row=0, column=col, sticky="ew", padx=padx, pady=(0, spacing("md")))

    def _atualizar_aba_quick_actions(self, actions) -> None:
        container = self._actions_container
        self._limpar(container)

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
        self._limpar(container)

        if not query or not query.strip():
            return

        self._search_results = None

        def fetch() -> list:
            return self.servico_analytics.search_students(query)

        def on_success(result: list) -> None:
            self._search_results = result
            self._render_search_results(result)

        def on_error(exc: Exception) -> None:
            logger.error("Erro na busca de estudantes: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _render_search_results(self, result) -> None:
        container = self._search_results_frame
        self._limpar(container)

        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            items = (
                result.get("students", []) +
                result.get("appointments", []) +
                result.get("screenings", [])
            )

        if not items:
            EmptyState(
                container, icon=ICONS["search"],
                title="Sem resultados",
                subtitle="Nenhum estudante encontrado para a busca",
            ).pack(pady=spacing("md"))
            return

        ctk.CTkLabel(
            container, text=f"{len(items)} estudante(s) encontrado(s)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, spacing("xs")))

        for item in items:
            _SearchResultRow(
                container, item,
                on_click=self._abrir_detalhe_busca,
            ).pack(fill="x", pady=(0, spacing("xs")))

    def _abrir_detalhe_busca(self, item: dict) -> None:
        SearchDetailModal(
            self, item,
            on_navigate=self._on_quick_action_click,
        )

    def _atualizar_aba_retention(self, data) -> None:
        container = self._retention_container
        self._limpar(container)

        if not data:
            EmptyState(
                container, icon=ICONS["users"],
                title="Sem dados de retencao",
                subtitle="Nao ha dados suficientes para exibir a taxa de retencao",
            ).pack(pady=spacing("xl"))
            return

        kpi_frame = ctk.CTkFrame(container, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, spacing("md")))
        for col in range(3):
            kpi_frame.grid_columnconfigure(col, weight=1)

        kpis = [
            ("Taxa de Retencao", f"{data.get('retention_rate', 0):.1f}%", "↑", THEME["success"]),
            ("Estudantes Ativos", str(data.get("total_students", 0)), ICONS["users"], THEME["kpi_violet"]),
            ("Mantidos", str(data.get("retained_students", 0)), ICONS["check"], THEME["kpi_green"]),
        ]
        for i, (title, value, icon, accent) in enumerate(kpis):
            card = KPICard(
                kpi_frame, title=title, value=value, icon=icon,
                accent=accent, trend="", unit="", size="md",
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=(0, spacing("md")))

        info_card = Card(container, title=f"{ICONS['info']}  Sobre a taxa de retencao")
        info_card.pack(fill="x", pady=(0, spacing("md")))
        ctk.CTkLabel(
            info_card.body,
            text="A taxa de retencao mede o percentual de estudantes que retornaram para um novo atendimento nos ultimos 30 dias, comparando com o periodo anterior de 30 dias.",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
            wraplength=600,
        ).pack(anchor="w", pady=spacing("sm"))

    def _atualizar_aba_conversion(self, data) -> None:
        container = self._conversion_container
        self._limpar(container)

        if not data:
            EmptyState(
                container, icon=ICONS["chart"],
                title="Sem dados de conversao",
                subtitle="Nao ha dados suficientes para exibir a taxa de conversao",
            ).pack(pady=spacing("xl"))
            return

        kpi_frame = ctk.CTkFrame(container, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, spacing("md")))
        for col in range(3):
            kpi_frame.grid_columnconfigure(col, weight=1)

        kpis = [
            ("Taxa de Conversao", f"{data.get('conversion_rate', 0):.1f}%", "↑", THEME["success"]),
            ("No Estagio Inicial", str(data.get("total", 0)), ICONS["calendar"], THEME["kpi_blue"]),
            ("Convertidos", str(data.get("converted", 0)), ICONS["check"], THEME["kpi_green"]),
        ]
        for i, (title, value, icon, accent) in enumerate(kpis):
            card = KPICard(
                kpi_frame, title=title, value=value, icon=icon,
                accent=accent, trend="", unit="", size="md",
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=(0, spacing("md")))

        detail_card = Card(container, title=f"{ICONS['info']}  Detalhes da conversao")
        detail_card.pack(fill="x", pady=(0, spacing("md")))
        ctk.CTkLabel(
            detail_card.body,
            text=f"Estagio inicial: {data.get('from_stage', '')} -> Estagio final: {data.get('to_stage', '')}",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(anchor="w", pady=spacing("sm"))

    def _atualizar_aba_journey(self, data) -> None:
        container = self._journey_container
        self._limpar(container)

        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, spacing("md")))

        ctk.CTkLabel(
            search_frame, text="ID do Estudante:",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left", padx=(0, spacing("sm")))

        journey_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Digite o ID do estudante...",
            width=200,
            font=themed_font("body"),
        )
        journey_entry.pack(side="left", padx=(0, spacing("sm")))

        ctk.CTkButton(
            search_frame,
            text="Buscar",
            command=lambda: self._on_journey_search(journey_entry.get()),
            font=themed_font("caption", "bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            width=80,
        ).pack(side="left")

        if not data or not data.get("events"):
            EmptyState(
                container, icon="📈",
                title="Sem eventos",
                subtitle="Selecione um estudante para ver sua jornada",
            ).pack(pady=spacing("xl"))
            return

        events = data.get("events", [])
        student_id = data.get("student_id")

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, spacing("md")))
        ctk.CTkLabel(
            header, text=f"Jornada do Estudante #{student_id}",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(side="left")

        timeline = ctk.CTkFrame(container, fg_color="transparent")
        timeline.pack(fill="both", expand=True)

        for idx, event in enumerate(events):
            row = ctk.CTkFrame(timeline, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"])
            row.pack(fill="x", pady=(0, spacing("xs")))

            type_colors = {
                "orientation": THEME["kpi_blue"],
                "intervention": THEME["kpi_amber"],
                "screening": THEME["kpi_violet"],
                "appointment": THEME["kpi_green"],
                "mood": THEME["kpi_red"],
            }
            color = type_colors.get(event.get("type", ""), THEME["primary"])

            icon_map = {
                "orientation": ICONS["brain"],
                "intervention": ICONS["handshake"],
                "screening": ICONS["search"],
                "appointment": ICONS["calendar"],
                "mood": ICONS["mood_good"],
            }
            icon = icon_map.get(event.get("type", ""), ICONS["info"])

            ctk.CTkLabel(
                row, text=icon,
                font=themed_font("h3"),
                text_color=color,
            ).pack(side="left", padx=(spacing("md"), spacing("sm")), pady=spacing("md"))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, pady=spacing("md"))

            ctk.CTkLabel(
                info, text=event.get("detail", ""),
                font=themed_font("body", "bold"),
                text_color=THEME["text"], anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                info, text=event.get("date", ""),
                font=themed_font("caption"),
                text_color=THEME["text_muted"], anchor="w",
            ).pack(anchor="w", pady=(spacing("xs"), 0))

    def _atualizar_aba_peak_hours(self, data) -> None:
        container = self._peak_hours_container
        self._limpar(container)

        if not data or not data.get("peak_hours"):
            EmptyState(
                container, icon=ICONS["schedule"],
                title="Sem dados de horarios",
                subtitle="Nao ha dados de horarios de pico disponiveis",
            ).pack(pady=spacing("xl"))
            return

        peak_hours = data.get("peak_hours", [])
        hour_distribution = data.get("hour_distribution", {})

        kpi_frame = ctk.CTkFrame(container, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, spacing("md")))
        for col in range(3):
            kpi_frame.grid_columnconfigure(col, weight=1)

        top_hour = peak_hours[0] if peak_hours else {}
        kpis = [
            ("Hora de Pico", f"{top_hour.get('hour', 0):02d}:00", ICONS["hourglass"], THEME["kpi_blue"]),
            ("Atendimentos no Pico", str(top_hour.get("count", 0)), ICONS["calendar"], THEME["kpi_amber"]),
            ("Total de Horas", str(len(hour_distribution)), ICONS["clock"], THEME["kpi_violet"]),
        ]
        for i, (title, value, icon, accent) in enumerate(kpis):
            card = KPICard(
                kpi_frame, title=title, value=value, icon=icon,
                accent=accent, trend="", unit="", size="md",
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=(0, spacing("md")))

        list_card = Card(container, title=f"{ICONS['schedule']}  Distribuicao por Hora")
        list_card.pack(fill="x", pady=(0, spacing("md")))

        for hour_info in peak_hours:
            hour = hour_info.get("hour", 0)
            count = hour_info.get("count", 0)
            row = ListRow(
                list_card.body,
                title=f"{hour:02d}:00 - {hour:02d}:59",
                subtitle=f"{count} atendimento(s)",
                color=THEME["primary"],
                soft_color=THEME["primary_soft"],
                trailing_badge=str(count),
                icon=ICONS["calendar"],
            )
            row.pack(fill="x", pady=(0, spacing("xs")))

    def _atualizar_aba_workload(self, data) -> None:
        container = self._workload_container
        self._limpar(container)

        if not data or not data.get("workload"):
            EmptyState(
                container, icon=ICONS["psychology"],
                title="Sem dados de carga",
                subtitle="Nao ha dados de carga de trabalho disponiveis",
            ).pack(pady=spacing("xl"))
            return

        workload = data.get("workload", [])
        total = data.get("total_appointments", 0)

        kpi_frame = ctk.CTkFrame(container, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, spacing("md")))
        for col in range(2):
            kpi_frame.grid_columnconfigure(col, weight=1)

        kpis = [
            ("Total Atendimentos", str(total), ICONS["calendar"], THEME["kpi_blue"]),
            ("Profissionais", str(len(workload)), ICONS["users"], THEME["kpi_violet"]),
        ]
        for i, (title, value, icon, accent) in enumerate(kpis):
            card = KPICard(
                kpi_frame, title=title, value=value, icon=icon,
                accent=accent, trend="", unit="", size="md",
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=(0, spacing("md")))

        list_card = Card(container, title=f"{ICONS['users']}  Carga por Profissional")
        list_card.pack(fill="x", pady=(0, spacing("md")))

        for w in workload:
            row = ListRow(
                list_card.body,
                title=w.get("name", "Nao atribuido"),
                subtitle=f"Orientacoes: {w.get('orientations', 0)} | Intervencoes: {w.get('interventions', 0)} | Triagens: {w.get('screenings', 0)}",
                color=THEME["primary"],
                soft_color=THEME["primary_soft"],
                trailing_badge=str(w.get("total", 0)),
                icon=ICONS["user"],
            )
            row.pack(fill="x", pady=(0, spacing("xs")))

    def _atualizar_aba_prediction(self, data) -> None:
        container = self._prediction_container
        self._limpar(container)

        search_frame = ctk.CTkFrame(container, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, spacing("md")))

        ctk.CTkLabel(
            search_frame, text="ID do Agendamento:",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left", padx=(0, spacing("sm")))

        prediction_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Digite o ID do agendamento...",
            width=200,
            font=themed_font("body"),
        )
        prediction_entry.pack(side="left", padx=(0, spacing("sm")))

        ctk.CTkButton(
            search_frame,
            text="Buscar",
            command=lambda: self._on_prediction_search(prediction_entry.get()),
            font=themed_font("caption", "bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            width=80,
        ).pack(side="left")

        if not data:
            EmptyState(
                container, icon=ICONS["alert"],
                title="Sem predicao",
                subtitle="Informe o ID do agendamento para ver a probabilidade de falta",
            ).pack(pady=spacing("xl"))
            return

        probability = data.get("no_show_probability", 0.0)
        risk_level = data.get("risk_level", "low")

        risk_colors = {
            "low": THEME["success"],
            "medium": THEME["warning"],
            "high": THEME["danger"],
        }
        risk_labels = {
            "low": "Baixo",
            "medium": "Medio",
            "high": "Alto",
        }

        kpi_frame = ctk.CTkFrame(container, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, spacing("md")))
        for col in range(3):
            kpi_frame.grid_columnconfigure(col, weight=1)

        kpis = [
            ("Probabilidade de Falta", f"{probability:.1f}%", ICONS["alert"], risk_colors.get(risk_level, THEME["warning"])),
            ("Nivel de Risco", risk_labels.get(risk_level, "Baixo"), ICONS["priority_high"], risk_colors.get(risk_level, THEME["success"])),
            ("Agendamento", f"#{data.get('appointment_id', '')}", ICONS["calendar"], THEME["kpi_blue"]),
        ]
        for i, (title, value, icon, accent) in enumerate(kpis):
            card = KPICard(
                kpi_frame, title=title, value=value, icon=icon,
                accent=accent, trend="", unit="", size="md",
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=(0, spacing("md")))

        risk_factors = data.get("risk_factors", [])
        if risk_factors:
            detail_card = Card(container, title=f"{ICONS['alert']}  Fatores de Risco")
            detail_card.pack(fill="x", pady=(0, spacing("md")))
            for factor in risk_factors:
                ctk.CTkLabel(
                    detail_card.body,
                    text=f"• {factor}",
                    font=themed_font("body"),
                    text_color=THEME["text_secondary"],
                    anchor="w",
                ).pack(anchor="w", pady=spacing("xs"))

    def _carregar_jornada(self, student_id: int) -> None:
        container = self._journey_container
        self._limpar(container)

        def fetch() -> dict:
            return self.servico_analytics.get_student_journey(student_id)

        def on_success(data: dict) -> None:
            self._journey_data = data
            self._atualizar_aba_journey(data)

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao carregar jornada: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _carregar_predicao(self, appointment_id: int) -> None:
        container = self._prediction_container
        self._limpar(container)

        def fetch() -> dict:
            return self.servico_analytics.predict_no_show(appointment_id)

        def on_success(data: dict) -> None:
            self._prediction_data = data
            self._atualizar_aba_prediction(data)

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao carregar predicao: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _on_journey_search(self, student_id_str: str) -> None:
        if not student_id_str or not student_id_str.strip():
            return
        try:
            student_id = int(student_id_str.strip())
        except ValueError:
            return
        self._journey_student_id = student_id
        self._carregar_jornada(student_id)

    def _on_prediction_search(self, appointment_id_str: str) -> None:
        if not appointment_id_str or not appointment_id_str.strip():
            return
        try:
            appointment_id = int(appointment_id_str.strip())
        except ValueError:
            return
        self._carregar_predicao(appointment_id)

    @staticmethod
    def _limpar(widget) -> None:
        for child in widget.winfo_children():
            child.destroy()
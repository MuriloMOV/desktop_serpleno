import logging
import customtkinter as ctk
from components.ui_components import Divider, PrimaryButton, GhostButton
from services.relatorios import ServicoRelatorio
from utils.async_runner import AsyncRunner
from ui_theme import THEME, SPACING, RADIUS, font, themed_font

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
#  Design tokens – família índigo (consistente com todo o sistema)
# ══════════════════════════════════════════════════════════════════════════════

# Mapeamento chip por tipo
_CHIP = {
    "Geral":         (THEME["chip_geral_bg"],     THEME["chip_geral_text"]),
    "Estudante":     (THEME["chip_estudante_bg"],  THEME["chip_estudante_text"]),
    "Agendamentos":  (THEME["chip_agenda_bg"],     THEME["chip_agenda_text"]),
    "Intervenções":  (THEME["kpi_violet_soft"],    THEME["kpi_violet"]),
    "Triagens":      (THEME["kpi_amber_soft"],     THEME["kpi_amber"]),
    "Estatísticas":  (THEME["export_item_bg"],     THEME["accent"]),
}

# KPIs (título, ícone, acento, soft, chave nos dados)
_KPIS = [
    ("Estudantes",    "🎓", THEME["kpi_blue"],   THEME["kpi_blue_soft"],   "students_total"),
    ("Agendamentos",  "📅", THEME["kpi_green"],  THEME["kpi_green_soft"],  "appointments_total"),
    ("Intervenções",  "🤝", THEME["kpi_violet"], THEME["kpi_violet_soft"], "interventions_total"),
    ("Triagens",      "🔍", THEME["kpi_amber"],  THEME["kpi_amber_soft"],  "screenings_total"),
]

# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de layout
# ──────────────────────────────────────────────────────────────────────────────
def _card(parent, **kwargs) -> ctk.CTkFrame:
    return ctk.CTkFrame(
        parent,
        fg_color=THEME["surface"],
        corner_radius=RADIUS["card"],
        border_width=1,
        border_color=THEME["border"],
        **kwargs,
    )

def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=THEME["divider"]).pack(fill="x")

def _section_title(parent, text: str, pady=(16, 12)):
    ctk.CTkLabel(
        parent, text=text,
        font=themed_font("body", "bold"),
        text_color=THEME["text"], anchor="w",
    ).pack(fill="x", padx=20, pady=pady)

def _chip(parent, text: str, tipo: str = "") -> ctk.CTkFrame:
    bg, fg = _CHIP.get(tipo, (THEME["chip_default_bg"], THEME["chip_default_text"]))
    f = ctk.CTkFrame(parent, fg_color=bg, corner_radius=RADIUS["md"])
    ctk.CTkLabel(
        f, text=text,
        font=themed_font("body_sm", "bold"),
        text_color=fg,
    ).pack(padx=10, pady=3)
    return f

# ══════════════════════════════════════════════════════════════════════════════
#  Componente: KPI Card
# ══════════════════════════════════════════════════════════════════════════════
class _KPICard(ctk.CTkFrame):
    def __init__(self, parent, title: str, icon: str,
                 accent: str, soft: str, sub: str = ""):
        super().__init__(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
        )
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["card_pad"])

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        icon_bg = ctk.CTkFrame(top, width=44, height=44, corner_radius=RADIUS["button"], fg_color=soft)
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon,
                     font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")

        self._val_lbl = ctk.CTkLabel(
            top, text="—",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"],
        )
        self._val_lbl.pack(side="right", anchor="e")

        ctk.CTkLabel(
            inner, text=title,
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(fill="x", pady=(SPACING["icon_gap"], SPACING["label_gap"]))

        if sub:
            ctk.CTkLabel(
                inner, text=sub,
                font=themed_font("body_sm"),
                text_color=THEME["text_muted"], anchor="w",
            ).pack(fill="x")

        ctk.CTkFrame(self, height=3, corner_radius=RADIUS["none"], fg_color=accent).pack(
            side="bottom", fill="x"
        )

    def set_value(self, v: str):
        self._val_lbl.configure(text=v)

# ══════════════════════════════════════════════════════════════════════════════
#  RelatorioFrame
# ══════════════════════════════════════════════════════════════════════════════
class RelatorioFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(
            parent,
            fg_color=THEME["page_bg"],
            scrollbar_button_color="#C7D2FE",
            scrollbar_button_hover_color="#A5B4FC",
        )
        self.controller        = controller
        self.servico_relatorio = ServicoRelatorio()
        self._kpi_cards: dict[str, _KPICard] = {}
        self._summary_vals: dict[str, ctk.CTkLabel] = {}
        self._chart_data   = []

        self._criar_cabecalho()
        self._criar_kpis()
        self._criar_grid_central()
        self._criar_secao_exportacao()
        self._criar_lista_relatorios()
        self._carregar_dados()

    # ══════════════════════════════════════════
    #  Dados
    # ══════════════════════════════════════════
    def _carregar_dados(self):
        def fetch():
            stats   = self.servico_relatorio.obter_estatisticas()
            reports = self.servico_relatorio.listar_relatorios()
            return stats, reports

        AsyncRunner.run(
            task=fetch,
            on_success=lambda res: self._atualizar_view(*res),
            on_error=lambda exc: ctk.CTkMessagebox(
                self, title="Erro",
                message=f"Não foi possível carregar relatórios.\n{exc}",
                icon="error",
            ),
            widget_ref=self,
        )

    def _atualizar_view(self, stats_res, reports_res):
        if stats_res.get("success"):
            summary = stats_res.get("data", {}).get("summary", {})
            for _, _, _, _, key in _KPIS:
                title_map = {
                    "students_total":      "Estudantes",
                    "appointments_total":  "Agendamentos",
                    "interventions_total": "Intervenções",
                    "screenings_total":    "Triagens",
                }
                t = title_map.get(key, key)
                if t in self._kpi_cards:
                    self._kpi_cards[t].set_value(str(summary.get(key, 0)))

            # Resumo lateral
            mapping_resumo = {
                "total_estudantes":   summary.get("students_total", "—"),
                "consultas_30d":      summary.get("appointments_30d", "—"),
                "intervencoes_30d":   summary.get("interventions_30d", "—"),
                "triagens_30d":       summary.get("screenings_30d", "—"),
                "comparecimento":     summary.get("attendance_rate", "—"),
            }
            for key, val in mapping_resumo.items():
                if key in self._summary_vals:
                    self._summary_vals[key].configure(text=str(val))

            # Gráfico
            self._chart_data = stats_res.get("data", {}).get("monthly", [])
            self._draw_chart()

        if reports_res.get("success"):
            data = reports_res.get("data", {})
            if isinstance(data, list):
                items = data
            else:
                items = data.get("reports") or data.get("results") or []
            if isinstance(items, dict):
                items = []
            self._popular_lista(items)

    # Aliases legados
    def load_data(self):
        self._carregar_dados()

    def update_view(self, stats_res, reports_res):
        self._atualizar_view(stats_res, reports_res)

    def update_card(self, key, value):
        if key in self._kpi_cards:
            self._kpi_cards[key].set_value(value)

    def populate_reports_list(self, reports):
        self._popular_lista(reports)

    def criar_layout(self):
        pass  # compatibilidade

    # ══════════════════════════════════════════
    #  CABEÇALHO
    # ══════════════════════════════════════════
    def _criar_cabecalho(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], SPACING["label_gap"]))

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(
            left, text="Relatórios",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left, text="Visão gerencial e indicadores do sistema",
            font=themed_font("body"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(SPACING["label_gap"], 0))

        PrimaryButton(
            bar,
            text="＋  Gerar Relatório",
            command=lambda: None,
            height=40, corner_radius=RADIUS["button"], width=180,
        ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color=THEME["border"]).pack(
            fill="x", padx=SPACING["page_x"], pady=(SPACING["item_gap"], 0)
        )

    # ══════════════════════════════════════════
    #  KPIs
    # ══════════════════════════════════════════
    def _criar_kpis(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

        for i, (title, icon, accent, soft, _) in enumerate(_KPIS):
            row.grid_columnconfigure(i, weight=1)
            card = _KPICard(row, title, icon, accent, soft,
                            sub="Total cadastrado" if i == 0 else "Total registrado")
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["icon_gap"] // 2)
            self._kpi_cards[title] = card

    # ══════════════════════════════════════════
    #  GRID CENTRAL: gráfico + resumo
    # ══════════════════════════════════════════
    def _criar_grid_central(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))
        grid.grid_columnconfigure(0, weight=3)
        grid.grid_columnconfigure(1, weight=2)

        self._criar_card_grafico(grid)
        self._criar_card_resumo(grid)

    # ── Gráfico ─────────────────────────────────────────────────────────────
    def _criar_card_grafico(self, parent):
        card = _card(parent)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Cabeçalho do card
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))

        ctk.CTkLabel(
            hdr, text="Atividades nos Últimos 30 Dias",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        # Legenda
        leg = ctk.CTkFrame(hdr, fg_color="transparent")
        leg.pack(side="right")
        for label, color in [
            ("Agendamentos", THEME["chart_bar_1"]),
            ("Intervenções", THEME["chart_bar_2"]),
            ("Triagens",     THEME["chart_bar_3"]),
        ]:
            dot_row = ctk.CTkFrame(leg, fg_color="transparent")
            dot_row.pack(side="left", padx=SPACING["icon_gap"] // 2)
            ctk.CTkFrame(dot_row, width=10, height=10, corner_radius=RADIUS["sm"],
                         fg_color=color).pack(side="left", padx=(0, SPACING["label_gap"] // 2))
            ctk.CTkLabel(dot_row, text=label,
                         font=themed_font("body_sm"),
                         text_color=THEME["text_muted"]).pack(side="left")

        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))

        self.canvas_chart = ctk.CTkCanvas(
            card, bg=THEME["surface"], height=220, highlightthickness=0
        )
        self.canvas_chart.pack(fill="both", expand=True, padx=SPACING["icon_gap"], pady=(SPACING["label_gap"], SPACING["item_gap"]))
        self.canvas_chart.bind("<Configure>", lambda e: self._draw_chart())

    def _draw_chart(self, data=None):
        if data is not None:
            self._chart_data = data

        self.canvas_chart.delete("all")
        cw = self.canvas_chart.winfo_width()
        ch = self.canvas_chart.winfo_height()
        if cw < 60 or ch < 60:
            return

        # Dados de exemplo se vazio
        samples = self._chart_data or [
            {"label": "Jan", "appointments": 12, "interventions": 5, "screenings": 8},
            {"label": "Fev", "appointments": 18, "interventions": 7, "screenings": 11},
            {"label": "Mar", "appointments": 14, "interventions": 9, "screenings": 6},
            {"label": "Abr", "appointments": 22, "interventions": 6, "screenings": 14},
            {"label": "Mai", "appointments": 16, "interventions": 11, "screenings": 9},
            {"label": "Jun", "appointments": 25, "interventions": 8, "screenings": 17},
            {"label": "Jul", "appointments": 19, "interventions": 12, "screenings": 10},
        ]

        mx, my = 40, 20
        bw = (cw - 2 * mx) / max(1, len(samples))
        series = [
            ("appointments",  THEME["chart_bar_1"], THEME["chart_bar_soft_1"]),
            ("interventions", THEME["chart_bar_2"], THEME["chart_bar_soft_2"]),
            ("screenings",    THEME["chart_bar_3"], THEME["chart_bar_soft_3"]),
        ]

        all_vals = [s[k] for s in samples for k, *_ in series if k in s]
        max_v    = max(all_vals) if all_vals else 1
        bar_w    = max(4, int(bw / (len(series) + 1.5)))

        # Linhas de grade
        for i in range(5):
            gy = my + i * (ch - 2 * my) / 4
            self.canvas_chart.create_line(
                mx, gy, cw - mx, gy,
                fill=THEME["chart_grid"], dash=(3, 4),
            )
            val_lbl = int(max_v * (1 - i / 4))
            self.canvas_chart.create_text(
                mx - 4, gy, text=str(val_lbl),
                font=(FONT_FAMILY, 8), fill=THEME["text_secondary"], anchor="e",
            )

        for i, sample in enumerate(samples):
            group_x = mx + i * bw + bw / 2 - (len(series) * bar_w) / 2

            for j, (key, color, _) in enumerate(series):
                v    = sample.get(key, 0)
                h    = (v / max_v) * (ch - 2 * my) if max_v else 0
                x0   = group_x + j * (bar_w + 2)
                x1   = x0 + bar_w
                y0   = ch - my - h
                y1   = ch - my

                # Barra com topo arredondado simulado
                self.canvas_chart.create_rectangle(
                    x0, y0 + 4, x1, y1, fill=color, outline="",
                )
                self.canvas_chart.create_oval(
                    x0, y0, x1, y0 + 8, fill=color, outline="",
                )

            # Label do grupo
            lx = mx + i * bw + bw / 2
            self.canvas_chart.create_text(
                lx, ch - 6, text=sample.get("label", ""),
                font=(FONT_FAMILY, 8), fill=THEME["text_muted"],
            )

    # ── Resumo lateral ───────────────────────────────────────────────────────
    def _criar_card_resumo(self, parent):
        card = _card(parent)
        card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        _section_title(card, "Resumo do Período")
        ctk.CTkFrame(card, height=1, fg_color=THEME["divider"]).pack(
            fill="x", padx=20, pady=(0, 8)
        )

        rows_cfg = [
            ("total_estudantes",  "Total de Estudantes",   THEME["text"],           None),
            ("consultas_30d",     "Consultas (30d)",        THEME["text"],           None),
            ("intervencoes_30d",  "Intervenções (30d)",     THEME["text"],           None),
            ("triagens_30d",      "Triagens (30d)",         THEME["text"],           None),
        ]

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=(0, 4))

        for key, label, _, _ in rows_cfg:
            row = ctk.CTkFrame(body, fg_color=THEME["row_bg"], corner_radius=RADIUS["md"])
            row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
            ctk.CTkLabel(
                row, text=label,
                font=themed_font("body"),
                text_color=THEME["text_secondary"], anchor="w",
            ).pack(side="left", padx=SPACING["icon_gap"], pady=SPACING["icon_gap"])
            val_lbl = ctk.CTkLabel(
                row, text="—",
                font=themed_font("body", "bold"),
                text_color=THEME["text"],
            )
            val_lbl.pack(side="right", padx=SPACING["icon_gap"])
            self._summary_vals[key] = val_lbl

        # Taxa de comparecimento — destaque especial
        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], SPACING["label_gap"]))

        comp_row = ctk.CTkFrame(
            card,
            fg_color=THEME["kpi_green_soft"],
            corner_radius=RADIUS["button"],
        )
        comp_row.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["item_gap"]))

        ctk.CTkLabel(
            comp_row, text="Taxa de Comparecimento",
            font=themed_font("body"),
            text_color=THEME["kpi_green"], anchor="w",
        ).pack(side="left", padx=12, pady=10)

        comp_val = ctk.CTkLabel(
            comp_row, text="—",
            font=themed_font("body", "bold"),
            text_color=THEME["kpi_green"],
        )
        comp_val.pack(side="right", padx=SPACING["icon_gap"])
        self._summary_vals["comparecimento"] = comp_val

    # ══════════════════════════════════════════
    #  EXPORTAÇÃO
    # ══════════════════════════════════════════
    def _criar_secao_exportacao(self):
        card = _card(self)
        card.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], SPACING["section_gap"]))

        ctk.CTkLabel(
            hdr, text="📥  Exportação de Dados",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["item_gap"]))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["item_gap"]))

        exports = [
            ("📋  Estudantes",    "CSV",  self.servico_relatorio.exportar_estudantes,    THEME["kpi_blue"],   THEME["kpi_blue_soft"]),
            ("📅  Agenda",        "CSV",  self.servico_relatorio.exportar_agendamentos,   THEME["kpi_green"],  THEME["kpi_green_soft"]),
            ("🔍  Triagens",      "CSV",  self.servico_relatorio.exportar_triagens,       THEME["kpi_amber"],  THEME["kpi_amber_soft"]),
            ("📊  Relatório PDF", "PDF",  lambda: None,                                   THEME["kpi_violet"], THEME["kpi_violet_soft"]),
        ]

        for label, fmt, cmd, accent, soft in exports:
            btn_wrap = ctk.CTkFrame(btn_row, fg_color=soft, corner_radius=RADIUS["button"])
            btn_wrap.pack(side="left", padx=(0, SPACING["icon_gap"]))

            inner = ctk.CTkFrame(btn_wrap, fg_color="transparent")
            inner.pack(padx=SPACING["card_pad"], pady=SPACING["icon_gap"])

            ctk.CTkLabel(
                inner, text=label,
                font=themed_font("body", "bold"),
                text_color=accent,
            ).pack(anchor="w")

            ctk.CTkButton(
                inner, text=f"Exportar {fmt}",
                command=cmd,
                height=30, corner_radius=RADIUS["xs"], width=120,
                font=themed_font("body_sm", "bold"),
                fg_color=accent,
                hover_color=THEME["primary_hover"],
                text_color=THEME["text_on_primary"],
            ).pack(anchor="w", pady=(SPACING["label_gap"], 0))

    def criar_secao_exportacao(self):
        self._criar_secao_exportacao()

    # ══════════════════════════════════════════
    #  LISTA DE RELATÓRIOS
    # ══════════════════════════════════════════
    def _criar_lista_relatorios(self):
        card = _card(self)
        card.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(SPACING["section_gap"], SPACING["page_y"]))

        # Cabeçalho com filtro
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))

        ctk.CTkLabel(
            hdr, text="Relatórios Gerados",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        ctk.CTkOptionMenu(
            hdr,
            values=["Todos os tipos", "Geral", "Estudante",
                    "Agendamentos", "Intervenções", "Triagens", "Estatísticas"],
            font=themed_font("body"),
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            width=160,
            height=34,
            corner_radius=RADIUS["input"],
            command=self._filtrar_por_tipo,
        )
        self.filtro_tipo.pack(side="right")

        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))

        # Coluna header
        col_hdr = ctk.CTkFrame(card, fg_color="transparent")
        col_hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))
        col_hdr.grid_columnconfigure(0, weight=3)
        col_hdr.grid_columnconfigure(1, weight=1)
        col_hdr.grid_columnconfigure(2, weight=1)
        col_hdr.grid_columnconfigure(3, weight=1)

        for i, txt in enumerate(["Nome do Relatório", "Tipo", "Data", "Ações"]):
            ctk.CTkLabel(
                col_hdr, text=txt,
                font=themed_font("body_sm", "bold"),
                text_color=THEME["text_secondary"], anchor="w",
            ).grid(row=0, column=i, sticky="w", padx=(0 if i else SPACING["icon_gap"], 0))

        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))

        self.reports_container = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.reports_container.pack(fill="both", expand=True, padx=SPACING["icon_gap"], pady=(SPACING["label_gap"], SPACING["icon_gap"]))

    def _filtrar_por_tipo(self, tipo: str):
        # Re-renderiza com filtro (dados em memória)
        if hasattr(self, "_todos_relatorios"):
            if tipo == "Todos os tipos":
                self._popular_lista(self._todos_relatorios)
            else:
                filtrados = [r for r in self._todos_relatorios
                             if r.get("type", "Geral") == tipo]
                self._popular_lista(filtrados)

    def _popular_lista(self, reports: list):
        self._todos_relatorios = reports
        if not hasattr(self, "reports_container"):
            return
        for w in self.reports_container.winfo_children():
            w.destroy()

        if not reports:
            ctk.CTkFrame(
                self.reports_container,
                fg_color=THEME["kpi_blue_soft"],
                corner_radius=RADIUS["lg"], height=100,
            ).pack(fill="x", pady=8)
            EmptyState(
                self.reports_container,
                icon="📄",
                title="Nenhum relatório encontrado",
                subtitle="",
            ).pack(pady=SPACING["section_gap"])
            return

        for r in reports:
            self._criar_row_relatorio(r)

    def _criar_row_relatorio(self, report: dict):
        row = ctk.CTkFrame(
            self.reports_container,
            fg_color=THEME["row_bg"],
            corner_radius=RADIUS["button"],
        )
        row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=1)

        # Hover
        row.bind("<Enter>",  lambda e, r=row: r.configure(fg_color=THEME["row_hover"]))
        row.bind("<Leave>",  lambda e, r=row: r.configure(fg_color=THEME["row_bg"]))

        # Ícone + Nome
        name_cell = ctk.CTkFrame(row, fg_color="transparent")
        name_cell.grid(row=0, column=0, sticky="w", padx=SPACING["icon_gap"], pady=SPACING["item_gap"])

        icon_bg = ctk.CTkFrame(name_cell, width=32, height=32, corner_radius=RADIUS["xs"],
                               fg_color=THEME["kpi_blue_soft"])
        icon_bg.pack(side="left", padx=(0, SPACING["icon_gap"]))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="📄",
                     font=themed_font("h4")).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            name_cell,
            text=report.get("name", "Relatório"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        # Tipo – chip colorido
        tipo = report.get("type", "Geral")
        chip = _chip(row, tipo, tipo)
        chip.grid(row=0, column=1, sticky="w", padx=SPACING["icon_gap"], pady=SPACING["item_gap"])

        # Data
        data_str = (report.get("generated_at") or report.get("created_at") or "Hoje")
        if len(data_str) > 10:
            data_str = data_str[:10]

        ctk.CTkLabel(
            row, text=data_str,
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=2, sticky="w", padx=SPACING["icon_gap"])

        # Ações
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=3, sticky="e", padx=SPACING["icon_gap"], pady=SPACING["icon_gap"])

        for icon, tip, cmd in [
            ("👁", "Visualizar", lambda: None),
            ("📥", "Baixar",     lambda: None),
            ("🗑", "Excluir",    lambda: None),
        ]:
            GhostButton(
                actions, text=icon,
                width=30, height=30, corner_radius=RADIUS["xs"],
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=cmd,
            ).pack(side="left", padx=SPACING["label_gap"] // 2)

    # Alias legado
    def create_report_row(self, report):
        self._criar_row_relatorio(report)

    def criar_lista_relatorios(self):
        self._criar_lista_relatorios()

    def criar_cards(self):
        self._criar_kpis()

    def criar_secao_inferior(self):
        self._criar_grid_central()

    def item_resumo(self, parent, texto, valor, cor_valor=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["card_pad"], pady=SPACING["label_gap"])
        ctk.CTkLabel(row, text=texto,
                     font=themed_font("body"),
                     text_color=THEME["text_secondary"]).pack(side="left")
        ctk.CTkLabel(row, text=valor,
                     font=themed_font("body", "bold"),
                     text_color=cor_valor or THEME["text"]).pack(side="right")
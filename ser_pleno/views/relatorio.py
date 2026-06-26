import customtkinter as ctk
import threading
from services.relatorios import ServicoRelatorio


# ══════════════════════════════════════════════════════════════════════════════
#  Design tokens – família índigo (consistente com todo o sistema)
# ══════════════════════════════════════════════════════════════════════════════
R = {
    # Fundo
    "page_bg":          "#F8F7FF",
    "card_bg":          "#FFFFFF",
    "card_border":      "#E5E7EB",
    "card_radius":      16,

    # Acento principal
    "accent":           "#4F46E5",
    "accent_hover":     "#4338CA",
    "accent_soft":      "#EEF2FF",

    # KPI cores
    "kpi_blue":         "#4F46E5",
    "kpi_blue_soft":    "#EEF2FF",
    "kpi_green":        "#059669",
    "kpi_green_soft":   "#D1FAE5",
    "kpi_violet":       "#7C3AED",
    "kpi_violet_soft":  "#EDE9FE",
    "kpi_amber":        "#D97706",
    "kpi_amber_soft":   "#FEF3C7",

    # Texto
    "text":             "#111827",
    "text_muted":       "#6B7280",
    "text_light":       "#9CA3AF",

    # Divider
    "divider":          "#F3F4F6",

    # Gráfico (canvas)
    "chart_bg":         "#FFFFFF",
    "chart_grid":       "#F3F4F6",
    "chart_bar_1":      "#4F46E5",   # Agendamentos
    "chart_bar_2":      "#059669",   # Intervenções
    "chart_bar_3":      "#D97706",   # Triagens
    "chart_bar_soft_1": "#C7D2FE",
    "chart_bar_soft_2": "#6EE7B7",
    "chart_bar_soft_3": "#FDE68A",

    # Exportação
    "export_item_bg":   "#F5F3FF",
    "export_item_hover":"#EEF2FF",

    # Lista de relatórios
    "row_bg":           "#FAFAFA",
    "row_hover":        "#F5F3FF",
    "row_border":       "#F3F4F6",

    # Chips de tipo
    "chip_geral_bg":    "#EEF2FF",
    "chip_geral_text":  "#4F46E5",
    "chip_estudante_bg":"#D1FAE5",
    "chip_estudante_text":"#065F46",
    "chip_agenda_bg":   "#FEF3C7",
    "chip_agenda_text": "#92400E",
    "chip_default_bg":  "#F3F4F6",
    "chip_default_text":"#374151",
}

# Mapeamento chip por tipo
_CHIP = {
    "Geral":         (R["chip_geral_bg"],     R["chip_geral_text"]),
    "Estudante":     (R["chip_estudante_bg"],  R["chip_estudante_text"]),
    "Agendamentos":  (R["chip_agenda_bg"],     R["chip_agenda_text"]),
    "Intervenções":  (R["kpi_violet_soft"],    R["kpi_violet"]),
    "Triagens":      (R["kpi_amber_soft"],     R["kpi_amber"]),
    "Estatísticas":  (R["export_item_bg"],     R["accent"]),
}

# KPIs (título, ícone, acento, soft, chave nos dados)
_KPIS = [
    ("Estudantes",    "🎓", R["kpi_blue"],   R["kpi_blue_soft"],   "students_total"),
    ("Agendamentos",  "📅", R["kpi_green"],  R["kpi_green_soft"],  "appointments_total"),
    ("Intervenções",  "🤝", R["kpi_violet"], R["kpi_violet_soft"], "interventions_total"),
    ("Triagens",      "🔍", R["kpi_amber"],  R["kpi_amber_soft"],  "screenings_total"),
]


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de layout
# ──────────────────────────────────────────────────────────────────────────────
def _card(parent, **kwargs) -> ctk.CTkFrame:
    return ctk.CTkFrame(
        parent,
        fg_color=R["card_bg"],
        corner_radius=R["card_radius"],
        border_width=1,
        border_color=R["card_border"],
        **kwargs,
    )


def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=R["divider"]).pack(fill="x")


def _section_title(parent, text: str, pady=(16, 12)):
    ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont("Segoe UI", 13, "bold"),
        text_color=R["text"], anchor="w",
    ).pack(fill="x", padx=20, pady=pady)


def _chip(parent, text: str, tipo: str = "") -> ctk.CTkFrame:
    bg, fg = _CHIP.get(tipo, (R["chip_default_bg"], R["chip_default_text"]))
    f = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8)
    ctk.CTkLabel(
        f, text=text,
        font=ctk.CTkFont("Segoe UI", 11, "bold"),
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
            fg_color=R["card_bg"],
            corner_radius=R["card_radius"],
            border_width=1,
            border_color=R["card_border"],
        )
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        icon_bg = ctk.CTkFrame(top, width=44, height=44, corner_radius=12, fg_color=soft)
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon,
                     font=ctk.CTkFont("Segoe UI", 20)).place(relx=0.5, rely=0.5, anchor="center")

        self._val_lbl = ctk.CTkLabel(
            top, text="—",
            font=ctk.CTkFont("Segoe UI", 30, "bold"),
            text_color=R["text"],
        )
        self._val_lbl.pack(side="right", anchor="e")

        ctk.CTkLabel(
            inner, text=title,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=R["text"], anchor="w",
        ).pack(fill="x", pady=(10, 2))

        if sub:
            ctk.CTkLabel(
                inner, text=sub,
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=R["text_muted"], anchor="w",
            ).pack(fill="x")

        ctk.CTkFrame(self, height=3, corner_radius=0, fg_color=accent).pack(
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
            fg_color=R["page_bg"],
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
            self.after(0, lambda: self._atualizar_view(stats, reports))
        threading.Thread(target=fetch, daemon=True).start()

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
        bar.pack(fill="x", padx=28, pady=(20, 4))

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(
            left, text="Relatórios",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=R["text"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left, text="Visão gerencial e indicadores do sistema",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=R["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            bar,
            text="＋  Gerar Relatório",
            command=lambda: None,
            height=40, corner_radius=12,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=R["accent"],
            hover_color=R["accent_hover"],
            text_color="white",
            width=180,
        ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color=R["card_border"]).pack(
            fill="x", padx=28, pady=(12, 0)
        )

    # ══════════════════════════════════════════
    #  KPIs
    # ══════════════════════════════════════════
    def _criar_kpis(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(18, 0))

        for i, (title, icon, accent, soft, _) in enumerate(_KPIS):
            row.grid_columnconfigure(i, weight=1)
            card = _KPICard(row, title, icon, accent, soft,
                            sub="Total cadastrado" if i == 0 else "Total registrado")
            card.grid(row=0, column=i, sticky="ew", padx=5)
            self._kpi_cards[title] = card

    # ══════════════════════════════════════════
    #  GRID CENTRAL: gráfico + resumo
    # ══════════════════════════════════════════
    def _criar_grid_central(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=28, pady=(16, 0))
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
        hdr.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(
            hdr, text="Atividades nos Últimos 30 Dias",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=R["text"],
        ).pack(side="left")

        # Legenda
        leg = ctk.CTkFrame(hdr, fg_color="transparent")
        leg.pack(side="right")
        for label, color in [
            ("Agendamentos", R["chart_bar_1"]),
            ("Intervenções", R["chart_bar_2"]),
            ("Triagens",     R["chart_bar_3"]),
        ]:
            dot_row = ctk.CTkFrame(leg, fg_color="transparent")
            dot_row.pack(side="left", padx=6)
            ctk.CTkFrame(dot_row, width=10, height=10, corner_radius=5,
                         fg_color=color).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(dot_row, text=label,
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=R["text_muted"]).pack(side="left")

        ctk.CTkFrame(card, height=1, fg_color=R["divider"]).pack(
            fill="x", padx=20, pady=(10, 0)
        )

        self.canvas_chart = ctk.CTkCanvas(
            card, bg=R["chart_bg"], height=220, highlightthickness=0
        )
        self.canvas_chart.pack(fill="both", expand=True, padx=16, pady=(8, 16))
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
            ("appointments",  R["chart_bar_1"], R["chart_bar_soft_1"]),
            ("interventions", R["chart_bar_2"], R["chart_bar_soft_2"]),
            ("screenings",    R["chart_bar_3"], R["chart_bar_soft_3"]),
        ]

        all_vals = [s[k] for s in samples for k, *_ in series if k in s]
        max_v    = max(all_vals) if all_vals else 1
        bar_w    = max(4, int(bw / (len(series) + 1.5)))

        # Linhas de grade
        for i in range(5):
            gy = my + i * (ch - 2 * my) / 4
            self.canvas_chart.create_line(
                mx, gy, cw - mx, gy,
                fill=R["chart_grid"], dash=(3, 4),
            )
            val_lbl = int(max_v * (1 - i / 4))
            self.canvas_chart.create_text(
                mx - 4, gy, text=str(val_lbl),
                font=("Segoe UI", 8), fill=R["text_light"], anchor="e",
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
                font=("Segoe UI", 8), fill=R["text_muted"],
            )

    # ── Resumo lateral ───────────────────────────────────────────────────────
    def _criar_card_resumo(self, parent):
        card = _card(parent)
        card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        _section_title(card, "Resumo do Período")
        ctk.CTkFrame(card, height=1, fg_color=R["divider"]).pack(
            fill="x", padx=20, pady=(0, 8)
        )

        rows_cfg = [
            ("total_estudantes",  "Total de Estudantes",   R["text"],           None),
            ("consultas_30d",     "Consultas (30d)",        R["text"],           None),
            ("intervencoes_30d",  "Intervenções (30d)",     R["text"],           None),
            ("triagens_30d",      "Triagens (30d)",         R["text"],           None),
        ]

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=(0, 4))

        for key, label, _, _ in rows_cfg:
            row = ctk.CTkFrame(body, fg_color=R["row_bg"], corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=label,
                font=ctk.CTkFont("Segoe UI", 12),
                text_color=R["text_muted"], anchor="w",
            ).pack(side="left", padx=12, pady=8)
            val_lbl = ctk.CTkLabel(
                row, text="—",
                font=ctk.CTkFont("Segoe UI", 13, "bold"),
                text_color=R["text"],
            )
            val_lbl.pack(side="right", padx=12)
            self._summary_vals[key] = val_lbl

        # Taxa de comparecimento — destaque especial
        ctk.CTkFrame(card, height=1, fg_color=R["divider"]).pack(
            fill="x", padx=20, pady=(6, 6)
        )

        comp_row = ctk.CTkFrame(
            card,
            fg_color=R["kpi_green_soft"],
            corner_radius=10,
        )
        comp_row.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            comp_row, text="Taxa de Comparecimento",
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=R["kpi_green"], anchor="w",
        ).pack(side="left", padx=12, pady=10)

        comp_val = ctk.CTkLabel(
            comp_row, text="—",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=R["kpi_green"],
        )
        comp_val.pack(side="right", padx=12)
        self._summary_vals["comparecimento"] = comp_val

    # ══════════════════════════════════════════
    #  EXPORTAÇÃO
    # ══════════════════════════════════════════
    def _criar_secao_exportacao(self):
        card = _card(self)
        card.pack(fill="x", padx=28, pady=(16, 0))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 12))

        ctk.CTkLabel(
            hdr, text="📥  Exportação de Dados",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=R["text"],
        ).pack(side="left")

        ctk.CTkFrame(card, height=1, fg_color=R["divider"]).pack(
            fill="x", padx=20, pady=(0, 12)
        )

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        exports = [
            ("📋  Estudantes",    "CSV",  self.servico_relatorio.exportar_estudantes,    R["kpi_blue"],   R["kpi_blue_soft"]),
            ("📅  Agenda",        "CSV",  self.servico_relatorio.exportar_agendamentos,   R["kpi_green"],  R["kpi_green_soft"]),
            ("🔍  Triagens",      "CSV",  self.servico_relatorio.exportar_triagens,       R["kpi_amber"],  R["kpi_amber_soft"]),
            ("📊  Relatório PDF", "PDF",  lambda: None,                                   R["kpi_violet"], R["kpi_violet_soft"]),
        ]

        for label, fmt, cmd, accent, soft in exports:
            btn_wrap = ctk.CTkFrame(btn_row, fg_color=soft, corner_radius=12)
            btn_wrap.pack(side="left", padx=(0, 10))

            inner = ctk.CTkFrame(btn_wrap, fg_color="transparent")
            inner.pack(padx=16, pady=10)

            ctk.CTkLabel(
                inner, text=label,
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                text_color=accent,
            ).pack(anchor="w")

            ctk.CTkButton(
                inner, text=f"Exportar {fmt}",
                command=cmd,
                height=30, corner_radius=8, width=120,
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                fg_color=accent,
                hover_color=R["accent_hover"],
                text_color="white",
            ).pack(anchor="w", pady=(6, 0))

    def criar_secao_exportacao(self):
        self._criar_secao_exportacao()

    # ══════════════════════════════════════════
    #  LISTA DE RELATÓRIOS
    # ══════════════════════════════════════════
    def _criar_lista_relatorios(self):
        card = _card(self)
        card.pack(fill="both", expand=True, padx=28, pady=(16, 28))

        # Cabeçalho com filtro
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(
            hdr, text="Relatórios Gerados",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=R["text"],
        ).pack(side="left")

        self.filtro_tipo = ctk.CTkOptionMenu(
            hdr,
            values=["Todos os tipos", "Geral", "Estudante",
                    "Agendamentos", "Intervenções", "Triagens", "Estatísticas"],
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=R["accent_soft"],
            button_color=R["accent"],
            button_hover_color=R["accent_hover"],
            text_color=R["accent"],
            dropdown_fg_color="#FFFFFF",
            dropdown_text_color=R["text"],
            width=160,
            height=34,
            corner_radius=8,
            command=self._filtrar_por_tipo,
        )
        self.filtro_tipo.pack(side="right")

        ctk.CTkFrame(card, height=1, fg_color=R["divider"]).pack(
            fill="x", padx=20, pady=(12, 0)
        )

        # Coluna header
        col_hdr = ctk.CTkFrame(card, fg_color="transparent")
        col_hdr.pack(fill="x", padx=20, pady=(8, 4))
        col_hdr.grid_columnconfigure(0, weight=3)
        col_hdr.grid_columnconfigure(1, weight=1)
        col_hdr.grid_columnconfigure(2, weight=1)
        col_hdr.grid_columnconfigure(3, weight=1)

        for i, txt in enumerate(["Nome do Relatório", "Tipo", "Data", "Ações"]):
            ctk.CTkLabel(
                col_hdr, text=txt,
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                text_color=R["text_light"], anchor="w",
            ).grid(row=0, column=i, sticky="w", padx=(0 if i else 4, 0))

        ctk.CTkFrame(card, height=1, fg_color=R["divider"]).pack(
            fill="x", padx=20, pady=(0, 4)
        )

        self.reports_container = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color="#D1D5DB",
            scrollbar_button_hover_color="#9CA3AF",
        )
        self.reports_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

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
                fg_color=R["kpi_blue_soft"],
                corner_radius=12, height=100,
            ).pack(fill="x", pady=8)
            ctk.CTkLabel(
                self.reports_container,
                text="📄  Nenhum relatório encontrado",
                font=ctk.CTkFont("Segoe UI", 13),
                text_color=R["text_muted"],
            ).pack(pady=20)
            return

        for r in reports:
            self._criar_row_relatorio(r)

    def _criar_row_relatorio(self, report: dict):
        row = ctk.CTkFrame(
            self.reports_container,
            fg_color=R["row_bg"],
            corner_radius=10,
        )
        row.pack(fill="x", pady=3)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=1)

        # Hover
        row.bind("<Enter>",  lambda e, r=row: r.configure(fg_color=R["row_hover"]))
        row.bind("<Leave>",  lambda e, r=row: r.configure(fg_color=R["row_bg"]))

        # Ícone + Nome
        name_cell = ctk.CTkFrame(row, fg_color="transparent")
        name_cell.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        icon_bg = ctk.CTkFrame(name_cell, width=32, height=32, corner_radius=8,
                               fg_color=R["kpi_blue_soft"])
        icon_bg.pack(side="left", padx=(0, 10))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="📄",
                     font=ctk.CTkFont("Segoe UI", 14)).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            name_cell,
            text=report.get("name", "Relatório"),
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=R["text"],
        ).pack(side="left")

        # Tipo – chip colorido
        tipo = report.get("type", "Geral")
        chip = _chip(row, tipo, tipo)
        chip.grid(row=0, column=1, sticky="w", padx=8, pady=10)

        # Data
        data_str = (report.get("generated_at") or report.get("created_at") or "Hoje")
        if len(data_str) > 10:
            data_str = data_str[:10]

        ctk.CTkLabel(
            row, text=data_str,
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=R["text_muted"],
        ).grid(row=0, column=2, sticky="w", padx=8)

        # Ações
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=3, sticky="e", padx=12, pady=8)

        for icon, tip, cmd in [
            ("👁", "Visualizar", lambda: None),
            ("📥", "Baixar",     lambda: None),
            ("🗑", "Excluir",    lambda: None),
        ]:
            ctk.CTkButton(
                actions, text=icon,
                width=30, height=30, corner_radius=8,
                fg_color="transparent",
                hover_color=R["accent_soft"],
                text_color=R["text_muted"],
                font=ctk.CTkFont("Segoe UI", 13),
                command=cmd,
            ).pack(side="left", padx=2)

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
        row.pack(fill="x", padx=18, pady=4)
        ctk.CTkLabel(row, text=texto,
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=R["text_muted"]).pack(side="left")
        ctk.CTkLabel(row, text=valor,
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=cor_valor or R["text"]).pack(side="right")
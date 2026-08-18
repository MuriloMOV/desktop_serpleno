from __future__ import annotations

import logging
import os
import shutil
import time
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk

from ser_pleno.features.relatorio.service import ServicoRelatorio
from ser_pleno.features.report_template.service import ServicoReportTemplate
from ser_pleno.ui.components.ui_components import (
    BaseModal,
    Card,
    Chip,
    DangerButton,
    Divider,
    EmptyState,
    GhostButton,
    PrimaryButton,
    SummaryCard,
    Toast,
    _CLICKABLE_EXCLUDE,
)
from ser_pleno.ui.views.base import BaseViewFrame
from ser_pleno.ui.components.icons import ICONS, IconLabel
from ser_pleno.ui.theme import FONT_FAMILY, RADIUS, SPACING, THEME, font, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger(__name__)

_CHIP = {
    "Geral": (THEME["chip_geral_bg"], THEME["chip_geral_text"]),
    "Estudante": (THEME["chip_estudante_bg"], THEME["chip_estudante_text"]),
    "Agendamentos": (THEME["chip_agenda_bg"], THEME["chip_agenda_text"]),
    "Intervenções": (THEME["kpi_violet_soft"], THEME["kpi_violet"]),
    "Triagens": (THEME["kpi_amber_soft"], THEME["kpi_amber"]),
    "Estatísticas": (THEME["export_item_bg"], THEME["accent"]),
}

_KPIS = [
    ("Estudantes", ICONS["group"], THEME["kpi_blue"], THEME["kpi_blue_soft"], "students_total"),
    (
        "Agendamentos",
        ICONS["calendar"],
        THEME["kpi_green"],
        THEME["kpi_green_soft"],
        "appointments_total",
    ),
    (
        "Intervenções",
        ICONS["user"],
        THEME["kpi_violet"],
        THEME["kpi_violet_soft"],
        "interventions_total",
    ),
    ("Triagens", ICONS["search"], THEME["kpi_amber"], THEME["kpi_amber_soft"], "screenings_total"),
]

_QUICK_CARDS = [
    (
        ICONS["document"],
        "Relatório Geral",
        "geral",
        "Visão completa do sistema",
        THEME["kpi_blue"],
        THEME["kpi_blue_soft"],
    ),
    (
        ICONS["calendar"],
        "Agendamentos",
        "agendamentos",
        "Análise de consultas",
        THEME["kpi_green"],
        THEME["kpi_green_soft"],
    ),
    (
        ICONS["user"],
        "Intervenções",
        "intervencoes",
        "Acompanhamentos realizados",
        THEME["kpi_violet"],
        THEME["kpi_violet_soft"],
    ),
    (
        ICONS["search"],
        "Triagens",
        "triagens",
        "Análise de triagens",
        THEME["kpi_amber"],
        THEME["kpi_amber_soft"],
    ),
]


def bind_clickable(widget, on_click):
    widget.configure(cursor="hand2")
    _bind_clickable_recursive(widget, on_click)


def _bind_clickable_recursive(widget, on_click):
    if isinstance(widget, _CLICKABLE_EXCLUDE):
        return
    widget.bind("<Button-1>", lambda *args: on_click())
    widget.bind("<Return>", lambda *args: on_click())
    widget.bind("<space>", lambda *args: on_click())
    for child in widget.winfo_children():
        _bind_clickable_recursive(child, on_click)


class RelatorioFrame(BaseViewFrame):
    def __init__(self, parent, controller):
        self._t0 = time.perf_counter()
        super().__init__(
            parent,
            controller,
            fg_color=THEME["page_bg"],
            scrollbar_button_color="#C7D2FE",
            scrollbar_button_hover_color="#A5B4FC",
        )
        auth_service = getattr(controller, "auth_service", None)
        self.servico_relatorio = ServicoRelatorio(auth_service=auth_service)
        self.servico_report_template = ServicoReportTemplate(auth_service=auth_service)

        self._kpi_cards: dict[str, SummaryCard] = {}
        self._summary_vals: dict[str, ctk.CTkLabel] = {}
        self._chart_data = []
        self._todos_relatorios: list[dict] = []
        self._selecionados: set[int] = set()
        self._heavy_built = False
        self.filtro_tipo = None
        self.filtro_busca = None
        self.filtro_data_inicio = None
        self.filtro_data_fim = None
        self._export_data_inicio = None
        self._export_data_fim = None
        self._export_tipo = None
        self._export_formato = None
        self.reports_container = None
        self._bulk_bar = None
        self._bulk_count_lbl = None
        self._select_all_var = None

        self._criar_cards_relatorios_rapidos()
        self._criar_kpis()
        self._criar_grid_central()

        self.after_idle(self._build_heavy_sections)
        self.after_idle(self._carregar_dados)
        log_view_init_ms("relatorio", self._t0, widget_ref=self)

    def _build_heavy_sections(self):
        if self._heavy_built:
            return
        self._heavy_built = True
        self._criar_secao_exportacao()
        self._criar_lista_relatorios()
        self._criar_secao_templates()

    def _extract_items(self, res_data):
        if isinstance(res_data, list):
            return res_data
        if isinstance(res_data, dict):
            return res_data.get("reports") or res_data.get("results") or []
        return []

    def _carregar_dados(self):
        def fetch():
            stats = self.servico_relatorio.obter_estatisticas()
            reports = self.servico_relatorio.listar_relatorios()
            return stats, reports

        AsyncRunner.run(
            task=fetch,
            on_success=lambda res: self._atualizar_view(*res),
            on_error=lambda exc: self._show_error(f"Não foi possível carregar relatórios.\n{exc}"),
            widget_ref=self,
        )

    def _atualizar_view(self, stats_res, reports_res):
        if stats_res.get("success"):
            summary = stats_res.get("data", {}).get("summary", {})
            title_map = {
                "students_total": "Estudantes",
                "appointments_total": "Agendamentos",
                "interventions_total": "Intervenções",
                "screenings_total": "Triagens",
            }
            for _, _, _, _, key in _KPIS:
                t = title_map.get(key, key)
                if t in self._kpi_cards:
                    self._kpi_cards[t].set_value(str(summary.get(key, 0)))

            mapping_resumo = {
                "total_estudantes": summary.get("students_total", "—"),
                "consultas_30d": summary.get(
                    "appointments_30d", summary.get("appointments_total", "—")
                ),
                "intervencoes_30d": summary.get(
                    "interventions_30d", summary.get("interventions_total", "—")
                ),
                "triagens_30d": summary.get("screenings_30d", summary.get("screenings_total", "—")),
                "comparecimento": summary.get("attendance_rate", "—"),
            }
            for key, val in mapping_resumo.items():
                if key in self._summary_vals:
                    self._summary_vals[key].configure(text=str(val))

            self._chart_data = stats_res.get("data", {}).get("monthly", [])
            self._draw_chart()

        if reports_res.get("success"):
            items = self._extract_items(reports_res.get("data", {}))
            self._popular_lista(items)

    def load_data(self):
        self._carregar_dados()

    def update_view(self, stats_res, reports_res):
        self._atualizar_view(stats_res, reports_res)

    def update_card(self, key, value):
        if key in self._kpi_cards:
            self._kpi_cards[key].set_value(value)

    def populate_reports_list(self, reports):
        self._popular_lista(reports)

    def _criar_cards_relatorios_rapidos(self):
        card = Card(self, padding=(SPACING["card_pad"], SPACING["label_gap"]))
        card.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

        hdr = ctk.CTkFrame(card.body, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, SPACING["label_gap"]))
        ctk.CTkLabel(
            hdr,
            text="Relatórios Rápidos",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        grid = ctk.CTkFrame(card.body, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)

        for idx, (icon, title, rtype, subtitle, accent, soft) in enumerate(_QUICK_CARDS):
            wrap = ctk.CTkFrame(grid, fg_color=soft, corner_radius=RADIUS["button"])
            wrap.grid(
                row=0, column=idx, sticky="ew", padx=(0 if idx == 0 else SPACING["icon_gap"] // 2)
            )

            inner = ctk.CTkFrame(wrap, fg_color="transparent")
            inner.pack(padx=SPACING["card_pad"], pady=SPACING["icon_gap"])

            ctk.CTkLabel(inner, text=icon, font=themed_font("h3")).pack(anchor="w")
            ctk.CTkLabel(
                inner,
                text=title,
                font=themed_font("body", "bold"),
                text_color=accent,
            ).pack(anchor="w")
            ctk.CTkLabel(
                inner,
                text=subtitle,
                font=themed_font("body_sm"),
                text_color=THEME["text_muted"],
            ).pack(anchor="w")

            bind_clickable(wrap, lambda rtype=rtype: self._abrir_modal_gerar_relatorio(rtype))

    def _criar_kpis(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["item_gap"], 0))

        for i, (title, icon, accent, soft, _) in enumerate(_KPIS):
            row.grid_columnconfigure(i, weight=1)
            card = SummaryCard(
                row,
                title,
                icon,
                accent,
                soft,
                sub="Total cadastrado" if i == 0 else "Total registrado",
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["icon_gap"] // 2)
            self._kpi_cards[title] = card

    def _criar_grid_central(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["item_gap"], 0))
        grid.grid_columnconfigure(0, weight=3)
        grid.grid_columnconfigure(1, weight=2)

        self._criar_card_grafico(grid)
        self._criar_card_resumo(grid)

    def _criar_card_grafico(self, parent):
        card = Card(parent, padding=(SPACING["card_pad"], SPACING["label_gap"]), auto_body=False)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["icon_gap"] // 2))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=SPACING["card_pad"], pady=(0, SPACING["label_gap"])
        )

        hdr = ctk.CTkFrame(body, fg_color="transparent")
        hdr.pack(fill="x")

        ctk.CTkLabel(
            hdr,
            text="Atividades nos Últimos 30 Dias",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        self._comparison_btn = ctk.CTkButton(
            hdr,
            text=f"{ICONS['layout']} Comparar períodos",
            command=self._toggle_comparacao,
            width=160,
            height=32,
            fg_color="transparent",
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text_secondary"],
            hover_color=THEME["bg_alt"],
            font=themed_font("body_sm", "bold"),
            corner_radius=RADIUS["button"],
        )
        self._comparison_btn.pack(side="right")

        leg = ctk.CTkFrame(hdr, fg_color="transparent")
        leg.pack(side="right", padx=(0, SPACING["icon_gap"]))
        for label, color in [
            ("Agendamentos", THEME["chart_bar_1"]),
            ("Intervenções", THEME["chart_bar_2"]),
            ("Triagens", THEME["chart_bar_3"]),
        ]:
            dot_row = ctk.CTkFrame(leg, fg_color="transparent")
            dot_row.pack(side="left", padx=SPACING["icon_gap"] // 2)
            ctk.CTkFrame(
                dot_row, width=10, height=10, corner_radius=RADIUS["sm"], fg_color=color
            ).pack(side="left", padx=(0, SPACING["label_gap"] // 2))
            ctk.CTkLabel(
                dot_row, text=label, font=themed_font("body_sm"), text_color=THEME["text_muted"]
            ).pack(side="left")

        Divider(body).pack(fill="x", pady=(SPACING["label_gap"], 0))

        self._comparison_panel = ctk.CTkFrame(
            body, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"]
        )
        self._comparison_panel.pack(fill="x", pady=(0, SPACING["label_gap"]))
        self._comparison_panel.pack_forget()

        comp_inner = ctk.CTkFrame(self._comparison_panel, fg_color="transparent")
        comp_inner.pack(fill="x", padx=SPACING["card_pad"], pady=SPACING["label_gap"])

        for label, key in [("Período A", "a"), ("Período B", "b")]:
            col = ctk.CTkFrame(comp_inner, fg_color="transparent")
            col.pack(
                side="left",
                expand=True,
                fill="x",
                padx=(0 if key == "a" else SPACING["icon_gap"], 0),
            )
            ctk.CTkLabel(
                col,
                text=label,
                font=themed_font("body_sm", "bold"),
                text_color=THEME["text_secondary"],
            ).pack(anchor="w")
            row = ctk.CTkFrame(col, fg_color="transparent")
            row.pack(fill="x", pady=(SPACING["xs"], 0))

            start_entry = ctk.CTkEntry(
                row, width=120, height=32, placeholder_text="Início", font=themed_font("body_sm")
            )
            start_entry.pack(side="left", padx=(0, SPACING["xs"]))

            end_entry = ctk.CTkEntry(
                row, width=120, height=32, placeholder_text="Fim", font=themed_font("body_sm")
            )
            end_entry.pack(side="left")

            setattr(self, f"_comp_{key}_start", start_entry)
            setattr(self, f"_comp_{key}_end", end_entry)

        comp_btns = ctk.CTkFrame(self._comparison_panel, fg_color="transparent")
        comp_btns.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["label_gap"]))
        PrimaryButton(
            comp_btns,
            text="Aplicar",
            command=self._aplicar_comparacao,
            width=100,
            height=32,
            size="sm",
        ).pack(side="right", padx=(SPACING["xs"], 0))
        GhostButton(
            comp_btns, text="Limpar", command=self._limpar_comparacao, width=80, height=32
        ).pack(side="right")

        chart_wrap = ctk.CTkFrame(body, fg_color="transparent")
        chart_wrap.pack(fill="both", expand=True, pady=(SPACING["label_gap"], 0))
        chart_wrap.grid_rowconfigure(0, weight=1)
        chart_wrap.grid_columnconfigure(0, weight=1)

        self.canvas_chart = ctk.CTkCanvas(
            chart_wrap, bg=THEME["surface"], height=220, highlightthickness=0
        )
        self.canvas_chart.grid(row=0, column=0, sticky="nsew")
        self.canvas_chart.bind("<Configure>", lambda e: self._draw_chart())

        self._chart_empty = EmptyState(
            chart_wrap,
            icon=ICONS["chart"],
            title="Sem dados para o gráfico",
            subtitle="Os registros aparecerão aqui quando houver movimentação",
        )
        self._chart_empty.grid(
            row=0, column=0, sticky="nsew", padx=SPACING["icon_gap"], pady=SPACING["icon_gap"]
        )
        self._chart_empty.lower()

    def _toggle_comparacao(self):
        if self._comparison_panel.winfo_ismapped():
            self._comparison_panel.pack_forget()
        else:
            self._comparison_panel.pack(fill="x", pady=(0, SPACING["label_gap"]))

    def _aplicar_comparacao(self):
        a_start = getattr(self, "_comp_a_start", None)
        a_end = getattr(self, "_comp_a_end", None)
        b_start = getattr(self, "_comp_b_start", None)
        b_end = getattr(self, "_comp_b_end", None)

        if not (
            a_start
            and a_end
            and b_start
            and b_end
            and a_start.get()
            and a_end.get()
            and b_start.get()
            and b_end.get()
        ):
            self._show_error("Preencha todos os campos de período.", title="Aviso")
            return
        try:
            periodo_inicio = (a_start.get(), a_end.get())
            periodo_fim = (b_start.get(), b_end.get())
            res = self.servico_relatorio.obter_comparacao_estatisticas(periodo_inicio, periodo_fim)
            if res.get("success"):
                data = res.get("data", {})
                period_a = data.get("periodo_inicio", {}).get("stats", {}).get("summary", {})
                period_b = data.get("periodo_fim", {}).get("stats", {}).get("summary", {})
                variations = data.get("variations", {})
                lines = [
                    f"Período A: {periodo_inicio[0]} a {periodo_inicio[1]}",
                    f"  Consultas: {period_a.get('appointments_total', 0)}",
                    f"  Intervenções: {period_a.get('interventions_total', 0)}",
                    f"  Triagens: {period_a.get('screenings_total', 0)}",
                    f"  Taxa comparecimento: {period_a.get('attendance_rate', 0)}%",
                    "",
                    f"Período B: {periodo_fim[0]} a {periodo_fim[1]}",
                    f"  Consultas: {period_b.get('appointments_total', 0)}",
                    f"  Intervenções: {period_b.get('interventions_total', 0)}",
                    f"  Triagens: {period_b.get('screenings_total', 0)}",
                    f"  Taxa comparecimento: {period_b.get('attendance_rate', 0)}%",
                    "",
                    "Variações:",
                ]
                for k, v in variations.items():
                    if v is not None:
                        lines.append(f"  {k}: {v:+.1f}%")
                self._show_success("\n".join(lines), duration=5000)
            else:
                self._show_error(res.get("message", "Falha ao obter comparação."))
        except Exception as e:
            self._show_error(f"Falha ao comparar períodos.\n{e}")

    def _limpar_comparacao(self):
        for key in ["a_start", "a_end", "b_start", "b_end"]:
            entry = getattr(self, f"_comp_{key}", None)
            if entry:
                entry.delete(0, "end")

    def _draw_chart(self, data=None):
        if data is not None:
            self._chart_data = data

        self.canvas_chart.delete("all")
        cw = self.canvas_chart.winfo_width()
        ch = self.canvas_chart.winfo_height()
        if cw < 60 or ch < 60:
            return

        samples = self._chart_data or []
        if not samples:
            if hasattr(self, "_chart_empty") and self._chart_empty.winfo_exists():
                self._chart_empty.lift()
            return

        if hasattr(self, "_chart_empty") and self._chart_empty.winfo_exists():
            self._chart_empty.lower()

        mx, my = 40, 20
        bw = (cw - 2 * mx) / max(1, len(samples))
        series = [
            ("appointments", THEME["chart_bar_1"]),
            ("interventions", THEME["chart_bar_2"]),
            ("screenings", THEME["chart_bar_3"]),
        ]

        all_vals = [s[k] for s in samples for k, _ in series if k in s]
        max_v = max(all_vals) if all_vals else 1
        bar_w = max(4, int(bw / (len(series) + 1.5)))

        for i in range(5):
            gy = my + i * (ch - 2 * my) / 4
            self.canvas_chart.create_line(
                mx, gy, cw - mx, gy, fill=THEME["chart_grid"], dash=(3, 4)
            )
            val_lbl = int(max_v * (1 - i / 4))
            self.canvas_chart.create_text(
                mx - 4,
                gy,
                text=str(val_lbl),
                font=(FONT_FAMILY, 8),
                fill=THEME["text_secondary"],
                anchor="e",
            )

        for i, sample in enumerate(samples):
            group_x = mx + i * bw + bw / 2 - (len(series) * bar_w) / 2
            for j, (key, color) in enumerate(series):
                v = sample.get(key, 0)
                h = (v / max_v) * (ch - 2 * my) if max_v else 0
                x0 = group_x + j * (bar_w + 2)
                x1 = x0 + bar_w
                y0 = ch - my - h
                y1 = ch - my

                self.canvas_chart.create_rectangle(
                    x0, y0 + 4, x1, y1, fill=color, outline=""
                )
                self.canvas_chart.create_oval(
                    x0, y0, x1, y0 + 8, fill=color, outline=""
                )

            lx = mx + i * bw + bw / 2
            self.canvas_chart.create_text(
                lx,
                ch - 6,
                text=sample.get("label", ""),
                font=(FONT_FAMILY, 8),
                fill=THEME["text_muted"],
            )

    def _criar_card_resumo(self, parent):
        card = Card(parent, padding=(SPACING["card_pad"], SPACING["label_gap"]), auto_body=False)
        card.grid(row=0, column=1, sticky="nsew", padx=(SPACING["icon_gap"] // 2, 0))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=SPACING["card_pad"], pady=(0, SPACING["label_gap"])
        )

        hdr = ctk.CTkFrame(body, fg_color="transparent")
        hdr.pack(fill="x")

        ctk.CTkLabel(
            hdr,
            text="Resumo do Período",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).pack(fill="x")

        ctk.CTkFrame(body, height=1, fg_color=THEME["divider"]).pack(
            fill="x", pady=(SPACING["label_gap"], 0)
        )

        rows_cfg = [
            ("total_estudantes", "Total de Estudantes"),
            ("consultas_30d", "Consultas (30d)"),
            ("intervencoes_30d", "Intervenções (30d)"),
            ("triagens_30d", "Triagens (30d)"),
        ]

        rows_body = ctk.CTkFrame(body, fg_color="transparent")
        rows_body.pack(fill="x", pady=(0, SPACING["label_gap"]))

        for key, label in rows_cfg:
            row = ctk.CTkFrame(rows_body, fg_color=THEME["row_bg"], corner_radius=RADIUS["md"])
            row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
            ctk.CTkLabel(
                row,
                text=label,
                font=themed_font("body"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).pack(side="left", padx=SPACING["icon_gap"], pady=SPACING["icon_gap"])
            val_lbl = ctk.CTkLabel(
                row,
                text="--",
                font=themed_font("body", "bold"),
                text_color=THEME["text"],
            )
            val_lbl.pack(side="right", padx=SPACING["icon_gap"])
            self._summary_vals[key] = val_lbl

        Divider(body).pack(fill="x", pady=(SPACING["label_gap"], SPACING["label_gap"]))

        comp_row = ctk.CTkFrame(
            body,
            fg_color=THEME["kpi_green_soft"],
            corner_radius=RADIUS["button"],
        )
        comp_row.pack(fill="x", pady=(0, SPACING["item_gap"]))

        ctk.CTkLabel(
            comp_row,
            text="Taxa de Comparecimento",
            font=themed_font("body"),
            text_color=THEME["kpi_green"],
            anchor="w",
        ).pack(side="left", padx=spacing("md"), pady=spacing("md"))

        comp_val = ctk.CTkLabel(
            comp_row,
            text="--",
            font=themed_font("body", "bold"),
            text_color=THEME["kpi_green"],
        )
        comp_val.pack(side="right", padx=SPACING["icon_gap"])
        self._summary_vals["comparecimento"] = comp_val

    def _criar_secao_exportacao(self):
        card = Card(self, padding=(SPACING["card_pad"], SPACING["label_gap"]))
        card.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["item_gap"], 0))

        hdr = ctk.CTkFrame(card.body, fg_color="transparent")
        hdr.pack(fill="x")

        ctk.CTkLabel(
            hdr,
            text=f"{ICONS['export']}  Exportação de Dados",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        Divider(card.body).pack(fill="x", pady=(SPACING["label_gap"], 0))

        filtros_frame = ctk.CTkFrame(card.body, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"])
        filtros_frame.pack(fill="x", pady=(0, SPACING["label_gap"]))

        ctk.CTkLabel(
            filtros_frame, text="De:", font=themed_font("body_sm"), text_color=THEME["text_secondary"]
        ).pack(side="left", padx=(SPACING["card_pad"], SPACING["xs"]))
        self._export_data_inicio = ctk.CTkEntry(
            filtros_frame, width=100, height=32, placeholder_text="YYYY-MM-DD", font=themed_font("body_sm")
        )
        self._export_data_inicio.pack(side="left", padx=(0, SPACING["xs"]))

        ctk.CTkLabel(
            filtros_frame, text="Até:", font=themed_font("body_sm"), text_color=THEME["text_secondary"]
        ).pack(side="left", padx=(SPACING["xs"], SPACING["xs"]))
        self._export_data_fim = ctk.CTkEntry(
            filtros_frame, width=100, height=32, placeholder_text="YYYY-MM-DD", font=themed_font("body_sm")
        )
        self._export_data_fim.pack(side="left", padx=(0, SPACING["icon_gap"]))

        ctk.CTkLabel(
            filtros_frame, text="Tipo:", font=themed_font("body_sm"), text_color=THEME["text_secondary"]
        ).pack(side="left", padx=(0, SPACING["xs"]))
        self._export_tipo = ctk.CTkOptionMenu(
            filtros_frame,
            values=["Todos", "Geral", "Estudante", "Agendamentos", "Intervenções", "Triagens", "Estatísticas"],
            width=130,
            height=32,
            font=themed_font("body_sm"),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
        )
        self._export_tipo.set("Todos")
        self._export_tipo.pack(side="left", padx=(0, SPACING["icon_gap"]))

        ctk.CTkLabel(
            filtros_frame, text="Formato:", font=themed_font("body_sm"), text_color=THEME["text_secondary"]
        ).pack(side="left", padx=(0, SPACING["xs"]))
        self._export_formato = ctk.StringVar(value="csv")
        for fmt, label in [("csv", "CSV"), ("excel", "Excel"), ("json", "JSON")]:
            ctk.CTkRadioButton(
                filtros_frame,
                text=label,
                variable=self._export_formato,
                value=fmt,
                font=themed_font("body_sm"),
                fg_color=THEME["primary"],
            ).pack(side="left", padx=(0, SPACING["icon_gap"]))

        btn_row = ctk.CTkFrame(card.body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, SPACING["item_gap"]))

        exports = [
            (
                f"{ICONS['chart']}  Estudantes",
                self.servico_relatorio.exportar_estudantes,
                THEME["kpi_blue"],
                THEME["kpi_blue_soft"],
            ),
            (
                f"{ICONS['calendar']}  Agenda",
                self.servico_relatorio.exportar_agendamentos,
                THEME["kpi_green"],
                THEME["kpi_green_soft"],
            ),
            (
                f"{ICONS['search']}  Triagens",
                self.servico_relatorio.exportar_triagens,
                THEME["kpi_amber"],
                THEME["kpi_amber_soft"],
            ),
            (
                f"{ICONS['user']}  Intervenções",
                self.servico_relatorio.exportar_intervencoes,
                THEME["kpi_violet"],
                THEME["kpi_violet_soft"],
            ),
        ]

        for label, cmd, accent, soft in exports:
            btn_wrap = ctk.CTkFrame(btn_row, fg_color=soft, corner_radius=RADIUS["button"])
            btn_wrap.pack(side="left", padx=(0, SPACING["icon_gap"]))

            inner = ctk.CTkFrame(btn_wrap, fg_color="transparent")
            inner.pack(padx=SPACING["card_pad"], pady=SPACING["icon_gap"])

            ctk.CTkLabel(
                inner,
                text=label,
                font=themed_font("body", "bold"),
                text_color=accent,
            ).pack(anchor="w")

            ctk.CTkButton(
                inner,
                text="Exportar",
                command=self._criar_handler_exportacao(cmd),
                height=30,
                corner_radius=RADIUS["xs"],
                width=120,
                font=themed_font("body_sm", "bold"),
                fg_color=accent,
                hover_color=THEME["primary_hover"],
                text_color=THEME["text_on_primary"],
            ).pack(anchor="w", pady=(SPACING["label_gap"], 0))

    def _criar_handler_exportacao(self, metodo):
        def handler():
            self._executar_exportacao(metodo)
        return handler

    def _obter_filtros_exportacao(self):
        filtros = {}
        if self._export_data_inicio is not None:
            val = self._export_data_inicio.get().strip()
            if val:
                filtros["date_from"] = val
        if self._export_data_fim is not None:
            val = self._export_data_fim.get().strip()
            if val:
                filtros["date_to"] = val
        if self._export_tipo is not None:
            tipo = self._export_tipo.get()
            if tipo and tipo != "Todos":
                filtros["tipo"] = tipo
        return filtros

    def _executar_exportacao(self, metodo):
        def fetch():
            filtros = self._obter_filtros_exportacao()
            formato = self._export_formato.get() if self._export_formato else "csv"
            return metodo(filtros=filtros, formato=formato)

        def on_success(res):
            if res.get("success"):
                data = res.get("data", {})
                content = data.get("content")
                fmt = data.get("format", "csv")
                nome = data.get("filename", "export_{}".format(__import__("datetime").datetime.now().strftime("%Y%m%d")))
                ext = {"csv": ".csv", "excel": ".xlsx", "json": ".json"}.get(fmt, ".txt")
                mime_types = {"csv": "CSV", "excel": "Excel", "json": "JSON"}
                destino = filedialog.asksaveasfilename(
                    initialfile=nome,
                    defaultextension=ext,
                    filetypes=[(mime_types.get(fmt, "Arquivo"), f"*{ext}"), ("Todos", "*.*")]
                )
                if destino:
                    if fmt == "excel":
                        with open(destino, "wb") as f:
                            f.write(content)
                    else:
                        with open(destino, "w", encoding="utf-8") as f:
                            f.write(content)
                    self._show_success(f"Exportado para:\n{destino}")
            else:
                self._show_error(res.get("message", "Falha ao exportar."))

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=lambda exc: self._show_error(f"Falha ao exportar.\n{exc}"),
            widget_ref=self,
        )

    def _criar_lista_relatorios(self):
        card = Card(self, padding=(SPACING["card_pad"], SPACING["label_gap"]))
        card.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(SPACING["item_gap"], 0))

        hdr = ctk.CTkFrame(card.body, fg_color="transparent")
        hdr.pack(fill="x")

        ctk.CTkLabel(
            hdr,
            text="Relatórios Gerados",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        filters = ctk.CTkFrame(hdr, fg_color="transparent")
        filters.pack(side="right")

        self.filtro_busca = ctk.CTkEntry(
            filters,
            placeholder_text="Buscar...",
            width=160,
            height=34,
            font=themed_font("body_sm"),
            corner_radius=RADIUS["input"],
        )
        self.filtro_busca.pack(side="left", padx=(0, SPACING["xs"]))
        self.filtro_busca.bind("<Return>", lambda e: self._filtrar_relatorios())

        self.filtro_data_inicio = ctk.CTkEntry(
            filters,
            placeholder_text="De",
            width=100,
            height=34,
            font=themed_font("body_sm"),
            corner_radius=RADIUS["input"],
        )
        self.filtro_data_inicio.pack(side="left", padx=(0, SPACING["xs"]))
        self.filtro_data_inicio.bind("<Return>", lambda e: self._filtrar_relatorios())

        self.filtro_data_fim = ctk.CTkEntry(
            filters,
            placeholder_text="Até",
            width=100,
            height=34,
            font=themed_font("body_sm"),
            corner_radius=RADIUS["input"],
        )
        self.filtro_data_fim.pack(side="left", padx=(0, SPACING["xs"]))
        self.filtro_data_fim.bind("<Return>", lambda e: self._filtrar_relatorios())

        self.filtro_tipo = ctk.CTkOptionMenu(
            filters,
            values=[
                "Todos os tipos",
                "Geral",
                "Estudante",
                "Agendamentos",
                "Intervenções",
                "Triagens",
                "Estatísticas",
            ],
            font=themed_font("body"),
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            width=150,
            height=34,
            corner_radius=RADIUS["input"],
            command=lambda _: self._filtrar_relatorios(),
        )
        self.filtro_tipo.pack(side="left", padx=(0, SPACING["xs"]))

        PrimaryButton(
            filters,
            text="Filtrar",
            command=self._filtrar_relatorios,
            width=80,
            height=34,
            size="sm",
        ).pack(side="left")

        Divider(card.body).pack(fill="x", pady=(SPACING["label_gap"], 0))

        self._bulk_bar = ctk.CTkFrame(
            card.body, fg_color=THEME["primary_soft"], corner_radius=RADIUS["md"]
        )
        self._bulk_bar.pack(fill="x", pady=(SPACING["label_gap"], 0))
        self._bulk_bar.pack_forget()

        bulk_inner = ctk.CTkFrame(self._bulk_bar, fg_color="transparent")
        bulk_inner.pack(fill="x", padx=SPACING["card_pad"], pady=SPACING["icon_gap"])

        self._bulk_count_lbl = ctk.CTkLabel(
            bulk_inner,
            text="0 selecionado(s)",
            font=themed_font("body", "bold"),
            text_color=THEME["primary"],
        )
        self._bulk_count_lbl.pack(side="left")

        PrimaryButton(
            bulk_inner,
            text=f"{ICONS['download']} Baixar ZIP",
            command=self._bulk_download,
            width=120,
            height=34,
            size="sm",
        ).pack(side="right", padx=(SPACING["xs"], 0))
        DangerButton(
            bulk_inner,
            text=f"{ICONS['delete']} Excluir",
            command=self._bulk_delete,
            width=100,
            height=34,
        ).pack(side="right", padx=(0, SPACING["xs"]))
        GhostButton(
            bulk_inner, text="Cancelar", command=self._limpar_selecao, width=80, height=34
        ).pack(side="right")

        col_hdr = ctk.CTkFrame(card.body, fg_color="transparent")
        col_hdr.pack(fill="x", pady=(SPACING["label_gap"], 0))
        col_hdr.grid_columnconfigure(0, weight=0)
        col_hdr.grid_columnconfigure(1, weight=3)
        col_hdr.grid_columnconfigure(2, weight=1)
        col_hdr.grid_columnconfigure(3, weight=1)
        col_hdr.grid_columnconfigure(4, weight=1)

        self._select_all_var = ctk.StringVar(value="0")
        ctk.CTkCheckBox(
            col_hdr,
            text="",
            variable=self._select_all_var,
            command=self._toggle_selecao_todos,
            width=24,
            height=24,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
        ).grid(row=0, column=0, sticky="w", padx=(0, SPACING["icon_gap"]))

        for i, txt in enumerate(["Nome do Relatório", "Tipo", "Data", "Ações"]):
            ctk.CTkLabel(
                col_hdr,
                text=txt,
                font=themed_font("body_sm", "bold"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).grid(row=0, column=i + 1, sticky="w", padx=(0 if i else SPACING["icon_gap"], 0))

        Divider(card.body).pack(fill="x", pady=(SPACING["label_gap"], 0))

        self.reports_container = ctk.CTkScrollableFrame(
            card.body,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.reports_container.pack(
            fill="both", expand=True, pady=(SPACING["label_gap"], SPACING["icon_gap"])
        )

    def _filtrar_relatorios(self):
        tipo = self.filtro_tipo.get() if self.filtro_tipo is not None else "Todos os tipos"
        tipo_map = {
            "Todos os tipos": None,
            "Geral": "geral",
            "Estudante": "estudante",
            "Agendamentos": "agendamentos",
            "Intervenções": "intervencoes",
            "Triagens": "triagens",
            "Estatísticas": "estatisticas",
        }
        search = self.filtro_busca.get().strip() or None if self.filtro_busca is not None else None
        data_inicio = self.filtro_data_inicio.get().strip() or None if self.filtro_data_inicio is not None else None
        data_fim = self.filtro_data_fim.get().strip() or None if self.filtro_data_fim is not None else None

        def fetch():
            return self.servico_relatorio.listar_relatorios(
                tipo=tipo_map.get(tipo), search=search, data_inicio=data_inicio, data_fim=data_fim
            )

        AsyncRunner.run(
            task=fetch,
            on_success=self._on_filter_success,
            on_error=lambda exc: self._show_error(f"Falha ao filtrar.\n{exc}"),
            widget_ref=self,
        )

    def _on_filter_success(self, res):
        if res.get("success"):
            items = self._extract_items(res.get("data", {}))
            self._popular_lista(items)
        else:
            self._show_error(res.get("message", "Falha ao filtrar relatórios."))

    def _toggle_selecao(self, report_id: int):
        if report_id in self._selecionados:
            self._selecionados.discard(report_id)
        else:
            self._selecionados.add(report_id)
        self._atualizar_bulk_bar()

    def _toggle_selecao_todos(self):
        if self._select_all_var.get() == "1":
            self._selecionados = {r.get("id") for r in self._todos_relatorios if r.get("id")}
        else:
            self._selecionados.clear()
        self._atualizar_bulk_bar()
        self._popular_lista(self._todos_relatorios)

    def _limpar_selecao(self):
        self._selecionados.clear()
        self._select_all_var.set("0")
        self._atualizar_bulk_bar()
        self._popular_lista(self._todos_relatorios)

    def _atualizar_bulk_bar(self):
        count = len(self._selecionados)
        if count > 0:
            self._bulk_bar.pack(fill="x", pady=(SPACING["label_gap"], 0))
            self._bulk_count_lbl.configure(text=f"{count} selecionado(s)")
        else:
            self._bulk_bar.pack_forget()

    def _bulk_delete(self):
        if not self._selecionados:
            return
        if not self._confirmar(f"Excluir {len(self._selecionados)} relatório(s)?"):
            return
        try:
            res = self.servico_relatorio.deletar_lote(list(self._selecionados))
            if res.get("success"):
                self._show_success(res.get("message", "Excluídos com sucesso."))
                self._limpar_selecao()
                self._carregar_dados()
            else:
                self._show_error(res.get("message", "Falha ao excluir."))
        except Exception as e:
            self._show_error(f"Falha ao excluir em lote.\n{e}")

    def _bulk_download(self):
        if not self._selecionados:
            return
        try:
            res = self.servico_relatorio.baixar_lote(list(self._selecionados))
            if res.get("success"):
                paths = res.get("data", {}).get("file_paths", [])
                if not paths:
                    self._show_error("Nenhum arquivo disponível para download.", title="Informação")
                    return

                destino = filedialog.askdirectory()
                if destino:
                    for p in paths:
                        if os.path.exists(p):
                            shutil.copy2(p, os.path.join(destino, os.path.basename(p)))
                    self._show_success(f"{len(paths)} arquivo(s) copiado(s).")
            else:
                self._show_error(res.get("message", "Falha ao baixar."))
        except Exception as e:
            self._show_error(f"Falha ao baixar em lote.\n{e}")

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
                corner_radius=RADIUS["lg"],
                height=100,
            ).pack(fill="x", pady=8)
            EmptyState(
                self.reports_container,
                icon=ICONS["file"],
                title="Nenhum relatório encontrado",
                subtitle="",
            ).pack(pady=SPACING["section_gap"])
            return

        batch = WidgetBatchBuilder(parent=self, batch_size=20)
        for r in reports:
            batch.add(lambda r=r: self._criar_row_relatorio(r))
        batch.execute()

    def _criar_row_relatorio(self, report: dict):
        row = ctk.CTkFrame(
            self.reports_container,
            fg_color=THEME["row_bg"],
            corner_radius=RADIUS["button"],
        )
        row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
        row.grid_columnconfigure(0, weight=0)
        row.grid_columnconfigure(1, weight=3)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=1)
        row.grid_columnconfigure(4, weight=1)

        row.bind("<Enter>", lambda e: row.configure(fg_color=THEME["row_hover"]))
        row.bind("<Leave>", lambda e: row.configure(fg_color=THEME["row_bg"]))

        report_id = report.get("id")
        sel_var = ctk.StringVar(value="1" if report_id in self._selecionados else "0")

        chk = ctk.CTkCheckBox(
            row,
            text="",
            variable=sel_var,
            command=lambda: self._toggle_selecao(report_id),
            width=24,
            height=24,
            fg_color=THEME["primary"],
        )
        chk.grid(
            row=0,
            column=0,
            sticky="w",
            padx=(SPACING["icon_gap"], SPACING["xs"]),
            pady=SPACING["item_gap"],
        )

        icon_bg = ctk.CTkFrame(
            row, fg_color=THEME["kpi_blue_soft"], corner_radius=RADIUS["xs"], width=32, height=32
        )
        icon_bg.grid(
            row=0, column=1, sticky="w", padx=(0, SPACING["icon_gap"]), pady=SPACING["item_gap"]
        )
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=ICONS["file"], font=themed_font("h4")).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        name_cell = ctk.CTkFrame(row, fg_color="transparent")
        name_cell.grid(
            row=0, column=1, sticky="w", padx=(SPACING["icon_gap"], 0), pady=SPACING["item_gap"]
        )
        ctk.CTkLabel(
            name_cell,
            text=report.get("name", "Relatório"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        tipo = report.get("type", report.get("report_type", "Geral"))
        bg, fg = _CHIP.get(tipo, (THEME["border"], THEME["text_secondary"]))
        chip = Chip(row, text=tipo, fg_color=bg, text_color=fg)
        chip.grid(row=0, column=2, sticky="w", padx=SPACING["icon_gap"], pady=SPACING["item_gap"])

        data_str = report.get("generated_at") or report.get("created_at") or "Hoje"
        if len(data_str) > 10:
            data_str = data_str[:10]

        ctk.CTkLabel(
            row,
            text=data_str,
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=3, sticky="w", padx=SPACING["icon_gap"], pady=SPACING["item_gap"])

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(
            row=0, column=4, sticky="e", padx=SPACING["icon_gap"], pady=SPACING["icon_gap"]
        )

        for icon, cmd in [
            (ICONS["view"], lambda r=report: self._visualizar_relatorio(r)),
            (ICONS["download"], lambda r=report: self._abrir_modal_download(r)),
            (ICONS["delete"], lambda r=report: self._excluir_relatorio(r)),
        ]:
            GhostButton(
                actions,
                text=icon,
                width=30,
                height=30,
                corner_radius=RADIUS["xs"],
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=cmd,
            ).pack(side="left", padx=SPACING["label_gap"] // 2)

    def _abrir_modal_gerar_relatorio(self, report_type=None):
        modal = BaseModal(self, title="Gerar Novo Relatório", width=560, height=520)

        wrapper = ctk.CTkFrame(modal, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=f"{ICONS['file']}  Gerar Novo Relatório",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            wrapper,
            text="Template (Opcional)",
            font=themed_font("body_sm", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

        self._modal_template = ctk.CTkOptionMenu(
            wrapper,
            values=["Sem template"],
            font=themed_font("body"),
            height=36,
            corner_radius=RADIUS["input"],
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
        )
        self._modal_template.pack(fill="x", pady=(0, spacing("md")))

        def _load_templates():
            try:
                res = self.servico_report_template.listar_templates()
                if res.get("success"):
                    templates = res.get("data", [])
                    if isinstance(templates, dict):
                        templates = templates.get("templates", [])
                    vals = ["Sem template"] + [
                        f"{t.get('id')} - {t.get('name', '')}"
                        for t in templates
                        if isinstance(t, dict)
                    ]
                    self._modal_template.configure(values=vals)
                    if vals:
                        self._modal_template.set(vals[0])
            except Exception:
                pass

        AsyncRunner.run(task=_load_templates, widget_ref=modal)

        ctk.CTkLabel(
            wrapper,
            text="Título do Relatório (Opcional)",
            font=themed_font("body_sm", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")
        self._modal_nome = ctk.CTkEntry(
            wrapper,
            height=36,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
            placeholder_text="Ex: Fechamento Jan/2026",
        )
        self._modal_nome.pack(fill="x", pady=(0, spacing("md")))

        ctk.CTkLabel(
            wrapper,
            text="Tipo de Relatório",
            font=themed_font("body_sm", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

        opcoes_tipo = [
            "geral",
            "estudante",
            "agendamentos",
            "intervencoes",
            "triagens",
            "estatisticas",
        ]
        self._modal_tipo = ctk.CTkOptionMenu(
            wrapper,
            values=opcoes_tipo,
            font=themed_font("body"),
            height=36,
            corner_radius=RADIUS["input"],
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            command=self._toggle_modal_campos_condicionais,
        )
        self._modal_tipo.pack(fill="x", pady=(0, spacing("md")))
        if report_type and report_type in opcoes_tipo:
            self._modal_tipo.set(report_type)

        self._modal_student_frame = ctk.CTkFrame(
            wrapper, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"]
        )
        self._modal_student_frame.pack(fill="x", pady=(0, spacing("md")))
        self._modal_student_frame.pack_forget()

        ctk.CTkLabel(
            self._modal_student_frame,
            text="ID do Estudante",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", padx=SPACING["card_pad"], pady=(SPACING["icon_gap"], 0))
        self._modal_student_id = ctk.CTkEntry(
            self._modal_student_frame,
            height=36,
            width=200,
            font=themed_font("body"),
            placeholder_text="Ex: 1",
        )
        self._modal_student_id.pack(
            fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["icon_gap"])
        )

        self._modal_date_frame = ctk.CTkFrame(
            wrapper, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"]
        )
        self._modal_date_frame.pack(fill="x", pady=(0, spacing("md")))
        self._modal_date_frame.pack_forget()

        date_grid = ctk.CTkFrame(self._modal_date_frame, fg_color="transparent")
        date_grid.pack(fill="x", padx=SPACING["card_pad"], pady=SPACING["icon_gap"])
        date_grid.grid_columnconfigure(0, weight=1)
        date_grid.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            date_grid,
            text="Data Início",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=0, sticky="w")
        self._modal_data_inicio = ctk.CTkEntry(
            date_grid, height=36, font=themed_font("body"), placeholder_text="YYYY-MM-DD"
        )
        self._modal_data_inicio.grid(row=1, column=0, sticky="ew", padx=(0, SPACING["xs"]))

        ctk.CTkLabel(
            date_grid,
            text="Data Fim",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=1, sticky="w")
        self._modal_data_fim = ctk.CTkEntry(
            date_grid, height=36, font=themed_font("body"), placeholder_text="YYYY-MM-DD"
        )
        self._modal_data_fim.grid(row=1, column=1, sticky="ew", padx=(SPACING["xs"], 0))

        ctk.CTkLabel(
            wrapper,
            text="Formato de Saída",
            font=themed_font("body_sm", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")
        fmt_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        fmt_row.pack(fill="x", pady=(0, spacing("md")))

        self._modal_formato = ctk.StringVar(value="pdf")
        for fmt, label in [("pdf", "PDF"), ("excel", "Excel"), ("csv", "CSV"), ("json", "JSON")]:
            ctk.CTkRadioButton(
                fmt_row,
                text=label,
                variable=self._modal_formato,
                value=fmt,
                font=themed_font("body_sm"),
                fg_color=THEME["primary"],
            ).pack(side="left", padx=(0, SPACING["icon_gap"]))

        btns = ctk.CTkFrame(wrapper, fg_color="transparent")
        btns.pack(fill="x", pady=(spacing("md"), 0))
        PrimaryButton(
            btns,
            text="Gerar Relatório",
            command=self._confirmar_gerar_relatorio,
            width=160,
            height=40,
        ).pack(side="right", padx=(spacing("sm"), 0))
        GhostButton(btns, text="Cancelar", command=modal.destroy, width=120, height=40).pack(
            side="right"
        )

        self._toggle_modal_campos_condicionais(self._modal_tipo.get())

    def _toggle_modal_campos_condicionais(self, tipo):
        if tipo == "estudante":
            self._modal_student_frame.pack(fill="x", pady=(0, spacing("md")))
        else:
            self._modal_student_frame.pack_forget()

        if tipo in ("agendamentos", "triagens", "intervencoes"):
            self._modal_date_frame.pack(fill="x", pady=(0, spacing("md")))
        else:
            self._modal_date_frame.pack_forget()

    def _confirmar_gerar_relatorio(self):
        try:
            template_val = self._modal_template.get()
            nome = self._modal_nome.get().strip()
            tipo = self._modal_tipo.get()
            formato = self._modal_formato.get()

            id_template = None
            if template_val and template_val != "Sem template":
                parts = template_val.split(" - ", 1)
                if parts[0].isdigit():
                    id_template = int(parts[0])

            parametros: dict = {}
            if tipo == "estudante":
                sid = self._modal_student_id.get().strip()
                if sid.isdigit():
                    parametros["student_id"] = int(sid)
            if tipo in ("agendamentos", "triagens", "intervencoes"):
                parametros["date_from"] = self._modal_data_inicio.get().strip()
                parametros["date_to"] = self._modal_data_fim.get().strip()
            parametros["format"] = formato

            if id_template:
                task = lambda: self.servico_relatorio.gerar_relatorio_por_template(
                    id_template, parametros
                )
            else:
                task = lambda: self.servico_relatorio.gerar_relatorio(
                    {
                        "name": nome or f"Relatório {tipo}",
                        "report_type": tipo,
                        "format": formato,
                        "parameters": str(parametros),
                        "data": "{}",
                        "file_path": "",
                        "file_size": 0,
                        "is_public": False,
                        "generated_by_id": 1,
                    }
                )

            AsyncRunner.run(
                task=task,
                on_success=self._on_generate_success,
                on_error=lambda exc: self._show_error(f"Falha ao gerar relatório.\n{exc}"),
                widget_ref=self,
            )
        except Exception as e:
            self._show_error(f"Falha ao gerar relatório.\n{e}")

    def _on_generate_success(self, res):
        if isinstance(res, dict) and res.get("success"):
            self._show_success(
                res.get("message", res.get("data", {}).get("name", "Relatório gerado."))
            )
            self._carregar_dados()
        else:
            msg = (
                res.get("message", "Falha ao gerar relatório.")
                if isinstance(res, dict)
                else "Falha ao gerar relatório."
            )
            self._show_error(msg)

    def _abrir_modal_download(self, report):
        modal = BaseModal(self, title="Baixar Relatório", width=400, height=280)
        wrapper = ctk.CTkFrame(modal, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=f"{ICONS['download']}  Baixar Relatório",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            wrapper,
            text=report.get("name", "Relatório"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")

        formats = [
            ("pdf", "PDF", THEME["kpi_violet"]),
            ("excel", "Excel", THEME["kpi_green"]),
            ("csv", "CSV", THEME["kpi_amber"]),
            ("json", "JSON", THEME["kpi_blue"]),
        ]
        for fmt_key, fmt_label, accent in formats:
            ctk.CTkButton(
                wrapper,
                text=f"Baixar {fmt_label}",
                command=lambda f=fmt_key, r=report: self._baixar_relatorio_formato(r, f),
                height=38,
                corner_radius=RADIUS["button"],
                fg_color=accent,
                hover_color=THEME["primary_hover"],
                text_color=THEME["text_on_primary"],
                font=themed_font("body", "bold"),
            ).pack(fill="x", pady=SPACING["grid_gap"] // 2)

        GhostButton(wrapper, text="Cancelar", command=modal.destroy, width=120, height=38).pack(
            fill="x", pady=(SPACING["label_gap"], 0)
        )

    def _baixar_relatorio_formato(self, report, formato):
        try:
            res = self.servico_relatorio.baixar_relatorio(report.get("id"))
            if not res.get("success"):
                self._show_error(res.get("message", "Relatório não encontrado."))
                return

            nome = report.get("name", "relatorio")
            ext = {"pdf": ".pdf", "excel": ".xlsx", "csv": ".csv", "json": ".json"}.get(
                formato, ".txt"
            )
            destino = filedialog.asksaveasfilename(
                initialfile=f"{nome}{ext}",
                defaultextension=ext,
                filetypes=[(fmt.upper(), f"*{ext}") for fmt in ["pdf", "excel", "csv", "json"]]
                + [("Todos", "*.*")],
            )
            if destino:
                file_path = res.get("data", {}).get("file_path", "")
                if file_path and os.path.exists(file_path):
                    shutil.copy2(file_path, destino)
                else:
                    with open(destino, "w", encoding="utf-8") as f:
                        f.write(
                            f"Relatório: {nome}\nTipo: {report.get('type')}\nFormato: {formato}\n"
                        )
                self._show_success(f"Relatório salvo em:\n{destino}")
        except Exception as e:
            self._show_error(f"Falha ao baixar.\n{e}")

    def _visualizar_relatorio(self, report):
        modal = BaseModal(self, title="Visualizar Relatório", width=600, height=480)
        wrapper = ctk.CTkFrame(modal, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=f"{ICONS['file']}  {report.get('name', 'Relatório')}",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        info = ctk.CTkFrame(wrapper, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"])
        info.pack(fill="x", pady=(0, SPACING["label_gap"]))

        rows = [
            ("Tipo", report.get("type", report.get("report_type", "—"))),
            ("Formato", report.get("format", "—")),
            (
                "Gerado em",
                str(report.get("generated_at", "—"))[:19] if report.get("generated_at") else "—",
            ),
        ]
        for k, v in rows:
            r = ctk.CTkFrame(info, fg_color="transparent")
            r.pack(fill="x", padx=SPACING["card_pad"], pady=SPACING["grid_gap"] // 2)
            ctk.CTkLabel(
                r, text=k, font=themed_font("body_sm"), text_color=THEME["text_muted"]
            ).pack(side="left")
            ctk.CTkLabel(
                r, text=str(v), font=themed_font("body", "bold"), text_color=THEME["text"]
            ).pack(side="right")

        ctk.CTkLabel(
            wrapper, text="Conteúdo", font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack(anchor="w", pady=(SPACING["label_gap"], 0))

        content = ctk.CTkTextbox(
            wrapper,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["md"],
            font=themed_font("body"),
            text_color=THEME["text"],
        )
        content.pack(fill="both", expand=True)
        content.insert("1.0", f"Relatório: {report.get('name', 'Relatório')}\n")
        content.insert("end", f"Tipo: {report.get('type', report.get('report_type', '—'))}\n")
        content.insert("end", f"Formato: {report.get('format', '—')}\n")
        content.insert("end", f"Gerado em: {report.get('generated_at', '—')}\n")
        content.insert("end", f"Caminho: {report.get('file_path', '—')}\n")
        content.configure(state="disabled")

        btns = ctk.CTkFrame(wrapper, fg_color="transparent")
        btns.pack(fill="x", pady=(SPACING["label_gap"], 0))
        PrimaryButton(
            btns,
            text=f"{ICONS['download']} Baixar PDF",
            command=lambda: self._baixar_relatorio_formato(report, "pdf"),
            width=140,
            height=38,
        ).pack(side="right", padx=(spacing("sm"), 0))
        GhostButton(btns, text="Fechar", command=modal.destroy, width=120, height=38).pack(
            side="right"
        )

    def _excluir_relatorio(self, report):
        rid = report.get("id")
        if not rid or not self._confirmar("Excluir este relatório?"):
            return
        try:
            res = self.servico_relatorio.deletar_relatorio(rid)
            if res.get("success"):
                self._show_success("Relatório excluído.")
                self._carregar_dados()
            else:
                self._show_error(res.get("message", "Falha ao excluir."))
        except Exception as e:
            self._show_error(f"Falha ao excluir relatório.\n{e}")

    def _criar_secao_templates(self):
        card = Card(self, padding=(SPACING["card_pad"], SPACING["label_gap"]))
        card.pack(
            fill="both",
            expand=True,
            padx=SPACING["page_x"],
            pady=(SPACING["item_gap"], SPACING["page_y"]),
        )

        hdr = ctk.CTkFrame(card.body, fg_color="transparent")
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr,
            text="Templates de Relatório",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")
        PrimaryButton(
            hdr,
            text=f"{ICONS['add']} Novo Template",
            command=self._abrir_modal_template,
            height=36,
            width=160,
            size="sm",
        ).pack(side="right")

        Divider(card.body).pack(fill="x", pady=(SPACING["label_gap"], 0))

        self._templates_filtro = ctk.CTkOptionMenu(
            card.body,
            values=[
                "Todos",
                "geral",
                "estudante",
                "agendamentos",
                "triagens",
                "estatisticas",
                "intervencoes",
            ],
            font=themed_font("body"),
            height=34,
            width=160,
            corner_radius=RADIUS["input"],
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            command=lambda _: self._carregar_templates(),
        )
        self._templates_filtro.pack(anchor="e", pady=(0, SPACING["label_gap"]))

        self.templates_container = ctk.CTkScrollableFrame(
            card.body,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.templates_container.pack(fill="both", expand=True)

        self._carregar_templates()

    def _carregar_templates(self):
        tipo = self._templates_filtro.get()
        tipo_val = None if tipo == "Todos" else tipo

        def fetch():
            return self.servico_report_template.listar_templates(tipo=tipo_val)

        AsyncRunner.run(
            task=fetch,
            on_success=self._popular_lista_templates,
            on_error=lambda exc: self._show_error(f"Falha ao carregar templates.\n{exc}"),
            widget_ref=self,
        )

    def _popular_lista_templates(self, res):
        if not hasattr(self, "templates_container"):
            return
        for w in self.templates_container.winfo_children():
            w.destroy()

        templates = []
        if isinstance(res, dict):
            if res.get("success") is False:
                EmptyState(
                    self.templates_container,
                    icon=ICONS["bolt"],
                    title="Erro ao carregar templates",
                    subtitle=res.get("message", ""),
                ).pack(pady=20)
                return
            data = res.get("data")
            if isinstance(data, list):
                templates = data
            elif isinstance(data, dict):
                templates = data.get("templates", [])
        elif isinstance(res, list):
            templates = res

        if not templates:
            EmptyState(
                self.templates_container,
                icon=ICONS["empty"],
                title="Nenhum template encontrado",
                subtitle="Crie um novo template para começar",
            ).pack(pady=30)
            return

        batch = WidgetBatchBuilder(parent=self, batch_size=20)
        for t in templates:
            if isinstance(t, dict):
                batch.add(lambda t=t: self._criar_row_template(t))
        batch.execute()

    def _criar_row_template(self, template: dict):
        row = ctk.CTkFrame(
            self.templates_container,
            fg_color=THEME["row_bg"],
            corner_radius=RADIUS["button"],
        )
        row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)

        row.bind("<Enter>", lambda e: row.configure(fg_color=THEME["row_hover"]))
        row.bind("<Leave>", lambda e: row.configure(fg_color=THEME["row_bg"]))

        ctk.CTkLabel(
            row,
            text=template.get("name", "Template"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).grid(row=0, column=0, sticky="w", padx=spacing("md"), pady=spacing("item_gap"))

        ctk.CTkLabel(
            row,
            text=template.get("report_type", "geral"),
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=1, sticky="w", padx=spacing("md"), pady=spacing("item_gap"))

        acts = ctk.CTkFrame(row, fg_color="transparent")
        acts.grid(row=0, column=2, sticky="e", padx=spacing("md"), pady=spacing("icon_gap"))

        for icon, cmd in [
            (ICONS["view"], lambda t=template: self._preview_template(t)),
            (ICONS["edit"], lambda t=template: self._abrir_modal_template(t)),
            (ICONS["delete"], lambda t=template: self._excluir_template(t)),
        ]:
            GhostButton(
                acts,
                text=icon,
                width=30,
                height=30,
                corner_radius=RADIUS["xs"],
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=cmd,
            ).pack(side="left", padx=spacing("label_gap") // 2)

    def _abrir_modal_template(self, template=None):
        modal = BaseModal(
            self,
            title="Novo Template" if not template else "Editar Template",
            width=560,
            height=420,
        )
        modal.configure(fg_color=THEME["surface"])

        wrapper = ctk.CTkFrame(modal, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=f"{ICONS['file']}  {'Novo Template' if not template else 'Editar Template'}",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            wrapper, text="Nome", font=themed_font("body_sm"), text_color=THEME["text"]
        ).pack(anchor="w")
        self._tmpl_nome = ctk.CTkEntry(
            wrapper,
            height=36,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
        )
        self._tmpl_nome.pack(fill="x", pady=(0, spacing("md")))
        if template:
            self._tmpl_nome.insert(0, template.get("name", ""))

        ctk.CTkLabel(
            wrapper, text="Tipo", font=themed_font("body_sm"), text_color=THEME["text"]
        ).pack(anchor="w")
        self._tmpl_tipo = ctk.CTkOptionMenu(
            wrapper,
            values=[
                "geral",
                "estudante",
                "agendamentos",
                "triagens",
                "estatisticas",
                "intervencoes",
            ],
            font=themed_font("body"),
            height=36,
            corner_radius=RADIUS["input"],
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
        )
        self._tmpl_tipo.pack(fill="x", pady=(0, spacing("md")))
        if template:
            self._tmpl_tipo.set(template.get("report_type", "geral"))

        ctk.CTkLabel(
            wrapper,
            text="Configuração (JSON opcional)",
            font=themed_font("body_sm"),
            text_color=THEME["text"],
        ).pack(anchor="w")
        self._tmpl_config = ctk.CTkTextbox(
            wrapper,
            height=100,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
        )
        self._tmpl_config.pack(fill="x", pady=(0, spacing("md")))
        if template:
            cfg = template.get("template_config") or {}
            self._tmpl_config.insert("1.0", str(cfg))

        btns = ctk.CTkFrame(wrapper, fg_color="transparent")
        btns.pack(fill="x", pady=(spacing("md"), 0))
        PrimaryButton(
            btns,
            text="Salvar",
            command=lambda: self._salvar_template(modal, template),
            width=120,
            height=40,
        ).pack(side="right", padx=(spacing("sm"), 0))
        GhostButton(btns, text="Cancelar", command=modal.destroy, width=120, height=40).pack(
            side="right"
        )

    def _salvar_template(self, modal, template=None):
        nome = self._tmpl_nome.get().strip()
        tipo = self._tmpl_tipo.get()
        if not nome:
            self._show_error("Nome do template é obrigatório.")
            return

        config_text = self._tmpl_config.get("1.0", "end").strip()
        try:
            import json

            config = json.loads(config_text) if config_text else {}
        except Exception:
            config = {}

        dados = {
            "name": nome,
            "report_type": tipo,
            "template_config": config,
            "is_active": True,
        }

        def fetch():
            if template:
                return self.servico_report_template.atualizar_template(template.get("id"), dados)
            return self.servico_report_template.criar_template(dados)

        AsyncRunner.run(
            task=fetch,
            on_success=lambda res: self._on_template_save(res, modal),
            on_error=lambda exc: self._show_error(f"Falha ao salvar template.\n{exc}"),
            widget_ref=self,
        )

    def _on_template_save(self, res, modal):
        if isinstance(res, dict) and res.get("success") is False:
            self._show_error(res.get("message", "Falha ao salvar template."))
            return
        self._show_success("Template salvo com sucesso.")
        modal.destroy()
        self._carregar_templates()

    def _preview_template(self, template):
        def fetch():
            return self.servico_relatorio.listar_relatorios_filtrados(
                tipo=template.get("report_type"), search=None, data_inicio=None, data_fim=None
            )

        def on_success(res):
            if isinstance(res, dict) and res.get("success"):
                data = res.get("data", [])
                msg = f"Template: {template.get('name')}\nTipo: {template.get('report_type')}\nRegistros encontrados: {len(data)}"
                self._show_success(msg, duration=5000)
            else:
                self._show_error("Falha ao gerar preview.")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=lambda exc: self._show_error(f"Falha no preview.\n{exc}"),
            widget_ref=self,
        )

    def _excluir_template(self, template):
        if not self._confirmar(f"Excluir template '{template.get('name')}'?"):
            return

        def fetch():
            return self.servico_report_template.deletar_template(template.get("id"))

        AsyncRunner.run(
            task=fetch,
            on_success=self._on_template_delete,
            on_error=lambda exc: self._show_error(f"Falha ao excluir template.\n{exc}"),
            widget_ref=self,
        )

    def _on_template_delete(self, res):
        if isinstance(res, dict) and res.get("success") is False:
            self._show_error(res.get("message", "Falha ao excluir template."))
            return
        self._show_success("Template excluído.")
        self._carregar_templates()

    def _filtrar_por_tipo(self, tipo: str):
        if self.filtro_tipo is not None:
            self.filtro_tipo.set(tipo)
        self._filtrar_relatorios()

    def _baixar_relatorio(self, report: dict):
        self._baixar_relatorio_formato(report, "pdf")

    def _exportar_pdf(self):
        self._abrir_modal_gerar_relatorio("geral")
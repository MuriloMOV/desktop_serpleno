import customtkinter as ctk
from PIL import Image
import threading
from services.relatorios import ServicoRelatorio
from ui_theme import THEME, SPACING, RADIUS, themed_font, blend_color, lighten
from components.ui_components import (
    PageHeader, Card, PrimaryButton, SecondaryButton, GhostButton, DangerButton,
    SectionHeader, InputField, SearchField, EmptyState, Divider, Pill, Badge,
    Avatar, Tabs, SegmentedButton, Dropdown, Tooltip, Toast, SkeletonLoader
)


class RelatorioFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_relatorio = ServicoRelatorio()
        self.card_widgets = {}
        self.grid_columnconfigure(0, weight=1)
        self.criar_layout()
        self.load_data()

    def load_data(self):
        def fetch():
            stats = self.servico_relatorio.obter_estatisticas()
            reports = self.servico_relatorio.listar_relatorios()
            self.after(0, lambda: self.update_view(stats, reports))
        threading.Thread(target=fetch, daemon=True).start()

    def update_view(self, stats_res, reports_res):
        if stats_res.get('success'):
            data = stats_res.get('data', {})
            summary = data.get('summary', {})
            self.update_card("Relatório Geral", str(summary.get('students_total', 0)))
            self.update_card("Agendamentos", str(summary.get('appointments_total', 0)))
            self.update_card("Intervenções", str(summary.get('interventions_total', 0)))
            self.update_card("Triagens", str(summary.get('screenings_total', 0)))
        if reports_res.get('success'):
            data = reports_res.get('data', {})
            if isinstance(data, dict):
                items = data.get('reports', []) or data.get('results', [])
            else:
                items = data if isinstance(data, list) else []
            self.populate_reports_list(items)

    def update_card(self, key, value):
        if key in self.card_widgets:
            self.card_widgets[key].configure(text=value)

    def populate_reports_list(self, reports):
        if hasattr(self, 'reports_container'):
            for w in self.reports_container.winfo_children():
                w.destroy()
        if not reports:
            EmptyState(self.reports_container, icon="📄", title="Nenhum relatório encontrado", subtitle="Os relatórios gerados aparecerão aqui").pack(pady=20)
            return
        for r in reports:
            self.create_report_row(r)

    def create_report_row(self, report):
        row = Card(self.reports_container, title="")
        row.pack(fill="x", pady=4)
        inner = row.body
        ctk.CTkLabel(inner, text="📄", font=themed_font("h3")).pack(side="left", padx=(14, 10))
        ctk.CTkLabel(inner, text=report.get('name', 'Relatório'), font=themed_font("body", "bold"), text_color=THEME["text"]).pack(side="left")
        created = report.get('generated_at') or report.get('created_at') or 'Hoje'
        ctk.CTkLabel(inner, text=created, font=themed_font("overline"), text_color=THEME["text_muted"]).pack(side="right", padx=14)
        ctk.CTkLabel(inner, text=report.get('type', 'Geral'), font=themed_font("body"), text_color=THEME["text_muted"]).pack(side="right", padx=10)

    def criar_layout(self):
        header = PageHeader(
            self, title="Relatórios",
            subtitle="Visão gerencial e indicadores",
            show_breadcrumb=True, breadcrumb_parts=["Relatórios", "Geral"],
            actions=[PrimaryButton(None, text="Gerar Relatório", command=lambda: None, width=180, icon="＋")],
        )
        header.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["section_gap"]))
        self.criar_cards()
        self.criar_secao_inferior()
        self.criar_secao_exportacao()
        self.criar_lista_relatorios()

    def criar_cards(self):
        container_cards = ctk.CTkFrame(self, fg_color="transparent")
        container_cards.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["section_gap"]))
        for i in range(4):
            container_cards.grid_columnconfigure(i, weight=1)
        cards_data = [
            ("Relatório Geral", "Visão completa", THEME["info"]),
            ("Agendamentos", "Análise de consultas", THEME["success"]),
            ("Intervenções", "Acompanhamentos", THEME["accent"]),
            ("Triagens", "Análise de triagens", THEME["warning"]),
        ]
        for i, (titulo, subtitulo, accent) in enumerate(cards_data):
            card = Card(container_cards, title="")
            card.grid(row=0, column=i, sticky="ew", padx=8)
            icon_box = ctk.CTkFrame(card.body, fg_color=blend_color(accent, 0.12), width=40, height=40, corner_radius=RADIUS["lg"])
            icon_box.pack(side="left", padx=(0, 12), pady=4)
            icon_box.pack_propagate(False)
            ctk.CTkLabel(icon_box, text=titulo[0], font=themed_font("h2", "bold"), text_color=accent).place(relx=0.5, rely=0.5, anchor="center")
            txt = ctk.CTkFrame(card.body, fg_color="transparent")
            txt.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(txt, text=titulo, font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(4, 0))
            ctk.CTkLabel(txt, text=subtitulo, font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w")
            val = ctk.CTkLabel(card.body, text="--", font=themed_font("h2", "bold"), text_color=THEME["text"])
            val.pack(side="right", padx=(0, 10))
            self.card_widgets[titulo] = val

    def criar_secao_inferior(self):
        container_inferior = ctk.CTkFrame(self, fg_color="transparent")
        container_inferior.pack(fill="x", padx=SPACING["page_x"], pady=(0, 16))
        container_inferior.grid_columnconfigure(0, weight=3)
        container_inferior.grid_columnconfigure(1, weight=1)

        chart_box = Card(container_inferior)
        chart_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(chart_box.body, text="Atividades nos Últimos 30 dias", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(anchor="nw", padx=18, pady=(16, 8))

        summary_box = Card(container_inferior)
        summary_box.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(summary_box.body, text="Resumo", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(anchor="nw", padx=18, pady=(16, 10))
        itens = [("Total de Estudantes", "-"), ("Consultas (30d)", "-"), ("Intervenções (30d)", "-"), ("Triagens (30d)", "-")]
        for texto, valor in itens:
            self.item_resumo(summary_box.body, texto, valor)
        Divider(summary_box.body).pack(fill="x", padx=18, pady=10)
        self.item_resumo(summary_box.body, "Taxa de Comparecimento", "-", cor_valor=THEME["success"])

    def item_resumo(self, parent, texto, valor, cor_valor=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=18, pady=4)
        ctk.CTkLabel(f, text=texto, font=themed_font("body"), text_color=THEME["text_muted"]).pack(side="left")
        ctk.CTkLabel(f, text=valor, font=themed_font("body", "bold"), text_color=cor_valor or THEME["text"]).pack(side="right")

    def criar_secao_exportacao(self):
        export_card = Card(self, title="")
        export_card.pack(fill="x", padx=SPACING["page_x"], pady=(0, 16))
        h = ctk.CTkFrame(export_card.body, fg_color="transparent")
        h.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkLabel(h, text="📥  Exportação de Dados", font=themed_font("h4", "bold"), text_color=THEME["text"]).pack(side="left", padx=(0, 14))
        GhostButton(h, text="Exportar Estudantes (CSV)", command=self.servico_relatorio.exportar_estudantes, width=200).pack(side="left", padx=5)
        GhostButton(h, text="Exportar Agenda (CSV)", command=self.servico_relatorio.exportar_agendamentos, width=190).pack(side="left", padx=5)
        GhostButton(h, text="Exportar Triagens (CSV)", command=self.servico_relatorio.exportar_triagens, width=190).pack(side="left", padx=5)

    def criar_lista_relatorios(self):
        card = Card(self, title="Relatórios Gerados")
        card.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))
        header = ctk.CTkFrame(card.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(header, text="Relatórios Gerados", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")
        self.filtro_tipo = Dropdown(header, values=["Todos os tipos", "Geral", "Estudante", "Agendamentos", "Intervenções", "Triagens", "Estatísticas"], initial="Todos os tipos")
        self.filtro_tipo.pack(side="right", padx=5)
        Divider(card.body).pack(fill="x", pady=(0, 8))
        self.reports_container = ctk.CTkScrollableFrame(card.body, fg_color="transparent")
        self.reports_container.pack(expand=True, fill="both")

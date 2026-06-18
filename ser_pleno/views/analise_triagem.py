import customtkinter as ctk
from services.estudantes import ServicoEstudante
from services.orientacoes import ServicoOrientacoes, servico_orientacoes
from ui_theme import THEME, SPACING, RADIUS, themed_font, blend_color, lighten, darken
from components.ui_components import (
    PageHeader, Card, PrimaryButton, SecondaryButton, GhostButton, DangerButton,
    SectionHeader, InputField, SearchField, EmptyState, Divider, Pill, Badge,
    Avatar, Tabs, SegmentedButton, Dropdown, Tooltip, Toast, SkeletonLoader, KPICard
)


class AnaliseTriagemFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.data_master = [
            {"student": "Bruno Henrique", "date": "23/01/2026", "priority": "Alta", "status": "Pendente"},
            {"student": "Diego Martins", "date": "22/01/2026", "priority": "Média", "status": "Pendente"},
            {"student": "Carla Diaz", "date": "20/01/2026", "priority": "Baixa", "status": "Concluída"},
            {"student": "Ana Beatriz", "date": "19/01/2026", "priority": "Urgente", "status": "Pendente"},
            {"student": "Ana Laura", "date": "24/01/2026", "priority": "Baixa", "status": "Cancelada"},
        ]
        self.grid_columnconfigure(0, weight=1)
        self.criar_cabecalho()
        self.criar_cards_metricas()
        self.criar_filtros()
        self.criar_area_conteudo()

    def criar_cabecalho(self):
        header = PageHeader(
            self, title="Análise de Triagem",
            subtitle="Acompanhamento de triagens e encaminhamentos",
            show_breadcrumb=True, breadcrumb_parts=["Análise", "Triagem"],
            actions=[PrimaryButton(None, text="+ Nova Triagem", command=self.abrir_nova_triagem, width=160, icon="＋")],
        )
        header.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["section_gap"]))

    def criar_cards_metricas(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["section_gap"]))
        for i in range(4):
            container.grid_columnconfigure(i, weight=1)
        metrics = [
            {"label": "Total", "value": str(len(self.data_master)), "icon": "📋", "accent": THEME["info"], "trend": "Registros"},
            {"label": "Pendentes", "value": "3", "icon": "⏳", "accent": THEME["warning"], "trend": "Aguardando"},
            {"label": "Concluídas", "value": "1", "icon": "✅", "accent": THEME["success"], "trend": "Finalizadas"},
            {"label": "Alta Prioridade", "value": "2", "icon": "⚠️", "accent": THEME["danger"], "trend": "Urgente"},
        ]
        for i, m in enumerate(metrics):
            KPICard(container, title=m["label"], value=m["value"], icon=m["icon"], accent=m["accent"], trend=m.get("trend", "")).grid(row=0, column=i, sticky="ew", padx=8)

    def criar_filtros(self):
        card = Card(self)
        card.pack(fill="x", padx=SPACING["page_x"], pady=(0, 16))
        inner = card.body
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))
        for i in range(4):
            row.grid_columnconfigure(i, weight=1)

        self.filtro_status = Dropdown(row, values=["Todos", "Pendente", "Em Andamento", "Concluída", "Cancelada"], initial="Todos")
        self.filtro_status.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 8))
        self.filtro_prioridade = Dropdown(row, values=["Todas", "Baixa", "Média", "Alta", "Urgente"], initial="Todas")
        self.filtro_prioridade.grid(row=0, column=1, sticky="ew", padx=6, pady=(0, 8))
        self.data_inicial = Dropdown(row, values=[""], initial="")
        self.data_inicial = ctk.CTkEntry(row, placeholder_text="dd/mm/aaaa", fg_color=THEME["bg_alt"], border_color=THEME["border"], height=34, corner_radius=RADIUS["sm"])
        self.data_inicial.grid(row=0, column=2, sticky="ew", padx=6, pady=(0, 8))
        self.data_final = ctk.CTkEntry(row, placeholder_text="dd/mm/aaaa", fg_color=THEME["bg_alt"], border_color=THEME["border"], height=34, corner_radius=RADIUS["sm"])
        self.data_final.grid(row=0, column=3, sticky="ew", padx=(6, 0), pady=(0, 8))

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack(fill="x")
        GhostButton(btns, text="Limpar", command=self.limpar_filtros, width=110).pack(side="right", padx=6)
        PrimaryButton(btns, text="Aplicar Filtros", command=self.aplicar_filtros, width=140).pack(side="right")

    def criar_area_conteudo(self):
        card = Card(self, title="Lista de Triagens")
        card.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))
        self.lista_triagens = ctk.CTkScrollableFrame(card.body, fg_color="transparent")
        self.lista_triagens.pack(fill="both", expand=True, pady=8)
        self.renderizar_tabela(self.data_master)

    def aplicar_filtros(self):
        status_f = self.filtro_status.get()
        prioridade_f = self.filtro_prioridade.get()
        filtered = [d for d in self.data_master if (status_f == "Todos" or d["status"] == status_f) and (prioridade_f == "Todas" or d["priority"] == prioridade_f)]
        self.renderizar_tabela(filtered)

    def limpar_filtros(self):
        self.filtro_status.set("Todos")
        self.filtro_prioridade.set("Todas")
        self.data_inicial.delete(0, "end")
        self.data_final.delete(0, "end")
        self.renderizar_tabela(self.data_master)

    def renderizar_tabela(self, data_list):
        for w in self.lista_triagens.winfo_children():
            w.destroy()
        if not data_list:
            EmptyState(self.lista_triagens, icon="📭", title="Nenhuma triagem encontrada", subtitle="Ajuste os filtros ou crie uma nova triagem").pack(pady=20)
            return
        header = ctk.CTkFrame(self.lista_triagens, fg_color=THEME["bg_alt"], height=38, corner_radius=RADIUS["sm"], border_width=1, border_color=THEME["border"])
        header.pack(fill="x", pady=(0, 6))
        for c in ["Estudante", "Data", "Prioridade", "Status"]:
            f = ctk.CTkFrame(header, fg_color="transparent")
            f.pack(side="left", fill="x", expand=True, padx=8)
            ctk.CTkLabel(f, text=c, font=themed_font("caption", "bold"), text_color=THEME["text_muted"]).pack(anchor="w")
        for item in data_list:
            row = Card(self.lista_triagens, title="")
            row.pack(fill="x", pady=3)
            inner = row.body
            cols = [item["student"], item["date"], item["priority"], item["status"]]
            colors = [THEME["text"], THEME["text_secondary"], self.get_priority_color(item["priority"]), THEME["text_secondary"]]
            for idx, (txt, clr) in enumerate(zip(cols, colors)):
                c = ctk.CTkFrame(inner, fg_color="transparent")
                c.pack(side="left", fill="x", expand=True, padx=8)
                bold = idx == 0
                ctk.CTkLabel(c, text=txt, font=themed_font("body", "bold" if bold else "normal"), text_color=clr).pack(anchor="w")

    def get_priority_color(self, p):
        return {"Alta": THEME["danger"], "Urgente": THEME["danger_strong"], "Média": THEME["warning"], "Baixa": THEME["success"]}.get(p, THEME["text_muted"])

    def abrir_nova_triagem(self):
        print("Modal Nova Triagem")

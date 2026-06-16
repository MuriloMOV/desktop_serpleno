import customtkinter as ctk
from services.estudantes import ServicoEstudante
from services.orientacoes import ServicoOrientacoes, servico_orientacoes
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    KPICard,
    PrimaryButton,
    GhostButton,
    SearchField,
    EmptyState,
    Divider,
    Pill,
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
            self,
            title="Análise de Triagem",
            subtitle="Acompanhamento de triagens e encaminhamentos",
            actions=[PrimaryButton(None, text="+ Nova Triagem", command=self.abrir_nova_triagem, width=160, icon="＋")],
        )
        header.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 16))

    def criar_cards_metricas(self):
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="x", padx=SPACING["page_x"], pady=(0, 16))
        for i in range(4):
            cards_container.grid_columnconfigure(i, weight=1)

        metrics = [
            {"label": "Total", "value": str(len(self.data_master)), "icon": "📋", "accent": THEME["info"], "trend": "Registros"},
            {"label": "Pendentes", "value": "3", "icon": "⏳", "accent": THEME["warning"], "trend": "Aguardando"},
            {"label": "Concluídas", "value": "1", "icon": "✅", "accent": THEME["success"], "trend": "Finalizadas"},
            {"label": "Alta Prioridade", "value": "2", "icon": "⚠️", "accent": THEME["danger"], "trend": "Urgente"},
        ]

        for i, m in enumerate(metrics):
            KPICard(
                cards_container,
                title=m["label"],
                value=m["value"],
                icon=m["icon"],
                accent=m["accent"],
                trend=m.get("trend", ""),
            ).grid(row=0, column=i, sticky="ew", padx=6)

    def criar_filtros(self):
        filtro_card = Card(self)
        filtro_card.pack(fill="x", padx=SPACING["page_x"], pady=(0, 16))

        filtro_frame = ctk.CTkFrame(filtro_card.body, fg_color="transparent")
        filtro_frame.pack(fill="x", pady=(0, 12))
        for i in range(4):
            filtro_frame.grid_columnconfigure(i, weight=1)

        self.filtro_status = self.criar_input_filtro(filtro_frame, 0, "Status", ["Todos", "Pendente", "Em Andamento", "Concluída", "Cancelada"])
        self.filtro_prioridade = self.criar_input_filtro(filtro_frame, 1, "Prioridade", ["Todas", "Baixa", "Média", "Alta", "Urgente"])
        self.data_inicial = self.criar_date_input(filtro_frame, 2, "Data Inicial")
        self.data_final = self.criar_date_input(filtro_frame, 3, "Data Final")

        btn_frame = ctk.CTkFrame(filtro_card.body, fg_color="transparent")
        btn_frame.pack(fill="x")
        GhostButton(btn_frame, text="Limpar", command=self.limpar_filtros, width=110).pack(side="right", padx=6)
        PrimaryButton(btn_frame, text="Aplicar Filtros", command=self.aplicar_filtros, width=140).pack(side="right")

    def criar_input_filtro(self, parent, col, label, options):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(f, text=label, font=themed_font("caption", "bold"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(0, 4))
        menu = ctk.CTkOptionMenu(
            f,
            values=options,
            fg_color=THEME["bg_alt"],
            button_color=THEME["border"],
            button_hover_color=THEME["border_strong"],
            text_color=THEME["text"],
            dropdown_fg_color=THEME["card"],
            height=34,
        )
        menu.pack(fill="x")
        return menu

    def criar_date_input(self, parent, col, label):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(f, text=label, font=themed_font("caption", "bold"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(0, 4))
        entry = ctk.CTkEntry(
            f,
            placeholder_text="dd/mm/aaaa",
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            text_color=THEME["text"],
            height=34,
            corner_radius=RADIUS["sm"],
        )
        entry.pack(fill="x")
        return entry

    def criar_area_conteudo(self):
        card = Card(self, title="Lista de Triagens")
        card.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))
        self.lista_triagens = ctk.CTkFrame(card.body, fg_color="transparent")
        self.lista_triagens.pack(fill="both", expand=True, pady=8)
        self.renderizar_tabela(self.data_master)

    def aplicar_filtros(self):
        status_f = self.filtro_status.get()
        prioridade_f = self.filtro_prioridade.get()

        filtered = []
        for d in self.data_master:
            match_status = (status_f == "Todos" or d["status"] == status_f)
            match_prioridade = (prioridade_f == "Todas" or d["priority"] == prioridade_f)
            if match_status and match_prioridade:
                filtered.append(d)

        self.renderizar_tabela(filtered)

    def limpar_filtros(self):
        self.filtro_status.set("Todos")
        self.filtro_prioridade.set("Todas")
        self.data_inicial.delete(0, 'end')
        self.data_final.delete(0, 'end')
        self.renderizar_tabela(self.data_master)

    def renderizar_tabela(self, data_list):
        for w in self.lista_triagens.winfo_children():
            w.destroy()

        if not data_list:
            EmptyState(self.lista_triagens, icon="📭", title="Nenhuma triagem encontrada", subtitle="Ajuste os filtros ou crie uma nova triagem").pack(pady=20)
            return

        header = ctk.CTkFrame(self.lista_triagens, fg_color=THEME["bg_alt"], height=40, corner_radius=RADIUS["sm"])
        header.pack(fill="x", pady=(0, 6))
        for c in ["Estudante", "Data", "Prioridade", "Status", "Ações"]:
            f = ctk.CTkFrame(header, fg_color="transparent")
            f.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(f, text=c, font=themed_font("caption", "bold"), text_color=THEME["text_muted"]).pack(anchor="w")

        for item in data_list:
            row = ctk.CTkFrame(self.lista_triagens, fg_color=THEME["card"], corner_radius=RADIUS["sm"], border_width=1, border_color=THEME["border"])
            row.pack(fill="x", pady=3)
            self.create_list_col(row, item["student"], bold=True)
            self.create_list_col(row, item["date"])
            self.create_list_col(row, item["priority"], color=self.get_priority_color(item["priority"]))
            self.create_list_col(row, item["status"], color=THEME["text_secondary"])

            act_f = ctk.CTkFrame(row, fg_color="transparent")
            act_f.pack(side="left", fill="x", expand=True, padx=5)
            GhostButton(act_f, text="Ver", command=lambda i=item: None, width=70).pack(side="left")

    def create_list_col(self, parent, text, bold=False, color="#1F2937"):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkLabel(f, text=text, font=themed_font("body", "bold" if bold else "normal"), text_color=color).pack(anchor="w")

    def get_priority_color(self, p):
        colors = {"Alta": THEME["danger"], "Urgente": "#B91C1C", "Média": THEME["warning"], "Baixa": THEME["success"]}
        return colors.get(p, THEME["success"])

    def abrir_nova_triagem(self):
        print("Modal Nova Triagem")

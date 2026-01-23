import customtkinter as ctk


class AnaliseTriagemFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="#f4f6fb")
        self.controller = controller

        self.criar_layout()

    # ================= LAYOUT GERAL =================
    def criar_layout(self):
        self.criar_topo()
        self.criar_cards()
        self.criar_filtros()
        self.criar_tabs()
        self.criar_lista()

    # ================= TOPO =================
    def criar_topo(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", pady=(0, 24))

        ctk.CTkLabel(
            topo,
            text="Análise de Triagem",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            topo,
            text="+ Nova Triagem",
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            height=36,
            corner_radius=8
        ).pack(side="right")

    # ================= CARDS =================
    def criar_cards(self):
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 24))

        for i in range(4):
            cards.grid_columnconfigure(i, weight=1)

        self.card(cards, "Total", "3", "#6d28d9").grid(row=0, column=0, padx=8, sticky="ew")
        self.card(cards, "Pendentes", "1", "#f59e0b").grid(row=0, column=1, padx=8, sticky="ew")
        self.card(cards, "Concluídas", "2", "#10b981").grid(row=0, column=2, padx=8, sticky="ew")
        self.card(cards, "Alta Prioridade", "1", "#ef4444").grid(row=0, column=3, padx=8, sticky="ew")

    def card(self, parent, titulo, valor, cor):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)

        ctk.CTkLabel(
            frame,
            text=titulo,
            text_color="#6b7280",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            frame,
            text=valor,
            text_color=cor,
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", padx=16, pady=(0, 14))

        return frame

    # ================= FILTROS =================
    def criar_filtros(self):
        filtros = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        filtros.pack(fill="x", pady=(0, 24))

        filtros.grid_columnconfigure((0, 1, 2, 3), weight=1)
        filtros.grid_columnconfigure(4, weight=0)

        self.filtro_select(filtros, "Status", ["Todos", "Pendentes", "Concluídas"]).grid(
            row=0, column=0, padx=12, pady=16, sticky="ew"
        )
        self.filtro_select(filtros, "Prioridade", ["Todas", "Alta", "Média", "Baixa"]).grid(
            row=0, column=1, padx=12, pady=16, sticky="ew"
        )
        self.filtro_input(filtros, "Data Inicial").grid(
            row=0, column=2, padx=12, pady=16, sticky="ew"
        )
        self.filtro_input(filtros, "Data Final").grid(
            row=0, column=3, padx=12, pady=16, sticky="ew"
        )

        botoes = ctk.CTkFrame(filtros, fg_color="transparent")
        botoes.grid(row=0, column=4, padx=12, pady=16, sticky="e")

        ctk.CTkButton(
            botoes,
            text="Aplicar",
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            height=36,
            width=100,
            corner_radius=8
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            botoes,
            text="Limpar",
            fg_color="#e5e7eb",
            text_color="#111827",
            hover_color="#d1d5db",
            height=36,
            width=80,
            corner_radius=8
        ).pack(side="left", padx=6)

    def filtro_select(self, parent, label, valores):
        frame = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(
            frame,
            text=label,
            text_color="#6b7280",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkOptionMenu(
            frame,
            values=valores,
            height=36,
            fg_color="#f9fafb",
            button_color="#6d28d9",
            button_hover_color="#5b21b6",
            text_color="white",
            dropdown_fg_color="white",
            dropdown_text_color="#111827"
        ).pack(fill="x")

        return frame

    def filtro_input(self, parent, label):
        frame = ctk.CTkFrame(parent, fg_color="transparent")

        ctk.CTkLabel(
            frame,
            text=label,
            text_color="#6b7280",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkEntry(frame, height=36).pack(fill="x")

        return frame

    # ================= TABS =================
    def criar_tabs(self):
        self.tabs = ctk.CTkFrame(self, fg_color="transparent")
        self.tabs.pack(fill="x", pady=(0, 12))

        self.tab("Pendentes", "1", True)
        self.tab("Concluídas", "2", False)
        self.tab("Todas", "3", False)

    def tab(self, texto, badge, ativo):
        frame = ctk.CTkFrame(self.tabs, fg_color="transparent")
        frame.pack(side="left", padx=12)

        cor = "#6d28d9" if ativo else "#6b7280"

        ctk.CTkLabel(
            frame,
            text=texto,
            text_color=cor,
            font=ctk.CTkFont(size=13, weight="bold" if ativo else "normal")
        ).pack(side="left")

        ctk.CTkLabel(
            frame,
            text=badge,
            fg_color="#ede9fe" if ativo else "#e5e7eb",
            text_color=cor,
            corner_radius=12,
            width=28,
            height=22
        ).pack(side="left", padx=6)

    # ================= LISTA =================
    def criar_lista(self):
        lista = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        lista.pack(fill="both", expand=True)

        item = ctk.CTkFrame(lista, fg_color="#f9fafb", corner_radius=10)
        item.pack(fill="x", padx=16, pady=16)

        ctk.CTkLabel(
            item,
            text="Bruno Henrique Souza",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            item,
            text="Avaliação de Adaptação Acadêmica\nAgendada para: 03/12/2025",
            text_color="#6b7280",
            justify="left"
        ).pack(anchor="w", pady=(4, 0))

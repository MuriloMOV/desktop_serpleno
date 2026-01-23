import customtkinter as ctk

class AnaliseTriagemFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#F3F4F6") # tailwind gray-100
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)

        # 1. Cabeçalho
        self.criar_cabecalho()

        # 2. Key Metrics Cards
        self.criar_cards_metricas()

        # 3. Filtros
        self.criar_filtros()

        # 4. Tabs e Lista
        self.criar_area_conteudo()

    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # Título
        ctk.CTkLabel(
            header,
            text="Análise de Triagem",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#1F2937"
        ).pack(side="left")

        # Botão Nova Triagem
        ctk.CTkButton(
            header,
            text="+ Nova Triagem",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#3B82F6", # blue-500
            hover_color="#2563EB", # blue-600
            text_color="white",
            height=40,
            corner_radius=8,
            command=self.abrir_nova_triagem
        ).pack(side="right")

    def criar_cards_metricas(self):
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # 4 colunas
        for i in range(4):
            cards_container.grid_columnconfigure(i, weight=1)

        # Cards Data
        metrics = [
            {"label": "Total", "value": "12", "icon": "📋", "color": "#3B82F6"},
            {"label": "Pendentes", "value": "4", "icon": "⏳", "color": "#F59E0B"},
            {"label": "Concluídas", "value": "7", "icon": "✅", "color": "#10B981"},
            {"label": "Alta Prioridade", "value": "1", "icon": "⚠️", "color": "#EF4444"}
        ]

        for i, m in enumerate(metrics):
            self.criar_card_metrica(cards_container, i, m)

    def criar_card_metrica(self, parent, idx, metric):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        card.grid(row=0, column=idx, sticky="ew", padx=5)
        
        # Layout interno
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", padx=15, pady=15)

        # Icone a direita
        icon_f = ctk.CTkFrame(content, fg_color="transparent")
        icon_f.pack(side="right", anchor="n")
        ctk.CTkLabel(icon_f, text=metric["icon"], font=ctk.CTkFont(size=24)).pack()

        # Texto a esquerda
        text_f = ctk.CTkFrame(content, fg_color="transparent")
        text_f.pack(side="left", anchor="n", fill="both", expand=True)

        ctk.CTkLabel(
            text_f,
            text=metric["label"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#6B7280"
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_f,
            text=metric["value"],
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=metric["color"]
        ).pack(anchor="w")

    def criar_filtros(self):
        filtro_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        filtro_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        # 4 colunas para inputs + 1 para botões
        filtro_frame.columnconfigure((0,1,2,3), weight=1)
        
        # Inputs
        self.criar_input_filtro(filtro_frame, 0, "Status", ["Todos", "Pendente", "Em Andamento", "Concluída", "Cancelada"])
        self.criar_input_filtro(filtro_frame, 1, "Prioridade", ["Todas", "Baixa", "Média", "Alta", "Urgente"])
        
        # Datas (Stub inputs text)
        self.criar_date_input(filtro_frame, 2, "Data Inicial")
        self.criar_date_input(filtro_frame, 3, "Data Final")

        # Botões
        btn_frame = ctk.CTkFrame(filtro_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=4, sticky="e", padx=20, pady=(0, 20))

        ctk.CTkButton(
            btn_frame, text="Limpar", fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", width=100
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame, text="Aplicar Filtros", fg_color="#3B82F6", text_color="white", hover_color="#2563EB", width=120
        ).pack(side="right", padx=5)

    def criar_input_filtro(self, parent, col, label, options):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=15, pady=15)
        
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151").pack(anchor="w", pady=(0, 5))
        ctk.CTkOptionMenu(f, values=options, fg_color="#F3F4F6", button_color="#E5E7EB", button_hover_color="#D1D5DB", text_color="#111827", dropdown_fg_color="white").pack(fill="x")

    def criar_date_input(self, parent, col, label):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=15, pady=15)
        
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151").pack(anchor="w", pady=(0, 5))
        ctk.CTkEntry(f, placeholder_text="dd/mm/aaaa", fg_color="#F3F4F6", border_color="#E5E7EB", text_color="#111827").pack(fill="x")

    def criar_area_conteudo(self):
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        container.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)

        # Tabs (Navegação)
        tabs_nav = ctk.CTkFrame(container, fg_color="transparent")
        tabs_nav.pack(fill="x", padx=20, pady=20)
        
        # Mock Tabs logic
        self.tab_buttons = []
        for t in ["Pendentes", "Concluídas", "Todas"]:
            btn = ctk.CTkButton(
                tabs_nav, 
                text=t, 
                fg_color="transparent", 
                text_color="#6B7280", 
                hover_color="#F3F4F6", 
                corner_radius=20, 
                height=32,
                command=lambda x=t: self.mudar_tab(x)
            )
            btn.pack(side="left", padx=2)
            self.tab_buttons.append(btn)
        
        # Lista
        self.lista_triagens = ctk.CTkFrame(container, fg_color="transparent")
        self.lista_triagens.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Set Active Tab Style (initially first)
        self.mudar_tab("Pendentes")

    def mudar_tab(self, active_name):
        # Update styles
        for btn in self.tab_buttons:
            if btn.cget("text") == active_name:
                btn.configure(fg_color="#DBEAFE", text_color="#2563EB") # active blue
            else:
                btn.configure(fg_color="transparent", text_color="#6B7280")
        
        self.renderizar_lista(active_name)

    def renderizar_lista(self, tab_filtro):
        for w in self.lista_triagens.winfo_children(): w.destroy()

        # Mock Data List
        data = [
            {"student": "Bruno Henrique", "date": "23/01/2026", "priority": "Alta", "status": "Pendentes"},
            {"student": "Diego Martins", "date": "22/01/2026", "priority": "Média", "status": "Pendentes"},
            {"student": "Carla Diaz", "date": "20/01/2026", "priority": "Baixa", "status": "Concluídas"},
            {"student": "Ana Beatriz", "date": "19/01/2026", "priority": "Urgente", "status": "Pendentes"},
        ]

        filtered = [d for d in data if tab_filtro == "Todas" or d["status"] == tab_filtro]

        if not filtered:
            ctk.CTkLabel(self.lista_triagens, text="Nenhum item encontrado.", text_color="#9CA3AF").pack(pady=20)
            return

        # Header da Tabela
        header = ctk.CTkFrame(self.lista_triagens, fg_color="#F9FAFB", height=40)
        header.pack(fill="x", pady=(0, 5))
        
        cols = ["Estudante", "Data", "Prioridade", "Status", "Ações"]
        weights = [2, 1, 1, 1, 1]
        
        for i, c in enumerate(cols):
            f = ctk.CTkFrame(header, fg_color="transparent")
            f.pack(side="left", fill="x", expand=True, padx=5)
            # Simulating weights broadly
            ctk.CTkLabel(f, text=c, font=ctk.CTkFont(weight="bold", size=12), text_color="#374151").pack(anchor="w")

        # Rows
        for item in filtered:
            row = ctk.CTkFrame(self.lista_triagens, fg_color="white", border_width=0, border_color="#E5E7EB") # bottom border simulation hard in frames
            row.pack(fill="x", pady=2)
            
            # Helper to create col
            self.create_list_col(row, item["student"], weight=2, bold=True)
            self.create_list_col(row, item["date"], weight=1)
            self.create_list_col(row, item["priority"], weight=1, color=self.get_priority_color(item["priority"]))
            self.create_list_col(row, item["status"], weight=1, color="#4B5563")
            
            # Actions
            act_f = ctk.CTkFrame(row, fg_color="transparent")
            act_f.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkButton(act_f, text="👁️", width=30, fg_color="#eff6ff", text_color="#2563EB", hover_color="#dbeafe").pack(side="left")

    def create_list_col(self, parent, text, weight=1, bold=False, color="#1F2937"):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", fill="x", expand=True, padx=5)
        font = ctk.CTkFont(family="Segoe UI", size=13, weight="bold" if bold else "normal")
        ctk.CTkLabel(f, text=text, font=font, text_color=color).pack(anchor="w")

    def get_priority_color(self, p):
        if p == "Alta": return "#EF4444"
        if p == "Urgente": return "#B91C1C"
        if p == "Média": return "#F59E0B"
        return "#10B981" # Baixa/Verde

    def abrir_nova_triagem(self):
        print("Modal Nova Triagem")

import customtkinter as ctk

class AnaliseTriagemFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#F3F4F6")
        self.controller = controller
        
        # Dados mestre (Para não repetir o código toda hora)
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
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        ctk.CTkLabel(header, text="Análise de Triagem", font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color="#1F2937").pack(side="left")
        ctk.CTkButton(header, text="+ Nova Triagem", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), fg_color="#3B82F6", hover_color="#2563EB", height=40, corner_radius=8, command=self.abrir_nova_triagem).pack(side="right")

    def criar_cards_metricas(self):
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        for i in range(4): cards_container.grid_columnconfigure(i, weight=1)

        metrics = [
            {"label": "Total", "value": str(len(self.data_master)), "icon": "📋", "color": "#3B82F6"},
            {"label": "Pendentes", "value": "3", "icon": "⏳", "color": "#F59E0B"},
            {"label": "Concluídas", "value": "1", "icon": "✅", "color": "#10B981"},
            {"label": "Alta Prioridade", "value": "2", "icon": "⚠️", "color": "#EF4444"}
        ]
        for i, m in enumerate(metrics): self.criar_card_metrica(cards_container, i, m)

    def criar_card_metrica(self, parent, idx, metric):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        card.grid(row=0, column=idx, sticky="ew", padx=5)
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", padx=15, pady=15)
        ctk.CTkLabel(ctk.CTkFrame(content, fg_color="transparent"), text=metric["icon"], font=ctk.CTkFont(size=24)).pack(side="right", anchor="n")
        text_f = ctk.CTkFrame(content, fg_color="transparent")
        text_f.pack(side="left", anchor="n", fill="both", expand=True)
        ctk.CTkLabel(text_f, text=metric["label"], font=ctk.CTkFont(family="Segoe UI", size=13), text_color="#6B7280").pack(anchor="w")
        ctk.CTkLabel(text_f, text=metric["value"], font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"), text_color=metric["color"]).pack(anchor="w")

    def criar_filtros(self):
        filtro_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        filtro_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        filtro_frame.columnconfigure((0,1,2,3), weight=1)
        
        # Atribuindo os menus a variáveis da classe (self.)
        self.filtro_status = self.criar_input_filtro(filtro_frame, 0, "Status", ["Todos", "Pendente", "Em Andamento", "Concluída", "Cancelada"])
        self.filtro_prioridade = self.criar_input_filtro(filtro_frame, 1, "Prioridade", ["Todas", "Baixa", "Média", "Alta", "Urgente"])
        
        self.data_inicial = self.criar_date_input(filtro_frame, 2, "Data Inicial")
        self.data_final = self.criar_date_input(filtro_frame, 3, "Data Final")

        btn_frame = ctk.CTkFrame(filtro_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=4, sticky="e", padx=20, pady=(0, 20))

        ctk.CTkButton(btn_frame, text="Limpar", command=self.limpar_filtros, fg_color="#E5E7EB", text_color="#374151", hover_color="#D1D5DB", width=100).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="Aplicar Filtros", command=self.aplicar_filtros, fg_color="#3B82F6", text_color="white", hover_color="#2563EB", width=120).pack(side="right", padx=5)

    def criar_input_filtro(self, parent, col, label, options):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=15, pady=15)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151").pack(anchor="w", pady=(0, 5))
        menu = ctk.CTkOptionMenu(f, values=options, fg_color="#F3F4F6", button_color="#E5E7EB", button_hover_color="#D1D5DB", text_color="#111827", dropdown_fg_color="white")
        menu.pack(fill="x")
        return menu # Retorna para salvar na variável

    def criar_date_input(self, parent, col, label):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=0, column=col, sticky="ew", padx=15, pady=15)
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151").pack(anchor="w", pady=(0, 5))
        entry = ctk.CTkEntry(f, placeholder_text="dd/mm/aaaa", fg_color="#F3F4F6", border_color="#E5E7EB", text_color="#111827")
        entry.pack(fill="x")
        return entry

    def criar_area_conteudo(self):
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        container.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.lista_triagens = ctk.CTkFrame(container, fg_color="transparent")
        self.lista_triagens.pack(fill="both", expand=True, padx=20, pady=20)
        self.renderizar_tabela(self.data_master) # Começa mostrando tudo

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
        # Limpa a lista atual
        for w in self.lista_triagens.winfo_children(): w.destroy()

        if not data_list:
            ctk.CTkLabel(self.lista_triagens, text="Nenhum item encontrado.", text_color="#9CA3AF").pack(pady=20)
            return

        # Header
        header = ctk.CTkFrame(self.lista_triagens, fg_color="#F9FAFB", height=40)
        header.pack(fill="x", pady=(0, 5))
        for c in ["Estudante", "Data", "Prioridade", "Status", "Ações"]:
            f = ctk.CTkFrame(header, fg_color="transparent")
            f.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkLabel(f, text=c, font=ctk.CTkFont(weight="bold", size=12), text_color="#374151").pack(anchor="w")

        # Rows
        for item in data_list:
            row = ctk.CTkFrame(self.lista_triagens, fg_color="white")
            row.pack(fill="x", pady=2)
            self.create_list_col(row, item["student"], bold=True)
            self.create_list_col(row, item["date"])
            self.create_list_col(row, item["priority"], color=self.get_priority_color(item["priority"]))
            self.create_list_col(row, item["status"], color="#4B5563")
            
            act_f = ctk.CTkFrame(row, fg_color="transparent")
            act_f.pack(side="left", fill="x", expand=True, padx=5)
            ctk.CTkButton(act_f, text="👁️", width=30, fg_color="#eff6ff", text_color="#2563EB", hover_color="#dbeafe").pack(side="left")

    def create_list_col(self, parent, text, bold=False, color="#1F2937"):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", fill="x", expand=True, padx=5)
        font = ctk.CTkFont(family="Segoe UI", size=13, weight="bold" if bold else "normal")
        ctk.CTkLabel(f, text=text, font=font, text_color=color).pack(anchor="w")

    def get_priority_color(self, p):
        colors = {"Alta": "#EF4444", "Urgente": "#B91C1C", "Média": "#F59E0B", "Baixa": "#10B981"}
        return colors.get(p, "#10B981")

    def abrir_nova_triagem(self): print("Modal Nova Triagem")
import customtkinter as ctk

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb") # Cor de fundo cinza claro
        self.controller = controller

        # Layout Principal - Uma coluna flexível
        self.grid_columnconfigure(0, weight=1)

        # Cabeçalho
        self.criar_cabecalho()

        # 1. Linha de Estatísticas (KPIs)
        self.criar_kpis()

        # 2. Linha de Conteúdo (Agenda e Alertas)
        self.criar_conteudo_principal()

        # 3. Linha de Análise (Gráfico Humor + Bem-Estar)
        self.criar_analise_bem_estar()

        # 4. Linha de Risco
        self.criar_visao_risco()

    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        titulo = ctk.CTkLabel(
            header, 
            text="Dashboard Central", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#1f2937"
        )
        titulo.pack(side="left")

    def criar_kpis(self):
        # Container horizontal para os cards
        kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        kpi_container.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Grid para distribuir 5 cards uniformente
        for i in range(5):
            kpi_container.grid_columnconfigure(i, weight=1)

        # Dados Mockados
        kpis = [
            {"titulo": "Atendimentos do Dia", "valor": "0", "icone": "👥", "cor_icone": "#3b82f6"}, # Blue
            {"titulo": "Vagas Disponíveis", "valor": "0", "icone": "📅", "cor_icone": "#22c55e"}, # Green
            {"titulo": "Alertas Ativos", "valor": "0", "icone": "🔔", "cor_icone": "#ef4444"},   # Red
            {"titulo": "Total de Estudantes", "valor": "6", "icone": "🎓", "cor_icone": "#a855f7"}, # Purple
            {"titulo": "Humor Médio (Hoje)", "valor": "😊", "icone": "🙂", "cor_icone": "#eab308"}  # Yellow
        ]

        for i, kpi in enumerate(kpis):
            self.criar_card_kpi(kpi_container, i, kpi)

    def criar_card_kpi(self, parent, col_idx, dados):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=10)
        card.grid(row=0, column=col_idx, sticky="ew", padx=5, pady=5)
        
        # Ícone
        icon_frame = ctk.CTkFrame(card, fg_color="transparent", width=40)
        icon_frame.pack(side="right", padx=15, pady=15)
        
        ctk.CTkLabel(
            icon_frame, 
            text=dados["icone"], 
            font=ctk.CTkFont(size=24),
            text_color=dados["cor_icone"]
        ).pack()

        # Conteúdo
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", padx=15, pady=15, fill="both", expand=True)

        ctk.CTkLabel(
            content_frame,
            text=dados["titulo"],
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#6b7280", # gray-500
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            content_frame,
            text=dados["valor"],
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#111827", # gray-900
            anchor="w"
        ).pack(anchor="w")

    def criar_conteudo_principal(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        container.grid_columnconfigure(0, weight=3) # Agenda maior? Ou igual? No HTML diz appointment e alerts lado a lado. Vamos por igual ou 3:2
        container.grid_columnconfigure(1, weight=2)

        # ========= Esquerda: Próximos Atendimentos =========
        agenda_card = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        agenda_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Header Agenda
        ag_header = ctk.CTkFrame(agenda_card, fg_color="transparent")
        ag_header.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(ag_header, text="Próximos Atendimentos", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#1f2937").pack(side="left")
        ctk.CTkButton(ag_header, text="Ver agenda completa →", fg_color="transparent", text_color="#2563EB", font=ctk.CTkFont(size=12), hover=False, width=50, command=lambda: self.controller.mostrar_agenda()).pack(side="right") # Link style

        # Lista (Empty State Mock)
        ag_content = ctk.CTkFrame(agenda_card, fg_color="transparent")
        ag_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(ag_content, text="📅", font=ctk.CTkFont(size=32), text_color="#9ca3af").pack(pady=(10,5))
        ctk.CTkLabel(ag_content, text="Nenhum agendamento para hoje", text_color="#6b7280").pack()
        ctk.CTkButton(ag_content, text="+ Criar agendamento", fg_color="#2563eb", text_color="white", corner_radius=6, height=30).pack(pady=15)


        # ========= Direita: Estudantes em Alerta =========
        alert_card = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        alert_card.grid(row=0, column=1, sticky="nsew", padx=(0, 0))

        # Header Alert
        al_header = ctk.CTkFrame(alert_card, fg_color="transparent")
        al_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(al_header, text="Estudantes em Alerta", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#1f2937").pack(side="left")
        
        # Badge Mock
        # badge = ctk.CTkLabel(al_header, text=" 2 ", fg_color="#ef4444", text_color="white", corner_radius=10, height=20)
        # badge.pack(side="left", padx=10)

        # Lista de Alertas (Mock)
        al_content = ctk.CTkFrame(alert_card, fg_color="transparent")
        al_content.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        # Item de Alerta 1
        self.criar_item_alerta(al_content, "Bruno H. Souza", "Ansiedade alta recorrente", "Engenharia de Software")
        self.criar_item_alerta(al_content, "Mariana Costa", "Faltas consecutivas", "Gestão Empresarial")

    def criar_item_alerta(self, parent, nome, motivo, curso):
        item = ctk.CTkFrame(parent, fg_color="#fef2f2", corner_radius=8, border_width=1, border_color="#fee2e2") # red-50
        item.pack(fill="x", pady=5)
        
        ctk.CTkLabel(item, text=nome, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#991b1b").pack(anchor="w", padx=10, pady=(10, 0))
        
        msg_frame = ctk.CTkFrame(item, fg_color="transparent")
        msg_frame.pack(fill="x", padx=10, pady=(2, 0))
        ctk.CTkLabel(msg_frame, text="⚠️ " + motivo, font=ctk.CTkFont(size=12), text_color="#b91c1c").pack(anchor="w")
        
        ctk.CTkLabel(item, text=curso, font=ctk.CTkFont(size=11), text_color="#7f1d1d").pack(anchor="w", padx=10, pady=(2, 10))

    def criar_analise_bem_estar(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)

        # === Gráfico de Humor (Esquerda) ===
        chart_card = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        c_header = ctk.CTkFrame(chart_card, fg_color="transparent")
        c_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(c_header, text="📈 Humor dos Estudantes (30 dias)", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#1f2937").pack(side="left")

        # Mock do Gráfico (Area cinza)
        chart_area = ctk.CTkFrame(chart_card, fg_color="#f9fafb", corner_radius=10)
        chart_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        ctk.CTkLabel(chart_area, text="(Visualização do Gráfico)", text_color="#9ca3af").pack(expand=True, pady=60)

        # === Indicadores de Bem-Estar (Direita) ===
        well_card = ctk.CTkFrame(container, fg_color="white", corner_radius=10)
        well_card.grid(row=0, column=1, sticky="nsew", padx=(0, 0))

        w_header = ctk.CTkFrame(well_card, fg_color="transparent")
        w_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(w_header, text="Bem-Estar por Dimensão", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#1f2937").pack(side="left")

        w_content = ctk.CTkFrame(well_card, fg_color="transparent")
        w_content.pack(fill="both", expand=True, padx=20, pady=10)

        self.criar_barra_progresso(w_content, "Acadêmico", 0.75, "#3b82f6") # Blue
        self.criar_barra_progresso(w_content, "Emocional", 0.45, "#f43f5e") # Rose/Red
        self.criar_barra_progresso(w_content, "Social", 0.60, "#8b5cf6")    # Violet

    def criar_barra_progresso(self, parent, label, valor, cor):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=8)

        # Label e Valor
        lbl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_frame.pack(fill="x")
        ctk.CTkLabel(lbl_frame, text=label, font=ctk.CTkFont(size=13, weight="bold"), text_color="#374151").pack(side="left")
        ctk.CTkLabel(lbl_frame, text=f"{int(valor*100)}%", font=ctk.CTkFont(size=13, weight="bold"), text_color="#374151").pack(side="right")

        # Barra
        progress = ctk.CTkProgressBar(frame, height=10, corner_radius=5)
        progress.pack(fill="x", pady=(5,0))
        progress.set(valor)
        progress.configure(progress_color=cor)

    def criar_visao_risco(self):
        # Container grande
        risk_container = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        risk_container.grid(row=4, column=0, sticky="ew", padx=20, pady=10)

        # Header
        r_header = ctk.CTkFrame(risk_container, fg_color="transparent")
        r_header.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(r_header, text="🛡️ Visão de Risco dos Estudantes", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color="#1f2937").pack(side="left")

        # Grid Interno para os 4 cards de risco
        grid_risk = ctk.CTkFrame(risk_container, fg_color="transparent")
        grid_risk.pack(fill="x", padx=20, pady=(0, 20))
        for i in range(4):
            grid_risk.grid_columnconfigure(i, weight=1)

        # Crítico, Alto, Médio, Normal
        self.criar_card_risco(grid_risk, 0, "Crítico", "0", "#ef4444") # Red
        self.criar_card_risco(grid_risk, 1, "Alto", "0", "#f97316")    # Orange
        self.criar_card_risco(grid_risk, 2, "Médio", "1", "#eab308")   # Yellow
        self.criar_card_risco(grid_risk, 3, "Normal", "5", "#22c55e")  # Green

    def criar_card_risco(self, parent, col, nivel, count, cor):
        card = ctk.CTkFrame(parent, fg_color="#f9fafb", corner_radius=8, border_width=1, border_color="#e5e7eb")
        card.grid(row=0, column=col, sticky="ew", padx=5)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=10)

        # Bolinha de cor
        dot = ctk.CTkLabel(header, text="●", font=ctk.CTkFont(size=16), text_color=cor)
        dot.pack(side="left")

        ctk.CTkLabel(header, text=nivel, font=ctk.CTkFont(weight="bold"), text_color="#374151").pack(side="left", padx=5)
        ctk.CTkLabel(header, text=count, font=ctk.CTkFont(weight="bold"), text_color="#111827").pack(side="right")

        # Lista vazia mock
        lista = ctk.CTkFrame(card, fg_color="transparent")
        lista.pack(fill="x", padx=10, pady=(0, 10))
        if count == "0":
            ctk.CTkLabel(lista, text="Nenhum estudante", font=ctk.CTkFont(size=11), text_color="#9ca3af").pack(anchor="w")
        else:
            ctk.CTkLabel(lista, text="Ver lista...", font=ctk.CTkFont(size=11), text_color="#6b7280").pack(anchor="w")

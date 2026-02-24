import customtkinter as ctk
from ui_theme import THEME, SPACING, RADIUS, font
from tkcalendar import DateEntry

class RelatorioFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.THEME = THEME  # Necessário para o controller configurar o gráfico
        
        self.card_widgets = {}
        self.summary_labels = {} # Para atualizar o resumo lateral dinamicamente

        self._configurar_grid()
        self.criar_layout()
        
        # Conexão com o Controller
        self.controller.set_view(self)
        self.controller.inicializar_dashboard()

    def _configurar_grid(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=0) # Cards
        self.grid_rowconfigure(2, weight=1) # Gráfico/Resumo (Expansível)
        self.grid_rowconfigure(3, weight=2) # Lista de Relatórios (Mais espaço)
        self.grid_rowconfigure(4, weight=0) # Exportação

    def criar_layout(self):
        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 14))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        lbl_box = ctk.CTkFrame(inner, fg_color="transparent")
        lbl_box.pack(side="left")
        ctk.CTkLabel(lbl_box, text="Relatórios", font=font(20, "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(lbl_box, text="Visão gerencial e indicadores", font=font(12), text_color=THEME["text_muted"]).pack(anchor="w")

        ctk.CTkButton(
            inner, text="+ Novo Relatório", fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"], font=font(12, "bold"),
            height=36, corner_radius=RADIUS["button"],
            command=self.controller.gerar_novo_relatorio
        ).pack(side="right")

        # --- CONTEÚDO ---
        self._criar_cards()
        self._criar_dashboard_area() # Contém Gráfico + Resumo
        self._criar_lista_relatorios()
        self._criar_secao_exportacao()

    def _criar_cards(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="ew", padx=SPACING["page_x"], pady=(0, 20))
        for i in range(4): container.grid_columnconfigure(i, weight=1)

        configs = [
            ("Relatório Geral", "Geral", "#D0E1FD"),
            ("Agendamentos", "Consultas", "#D1FADF"),
            ("Intervenções", "Ações", "#EBE9FE"),
            ("Triagens", "Triagens", "#FEF0C7")
        ]

        for i, (titulo, cat, cor) in enumerate(configs):
            card = self.render_card(container, titulo, cat, cor)
            card.grid(row=0, column=i, padx=8, sticky="ew")

    def render_card(self, parent, titulo, categoria, cor_icone):
        frame = ctk.CTkFrame(parent, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"], height=90)
        frame.pack_propagate(False)
        
        icon_box = ctk.CTkFrame(frame, width=42, height=42, fg_color=cor_icone, corner_radius=8)
        icon_box.place(x=15, y=24)
        
        ctk.CTkLabel(frame, text=titulo, font=font(11), text_color=THEME["text_muted"]).place(x=70, y=20)
        val_lbl = ctk.CTkLabel(frame, text="--", font=font(22, "bold"), text_color=THEME["text"])
        val_lbl.place(x=70, y=40)
        
        self.card_widgets[titulo] = val_lbl
        return frame

    def _criar_dashboard_area(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, 20))
        container.grid_columnconfigure(0, weight=3) # Gráfico maior
        container.grid_columnconfigure(1, weight=1) # Resumo menor

        # Box do Gráfico (O Controller injetará o canvas aqui)
        self.chart_box = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        self.chart_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(self.chart_box, text="Atividades Nos Últimos 30 dias", font=font(14, "bold")).pack(anchor="nw", padx=20, pady=15)

        # Box de Resumo
        summary_box = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        summary_box.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(summary_box, text="Resumo Mensal", font=font(14, "bold")).pack(anchor="nw", padx=20, pady=15)

        self.summary_labels["Total Estudantes"] = self._add_item_resumo(summary_box, "Total Estudantes", "0")
        self.summary_labels["Consultas"] = self._add_item_resumo(summary_box, "Consultas (30d)", "0")
        self.summary_labels["Intervenções"] = self._add_item_resumo(summary_box, "Intervenções (30d)", "0")
        
        ctk.CTkFrame(summary_box, fg_color=THEME["border"], height=1).pack(fill="x", padx=20, pady=10)
        self.summary_labels["Taxa"] = self._add_item_resumo(summary_box, "Taxa Comparecimento", "0%", THEME["success"])

    def _add_item_resumo(self, parent, texto, valor, cor_valor=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(f, text=texto, text_color=THEME["text_muted"], font=font(12)).pack(side="left")
        lbl = ctk.CTkLabel(f, text=valor, text_color=cor_valor or THEME["text"], font=font(12, "bold"))
        lbl.pack(side="right")
        return lbl

    def _criar_lista_relatorios(self):
        container_lista = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        container_lista.grid(row=3, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(10, 24))
        
        filter_bar = ctk.CTkFrame(container_lista, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=15)

        # 1. Dropdown de Tipos (Em vez de busca por texto)
        ctk.CTkLabel(filter_bar, text="Tipo:", font=font(12, "bold")).pack(side="left", padx=(0, 5))
        self.filtro_tipo = ctk.CTkOptionMenu(
            filter_bar,
            values=["Todos", "Geral", "Estudante", "Agendamentos", "Intervenções", "Triagens"],
            width=140, height=32,
            fg_color=THEME["bg_alt"], text_color=THEME["text"],
            button_color=THEME["border"], button_hover_color=THEME["primary_light"]
        )
        self.filtro_tipo.pack(side="left", padx=(0, 20))

        # 2. Seleção de Datas com Botões/Calendário
        ctk.CTkLabel(filter_bar, text="Período:", font=font(12, "bold")).pack(side="left", padx=(0, 5))
        
        # Botões que abrem o seletor
        self.btn_data_ini = ctk.CTkButton(filter_bar, text="Data Início", width=100, height=32, 
                                          fg_color=THEME["bg_alt"], text_color=THEME["text"],
                                          command=lambda: self.abrir_calendario("inicio"))
        self.btn_data_ini.pack(side="left", padx=5)

        ctk.CTkLabel(filter_bar, text="até").pack(side="left", padx=2)

        self.btn_data_fim = ctk.CTkButton(filter_bar, text="Data Fim", width=100, height=32, 
                                          fg_color=THEME["bg_alt"], text_color=THEME["text"],
                                          command=lambda: self.abrir_calendario("fim"))
        self.btn_data_fim.pack(side="left", padx=5)

        # Botões de Ação
        ctk.CTkButton(filter_bar, text="Filtrar", width=90, height=32, 
                      command=self.controller.aplicar_filtros).pack(side="left", padx=(20, 10))
        
        ctk.CTkButton(filter_bar, text="Limpar", width=80, height=32, fg_color="transparent", 
                      border_width=1, text_color=THEME["text"],
                      command=self.controller.limpar_filtros).pack(side="left")

        self.reports_container = ctk.CTkScrollableFrame(container_lista, fg_color="transparent")
        self.reports_container.pack(expand=True, fill="both", padx=5, pady=5)

    def abrir_calendario(self, alvo):
        """Abre o calendário exatamente sob o botão clicado"""
        # Identifica qual botão foi clicado para pegar a posição
        botao = self.btn_data_ini if alvo == "inicio" else self.btn_data_fim
        
        # Calcula a posição do botão na tela
        # winfo_rootx/y pega a posição absoluta na tela
        x = botao.winfo_rootx()
        y = botao.winfo_rooty() + botao.winfo_height() + 5 # 5px de margem abaixo

        # Cria a janela flutuante
        janela_cal = ctk.CTkToplevel(self)
        janela_cal.withdraw() # Esconde a janela enquanto configura para evitar "pulo" visual
        janela_cal.title("")
        janela_cal.overrideredirect(True) # Remove a barra de título (estilo popup)
        janela_cal.attributes("-topmost", True)
        janela_cal.configure(fg_color=THEME["card"])
        
        # Define a posição calculada
        janela_cal.geometry(f"250x280+{x}+{y}")

        # Frame de borda para parecer um menu
        frame_borda = ctk.CTkFrame(janela_cal, fg_color=THEME["card"], 
                                   border_width=2, border_color=THEME["primary"])
        frame_borda.pack(fill="both", expand=True)

        from tkcalendar import Calendar
        cal = Calendar(frame_borda, selectmode='day', locale='pt_BR', 
                       date_pattern='dd/mm/yyyy', 
                       background=THEME["primary"], 
                       foreground='white', 
                       headersbackground=THEME["bg_alt"])
        cal.pack(pady=10, padx=10, fill="both", expand=True)

        def confirmar_data():
            data_selecionada = cal.get_date()
            if alvo == "inicio":
                self.btn_data_ini.configure(text=data_selecionada, fg_color=THEME["primary"], text_color="white")
            else:
                self.btn_data_fim.configure(text=data_selecionada, fg_color=THEME["primary"], text_color="white")
            janela_cal.destroy()

        # Botão para fechar sem selecionar
        btn_container = ctk.CTkFrame(frame_borda, fg_color="transparent")
        btn_container.pack(fill="x", pady=5)
        
        ctk.CTkButton(btn_container, text="Cancelar", width=80, fg_color="gray", 
                      command=janela_cal.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_container, text="Selecionar", width=120, 
                      command=confirmar_data).pack(side="right", padx=10)

        janela_cal.deiconify() # Mostra a janela já posicionada
        
        # Fecha a janela se o usuário clicar fora dela (opcional)
        janela_cal.bind("<FocusOut>", lambda e: janela_cal.destroy())

    def _criar_secao_exportacao(self):
        export_frame = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        export_frame.grid(row=4, column=0, sticky="ew", padx=SPACING["page_x"], pady=(0, 20))
        
        inner = ctk.CTkFrame(export_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(inner, text="📥 Exportar Dados:", font=font(12, "bold")).pack(side="left", padx=(0, 15))
        
        for label, tipo in [("Estudantes", "estudantes"), ("Agenda ", "agenda"), ("Triagens", "triagens")]:
            ctk.CTkButton(inner, text=label, width=90, height=28, fg_color=THEME["bg_alt"], 
                          text_color=THEME["text"], command=lambda t=tipo: self.controller.exportar(t)).pack(side="left", padx=5)

    # --- MÉTODOS CHAMADOS PELO CONTROLLER ---

    def update_view(self, stats_res, reports_res):
        """Atualiza todos os dados da tela"""
        if stats_res.get('success'):
            data = stats_res.get('data', {}).get('summary', {})
            # Atualiza Cards
            self.card_widgets["Relatório Geral"].configure(text=data.get('students_total', '0'))
            self.card_widgets["Agendamentos"].configure(text=data.get('appointments_total', '0'))
            self.card_widgets["Intervenções"].configure(text=data.get('interventions_total', '0'))
            self.card_widgets["Triagens"].configure(text=data.get('screenings_total', '0'))
            # Atualiza Resumo Lateral
            self.summary_labels["Total Estudantes"].configure(text=data.get('students_total', '0'))
            self.summary_labels["Consultas"].configure(text=data.get('appointments_total', '0'))

        if reports_res.get('success'):
            items = reports_res.get('data', {}).get('reports', [])
            for w in self.reports_container.winfo_children(): w.destroy()
            
            for r in items:
                row = ctk.CTkFrame(self.reports_container, fg_color=THEME["bg_alt"], height=40)
                row.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(row, text=f"📄 {r.get('name', 'Relatório')}", font=font(12)).pack(side="left", padx=15)
                ctk.CTkLabel(row, text=r.get('type', 'Geral'), font=font(11), text_color=THEME["text_muted"]).pack(side="right", padx=15)


    def criar_secao_inferior(self):
        container_inferior = ctk.CTkFrame(self, fg_color="transparent")
        container_inferior.grid(row=2, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, 20))
        
        # Gráfico (weight 3) ocupa mais espaço que o Resumo (weight 1)
        container_inferior.grid_columnconfigure(0, weight=3)
        container_inferior.grid_columnconfigure(1, weight=1)
        container_inferior.grid_rowconfigure(0, weight=1)

        chart_box = ctk.CTkFrame(container_inferior, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        chart_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        summary_box = ctk.CTkFrame(container_inferior, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        summary_box.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(
            chart_box, text="Atividades Nos Últimos 30 dias", 
            font=font(14, "bold")
        ).pack(anchor="nw", padx=20, pady=15)
        
        ctk.CTkLabel(
            summary_box, text="Resumo", 
            font=font(16, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="nw", padx=25, pady=(20, 10))

        itens = [
            ("Total de Estudantes", "300"),
            ("Consultas (30d)", "15"),
            ("Intervenções (30d)", "9"),
            ("Triagens (30d)", "7"),
        ]

        for texto, valor in itens:
            self.item_resumo(summary_box, texto, valor)

        divisor = ctk.CTkFrame(summary_box, fg_color=THEME["border"], height=1)
        divisor.pack(fill="x", padx=25, pady=15)

        self.item_resumo(summary_box, "Taxa de Comparecimento", "85%", cor_valor=THEME["success"])

    def item_resumo(self, parent, texto, valor, cor_valor=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=4)
        ctk.CTkLabel(f, text=texto, text_color=THEME["text_muted"], font=font(13)).pack(side="left")
        ctk.CTkLabel(f, text=valor, text_color=cor_valor or THEME["text"], font=font(13, "bold")).pack(side="right")
        
    def criar_lista_relatorios(self):
        # sticky="nsew" faz o box preencher toda a Row 3
        container_lista = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        container_lista.grid(row=3, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(10, 24))
        
        header_lista = ctk.CTkFrame(container_lista, fg_color="transparent")
        header_lista.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            header_lista, text="Relatórios Gerados", 
            font=font(16, "bold"), text_color=THEME["text"]
        ).pack(side="left")

        # Filtro de tipo
        self.filtro_tipo = ctk.CTkOptionMenu(
            header_lista,
            values=["Todos os tipos", "Geral", "Estudante", "Agendamentos", "Intervenções", "Triagens", "Estatísticas"],
            fg_color=THEME["card"],
            button_color=THEME["card"],
            button_hover_color=THEME["bg_alt"],
            text_color=THEME["text_muted"],
            dropdown_fg_color=THEME["card"],
            dropdown_text_color=THEME["text"],
            corner_radius=RADIUS["button"],
            height=32,
            font=font(12, "bold")
        )
        self.filtro_tipo.pack(side="right", padx=5)

        ctk.CTkFrame(container_lista, fg_color=THEME["border"], height=1).pack(fill="x")

        # Container para a lista de relatórios (Preenche o restante do espaço)
        self.reports_container = ctk.CTkScrollableFrame(container_lista, fg_color="transparent")
        self.reports_container.pack(expand=True, fill="both")
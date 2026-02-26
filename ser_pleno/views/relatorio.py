import customtkinter as ctk
from ui_theme import THEME, SPACING, RADIUS, font

class RelatorioFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.THEME = THEME  
        
        # Dicionários para acesso rápido aos widgets dinâmicos
        self.card_widgets = {}
        self.summary_labels = {} 

        self._configurar_grid()
        self.criar_layout()
        
        # Injeção de dependência e inicialização
        self.controller.set_view(self)
        self.controller.inicializar_dashboard()

    def _configurar_grid(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Header
        self.grid_rowconfigure(1, weight=0) # Cards
        self.grid_rowconfigure(2, weight=1) # Gráfico/Resumo
        self.grid_rowconfigure(3, weight=2) # Lista de Relatórios
        self.grid_rowconfigure(4, weight=0) # Exportação

    def criar_layout(self):
        """Orquestra a criação das seções da interface"""
        self._criar_header()
        self._criar_cards()
        self._criar_dashboard_area()
        self._criar_lista_relatorios_section()
        self._criar_secao_exportacao()

    def _criar_header(self):
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

    def _criar_cards(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="ew", padx=SPACING["page_x"], pady=(0, 20))
        
        # Configuração dos cards (Pode vir de um arquivo de config ou banco futuramente)
        card_configs = [
            {"key": "total", "label": "Relatório Geral", "color": "#D0E1FD"},
            {"key": "appointments", "label": "Agendamentos", "color": "#D1FADF"},
            {"key": "interventions", "label": "Intervenções", "color": "#EBE9FE"},
            {"key": "screenings", "label": "Triagens", "color": "#FEF0C7"}
        ]

        for i, conf in enumerate(card_configs):
            container.grid_columnconfigure(i, weight=1)
            card = self._render_card_item(container, conf["label"], conf["color"], conf["key"])
            card.grid(row=0, column=i, padx=8, sticky="ew")

    def _render_card_item(self, parent, titulo, cor_icone, key):
        frame = ctk.CTkFrame(parent, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"], height=90)
        frame.pack_propagate(False)
        
        icon_box = ctk.CTkFrame(frame, width=42, height=42, fg_color=cor_icone, corner_radius=8)
        icon_box.place(x=15, y=24)
        
        ctk.CTkLabel(frame, text=titulo, font=font(11), text_color=THEME["text_muted"]).place(x=70, y=20)
        val_lbl = ctk.CTkLabel(frame, text="--", font=font(22, "bold"), text_color=THEME["text"])
        val_lbl.place(x=70, y=40)
        
        self.card_widgets[key] = val_lbl # Mapeia o widget pela chave do banco
        return frame

    def _criar_dashboard_area(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, 20))
        container.grid_columnconfigure(0, weight=3)
        container.grid_columnconfigure(1, weight=1)

        # Container do Gráfico
        self.chart_box = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        self.chart_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(self.chart_box, text="Atividades Recentes", font=font(14, "bold")).pack(anchor="nw", padx=20, pady=15)

        # Container de Resumo
        summary_box = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        summary_box.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(summary_box, text="Resumo Mensal", font=font(14, "bold")).pack(anchor="nw", padx=20, pady=15)

        # Itens de resumo dinâmicos
        self.summary_labels["students"] = self._add_row_resumo(summary_box, "Total Estudantes", "0")
        self.summary_labels["appointments"] = self._add_row_resumo(summary_box, "Consultas (30d)", "0")
        self.summary_labels["interventions"] = self._add_row_resumo(summary_box, "Intervenções (30d)", "0")
        
        ctk.CTkFrame(summary_box, fg_color=THEME["border"], height=1).pack(fill="x", padx=20, pady=10)
        self.summary_labels["rate"] = self._add_row_resumo(summary_box, "Taxa Comparecimento", "0%", THEME["success"])

    def _add_row_resumo(self, parent, texto, valor, cor_valor=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(f, text=texto, text_color=THEME["text_muted"], font=font(12)).pack(side="left")
        lbl = ctk.CTkLabel(f, text=valor, text_color=cor_valor or THEME["text"], font=font(12, "bold"))
        lbl.pack(side="right")
        return lbl

    def _criar_lista_relatorios_section(self):
        container = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        container.grid(row=3, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(10, 24))
        
        filter_bar = ctk.CTkFrame(container, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=15)

        # Filtros
        ctk.CTkLabel(filter_bar, text="Tipo:", font=font(12, "bold")).pack(side="left", padx=(0, 5))
        self.filtro_tipo = ctk.CTkOptionMenu(
            filter_bar, values=["Todos", "Geral", "Estudante", "Agendamentos", "Intervenções"],
            fg_color=THEME["bg_alt"], text_color=THEME["text"], button_color=THEME["border"], width=140
        )
        self.filtro_tipo.pack(side="left", padx=(0, 20))

        ctk.CTkButton(filter_bar, text="Filtrar", width=90, command=self.controller.aplicar_filtros).pack(side="left", padx=5)
        
        # Scrollable Area
        self.reports_container = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.reports_container.pack(expand=True, fill="both", padx=5, pady=5)

    def _criar_secao_exportacao(self):
        export_frame = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        export_frame.grid(row=4, column=0, sticky="ew", padx=SPACING["page_x"], pady=(0, 20))
        
        btn = ctk.CTkButton(
            export_frame, text="📥 Exportar Dados", font=font(12, "bold"),
            fg_color=THEME["bg_alt"], text_color=THEME["text"],
            command=self.abrir_modal_exportacao, height=35
        )
        btn.pack(side="left", padx=20, pady=10)

    def abrir_modal_exportacao(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Exportar Dados")
        modal.geometry("400x320")
        modal.attributes("-topmost", True) # Garante que abra na frente
        modal.resizable(False, False)
        modal.grab_set() # Bloqueia interação com a janela de trás

        # Centralizar Modal
        modal.update_idletasks()
        x = self.winfo_screenwidth() // 2 - 200
        y = self.winfo_screenheight() // 2 - 160
        modal.geometry(f"+{x}+{y}")

        # --- Conteúdo do Modal ---
        ctk.CTkLabel(modal, text="Configurar Exportação", font=font(16, "bold")).pack(pady=20)

        # 1. Seleção de Tipo
        ctk.CTkLabel(modal, text="O que deseja exportar?", font=font(12)).pack(anchor="w", padx=40)
        tipo_var = ctk.StringVar(value="estudantes")
        opcoes_tipo = [("Estudantes", "estudantes"), ("Agenda", "agenda"), ("Triagens", "triagens")]
        
        tipo_frame = ctk.CTkFrame(modal, fg_color="transparent")
        tipo_frame.pack(fill="x", padx=40, pady=5)
        for text, val in opcoes_tipo:
            ctk.CTkRadioButton(tipo_frame, text=text, variable=tipo_var, value=val, font=font(11)).pack(side="left", expand=True)

        # 2. Seleção de Formato
        ctk.CTkLabel(modal, text="Formato do arquivo:", font=font(12)).pack(anchor="w", padx=40, pady=(15, 0))
        formato_var = ctk.StringVar(value="pdf")

        formato_frame = ctk.CTkFrame(modal, fg_color="transparent")
        formato_frame.pack(fill="x", padx=40, pady=5)

        # Adicionadas as três opções agora:
        ctk.CTkRadioButton(formato_frame, text="PDF", variable=formato_var, value="pdf").pack(side="left", expand=True)
        ctk.CTkRadioButton(formato_frame, text="Excel", variable=formato_var, value="excel").pack(side="left", expand=True)
        ctk.CTkRadioButton(formato_frame, text="Word", variable=formato_var, value="word").pack(side="left", expand=True)
        # 3. Botões de Ação
        btn_box = ctk.CTkFrame(modal, fg_color="transparent")
        btn_box.pack(fill="x", padx=40, pady=30)

        def confirmar():
            tipo = tipo_var.get()
            formato = formato_var.get()
            modal.destroy() # Fecha a modal antes de iniciar o processo pesado
            self.controller.exportar(tipo, formato)

        ctk.CTkButton(btn_box, text="Cancelar", fg_color="transparent", border_width=1, 
                      text_color=THEME["text"], command=modal.destroy, width=100).pack(side="left")
        
        ctk.CTkButton(btn_box, text="Gerar Arquivo", fg_color=THEME["primary"], 
                      hover_color=THEME["primary_hover"], command=confirmar, width=150).pack(side="right")

    def update_view(self, stats_res, reports_res):
        """Ponto único de entrada para atualizar a tela com dados do banco"""
        if stats_res.get('success'):
            data = stats_res.get('data', {}).get('summary', {})
            
            # Mapeamento dinâmico Banco -> UI
            mapping = {
                "total": data.get('students_total', '0'),
                "appointments": data.get('appointments_total', '0'),
                "interventions": data.get('interventions_total', '0'),
                "screenings": data.get('screenings_total', '0')
            }
            
            for key, value in mapping.items():
                if key in self.card_widgets:
                    self.card_widgets[key].configure(text=value)
            
            # Atualiza resumo lateral
            self.summary_labels["students"].configure(text=data.get('students_total', '0'))
            self.summary_labels["rate"].configure(text=f"{data.get('attendance_rate', '0')}%")

        if reports_res.get('success'):
            self._popular_lista_relatorios(reports_res.get('data', {}).get('reports', []))

    def _popular_lista_relatorios(self, items):
        """Limpa e reconstrói a lista com botão de excluir"""
        for w in self.reports_container.winfo_children():
            w.destroy()
            
        for r in items:
            row = ctk.CTkFrame(self.reports_container, fg_color=THEME["bg_alt"], height=45)
            row.pack(fill="x", pady=2, padx=5)
            
            # Nome do Relatório
            ctk.CTkLabel(row, text=f"📄 {r.get('name')}", font=font(12)).pack(side="left", padx=15)
            
            # Container para botões na direita
            btn_container = ctk.CTkFrame(row, fg_color="transparent")
            btn_container.pack(side="right", padx=10)

            # Botão Excluir (Ícone ou Texto)
            btn_delete = ctk.CTkButton(
                btn_container, 
                text="🗑️", 
                width=30, 
                height=30,
                fg_color="transparent",
                text_color="#FF4D4D", # Vermelho
                hover_color=THEME["bg"],
                # Importante: lambda r=r garante que o ID correto seja passado
                command=lambda r_id=r.get('id'): self.controller.solicitar_exclusao(r_id)
            )
            btn_delete.pack(side="right", padx=5)

            # Tipo do relatório (Muted)
            ctk.CTkLabel(btn_container, text=r.get('type'), font=font(11), text_color=THEME["text_muted"]).pack(side="right", padx=10)
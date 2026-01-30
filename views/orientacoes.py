import customtkinter as ctk
from datetime import datetime

class OrientacoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f8fafc")
        self.controller = controller

        # Cores (Padrão SerPleno)
        self.colors = {
            "bg": "#f8fafc",
            "card": "white",
            "primary": "#4f46e5",
            "primary_hover": "#4338ca",
            "text_main": "#1e293b",
            "text_muted": "#64748b",
            "border": "#e2e8f0",
            "purple_light": "#f5f3ff",
            "purple_icon": "#8b5cf6"
        }

        # Configuração do Layout Geral (2 Colunas)
        # 1. Cabeçalho Superior
        self.criar_cabecalho_superior()

        # 2. Banner de Orientações e Acompanhamento
        self.criar_banner_orientacoes()

        # Container Principal para Conteúdo Lado a Lado
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        self.main_container.columnconfigure(0, weight=1) # Coluna Alunos
        self.main_container.columnconfigure(1, weight=3) # Coluna Form

        # 3. Painel Esquerdo: Lista de Estudantes
        self.criar_painel_estudantes()

        # 4. Painel Direito: Construtor de Orientações
        self.criar_painel_construtor()

    def criar_cabecalho_superior(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(
            header, 
            text="Orientações", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.colors["text_main"]
        ).pack(side="left")

        # Ícones da direita
        icons_frame = ctk.CTkFrame(header, fg_color="transparent")
        icons_frame.pack(side="right")
        
        # Simulação de ícones para manter o padrão
        ctk.CTkLabel(icons_frame, text="🤝", font=ctk.CTkFont(size=22)).pack(side="left", padx=5)
        ctk.CTkLabel(icons_frame, text="🔔", font=ctk.CTkFont(size=20), text_color="#64748b").pack(side="left", padx=5)
        
        avatar = ctk.CTkFrame(icons_frame, fg_color="#e5e9f0", width=42, height=42, corner_radius=21)
        avatar.pack(side="left", padx=8)
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text="U", font=("Segoe UI", 15, "bold"), text_color="#475569").place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(icons_frame, text="⎗", font=("Segoe UI", 22, "bold"), text_color="#64748b").pack(side="left", padx=2)

    def criar_banner_orientacoes(self):
        banner = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=15, border_width=1, border_color=self.colors["border"])
        banner.pack(fill="x", padx=30, pady=(0, 25))

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=20)

        # Lado Esquerdo: Ícone e Texto
        cont_esq = ctk.CTkFrame(inner, fg_color="transparent")
        cont_esq.pack(side="left")

        icon_box = ctk.CTkFrame(cont_esq, width=54, height=54, fg_color=self.colors["purple_light"], corner_radius=12)
        icon_box.pack(side="left", padx=(0, 20))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="💜", font=("Segoe UI", 24)).place(relx=0.5, rely=0.5, anchor="center")

        texts = ctk.CTkFrame(cont_esq, fg_color="transparent")
        texts.pack(side="left")
        ctk.CTkLabel(texts, text="Orientações e Acompanhamento", font=("Segoe UI", 18, "bold"), text_color=self.colors["text_main"]).pack(anchor="w")
        ctk.CTkLabel(texts, text="Selecione um estudante ao lado para iniciar", font=("Segoe UI", 14), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Lado Direito: Botão Salvar Global (conforme imagem)
        btn_save = ctk.CTkButton(
            inner, text="💾", width=40, height=40, 
            fg_color=self.colors["primary"], text_color="white", corner_radius=8
        )
        btn_save.pack(side="right")

    def criar_painel_estudantes(self):
        panel = ctk.CTkFrame(self.main_container, fg_color="transparent")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 20))

        ctk.CTkLabel(panel, text="Estudantes", font=("Segoe UI", 16, "bold"), text_color=self.colors["text_main"]).pack(anchor="w", pady=(0, 10))

        # Barra de Pesquisa
        search_frame = ctk.CTkFrame(panel, fg_color=self.colors["card"], corner_radius=10, border_width=1, border_color=self.colors["border"])
        search_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(search_frame, text="🔍", font=("Segoe UI", 12)).pack(side="left", padx=10)
        self.search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="Filtrar alunos...", 
            fg_color="transparent", border_width=0, height=35
        )
        self.search_entry.pack(side="left", fill="x", expand=True)

        # Lista de Alunos (Mock estilo card conforme imagem)
        self.scroll_alunos = ctk.CTkScrollableFrame(panel, fg_color="transparent", height=1000)
        self.scroll_alunos.pack(fill="both", expand=True)

        # Mock Data estendida conforme imagem
        alunos = [
            ("Alice Lima", "Logística"),
            ("Bernardo Almeida", "Logística"),
            ("Bruno Oliveira", "Software Multiplataforma"),
            ("Bruno Silva", "Gestão de TI"),
            ("Clara Ribeiro", "Logística"),
            ("Daniel Silva", "Análise de Sistemas"),
            ("Eduarda Souza", "Logística"),
            ("Isabela Pereira", "Gestão Empresarial"),
            ("João Barbosa", "Software Multiplataforma"),
            ("João Lima", "Análise de Sistemas"),
            ("Karina Almeida", "Gestão de TI"),
            ("Karina Araujo", "Banco de Dados"),
            ("Karina Ribeiro", "Análise de Sistemas"),
            ("Lucas Santos", "Logística"),
            ("Mariana Costa", "Segurança da Informação"),
        ]

        for nome, curso in alunos:
            self.criar_card_aluno(self.scroll_alunos, nome, curso)

    def criar_card_aluno(self, parent, nome, curso):
        card = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=8, border_width=1, border_color=self.colors["border"])
        card.pack(fill="x", pady=4, padx=2)
        
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(info, text=nome, font=("Segoe UI", 13, "bold"), text_color=self.colors["text_main"]).pack(anchor="w")
        ctk.CTkLabel(info, text=curso, font=("Segoe UI", 11), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Eventos para simular seleção
        card.bind("<Button-1>", lambda e: self.selecionar_aluno(nome))

    def criar_painel_construtor(self):
        container = ctk.CTkFrame(self.main_container, fg_color=self.colors["card"], corner_radius=15, border_width=1, border_color=self.colors["border"])
        container.grid(row=0, column=1, sticky="nsew")

        # Tabs (Nova Orientação / Histórico)
        tab_frame = ctk.CTkFrame(container, fg_color="#f1f5f9", height=45, corner_radius=8)
        tab_frame.pack(fill="x", padx=20, pady=20)
        tab_frame.pack_propagate(False)

        ctk.CTkButton(tab_frame, text="Nova Orientação", fg_color="white", text_color=self.colors["text_main"], font=("Segoe UI", 12, "bold"), width=150, corner_radius=6, height=36).pack(side="left", padx=4, pady=4)
        ctk.CTkButton(tab_frame, text="Histórico", fg_color="transparent", text_color=self.colors["text_muted"], font=("Segoe UI", 12), width=150, height=36).pack(side="left", padx=4, pady=4)

        # Container do Formulário com Scroll
        form_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent", height=1200)
        form_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Seção 1: Campos Básicos
        self.criar_campo(form_scroll, "Título da Orientação", "Ex: Planejamento de Estudos Semanal")
        
        row_data_tema = ctk.CTkFrame(form_scroll, fg_color="transparent")
        row_data_tema.pack(fill="x", pady=10)
        self.criar_campo(row_data_tema, "Data da Sessão", "dd/mm/aaaa", side="left", width=250)
        self.criar_campo(row_data_tema, "Tema / Categoria", "Ex: Organização, Ansiedade, Rotina", side="left", padx=(20, 0))

        self.criar_campo(form_scroll, "Modelos Rápidos", "Selecione um modelo...", is_dropdown=True)
        self.criar_campo(form_scroll, "Mensagem Motivacional (Destaque)", "Escreva uma mensagem de apoio que aparecerá em destaque...", is_text=True, height=80)

        # Divisor
        ctk.CTkFrame(form_scroll, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=30)

        # Seção 2: Conteúdo Dinâmico
        header_din = ctk.CTkFrame(form_scroll, fg_color="transparent")
        header_din.pack(fill="x")
        ctk.CTkLabel(header_din, text="Conteúdo Dinâmico", font=("Segoe UI", 16, "bold"), text_color=self.colors["text_main"]).pack(side="left")
        ctk.CTkLabel(header_din, text="📥 Exportar JSON", font=("Segoe UI", 12, "bold"), text_color=self.colors["primary"], cursor="hand2").pack(side="right")

        grid_din = ctk.CTkFrame(form_scroll, fg_color="transparent")
        grid_din.pack(fill="x", pady=20)
        grid_din.columnconfigure(0, weight=1)
        grid_din.columnconfigure(1, weight=1)

        # Coluna Esquerda do Dinâmico
        col_esq = ctk.CTkFrame(grid_din, fg_color="transparent")
        col_esq.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        self.criar_campo(col_esq, "Título", "", side="top")
        self.criar_campo(col_esq, "Tema", "", side="top", pady=(15, 0))
        self.criar_campo(col_esq, "Data da Sessão", "dd/mm/aaaa", side="top", pady=(15, 0))
        self.criar_campo(col_esq, "Mensagem Motivacional", "Ass.: Olá, analista!", is_text=True, height=80, pady=(15, 0))
        
        # Anexos
        ctk.CTkLabel(col_esq, text="Anexos (PDFs, etc.)", font=("Segoe UI", 12, "bold"), text_color=self.colors["text_main"]).pack(anchor="w", pady=(15, 5))
        ctk.CTkButton(col_esq, text="Escolher Arquivos", fg_color="#f1f5f9", text_color=self.colors["text_main"], border_width=1, border_color=self.colors["border"], height=35).pack(anchor="w")

        # Coluna Direita do Dinâmico (Editor de Texto)
        col_dir = ctk.CTkFrame(grid_din, fg_color="transparent")
        col_dir.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(col_dir, text="Conteúdo (Markdown ou Rich Text)", font=("Segoe UI", 12, "bold"), text_color=self.colors["text_main"]).pack(anchor="w")
        
        editor_card = ctk.CTkFrame(col_dir, fg_color=self.colors["card"], border_width=1, border_color=self.colors["border"], corner_radius=10)
        editor_card.pack(fill="both", expand=True, pady=(5, 10))

        # Toolbar do Editor
        toolbar = ctk.CTkFrame(editor_card, fg_color="#f8fafc", height=40, corner_radius=0)
        toolbar.pack(fill="x")
        ctk.CTkLabel(toolbar, text="𝐁  𝐼  𝐇  ❝  𝓩  🔢  ●  🔗  🖼  ♾  ✖  ❓", font=("Segoe UI", 12), text_color="#475569").pack(pady=8)
        
        self.editor = ctk.CTkTextbox(editor_card, fg_color="transparent", border_width=0, font=("Segoe UI", 13))
        self.editor.pack(fill="both", expand=True, padx=5, pady=5)

        # Checkbox Markdown
        ctk.CTkCheckBox(col_dir, text="Usar Markdown", font=("Segoe UI", 12), border_color=self.colors["border"], hover_color=self.colors["purple_light"], checkmark_color=self.colors["primary"]).pack(anchor="w", pady=5)

        # Checklist
        ctk.CTkLabel(col_dir, text="Plano de Ação (Checklist)", font=("Segoe UI", 12, "bold"), text_color=self.colors["text_main"]).pack(anchor="w", pady=(10, 5))
        check_row = ctk.CTkFrame(col_dir, fg_color="transparent")
        check_row.pack(fill="x")
        ctk.CTkEntry(check_row, placeholder_text="Nova tarefa", fg_color="#f8fafc", height=35, corner_radius=8).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(check_row, text="Adicionar", fg_color="#f1f5f9", text_color=self.colors["text_main"], width=80, height=35).pack(side="left", padx=(10, 0))

        # Ações Finais
        final_actions = ctk.CTkFrame(form_scroll, fg_color="transparent")
        final_actions.pack(fill="x", pady=40)
        
        ctk.CTkButton(final_actions, text="Salvar Orientação", fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"], text_color="white", font=("Segoe UI", 14, "bold"), height=45, width=180, corner_radius=10).pack(side="left")
        ctk.CTkButton(final_actions, text="Resetar", fg_color="transparent", border_width=1, border_color=self.colors["border"], text_color=self.colors["text_muted"], font=("Segoe UI", 14), height=45, width=120, corner_radius=10).pack(side="left", padx=20)

    def criar_campo(self, parent, label, placeholder, side="top", width=None, padx=0, pady=15, is_text=False, is_dropdown=False, height=None):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        if side == "left":
            frame.pack(side="left", fill="x", expand=True, padx=padx)
        else:
            frame.pack(fill="x", pady=pady)
            
        ctk.CTkLabel(frame, text=label, font=("Segoe UI", 12, "bold"), text_color=self.colors["text_main"]).pack(anchor="w")
        
        if is_text:
            widget = ctk.CTkTextbox(frame, fg_color="#f8fafc", border_width=1, border_color=self.colors["border"], height=height or 100, corner_radius=8, font=("Segoe UI", 13))
            widget.insert("0.0", placeholder)
        elif is_dropdown:
            widget = ctk.CTkOptionMenu(frame, values=[placeholder, "Modelo: Ansiedade", "Modelo: Foco e Disciplina"], fg_color="#f8fafc", button_color="#f8fafc", button_hover_color="#e2e8f0", text_color=self.colors["text_muted"], corner_radius=8, dynamic_resizing=False)
        else:
            widget = ctk.CTkEntry(frame, placeholder_text=placeholder, fg_color="#f8fafc", border_width=1, border_color=self.colors["border"], height=42, corner_radius=10, font=("Segoe UI", 13))
            
        if width:
            widget.configure(width=width)
        widget.pack(fill="x", pady=(5, 0))

    def selecionar_aluno(self, nome):
        print(f"Estudante Selecionado: {nome}")

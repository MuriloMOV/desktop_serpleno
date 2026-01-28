import customtkinter as ctk

class ComunicacaoInternaFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller

        # Configuração do layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----- HEADER -----
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        
        self.titulo = ctk.CTkLabel(
            self.header_frame,
            text="Comunicação",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#111827"
        )
        self.titulo.pack(side="left")

        self.btn_nova_msg = ctk.CTkButton(
            self.header_frame,
            text=" Nova Mensagem", # Espaço para o "ícone"
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8
        )
        self.btn_nova_msg.pack(side="right")

        # ----- CONTEÚDO PRINCIPAL -----
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=30, pady=(10, 30))
        self.main_container.grid_columnconfigure(0, weight=1) # Coluna da esquerda (Conversas)
        self.main_container.grid_columnconfigure(1, weight=3) # Coluna da direita (Chat)
        self.main_container.grid_rowconfigure(0, weight=1)

        # --- Lado Esquerdo: Conversas ---
        self.conversas_frame = ctk.CTkFrame(self.main_container, fg_color="white", corner_radius=15, border_width=1, border_color="#e5e7eb")
        self.conversas_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(
            self.conversas_frame, 
            text="Conversas", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Lista de contatos
        self.scroll_contatos = ctk.CTkScrollableFrame(self.conversas_frame, fg_color="transparent")
        self.scroll_contatos.pack(fill="both", expand=True)

        self.lista_contatos = [("Admin", "#60a5fa"), ("Coordenação", "#4ade80"), ("Sistema", "#f87171")]
        for nome, cor in self.lista_contatos:
            self.criar_item_contato(nome, cor)

        # --- Lado Direito: Área de Chat ---
        self.chat_frame = ctk.CTkFrame(self.main_container, fg_color="white", corner_radius=15, border_width=1, border_color="#e5e7eb")
        self.chat_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.chat_frame.grid_rowconfigure(1, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Header do Chat
        self.chat_header_container = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.chat_header_container.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            self.chat_header_container,
            text="Assunto da Mensagem",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#111827"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            self.chat_header_container,
            text="De: Nome do Remetente",
            font=ctk.CTkFont(size=12),
            text_color="#6b7280"
        ).pack(anchor="w")
        
        # Linha separadora
        self.separator = ctk.CTkFrame(self.chat_frame, height=1, fg_color="#f3f4f6")
        self.separator.grid(row=0, column=0, sticky="ews", padx=20)

        # Área de Mensagens
        self.area_mensagens = ctk.CTkScrollableFrame(self.chat_frame, fg_color="transparent")
        self.area_mensagens.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        # Input de Mensagem Container
        self.container_input = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.container_input.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 10))

        self.input_inner_frame = ctk.CTkFrame(self.container_input, fg_color="transparent")
        self.input_inner_frame.pack(fill="x", expand=True)
        
        # Placeholder para avatar do usuário
        self.avatar_usuario = ctk.CTkFrame(self.input_inner_frame, width=40, height=40, corner_radius=20, fg_color="#fbbf24")
        self.avatar_usuario.pack(side="left", padx=(0, 15), anchor="n")

        self.entry_msg = ctk.CTkTextbox(
            self.input_inner_frame,
            height=90,
            fg_color="white",
            border_color="#d1d5db",
            border_width=1,
            corner_radius=10,
            font=ctk.CTkFont(size=14),
            text_color="#374151"
        )
        self.entry_msg.insert("0.0", "Escreva sua resposta...")
        self.entry_msg.pack(side="left", fill="x", expand=True)

        # Botão de Enviar embaixo no canto esquerdo da área de input
        self.btn_enviar = ctk.CTkButton(
            self.chat_frame,
            text="Enviar resposta",
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=38,
            width=160,
            corner_radius=8
        )
        self.btn_enviar.grid(row=3, column=0, sticky="w", padx=(75, 20), pady=(0, 20))

    def criar_item_contato(self, nome, cor):
        # Usamos um CTkFrame em vez de CTkButton para evitar conflitos de grid/pack interno do CTkButton
        item = ctk.CTkFrame(
            self.scroll_contatos,
            fg_color="transparent",
            height=60,
            corner_radius=8,
            cursor="hand2"
        )
        item.pack(fill="x", padx=5, pady=2)
        
        # Container interno para organizar avatar e texto
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10)

        # Avatar
        avatar = ctk.CTkFrame(inner, width=36, height=36, corner_radius=18, fg_color=cor)
        avatar.pack(side="left", padx=(0, 10), pady=10)
        
        label_nome = ctk.CTkLabel(
            inner,
            text=nome,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4b5563"
        )
        label_nome.pack(side="left")

        # Eventos de Hover e Clique
        def on_enter(e):
            item.configure(fg_color="#f3f4f6")
        
        def on_leave(e):
            item.configure(fg_color="transparent")

        def on_click(e):
            print(f"Selecionado: {nome}")
            # Aqui você pode adicionar a lógica para carregar as mensagens desse contato

        # Bind em todos os componentes para garantir que o clique funcione em qualquer lugar do item
        for widget in [item, inner, avatar, label_nome]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

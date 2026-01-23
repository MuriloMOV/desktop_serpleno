import customtkinter as ctk

class ComunicacaoInternaFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#F3F4F6") # tailwind gray-100
        self.controller = controller

        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Content Area

        # ============= 1. Header =============
        self.criar_header()

        # ============= 2. Content (Conversas + Chat) =============
        self.criar_conteudo()

    def criar_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        # Título
        ctk.CTkLabel(
            header,
            text="Comunicação",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#1F2937"
        ).pack(side="left")

        # Botão Nova Mensagem
        ctk.CTkButton(
            header,
            text="✉️ Nova Mensagem",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#3B82F6", # blue-500
            hover_color="#2563EB", # blue-600
            text_color="white",
            height=40,
            corner_radius=8,
            command=self.abrir_nova_mensagem
        ).pack(side="right")

    def criar_conteudo(self):
        # Main Container
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Grid Split: 1/3 Left (List), 2/3 Right (Detail)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        # === LEFT: Lista de Conversas ===
        left_panel = ctk.CTkFrame(main, fg_color="white", corner_radius=12)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Titulo Lista
        ctk.CTkLabel(
            left_panel, 
            text="Conversas", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#1F2937"
        ).pack(anchor="w", padx=20, pady=20)

        # Scroll List
        self.scroll_conversas = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.scroll_conversas.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        # Mock Data
        self.conversas = [
            {"sender": "Admin", "subject": "Atualização do Sistema", "time": "10:30", "avatar_color": "#60A5FA"},
            {"sender": "Coordenação", "subject": "Reunião Pedagógica", "time": "09:15", "avatar_color": "#4ADE80"},
            {"sender": "Lucas Silva", "subject": "Dúvida sobre matrícula", "time": "Ontem", "avatar_color": "#F87171"}
        ]

        for c in self.conversas:
            self.criar_item_conversa(c)


        # === RIGHT: Área de Mensagem ===
        right_panel = ctk.CTkFrame(main, fg_color="white", corner_radius=12)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Layout Direito
        right_panel.rowconfigure(1, weight=1) # Message body expands
        right_panel.columnconfigure(0, weight=1)

        # 1. Header Mensagem
        msg_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        msg_header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(msg_header, text="Assunto da Mensagem", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="#1F2937").pack(anchor="w")
        
        sub_info = ctk.CTkFrame(msg_header, fg_color="transparent")
        sub_info.pack(anchor="w", pady=(5,0))
        ctk.CTkLabel(sub_info, text="De:", font=ctk.CTkFont(size=12), text_color="#6B7280").pack(side="left")
        ctk.CTkLabel(sub_info, text="Nome do Remetente", font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151").pack(side="left", padx=5)

        # Linha Divisoria
        ctk.CTkFrame(right_panel, height=2, fg_color="#F3F4F6").grid(row=0, column=0, sticky="ews", pady=(75, 0)) # Hackish positioning or use separate row

        # 2. Corpo da Mensagem (Scrollable)
        self.msg_body = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        self.msg_body.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        # Mock Message Content
        ctk.CTkLabel(
            self.msg_body, 
            text="Olá,\n\nGostaria de informar que a atualização do sistema ocorrerá amanhã às 18h. O sistema ficará indisponível por cerca de 30 minutos.\n\nAtenciosamente,\nAdmin",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#374151",
            anchor="w",
            justify="left",
            wraplength=500
        ).pack(anchor="w")


        # 3. Área de Resposta (Footer)
        reply_area = ctk.CTkFrame(right_panel, fg_color="#F9FAFB", corner_radius=12) # gray-50
        reply_area.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        
        # Layout Reply
        reply_area.columnconfigure(1, weight=1)

        # Avatar "Eu"
        avatar_me = ctk.CTkLabel(
            reply_area, 
            text="EU", 
            width=40, height=40, 
            fg_color="#DBEAFE", # blue-100
            text_color="#1E40AF",
            corner_radius=20,
            font=ctk.CTkFont(size=10, weight="bold")
        )
        avatar_me.grid(row=0, column=0, sticky="n", padx=10, pady=10)

        # Text Area Container
        text_container = ctk.CTkFrame(reply_area, fg_color="transparent")
        text_container.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=10)
        
        self.reply_box = ctk.CTkTextbox(
            text_container, 
            height=80, 
            corner_radius=8, 
            border_width=1, 
            border_color="#D1D5DB", 
            fg_color="white",
            text_color="#111827"
        )
        self.reply_box.pack(fill="x")
        
        # Botão Enviar
        ctk.CTkButton(
            text_container,
            text="Enviar resposta",
            width=120,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="white",
            font=ctk.CTkFont(weight="bold"),
            command=self.enviar_resposta
        ).pack(anchor="e", pady=(10, 0))

    def criar_item_conversa(self, data):
        item = ctk.CTkFrame(self.scroll_conversas, fg_color="#F3F4F6", corner_radius=8) # gray-100 placeholder for item
        item.pack(fill="x", pady=4)

        # Avatar
        av = ctk.CTkLabel(
            item, 
            text=data["sender"][:2].upper(),
            width=40, height=40,
            corner_radius=20,
            fg_color=data["avatar_color"],
            text_color="white",
            font=ctk.CTkFont(weight="bold")
        )
        av.pack(side="left", padx=10, pady=10)

        # Info Middle
        info = ctk.CTkFrame(item, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(info, text=data["sender"], font=ctk.CTkFont(weight="bold", size=13), text_color="#1F2937").pack(anchor="w")
        ctk.CTkLabel(info, text=data["subject"], font=ctk.CTkFont(size=11), text_color="#6B7280").pack(anchor="w")

        # Time Right
        ctk.CTkLabel(item, text=data["time"], font=ctk.CTkFont(size=10), text_color="#9CA3AF").pack(side="right", padx=10, anchor="n", pady=12)

    def abrir_nova_mensagem(self):
        print("Nova mensagem")

    def enviar_resposta(self):
        msg = self.reply_box.get("0.0", "end").strip()
        print(f"Enviando: {msg}")
        self.reply_box.delete("0.0", "end")

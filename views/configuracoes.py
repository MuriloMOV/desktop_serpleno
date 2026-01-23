import customtkinter as ctk

class ConfiguracoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#F3F4F6") # tailwind gray-100
        self.controller = controller

        # Grid system
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Header
        self.criar_header()

        # Grid Content (2 cols)
        self.criar_coluna_esquerda()
        self.criar_coluna_direita()

    def criar_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="Configurações",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#1F2937"
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="💾 Salvar Alterações",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#3B82F6", 
            hover_color="#2563EB",
            text_color="white",
            height=40,
            corner_radius=8,
            command=self.salvar_alteracoes
        ).pack(side="right")

    def criar_coluna_esquerda(self):
        # Column 0 Container
        col0 = ctk.CTkFrame(self, fg_color="transparent")
        col0.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        
        # === 1. Perfil ===
        card_perfil = self.criar_card_base(col0, "Perfil")
        card_perfil.pack(fill="x", pady=(0, 20))

        # Inputs
        self.criar_input_texto(card_perfil, "Nome", "Admin Usuario")
        self.criar_input_texto(card_perfil, "Email", "admin@serpleno.edu")
        
        # Avatar
        lbl_foto = ctk.CTkLabel(card_perfil, text="Foto do Perfil", font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151")
        lbl_foto.pack(anchor="w", padx=20, pady=(10, 5))
        
        avatar_row = ctk.CTkFrame(card_perfil, fg_color="transparent")
        avatar_row.pack(fill="x", padx=20, pady=(0, 20))
        
        # Avatar Mock
        ctk.CTkLabel(avatar_row, text="", width=60, height=60, fg_color="#DBEAFE", corner_radius=30).pack(side="left") # Image Placeholder
        
        ctk.CTkButton(
            avatar_row, 
            text="Alterar foto", 
            fg_color="transparent", 
            border_width=1, 
            border_color="#D1D5DB", 
            text_color="#374151",
            hover_color="#F3F4F6",
            width=100
        ).pack(side="left", padx=15)


        # === 2. Privacidade ===
        card_priv = self.criar_card_base(col0, "Privacidade")
        card_priv.pack(fill="x")

        self.criar_switch(card_priv, "Perfil Público", False)
        self.criar_switch(card_priv, "Compartilhar Status Online", True)


    def criar_coluna_direita(self):
        # Column 1 Container
        col1 = ctk.CTkFrame(self, fg_color="transparent")
        col1.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)

        # === 3. Notificações ===
        card_notif = self.criar_card_base(col1, "Notificações")
        card_notif.pack(fill="x", pady=(0, 20))

        self.criar_switch(card_notif, "Notificações por Email", True)
        self.criar_switch(card_notif, "Notificações no Navegador", False)
        self.criar_switch(card_notif, "Sons de Notificação", True)

        # === 4. Aparência ===
        card_theme = self.criar_card_base(col1, "Aparência")
        card_theme.pack(fill="x")
        
        self.criar_combo(card_theme, "Tema", ["Claro", "Escuro", "Sistema"])
        self.criar_combo(card_theme, "Tamanho da Fonte", ["Pequena", "Média", "Grande"])


    # --- Helpers ---
    def criar_card_base(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        ctk.CTkLabel(
            card, 
            text=title, 
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#1F2937"
        ).pack(anchor="w", padx=20, pady=20)
        return card

    def criar_input_texto(self, parent, label, value):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151").pack(anchor="w", pady=(0, 5))
        entry = ctk.CTkEntry(f, width=300, fg_color="#F9FAFB", border_color="#D1D5DB", text_color="#111827", height=35)
        entry.pack(fill="x")
        entry.insert(0, value)

    def criar_switch(self, parent, label, initial_val):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=(5, 15))
        
        # Label left, switch right
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=14), text_color="#374151").pack(side="left")
        
        switch = ctk.CTkSwitch(f, text="", onvalue=True, offvalue=False, progress_color="#3B82F6")
        switch.pack(side="right")
        if initial_val: switch.select()

    def criar_combo(self, parent, label, options):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color="#374151").pack(anchor="w", pady=(0, 5))
        ctk.CTkOptionMenu(
            f, 
            values=options, 
            fg_color="#F9FAFB", 
            button_color="#E5E7EB", 
            button_hover_color="#D1D5DB", 
            dropdown_fg_color="white",
            text_color="#111827"
        ).pack(fill="x")

    def salvar_alteracoes(self):
        print("Salvar configurações...")

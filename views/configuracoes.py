import customtkinter as ctk

class ConfiguracoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#F8FAFC") # slate-50
        self.controller = controller

        # Layout principal em grid
        self.grid_columnconfigure(0, weight=2) # Coluna esquerda (Informações Pessoais)
        self.grid_columnconfigure(1, weight=3) # Coluna direita (Outras Configurações)

        # Header Superior
        self.criar_header_principal()
        
        # Card de Preferências do Sistema (no topo, atravessando colunas se necessário, 
        # mas faremos como um card de destaque)
        self.criar_card_preferencias()

        # Grid Content
        self.criar_coluna_pessoal()
        self.criar_coluna_preferencias()

    def criar_header_principal(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=30, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="Configurações",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#1E293B"
        ).pack(side="left")

        # Ícones do topo direito (Links rápidos)
        icons_frame = ctk.CTkFrame(header, fg_color="transparent")
        icons_frame.pack(side="right")
        
        ctk.CTkLabel(icons_frame, text="🔗", font=("Segoe UI", 16)).pack(side="left", padx=10)
        ctk.CTkLabel(icons_frame, text="🔔", font=("Segoe UI", 16)).pack(side="left", padx=10)
        ctk.CTkLabel(icons_frame, text="U", font=("Segoe UI", 14, "bold"), fg_color="#E2E8F0", width=30, height=30, corner_radius=15).pack(side="left", padx=10)
        ctk.CTkLabel(icons_frame, text="⊏↴", font=("Segoe UI", 16)).pack(side="left", padx=10)

    def criar_card_preferencias(self):
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0")
        card.grid(row=1, column=0, columnspan=2, sticky="ew", padx=30, pady=10)
        
        # Conteúdo interno do card
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        # Ícone e Textos (Esquerda)
        left_side = ctk.CTkFrame(inner, fg_color="transparent")
        left_side.pack(side="left")
        
        ctk.CTkLabel(left_side, text="⚙️", font=("Segoe UI", 24), fg_color="#EEF2FF", text_color="#6366F1", width=45, height=45, corner_radius=10).pack(side="left", padx=(0, 15))
        
        text_info = ctk.CTkFrame(left_side, fg_color="transparent")
        text_info.pack(side="left")
        
        ctk.CTkLabel(text_info, text="Preferências do Sistema", font=("Segoe UI", 16, "bold"), text_color="#1E293B").pack(anchor="w")
        ctk.CTkLabel(text_info, text="Personalize sua experiência no SerPleno", font=("Segoe UI", 13), text_color="#64748B").pack(anchor="w")
        
        # Botões (Direita)
        right_side = ctk.CTkFrame(inner, fg_color="transparent")
        right_side.pack(side="right")
        
        ctk.CTkButton(right_side, text="Descartar", fg_color="transparent", text_color="#64748B", hover_color="#F1F5F9", font=("Segoe UI", 13), width=80).pack(side="left", padx=10)
        
        # Botão de Check/Toggle
        ctk.CTkButton(right_side, text="✓", fg_color="#6366F1", hover_color="#4F46E5", text_color="white", font=("Segoe UI", 14, "bold"), width=35, height=35, corner_radius=8).pack(side="left")

    def criar_coluna_pessoal(self):
        # Container da coluna esquerda
        col_pessoal = ctk.CTkFrame(self, fg_color="transparent")
        col_pessoal.grid(row=2, column=0, sticky="nsew", padx=(30, 15), pady=10)
        
        # Card Informações Pessoais
        card = ctk.CTkFrame(col_pessoal, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0")
        card.pack(fill="both", expand=True)
        
        # Header do Card
        header = self.criar_card_header(card, "👤", "Informações Pessoais", color="#6366F1")
        
        # Área do Avatar
        avatar_frame = ctk.CTkFrame(card, fg_color="transparent")
        avatar_frame.pack(pady=20)
        
        # Placeholder do Avatar (Círculo azul com imagem simulada)
        avatar_circle = ctk.CTkFrame(avatar_frame, width=180, height=180, fg_color="#BFDBFE", corner_radius=90)
        avatar_circle.pack()
        avatar_circle.pack_propagate(False)
        
        # Emoji de "Avatar" centralizado
        ctk.CTkLabel(avatar_circle, text="👩‍🚀", font=("Segoe UI", 80)).place(relx=0.5, rely=0.5, anchor="center")
        
        # Texto e Botão de Câmera
        ctk.CTkLabel(card, text="Toque para alterar imagem", font=("Segoe UI", 11), text_color="#6366F1").pack()
        
        btn_cam = ctk.CTkButton(card, text="📸", width=35, height=35, corner_radius=17, fg_color="#6366F1", font=("Segoe UI", 14))
        # Posicionar sobre o avatar seria complexo aqui, vamos colocar abaixo ou em row
        btn_cam.pack(pady=(5, 20))
        
        # Campos de Input
        self.criar_input_field(card, "Nome de exibição", "Admin SerPleno", "👤")
        self.criar_input_field(card, "Endereço de E-mail", "analista@teste.com", "📧")

    def criar_coluna_preferencias(self):
        # Container da coluna direita
        col_pref = ctk.CTkFrame(self, fg_color="transparent")
        col_pref.grid(row=2, column=1, sticky="nsew", padx=(15, 30), pady=10)
        
        # === 1. Central de Avisos ===
        card_avisos = ctk.CTkFrame(col_pref, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0")
        card_avisos.pack(fill="x", pady=(0, 20))
        
        # Header com Badge
        head_avisos = self.criar_card_header(card_avisos, "🔔", "Central de Avisos", color="#F59E0B")
        badge = ctk.CTkLabel(head_avisos, text="Tempo Real", font=("Segoe UI", 10, "bold"), text_color="#F59E0B", fg_color="#FEF3C7", corner_radius=10, width=70, height=20)
        badge.pack(side="right", padx=10)
        
        # Itens de Avisos
        self.criar_toggle_item(card_avisos, "Mensagens Diretas", "Alerte novos chats privados e mural", True)
        self.criar_toggle_item(card_avisos, "Pedidos de Ajuda", "Notificações críticas de suporte ao aluno", False)
        self.criar_toggle_item(card_avisos, "Feedback de Alunos", "Novas avaliações e comentários nos atendimentos", True)
        self.criar_toggle_item(card_avisos, "Efeitos Sonoros", "Feedback auditivo para alertas e interações", True)

        # === 2. Aparência & Acessibilidade ===
        card_aparencia = ctk.CTkFrame(col_pref, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0")
        card_aparencia.pack(fill="x", pady=(0, 20))
        
        self.criar_card_header(card_aparencia, "🌎", "Aparência & Acessibilidade")
        
        # Combos Lado a Lado
        combo_row = ctk.CTkFrame(card_aparencia, fg_color="transparent")
        combo_row.pack(fill="x", padx=20, pady=10)
        
        f1 = self.criar_combo_field(combo_row, "Esquema de Cores", ["Modo Sereno (Claro)", "Modo Escuro", "Automático"])
        f1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        f2 = self.criar_combo_field(combo_row, "Escala de Texto", ["Padrão (16px)", "Grande (18px)", "Extra Grande (20px)"])
        f2.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Dica de Produtividade
        dica_box = ctk.CTkFrame(card_aparencia, fg_color="#F8FAFC", corner_radius=10, border_width=1, border_color="#E2E8F0")
        dica_box.pack(fill="x", padx=20, pady=(0, 20))
        
        dica_inner = ctk.CTkFrame(dica_box, fg_color="transparent")
        dica_inner.pack(padx=15, pady=10)
        
        ctk.CTkLabel(dica_inner, text="✎", font=("Segoe UI", 14), text_color="#6366F1").pack(side="left", anchor="n", padx=(0, 10))
        
        txt_dica = "Dica de Produtividade\nO Modo Foco (Escuro) reduz a emissão de luz azul, ideal para sessões noturnas de análise de relatórios, diminuindo significativamente a fadiga visual."
        lbl_dica = ctk.CTkLabel(dica_inner, text=txt_dica, font=("Segoe UI", 11), text_color="#64748B", justify="left")
        lbl_dica.pack(side="left")

        # === 3. Sessão & Segurança ===
        card_seguranca = ctk.CTkFrame(col_pref, fg_color="white", corner_radius=15, border_width=1, border_color="#E2E8F0")
        card_seguranca.pack(fill="x")
        
        self.criar_card_header(card_seguranca, "🛡️", "Sessão & Segurança", color="#10B981")
        
        # Itens de Segurança
        self.criar_sessao_item(card_seguranca, "👥", "Perfil Público", "Permitir que outros visualizem suas conquistas", toggle=True, active=True)
        self.criar_sessao_item(card_seguranca, "🔑", "Credenciais", "Última alteração há 3 meses", button_text="Alterar Senha")
        self.criar_sessao_item(card_seguranca, "💻", "Este Dispositivo", "Sessão ativa agora • Windows Desktop", link_text="Encerrar Acesso", link_color="#EF4444")


    # --- Auxiliares de Construção ---

    def criar_card_header(self, parent, icon, title, color="#64748B"):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text=icon, font=("Segoe UI", 16), text_color=color).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(header, text=title, font=("Segoe UI", 14, "bold"), text_color="#1E293B").pack(side="left")
        
        return header

    def criar_input_field(self, parent, label, value, icon):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(container, text=label, font=("Segoe UI", 12), text_color="#64748B").pack(anchor="w")
        
        input_row = ctk.CTkFrame(container, fg_color="#F8FAFC", height=40, corner_radius=8, border_width=1, border_color="#E2E8F0")
        input_row.pack(fill="x", pady=5)
        input_row.pack_propagate(False)
        
        ctk.CTkLabel(input_row, text=icon, font=("Segoe UI", 14), text_color="#94A3B8").pack(side="left", padx=10)
        
        entry = ctk.CTkEntry(input_row, fg_color="transparent", border_width=0, font=("Segoe UI", 13), text_color="#1E293B")
        entry.pack(side="left", fill="both", expand=True)
        entry.insert(0, value)

    def criar_toggle_item(self, parent, title, subtitle, initial_val):
        item = ctk.CTkFrame(parent, fg_color="transparent")
        item.pack(fill="x", padx=20, pady=10)
        
        text_frame = ctk.CTkFrame(item, fg_color="transparent")
        text_frame.pack(side="left")
        
        ctk.CTkLabel(text_frame, text=title, font=("Segoe UI", 13, "bold"), text_color="#1E293B").pack(anchor="w")
        ctk.CTkLabel(text_frame, text=subtitle, font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w")
        
        switch = ctk.CTkSwitch(item, text="", progress_color="#6366F1")
        switch.pack(side="right")
        if initial_val: switch.select()

    def criar_combo_field(self, parent, label, options):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        
        ctk.CTkLabel(container, text=label, font=("Segoe UI", 12), text_color="#64748B").pack(anchor="w")
        
        combo = ctk.CTkOptionMenu(
            container, 
            values=options, 
            fg_color="#F8FAFC", 
            text_color="#1E293B",
            button_color="#F1F5F9",
            button_hover_color="#E2E8F0",
            font=("Segoe UI", 13),
            dropdown_font=("Segoe UI", 13),
            corner_radius=8,
            height=40
        )
        combo.pack(fill="x", pady=5)
        return container

    def criar_sessao_item(self, parent, icon, title, subtitle, toggle=False, active=False, button_text=None, link_text=None, link_color="#6366F1"):
        # Uma linha separadora se não for o primeiro item (simplificado aqui como frame com padding)
        row = ctk.CTkFrame(parent, fg_color="#F8FAFC", corner_radius=10, border_width=1, border_color="#E2E8F0")
        row.pack(fill="x", padx=20, pady=5)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)
        
        # Ícone à esquerda
        icon_box = ctk.CTkFrame(inner, width=40, height=40, fg_color="white", corner_radius=8)
        icon_box.pack(side="left", padx=(0, 15))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=("Segoe UI", 16)).place(relx=0.5, rely=0.5, anchor="center")
        
        # Textos centrais
        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.pack(side="left")
        
        ctk.CTkLabel(text_frame, text=title, font=("Segoe UI", 13, "bold"), text_color="#1E293B").pack(anchor="w")
        ctk.CTkLabel(text_frame, text=subtitle, font=("Segoe UI", 11), text_color="#94A3B8").pack(anchor="w")
        
        # Ação à direita
        if toggle:
            switch = ctk.CTkSwitch(inner, text="", progress_color="#6366F1")
            switch.pack(side="right")
            if active: switch.select()
        elif button_text:
            ctk.CTkButton(inner, text=button_text, font=("Segoe UI", 12), fg_color="#F1F5F9", text_color="#1E293B", hover_color="#E2E8F0", height=32, corner_radius=6).pack(side="right")
        elif link_text:
            ctk.CTkButton(inner, text=link_text, font=("Segoe UI", 12, "bold"), fg_color="transparent", text_color=link_color, hover_color="#FEF2F2" if link_color=="#EF4444" else "#F1F5F9", width=100).pack(side="right")


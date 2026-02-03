import customtkinter as ctk
from PIL import Image
import os

from ui_theme import THEME, SPACING, RADIUS, font

class ConfiguracoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller

        self.colors = THEME

        # Caminhos de imagens
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.img_path = os.path.join(self.base_path, "..", "serpleno_web", "staticfiles", "desktop", "img")

        # Layout principal em grid
        self.grid_columnconfigure(0, weight=2) # Coluna esquerda (Informações Pessoais)
        self.grid_columnconfigure(1, weight=3) # Coluna direita (Outras Configurações)

        # Header Superior
        self.criar_header_principal()
        
        # Card de Preferências do Sistema
        self.criar_card_preferencias()

        # Grid Content
        self.criar_coluna_pessoal()
        self.criar_coluna_preferencias()

    def load_image(self, name, size):
        try:
            path = os.path.join(self.img_path, name)
            if not os.path.exists(path):
                # Fallback para o diretório de imagens padrão se existir
                path = os.path.join(self.base_path, "..", "imagens", name)
            
            if os.path.exists(path):
                return ctk.CTkImage(light_image=Image.open(path), size=size)
        except Exception as e:
            print(f"Erro ao carregar imagem {name}: {e}")
        return None

    def criar_header_principal(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 8))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        icon_box = ctk.CTkFrame(inner, width=48, height=48, corner_radius=12, fg_color=self.colors["primary_light"])
        icon_box.pack(side="left", padx=(0, 16))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="⚙️", font=font(20), text_color=self.colors["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(inner, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="Preferências do Sistema", font=font(20, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(text_box, text="Personalize sua experiência no SerPleno", font=font(12), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Ícones do topo direito (Links rápidos)
        icons_frame = ctk.CTkFrame(inner, fg_color="transparent")
        icons_frame.pack(side="right")
        
        # Estilização dos ícones do topo
        btn_config = {
            "font": font(16),
            "text_color": self.colors["text_muted"],
            "fg_color": "transparent",
            "hover_color": self.colors["bg_alt"],
            "width": 40,
            "height": 40,
            "corner_radius": 20
        }
        
        ctk.CTkButton(icons_frame, text="🔗", **btn_config).pack(side="left", padx=5)
        ctk.CTkButton(icons_frame, text="🔔", **btn_config).pack(side="left", padx=5)
        
        # Avatar Resumido (Círculo com inicial)
        avatar_small = ctk.CTkLabel(
            icons_frame, 
            text="U", 
            font=font(12, "bold"), 
            text_color=self.colors["text_muted"],
            fg_color=self.colors["border"], 
            width=32, 
            height=32, 
            corner_radius=16
        )
        avatar_small.pack(side="left", padx=10)
        
        ctk.CTkButton(icons_frame, text="⊏↴", **btn_config).pack(side="left", padx=5)

    def criar_card_preferencias(self):
        card = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card.grid(row=1, column=0, columnspan=2, sticky="ew", padx=SPACING["page_x"], pady=10)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=25, pady=20)
        
        # Lado Esquerdo (Ícone e Título)
        left_side = ctk.CTkFrame(inner, fg_color="transparent")
        left_side.pack(side="left")
        
        icon_box = ctk.CTkFrame(left_side, width=54, height=54, fg_color=self.colors["primary_light"], corner_radius=15)
        icon_box.pack(side="left", padx=(0, 20))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="⚙️", font=font(20)).place(relx=0.5, rely=0.5, anchor="center")
        
        text_info = ctk.CTkFrame(left_side, fg_color="transparent")
        text_info.pack(side="left")
        
        ctk.CTkLabel(text_info, text="Preferências do Sistema", font=font(18, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(text_info, text="Personalize sua experiência no SerPleno", font=font(14), text_color=self.colors["text_muted"]).pack(anchor="w")
        
        # Lado Direito (Ações)
        right_side = ctk.CTkFrame(inner, fg_color="transparent")
        right_side.pack(side="right")
        
        ctk.CTkButton(
            right_side, 
            text="Descartar", 
            fg_color="transparent", 
            text_color=self.colors["text_muted"], 
            hover_color="#F1F5F9", 
            font=font(14, "bold"), 
            width=100
        ).pack(side="left", padx=15)
        
        ctk.CTkButton(
            right_side, 
            text="✓", 
            fg_color=self.colors["primary"], 
            hover_color=self.colors["primary_hover"], 
            text_color="white", 
            font=font(16, "bold"), 
            width=40, 
            height=40, 
            corner_radius=RADIUS["button"]
        ).pack(side="left")

    def criar_coluna_pessoal(self):
        col_pessoal = ctk.CTkFrame(self, fg_color="transparent")
        col_pessoal.grid(row=2, column=0, sticky="nsew", padx=(SPACING["page_x"], 12), pady=10)
        
        card = ctk.CTkFrame(col_pessoal, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card.pack(fill="both", expand=True)
        
        self.criar_card_header(card, "👤", "Informações Pessoais", color=self.colors["primary"])
        
        # Container do Avatar
        avatar_container = ctk.CTkFrame(card, fg_color="transparent")
        avatar_container.pack(pady=30)
        
        # Círculo externo do Avatar (com borda tracejada simulada por frame + padding)
        avatar_border = ctk.CTkFrame(avatar_container, width=190, height=190, fg_color="transparent", border_width=2, border_color="#E0E7FF", corner_radius=95)
        avatar_border.pack()
        avatar_border.pack_propagate(False)
        
        # Avatar Real ou Placeholder
        img_avatar = self.load_image("avatar-1.jpg", (180, 180))
        avatar_center = ctk.CTkLabel(avatar_border, text="" if img_avatar else "👩‍🚀", image=img_avatar, font=("Segoe UI", 80), width=180, height=180, corner_radius=90, fg_color="#BFDBFE")
        avatar_center.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botão de Câmera (Sobreposto)
        btn_cam = ctk.CTkButton(
            avatar_container, 
            text="📸", 
            width=45, 
            height=45, 
            corner_radius=22, 
            fg_color=self.colors["primary"], 
            hover_color=self.colors["primary_hover"],
            font=("Segoe UI", 16),
            border_width=4,
            border_color="white"
        )
        btn_cam.place(relx=0.88, rely=0.88, anchor="center")
        
        ctk.CTkLabel(card, text="Toque para alterar imagem", font=font(13, "bold"), text_color=self.colors["primary"]).pack()

        # Galeria de Avatares (estilo web)
        gallery = ctk.CTkFrame(card, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        gallery.pack(fill="x", padx=20, pady=(12, 20))

        gallery_inner = ctk.CTkFrame(gallery, fg_color="transparent")
        gallery_inner.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(gallery_inner, text="Galeria SerPleno", font=font(11, "bold"), text_color=self.colors["text_highlight"]).pack(anchor="w", pady=(0, 8))

        grid = ctk.CTkFrame(gallery_inner, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(3):
            grid.grid_columnconfigure(i, weight=1)

        self.avatar_images = []
        for idx in range(1, 7):
            img = self.load_image(f"avatar-{idx}.jpg", (64, 64))
            self.avatar_images.append(img)
            btn = ctk.CTkButton(
                grid,
                text="" if img else str(idx),
                image=img,
                fg_color=self.colors["card"],
                hover_color=self.colors["bg_alt"],
                border_width=1,
                border_color=self.colors["border"],
                corner_radius=RADIUS["input"],
                width=64,
                height=64
            )
            r, c = divmod(idx - 1, 3)
            btn.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
        
        # Campos de Input
        self.criar_input_field(card, "Nome de exibição", "Admin SerPleno", "👤")
        self.criar_input_field(card, "Endereço de E-mail", "analista@teste.com", "📧")

    def criar_coluna_preferencias(self):
        col_pref = ctk.CTkFrame(self, fg_color="transparent")
        col_pref.grid(row=2, column=1, sticky="nsew", padx=(12, SPACING["page_x"]), pady=10)
        
        # 1. Central de Avisos
        card_avisos = ctk.CTkFrame(col_pref, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card_avisos.pack(fill="x", pady=(0, 20))
        
        head = self.criar_card_header(card_avisos, "🔔", "Central de Avisos", color=self.colors["warning"])
        ctk.CTkLabel(
            head, 
            text="Tempo Real", 
            font=font(11, "bold"), 
            text_color=self.colors["warning"], 
            fg_color="#FEF3C7", 
            corner_radius=12, 
            width=85, 
            height=24
        ).pack(side="right", padx=10)
        
        self.criar_toggle_item(card_avisos, "Mensagens Diretas", "Alerte novos chats privados e mural", True)
        self.criar_toggle_item(card_avisos, "Pedidos de Ajuda", "Notificações críticas de suporte ao aluno", False)
        self.criar_toggle_item(card_avisos, "Feedback de Alunos", "Novas avaliações e comentários nos atendimentos", True)
        self.criar_toggle_item(card_avisos, "Efeitos Sonoros", "Feedback auditivo para alertas e interações", True)

        # 2. Aparência & Acessibilidade
        card_aparencia = ctk.CTkFrame(col_pref, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card_aparencia.pack(fill="x", pady=(0, 20))
        
        self.criar_card_header(card_aparencia, "🌎", "Aparência & Acessibilidade", color=self.colors["primary"])
        
        combo_row = ctk.CTkFrame(card_aparencia, fg_color="transparent")
        combo_row.pack(fill="x", padx=25, pady=15)
        
        self.criar_combo_field(combo_row, "Esquema de Cores", ["Modo Sereno (Claro)", "Modo Escuro", "Automático"]).pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.criar_combo_field(combo_row, "Escala de Texto", ["Padrão (16px)", "Grande (18px)", "Extra Grande (20px)"]).pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Dica de Produtividade
        dica_box = ctk.CTkFrame(card_aparencia, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        dica_box.pack(fill="x", padx=25, pady=(0, 25))
        
        dica_inner = ctk.CTkFrame(dica_box, fg_color="transparent")
        dica_inner.pack(padx=20, pady=15, fill="x")
        
        ctk.CTkLabel(dica_inner, text="✎", font=font(18), text_color=self.colors["primary"]).pack(side="left", anchor="n", padx=(0, 15))
        
        txt_dica = "Dica de Produtividade\nO Modo Foco (Escuro) reduz a emissão de luz azul, ideal para sessões noturnas de análise de relatórios, diminuindo significativamente a fadiga visual."
        ctk.CTkLabel(dica_inner, text=txt_dica, font=font(12), text_color=self.colors["text_muted"], justify="left", wraplength=400).pack(side="left")

        # 3. Sessão & Segurança
        card_seguranca = ctk.CTkFrame(col_pref, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card_seguranca.pack(fill="x")
        
        self.criar_card_header(card_seguranca, "🛡️", "Sessão & Segurança", color=self.colors["success"])
        
        self.criar_sessao_item(card_seguranca, "👥", "Perfil Público", "Permitir que outros visualizem suas conquistas", toggle=True, active=True)
        self.criar_sessao_item(card_seguranca, "🔑", "Credenciais", "Última alteração há 3 meses", button_text="Alterar Senha")
        self.criar_sessao_item(card_seguranca, "💻", "Este Dispositivo", "Sessão ativa agora • Windows Desktop", link_text="Encerrar Acesso", link_color=self.colors["danger"])

    def criar_card_header(self, parent, icon, title, color="#64748B"):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(25, 15))
        
        ctk.CTkLabel(header, text=icon, font=font(18), text_color=color).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(header, text=title, font=font(15, "bold"), text_color=self.colors["text"]).pack(side="left")
        
        return header

    def criar_input_field(self, parent, label, value, icon):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=25, pady=15)
        
        ctk.CTkLabel(container, text=label.upper(), font=font(11, "bold"), text_color=self.colors["text_highlight"]).pack(anchor="w", padx=5)
        
        input_row = ctk.CTkFrame(container, fg_color=self.colors["bg_alt"], height=50, corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        input_row.pack(fill="x", pady=8)
        input_row.pack_propagate(False)
        
        ctk.CTkLabel(input_row, text=icon, font=font(16), text_color=self.colors["text_highlight"]).pack(side="left", padx=15)
        
        entry = ctk.CTkEntry(input_row, fg_color="transparent", border_width=0, font=font(14), text_color=self.colors["text"])
        entry.pack(side="left", fill="both", expand=True)
        entry.insert(0, value)

    def criar_toggle_item(self, parent, title, subtitle, initial_val):
        item = ctk.CTkFrame(parent, fg_color="transparent")
        item.pack(fill="x", padx=25, pady=12)
        
        text_frame = ctk.CTkFrame(item, fg_color="transparent")
        text_frame.pack(side="left")
        
        ctk.CTkLabel(text_frame, text=title, font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=subtitle, font=font(12), text_color=self.colors["text_muted"]).pack(anchor="w")
        
        switch = ctk.CTkSwitch(item, text="", progress_color=self.colors["primary"], fg_color=self.colors["border"], button_color="white", button_hover_color=self.colors["border"])
        switch.pack(side="right")
        if initial_val: switch.select()

    def criar_combo_field(self, parent, label, options):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        
        ctk.CTkLabel(container, text=label, font=font(13, "bold"), text_color=self.colors["text_muted"]).pack(anchor="w")
        
        combo = ctk.CTkOptionMenu(
            container, 
            values=options, 
            fg_color=self.colors["bg_alt"], 
            text_color=self.colors["text"],
            button_color=self.colors["border"],
            button_hover_color=self.colors["text_highlight"],
            font=font(13),
            dropdown_font=font(13),
            corner_radius=RADIUS["input"],
            height=45
        )
        combo.pack(fill="x", pady=8)
        return container

    def criar_sessao_item(self, parent, icon, title, subtitle, toggle=False, active=False, button_text=None, link_text=None, link_color="#6366F1"):
        row = ctk.CTkFrame(parent, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        row.pack(fill="x", padx=25, pady=8)
        
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=15)
        
        icon_box = ctk.CTkFrame(inner, width=44, height=44, fg_color=self.colors["card"], corner_radius=RADIUS["button"], border_width=1, border_color=self.colors["border"])
        icon_box.pack(side="left", padx=(0, 15))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=font(18)).place(relx=0.5, rely=0.5, anchor="center")
        
        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.pack(side="left")
        
        ctk.CTkLabel(text_frame, text=title, font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=subtitle, font=font(12), text_color=self.colors["text_muted"]).pack(anchor="w")
        
        if toggle:
            switch = ctk.CTkSwitch(inner, text="", progress_color=self.colors["primary"])
            switch.pack(side="right")
            if active: switch.select()
        elif button_text:
            ctk.CTkButton(inner, text=button_text, font=font(12, "bold"), fg_color=self.colors["primary_light"], text_color=self.colors["primary"], hover_color="#E0E7FF", height=35, corner_radius=RADIUS["button"]).pack(side="right")
        elif link_text:
            ctk.CTkButton(inner, text=link_text, font=("Segoe UI", 12, "bold"), fg_color="transparent", text_color=link_color, hover_color=self.colors["danger_light"] if link_color==self.colors["danger"] else self.colors["primary_light"], width=110).pack(side="right")


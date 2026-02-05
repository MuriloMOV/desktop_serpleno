import customtkinter as ctk
from PIL import Image
import os
import json
from ui_theme import THEME, SPACING, RADIUS, font

class ConfiguracoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.colors = THEME
        self._images = {}
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.render_layout()

    def load_image(self, name, size):
        try:
            cache_key = f"{name}:{size}"
            if cache_key in self._images: return self._images[cache_key]
            path = os.path.join(self.base_path, "..", "imagens", name)
            if os.path.exists(path):
                img = ctk.CTkImage(light_image=Image.open(path), size=size)
                self._images[cache_key] = img
                return img
        except Exception: return None

    def render_layout(self):
        header = self.criar_secao_header("Preferências do Sistema", "Personalize sua experiência no SerPleno", show_actions=True)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=SPACING["page_x"], pady=(20, 10))

        col_left = ctk.CTkFrame(self, fg_color="transparent")
        col_left.grid(row=1, column=0, sticky="nsew", padx=(SPACING["page_x"], 10))
        
        self.render_cartao_pessoal(col_left)

        col_right = ctk.CTkFrame(self, fg_color="transparent")
        col_right.grid(row=1, column=1, sticky="nsew", padx=(10, SPACING["page_x"]))
        
        self.render_central_avisos(col_right)
        self.render_aparencia(col_right)
        self.render_seguranca(col_right)

    def criar_secao_header(self, title, subtitle, show_actions=False):
        frame = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        icon_box = ctk.CTkFrame(inner, width=40, height=40, corner_radius=8, fg_color="#EEF2FF")
        icon_box.pack(side="left", padx=(0, 15))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="⚙️", font=font(18)).place(relx=0.5, rely=0.5, anchor="center")

        txt_box = ctk.CTkFrame(inner, fg_color="transparent")
        txt_box.pack(side="left")
        ctk.CTkLabel(txt_box, text=title, font=font(14, "bold")).pack(anchor="w")
        ctk.CTkLabel(txt_box, text=subtitle, font=font(11), text_color=self.colors["text_muted"]).pack(anchor="w")

        if show_actions:
            actions = ctk.CTkFrame(inner, fg_color="transparent")
            actions.pack(side="right")
            ctk.CTkButton(actions, text="Descartar", fg_color="transparent", text_color=self.colors["text_muted"], width=80).pack(side="left", padx=5)
            ctk.CTkButton(actions, text="✓", fg_color="#4F46E5", width=35, height=35).pack(side="left")
        return frame

    def render_cartao_pessoal(self, container):
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="both", expand=True)
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="👤 Informações Pessoais", font=font(14, "bold")).pack(side="left")

        self.avatar_display = ctk.CTkLabel(card, text="", image=self.load_image("avatar-1.jpg", (160, 160)))
        self.avatar_display.pack(pady=10)

        change_btn = ctk.CTkButton(card, text="Toque para alterar imagem", fg_color="transparent", text_color="#4F46E5", font=font(11, "bold"), command=self.toggle_gallery)
        change_btn.pack()

        self.gallery_frame = ctk.CTkFrame(card, fg_color=self.colors["bg_alt"], corner_radius=12)
        self.grid_galeria = ctk.CTkFrame(self.gallery_frame, fg_color="transparent")
        self.grid_galeria.pack(padx=10, pady=10)
        
        for i in range(1, 7):
            btn = ctk.CTkButton(self.grid_galeria, text="", image=self.load_image(f"avatar-{i}.jpg", (50, 50)), width=50, height=50, fg_color="white", command=lambda x=i: self.update_avatar(x))
            btn.grid(row=(i-1)//3, column=(i-1)%3, padx=2, pady=2)

        self.criar_input_field(card, "Nome de exibição", "Admin", "👤")
        self.criar_input_field(card, "Endereço de E-mail", "analista@teste.com", "📧")

    def toggle_gallery(self):
        if self.gallery_frame.winfo_ismapped():
            self.gallery_frame.pack_forget()
        else:
            self.gallery_frame.pack(fill="x", padx=20, pady=10, before=self.avatar_display)

    def update_avatar(self, idx):
        img = self.load_image(f"avatar-{idx}.jpg", (160, 160))
        if img: self.avatar_display.configure(image=img)
        self.gallery_frame.pack_forget()

    def render_central_avisos(self, container):
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="x", pady=(0, 15))
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="🔔 Central de Avisos", font=font(14, "bold")).pack(side="left")
        ctk.CTkLabel(h, text="Tempo Real", font=font(9, "bold"), fg_color="#FEF3C7", text_color="#92400E", corner_radius=4, padx=8).pack(side="right")

        items = [
            ("Mensagens Diretas", "Alertar novos chats privados e mural"),
            ("Pedidos de Ajuda", "Notificações críticas de suporte ao aluno"),
            ("Feedback de Alunos", "Novas avaliações e comentários"),
            ("Efeitos Sonoros", "Feedback auditivo para alertas")
        ]
        for t, s in items:
            self.criar_toggle_row(card, t, s)

    def render_aparencia(self, container):
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="x", pady=(0, 15))
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="🌎 Aparência & Acessibilidade", font=font(14, "bold")).pack(side="left")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=10)
        self.criar_select(row, "Esquema de Cores", ["Modo Sereno (Claro)", "Modo Foco (Escuro)"]).pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.criar_select(row, "Escala de Texto", ["Padrão (16px)", "Grande (18px)"]).pack(side="left", expand=True, fill="x")

        tip = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color="#E2E8F0")
        tip.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkLabel(tip, text="📝 Dica de Produtividade", font=font(11, "bold")).pack(anchor="w", padx=15, pady=(8, 0))
        ctk.CTkLabel(tip, text="O Modo Foco reduz a emissão de luz azul, ideal para sessões noturnas.", font=font(10), text_color="#64748B", wraplength=400).pack(anchor="w", padx=15, pady=(0, 8))

    def render_seguranca(self, container):
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="x")
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="🛡️ Sessão & Segurança", font=font(14, "bold")).pack(side="left")

        self.criar_item_lista(card, "👥", "Perfil Público", "Permitir que outros visualizem suas conquistas", toggle=True)
        self.criar_item_lista(card, "🔑", "Credenciais", "Última alteração há 3 meses", btn_text="Alterar Senha")
        self.criar_item_lista(card, "💻", "Este Dispositivo", "Sessão ativa agora • Windows Desktop", btn_text="Encerrar Acesso", danger=True)

    def criar_toggle_row(self, parent, title, sub):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=10)
        txt = ctk.CTkFrame(f, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(txt, text=title, font=font(12, "bold")).pack(anchor="w")
        ctk.CTkLabel(txt, text=sub, font=font(10), text_color="#64748B").pack(anchor="w")
        ctk.CTkSwitch(f, text="", progress_color="#4F46E5").pack(side="right")

    def criar_input_field(self, parent, label, val, icon):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(f, text=label, font=font(10, "bold"), text_color="#64748B").pack(anchor="w")
        entry_f = ctk.CTkFrame(f, fg_color="#F8FAFC", height=35, corner_radius=6, border_width=1, border_color="#E2E8F0")
        entry_f.pack(fill="x", pady=4)
        entry_f.pack_propagate(False)
        ctk.CTkLabel(entry_f, text=icon, padx=10).pack(side="left")
        e = ctk.CTkEntry(entry_f, fg_color="transparent", border_width=0, font=font(11))
        e.pack(side="left", fill="both", expand=True)
        e.insert(0, val)

    def criar_select(self, parent, label, opts):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(f, text=label, font=font(10, "bold"), text_color="#64748B").pack(anchor="w")
        ctk.CTkOptionMenu(f, values=opts, fg_color="#F8FAFC", text_color="black", button_color="#F8FAFC", button_hover_color="#E2E8F0", height=35).pack(fill="x", pady=4)
        return f

    def criar_item_lista(self, parent, icon, title, sub, toggle=False, btn_text=None, danger=False):
        f = ctk.CTkFrame(parent, fg_color="transparent", border_width=1, border_color="#F1F5F9", corner_radius=8)
        f.pack(fill="x", padx=20, pady=5)
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        ctk.CTkLabel(inner, text=icon, font=font(16), fg_color="#F1F5F9", width=35, height=35, corner_radius=6).pack(side="left", padx=(0, 12))
        
        txt = ctk.CTkFrame(inner, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(txt, text=title, font=font(12, "bold")).pack(anchor="w")
        ctk.CTkLabel(txt, text=sub, font=font(10), text_color="#64748B").pack(anchor="w")

        if toggle:
            ctk.CTkSwitch(inner, text="", progress_color="#4F46E5").pack(side="right")
        elif btn_text:
            color = "#EF4444" if danger else "#4F46E5"
            ctk.CTkButton(inner, text=btn_text, font=font(10, "bold"), fg_color="transparent", text_color=color, hover_color="#FEF2F2" if danger else "#EEF2FF", width=100).pack(side="right")
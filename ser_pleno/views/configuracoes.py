import customtkinter as ctk
from PIL import Image
import os
import json
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    PrimaryButton,
    GhostButton,
    Divider,
    EmptyState,
)


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
            if cache_key in self._images:
                return self._images[cache_key]
            path = os.path.join(self.base_path, "assets", "avatars", name)
            if os.path.exists(path):
                img = ctk.CTkImage(light_image=Image.open(path), size=size)
                self._images[cache_key] = img
                return img
        except Exception as e:
            print(f"Erro ao carregar imagem {name}: {e}")
            return None

    def render_layout(self):
        header = self.criar_secao_header("Preferências do Sistema", "Personalize sua experiência no SerPleno", show_actions=True)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 16))

        col_left = ctk.CTkFrame(self, fg_color="transparent")
        col_left.grid(row=1, column=0, sticky="nsew", padx=(SPACING["page_x"], 10))

        self.render_cartao_pessoal(col_left)

        col_right = ctk.CTkFrame(self, fg_color="transparent")
        col_right.grid(row=1, column=1, sticky="nsew", padx=(10, SPACING["page_x"]))

        self.render_central_avisos(col_right)
        self.render_aparencia(col_right)
        self.render_seguranca(col_right)

    def criar_secao_header(self, title, subtitle, show_actions=False):
        frame = Card(self, title=f"{title} — {subtitle}" if subtitle else title)
        inner = frame.body

        icon_box = ctk.CTkFrame(inner, width=40, height=40, corner_radius=RADIUS["md"], fg_color=THEME["primary_light"])
        icon_box.place(x=20, y=18)
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="⚙️", font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")

        txt_box = ctk.CTkFrame(inner, fg_color="transparent")
        txt_box.place(x=70, y=12)

        ctk.CTkLabel(txt_box, text=title, font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(txt_box, text=subtitle, font=themed_font("body"), text_color=THEME["text_muted"]).pack(anchor="w")

        if show_actions:
            actions = ctk.CTkFrame(inner, fg_color="transparent")
            actions.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=16)
            GhostButton(actions, text="Descartar", width=90).pack(side="left", padx=5)
            PrimaryButton(actions, text="Salvar", width=80, command=lambda: None).pack(side="left")
        return frame

    def render_cartao_pessoal(self, container):
        card = Card(container)
        card.pack(fill="both", expand=True)

        h = ctk.CTkFrame(card.body, fg_color="transparent")
        h.pack(fill="x", padx=18, pady=(16, 10))
        ctk.CTkLabel(h, text="👤 Informações Pessoais", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")

        try:
            with open(os.path.join(self.base_path, "user_profile.json"), "r") as f:
                profile = json.load(f)
            avatar_name = profile.get("avatar", "avatar-1.jpg")
        except Exception as e:
            print(f"Erro ao carregar perfil: {e}")
            avatar_name = "avatar-1.jpg"

        self.avatar_display = ctk.CTkLabel(card.body, text="", image=self.load_image(avatar_name, (160, 160)))
        self.avatar_display.pack(pady=10)

        change_btn = GhostButton(card.body, text="Alterar imagem de perfil", command=self.toggle_gallery, width=220)
        change_btn.pack(pady=(0, 8))

        self.gallery_frame = ctk.CTkFrame(card.body, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"], border_width=1, border_color=THEME["border"])
        self.grid_galeria = ctk.CTkFrame(self.gallery_frame, fg_color="transparent")
        self.grid_galeria.pack(padx=10, pady=10)

        avatars_dir = os.path.join(self.base_path, "assets", "avatars")
        try:
            avatar_files = [f for f in os.listdir(avatars_dir) if f.startswith("avatar-") and f.endswith(".jpg")]
            avatar_files.sort()
        except Exception as e:
            print(f"Erro ao listar avatares: {e}")
            avatar_files = []

        for i, filename in enumerate(avatar_files):
            btn = ctk.CTkButton(
                self.grid_galeria,
                text="",
                image=self.load_image(filename, (52, 52)),
                width=52,
                height=52,
                fg_color="white",
                hover_color=THEME["primary_light"],
                command=lambda x=filename: self.update_avatar(x),
            )
            btn.grid(row=i // 3, column=i % 3, padx=3, pady=3)

        if self.controller.usuario_logado:
            nome_usuario = f"{self.controller.usuario_logado.get('first_name', '')} {self.controller.usuario_logado.get('last_name', '')}".strip()
            nome_usuario = nome_usuario if nome_usuario else self.controller.usuario_logado.get('username', 'Usuário')
            email_usuario = self.controller.usuario_logado.get('email', 'email@exemplo.com')
        else:
            nome_usuario = 'Usuário'
            email_usuario = 'email@exemplo.com'

        self.criar_input_field(card.body, "Nome de exibição", nome_usuario, "👤")
        self.criar_input_field(card.body, "Endereço de E-mail", email_usuario, "📧")

    def toggle_gallery(self):
        if self.gallery_frame.winfo_ismapped():
            self.gallery_frame.pack_forget()
        else:
            self.gallery_frame.pack(fill="x", padx=20, pady=10, before=self.avatar_display)

    def update_avatar(self, filename):
        img = self.load_image(filename, (160, 160))
        if img:
            self.avatar_display.configure(image=img)
            try:
                with open(os.path.join(self.base_path, "user_profile.json"), "w") as f:
                    json.dump({"avatar": filename}, f)
            except Exception as e:
                print(f"Erro ao salvar avatar: {e}")
        self.gallery_frame.pack_forget()

    def render_central_avisos(self, container):
        card = Card(container)
        card.pack(fill="x", pady=(0, 16))

        h = ctk.CTkFrame(card.body, fg_color="transparent")
        h.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkLabel(h, text="🔔 Central de Avisos", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")
        ctk.CTkLabel(h, text="Tempo Real", font=themed_font("overline", "bold"), fg_color=THEME["warning_soft"], text_color=THEME["warning_strong"], corner_radius=RADIUS["pill"], padx=10).pack(side="right")

        items = [
            ("Mensagens Diretas", "Alertar novos chats privados e mural"),
            ("Pedidos de Ajuda", "Notificações críticas de suporte ao aluno"),
            ("Feedback de Alunos", "Novas avaliações e comentários"),
            ("Efeitos Sonoros", "Feedback auditivo para alertas"),
        ]
        self.notification_switches = {}
        for t, s in items:
            switch = self.criar_toggle_row(card.body, t, s)
            self.notification_switches[t] = switch
            switch.configure(command=lambda switch=switch, t=t: self.toggle_notification(t, switch))

    def toggle_notification(self, notification_type, switch):
        estado = switch.get()
        print(f"Notificação '{notification_type}' {'ativada' if estado else 'desativada'}")

    def render_aparencia(self, container):
        card = Card(container)
        card.pack(fill="x", pady=(0, 16))

        h = ctk.CTkFrame(card.body, fg_color="transparent")
        h.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkLabel(h, text="🌎 Aparência & Acessibilidade", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")

        row = ctk.CTkFrame(card.body, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=8)
        self.theme_select = self.criar_select(row, "Esquema de Cores", ["Modo Sereno (Claro)", "Modo Foco (Escuro)"])
        self.theme_select.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.font_select = self.criar_select(row, "Escala de Texto", ["Padrão (16px)", "Grande (18px)"])
        self.font_select.pack(side="left", expand=True, fill="x")

        tip = Card(card.body)
        tip.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkLabel(tip.body, text="📝 Dica de Produtividade", font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(tip.body, text="O Modo Foco reduz a emissão de luz azul, ideal para sessões noturnas.", font=themed_font("body"), text_color=THEME["text_muted"], wraplength=420, justify="left").pack(anchor="w", padx=14, pady=(4, 14))

    def render_seguranca(self, container):
        card = Card(container)
        card.pack(fill="x")

        h = ctk.CTkFrame(card.body, fg_color="transparent")
        h.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkLabel(h, text="🛡️ Sessão & Segurança", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")

        self.criar_item_lista(card.body, "👥", "Perfil Público", "Permitir que outros visualizem suas conquistas", toggle=True)
        self.criar_item_lista(card.body, "🔑", "Credenciais", "Última alteração há 3 meses", btn_text="Alterar Senha")
        self.criar_item_lista(card.body, "💻", "Este Dispositivo", "Sessão ativa agora • Windows Desktop", btn_text="Encerrar Acesso", danger=True)

    def alterar_configuracao(self, valor):
        if valor == "Modo Sereno (Claro)":
            ctk.set_appearance_mode("light")
        elif valor == "Modo Foco (Escuro)":
            ctk.set_appearance_mode("dark")

    def toggle_seguranca_opcao(self, opcao, switch):
        estado = switch.get()
        print(f"Opção '{opcao}' {'ativada' if estado else 'desativada'}")

    def clicar_botao_seguranca(self, btn_text):
        if btn_text == "Alterar Senha":
            self.abrir_tela_alterar_senha()
        elif btn_text == "Encerrar Acesso":
            self.encerrar_sessao()

    def abrir_tela_alterar_senha(self):
        top = ctk.CTkToplevel(self)
        top.title("Alterar Senha")
        top.geometry("420x320")
        top.resizable(False, False)
        top.configure(fg_color=THEME["card"])

        top.update_idletasks()
        x = (top.winfo_screenwidth() // 2) - (420 // 2)
        y = (top.winfo_screenheight() // 2) - (320 // 2)
        top.geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(top, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(frame, text="Alterar Senha", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(pady=(0, 16))

        self.senha_atual_entry = self.criar_input_field(frame, "Senha Atual", "", "🔒")
        self.nova_senha_entry = self.criar_input_field(frame, "Nova Senha", "", "🔑")
        self.confirmar_senha_entry = self.criar_input_field(frame, "Confirmar Senha", "", "🔑")

        PrimaryButton(frame, text="Salvar Alterações", command=self.salvar_alteracao_senha, width=220).pack(fill="x", pady=(16, 0))

    def salvar_alteracao_senha(self):
        senha_atual = self.senha_atual_entry.get()
        nova_senha = self.nova_senha_entry.get()
        confirmar_senha = self.confirmar_senha_entry.get()

        if nova_senha != confirmar_senha:
            print("As senhas não coincidem")
            return

        if len(nova_senha) < 6:
            print("Senha deve ter pelo menos 6 caracteres")
            return

        print("Senha alterada com sucesso")

    def encerrar_sessao(self):
        self.controller.mostrar_login()

    def criar_toggle_row(self, parent, title, sub):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=18, pady=8)
        txt = ctk.CTkFrame(f, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(txt, text=title, font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(txt, text=sub, font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w")
        switch = ctk.CTkSwitch(f, text="", progress_color=THEME["primary"])
        switch.pack(side="right")
        return switch

    def criar_input_field(self, parent, label, val, icon):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=18, pady=6)
        ctk.CTkLabel(f, text=label, font=themed_font("caption", "bold"), text_color=THEME["text_muted"]).pack(anchor="w")
        entry_f = ctk.CTkFrame(f, fg_color=THEME["bg_alt"], height=36, corner_radius=RADIUS["sm"], border_width=1, border_color=THEME["border"])
        entry_f.pack(fill="x", pady=4)
        entry_f.pack_propagate(False)
        ctk.CTkLabel(entry_f, text=icon, font=themed_font("body")).pack(side="left", padx=10)
        e = ctk.CTkEntry(entry_f, fg_color="transparent", border_width=0, font=themed_font("body"))
        e.pack(side="left", fill="both", expand=True)
        e.insert(0, val)
        return e

    def criar_select(self, parent, label, opts):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(f, text=label, font=themed_font("caption", "bold"), text_color=THEME["text_muted"]).pack(anchor="w")
        option_menu = ctk.CTkOptionMenu(f, values=opts, fg_color=THEME["bg_alt"], text_color=THEME["text"], button_color=THEME["border"], button_hover_color=THEME["border_strong"], height=34, command=self.alterar_configuracao)
        option_menu.pack(fill="x", pady=4)
        return f

    def criar_item_lista(self, parent, icon, title, sub, toggle=False, btn_text=None, danger=False):
        f = ctk.CTkFrame(parent, fg_color="transparent", border_width=1, border_color=THEME["border"], corner_radius=RADIUS["md"])
        f.pack(fill="x", padx=18, pady=4)
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(inner, text=icon, font=themed_font("h3"), fg_color=THEME["bg_alt"], width=36, height=36, corner_radius=RADIUS["pill"]).pack(side="left", padx=(0, 12))

        txt = ctk.CTkFrame(inner, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(txt, text=title, font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(txt, text=sub, font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w")

        if toggle:
            switch = ctk.CTkSwitch(inner, text="", progress_color=THEME["primary"])
            switch.pack(side="right")
            switch.configure(command=lambda switch=switch, title=title: self.toggle_seguranca_opcao(title, switch))
        elif btn_text:
            color = THEME["danger"] if danger else THEME["primary"]
            btn = GhostButton(inner, text=btn_text, command=lambda btn_text=btn_text: self.clicar_botao_seguranca(btn_text), width=140)
            if danger:
                btn.configure(text_color=color, hover_color=THEME["danger_soft"])
            btn.pack(side="right")

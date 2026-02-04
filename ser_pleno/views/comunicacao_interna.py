import customtkinter as ctk
from PIL import Image
import os

from ui_theme import THEME, SPACING, RADIUS, font

class ComunicacaoInternaFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller

        self.colors = THEME

        # Caminhos de imagens
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.img_path = os.path.join(self.base_path, "..", "imagens")

        # Grid layout principal (Sidebar + Chat Area)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============= 1. Sidebar (Lista de Contatos) =============
        self.criar_sidebar()

        # ============= 2. Chat Area (Conversa Ativa) =============
        self.criar_chat_area()

    def load_image(self, name, size):
        try:
            if not hasattr(self, "_images"):
                self._images = {}
            cache_key = f"{name}:{size}"
            if cache_key in self._images:
                return self._images[cache_key]

            candidates = [
                os.path.join(self.img_path, name),
                os.path.join(self.base_path, "assets", "avatars", name),
                os.path.join(self.base_path, "..", "imagens", name),
            ]
            for path in candidates:
                if path and os.path.exists(path):
                    img = ctk.CTkImage(light_image=Image.open(path), size=size)
                    self._images[cache_key] = img
                    return img
        except Exception as e:
            print(f"Erro ao carregar imagem {name}: {e}")
        return None

    def criar_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=self.colors["card"], width=320, corner_radius=0, border_width=1, border_color=self.colors["border"])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Header Sidebar
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=25)
        
        header_text = ctk.CTkFrame(header, fg_color="transparent")
        header_text.pack(side="left")
        ctk.CTkLabel(
            header_text,
            text="Mensagens",
            font=font(20, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            header_text,
            text="Conversas internas e suporte",
            font=font(12),
            text_color=self.colors["text_muted"]
        ).pack(anchor="w")
        
        btn_new = ctk.CTkButton(
            header, text="+", width=35, height=35, corner_radius=18, 
            fg_color=self.colors["primary_light"], text_color=self.colors["primary"],
            hover_color="#E0E7FF", font=font(20, "bold")
        )
        btn_new.pack(side="right")

        # Busca
        search_frame = ctk.CTkFrame(sidebar, fg_color=self.colors["bg_alt"], height=45, corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        search_frame.pack(fill="x", padx=20, pady=(0, 20))
        search_frame.pack_propagate(False)
        
        ctk.CTkLabel(search_frame, text="🔍", font=font(14), text_color=self.colors["text_highlight"]).pack(side="left", padx=12)
        ctk.CTkEntry(search_frame, placeholder_text="Buscar conversas...", fg_color="transparent", border_width=0, font=font(13)).pack(side="left", fill="both", expand=True)

        # Lista de Conversas
        self.scroll_contacts = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", corner_radius=0)
        self.scroll_contacts.pack(fill="both", expand=True)

        # Mock Contacts
        contacts = [
            {"name": "Dra. Beatriz Clara", "msg": "Online agora", "active": True, "unread": 2, "img": "avatar-2.jpg"},
            {"name": "Coordenação", "msg": "Reunião Pedagógica", "active": False, "unread": 0, "img": "avatar-3.jpg"},
            {"name": "Suporte Técnico", "msg": "Chamado #442 aberto", "active": True, "unread": 0, "img": "avatar-4.jpg"},
            {"name": "Carlos Eduardo", "msg": "Vi seu relatório ontem", "active": False, "unread": 0, "img": "avatar-5.jpg"},
            {"name": "Ana Luiza", "msg": "Pode revisar a triagem?", "active": True, "unread": 1, "img": "avatar-6.jpg"}
        ]

        for i, c in enumerate(contacts):
            self.criar_contato_item(c, is_first=(i==0))

    def criar_contato_item(self, data, is_first=False):
        bg_color = self.colors["primary_light"] if is_first else "transparent"
        item = ctk.CTkFrame(self.scroll_contacts, fg_color=bg_color, height=80, corner_radius=RADIUS["input"] if is_first else 0)
        item.pack(fill="x", padx=10, pady=2)
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        # Avatar com Indicador Online
        avatar_box = ctk.CTkFrame(inner, width=48, height=48, fg_color="transparent")
        avatar_box.pack(side="left", padx=(0, 12))
        avatar_box.pack_propagate(False)
        
        img = self.load_image(data["img"], (48, 48))
        lbl_img = ctk.CTkLabel(avatar_box, text="" if img else "👤", image=img, width=48, height=48, corner_radius=24, fg_color=self.colors["border"])
        lbl_img.place(relx=0.5, rely=0.5, anchor="center")
        
        if data["active"]:
            ctk.CTkFrame(avatar_box, width=12, height=12, fg_color=self.colors["success"], corner_radius=6, border_width=2, border_color="white").place(relx=0.85, rely=0.85, anchor="center")

        # Textos
        txt_frame = ctk.CTkFrame(inner, fg_color="transparent")
        txt_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(txt_frame, text=data["name"], font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        # Corrigindo o erro de cor condicional
        color_msg = self.colors["text_muted"] if not is_first else self.colors["primary"]
        ctk.CTkLabel(txt_frame, text=data["msg"], font=font(12), text_color=color_msg).pack(anchor="w")

        # Unread / Time
        if data["unread"] > 0:
            badge = ctk.CTkLabel(inner, text=str(data["unread"]), width=20, height=20, corner_radius=10, fg_color=self.colors["danger"], text_color="white", font=font(10, "bold"))
            badge.pack(side="right")
        elif is_first:
            ctk.CTkLabel(inner, text="2 min", font=font(11), text_color=self.colors["primary"]).pack(side="right", anchor="n")

    def criar_chat_area(self):
        container = ctk.CTkFrame(self, fg_color=self.colors["bg_chat"], corner_radius=0)
        container.grid(row=0, column=1, sticky="nsew")
        
        # Grid Interno Chat
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # --- 1. Header Chat ---
        header = ctk.CTkFrame(container, fg_color=self.colors["card"], height=80, corner_radius=0, border_width=1, border_color=self.colors["border"])
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        
        inner_h = ctk.CTkFrame(header, fg_color="transparent")
        inner_h.pack(fill="both", expand=True, padx=25)

        # Info User
        user_info = ctk.CTkFrame(inner_h, fg_color="transparent")
        user_info.pack(side="left")
        
        img_h = self.load_image("avatar-2.jpg", (42, 42))
        ctk.CTkLabel(user_info, text="", image=img_h, width=42, height=42, corner_radius=21, fg_color=self.colors["border"]).pack(side="left", padx=(0, 15))
        
        title_v = ctk.CTkFrame(user_info, fg_color="transparent")
        title_v.pack(side="left")
        ctk.CTkLabel(title_v, text="Dra. Beatriz Clara", font=font(16, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(title_v, text="Online agora", font=font(12), text_color=self.colors["success"]).pack(anchor="w")

        # Actions
        actions = ctk.CTkFrame(inner_h, fg_color="transparent")
        actions.pack(side="right")
        
        btn_style = {"width": 40, "height": 40, "corner_radius": 20, "fg_color": "transparent", "hover_color": self.colors["bg_alt"], "text_color": self.colors["text_muted"]}
        ctk.CTkButton(actions, text="📷", **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="📞", **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="⋮", **btn_style).pack(side="left", padx=2)

        # --- 2. Mensagens ---
        self.msg_area = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.msg_area.grid(row=1, column=0, sticky="nsew", padx=24, pady=12)

        # Timeline
        ctk.CTkLabel(self.msg_area, text="HOJE", font=font(11, "bold"), text_color=self.colors["text_highlight"], fg_color=self.colors["bg_alt"], corner_radius=RADIUS["pill"], width=80).pack(pady=20)

        # Mensagens Mock
        self.criar_mensagem("Olá! Podemos revisar o relatório?", False, "10:41")
        self.criar_mensagem("Claro! Já estou com ele aberto aqui.", True, "10:42")
        self.criar_mensagem("Perfeito. Notei que alguns dados de triagem precisam ser ajustados na seção de estudantes.", False, "10:43")
        self.criar_mensagem("Vou verificar agora mesmo.", True, "10:44")

        # --- 3. Input Area ---
        input_container = ctk.CTkFrame(container, fg_color=self.colors["card"], height=100, corner_radius=0, border_width=1, border_color=self.colors["border"])
        input_container.grid(row=2, column=0, sticky="ew")
        input_container.grid_propagate(False)
        
        box = ctk.CTkFrame(input_container, fg_color=self.colors["bg_alt"], height=55, corner_radius=28, border_width=1, border_color=self.colors["border"])
        box.pack(fill="x", padx=25, pady=22)
        box.pack_propagate(False)
        
        ctk.CTkButton(box, text="📎", width=40, height=40, corner_radius=20, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["border"]).pack(side="left", padx=10)
        
        self.entry_msg = ctk.CTkEntry(box, placeholder_text="Digite sua mensagem...", fg_color="transparent", border_width=0, font=font(14))
        self.entry_msg.pack(side="left", fill="both", expand=True)
        
        actions_in = ctk.CTkFrame(box, fg_color="transparent")
        actions_in.pack(side="right", padx=10)
        
        ctk.CTkButton(actions_in, text="😊", width=40, height=40, corner_radius=20, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["border"]).pack(side="left")
        
        btn_send = ctk.CTkButton(
            actions_in, text="➤", width=42, height=42, corner_radius=21, 
            fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"], 
            text_color="white", font=font(16, "bold"),
            command=self.enviar_msg
        )
        btn_send.pack(side="left", padx=(5, 0))

    def criar_mensagem(self, text, is_mine, time):
        frame = ctk.CTkFrame(self.msg_area, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        # Alinhamento
        align = "right" if is_mine else "left"
        bubble_color = self.colors["bubble_sent"] if is_mine else self.colors["bubble_recv"]
        text_color = "white" if is_mine else self.colors["text"]
        
        # Outer wrapper for alignment
        wrapper = ctk.CTkFrame(frame, fg_color="transparent")
        wrapper.pack(side=align, padx=10)

        # Bubble
        bubble = ctk.CTkFrame(
            wrapper,
            fg_color=bubble_color,
            corner_radius=18,
            border_width=1 if not is_mine else 0,
            border_color=self.colors["border"] if not is_mine else None
        )
        bubble.pack(side="top")
        
        lbl = ctk.CTkLabel(bubble, text=text, font=font(13), text_color=text_color, wraplength=400, justify="left")
        lbl.pack(padx=15, pady=10)
        
        # Time and Status
        info = ctk.CTkFrame(wrapper, fg_color="transparent")
        info.pack(side="top", fill="x", pady=2)
        
        ctk.CTkLabel(info, text=time, font=font(10), text_color=self.colors["text_highlight"]).pack(side=align)
        if is_mine:
            ctk.CTkLabel(info, text="✓✓", font=font(10), text_color=self.colors["primary"]).pack(side=align, padx=5)

    def enviar_msg(self):
        txt = self.entry_msg.get()
        if txt:
            self.criar_mensagem(txt, True, "Agora")
            self.entry_msg.delete(0, 'end')
            # Scroll to bottom
            self.msg_area._parent_canvas.yview_moveto(1.0)

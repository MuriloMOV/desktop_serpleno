import customtkinter as ctk
from services.mural import ServicoMural
import threading
from datetime import datetime

from ui_theme import THEME, SPACING, RADIUS, font

class QuadroAvisosFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_mural = ServicoMural()

        self.colors = THEME

        # Configuração do layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----- HEADER -----
        self.criar_header()

        # ----- CONTEÚDO PRINCIPAL -----
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(10, 24))
        self.main_container.grid_columnconfigure(0, weight=3) # Feed
        self.main_container.grid_columnconfigure(1, weight=1) # Sidebar (Categorias/Fixados)

        # 1. Feed de Avisos
        self.criar_feed()
        
        # 2. Sidebar Lateral
        self.criar_sidebar()
        
        self.load_messages()

    def criar_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 8))
        
        ctk.CTkLabel(
            header,
            text="Quadro de Avisos",
            font=font(24, "bold"),
            text_color=self.colors["text"]
        ).pack(side="left")

        # Botão Novo Aviso
        ctk.CTkButton(
            header,
            text="+ Novo Comunicado", 
            fg_color=self.colors["primary"],
            hover_color="#4F46E5",
            text_color="white",
            font=font(14, "bold"),
            height=40,
            corner_radius=RADIUS["button"],
            command=self.novo_aviso
        ).pack(side="right")

    def criar_feed(self):
        self.scroll_avisos = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_avisos.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        # Title Section
        ctk.CTkLabel(self.scroll_avisos, text="Últimas Atualizações", font=font(16, "bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(0, 15))

    def criar_sidebar(self):
        sidebar = ctk.CTkFrame(self.main_container, fg_color="transparent")
        sidebar.grid(row=0, column=1, sticky="nsew")
        
        # Card Fixados
        card_fix = ctk.CTkFrame(sidebar, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card_fix.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(card_fix, text="📌 Importante", font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w", padx=15, pady=15)
        
        self.criar_item_fixado(card_fix, "Prazo de Rematrícula", "Até 15/06")
        self.criar_item_fixado(card_fix, "Manutenção no Sistema", "Domingo, 02:00h")

    def criar_item_fixado(self, parent, titulo, info):
        item = ctk.CTkFrame(parent, fg_color="transparent")
        item.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(item, text=titulo, font=font(13, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(item, text=info, font=font(12), text_color=self.colors["text_muted"]).pack(anchor="w")

    def load_messages(self):
        def fetch():
            res = self.servico_mural.listar_mensagens()
            self.after(0, lambda: self.render_messages(res))
        threading.Thread(target=fetch, daemon=True).start()

    def render_messages(self, result):
        # Clear feed content skipping the title
        for w in self.scroll_avisos.winfo_children():
            if isinstance(w, ctk.CTkFrame) and getattr(w, "is_message_card", False):
                w.destroy()
            
        items = []
        if result.get('success'):
            data = result.get('data', [])
            if isinstance(data, list): items = data
            elif isinstance(data, dict): items = data.get('results', [])

        if not items:
            # Mock Items if empty
            items = [
                {"title": "Reunião Pedagógica Semanal", "content": "A reunião ocorrerá na sala 302 às 14h. Pauta: Alinhamento de final de semestre e conselho de classe.", "author": "Coordenação", "date": "10/05/2024", "tag": "Pedagógico"},
                {"title": "Atualização do Sistema", "content": "O sistema passará por instabilidade no dia 12/05 devido à migração de servidores.", "author": "TI Suporte", "date": "09/05/2024", "tag": "Infraestrutura"},
            ]

        for item in items:
            self.criar_card_aviso(item)

    def criar_card_aviso(self, item):
        card = ctk.CTkFrame(self.scroll_avisos, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card.pack(fill="x", pady=10)
        card.is_message_card = True # Marker

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        # Header: Tag + Date
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        tag = item.get('tag') or item.get('category', 'Geral')
        tag_lbl = ctk.CTkLabel(
            header, text=f" {tag} ", fg_color=self.colors["tag_bg"], text_color=self.colors["tag_text"], 
            corner_radius=6, font=font(11, "bold"), height=24
        )
        tag_lbl.pack(side="left")
        
        date = item.get("date") or item.get("created_at") or "Hoje"
        ctk.CTkLabel(header, text=date, font=font(12), text_color=self.colors["text_muted"]).pack(side="right")

        # Title & Content
        ctk.CTkLabel(inner, text=item.get("title", "Sem título"), font=font(16, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(inner, text=item.get("content", ""), font=font(14), text_color=self.colors["text_muted"], wraplength=600, justify="left").pack(anchor="w", pady=(5, 10))

        # Footer: Author
        author = item.get("author", "Sistema")
        footer = ctk.CTkFrame(inner, fg_color="transparent")
        footer.pack(fill="x", pady=(5, 0))
        
        ctk.CTkLabel(footer, text="👤", font=font(14)).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(footer, text=author, font=font(12, "bold"), text_color=self.colors["text"]).pack(side="left")

    def novo_aviso(self):
        print("Novo aviso dialog")

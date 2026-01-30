import customtkinter as ctk
from PIL import Image
import os

class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#F8FAFC") # slate-50
        self.controller = controller
        
        # Cores do Sistema (Tailwind Slate & Indigo)
        self.colors = {
            "bg": "#F8FAFC",
            "card": "#FFFFFF",
            "border": "#E2E8F0",
            "primary": "#6366F1",
            "primary_hover": "#4F46E5",
            "primary_light": "#EEF2FF",
            "text_main": "#1E293B",
            "text_muted": "#64748B",
            "text_highlight": "#94A3B8",
            "success": "#10B981",
            "success_light": "#DCFCE7",
            "warning": "#F59E0B",
            "warning_light": "#FEF3C7",
            "danger": "#EF4444",
            "danger_light": "#FEF2F2",
            "info": "#3B82F6",
            "info_light": "#DBEAFE"
        }

        # Caminhos de imagens
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.img_path = os.path.join(self.base_path, "..", "web_serpleno", "apps", "desktop", "static", "desktop", "img")

        # Layout Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Mock Data
        self.mock_students = [
            {"id": 1, "name": "Ana Beatriz Costa", "course": "Desenv. de Software", "medical_report": True, "alert": False, "contact": "ana.costa@email.com", "age": 21},
            {"id": 2, "name": "Bruno Henrique Souza", "course": "Desenv. de Software", "medical_report": False, "alert": True, "reason": "Ansiedade recorrente", "contact": "bruno.souza@email.com", "age": 23},
            {"id": 3, "name": "Camila Ferreira Santos", "course": "Análise e Desenv.", "medical_report": False, "alert": False, "contact": "camila.santos@email.com", "age": 19},
            {"id": 4, "name": "Diego Martins Almeida", "course": "Gestão Empresarial", "medical_report": True, "alert": True, "reason": "Faltas consecutivas", "contact": "diego.almeida@email.com", "age": 25},
            {"id": 5, "name": "Eduarda Lima Oliveira", "course": "Gestão de TI", "medical_report": False, "alert": False, "contact": "eduarda.lima@email.com", "age": 22},
            {"id": 6, "name": "Rafael Moraes", "course": "Sistemas para Internet", "medical_report": False, "alert": False, "contact": "rafael.moraes@email.com", "age": 20},
        ]

        # Componentes
        self.criar_header()
        
        # Container de Conteúdo (Sidebar + Main)
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.content_container.grid_columnconfigure(1, weight=3)
        self.content_container.grid_rowconfigure(0, weight=1)

        self.criar_sidebar()
        self.criar_detalhes()

        # Seleção Inicial
        self.selecionar_estudante(self.mock_students[0])

    def load_image(self, name, size):
        try:
            path = os.path.join(self.img_path, name)
            if os.path.exists(path):
                return ctk.CTkImage(light_image=Image.open(path), size=size)
        except: pass
        return None

    def criar_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["card"], height=100, corner_radius=20, border_width=1, border_color=self.colors["border"])
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=25)
        header.grid_propagate(False)
        
        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25)

        # Lado Esquerdo
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left")
        
        icon_box = ctk.CTkFrame(info, width=54, height=54, fg_color=self.colors["primary_light"], corner_radius=15)
        icon_box.pack(side="left", padx=(0, 20))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="🎓", font=("Segoe UI", 24)).place(relx=0.5, rely=0.5, anchor="center")
        
        text_v = ctk.CTkFrame(info, fg_color="transparent")
        text_v.pack(side="left")
        ctk.CTkLabel(text_v, text="Gestão de Estudantes", font=("Segoe UI", 20, "bold"), text_color=self.colors["text_main"]).pack(anchor="w")
        ctk.CTkLabel(text_v, text="Acompanhamento e monitoramento discente", font=("Segoe UI", 14), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Lado Direito
        ctk.CTkButton(
            inner, text="+ Novo Estudante", 
            fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"],
            text_color="white", font=("Segoe UI", 14, "bold"),
            height=45, corner_radius=12,
            image=self.load_image("plus.png", (16, 16)) # Supondo que exista ou ignora
        ).pack(side="right")

    def criar_sidebar(self):
        sidebar = ctk.CTkFrame(self.content_container, fg_color=self.colors["card"], width=320, corner_radius=20, border_width=1, border_color=self.colors["border"])
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        sidebar.grid_propagate(False)

        # Busca
        search_frame = ctk.CTkFrame(sidebar, fg_color=self.colors["bg"], height=45, corner_radius=12, border_width=1, border_color=self.colors["border"])
        search_frame.pack(fill="x", padx=20, pady=20)
        search_frame.pack_propagate(False)
        
        ctk.CTkLabel(search_frame, text="🔍", font=("Segoe UI", 14), text_color=self.colors["text_highlight"]).pack(side="left", padx=12)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar estudante...", fg_color="transparent", border_width=0, font=("Segoe UI", 13))
        self.search_entry.pack(side="left", fill="both", expand=True)

        # Lista
        self.scroll_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", corner_radius=0)
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        self.student_items = []
        for i, st in enumerate(self.mock_students):
            self.criar_item_lista(st)

    def criar_item_lista(self, st):
        item = ctk.CTkFrame(self.scroll_list, fg_color="transparent", height=70, corner_radius=12, cursor="hand2")
        item.pack(fill="x", pady=2)
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=10)

        # Sigla do Nome (Avatar circular)
        sigla = st["name"][:2].upper()
        avatar = ctk.CTkLabel(inner, text=sigla, width=40, height=40, corner_radius=20, fg_color=self.colors["bg"], text_color=self.colors["text_muted"], font=("Segoe UI", 12, "bold"))
        avatar.pack(side="left", padx=(0, 12))

        # Textos
        txt_v = ctk.CTkFrame(inner, fg_color="transparent")
        txt_v.pack(side="left", fill="both", expand=True)
        
        lbl_nome = ctk.CTkLabel(txt_v, text=st["name"], font=("Segoe UI", 13, "bold"), text_color=self.colors["text_main"])
        lbl_nome.pack(anchor="w")
        ctk.CTkLabel(txt_v, text=st["course"], font=("Segoe UI", 11), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Badges (Pontos coloridos)
        if st["medical_report"] or st.get("alert"):
            badges = ctk.CTkFrame(inner, fg_color="transparent")
            badges.pack(side="right")
            if st["medical_report"]:
                ctk.CTkFrame(badges, width=8, height=8, corner_radius=4, fg_color=self.colors["info"]).pack(side="left", padx=2)
            if st.get("alert"):
                ctk.CTkFrame(badges, width=8, height=8, corner_radius=4, fg_color=self.colors["danger"]).pack(side="left", padx=2)

        # Bind Click
        def on_click(event, s=st, it=item):
            self.selecionar_estudante(s)
            for other_it in self.student_items: other_it.configure(fg_color="transparent")
            it.configure(fg_color=self.colors["primary_light"])

        item.bind("<Button-1>", on_click)
        for child in item.winfo_children():
            child.bind("<Button-1>", on_click)
            if isinstance(child, ctk.CTkFrame):
                for sub in child.winfo_children(): sub.bind("<Button-1>", on_click)

        self.student_items.append(item)

    def criar_detalhes(self):
        self.detail_card = ctk.CTkFrame(self.content_container, fg_color=self.colors["card"], corner_radius=20, border_width=1, border_color=self.colors["border"])
        self.detail_card.grid(row=0, column=1, sticky="nsew")
        
        # Header Perfil
        self.profile_header = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        self.profile_header.pack(fill="x", padx=40, pady=(40, 30))
        
        # Lado Esquerdo do Perfil (Avatar Grande + Nome)
        left_h = ctk.CTkFrame(self.profile_header, fg_color="transparent")
        left_h.pack(side="left")
        
        self.lbl_avatar_big = ctk.CTkLabel(
            left_h, text="AC", width=80, height=80, corner_radius=40, 
            fg_color=self.colors["primary"], text_color="white", font=("Segoe UI", 28, "bold")
        )
        self.lbl_avatar_big.pack(side="left", padx=(0, 25))
        
        title_v = ctk.CTkFrame(left_h, fg_color="transparent")
        title_v.pack(side="left")
        
        self.lbl_nome_det = ctk.CTkLabel(title_v, text="Ana Beatriz Costa", font=("Segoe UI", 26, "bold"), text_color=self.colors["text_main"])
        self.lbl_nome_det.pack(anchor="w")
        self.lbl_curso_det = ctk.CTkLabel(title_v, text="Desenvolvimento de Software", font=("Segoe UI", 16), text_color=self.colors["text_muted"])
        self.lbl_curso_det.pack(anchor="w")
        
        # Container de Badges (Abaixo do nome)
        self.badge_container = ctk.CTkFrame(title_v, fg_color="transparent")
        self.badge_container.pack(anchor="w", pady=(10, 0))

        # Botões de Ação (Direita do Perfil)
        right_h = ctk.CTkFrame(self.profile_header, fg_color="transparent")
        right_h.pack(side="right", anchor="n")
        
        ctk.CTkButton(right_h, text="Editar", width=90, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["bg"], font=("Segoe UI", 13, "bold"), border_width=1, border_color=self.colors["border"]).pack(side="left", padx=5)
        ctk.CTkButton(right_h, text="Excluir", width=90, fg_color="transparent", text_color=self.colors["danger"], hover_color=self.colors["danger_light"], font=("Segoe UI", 13, "bold")).pack(side="left", padx=5)

        # Tabview
        self.tabs = ctk.CTkTabview(
            self.detail_card, fg_color="transparent", 
            text_color=self.colors["text_muted"], 
            segmented_button_fg_color=self.colors["bg"],
            segmented_button_selected_color=self.colors["primary"],
            segmented_button_selected_hover_color=self.colors["primary_hover"],
            segmented_button_unselected_color=self.colors["bg"],
            segmented_button_unselected_hover_color=self.colors["border"]
        )
        self.tabs.pack(fill="both", expand=True, padx=40, pady=(0, 30))
        
        self.tab_info = self.tabs.add("Informações Pessoais")
        self.tab_hist = self.tabs.add("Histórico de Intervenções")

        # Conteúdo Info
        self.info_grid = ctk.CTkFrame(self.tab_info, fg_color="transparent")
        self.info_grid.pack(fill="both", expand=True, pady=20)
        self.info_grid.grid_columnconfigure((0, 1), weight=1)

        self.card_email = self.criar_info_box(self.info_grid, "CONTATO", "email@email.com", "📧", 0, 0)
        self.card_idade = self.criar_info_box(self.info_grid, "IDADE", "21 anos", "🎂", 0, 1)
        
        # Conteúdo Histórico
        self.hist_scroll = ctk.CTkScrollableFrame(self.tab_hist, fg_color="transparent")
        self.hist_scroll.pack(fill="both", expand=True, pady=10)

    def criar_info_box(self, parent, label, value, icon, r, c):
        box = ctk.CTkFrame(parent, fg_color=self.colors["bg"], corner_radius=15, border_width=1, border_color=self.colors["border"])
        box.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(padx=20, pady=20, fill="both")
        
        ctk.CTkLabel(inner, text=label, font=("Segoe UI", 11, "bold"), text_color=self.colors["text_highlight"]).pack(anchor="w")
        
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(5, 0))
        
        icon_lbl = ctk.CTkLabel(row, text=icon, font=("Segoe UI", 16), width=30)
        icon_lbl.pack(side="left", padx=(0, 10))
        
        val_lbl = ctk.CTkLabel(row, text=value, font=("Segoe UI", 15, "bold"), text_color=self.colors["text_main"])
        val_lbl.pack(side="left")
        
        return val_lbl

    def selecionar_estudante(self, st):
        # Update Info
        self.lbl_nome_det.configure(text=st["name"])
        self.lbl_curso_det.configure(text=st["course"])
        self.lbl_avatar_big.configure(text=st["name"][:2].upper())
        self.card_email.configure(text=st["contact"])
        self.card_idade.configure(text=f"{st['age']} anos")

        # Update Badges
        for child in self.badge_container.winfo_children(): child.destroy()
        
        if st.get("alert"):
            b = self.criar_badge(self.badge_container, f"⚠ {st['reason']}", self.colors["danger"], self.colors["danger_light"])
            b.pack(side="left", padx=(0, 10))
            
        if st["medical_report"]:
            b = self.criar_badge(self.badge_container, "📄 COM LAUDO", self.colors["info"], self.colors["info_light"])
            b.pack(side="left")

        # Update Histórico (Mock)
        for child in self.hist_scroll.winfo_children(): child.destroy()
        
        intervencoes = [
            {"date": "15 de Janeiro, 2026", "notes": "Realizada conversa inicial para acolhimento e escuta ativa sobre desafios no curso."},
            {"date": "10 de Janeiro, 2026", "notes": "Encaminhamento para feedback da coordenação pedagógica sobre aproveitamento acadêmico."}
        ]
        
        for inv in intervencoes:
            card = ctk.CTkFrame(self.hist_scroll, fg_color=self.colors["card"], corner_radius=15, border_width=1, border_color=self.colors["border"])
            card.pack(fill="x", pady=5)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=20, pady=15, fill="x")
            
            icon_c = ctk.CTkFrame(inner, width=40, height=40, corner_radius=20, fg_color=self.colors["success_light"])
            icon_c.pack(side="left", padx=(0, 15))
            icon_c.pack_propagate(False)
            ctk.CTkLabel(icon_c, text="✓", font=("Segoe UI", 16, "bold"), text_color=self.colors["success"]).place(relx=0.5, rely=0.5, anchor="center")
            
            txt_v = ctk.CTkFrame(inner, fg_color="transparent")
            txt_v.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(txt_v, text=inv["date"], font=("Segoe UI", 11, "bold"), text_color=self.colors["text_highlight"]).pack(anchor="w")
            ctk.CTkLabel(txt_v, text=inv["notes"], font=("Segoe UI", 13), text_color=self.colors["text_main"], wraplength=500, justify="left").pack(anchor="w")

    def criar_badge(self, parent, text, color, bg):
        badge = ctk.CTkFrame(parent, fg_color=bg, corner_radius=12, height=26)
        lbl = ctk.CTkLabel(badge, text=text, font=("Segoe UI", 10, "bold"), text_color=color)
        lbl.pack(padx=12, pady=2)
        return badge


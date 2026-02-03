import customtkinter as ctk
from PIL import Image
import os
import threading
from datetime import datetime
from services.estudantes import ServicoEstudante
# Compat alias para testes
StudentService = ServicoEstudante

from ui_theme import THEME, SPACING, RADIUS, font

class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_estudante = ServicoEstudante()

        self.colors = THEME

        
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.img_path = os.path.join(self.base_path, "..", "imagens")

        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        
        self.mock_students = [
            {"id": 1, "name": "Ana Beatriz Costa", "course": "Desenv. de Software", "medical_report": True, "alert": False, "contact": "ana.costa@email.com", "age": 21},
            {"id": 2, "name": "Bruno Henrique Souza", "course": "Desenv. de Software", "medical_report": False, "alert": True, "reason": "Ansiedade recorrente", "contact": "bruno.souza@email.com", "age": 23},
            {"id": 3, "name": "Camila Ferreira Santos", "course": "Análise e Desenv.", "medical_report": False, "alert": False, "contact": "camila.santos@email.com", "age": 19},
            {"id": 4, "name": "Diego Martins Almeida", "course": "Gestão Empresarial", "medical_report": True, "alert": True, "reason": "Faltas consecutivas", "contact": "diego.almeida@email.com", "age": 25},
            {"id": 5, "name": "Eduarda Lima Oliveira", "course": "Gestão de TI", "medical_report": False, "alert": False, "contact": "eduarda.lima@email.com", "age": 22},
            {"id": 6, "name": "Rafael Moraes", "course": "Sistemas para Internet", "medical_report": False, "alert": False, "contact": "rafael.moraes@email.com", "age": 20},
        ]

        self.criar_header()
        
        # Container de Conteúdo
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, 24))
        self.content_container.grid_columnconfigure(1, weight=3)
        self.content_container.grid_rowconfigure(0, weight=1)

        self.criar_sidebar()
        self.criar_detalhes()

        # Carregar Dados
        self.load_data()

    def load_data(self):
        def fetch():
            res = self.servico_estudante.listar_estudantes()
            self.after(0, lambda: self.render_list(res))
        threading.Thread(target=fetch, daemon=True).start()

    def render_list(self, result):
        # Limpar lista
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        self.student_items = []
        students = []

        if result.get('success'):
            data = result.get('data', [])
            if isinstance(data, dict):
                # Prioriza 'students' se existir na chave (mesmo que vazio)
                if 'students' in data:
                    students = data['students']
                else:
                    students = data.get('results', [])
            elif isinstance(data, list):
                students = data
        
        if not students:
            ctk.CTkLabel(self.scroll_list, text="Nenhum estudante encontrado", text_color=self.colors["text_muted"], font=font(12)).pack(pady=20)
            return

        for st in students:
            self.criar_item_lista(st)

        # Selecionar primeiro
        if students:
            self.selecionar_estudante(students[0])

    def load_image(self, name, size):
        try:
            # Simple cache to avoid garbage collection and repeated opens
            if not hasattr(self, "_images"):
                self._images = {}
            cache_key = f"{name}:{size}"
            if cache_key in self._images:
                return self._images[cache_key]

            # Candidate paths: project imagens, bundled assets, fallback
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

    def criar_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 18))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        icon_box = ctk.CTkFrame(inner, width=48, height=48, corner_radius=12, fg_color=self.colors["primary_light"])
        icon_box.pack(side="left", padx=(0, 16))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="🎓", font=font(20), text_color=self.colors["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(inner, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="Gestão de Estudantes", font=font(20, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(text_box, text="Acompanhamento e monitoramento discente", font=font(12), text_color=self.colors["text_muted"]).pack(anchor="w")

        ctk.CTkButton(
            inner, text="+ Novo Estudante", 
            fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"],
            text_color="white", font=font(14, "bold"),
            height=40, corner_radius=RADIUS["button"],
            command=self.novo_estudante_click
        ).pack(side="right")
    
    def novo_estudante_click(self):
        # Abre modal simples para criar estudante
        import tkinter as tk
        from tkinter import messagebox

        modal = ctk.CTkToplevel(self)
        modal.title("Novo Estudante")
        modal.geometry("480x320")
        modal.transient(self)
        modal.grab_set()

        frm = ctk.CTkFrame(modal, fg_color="transparent")
        frm.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frm, text="Nome", font=font(11, "bold")).pack(anchor="w")
        entry_name = ctk.CTkEntry(frm, width=420)
        entry_name.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frm, text="Curso", font=font(11, "bold")).pack(anchor="w")
        entry_course = ctk.CTkEntry(frm, width=420)
        entry_course.pack(fill="x", pady=(4, 10))

        ctk.CTkLabel(frm, text="E-mail de contato", font=font(11, "bold")).pack(anchor="w")
        entry_email = ctk.CTkEntry(frm, width=420)
        entry_email.pack(fill="x", pady=(4, 16))

        btns = ctk.CTkFrame(frm, fg_color="transparent")
        btns.pack(anchor="e")

        def salvar():
            nome = entry_name.get().strip()
            if not nome:
                messagebox.showerror("Erro", "Informe o nome do estudante")
                return
            dados = {
                'nome': nome,
                'email': entry_email.get().strip(),
                'has_medical_report': False,
                'requires_attention': False,
            }
            res = self.servico_estudante.criar_estudante(dados)
            if res.get('success'):
                messagebox.showinfo("Sucesso", res.get('message', 'Estudante criado com sucesso'))
                modal.destroy()
                self.load_data()
            else:
                messagebox.showerror("Erro", res.get('message', 'Erro ao criar estudante'))

        ctk.CTkButton(btns, text="Cancelar", width=120, command=modal.destroy, fg_color="transparent").pack(side="right", padx=8)
        ctk.CTkButton(btns, text="Salvar", width=120, command=salvar, fg_color=self.colors['primary'], text_color='white').pack(side="right")

    def criar_sidebar(self):
        sidebar = ctk.CTkFrame(self.content_container, fg_color=self.colors["card"], width=320, corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        sidebar.grid_propagate(False)

        # Busca
        search_frame = ctk.CTkFrame(sidebar, fg_color=self.colors["bg_alt"], height=45, corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        search_frame.pack(fill="x", padx=20, pady=20)
        search_frame.pack_propagate(False)
        
        ctk.CTkLabel(search_frame, text="🔍", font=font(14), text_color=self.colors["text_highlight"]).pack(side="left", padx=12)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar estudante...", fg_color="transparent", border_width=0, font=font(13))
        self.search_entry.pack(side="left", fill="both", expand=True)

        # Filtros
        filters = ctk.CTkFrame(sidebar, fg_color="transparent")
        filters.pack(fill="x", padx=20, pady=(0, 10))
        filters.grid_columnconfigure((0, 1), weight=1)

        self.filter_medical = ctk.CTkOptionMenu(
            filters,
            values=["Laudos: Todos", "Com Laudo", "Sem Laudo"],
            fg_color=self.colors["bg_alt"],
            button_color=self.colors["bg_alt"],
            button_hover_color=self.colors["border"],
            text_color=self.colors["text_muted"],
            dropdown_fg_color=self.colors["card"],
            dropdown_text_color=self.colors["text"],
            corner_radius=RADIUS["input"],
            height=36,
            font=font(11, "bold")
        )
        self.filter_medical.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.filter_attention = ctk.CTkOptionMenu(
            filters,
            values=["Atenção: Todos", "Requer Atenção", "Normal"],
            fg_color=self.colors["bg_alt"],
            button_color=self.colors["bg_alt"],
            button_hover_color=self.colors["border"],
            text_color=self.colors["text_muted"],
            dropdown_fg_color=self.colors["card"],
            dropdown_text_color=self.colors["text"],
            corner_radius=RADIUS["input"],
            height=36,
            font=font(11, "bold")
        )
        self.filter_attention.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        # Lista
        self.scroll_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", corner_radius=0)
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        ctk.CTkLabel(self.scroll_list, text="Carregando...", text_color=self.colors["text_muted"], font=font(12)).pack(pady=20)

    def criar_item_lista(self, st):
        item = ctk.CTkFrame(self.scroll_list, fg_color="transparent", height=72, corner_radius=RADIUS["input"], cursor="hand2")
        item.pack(fill="x", pady=2)
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=10)

        # Sigla do Nome (Avatar circular)
        name = st.get('name', 'N/A')
        course = st.get('course', 'Sem curso')
        has_medical = st.get('has_medical_report', False)
        alert = st.get('requires_attention', False)

        # Sigla do Nome (Avatar circular)
        sigla = name[:2].upper()
        avatar = ctk.CTkLabel(inner, text=sigla, width=40, height=40, corner_radius=20, fg_color=self.colors["bg_alt"], text_color=self.colors["text_muted"], font=font(12, "bold"))
        avatar.pack(side="left", padx=(0, 12))

        # Textos
        txt_v = ctk.CTkFrame(inner, fg_color="transparent")
        txt_v.pack(side="left", fill="both", expand=True)
        
        lbl_nome = ctk.CTkLabel(txt_v, text=name, font=font(13, "bold"), text_color=self.colors["text"])
        lbl_nome.pack(anchor="w")
        ctk.CTkLabel(txt_v, text=course, font=font(11), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Badges (Pontos coloridos)
        if has_medical or alert:
            badges = ctk.CTkFrame(inner, fg_color="transparent")
            badges.pack(side="right")
            if has_medical:
                ctk.CTkFrame(badges, width=8, height=8, corner_radius=4, fg_color=self.colors["info"]).pack(side="left", padx=2)
            if alert:
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
        self.detail_card = ctk.CTkFrame(self.content_container, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        self.detail_card.grid(row=0, column=1, sticky="nsew")
        
        # Header Perfil
        self.profile_header = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        self.profile_header.pack(fill="x", padx=32, pady=(28, 24))
        
        # Lado Esquerdo do Perfil (Avatar Grande + Nome)
        left_h = ctk.CTkFrame(self.profile_header, fg_color="transparent")
        left_h.pack(side="left")
        
        self.lbl_avatar_big = ctk.CTkLabel(
            left_h, text="AC", width=80, height=80, corner_radius=40, 
            fg_color=self.colors["primary"], text_color="white", font=font(28, "bold")
        )
        self.lbl_avatar_big.pack(side="left", padx=(0, 25))
        
        title_v = ctk.CTkFrame(left_h, fg_color="transparent")
        title_v.pack(side="left")
        
        self.lbl_nome_det = ctk.CTkLabel(title_v, text="Ana Beatriz Costa", font=font(24, "bold"), text_color=self.colors["text"])
        self.lbl_nome_det.pack(anchor="w")
        self.lbl_curso_det = ctk.CTkLabel(title_v, text="Desenvolvimento de Software", font=font(14), text_color=self.colors["text_muted"])
        self.lbl_curso_det.pack(anchor="w")
        
        # Container de Badges (Abaixo do nome)
        self.badge_container = ctk.CTkFrame(title_v, fg_color="transparent")
        self.badge_container.pack(anchor="w", pady=(10, 0))

        # Botões de Ação (Direita do Perfil)
        right_h = ctk.CTkFrame(self.profile_header, fg_color="transparent")
        right_h.pack(side="right", anchor="n")
        
        ctk.CTkButton(
            right_h, text="Editar", width=90, fg_color="transparent", text_color=self.colors["text_muted"],
            hover_color=self.colors["bg_alt"], font=font(12, "bold"), border_width=1, border_color=self.colors["border"],
            corner_radius=RADIUS["button"]
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            right_h, text="Excluir", width=90, fg_color="transparent", text_color=self.colors["danger"],
            hover_color=self.colors["danger_light"], font=font(12, "bold"), corner_radius=RADIUS["button"]
        ).pack(side="left", padx=5)

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
        self.tabs.pack(fill="both", expand=True, padx=32, pady=(0, 24))
        
        self.tab_info = self.tabs.add("Informações Pessoais")
        self.tab_hist = self.tabs.add("Histórico de Intervenções")

        # Conteúdo Info
        self.info_grid = ctk.CTkFrame(self.tab_info, fg_color="transparent")
        self.info_grid.pack(fill="both", expand=True, pady=20)
        self.info_grid.grid_columnconfigure((0, 1), weight=1)

        self.card_email = self.criar_info_box(self.info_grid, "CONTATO", "--", "📧", 0, 0)
        self.card_idade = self.criar_info_box(self.info_grid, "IDADE", "--", "🎂", 0, 1)
        self.card_phone = self.criar_info_box(self.info_grid, "TELEFONE", "--", "📱", 1, 0)
        self.card_emergency = self.criar_info_box(self.info_grid, "EMERGÊNCIA", "--", "🚑", 1, 1)
        
        # Conteúdo Histórico
        self.hist_scroll = ctk.CTkScrollableFrame(self.tab_hist, fg_color="transparent")
        self.hist_scroll.pack(fill="both", expand=True, pady=10)

    def criar_info_box(self, parent, label, value, icon, r, c):
        box = ctk.CTkFrame(parent, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        box.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        
        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(padx=20, pady=20, fill="both")
        
        ctk.CTkLabel(inner, text=label, font=font(11, "bold"), text_color=self.colors["text_highlight"]).pack(anchor="w")
        
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(5, 0))
        
        icon_lbl = ctk.CTkLabel(row, text=icon, font=font(16), width=30)
        icon_lbl.pack(side="left", padx=(0, 10))
        
        val_lbl = ctk.CTkLabel(row, text=value, font=font(15, "bold"), text_color=self.colors["text"])
        val_lbl.pack(side="left")
        return val_lbl

    def selecionar_estudante(self, st_summary):
        # Immediate update with summary data
        name = st_summary.get('name', 'N/A')
        course = st_summary.get('course', 'N/A')
        self.lbl_nome_det.configure(text=name)
        self.lbl_curso_det.configure(text=course)
        self.lbl_avatar_big.configure(text=name[:2].upper())
        
        # Loading indicator/Reset fields
        self.card_email.configure(text=st_summary.get('contact', '--'))
        self.card_idade.configure(text=str(st_summary.get('age', '--')) + " anos")
        self.card_phone.configure(text="Carregando...")
        self.card_emergency.configure(text="Carregando...")

        # Clear Lists
        for child in self.badge_container.winfo_children(): child.destroy()
        for child in self.hist_scroll.winfo_children(): child.destroy()

        # Update Badges (Summary)
        if st_summary.get("requires_attention"):
             reason = st_summary.get("attention_notes") or st_summary.get("attention_reason", "Atenção")
             b = self.criar_badge(self.badge_container, f"⚠ {reason}", self.colors["danger"], self.colors["danger_light"])
             b.pack(side="left", padx=(0, 10))
            
        if st_summary.get("has_medical_report"):
            b = self.criar_badge(self.badge_container, "📄 COM LAUDO", self.colors["info"], self.colors["info_light"])
            b.pack(side="left")

        # Async Fetch Details
        def fetch():
            res = self.servico_estudante.obter_estudante(st_summary['id'])
            self.after(0, lambda: self.update_details(res))
        
        threading.Thread(target=fetch, daemon=True).start()

    def update_details(self, res):
        if not res.get('success'): return
        
        data = res.get('data', {})
        
        # Update Info Fields
        self.card_email.configure(text=data.get('contact', 'N/A'))
        self.card_idade.configure(text=f"{data.get('age', 'N/A')} anos")
        self.card_phone.configure(text=data.get('phone') or "Não informado")
        
        emerg = data.get('emergency_contact')
        phone_emerg = data.get('emergency_phone')
        emerg_text = f"{emerg} ({phone_emerg})" if (emerg and phone_emerg) else (emerg or "Não informado")
        self.card_emergency.configure(text=emerg_text)
        
        # Update Interventions
        interventions = data.get('interventions', [])
        
        if not interventions:
             ctk.CTkLabel(self.hist_scroll, text="Nenhuma intervenção registrada.", text_color=self.colors["text_muted"], font=font(12)).pack(pady=20)
             return

        for inv in interventions:
            card = ctk.CTkFrame(self.hist_scroll, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
            card.pack(fill="x", pady=5)
            
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(padx=20, pady=15, fill="x")
            
            icon_c = ctk.CTkFrame(inner, width=40, height=40, corner_radius=20, fg_color=self.colors["success_light"])
            icon_c.pack(side="left", padx=(0, 15))
            icon_c.pack_propagate(False)
            ctk.CTkLabel(icon_c, text="✓", font=font(16, "bold"), text_color=self.colors["success"]).place(relx=0.5, rely=0.5, anchor="center")
            
            txt_v = ctk.CTkFrame(inner, fg_color="transparent")
            txt_v.pack(side="left", fill="both", expand=True)
            
            # Date Formatting
            date_str = inv.get('date', '')
            try:
                 dt = datetime.fromisoformat(date_str)
                 date_fmt = dt.strftime("%d/%m/%Y")
            except: 
                 date_fmt = date_str

            ctk.CTkLabel(txt_v, text=date_fmt, font=font(11, "bold"), text_color=self.colors["text_highlight"]).pack(anchor="w")
            ctk.CTkLabel(txt_v, text=inv.get('notes', ''), font=font(13), text_color=self.colors["text"], wraplength=400, justify="left").pack(anchor="w")

    def criar_badge(self, parent, text, color, bg):
        badge = ctk.CTkFrame(parent, fg_color=bg, corner_radius=RADIUS["pill"], height=26)
        lbl = ctk.CTkLabel(badge, text=text, font=font(10, "bold"), text_color=color)
        lbl.pack(padx=12, pady=2)
        return badge


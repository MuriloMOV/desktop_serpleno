import customtkinter as ctk
from PIL import Image
import os
import threading
from datetime import datetime
from services.estudantes import ServicoEstudante
from ui_theme import THEME, SPACING, RADIUS, font

class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_estudante = ServicoEstudante()
        self.colors = THEME
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.criar_navbar_superior()
        self.criar_header_secao()
        
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=2, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, 24))
        self.content_container.grid_columnconfigure(1, weight=3)
        self.content_container.grid_rowconfigure(0, weight=1)

        self.criar_sidebar()
        self.criar_detalhes()
        self.load_data()

    def criar_navbar_superior(self):
        nav = ctk.CTkFrame(self, fg_color="transparent", height=50)
        nav.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(10, 0))
        
        ctk.CTkLabel(nav, text="Estudantes", font=font(16, "bold"), text_color=self.colors["text"]).pack(side="left")
        
        actions = ctk.CTkFrame(nav, fg_color="transparent")
        actions.pack(side="right")
        
        icons = [("🤝", "Ajuda"), ("🔔", "Notificações"), ("👤", "Perfil"), ("⏻", "Sair")]
        for icon, tooltip in icons:
            btn = ctk.CTkLabel(actions, text=icon, font=font(18), cursor="hand2", width=40)
            btn.pack(side="left", padx=5)

    def criar_header_secao(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        header.grid(row=1, column=0, sticky="ew", padx=SPACING["page_x"], pady=(20, 18))

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
            inner, text="+", width=40, height=40,
            fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"],
            text_color="white", font=font(20, "bold"),
            corner_radius=RADIUS["button"],
            command=self.novo_estudante_click
        ).pack(side="right")

    def novo_estudante_click(self):
        from tkinter import messagebox
        modal = ctk.CTkToplevel(self)
        modal.title("Adicionar Novo Estudante")
        modal.geometry("550x650")
        modal.configure(fg_color=self.colors["card"])
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        def criar_input(parent, label, placeholder, width_val=None):
            ctk.CTkLabel(parent, text=label, font=font(12, "bold"), text_color=self.colors["text_muted"]).pack(anchor="w", pady=(10, 5))
            entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=40, fg_color=self.colors["bg_alt"], border_width=0)
            entry.pack(fill="x")
            return entry

        en_nome = criar_input(container, "Nome Completo", "Ex: Ana Silva")
        
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=10)
        en_curso = criar_input(row1, "Curso / Turma", "Ex: Psicologia")
        en_idade = criar_input(row1, "Idade", "Ex: 22")
        
        en_email = criar_input(container, "Email de Contato", "email@exemplo.com")

        sw_laudo = ctk.CTkSwitch(container, text="Laudo Médico\nPossui documentação médica?", font=font(12))
        sw_laudo.pack(fill="x", pady=20)
        
        sw_aten = ctk.CTkSwitch(container, text="Requer Atenção\nNecessita de monitoramento prioritário?", font=font(12))
        sw_aten.pack(fill="x", pady=10)

        def salvar():
            if not en_nome.get():
                return messagebox.showerror("Erro", "Nome é obrigatório")
            
            dados = {
                'nome': en_nome.get(),
                'email': en_email.get(),
                'has_medical_report': sw_laudo.get(),
                'requires_attention': sw_aten.get(),
                'course': en_curso.get(),
                'age': en_idade.get()
            }
            if self.servico_estudante.criar_estudante(dados).get('success'):
                modal.destroy()
                self.load_data()

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom", pady=20)
        ctk.CTkButton(btn_box, text="Cancelar", fg_color="transparent", text_color=self.colors["text"], command=modal.destroy).pack(side="left")
        ctk.CTkButton(btn_box, text="Salvar Estudante", fg_color=self.colors["primary"], command=salvar).pack(side="right")

    def criar_sidebar(self):
        sidebar = ctk.CTkFrame(self.content_container, fg_color=self.colors["card"], width=300, corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        sidebar.grid_propagate(False)

        search_frame = ctk.CTkFrame(sidebar, fg_color=self.colors["bg_alt"], height=40, corner_radius=RADIUS["input"])
        search_frame.pack(fill="x", padx=15, pady=15)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar estudante...", fg_color="transparent", border_width=0)
        self.search_entry.pack(fill="both", expand=True, padx=10)

        filter_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        filter_box.pack(fill="x", padx=15)
        
        self.f_laudo = ctk.CTkOptionMenu(filter_box, values=["Laudos: Todos", "Com Laudo", "Sem Laudo"], fg_color=self.colors["bg_alt"], text_color=self.colors["text"], height=30)
        self.f_laudo.pack(side="left", expand=True, padx=(0, 5))
        
        self.f_aten = ctk.CTkOptionMenu(filter_box, values=["Atenção: Todos", "Requer Atenção"], fg_color=self.colors["bg_alt"], text_color=self.colors["text"], height=30)
        self.f_aten.pack(side="left", expand=True, padx=(5, 0))

        self.scroll_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=5, pady=10)

    def criar_detalhes(self):
        self.detail_card = ctk.CTkFrame(self.content_container, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        self.detail_card.grid(row=0, column=1, sticky="nsew")
        
        header = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=25)
        
        self.lbl_avatar_big = ctk.CTkLabel(header, text="AS", width=60, height=60, corner_radius=30, fg_color=self.colors["primary"], text_color="white", font=font(20, "bold"))
        self.lbl_avatar_big.pack(side="left", padx=(0, 15))
        
        info_v = ctk.CTkFrame(header, fg_color="transparent")
        info_v.pack(side="left")
        self.lbl_nome_det = ctk.CTkLabel(info_v, text="Ana Silva", font=font(22, "bold"), text_color=self.colors["text"])
        self.lbl_nome_det.pack(anchor="w")
        self.lbl_curso_det = ctk.CTkLabel(info_v, text="Segurança da Informação", font=font(13), text_color=self.colors["text_muted"])
        self.lbl_curso_det.pack(anchor="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", anchor="n")
        ctk.CTkButton(actions, text="✎ Editar", width=80, fg_color="transparent", text_color=self.colors["text_muted"], border_width=1).pack(side="left", padx=5)
        ctk.CTkButton(actions, text="🗑 Excluir", width=80, fg_color="transparent", text_color=self.colors["danger"]).pack(side="left", padx=5)

        self.tabs = ctk.CTkTabview(self.detail_card, fg_color="transparent", segmented_button_selected_color=self.colors["primary"])
        self.tabs.pack(fill="both", expand=True, padx=30)
        
        self.tab_info = self.tabs.add("Informações Pessoais")
        self.tabs.add("Histórico de Intervenções")
        self.tabs.add("Agendamentos")

        self.info_grid = ctk.CTkFrame(self.tab_info, fg_color="transparent")
        self.info_grid.pack(fill="both", expand=True, pady=10)
        self.info_grid.grid_columnconfigure((0, 1), weight=1)

        self.card_email = self.criar_info_box(self.info_grid, "Contato", "--", "📧", 0, 0)
        self.card_idade = self.criar_info_box(self.info_grid, "Idade", "--", "🎂", 0, 1)
        self.card_curso = self.criar_info_box(self.info_grid, "Curso / Turma", "--", "🎓", 1, 0)
        self.card_laudo = self.criar_info_box(self.info_grid, "Laudo Médico", "--", "📄", 1, 1)

    def criar_info_box(self, parent, label, value, icon, r, c):
        box = ctk.CTkFrame(parent, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["card"], height=80)
        box.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
        box.grid_propagate(False)
        
        ctk.CTkLabel(box, text=label, font=font(10, "bold"), text_color=self.colors["text_muted"]).pack(anchor="w", padx=15, pady=(10, 0))
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=15)
        ctk.CTkLabel(row, text=icon).pack(side="left", padx=(0, 5))
        lbl = ctk.CTkLabel(row, text=value, font=font(13, "bold"))
        lbl.pack(side="left")
        return lbl

    def load_data(self):
        def fetch():
            res = self.servico_estudante.listar_estudantes()
            self.after(0, lambda: self.render_list(res))
        threading.Thread(target=fetch, daemon=True).start()

    def render_list(self, result):
        for widget in self.scroll_list.winfo_children(): widget.destroy()
        students = result.get('data', []) if result.get('success') else []
        
        for st in students:
            item = ctk.CTkFrame(self.scroll_list, fg_color="transparent", height=60, cursor="hand2")
            item.pack(fill="x", pady=2)
            
            lbl_n = ctk.CTkLabel(item, text=st.get('name', 'N/A'), font=font(13, "bold"))
            lbl_n.pack(anchor="w", padx=15, pady=(5, 0))
            lbl_c = ctk.CTkLabel(item, text=st.get('course', 'Sem curso'), font=font(11), text_color=self.colors["text_muted"])
            lbl_c.pack(anchor="w", padx=15)
            
            item.bind("<Button-1>", lambda e, s=st: self.selecionar_estudante(s))

    def selecionar_estudante(self, st):
        self.lbl_nome_det.configure(text=st.get('name', 'N/A'))
        self.lbl_curso_det.configure(text=st.get('course', 'N/A'))
        self.lbl_avatar_big.configure(text=st.get('name', '??')[:2].upper())
        
        self.card_email.configure(text=st.get('contact', '--'))
        self.card_idade.configure(text=f"{st.get('age', '--')} anos")
        self.card_curso.configure(text=st.get('course', '--'))
        self.card_laudo.configure(text="Sim" if st.get('has_medical_report') else "Não")
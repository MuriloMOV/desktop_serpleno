import customtkinter as ctk

class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb") # Background
        self.controller = controller

        # Grid Principal: 2 Colunas 
        # Coluna 0 (1/3): Lista | Coluna 1 (2/3): Detalhes
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Variável para controlar o estudante selecionado (mock)
        self.student_name_var = ctk.StringVar(value="Selecione um estudante")
        self.student_course_var = ctk.StringVar(value="")
        
        self.criar_painel_lista()
        self.criar_painel_detalhes()

    # ================= 1. PAINEL DE LISTA (Esquerda) =================
    def criar_painel_lista(self):
        # Card container
        lista_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        lista_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Layout interno da lista
        lista_frame.grid_rowconfigure(2, weight=1) # Lista em si expande
        lista_frame.grid_columnconfigure(0, weight=1)

        # --- Header ---
        header = ctk.CTkFrame(lista_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="Lista de Estudantes",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#1f2937"
        ).pack(side="left")

        # Botão Novo
        ctk.CTkButton(
            header,
            text="+ Novo",
            width=80,
            fg_color="transparent",
            text_color="#2563EB", # Primary Blue Link Style
            hover=False,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.adicionar_estudante_mock
        ).pack(side="right")

        # --- Busca ---
        self.search_entry = ctk.CTkEntry(
            lista_frame,
            placeholder_text="Buscar estudante...",
            height=35,
            corner_radius=6,
            border_color="#d1d5db"
        )
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))

        # --- Scrollable List ---
        self.scroll_list = ctk.CTkScrollableFrame(lista_frame, fg_color="transparent")
        self.scroll_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 20))

        # Populate Mock Data
        self.mock_students = [
            {"id": 1, "name": "Ana Beatriz Costa", "course": "Desenv. de Software", "medical_report": True, "alert": False},
            {"id": 2, "name": "Bruno Henrique Souza", "course": "Desenv. de Software", "medical_report": False, "alert": True, "reason": "Ansiedade alta recorrente"},
            {"id": 3, "name": "Camila Ferreira Santos", "course": "Análise e Desenv.", "medical_report": False, "alert": False},
            {"id": 4, "name": "Diego Martins Almeida", "course": "Gestão Empresarial", "medical_report": True, "alert": True, "reason": "Faltas consecutivas"},
            {"id": 5, "name": "Eduarda Lima Oliveira", "course": "Gestão de TI", "medical_report": False, "alert": False},
            {"id": 6, "name": "Rafael Moraes", "course": "Sistemas para Internet", "medical_report": False, "alert": False},
        ]

        for st in self.mock_students:
            self.criar_item_estudante(st)

    def criar_item_estudante(self, student):
        # Card item
        item = ctk.CTkFrame(self.scroll_list, fg_color="#f9fafb", corner_radius=6) # gray-50
        item.pack(fill="x", pady=4)
        
        # Click handler (bind no frame e nos labels)
        handler = lambda event=None, s=student: self.selecionar_estudante(s)
        item.bind("<Button-1>", handler)

        # Info Esquerda
        info_frame = ctk.CTkFrame(item, fg_color="transparent")
        info_frame.pack(side="left", padx=10, pady=10)
        info_frame.bind("<Button-1>", handler)

        name_lbl = ctk.CTkLabel(info_frame, text=student["name"], font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="#1f2937")
        name_lbl.pack(anchor="w")
        name_lbl.bind("<Button-1>", handler)

        course_lbl = ctk.CTkLabel(info_frame, text=student["course"], font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#6b7280")
        course_lbl.pack(anchor="w")
        course_lbl.bind("<Button-1>", handler)

        # Ícones à Direita
        icon_frame = ctk.CTkFrame(item, fg_color="transparent")
        icon_frame.pack(side="right", padx=10)
        
        if student["medical_report"]:
            # Icon mock "file-medical"
            lbl = ctk.CTkLabel(icon_frame, text="📄", text_color="#3b82f6", font=ctk.CTkFont(size=14)) # Blue icon
            lbl.pack(side="left", padx=2)
        
        if student.get("alert"):
             # Icon mock "warning"
            lbl = ctk.CTkLabel(icon_frame, text="⚠️", text_color="#ef4444", font=ctk.CTkFont(size=14)) # Red icon
            lbl.pack(side="left", padx=2)

    # ================= 2. PAINEL DE DETALHES (Direita) =================
    def criar_painel_detalhes(self):
        # Container Principal
        self.painel_detalhe = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        self.painel_detalhe.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        # Estado Vazio Inicial ou Conteúdo
        # Vamos criar o conteiner de conteúdo e manipulá-lo
        
        # Layout interno
        self.painel_detalhe.grid_columnconfigure(0, weight=1)
        self.painel_detalhe.grid_rowconfigure(2, weight=1) # Conteúdo expande

        # --- Header Detalhes ---
        header_det = ctk.CTkFrame(self.painel_detalhe, fg_color="transparent")
        header_det.grid(row=0, column=0, sticky="ew", padx=25, pady=25)

        self.lbl_detalhe_nome = ctk.CTkLabel(
            header_det, 
            text="Selecione um estudante", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#111827"
        )
        self.lbl_detalhe_nome.pack(side="left")

        # Badge de Alerta (inicialmente oculto)
        self.alert_badge = ctk.CTkButton(
            header_det,
            text="",
            fg_color="#fee2e2", # red-100 (ajustado dynamic)
            text_color="#991b1b",
            hover=False,
            height=24,
            corner_radius=12,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        # self.alert_badge.pack(side="left", padx=10) # Show dynamically

        # Botão Fechar (Visual apenas, pois é layout fixo divido, mas pode "limpar" a seleção)
        ctk.CTkButton(
            header_det,
            text="✕",
            width=30,
            fg_color="transparent",
            text_color="#9ca3af",
            hover_color="#f3f4f6",
            command=self.limpar_selecao
        ).pack(side="right")

        # --- Abas (Tabs) ---
        self.tab_view = ctk.CTkTabview(self.painel_detalhe, fg_color="transparent")
        self.tab_view.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Add Tabs
        self.tab_info = self.tab_view.add("Informações")
        self.tab_interv = self.tab_view.add("Intervenções")

        # -- Conteúdo Info --
        self.lbl_info_curso = ctk.CTkLabel(self.tab_info, text="", anchor="w", text_color="#4b5563")
        self.lbl_info_curso.pack(fill="x", pady=5)
        
        self.lbl_info_idade = ctk.CTkLabel(self.tab_info, text="", anchor="w", text_color="#4b5563")
        self.lbl_info_idade.pack(fill="x", pady=5)
        
        self.lbl_info_contato = ctk.CTkLabel(self.tab_info, text="", anchor="w", text_color="#4b5563")
        self.lbl_info_contato.pack(fill="x", pady=5)
        
        self.lbl_info_laudo = ctk.CTkLabel(self.tab_info, text="", anchor="w", text_color="#4b5563")
        self.lbl_info_laudo.pack(fill="x", pady=5)

        # -- Conteúdo Intervenções --
        self.interv_container = ctk.CTkScrollableFrame(self.tab_interv, fg_color="transparent")
        self.interv_container.pack(fill="both", expand=True)
        # Placeholder
        ctk.CTkLabel(self.interv_container, text="Selecione um estudante para ver histórico.", text_color="#9ca3af").pack(pady=20)

    # ================= LÓGICA =================
    def selecionar_estudante(self, student):
        # Update Header
        self.lbl_detalhe_nome.configure(text=student["name"])

        # Update Badge
        self.alert_badge.pack_forget() # Reset
        if student.get("alert"):
            self.alert_badge.configure(text=student.get("reason", "Atenção"), fg_color="#fee2e2", text_color="#991b1b") # red style
            self.alert_badge.pack(side="left", padx=15)
        
        # Update Infos (Mock Data)
        self.lbl_info_curso.configure(text=f"Curso: {student['course']}")
        self.lbl_info_idade.configure(text=f"Idade: 20 anos (Mock)")
        self.lbl_info_contato.configure(text=f"Contato: (11) 99999-9999")
        
        laudo_text = "Sim" if student["medical_report"] else "Não"
        self.lbl_info_laudo.configure(text=f"Laudo Médico: {laudo_text}")

        # Update Interventions (Mock)
        for widget in self.interv_container.winfo_children():
            widget.destroy()

        if student.get("alert"):
            # Mock intervention list
            self.add_intervention_item("23/01/2026", "Encaminhamento para psicólogo externo.")
            self.add_intervention_item("15/01/2026", "Conversa inicial sobre desempenho acadêmico.")
        else:
            ctk.CTkLabel(self.interv_container, text="Nenhuma intervenção registrada recentes.", text_color="#6b7280").pack(pady=10)

    def add_intervention_item(self, data, texto):
        frame = ctk.CTkFrame(self.interv_container, fg_color="#f9fafb", corner_radius=6)
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame, text=data, font=ctk.CTkFont(weight="bold"), text_color="#374151").pack(anchor="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(frame, text=texto, text_color="#4b5563", wraplength=400).pack(anchor="w", padx=10, pady=(2, 10))

    def limpar_selecao(self):
        self.lbl_detalhe_nome.configure(text="Selecione um estudante")
        self.alert_badge.pack_forget()
        self.lbl_info_curso.configure(text="")
        self.lbl_info_idade.configure(text="")
        self.lbl_info_contato.configure(text="")
        self.lbl_info_laudo.configure(text="")
        
        for widget in self.interv_container.winfo_children():
            widget.destroy()

    def adicionar_estudante_mock(self):
        print("Abrir modal de adicionar estudante...")

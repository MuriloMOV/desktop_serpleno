import customtkinter as ctk

class OrientacoesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#F3F4F6") # tailwind gray-100
        self.controller = controller

        # Grid Layout: 1/4 Left (Students), 3/4 Right (Content)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # ============= Left Panel: Students List =============
        self.criar_painel_alunos()

        # ============= Right Panel: Content/Builder =============
        self.criar_painel_conteudo()

    def criar_painel_alunos(self):
        panel = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        
        # Header
        ctk.CTkLabel(
            panel, 
            text="Estudantes", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#1F2937"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Search Input
        self.search_entry = ctk.CTkEntry(
            panel,
            placeholder_text="Filtrar alunos...",
            height=35,
            corner_radius=6,
            border_color="#D1D5DB",
            bg_color="transparent",
            fg_color="white",
            text_color="#374151"
        )
        self.search_entry.pack(fill="x", padx=20, pady=(0, 10))

        # List Container
        self.student_list = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        self.student_list.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        # Mock Data
        students = ["Ana Beatriz", "Bruno Henrique", "Camila Ferreira", "Diego Martins", "Eduarda Lima"]
        for st in students:
            btn = ctk.CTkButton(
                self.student_list,
                text=st,
                fg_color="transparent",
                text_color="#374151",
                hover_color="#F3F4F6",
                anchor="w",
                height=30,
                command=lambda s=st: self.selecionar_aluno(s)
            )
            btn.pack(fill="x", pady=2)

    def criar_painel_conteudo(self):
        # Main Right Container
        self.content_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.content_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        
        # Header Row
        header = ctk.CTkFrame(self.content_panel, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text="Construtor de Orientações", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#1F2937"
        ).pack(side="left")

        # Buttons
        btns = ctk.CTkFrame(header, fg_color="transparent")
        btns.pack(side="right")

        ctk.CTkButton(
            btns,
            text="Exportar JSON",
            fg_color="transparent",
            border_width=1,
            border_color="#6D28D9",
            text_color="#6D28D9",
            hover_color="#F3F4F6",
            width=100
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btns,
            text="Salvar Local",
            fg_color="#6D28D9", # purple-700
            text_color="white",
            hover_color="#5B21B6",
            width=100
        ).pack(side="left", padx=5)

        # Scrollable Content Area
        self.scroll_content = ctk.CTkScrollableFrame(self.content_panel, fg_color="transparent")
        self.scroll_content.pack(fill="both", expand=True)

        # 1. Preview Area (Mock)
        self.criar_secao_preview()

        # 2. Dynamic Content Area (Mock Loaded Data)
        self.criar_orientacao_dinamica()

        # 3. Motivational Message
        self.criar_mensagem_motivacional()

        # 4. JSON Debug (TextArea)
        ctk.CTkLabel(
            self.scroll_content,
            text="Dados Atuais / Template",
            font=ctk.CTkFont(weight="bold", size=14),
            text_color="#374151"
        ).pack(anchor="w", pady=(20, 5))

        self.json_box = ctk.CTkTextbox(
            self.scroll_content,
            height=100,
            fg_color="white",
            border_color="#D1D5DB",
            border_width=1,
            text_color="#374151"
        )
        self.json_box.pack(fill="x")
        self.json_box.insert("0.0", "{ 'id': 123, 'student': 'Bruno', 'theme': 'Ansiedade' ... }")

    def criar_secao_preview(self):
        f = ctk.CTkFrame(self.scroll_content, fg_color="transparent")
        f.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(f, text="Pré-visualização (arraste para reordenar)", font=ctk.CTkFont(weight="bold", size=14), text_color="#374151").pack(anchor="w", pady=(0, 5))
        
        preview_box = ctk.CTkFrame(f, fg_color="white", border_width=1, border_color="#E5E7EB", corner_radius=6, height=100)
        preview_box.pack(fill="x")
        
        ctk.CTkLabel(preview_box, text="(Área de Drag & Drop)", text_color="#9CA3AF").place(relx=0.5, rely=0.5, anchor="center")

    def criar_orientacao_dinamica(self):
        self.dynamic_frame = ctk.CTkFrame(self.scroll_content, fg_color="#F9FAFB", corner_radius=8, border_width=1, border_color="#E5E7EB")
        self.dynamic_frame.pack(fill="x", pady=(0, 20))
        
        # Default Content
        self.content_title = ctk.CTkLabel(self.dynamic_frame, text="Nenhuma orientação selecionada", font=ctk.CTkFont(weight="bold", size=16), text_color="#1F2937")
        self.content_title.pack(anchor="w", padx=20, pady=(20, 5))
        
        self.content_text = ctk.CTkLabel(self.dynamic_frame, text="Selecione um aluno para ver os detalhes.", text_color="#6B7280", wraplength=600, justify="left")
        self.content_text.pack(anchor="w", padx=20, pady=(0, 20))

    def criar_mensagem_motivacional(self):
        msg_frame = ctk.CTkFrame(self.scroll_content, fg_color="#EFF6FF", corner_radius=10, border_width=1, border_color="#BFDBFE") # blue-50, border-blue-200
        msg_frame.pack(fill="x", pady=(0, 20))
        
        self.msg_text = ctk.CTkLabel(
            msg_frame, 
            text='"Lembre-se: acolher seus sentimentos é o primeiro passo para cuidar da sua saúde mental. Estarei com você nessa jornada."',
            font=ctk.CTkFont(family="Segoe UI", size=14, slant="italic"),
            text_color="#1E40AF", # blue-800
            wraplength=600
        )
        self.msg_text.pack(anchor="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(
            msg_frame,
            text="— Psicóloga",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#1D4ED8" # blue-700
        ).pack(anchor="w", padx=20, pady=(0, 15))

    def selecionar_aluno(self, nome):
        # Update UI Mock
        self.content_title.configure(text=f"Orientação Recente - {nome}")
        self.content_text.configure(text=f"Tema: Ansiedade\nData: 23/01/2026\n\nConteúdo:\nO aluno relatou melhorias significativas após a aplicação da técnica de respiração diafragmática sugerida na última sessão.")
        print(f"Aluno selecionado: {nome}")

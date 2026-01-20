import customtkinter as ctk


class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        self.criar_lista_estudantes()
        self.criar_detalhes_estudante()

    # ================= LISTA =================
    def criar_lista_estudantes(self):
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text="Lista de Estudantes",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Novo",
            width=80,
            fg_color="#6d28d9",
            hover_color="#5b21b6"
        ).pack(side="right")

        # Busca
        ctk.CTkEntry(
            container,
            placeholder_text="Buscar estudante..."
        ).pack(fill="x", padx=20, pady=(0, 15))

        # Lista
        lista = ctk.CTkFrame(container, fg_color="transparent")
        lista.pack(fill="both", expand=True, padx=10)

        estudantes = [
            ("Ana Beatriz Costa", "Desenvolvimento de Software"),
            ("Bruno Henrique Souza", "Desenvolvimento de Software"),
            ("Camila Ferreira Santos", "Análise e Desenvolvimento"),
            ("Diego Martins Almeida", "Gestão Empresarial"),
            ("Eduarda Lima Oliveira", "Gestão de TI"),
            ("Rafael Moraes", "Desenvolvimento de Sistemas"),
        ]

        for nome, curso in estudantes:
            item = ctk.CTkButton(
                lista,
                text=f"{nome}\n{curso}",
                anchor="w",
                height=55,
                fg_color="#f9fafb",
                text_color="#111827",
                hover_color="#ede9fe",
                command=lambda n=nome: self.selecionar_estudante(n)
            )
            item.pack(fill="x", padx=10, pady=5)

    # ================= DETALHES =================
    def criar_detalhes_estudante(self):
        self.detalhes = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        self.detalhes.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        # Header
        header = ctk.CTkFrame(self.detalhes, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(20, 10))

        self.nome_label = ctk.CTkLabel(
            header,
            text="Rafael Moraes",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.nome_label.pack(side="left")

        ctk.CTkButton(
            header,
            text="✕",
            width=32,
            fg_color="transparent",
            text_color="#6b7280",
            hover_color="#f3f4f6"
        ).pack(side="right")

        # Tabs
        tabs = ctk.CTkFrame(self.detalhes, fg_color="transparent")
        tabs.pack(fill="x", padx=25, pady=(0, 15))

        ctk.CTkButton(
            tabs, text="Informações",
            fg_color="transparent",
            text_color="#6d28d9"
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            tabs, text="Intervenções",
            fg_color="transparent",
            text_color="#6b7280"
        ).pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            tabs, text="Agendamentos",
            fg_color="transparent",
            text_color="#6b7280"
        ).pack(side="left")

        # Conteúdo
        info = ctk.CTkFrame(self.detalhes, fg_color="transparent")
        info.pack(fill="both", expand=True, padx=25)

        dados = [
            ("🎓 Curso:", "Desenvolvimento de Sistemas"),
            ("🎂 Idade:", "22 anos"),
            ("✉️ Contato:", "rafael@email.com"),
            ("📄 Laudo Médico:", "Sim"),
            ("📅 Cadastrado em:", "05/12/2025"),
        ]

        for label, valor in dados:
            linha = ctk.CTkFrame(info, fg_color="transparent")
            linha.pack(fill="x", pady=8)

            ctk.CTkLabel(
                linha,
                text=label,
                font=ctk.CTkFont(weight="bold"),
                width=180,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                linha,
                text=valor,
                text_color="#374151"
            ).pack(side="left")

    # ================= AÇÕES =================
    def selecionar_estudante(self, nome):
        self.nome_label.configure(text=nome)

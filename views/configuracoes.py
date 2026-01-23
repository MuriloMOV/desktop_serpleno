import customtkinter as ctk

class ConfiguracoesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller

        # Configuração do layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----- HEADER -----
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        
        self.titulo = ctk.CTkLabel(
            self.header_frame,
            text="Quadro de Avisos",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#111827"
        )
        self.titulo.pack(side="left")

        self.btn_novo_aviso = ctk.CTkButton(
            self.header_frame,
            text=" Novo Aviso", # Espaço para o "ícone"
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8
        )
        self.btn_novo_aviso.pack(side="right")

        # ----- CONTEÚDO PRINCIPAL -----
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=1, column=0, sticky="nsew", padx=30, pady=(10, 30))
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Lista de avisos
        self.scroll_avisos = ctk.CTkScrollableFrame(self.main_container, fg_color="white", corner_radius=15, border_width=1, border_color="#e5e7eb")
        self.scroll_avisos.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            self.scroll_avisos, 
            text="Avisos Recentes", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

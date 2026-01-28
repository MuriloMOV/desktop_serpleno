import customtkinter as ctk

class ChatInternoFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#F0F2F5") 
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=1) 

        self.criar_layout()

    def criar_layout(self):
        # --- CABEÇALHO ---
        header_tela = ctk.CTkFrame(self, fg_color="transparent")
        header_tela.grid(row=0, column=0, sticky="ew", padx=30, pady=(15, 5))

        ctk.CTkLabel(
            header_tela,
            text="Comunicação Interna",
            font=ctk.CTkFont(family="Arial", size=22, weight="bold"),
            text_color="#111827"
        ).pack(side="left")

        # --- CONTAINER DO CONTEÚDO ---
        container_chat = ctk.CTkFrame(self, fg_color="transparent")
        container_chat.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # AJUSTE DE RESPONSIVIDADE AQUI:
        # Coluna 0 (Contatos) terá 1 parte do espaço
        container_chat.grid_columnconfigure(0, weight=1, minsize=250) 
        # Coluna 1 (Chat) terá 3 partes do espaço (será sempre maior)
        container_chat.grid_columnconfigure(1, weight=3) 
        container_chat.grid_rowconfigure(0, weight=1)

        # --- 1. BARRA LATERAL DE MENSAGENS (RESPONSIVA) ---
        # Removi o 'width' fixo para ela poder obedecer ao weight
        sidebar_contatos = ctk.CTkFrame(container_chat, fg_color="white", corner_radius=15)
        sidebar_contatos.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        # Importante: NÃO use grid_propagate(False) se quiser que ela estique livremente

        ctk.CTkLabel(
            sidebar_contatos, 
            text="Mensagens", 
            font=("Arial", 18, "bold"),
            text_color="black"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        busca = ctk.CTkEntry(
            sidebar_contatos, 
            placeholder_text="Buscar conversas...", 
            height=35, 
            corner_radius=20,
            fg_color="#F3F4F6",
            border_width=0
        )
        busca.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            sidebar_contatos, 
            text="Nenhum contato encontrado.", 
            text_color="gray",
            font=("Arial", 12)
        ).pack(pady=40)

        # --- 2. ÁREA DE CONVERSA (RESPONSIVA) ---
        area_conversa = ctk.CTkFrame(container_chat, fg_color="#FCFBF8", corner_radius=15)
        area_conversa.grid(row=0, column=1, sticky="nsew")

        # Header interno
        header_conversa = ctk.CTkFrame(area_conversa, height=60, fg_color="white", corner_radius=15)
        header_conversa.pack(fill="x", side="top", padx=2, pady=2)
        header_conversa.pack_propagate(False)

        info_contato = ctk.CTkLabel(header_conversa, text="Selecione um contato", font=("Arial", 15, "bold"), text_color="black")
        info_contato.pack(side="left", padx=20)
        
        # Barra de entrada inferior
        entrada_container = ctk.CTkFrame(area_conversa, fg_color="white", height=60, corner_radius=15)
        entrada_container.pack(fill="x", side="bottom", padx=10, pady=10)
        
        entrada_msg = ctk.CTkEntry(entrada_container, placeholder_text="Digite sua mensagem...", height=40, corner_radius=10)
        entrada_msg.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=10)

        btn_enviar = ctk.CTkButton(entrada_container, text="Enviar", width=80, height=40)
        btn_enviar.pack(side="right", padx=(0, 20), pady=10)
import customtkinter as ctk
from PIL import Image

class RelatorioFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=1) 

        self.criar_layout()

    def criar_layout(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 15))

        ctk.CTkLabel(
            header,
            text="Relatórios",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#111827"
        ).pack(side="left") 

        self.criar_cards()

    def criar_cards(self):
        container_cards = ctk.CTkFrame(self, fg_color="transparent")
        container_cards.grid(row=1, column=0, sticky="new", padx=22, pady=(0, 24))

        # Tente carregar as imagens (mude para caminhos reais ou use try/except)
        try:
            img_geral = ctk.CTkImage(light_image=Image.open("assets/icone_geral.png"), size=(20, 20))
            img_agenda = ctk.CTkImage(light_image=Image.open("assets/icone_agenda.png"), size=(20, 20))
        except:
            img_geral = None
            img_agenda = None

        for i in range(4):
            container_cards.grid_columnconfigure(i, weight=1)

        self.card(container_cards, "Relatório Geral", "10", "#3b82f6", icone=img_geral).grid(row=0, column=0, padx=8, sticky="ew")
        self.card(container_cards, "Agendamentos", "4", "#10b981", icone=img_agenda).grid(row=0, column=1, padx=8, sticky="ew")
        self.card(container_cards, "Intervenções", "8", "#8B5CF6").grid(row=0, column=2, padx=8, sticky="ew")
        self.card(container_cards, "Triagens", "12", "#f59e0b").grid(row=0, column=3, padx=8, sticky="ew")

    def card(self, parent, titulo, valor, cor, icone=None):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        
        # Frame para alinhar Título e Ícone
        header_card = ctk.CTkFrame(frame, fg_color="transparent")
        header_card.pack(fill="x", padx=16, pady=(14, 0)) # Reduzi o pady inferior

        if icone:
            ctk.CTkLabel(header_card, text="", image=icone).pack(side="right")

        ctk.CTkLabel(
            header_card, # MUDANÇA: Agora o pai é header_card
            text=titulo,
            text_color="#020202",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            frame,
            text=valor,
            text_color=cor,
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w", padx=16, pady=(5, 14))

        return frame
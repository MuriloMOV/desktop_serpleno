import customtkinter as ctk
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class RelatorioFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        # Fundo cinza claro padrão
        super().__init__(parent, fg_color="#F8F9FA") 
        self.controller = controller

        # --- Configuração Dos ÍCONES ---

        img_path = "ser_pleno/assets/icons/relatorio_geral_icon.png"
        img_path2 = "ser_pleno/assets/icons/calendario_icon.png"
        img_path3 = "ser_pleno/assets/icons/intervencao_icon.png"
        img_path4 = "ser_pleno/assets/icons/triagem_icon.png"

        img_data = Image.open(img_path)
        img_data2 = Image.open(img_path2)
        img_data3 = Image.open(img_path3)
        img_data4 = Image.open(img_path4)

        self.icon_geral = ctk.CTkImage(img_data, size=(22, 22))
        self.icon_agenda = ctk.CTkImage(img_data2, size=(22, 22)) 
        self.icon_interv = ctk.CTkImage(img_data3, size=(22, 22))
        self.icon_triagem = ctk.CTkImage(img_data4, size=(22, 22))

        # --- CONFIGURAÇÃO DE RESPONSIVIDADE (GRID) ---
        self.grid_columnconfigure(0, weight=1) # Coluna principal expande
        
        # Linhas: 0 e 1 (Header/Cards) são fixas. 2 e 3 (Gráfico/Lista) expandem.
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=0) 
        self.grid_rowconfigure(2, weight=1) # Espaço para o gráfico/resumo
        self.grid_rowconfigure(3, weight=2) # Espaço maior para a lista de relatórios

        self.criar_layout()

    def criar_layout(self):
        # --- BLOCO 1: CABEÇALHO ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(25, 15))

        ctk.CTkLabel(
            header,
            text="Relatórios",
            font=ctk.CTkFont(family="Arial", size=24, weight="bold"),
            text_color="#111827"
        ).pack(side="left") 

        ctk.CTkButton(
            header,
            text="Gerar Relatório",
            fg_color="#4f46e5",
            hover_color="#2E2EA7",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=35
        ).pack(side="right")

        self.criar_cards()
        self.criar_secao_inferior()
        self.criar_lista_relatorios()

    def criar_cards(self):
        """Cria a fileira de 4 cards responsivos"""
        container_cards = ctk.CTkFrame(self, fg_color="transparent")
        container_cards.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 24))

        # Configura as 4 colunas dos cards para expandirem igualmente
        for i in range(4):
            container_cards.grid_columnconfigure(i, weight=1)

        # sticky="ew" garante que o card preencha a largura da sua coluna
        self.card(container_cards, "Relatório Geral", "Visão completa", "Geral", "#D0E1FD", self.icon_geral).grid(row=0, column=0, padx=8, sticky="ew")
        self.card(container_cards, "Agendamentos", "Análise de consultas", "Agendamentos", "#D1FADF",self.icon_agenda).grid(row=0, column=1, padx=8, sticky="ew")
        self.card(container_cards, "Intervenções", "Acompanhamentos", "Intervenções", "#EBE9FE",self.icon_interv).grid(row=0, column=2, padx=8, sticky="ew")
        self.card(container_cards, "Triagens", "Análise de triagens", "Triagens", "#FEF0C7",self.icon_triagem).grid(row=0, column=3, padx=8, sticky="ew")

    def card(self, parent, titulo, subtitulo, categoria, cor_fundo_icone, imagem_icone):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12, border_width=1, border_color="#EAEAEA")
        frame.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(frame, width=42, height=42, fg_color=cor_fundo_icone, corner_radius=8)
        icon_box.grid(row=0, column=0, rowspan=3, padx=(15, 12), pady=15)
        icon_box.grid_propagate(False)

        label_foto = ctk.CTkLabel(icon_box, text="", image=imagem_icone)
        label_foto.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame, text=categoria, text_color="#9DA1A7",
            font=ctk.CTkFont(family="Arial", size=11)
        ).grid(row=0, column=1, sticky="ne", padx=15, pady=10) 

        ctk.CTkLabel(
            frame, text=titulo, text_color="#1A1C1E",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold")
        ).grid(row=1, column=1, sticky="nw")

        ctk.CTkLabel(
            frame, text=subtitulo, text_color="#6F767E",
            font=ctk.CTkFont(family="Arial", size=12)
        ).grid(row=2, column=1, sticky="nw", padx=(0, 15), pady=(0, 15))
        
        return frame

    def criar_secao_inferior(self):
        container_inferior = ctk.CTkFrame(self, fg_color="transparent")
        container_inferior.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
        
        # Gráfico (weight 3) ocupa mais espaço que o Resumo (weight 1)
        container_inferior.grid_columnconfigure(0, weight=3)
        container_inferior.grid_columnconfigure(1, weight=1)
        container_inferior.grid_rowconfigure(0, weight=1)

        chart_box = ctk.CTkFrame(container_inferior, fg_color="white", corner_radius=12, border_width=1, border_color="#EAEAEA")
        chart_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        summary_box = ctk.CTkFrame(container_inferior, fg_color="white", corner_radius=12, border_width=1, border_color="#EAEAEA")
        summary_box.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(
            chart_box, text="Atividades Nos Últimos 30 dias", 
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="nw", padx=20, pady=15)

        self.desenhar_grafico(chart_box)
        
        ctk.CTkLabel(
            summary_box, text="Resumo", 
            font=ctk.CTkFont(family="Arial", size=16, weight="bold"),
            text_color="#111827"
        ).pack(anchor="nw", padx=25, pady=(20, 10))

        itens = [
            ("Total de Estudantes", "0"),
            ("Consultas (30d)", "0"),
            ("Intervenções (30d)", "0"),
            ("Triagens (30d)", "0"),
        ]

        for texto, valor in itens:
            self.item_resumo(summary_box, texto, valor)

        divisor = ctk.CTkFrame(summary_box, fg_color="#EAEAEA", height=1)
        divisor.pack(fill="x", padx=25, pady=15)

        self.item_resumo(summary_box, "Taxa de Comparecimento", "0%", cor_valor="#10B981")

    def item_resumo(self, parent, texto, valor, cor_valor="#1A1C1E"):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=4)
        ctk.CTkLabel(f, text=texto, text_color="#6B7280", font=ctk.CTkFont(size=13)).pack(side="left")
        ctk.CTkLabel(f, text=valor, text_color=cor_valor, font=ctk.CTkFont(size=13, weight="bold")).pack(side="right")
        
    def criar_lista_relatorios(self):
        # sticky="nsew" faz o box preencher toda a Row 3
        container_lista = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#EAEAEA")
        container_lista.grid(row=3, column=0, sticky="nsew", padx=30, pady=(10, 30))
        
        header_lista = ctk.CTkFrame(container_lista, fg_color="transparent")
        header_lista.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            header_lista, text="Relatórios Gerados", 
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#111827"
        ).pack(side="left")

        # Botão de Filtro
        ctk.CTkButton(
            header_lista, text="Todos os tipos", fg_color="white", text_color="#6B7280",
            border_width=1, border_color="#EAEAEA", hover_color="#F9FAFB", width=120, height=32
        ).pack(side="right", padx=5)

        ctk.CTkFrame(container_lista, fg_color="#EAEAEA", height=1).pack(fill="x")

        # --- ESTADO VAZIO RESPONSIVO ---
        empty_state = ctk.CTkFrame(container_lista, fg_color="transparent")
        empty_state.pack(expand=True, fill="both") 

        # O segredo: centraliza o conteúdo horizontal e verticalmente
        content_center = ctk.CTkFrame(empty_state, fg_color="transparent")
        content_center.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(content_center, text="📄", font=ctk.CTkFont(size=40)).pack(pady=5)
        ctk.CTkLabel(
            content_center, text="Nenhum relatório gerado ainda",
            font=ctk.CTkFont(size=14), text_color="#6B7280"
        ).pack(pady=(0, 15))

        ctk.CTkButton(
            content_center, text="+ Gerar Primeiro Relatório",
            fg_color="#5D5FEF", hover_color="#4A49D1",
            font=ctk.CTkFont(size=13, weight="bold"), height=38, corner_radius=8
        ).pack()

    def desenhar_grafico(self, parent):

        fig, ax = plt.subplots(figsize=(8, 2.5), dpi=100)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')

        # Configurações de escala
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        
        # Estilização das bordas (spines)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#EAEAEA')
        ax.spines['bottom'].set_color('#EAEAEA')

        # Grade horizontal suave
        ax.yaxis.grid(True, linestyle='-', linewidth=0.5, color='#EAEAEA')
        ax.set_axisbelow(True)

        # Labels e Ticks
        ax.tick_params(axis='both', which='major', labelsize=8, colors='#6B7280')
        ax.set_xticks([]) 


        # Ajusta o gráfico para encostar nas bordas da figura
        fig.tight_layout()
        plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas_widget = canvas.get_tk_widget()
        
        # Usamos pack com fill="both" e expand=True
        canvas_widget.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        canvas_widget.configure(background='white')
        
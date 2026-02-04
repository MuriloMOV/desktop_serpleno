import customtkinter as ctk
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from services.relatorios import ServicoRelatorio

from ui_theme import THEME, SPACING, RADIUS, font

class RelatorioFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_relatorio = ServicoRelatorio()
        
        # Reference mapping for card widgets to update them later
        self.card_widgets = {}

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
        self.load_data()

    def load_data(self):
        def fetch():
            stats = self.servico_relatorio.obter_estatisticas()
            reports = self.servico_relatorio.listar_relatorios()
            self.after(0, lambda: self.update_view(stats, reports))
        threading.Thread(target=fetch, daemon=True).start()

    def update_view(self, stats_res, reports_res):
        if stats_res.get('success'):
            data = stats_res.get('data', {})
            summary = data.get('summary', {})
            
            # Update Cards
            self.update_card("Relatório Geral", str(summary.get('students_total', 0)))
            self.update_card("Agendamentos", str(summary.get('appointments_total', 0)))
            self.update_card("Intervenções", str(summary.get('interventions_total', 0)))
            self.update_card("Triagens", str(summary.get('screenings_total', 0)))

        if reports_res.get('success'):
            data = reports_res.get('data', {})
            if isinstance(data, dict):
                items = data.get('reports', []) or data.get('results', [])
            else:
                items = data if isinstance(data, list) else []
            self.populate_reports_list(items)

    def populate_reports_list(self, reports):
        # Clear existing
        if hasattr(self, 'reports_container'):
            for w in self.reports_container.winfo_children():
                w.destroy()

        if not reports:
            ctk.CTkLabel(self.reports_container, text="Nenhum relatório encontrado.", text_color=THEME["text_muted"], font=font(13)).pack(pady=20)
            return

        for r in reports:
            self.create_report_row(r)

    def create_report_row(self, report):
        row = ctk.CTkFrame(self.reports_container, fg_color=THEME["card"], corner_radius=RADIUS["button"], height=56, border_width=1, border_color=THEME["border"])
        row.pack(fill="x", pady=4, padx=5)
        row.pack_propagate(False)

        ctk.CTkLabel(row, text="📄", font=font(16)).pack(side="left", padx=(15, 10))
        ctk.CTkLabel(row, text=report.get('name', 'Relatório'), font=font(13, "bold"), text_color=THEME["text"]).pack(side="left")
        
        created = report.get('generated_at') or report.get('created_at') or 'Hoje'
        ctk.CTkLabel(row, text=created, font=font(12), text_color=THEME["text_muted"]).pack(side="right", padx=15)
        
        ctk.CTkLabel(row, text=report.get('type', 'Geral'), font=font(12), text_color=THEME["text_muted"]).pack(side="right", padx=10)

    def criar_layout(self):
        # --- BLOCO 1: CABEÇALHO ---
        header = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 14))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        icon_box = ctk.CTkFrame(inner, width=48, height=48, corner_radius=12, fg_color=THEME["primary_light"])
        icon_box.pack(side="left", padx=(0, 16))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="📄", font=font(20), text_color=THEME["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(inner, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="Relatórios", font=font(20, "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(text_box, text="Visão gerencial e indicadores", font=font(12), text_color=THEME["text_muted"]).pack(anchor="w")

        ctk.CTkButton(
            inner,
            text="Gerar Relatório",
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            font=font(12, "bold"),
            height=36,
            corner_radius=RADIUS["button"]
        ).pack(side="right")

        self.criar_cards()
        self.criar_secao_inferior()
        self.criar_secao_exportacao()
        self.criar_lista_relatorios()

    def criar_secao_exportacao(self):
        export_frame = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        export_frame.grid(row=4, column=0, sticky="ew", padx=SPACING["page_x"], pady=(0, 20))
        
        inner = ctk.CTkFrame(export_frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(inner, text="📥 Exportação de Dados", font=font(14, "bold")).pack(side="left", padx=(0, 20))
        
        btn_style = {"height": 32, "corner_radius": RADIUS["button"], "font": font(11, "bold")}
        
        ctk.CTkButton(inner, text="Exportar Estudantes (CSV)", fg_color=THEME["bg_alt"], text_color=THEME["text"], hover_color=THEME["border"], command=self.servico_relatorio.exportar_estudantes, **btn_style).pack(side="left", padx=5)
        ctk.CTkButton(inner, text="Exportar Agenda (CSV)", fg_color=THEME["bg_alt"], text_color=THEME["text"], hover_color=THEME["border"], command=self.servico_relatorio.exportar_agendamentos, **btn_style).pack(side="left", padx=5)
        ctk.CTkButton(inner, text="Exportar Triagens (CSV)", fg_color=THEME["bg_alt"], text_color=THEME["text"], hover_color=THEME["border"], command=self.servico_relatorio.exportar_triagens, **btn_style).pack(side="left", padx=5)

    def criar_cards(self):
        """Cria a fileira de 4 cards responsivos"""
        container_cards = ctk.CTkFrame(self, fg_color="transparent")
        container_cards.grid(row=1, column=0, sticky="ew", padx=SPACING["page_x"], pady=(0, 20))

        # Configura as 4 colunas dos cards para expandirem igualmente
        for i in range(4):
            container_cards.grid_columnconfigure(i, weight=1)

        # sticky="ew" garante que o card preencha a largura da sua coluna
        self.card(container_cards, "Relatório Geral", "Visão completa", "Geral", "#D0E1FD", self.icon_geral).grid(row=0, column=0, padx=8, sticky="ew")
        self.card(container_cards, "Agendamentos", "Análise de consultas", "Agendamentos", "#D1FADF",self.icon_agenda).grid(row=0, column=1, padx=8, sticky="ew")
        self.card(container_cards, "Intervenções", "Acompanhamentos", "Intervenções", "#EBE9FE",self.icon_interv).grid(row=0, column=2, padx=8, sticky="ew")
        self.card(container_cards, "Triagens", "Análise de triagens", "Triagens", "#FEF0C7",self.icon_triagem).grid(row=0, column=3, padx=8, sticky="ew")

    def card(self, parent, titulo, subtitulo, categoria, cor_fundo_icone):
        frame = ctk.CTkFrame(parent, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
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

        # Store label to update later
        value_lbl = ctk.CTkLabel(
            frame, text="--", text_color="#1A1C1E",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold")
        )
        value_lbl.grid(row=1, column=1, sticky="w", padx=(0, 25))
        self.card_widgets[titulo] = value_lbl
        
        # Keep title visuals but maybe move them? 
        # Actually the original code had title = Value usually in dashboards.
        # But here 'titulo' is "Relatório Geral". 
        # Let's re-arrange: Title top left, Value big middle.
        
        # Overwrite previous layout slightly for better data display
        # "titulo" var passed is "Relatório Geral".
        
        # Reset grid for this frame to matching design
        for w in frame.winfo_children(): w.destroy()
        
        icon_box = ctk.CTkFrame(frame, width=42, height=42, fg_color=cor_fundo_icone, corner_radius=8)
        icon_box.place(x=15, y=15)
        
        ctk.CTkLabel(frame, text=titulo, font=font(12, "normal"), text_color=THEME["text_muted"]).place(x=70, y=15)
        
        val = ctk.CTkLabel(frame, text="--", font=font(20, "bold"), text_color=THEME["text"])
        val.place(x=70, y=38)
        self.card_widgets[titulo] = val
        
        return frame

    def update_card(self, key, value):
        if key in self.card_widgets:
            self.card_widgets[key].configure(text=value)



    def criar_secao_inferior(self):
        container_inferior = ctk.CTkFrame(self, fg_color="transparent")
        container_inferior.grid(row=2, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, 20))
        
        # Gráfico (weight 3) ocupa mais espaço que o Resumo (weight 1)
        container_inferior.grid_columnconfigure(0, weight=3)
        container_inferior.grid_columnconfigure(1, weight=1)
        container_inferior.grid_rowconfigure(0, weight=1)

        chart_box = ctk.CTkFrame(container_inferior, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        chart_box.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        summary_box = ctk.CTkFrame(container_inferior, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        summary_box.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(
            chart_box, text="Atividades Nos Últimos 30 dias", 
            font=font(14, "bold")
        ).pack(anchor="nw", padx=20, pady=15)

        self.desenhar_grafico(chart_box)
        
        ctk.CTkLabel(
            summary_box, text="Resumo", 
            font=font(16, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="nw", padx=25, pady=(20, 10))

        itens = [
            ("Total de Estudantes", "0"),
            ("Consultas (30d)", "0"),
            ("Intervenções (30d)", "0"),
            ("Triagens (30d)", "0"),
        ]

        for texto, valor in itens:
            self.item_resumo(summary_box, texto, valor)

        divisor = ctk.CTkFrame(summary_box, fg_color=THEME["border"], height=1)
        divisor.pack(fill="x", padx=25, pady=15)

        self.item_resumo(summary_box, "Taxa de Comparecimento", "-", cor_valor=THEME["success"])

    def item_resumo(self, parent, texto, valor, cor_valor=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=25, pady=4)
        ctk.CTkLabel(f, text=texto, text_color=THEME["text_muted"], font=font(13)).pack(side="left")
        ctk.CTkLabel(f, text=valor, text_color=cor_valor or THEME["text"], font=font(13, "bold")).pack(side="right")
        
    def criar_lista_relatorios(self):
        # sticky="nsew" faz o box preencher toda a Row 3
        container_lista = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        container_lista.grid(row=3, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(10, 24))
        
        header_lista = ctk.CTkFrame(container_lista, fg_color="transparent")
        header_lista.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            header_lista, text="Relatórios Gerados", 
            font=font(16, "bold"), text_color=THEME["text"]
        ).pack(side="left")

        # Filtro de tipo
        self.filtro_tipo = ctk.CTkOptionMenu(
            header_lista,
            values=["Todos os tipos", "Geral", "Estudante", "Agendamentos", "Intervenções", "Triagens", "Estatísticas"],
            fg_color=THEME["card"],
            button_color=THEME["card"],
            button_hover_color=THEME["bg_alt"],
            text_color=THEME["text_muted"],
            dropdown_fg_color=THEME["card"],
            dropdown_text_color=THEME["text"],
            corner_radius=RADIUS["button"],
            height=32,
            font=font(12, "bold")
        )
        self.filtro_tipo.pack(side="right", padx=5)

        ctk.CTkFrame(container_lista, fg_color=THEME["border"], height=1).pack(fill="x")

        # Container para a lista de relatórios (Preenche o restante do espaço)
        self.reports_container = ctk.CTkScrollableFrame(container_lista, fg_color="transparent")
        self.reports_container.pack(expand=True, fill="both")

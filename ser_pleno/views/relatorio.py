import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
import threading
from datetime import datetime, timedelta
from services.relatorios import ServicoRelatorio

from ui_theme import THEME, SPACING, RADIUS, font

class RelatorioFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_relatorio = ServicoRelatorio()
        
        # Reference mapping for card widgets to update them later
        self.card_widgets = {}
        
        # Cache para dados
        self._relatorios_cache = []

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
            corner_radius=RADIUS["button"],
            command=self.abrir_dialog_gerar_relatorio
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
        self.card(container_cards, "Relatório Geral", "Visão completa", "Geral", "#D0E1FD").grid(row=0, column=0, padx=8, sticky="ew")
        self.card(container_cards, "Agendamentos", "Análise de consultas", "Agendamentos", "#D1FADF").grid(row=0, column=1, padx=8, sticky="ew")
        self.card(container_cards, "Intervenções", "Acompanhamentos", "Intervenções", "#EBE9FE").grid(row=0, column=2, padx=8, sticky="ew")
        self.card(container_cards, "Triagens", "Análise de triagens", "Triagens", "#FEF0C7").grid(row=0, column=3, padx=8, sticky="ew")

    def card(self, parent, titulo, subtitulo, categoria, cor_fundo_icone):
        frame = ctk.CTkFrame(parent, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        frame.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(frame, width=42, height=42, fg_color=cor_fundo_icone, corner_radius=8)
        icon_box.grid(row=0, column=0, rowspan=3, padx=(15, 12), pady=15)
        icon_box.grid_propagate(False)

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
        
        ctk.CTkLabel(
            summary_box, text="Resumo", 
            font=font(16, "bold"),
            text_color=THEME["text"]
        ).pack(anchor="nw", padx=25, pady=(20, 10))

        itens = [
            ("Total de Estudantes", "-"),
            ("Consultas (30d)", "-"),
            ("Intervenções (30d)", "-"),
            ("Triagens (30d)", "-"),
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
    
    def abrir_dialog_gerar_relatorio(self):
        """Abre dialog para gerar novo relatório"""
        dialog = DialogGerarRelatorio(self)
        dialog.grab_set()
    
    def on_relatorio_gerado(self):
        """Callback após gerar relatório"""
        self.load_data()
    
    def aplicar_filtro(self, tipo):
        """Aplica filtro na lista de relatórios"""
        if not self._relatorios_cache:
            return
        
        if tipo == "Todos os tipos":
            filtrados = self._relatorios_cache
        else:
            tipo_map = {
                "Geral": "general",
                "Estudante": "student",
                "Agendamentos": "appointments",
                "Intervenções": "interventions",
                "Triagens": "screenings",
                "Estatísticas": "statistics"
            }
            tipo_api = tipo_map.get(tipo, tipo.lower() if tipo else "")
            filtrados = [r for r in self._relatorios_cache 
                        if r.get('report_type', '').lower() == (tipo_api or "").lower()]
        
        self.populate_reports_list(filtrados)


class DialogGerarRelatorio(ctk.CTkToplevel):
    """Dialog para gerar novo relatório com preview"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.servico = ServicoRelatorio()
        
        self.title("Gerar Relatório")
        self.geometry("600x700")
        self.resizable(False, False)
        
        # Centraliza
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"+{x}+{y}")
        
        self._preview_data = None
        
        self._build_ui()
    
    def _build_ui(self):
        main = ctk.CTkFrame(self, fg_color=THEME["bg"])
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(main, text="📄 Gerar Novo Relatório", font=font(18, "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(0, 20))
        
        # Tipo de relatório
        ctk.CTkLabel(main, text="Tipo de Relatório:", font=font(12), text_color=THEME["text"]).pack(anchor="w")
        self.tipo_var = ctk.StringVar(value="Geral")
        tipo_frame = ctk.CTkFrame(main, fg_color="transparent")
        tipo_frame.pack(fill="x", pady=(4, 12))
        
        tipos = ["Geral", "Estudantes", "Agendamentos", "Intervenções", "Triagens", "Estatísticas"]
        self.tipo_combo = ctk.CTkComboBox(tipo_frame, variable=self.tipo_var, values=tipos, 
                                          height=36, command=self._on_tipo_change)
        self.tipo_combo.pack(fill="x")
        
        # Filtros
        filtros_frame = ctk.CTkFrame(main, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        filtros_frame.pack(fill="x", pady=(0, 12))
        
        inner_filtros = ctk.CTkFrame(filtros_frame, fg_color="transparent")
        inner_filtros.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(inner_filtros, text="Filtros", font=font(14, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Período
        periodo_frame = ctk.CTkFrame(inner_filtros, fg_color="transparent")
        periodo_frame.pack(fill="x", pady=4)
        
        ctk.CTkLabel(periodo_frame, text="Período:", font=font(11)).pack(side="left")
        
        self.periodo_var = ctk.StringVar(value="Últimos 30 dias")
        periodos = ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Este ano", "Personalizado"]
        ctk.CTkOptionMenu(periodo_frame, variable=self.periodo_var, values=periodos, 
                         height=28, width=150).pack(side="left", padx=(10, 0))
        
        # Formato
        formato_frame = ctk.CTkFrame(inner_filtros, fg_color="transparent")
        formato_frame.pack(fill="x", pady=4)
        
        ctk.CTkLabel(formato_frame, text="Formato:", font=font(11)).pack(side="left")
        
        self.formato_var = ctk.StringVar(value="PDF")
        formatos = ["PDF", "CSV", "Excel", "JSON"]
        ctk.CTkOptionMenu(formato_frame, variable=self.formato_var, values=formatos,
                         height=28, width=100).pack(side="left", padx=(10, 0))
        
        # Nome do relatório
        ctk.CTkLabel(inner_filtros, text="Nome do Relatório:", font=font(11)).pack(anchor="w", pady=(10, 4))
        self.nome_entry = ctk.CTkEntry(inner_filtros, placeholder_text="Ex: Relatório Mensal - Janeiro/2026", height=36)
        self.nome_entry.pack(fill="x")
        
        # Botão Preview
        preview_btn = ctk.CTkButton(main, text="🔍 Visualizar Preview", fg_color=THEME["info"],
                                   hover_color="#2563EB", height=36, command=self._gerar_preview)
        preview_btn.pack(fill="x", pady=(0, 12))
        
        # Área de Preview
        preview_container = ctk.CTkFrame(main, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        preview_container.pack(fill="both", expand=True, pady=(0, 12))
        
        ctk.CTkLabel(preview_container, text="Preview", font=font(14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.preview_frame = ctk.CTkScrollableFrame(preview_container, fg_color=THEME["bg_alt"])
        self.preview_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        ctk.CTkLabel(self.preview_frame, text="Clique em 'Visualizar Preview' para ver os dados", 
                    font=font(12), text_color=THEME["text_muted"]).pack(pady=40)
        
        # Botões
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color=THEME["bg_alt"], text_color=THEME["text"],
                      hover_color=THEME["border"], command=self.destroy).pack(side="right", padx=(8, 0))
        
        self.gerar_btn = ctk.CTkButton(btn_frame, text="Gerar Relatório", fg_color=THEME["success"],
                                       hover_color="#0EA472", command=self._gerar_relatorio)
        self.gerar_btn.pack(side="right")
    
    def _on_tipo_change(self, value):
        """Atualiza nome sugerido quando tipo muda"""
        tipo = self.tipo_var.get()
        data_str = datetime.now().strftime("%m/%Y")
        self.nome_entry.delete(0, "end")
        self.nome_entry.insert(0, f"Relatório {tipo} - {data_str}")
    
    def _gerar_preview(self):
        """Gera preview do relatório"""
        self.preview_frame.configure(fg_color=THEME["bg_alt"])
        for w in self.preview_frame.winfo_children():
            w.destroy()
        
        # Mostra loading
        loading = ctk.CTkLabel(self.preview_frame, text="Carregando preview...", 
                              font=font(12), text_color=THEME["text_muted"])
        loading.pack(pady=40)
        
        def fetch():
            tipo = self.tipo_var.get()
            
            if tipo == "Estudantes":
                result = self.servico.exportar_estudantes()
            elif tipo == "Agendamentos":
                result = self.servico.exportar_agendamentos()
            elif tipo == "Triagens":
                result = self.servico.exportar_triagens()
            else:
                result = self.servico.obter_estatisticas()
            
            self.after(0, lambda: self._mostrar_preview(result))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _mostrar_preview(self, result):
        """Exibe preview dos dados"""
        for w in self.preview_frame.winfo_children():
            w.destroy()
        
        if not result.get('success'):
            ctk.CTkLabel(self.preview_frame, text="Erro ao carregar dados", 
                        text_color=THEME["danger"]).pack(pady=20)
            return
        
        data = result.get('data', {})
        
        if isinstance(data, list):
            # Dados em lista
            total = len(data)
            ctk.CTkLabel(self.preview_frame, text=f"Total de registros: {total}", 
                        font=font(12, "bold")).pack(anchor="w", pady=(0, 10))
            
            # Mostra primeiros 5 registros
            for i, item in enumerate(data[:5]):
                if isinstance(item, dict):
                    item_frame = ctk.CTkFrame(self.preview_frame, fg_color=THEME["card"])
                    item_frame.pack(fill="x", pady=2)
                    
                    # Mostra alguns campos
                    campos = list(item.items())[:3]
                    for key, value in campos:
                        ctk.CTkLabel(item_frame, text=f"{key}: {value}", 
                                    font=font(10), anchor="w").pack(anchor="w", padx=10, pady=2)
            
            if total > 5:
                ctk.CTkLabel(self.preview_frame, text=f"... e mais {total - 5} registros", 
                            font=font(10), text_color=THEME["text_muted"]).pack(pady=5)
        else:
            # Dados em dict (estatísticas)
            for key, value in data.items():
                item_frame = ctk.CTkFrame(self.preview_frame, fg_color=THEME["card"])
                item_frame.pack(fill="x", pady=2)
                
                ctk.CTkLabel(item_frame, text=f"{key}:", font=font(11)).pack(side="left", padx=10)
                ctk.CTkLabel(item_frame, text=str(value), font=font(11, "bold")).pack(side="right", padx=10)
        
        self._preview_data = result
    
    def _gerar_relatorio(self):
        """Gera o relatório final"""
        nome = self.nome_entry.get()
        if not nome:
            nome = f"Relatório {self.tipo_var.get()} - {datetime.now().strftime('%d/%m/%Y')}"
        
        tipo_map = {
            "Geral": "general",
            "Estudantes": "student",
            "Agendamentos": "appointments",
            "Intervenções": "interventions",
            "Triagens": "screenings",
            "Estatísticas": "statistics"
        }
        
        dados = {
            'name': nome,
            'report_type': tipo_map.get(self.tipo_var.get(), 'general'),
            'format': self.formato_var.get().lower(),
            'parameters': {'periodo': self.periodo_var.get()},
            'data': self._preview_data.get('data', {}) if self._preview_data else {}
        }
        
        result = self.servico.gerar_relatorio(dados)
        
        if result.get('success'):
            messagebox.showinfo("Sucesso", f"Relatório '{nome}' gerado com sucesso!")
            self.parent.on_relatorio_gerado()
            self.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao gerar relatório")
import threading
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from models.relatorio import NovoRelatorioModal

class RelatorioController:
    def __init__(self):
        self.view = None
        self.servico = None

    def set_view(self, view):
        self.view = view
        from services.relatorios import ServicoRelatorio
        self.servico = ServicoRelatorio()

    def inicializar_dashboard(self):
        if not self.view: return
        
        def carregar():
            try:
                stats = self.servico.obter_estatisticas()
                reports = self.servico.listar_relatorios()
                
                # Atualiza UI e Gráfico na thread principal
                if self.view.winfo_exists():
                    self.view.after(0, lambda: self.view.update_view(stats, reports))
                    self.view.after(0, self.renderizar_grafico)
            except Exception as e:
                print(f"Erro ao carregar dashboard: {e}")

        threading.Thread(target=carregar, daemon=True).start()

    def renderizar_grafico(self):
        if not self.view or not hasattr(self.view, 'chart_box'): return

        # Dados
        dias = ['01', '05', '10', '15', '20', '25', '30']
        atendimentos = [5, 12, 8, 15, 10, 20, 18]

        # Estilização usando o tema da View
        bg_color = self.view.THEME["card"]
        text_color = self.view.THEME["text"]
        primary_color = self.view.THEME["primary"]

        fig = Figure(figsize=(5, 3), dpi=100, facecolor=bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        ax.plot(dias, atendimentos, color=primary_color, marker='o', linewidth=2)
        
        # Remove bordas desnecessárias
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        ax.tick_params(colors=text_color, labelsize=8)
        ax.grid(True, alpha=0.1, color=text_color)

        if not self.view or not hasattr(self.view, 'chart_box'): return

        # --- ADICIONE ESTA LINHA ---
        # Remove widgets antigos (canvas anteriores) para evitar duplicação
        for widget in self.view.chart_box.winfo_children():
            # Mantemos apenas o Label de título, se houver
            if isinstance(widget, ctk.CTkCanvas) or "canvas" in str(widget).lower():
                widget.destroy()
        # ---------------------------

        # ... seu código de criação da Figure ...
        
        canvas = FigureCanvasTkAgg(fig, master=self.view.chart_box)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()

    def exportar(self, tipo):
        try:
            metodos = {
                "estudantes": self.servico.exportar_estudantes,
                "agenda": self.servico.exportar_agendamentos,
                "triagens": self.servico.exportar_triagens
            }
            if tipo in metodos:
                metodos[tipo]()
        except Exception as e:
            print(f"Erro na exportação: {e}")

    # No RelatorioController
    def gerar_novo_relatorio(self):
        tipos_django = [
            ('general', 'Relatório Geral'),
            ('student', 'Relatório de Estudante'),
            ('appointments', 'Relatório de Agendamentos'),
            ('interventions', 'Relatório de Intervenções'),
            ('screenings', 'Relatório de Triagens')
        ]
        # Instancia a modal passando a view como parent para o grab_set() funcionar
        NovoRelatorioModal(self.view, tipos=tipos_django, callback=self._salvar_relatorio)

    def _salvar_relatorio(self, dados):
        if not dados.get("name"):
            print("Erro: Nome do relatório é obrigatório")
            return

        def salvar():
            try:
                self.servico.criar_relatorio(dados)
                # Recarrega o dashboard para mostrar o novo item na lista
                self.view.after(0, self.inicializar_dashboard)
            except Exception as e:
                print(f"Erro ao salvar: {e}")

        threading.Thread(target=salvar, daemon=True).start()
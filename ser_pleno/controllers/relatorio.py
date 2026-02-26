import threading
from tkinter import messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from models.relatorio import NovoRelatorioModal

class RelatorioController:
    def __init__(self):
        self.view = None
        self.servico = None
        self._cache_relatorios = [] # Armazena os dados vindos do banco para filtros rápidos

    def set_view(self, view):
        self.view = view
        from services.relatorios import ServicoRelatorio
        self.servico = ServicoRelatorio()

    def run_in_thread(self, target, *args):
        """Helper para executar tarefas pesadas sem travar a UI"""
        threading.Thread(target=target, args=args, daemon=True).start()

    def inicializar_dashboard(self):
        """Carrega dados iniciais do banco e renderiza o gráfico"""
        if not self.view: return
        
        def carregar():
            try:
                # Busca dados reais do banco via Service
                stats = self.servico.obter_estatisticas()
                reports = self.servico.listar_relatorios()
                graph_data = self.servico.obter_dados_grafico() # NOVO: Método no service
                
                self._cache_relatorios = reports.get('data', {}).get('reports', [])

                if self.view.winfo_exists():
                    # Atualiza UI e Gráfico na thread principal
                    self.view.after(0, lambda: self.view.update_view(stats, reports))
                    self.view.after(0, lambda: self.renderizar_grafico(graph_data))
            except Exception as e:
                print(f"Erro ao carregar dashboard: {e}")

        self.run_in_thread(carregar)

    def renderizar_grafico(self, data_res):
        """Renderiza o gráfico com dados dinâmicos vindos do banco"""
        if not self.view or not hasattr(self.view, 'chart_box'): return

        # Extrai dados do resultado do service ou usa fallback vazio
        data = data_res.get('data', {})
        eixo_x = data.get('labels', []) # Ex: ['01/02', '02/02'...]
        eixo_y = data.get('values', []) # Ex: [5, 12, 8...]

        # Configurações de Estilo baseadas no tema
        theme = self.view.THEME
        fig = Figure(figsize=(5, 3), dpi=100, facecolor=theme["card"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(theme["card"])

        # Plotagem dinâmica
        ax.plot(eixo_x, eixo_y, color=theme["primary"], marker='o', linewidth=2, markersize=4)
        
        # Estilização do Plot
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.tick_params(colors=theme["text_muted"], labelsize=8)
        ax.grid(True, alpha=0.05, color=theme["text"])

        # Limpeza de memória/widgets antigos
        for widget in self.view.chart_box.winfo_children():
            if "canvas" in str(widget).lower():
                widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.view.chart_box)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()

    # controllers/relatorio_controller.py

    def aplicar_filtros(self):
        """Filtra os dados comparando o valor selecionado com o banco"""
        tipo_selecionado = self.view.filtro_tipo.get() # Pega "Estudante"
        
        # Mapeamento para garantir que o filtro entenda o valor técnico do banco
        mapa_tipos = {
            "Estudante": "student",
            "Agendamentos": "appointments",
            "Intervenções": "interventions",
            "Geral": "general",
            "Triagens": "screenings"
        }

        filtrados = self._cache_relatorios
        
        if tipo_selecionado != "Todos":
            # Buscamos o valor técnico. Se não achar no mapa, usa o próprio texto
            valor_tecnico = mapa_tipos.get(tipo_selecionado, tipo_selecionado)
            
            # Filtra comparando com o que veio do banco (r['type'])
            filtrados = [r for r in self._cache_relatorios if r.get('type') == valor_tecnico]

        # Atualiza a View (enviando stats vazios para não sobrescrever os cards)
        res_formatado = {'success': True, 'data': {'reports': filtrados}}
        self.view.update_view({'success': False}, res_formatado)

    def exportar(self, tipo, formato):
        def thread_exportacao():
            try:
                # O mapeamento deve bater com os 'values' do RadioButton da View
                metodos = {
                    "estudantes": self.servico.exportar_estudantes,
                    "agenda": self.servico.exportar_agendamentos,
                    "triagens": self.servico.exportar_triagens
                }

                if tipo not in metodos:
                    print(f"Tipo de exportação '{tipo}' não reconhecido.")
                    return

                # Chama a função do service passando o formato
                sucesso = metodos[tipo](formato=formato)
                
                self.view.after(0, lambda: self._finalizar_exportacao(sucesso, tipo, formato))
            except Exception as e:
                print(f"Erro na thread de exportação: {e}")
                self.view.after(0, lambda: messagebox.showerror("Erro", f"Falha ao exportar: {e}"))

        self.run_in_thread(thread_exportacao)
        
    def _finalizar_exportacao(self, sucesso, tipo, formato):
        if sucesso:
            messagebox.showinfo("Sucesso", f"Relatório de {tipo} gerado em {formato.upper()}.")

    def gerar_novo_relatorio(self):
        """Abre o modal e define o callback de retorno"""
        tipos_disponiveis = self.servico.obter_tipos_relatorio() # Pega do Service/Banco
        NovoRelatorioModal(self.view, tipos=tipos_disponiveis, callback=self._salvar_relatorio)

    def _salvar_relatorio(self, dados):
        """Processa a criação do novo relatório"""
        if not dados.get("name"): return

        def task():
            if self.servico.criar_relatorio(dados):
                self.view.after(0, self.inicializar_dashboard)
        
        self.run_in_thread(task)
    
    def solicitar_exclusao(self, relatorio_id):
        """Pede confirmação e executa a exclusão"""
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja apagar este relatório permanentemente?"):
            
            def task():
                resultado = self.servico.excluir_relatorio(relatorio_id)
                if resultado.get("success"):
                    # Recarrega a lista para refletir a alteração
                    self.view.after(0, self.inicializar_dashboard)
                else:
                    self.view.after(0, lambda: messagebox.showerror("Erro", "Não foi possível excluir o relatório."))
            
            self.run_in_thread(task)
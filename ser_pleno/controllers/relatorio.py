import threading
from tkinter import messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 
from models.relatorio import NovoRelatorioModal
import datetime
from ui_theme import THEME

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


        for widget in self.view.chart_box.winfo_children():
            
            if isinstance(widget, FigureCanvasTkAgg) or "canvas" in str(widget).lower():
                widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.view.chart_box)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()

    def exportar(self, tipo, formato):
        """
        Coordena a exportação usando Threads para não travar a interface.
        """
        # 1. Feedback visual imediato
        self.view.mostrar_loading_exportacao(True)

        def thread_exportacao():
            try:
                # Dicionário de métodos do serviço
                metodos = {
                    "estudantes": self.servico.exportar_estudantes,
                    "agenda": self.servico.exportar_agendamentos,
                    "triagens": self.servico.exportar_triagens
                }

                if tipo not in metodos:
                    raise ValueError(f"Tipo '{tipo}' não suportado.")

                # Executa a exportação (demorada) no serviço
                # O retorno agora é True/False baseado no que fizemos no Service
                resultado = metodos[tipo](formato=formato)
                
                # Se for um dicionário (como estava no seu service original), 
                # extraímos o sucesso. Se for booleano, usamos direto.
                sucesso = resultado.get("success", False) if isinstance(resultado, dict) else resultado

                # 2. Volta para a thread principal para atualizar a UI
                self.view.after(0, lambda: self.finalizar_exportacao(sucesso, tipo, formato))

            except PermissionError:
                self.view.after(0, lambda: self.finalizar_exportacao(False, tipo, formato, 
                    erro="O arquivo está aberto em outro programa. Feche-o e tente novamente."))
            except Exception as e:
                self.view.after(0, lambda: self.finalizar_exportacao(False, tipo, formato, erro=str(e)))

        # Inicia o processamento em background
        threading.Thread(target=thread_exportacao, daemon=True).start()

    def finalizar_exportacao(self, sucesso, tipo, formato, erro=None):
        """Fecha o loading e mostra a mensagem final"""
        self.view.mostrar_loading_exportacao(False)
        
        if sucesso:
            messagebox.showinfo("Sucesso", f"O relatório de {tipo.capitalize()} foi exportado para {formato.upper()} com sucesso!")
        elif erro:
            messagebox.showerror("Erro na Exportação", f"Ocorreu um problema: {erro}")
        else:
            # Caso onde o usuário apenas cancelou a janela de salvar
            pass

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

    def aplicar_filtros(self):
        # Captura os valores da View
        tipo_selecionado = self.view.filtro_tipo.get()
        data_ini_str = self.view.btn_data_ini.cget("text")
        data_fim_str = self.view.btn_data_fim.cget("text")

        relatorios_filtrados = self.todos_relatorios

        # 1. Filtro por Tipo (Dropdown)
        if tipo_selecionado != "Todos":
            relatorios_filtrados = [r for r in relatorios_filtrados if r.get('type') == tipo_selecionado]

        # 2. Filtro por Data
        try:
            # Verifica se os botões não estão com o texto padrão
            if data_ini_str != "Data Início" and data_fim_str != "Data Fim":
                d_ini = datetime.strptime(data_ini_str, "%d/%m/%Y")
                d_fim = datetime.strptime(data_fim_str, "%d/%m/%Y")
                
                temp = []
                for r in relatorios_filtrados:
                    data_r_str = r.get('generated_at') or r.get('created_at')
                    if data_r_str:
                        # Tratando data ISO (YYYY-MM-DD)
                        data_r = datetime.fromisoformat(data_r_str.split('T')[0])
                        if d_ini <= data_r <= d_fim:
                            temp.append(r)
                relatorios_filtrados = temp
        except Exception as e:
            print(f"Erro ao processar datas do filtro: {e}")

        # Atualiza a lista
        self.view.populate_reports_list(relatorios_filtrados)

    def limpar_filtros(self):
        self.view.filtro_tipo.set("Todos")
        self.view.btn_data_ini.configure(text="Data Início", fg_color=THEME["bg_alt"], text_color=THEME["text"])
        self.view.btn_data_fim.configure(text="Data Fim", fg_color=THEME["bg_alt"], text_color=THEME["text"])
        self.view.populate_reports_list(self.todos_relatorios)

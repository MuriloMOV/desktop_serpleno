import customtkinter as ctk
from tkinter import messagebox
import threading
from services.triagem import ServicoTriagem
from ui_theme import THEME, SPACING, RADIUS, font

class AnaliseTriagemFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_triagem = ServicoTriagem()
        
        # Cache para dados
        self._triagens_cache = []
        self._estatisticas = {}

        self.grid_columnconfigure(0, weight=1)

        self.criar_cabecalho()
        self.criar_cards_metricas()
        self.criar_graficos()
        self.criar_filtros()
        self.criar_area_conteudo()
        
        self.load_data()

    def load_data(self):
        """Carrega dados da API"""
        def fetch():
            triagens = self.servico_triagem.listar_triagens()
            self.after(0, lambda: self.update_view(triagens))
        threading.Thread(target=fetch, daemon=True).start()

    def update_view(self, triagens_res):
        """Atualiza a view com dados da API"""
        if triagens_res.get('success'):
            self._triagens_cache = triagens_res.get('data', [])
            self._calcular_estatisticas()
            self._atualizar_cards()
            self._atualizar_graficos()
            self.renderizar_tabela(self._triagens_cache)

    def _calcular_estatisticas(self):
        """Calcula estatísticas das triagens"""
        total = len(self._triagens_cache)
        pendentes = sum(1 for t in self._triagens_cache if t.get('status') == 'pending')
        concluidas = sum(1 for t in self._triagens_cache if t.get('status') == 'completed')
        alta_prioridade = sum(1 for t in self._triagens_cache if t.get('priority') in ['high', 'urgent'])
        
        self._estatisticas = {
            'total': total,
            'pendentes': pendentes,
            'concluidas': concluidas,
            'alta_prioridade': alta_prioridade
        }

    def _atualizar_cards(self):
        """Atualiza os cards com valores reais"""
        if hasattr(self, 'card_values'):
            self.card_values['total'].configure(text=str(self._estatisticas.get('total', 0)))
            self.card_values['pendentes'].configure(text=str(self._estatisticas.get('pendentes', 0)))
            self.card_values['concluidas'].configure(text=str(self._estatisticas.get('concluidas', 0)))
            self.card_values['alta_prioridade'].configure(text=str(self._estatisticas.get('alta_prioridade', 0)))

    def _atualizar_graficos(self):
        """Atualiza os gráficos com dados reais"""
        self._draw_status_chart()
        self._draw_priority_chart()

    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 12))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        icon_box = ctk.CTkFrame(inner, width=48, height=48, corner_radius=12, fg_color=THEME["primary_light"])
        icon_box.pack(side="left", padx=(0, 16))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="🔍", font=font(20), text_color=THEME["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(inner, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="Análise de Triagem", font=font(20, "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(text_box, text="Gerenciamento e análise de triagens", font=font(12), text_color=THEME["text_muted"]).pack(anchor="w")

        ctk.CTkButton(
            inner, text="+ Nova Triagem", font=font(12, "bold"),
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
            height=36, corner_radius=RADIUS["button"],
            command=self.abrir_nova_triagem
        ).pack(side="right")

    def criar_cards_metricas(self):
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.grid(row=1, column=0, sticky="ew", padx=SPACING["page_x"], pady=10)
        for i in range(4): cards_container.grid_columnconfigure(i, weight=1)

        self.card_values = {}
        metrics = [
            {"label": "Total", "key": "total", "icon": "📋", "color": THEME["primary"]},
            {"label": "Pendentes", "key": "pendentes", "icon": "⏳", "color": THEME["warning"]},
            {"label": "Concluídas", "key": "concluidas", "icon": "✅", "color": THEME["success"]},
            {"label": "Alta Prioridade", "key": "alta_prioridade", "icon": "⚠️", "color": THEME["danger"]}
        ]
        
        for i, m in enumerate(metrics):
            card = ctk.CTkFrame(cards_container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
            card.grid(row=0, column=i, sticky="ew", padx=5)
            
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", padx=15, pady=15)
            
            ctk.CTkLabel(content, text=m["icon"], font=font(24)).pack(side="right", anchor="n")
            
            text_f = ctk.CTkFrame(content, fg_color="transparent")
            text_f.pack(side="left", anchor="n", fill="both", expand=True)
            ctk.CTkLabel(text_f, text=m["label"], font=font(12), text_color=THEME["text_muted"]).pack(anchor="w")
            
            value_lbl = ctk.CTkLabel(text_f, text="0", font=font(24, "bold"), text_color=m["color"])
            value_lbl.pack(anchor="w")
            self.card_values[m["key"]] = value_lbl

    def criar_graficos(self):
        """Cria seção de gráficos"""
        graficos_container = ctk.CTkFrame(self, fg_color="transparent")
        graficos_container.grid(row=2, column=0, sticky="ew", padx=SPACING["page_x"], pady=10)
        graficos_container.grid_columnconfigure(0, weight=1)
        graficos_container.grid_columnconfigure(1, weight=1)
        
        # Gráfico de Status
        status_box = ctk.CTkFrame(graficos_container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        status_box.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        ctk.CTkLabel(status_box, text="📊 Distribuição por Status", font=font(14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.status_canvas = ctk.CTkCanvas(status_box, bg=THEME["bg_alt"], height=150, highlightthickness=0)
        self.status_canvas.pack(fill="x", padx=15, pady=(0, 15))
        
        # Gráfico de Prioridade
        priority_box = ctk.CTkFrame(graficos_container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        priority_box.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        ctk.CTkLabel(priority_box, text="📈 Distribuição por Prioridade", font=font(14, "bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.priority_canvas = ctk.CTkCanvas(priority_box, bg=THEME["bg_alt"], height=150, highlightthickness=0)
        self.priority_canvas.pack(fill="x", padx=15, pady=(0, 15))

    def _draw_status_chart(self):
        """Desenha gráfico de status"""
        self.status_canvas.delete("all")
        
        status_counts = {}
        for t in self._triagens_cache:
            status = t.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if not status_counts:
            self.status_canvas.create_text(100, 75, text="Sem dados", fill=THEME["text_muted"])
            return
        
        colors = {
            'pending': THEME["warning"],
            'completed': THEME["success"],
            'in_progress': THEME["info"],
            'cancelled': THEME["danger"],
            'unknown': THEME["text_muted"]
        }
        
        labels = {
            'pending': 'Pendente',
            'completed': 'Concluída',
            'in_progress': 'Em Andamento',
            'cancelled': 'Cancelada'
        }
        
        total = sum(status_counts.values())
        w = self.status_canvas.winfo_width() or 300
        
        # Desenha barras horizontais
        y = 20
        bar_height = 25
        for status, count in status_counts.items():
            pct = count / total if total > 0 else 0
            bar_width = int((w - 100) * pct)
            
            # Barra
            self.status_canvas.create_rectangle(80, y, 80 + bar_width, y + bar_height, 
                                               fill=colors.get(status, THEME["text_muted"]), outline="")
            # Label
            label_text = labels.get(status, status) or status
            self.status_canvas.create_text(10, y + bar_height/2, text=label_text, 
                                          anchor="w", fill=THEME["text"], font=("Arial", 10))
            # Valor
            self.status_canvas.create_text(w - 10, y + bar_height/2, text=f"{count} ({pct*100:.0f}%)", 
                                          anchor="e", fill=THEME["text"], font=("Arial", 10, "bold"))
            
            y += bar_height + 10

    def _draw_priority_chart(self):
        """Desenha gráfico de prioridade"""
        self.priority_canvas.delete("all")
        
        priority_counts = {}
        for t in self._triagens_cache:
            priority = t.get('priority', 'unknown')
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        if not priority_counts:
            self.priority_canvas.create_text(100, 75, text="Sem dados", fill=THEME["text_muted"])
            return
        
        colors = {
            'urgent': "#B91C1C",
            'high': THEME["danger"],
            'medium': THEME["warning"],
            'low': THEME["success"],
            'unknown': THEME["text_muted"]
        }
        
        labels = {
            'urgent': 'Urgente',
            'high': 'Alta',
            'medium': 'Média',
            'low': 'Baixa'
        }
        
        total = sum(priority_counts.values())
        w = self.priority_canvas.winfo_width() or 300
        
        # Desenha barras horizontais
        y = 20
        bar_height = 25
        for priority, count in priority_counts.items():
            pct = count / total if total > 0 else 0
            bar_width = int((w - 100) * pct)
            
            # Barra
            self.priority_canvas.create_rectangle(80, y, 80 + bar_width, y + bar_height, 
                                               fill=colors.get(priority, THEME["text_muted"]), outline="")
            # Label
            label_text = labels.get(priority, priority) or priority
            self.priority_canvas.create_text(10, y + bar_height/2, text=label_text, 
                                          anchor="w", fill=THEME["text"], font=("Arial", 10))
            # Valor
            self.priority_canvas.create_text(w - 10, y + bar_height/2, text=f"{count} ({pct*100:.0f}%)", 
                                          anchor="e", fill=THEME["text"], font=("Arial", 10, "bold"))
            
            y += bar_height + 10

    def criar_filtros(self):
        filtro_frame = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        filtro_frame.grid(row=3, column=0, sticky="ew", padx=SPACING["page_x"], pady=10)
        
        inner = ctk.CTkFrame(filtro_frame, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=15)
        
        # Filtros em linha
        filtros_row = ctk.CTkFrame(inner, fg_color="transparent")
        filtros_row.pack(fill="x")
        
        # Status
        ctk.CTkLabel(filtros_row, text="Status:", font=font(11)).pack(side="left", padx=(0, 5))
        self.filtro_status = ctk.CTkOptionMenu(
            filtros_row, values=["Todos", "Pendente", "Em Andamento", "Concluída", "Cancelada"],
            height=28, width=120
        )
        self.filtro_status.set("Todos")
        self.filtro_status.pack(side="left", padx=(0, 15))
        
        # Prioridade
        ctk.CTkLabel(filtros_row, text="Prioridade:", font=font(11)).pack(side="left", padx=(0, 5))
        self.filtro_prioridade = ctk.CTkOptionMenu(
            filtros_row, values=["Todas", "Baixa", "Média", "Alta", "Urgente"],
            height=28, width=100
        )
        self.filtro_prioridade.set("Todas")
        self.filtro_prioridade.pack(side="left", padx=(0, 15))
        
        # Botões
        ctk.CTkButton(filtros_row, text="Limpar", command=self.limpar_filtros, 
                     fg_color=THEME["bg_alt"], text_color=THEME["text"], 
                     hover_color=THEME["border"], width=80, height=28).pack(side="right")
        ctk.CTkButton(filtros_row, text="Aplicar", command=self.aplicar_filtros, 
                     fg_color=THEME["primary"], width=80, height=28).pack(side="right", padx=(0, 5))

    def criar_area_conteudo(self):
        container = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        container.grid(row=4, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(10, 20))
        
        # Header da tabela
        header = ctk.CTkFrame(container, fg_color=THEME["bg_alt"])
        header.pack(fill="x", padx=15, pady=(15, 5))
        
        cols = [("Estudante", 2), ("Formulário", 1.5), ("Data", 1), ("Prioridade", 1), ("Status", 1), ("Ações", 0.8)]
        for col_name, weight in cols:
            ctk.CTkLabel(header, text=col_name, font=font(11, "bold"), text_color=THEME["text_muted"]).pack(side="left", expand=True, fill="x", padx=5)
        
        # Lista de triagens
        self.lista_triagens = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.lista_triagens.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def aplicar_filtros(self):
        status_f = self.filtro_status.get()
        prioridade_f = self.filtro_prioridade.get()
        
        status_map = {
            "Pendente": "pending",
            "Em Andamento": "in_progress", 
            "Concluída": "completed",
            "Cancelada": "cancelled"
        }
        
        priority_map = {
            "Baixa": "low",
            "Média": "medium",
            "Alta": "high",
            "Urgente": "urgent"
        }
        
        filtered = []
        for t in self._triagens_cache:
            match_status = (status_f == "Todos" or t.get('status') == status_map.get(status_f))
            match_prioridade = (prioridade_f == "Todas" or t.get('priority') == priority_map.get(prioridade_f))
            if match_status and match_prioridade:
                filtered.append(t)
        
        self.renderizar_tabela(filtered)

    def limpar_filtros(self):
        self.filtro_status.set("Todos")
        self.filtro_prioridade.set("Todas")
        self.renderizar_tabela(self._triagens_cache)

    def renderizar_tabela(self, data_list):
        for w in self.lista_triagens.winfo_children(): w.destroy()

        if not data_list:
            ctk.CTkLabel(self.lista_triagens, text="Nenhuma triagem encontrada.", 
                        text_color=THEME["text_muted"], font=font(12)).pack(pady=20)
            return

        for item in data_list:
            row = ctk.CTkFrame(self.lista_triagens, fg_color=THEME["card"], border_width=1, border_color=THEME["border"])
            row.pack(fill="x", pady=2)
            
            # Estudante
            ctk.CTkLabel(row, text=item.get('student_name', 'Estudante'), 
                        font=font(11, "bold")).pack(side="left", expand=True, fill="x", padx=5)
            
            # Formulário
            ctk.CTkLabel(row, text=item.get('form_name', 'Formulário'), 
                        font=font(11), text_color=THEME["text_muted"]).pack(side="left", expand=True, fill="x", padx=5)
            
            # Data
            data = item.get('created_at', '')[:10] if item.get('created_at') else '--'
            ctk.CTkLabel(row, text=data, font=font(11)).pack(side="left", expand=True, fill="x", padx=5)
            
            # Prioridade
            priority_colors = {
                'urgent': THEME["danger"],
                'high': "#F97316",
                'medium': THEME["warning"],
                'low': THEME["success"]
            }
            priority_labels = {'urgent': 'Urgente', 'high': 'Alta', 'medium': 'Média', 'low': 'Baixa'}
            priority = item.get('priority', 'medium')
            priority_text = priority_labels.get(priority, priority) or priority
            ctk.CTkLabel(row, text=priority_text, 
                        font=font(11, "bold"), text_color=priority_colors.get(priority, THEME["text"])
                        ).pack(side="left", expand=True, fill="x", padx=5)
            
            # Status
            status_colors = {
                'pending': THEME["warning"],
                'completed': THEME["success"],
                'in_progress': THEME["info"],
                'cancelled': THEME["danger"]
            }
            status_labels = {'pending': 'Pendente', 'completed': 'Concluída', 'in_progress': 'Em Andamento', 'cancelled': 'Cancelada'}
            status = item.get('status', 'pending')
            ctk.CTkLabel(row, text=status_labels.get(status, status), 
                        font=font(11), text_color=status_colors.get(status, THEME["text"])
                        ).pack(side="left", expand=True, fill="x", padx=5)
            
            # Ações
            act_frame = ctk.CTkFrame(row, fg_color="transparent")
            act_frame.pack(side="left", expand=True, fill="x", padx=5)
            
            ctk.CTkButton(act_frame, text="👁", width=30, height=28, 
                         fg_color=THEME["primary_light"], text_color=THEME["primary"],
                         hover_color=THEME["primary"], 
                         command=lambda id=item.get('id'): self.ver_triagem(id)).pack(side="left", padx=2)

    def ver_triagem(self, id_triagem):
        """Abre dialog para ver detalhes da triagem"""
        messagebox.showinfo("Triagem", f"Visualizando triagem #{id_triagem}")

    def abrir_nova_triagem(self):
        """Abre dialog para nova triagem"""
        messagebox.showinfo("Nova Triagem", "Funcionalidade de nova triagem")

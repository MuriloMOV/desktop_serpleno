import customtkinter as ctk
from services.triagem import ServicoTriagem
# Compat alias para testes
ScreeningService = ServicoTriagem
import threading
from datetime import datetime

from ui_theme import THEME, SPACING, RADIUS, font

class AnaliseTriagemFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_triagem = ServicoTriagem()

        self.colors = THEME

        self.grid_columnconfigure(0, weight=1)

        # 1. Cabeçalho
        self.criar_cabecalho()

        # 2. Key Metrics Cards
        self.criar_cards_metricas()

        # Container Principal com Abas estilizadas
        self.container_lista = None
        self.criar_area_conteudo()

    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 12))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        # Título
        icon_box = ctk.CTkFrame(inner, width=48, height=48, corner_radius=12, fg_color=self.colors["primary_light"])
        icon_box.pack(side="left", padx=(0, 16))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="📋", font=font(20), text_color=self.colors["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(inner, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="Análise de Triagem", font=font(20, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(text_box, text="Gerenciamento e acompanhamento de triagens", font=font(12), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Botão Nova Triagem
        ctk.CTkButton(
            inner,
            text="+ Nova Triagem",
            font=font(14, "bold"),
            fg_color=self.colors["primary"],
            hover_color="#4F46E5",
            text_color="white",
            height=40,
            corner_radius=RADIUS["button"],
            command=self.abrir_nova_triagem
        ).pack(side="right")

    def criar_cards_metricas(self):
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.grid(row=1, column=0, sticky="ew", padx=SPACING["page_x"], pady=10)
        
        # 4 colunas
        for i in range(4):
            cards_container.grid_columnconfigure(i, weight=1)

        # Cards Data
        metrics = [
            {"label": "Total Triagens", "value": "12", "icon": "📋", "color": "#3B82F6", "bg": "#DBEAFE"},
            {"label": "Pendentes", "value": "4", "icon": "⏳", "color": "#F59E0B", "bg": "#FEF3C7"},
            {"label": "Concluídas", "value": "7", "icon": "✅", "color": "#10B981", "bg": "#D1FAE5"},
            {"label": "Alta Prioridade", "value": "1", "icon": "⚠️", "color": "#EF4444", "bg": "#FEE2E2"}
        ]

        for i, m in enumerate(metrics):
            self.criar_card_metrica(cards_container, i, m)

    def criar_card_metrica(self, parent, idx, metric):
        card = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card.grid(row=0, column=idx, sticky="ew", padx=5)
        
        # Layout interno
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", padx=20, pady=20)

        # Icone (Círculo colorido)
        icon_f = ctk.CTkFrame(content, width=48, height=48, corner_radius=24, fg_color=metric["bg"])
        icon_f.pack(side="left", padx=(0, 15))
        icon_f.pack_propagate(False) # Force size
        ctk.CTkLabel(icon_f, text=metric["icon"], font=("Segoe UI", 20)).place(relx=0.5, rely=0.5, anchor="center")

        # Dados
        text_f = ctk.CTkFrame(content, fg_color="transparent")
        text_f.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            text_f,
            text=metric["value"],
            font=font(22, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_f,
            text=metric["label"],
            font=font(12, "bold"),
            text_color=self.colors["text_muted"]
        ).pack(anchor="w")

    def criar_area_conteudo(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=3, column=0, sticky="nsew", padx=SPACING["page_x"], pady=20)

        # Filtros (estilo web)
        filtros = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        filtros.pack(fill="x", pady=(0, 16))

        filtros_inner = ctk.CTkFrame(filtros, fg_color="transparent")
        filtros_inner.pack(fill="x", padx=16, pady=14)

        ctk.CTkLabel(filtros_inner, text="Filtros", font=font(14, "bold"), text_color=self.colors["text"]).grid(row=0, column=0, sticky="w")

        filtros_inner.grid_columnconfigure(1, weight=1)

        # Busca
        search_box = ctk.CTkFrame(filtros_inner, fg_color=self.colors["bg_alt"], height=36, corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        search_box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 8))
        search_box.pack_propagate(False)
        ctk.CTkLabel(search_box, text="🔍", text_color=self.colors["text_muted"], font=font(12)).pack(side="left", padx=10)
        ctk.CTkEntry(search_box, placeholder_text="Buscar estudante...", fg_color="transparent", border_width=0, font=font(12)).pack(side="left", fill="both", expand=True)

        filtros_row = ctk.CTkFrame(filtros_inner, fg_color="transparent")
        filtros_row.grid(row=2, column=0, columnspan=2, sticky="ew")
        filtros_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.filtro_status = ctk.CTkOptionMenu(
            filtros_row,
            values=["Todos os status", "Pendente", "Em Andamento", "Concluída", "Cancelada"],
            fg_color=self.colors["bg_alt"],
            button_color=self.colors["bg_alt"],
            button_hover_color=self.colors["border"],
            text_color=self.colors["text_muted"],
            dropdown_fg_color=self.colors["card"],
            dropdown_text_color=self.colors["text"],
            corner_radius=RADIUS["input"],
            height=34,
            font=font(11, "bold")
        )
        self.filtro_status.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.filtro_prioridade = ctk.CTkOptionMenu(
            filtros_row,
            values=["Todas as prioridades", "Baixa", "Média", "Alta", "Urgente"],
            fg_color=self.colors["bg_alt"],
            button_color=self.colors["bg_alt"],
            button_hover_color=self.colors["border"],
            text_color=self.colors["text_muted"],
            dropdown_fg_color=self.colors["card"],
            dropdown_text_color=self.colors["text"],
            corner_radius=RADIUS["input"],
            height=34,
            font=font(11, "bold")
        )
        self.filtro_prioridade.grid(row=0, column=1, padx=(6, 6), sticky="ew")

        ctk.CTkEntry(
            filtros_row,
            placeholder_text="De (dd/mm/aaaa)",
            fg_color=self.colors["bg_alt"],
            border_color=self.colors["border"],
            border_width=1,
            corner_radius=RADIUS["input"],
            height=34,
            font=font(11)
        ).grid(row=0, column=2, padx=(6, 6), sticky="ew")

        ctk.CTkEntry(
            filtros_row,
            placeholder_text="Até (dd/mm/aaaa)",
            fg_color=self.colors["bg_alt"],
            border_color=self.colors["border"],
            border_width=1,
            corner_radius=RADIUS["input"],
            height=34,
            font=font(11)
        ).grid(row=0, column=3, padx=(6, 0), sticky="ew")

        # Header da Lista com Tabs e Filtros
        list_header = ctk.CTkFrame(container, fg_color="transparent")
        list_header.pack(fill="x", pady=(0, 15))

        # Tabs
        self.tab_buttons = []
        tab_frame = ctk.CTkFrame(list_header, fg_color="transparent")
        tab_frame.pack(side="left")
        
        for t in ["Pendentes", "Concluídas", "Todas"]:
            self.criar_tab_botao(tab_frame, t)
        
        # Search Box
        search_box = ctk.CTkFrame(list_header, fg_color=self.colors["card"], width=250, height=40, corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        search_box.pack(side="right")
        search_box.pack_propagate(False)
        ctk.CTkLabel(search_box, text="🔍", text_color=self.colors["text_muted"], font=font(13)).pack(side="left", padx=10)
        ctk.CTkEntry(search_box, placeholder_text="Buscar por aluno...", fg_color="transparent", border_width=0, font=font(13)).pack(side="left", fill="both", expand=True)

        # Lista Real
        self.lista_triagens = ctk.CTkFrame(container, fg_color="transparent")
        self.lista_triagens.pack(fill="both", expand=True)

        # Start
        self.mudar_tab("Pendentes")

    def criar_tab_botao(self, parent, text):
        btn = ctk.CTkButton(
            parent, 
            text=text, 
            fg_color="transparent", 
            text_color=self.colors["text_muted"], 
            hover_color=self.colors["bg_alt"], 
            corner_radius=RADIUS["button"], 
            height=32,
            font=font(13, "bold"),
            command=lambda x=text: self.mudar_tab(x)
        )
        btn.pack(side="left", padx=2)
        self.tab_buttons.append(btn)

    def mudar_tab(self, active_name):
        # Update styling
        for btn in self.tab_buttons:
            if btn.cget("text") == active_name:
                btn.configure(fg_color=self.colors["card"], text_color=self.colors["primary"], border_width=1, border_color=self.colors["border"]) 
            else:
                btn.configure(fg_color="transparent", text_color=self.colors["text_muted"], border_width=0)
        
        # Track active tab for refreshes
        self.current_tab = active_name
        self.renderizar_lista(active_name)

    def renderizar_lista(self, tab_filtro):
        for w in self.lista_triagens.winfo_children(): w.destroy()
        
        status_map = {
            "Pendentes": "pending",
            "Concluídas": "completed",
            "Todas": None
        }
        status_filter = status_map.get(tab_filtro)
        
        # Skeleton loading
        ctk.CTkLabel(self.lista_triagens, text="Carregando dados...", text_color=self.colors["text_muted"]).pack(pady=20)
        
        def fetch():
            res = self.servico_triagem.listar_triagens(status=status_filter)
            self.after(0, lambda: self._populate_list(res))
            
        threading.Thread(target=fetch, daemon=True).start()

    def _populate_list(self, result):
        for w in self.lista_triagens.winfo_children(): w.destroy()
        
        items = result.get('data', getattr(result, 'data', {}))
        if isinstance(items, dict): 
             items = items.get('screenings', []) or items.get('results', [])
        
        if not items:
            ctk.CTkLabel(self.lista_triagens, text="Nenhum registro encontrado nesta categoria.", text_color=self.colors["text_muted"]).pack(pady=40)
            return

        for item in items:
            self.criar_item_triagem(item)

    def criar_item_triagem(self, item):
        card = ctk.CTkFrame(self.lista_triagens, fg_color="white", corner_radius=12, border_width=1, border_color=self.colors["border"])
        card.pack(fill="x", pady=6)
        
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=15)
        
        # 1. Aluno Info
        info_box = ctk.CTkFrame(row, fg_color="transparent")
        info_box.pack(side="left")
        
        student_name = item.get('student', {}).get('name', 'Aluno Desconhecido')
        ctk.CTkLabel(info_box, text=student_name, font=("Segoe UI", 14, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        created = item.get('created_at', '')
        # Simple date parse logic if needed
        ctk.CTkLabel(info_box, text=f"Solicitado em: {created}", font=("Segoe UI", 12), text_color=self.colors["text_muted"]).pack(anchor="w")

        # 2. Status Badge (Right)
        status_raw = item.get('status', 'pending')
        status_display = item.get('status_display', status_raw.capitalize())
        
        # Determine colors
        st_conf = self.colors["pending"] # default
        if status_raw == 'completed': st_conf = self.colors["completed"]
        
        badge = ctk.CTkLabel(
            row, 
            text=f"  {status_display}  ", 
            fg_color=st_conf["bg"], 
            text_color=st_conf["fg"], 
            corner_radius=6, 
            font=("Segoe UI", 12, "bold"),
            height=28
        )
        badge.pack(side="right")

    def abrir_nova_triagem(self):
        """Abre um modal para criar uma nova triagem."""
        # Build modal window
        modal = ctk.CTkToplevel(self)
        modal.title("Nova Triagem")
        modal.geometry("560x420")
        modal.transient(self)

        content = ctk.CTkFrame(modal, fg_color=self.colors["card"], corner_radius=12)
        content.pack(fill="both", expand=True, padx=12, pady=12)

        # Student select
        ctk.CTkLabel(content, text="Estudante", font=font(12, "bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(6, 0))
        students_var = ctk.StringVar()
        students_menu = ctk.CTkOptionMenu(content, values=["Carregando..."], variable=students_var, fg_color=self.colors["bg_alt"], button_color=self.colors["bg_alt"], corner_radius=RADIUS["input"]) 
        students_menu.pack(fill="x", pady=(4, 8))

        # Form select
        ctk.CTkLabel(content, text="Formulário", font=font(12, "bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(6, 0))
        forms_var = ctk.StringVar()
        forms_menu = ctk.CTkOptionMenu(content, values=["Carregando..."], variable=forms_var, fg_color=self.colors["bg_alt"], button_color=self.colors["bg_alt"], corner_radius=RADIUS["input"]) 
        forms_menu.pack(fill="x", pady=(4, 8))

        # Priority + scheduled date
        row = ctk.CTkFrame(content, fg_color="transparent")
        row.pack(fill="x", pady=(6, 8))
        ctk.CTkLabel(row, text="Prioridade", font=font(11, "bold"), text_color=self.colors["text"]).grid(row=0, column=0, sticky="w")
        prioridade_var = ctk.StringVar(value="medium")
        prioridade_menu = ctk.CTkOptionMenu(row, values=["low", "medium", "high", "urgent"], variable=prioridade_var, fg_color=self.colors["bg_alt"], button_color=self.colors["bg_alt"], corner_radius=RADIUS["input"]) 
        prioridade_menu.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(row, text="Data Agendada (YYYY-MM-DD)", font=font(11, "bold"), text_color=self.colors["text"]).grid(row=0, column=1, sticky="w")
        date_entry = ctk.CTkEntry(row, placeholder_text="YYYY-MM-DD", fg_color=self.colors["bg_alt"], border_width=1, corner_radius=RADIUS["input"]) 
        date_entry.grid(row=1, column=1, sticky="ew")
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)

        # Observações
        ctk.CTkLabel(content, text="Observações", font=font(12, "bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(6, 0))
        observations = ctk.CTkTextbox(content, height=100, fg_color=self.colors["bg_alt"], corner_radius=8)
        observations.pack(fill="both", pady=(6, 8))

        # Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(fill="x", pady=(8, 0))
        btn_cancel = ctk.CTkButton(actions, text="Cancelar", command=modal.destroy, fg_color=self.colors["bg_alt"], text_color=self.colors["text_muted"]) 
        btn_cancel.pack(side="right", padx=6)

        def submit():
            # Find selected student id and form id from the mapped lookups
            student_label = students_var.get()
            form_label = forms_var.get()
            student_id = getattr(modal, "_students_map", {}).get(student_label)
            form_id = getattr(modal, "_forms_map", {}).get(form_label)
            payload = {
                'student_id': student_id,
                'form_id': form_id,
                'priority': prioridade_var.get(),
                'scheduled_date': date_entry.get().strip() or None,
                'observations': observations.get("1.0", "end").strip()
            }
            self.criar_triagem(payload)
            modal.destroy()

        btn_save = ctk.CTkButton(actions, text="Criar Triagem", command=submit, fg_color=self.colors["primary"], text_color="white")
        btn_save.pack(side="right")

        # Load students and forms async to avoid blocking UI
        def load_lookups():
            # Students
            from services.estudantes import ServicoEstudante
            ss = ServicoEstudante()
            students_resp = ss.listar_estudantes()
            s_list = []
            s_map = {}
            if students_resp:
                for s in students_resp.get('data', []):
                    label = f"{s.get('name')} ({s.get('id')})"
                    s_list.append(label)
                    s_map[label] = s.get('id')

            # Forms
            forms_resp = self.servico_triagem.listar_formularios() if hasattr(self.servico_triagem, 'listar_formularios') else None
            f_list = []
            f_map = {}
            if forms_resp and isinstance(forms_resp, dict):
                for f in forms_resp.get('data', []):
                    label = f.get('name') or str(f.get('id'))
                    f_list.append(label)
                    f_map[label] = f.get('id')

            # Apply to widgets in main thread
            def apply():
                if s_list:
                    students_menu.configure(values=s_list)
                    students_var.set(s_list[0])
                else:
                    students_menu.configure(values=["Nenhum estudante disponível"])
                    students_var.set("Nenhum estudante disponível")

                if f_list:
                    forms_menu.configure(values=f_list)
                    forms_var.set(f_list[0])
                else:
                    forms_menu.configure(values=["Padrão"])
                    forms_var.set("Padrão")

                modal._students_map = s_map
                modal._forms_map = f_map

            self.after(0, apply)

        threading.Thread(target=load_lookups, daemon=True).start()

    def criar_triagem(self, dados):
        """Cria uma triagem via serviço e atualiza a lista em seguida."""
        # Defensive: ensure required fields
        if not dados.get('student_id'):
            print("Erro: estudante não selecionado")
            return

        res = self.servico_triagem.criar_triagem(dados)
        # Accept dict-like or response-like
        ok = False
        if isinstance(res, dict):
            ok = res.get('success', False)
        else:
            ok = getattr(res, 'status_code', 200) in (200, 201)

        if ok:
            # Refresh current tab list
            try:
                self.renderizar_lista(getattr(self, 'current_tab', 'Pendentes'))
            except Exception:
                pass
        else:
            print('Erro ao criar triagem:', res)

"""
Tela de Orientações para o Desktop CustomTkinter
Implementação baseada na lógica do SerPleno Web
"""
import customtkinter as ctk
from datetime import datetime
import threading
import json
from typing import Optional, List, Dict, Any, Callable

from services.estudantes import ServicoEstudante
from services.orientacoes import ServicoOrientacoes, servico_orientacoes
from ui_theme import THEME, SPACING, RADIUS, font


class OrientacoesFrame(ctk.CTkFrame):
    """Frame principal de Orientações com layout similar ao web"""
    
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_estudante = ServicoEstudante()
        self.servico_orientacoes = servico_orientacoes
        
        # Estado
        self.colors = THEME
        self.selected_student: Optional[Dict] = None
        self.selected_student_id: Optional[int] = None
        self.orientacoes_history: List[Dict] = []
        self.current_tab: str = "new"  # "new" ou "history"
        self.dynamic_components: List[Dict] = []
        self.action_plan: List[Dict] = []
        
        # Estado de edição
        self.editing_orientation_id: Optional[int] = None
        self.is_editing: bool = False
        
        # Referências para widgets dinâmicos (para coletar valores ao salvar)
        self.dynamic_widgets: Dict[str, Any] = {}
        
        # Campos do formulário
        self.entry_titulo: Optional[ctk.CTkEntry] = None
        self.entry_data: Optional[ctk.CTkEntry] = None
        self.entry_tema: Optional[ctk.CTkEntry] = None
        self.text_mensagem: Optional[ctk.CTkTextbox] = None
        self.text_conteudo: Optional[ctk.CTkTextbox] = None
        self.preview_container: Optional[ctk.CTkFrame] = None
        self.history_container: Optional[ctk.CTkFrame] = None
        
        # Configurar grid principal para expandir
        self.grid_rowconfigure(0, weight=0)  # header
        self.grid_rowconfigure(1, weight=0)  # banner
        self.grid_rowconfigure(2, weight=1)  # main container
        self.grid_columnconfigure(0, weight=1)
        
        # Construir UI
        self._build_ui()
        
        # Carregar dados
        self._load_students()
    
    def _build_ui(self):
        """Constrói a interface completa"""
        # 1. Cabeçalho Superior
        self._create_header()
        
        # 2. Banner de Orientações
        self._create_banner()
        
        # 3. Container Principal (2 colunas) - usando grid para ocupar todo espaço
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=2, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, 12))
        self.main_container.grid_rowconfigure(0, weight=1)  # Linha única expande
        self.main_container.grid_columnconfigure(0, weight=1, minsize=280)  # Coluna Alunos
        self.main_container.grid_columnconfigure(1, weight=4, minsize=600)  # Coluna Form
        
        # 4. Painel Esquerdo: Lista de Estudantes
        self._create_students_panel()
        
        # 5. Painel Direito: Construtor de Orientações
        self._create_builder_panel()
    
    def _create_header(self):
        """Cria o cabeçalho com título e botão salvar"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 8))
        
        # Título
        ctk.CTkLabel(
            header, 
            text="Orientações", 
            font=font(20, "bold"),
            text_color=self.colors["text"]
        ).pack(side="left")
        
        # Botões da direita
        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.pack(side="right")
        
        # Botão Salvar
        self.btn_salvar = ctk.CTkButton(
            actions_frame,
            text="Salvar Orientação",
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            font=font(12, "bold"),
            height=36,
            width=140,
            corner_radius=RADIUS["button"],
            command=self._save_orientation
        )
        self.btn_salvar.pack(side="left", padx=5)
        
        # Ícone de notificação (usando emoji como ícone)
        ctk.CTkLabel(actions_frame, text="🔔", font=font(18), text_color=self.colors["text_muted"]).pack(side="left", padx=5)
    
    def _create_banner(self):
        """Cria o banner de orientações"""
        banner = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        banner.grid(row=1, column=0, sticky="ew", padx=SPACING["page_x"], pady=(0, 16))
        
        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=14)
        
        # Ícone
        icon_box = ctk.CTkFrame(inner, width=48, height=48, fg_color=self.colors["purple_light"], corner_radius=12)
        icon_box.pack(side="left", padx=(0, 16))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="💜", font=("Segoe UI", 20)).place(relx=0.5, rely=0.5, anchor="center")
        
        # Textos
        texts = ctk.CTkFrame(inner, fg_color="transparent")
        texts.pack(side="left")
        ctk.CTkLabel(texts, text="Orientações e Acompanhamento", font=font(16, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        self.subtitle_label = ctk.CTkLabel(texts, text="Selecione um estudante ao lado para iniciar", font=font(13), text_color=self.colors["text_muted"])
        self.subtitle_label.pack(anchor="w")
    
    def _create_students_panel(self):
        """Cria o painel de lista de estudantes"""
        container = ctk.CTkFrame(self.main_container, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        container.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        
        # Configurar container para expandir verticalmente
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Header com título e busca
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        
        ctk.CTkLabel(header_frame, text="Estudantes", font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        # Campo de busca
        search_frame = ctk.CTkFrame(header_frame, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"], height=36)
        search_frame.pack(fill="x", pady=(6, 0))
        search_frame.pack_propagate(False)
        
        ctk.CTkLabel(search_frame, text="🔍", text_color=self.colors["text_muted"], font=font(11)).pack(side="left", padx=8)
        
        self.entry_busca = ctk.CTkEntry(search_frame, placeholder_text="Filtrar alunos...", fg_color="transparent", border_width=0, font=font(11))
        self.entry_busca.pack(side="left", fill="both", expand=True)
        self.entry_busca.bind("<KeyRelease>", lambda e: self._filter_students())
        
        # Lista de alunos com scroll
        self.scroll_alunos = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.scroll_alunos.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
    
    def _create_builder_panel(self):
        """Cria o painel do construtor de orientações"""
        container = ctk.CTkFrame(self.main_container, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        container.grid(row=0, column=1, sticky="nsew")
        
        # Configurar para expandir
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Tabs (Nova Orientação / Histórico / Estatísticas)
        tab_frame = ctk.CTkFrame(container, fg_color=self.colors["bg_alt"], height=42, corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        tab_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_propagate(False)
        
        self.btn_tab_new = ctk.CTkButton(
            tab_frame, text="Nova Orientação", fg_color=self.colors["card"], text_color=self.colors["text"],
            font=font(12, "bold"), width=140, corner_radius=6, height=32,
            command=lambda: self._switch_tab("new")
        )
        self.btn_tab_new.pack(side="left", padx=4, pady=4)
        
        self.btn_tab_history = ctk.CTkButton(
            tab_frame, text="Histórico", fg_color="transparent", text_color=self.colors["text_muted"],
            font=font(12), width=100, height=32,
            command=lambda: self._switch_tab("history")
        )
        self.btn_tab_history.pack(side="left", padx=4, pady=4)
        
        self.btn_tab_stats = ctk.CTkButton(
            tab_frame, text="Estatísticas", fg_color="transparent", text_color=self.colors["text_muted"],
            font=font(12), width=100, height=32,
            command=lambda: self._switch_tab("stats")
        )
        self.btn_tab_stats.pack(side="left", padx=4, pady=4)
        
        # Container de conteúdo com scroll
        self.content_scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.content_scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        
        # Tab: Nova Orientação
        self.tab_new_frame = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        self.tab_new_frame.pack(fill="both", expand=True)
        self._create_new_orientation_form()
        
        # Tab: Histórico (inicialmente oculto)
        self.tab_history_frame = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        self._create_history_panel()
        
        # Tab: Estatísticas (inicialmente oculto)
        self.tab_stats_frame = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
        self._create_stats_panel()
    
    def _create_new_orientation_form(self):
        """Cria o formulário de nova orientação"""
        # Campos de metadados
        self.entry_titulo = self._create_field(self.tab_new_frame, "Título da Orientação", "Ex: Planejamento de Estudos Semanal")
        
        # Linha: Data e Tema
        row_data_tema = ctk.CTkFrame(self.tab_new_frame, fg_color="transparent")
        row_data_tema.pack(fill="x", pady=8)
        
        self.entry_data = self._create_field(row_data_tema, "Data da Sessão", datetime.now().strftime("%d/%m/%Y"), side="left", width=200)
        self.entry_tema = self._create_field(row_data_tema, "Tema / Categoria", "Ex: Organização, Ansiedade, Rotina", side="left", padx=16)
        
        # Modelos Rápidos
        self._create_presets_section()
        
        # Mensagem Motivacional
        self.text_mensagem = self._create_text_field(self.tab_new_frame, "Mensagem Motivacional (Destaque)", "Escreva uma mensagem de apoio...", height=70)
        
        # Divisor
        ctk.CTkFrame(self.tab_new_frame, height=1, fg_color=self.colors["border"]).pack(fill="x", pady=12)
        
        # Conteúdo Dinâmico
        self._create_dynamic_content_section()
        
        # Anexos
        self._create_attachments_section()
        
        # Botões de ação
        self._create_action_buttons()
    
    def _create_field(self, parent, label, placeholder, side="top", width=None, padx=0, pady=8) -> ctk.CTkEntry:
        """Cria um campo de entrada"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        if side == "left":
            # padx pode ser int ou tuple
            if isinstance(padx, tuple):
                frame.pack(side="left", fill="x", expand=True, padx=padx)
            else:
                frame.pack(side="left", fill="x", expand=True, padx=padx)
        else:
            frame.pack(fill="x", pady=pady)
        
        ctk.CTkLabel(frame, text=label, font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        entry = ctk.CTkEntry(
            frame, placeholder_text=placeholder, fg_color="#f8fafc", 
            border_width=1, border_color=self.colors["border"], 
            height=36, corner_radius=8, font=font(12)
        )
        if width:
            entry.configure(width=width)
        entry.pack(fill="x", pady=(4, 0))
        
        return entry
    
    def _create_text_field(self, parent, label, placeholder, height=80) -> ctk.CTkTextbox:
        """Cria um campo de texto multilinha"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        ctk.CTkLabel(frame, text=label, font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        textbox = ctk.CTkTextbox(
            frame, fg_color="#f8fafc", border_width=1, 
            border_color=self.colors["border"], height=height, 
            corner_radius=8, font=font(12)
        )
        textbox.pack(fill="x", pady=(4, 0))
        # Não inserir placeholder como texto - CTkTextbox não suporta placeholder nativo
        # O usuário verá o campo vazio
        
        return textbox
    
    def _create_presets_section(self):
        """Cria a seção de modelos rápidos"""
        frame = ctk.CTkFrame(self.tab_new_frame, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        ctk.CTkLabel(frame, text="Modelos Rápidos", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        presets_container = ctk.CTkFrame(frame, fg_color="transparent")
        presets_container.pack(fill="x", pady=(4, 0))
        
        presets = self.servico_orientacoes.get_presets()
        for key, preset in presets.items():
            btn = ctk.CTkButton(
                presets_container, text=preset["label"], 
                fg_color=self.colors["bg_alt"], text_color=self.colors["text"],
                font=font(10), height=28, corner_radius=6,
                border_width=1, border_color=self.colors["border"],
                command=lambda k=key: self._apply_preset(k)
            )
            btn.pack(side="left", padx=(0, 6))
    
    def _create_dynamic_content_section(self):
        """Cria a seção de conteúdo dinâmico"""
        # Header
        header = ctk.CTkFrame(self.tab_new_frame, fg_color="transparent")
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="Conteúdo Dinâmico", font=font(14, "bold"), text_color=self.colors["text"]).pack(side="left")
        
        btn_export = ctk.CTkButton(
            header, text="Exportar JSON", fg_color="transparent", 
            text_color=self.colors["primary"], font=font(11, "bold"),
            command=self._export_json
        )
        btn_export.pack(side="right")
        
        # Preview container
        self.preview_container = ctk.CTkFrame(self.tab_new_frame, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["card"])
        self.preview_container.pack(fill="x", pady=10)
        
        # Mensagem vazia inicial
        self.empty_preview_label = ctk.CTkLabel(
            self.preview_container, 
            text="Adicione campos abaixo ou selecione um modelo...",
            font=font(12), text_color=self.colors["text_muted"]
        )
        self.empty_preview_label.pack(pady=20)
        
        # Controles para adicionar campos
        controls = ctk.CTkFrame(self.tab_new_frame, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["input"])
        controls.pack(fill="x", pady=8)
        
        inner_controls = ctk.CTkFrame(controls, fg_color="transparent")
        inner_controls.pack(fill="x", padx=12, pady=8)
        
        # Tipo de campo
        ctk.CTkLabel(inner_controls, text="Tipo:", font=font(10, "bold")).pack(side="left")
        
        self.combo_field_type = ctk.CTkOptionMenu(
            inner_controls, values=["Texto Curto", "Texto Longo", "Tarefa/Checkbox", "Data"],
            fg_color="white", button_color="white", width=120, height=28
        )
        self.combo_field_type.pack(side="left", padx=(6, 12))
        
        # Label do campo
        self.entry_field_label = ctk.CTkEntry(
            inner_controls, placeholder_text="Rótulo do campo...", 
            width=180, height=28
        )
        self.entry_field_label.pack(side="left", padx=(0, 8))
        
        # Botão adicionar
        ctk.CTkButton(
            inner_controls, text="Adicionar", fg_color=self.colors["text"],
            font=font(11, "bold"), height=28, width=90,
            command=self._add_dynamic_field
        ).pack(side="left")
        
        # Editor de conteúdo principal
        ctk.CTkLabel(self.tab_new_frame, text="Conteúdo Principal", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w", pady=(10, 4))
        
        self.text_conteudo = ctk.CTkTextbox(
            self.tab_new_frame, fg_color="#f8fafc", border_width=1,
            border_color=self.colors["border"], height=120,
            corner_radius=8, font=font(12)
        )
        self.text_conteudo.pack(fill="x")
        
        # Checkbox Markdown
        self.check_markdown = ctk.CTkCheckBox(
            self.tab_new_frame, text="Usar Markdown", font=font(11),
            border_color=self.colors["border"], 
            checkmark_color=self.colors["primary"]
        )
        self.check_markdown.pack(anchor="w", pady=6)
    
    def _create_attachments_section(self):
        """Cria a seção de anexos"""
        frame = ctk.CTkFrame(self.tab_new_frame, fg_color=self.colors["purple_light"], corner_radius=RADIUS["card"])
        frame.pack(fill="x", pady=10)
        
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        ctk.CTkLabel(inner, text="Anexos e Documentos", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(6, 0))
        
        self.btn_anexos = ctk.CTkButton(
            btn_frame, text="Escolher Arquivos", 
            fg_color="white", text_color=self.colors["primary"],
            font=font(11), height=30, corner_radius=6,
            border_width=1, border_color=self.colors["border"],
            command=self._choose_files
        )
        self.btn_anexos.pack(side="left")
        
        self.label_files = ctk.CTkLabel(btn_frame, text="Nenhum arquivo selecionado", font=font(10), text_color=self.colors["text_muted"])
        self.label_files.pack(side="left", padx=8)
    
    def _create_action_buttons(self):
        """Cria os botões de ação final"""
        frame = ctk.CTkFrame(self.tab_new_frame, fg_color="transparent")
        frame.pack(fill="x", pady=12)
        
        ctk.CTkButton(
            frame, text="Salvar Orientação", 
            fg_color=self.colors["primary"], 
            hover_color=self.colors["primary_hover"],
            text_color="white", font=font(12, "bold"), 
            height=38, width=160, corner_radius=RADIUS["button"],
            command=self._save_orientation
        ).pack(side="left")
        
        ctk.CTkButton(
            frame, text="Resetar", fg_color="transparent",
            border_width=1, border_color=self.colors["border"],
            text_color=self.colors["text_muted"], font=font(12),
            height=38, width=100, corner_radius=RADIUS["button"],
            command=self._reset_form
        ).pack(side="left", padx=12)
    
    def _create_history_panel(self):
        """Cria o painel de histórico de orientações"""
        # Filtros do histórico
        filters_frame = ctk.CTkFrame(self.tab_history_frame, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["card"])
        filters_frame.pack(fill="x", pady=(0, 12))
        
        filters_inner = ctk.CTkFrame(filters_frame, fg_color="transparent")
        filters_inner.pack(fill="x", padx=12, pady=10)
        
        # Busca
        ctk.CTkLabel(filters_inner, text="Buscar:", font=font(10, "bold")).pack(side="left")
        self.entry_history_search = ctk.CTkEntry(filters_inner, placeholder_text="Título, tema ou conteúdo...", width=200, height=28)
        self.entry_history_search.pack(side="left", padx=(6, 16))
        self.entry_history_search.bind("<Return>", lambda e: self._load_history())
        
        # Data início
        ctk.CTkLabel(filters_inner, text="De:", font=font(10, "bold")).pack(side="left")
        self.entry_history_date_from = ctk.CTkEntry(filters_inner, placeholder_text="DD/MM/AAAA", width=100, height=28)
        self.entry_history_date_from.pack(side="left", padx=(6, 16))
        
        # Data fim
        ctk.CTkLabel(filters_inner, text="Até:", font=font(10, "bold")).pack(side="left")
        self.entry_history_date_to = ctk.CTkEntry(filters_inner, placeholder_text="DD/MM/AAAA", width=100, height=28)
        self.entry_history_date_to.pack(side="left", padx=(6, 16))
        
        # Botões
        ctk.CTkButton(filters_inner, text="Filtrar", height=28, width=70,
                      fg_color=self.colors["primary"], command=self._load_history).pack(side="left", padx=(6, 4))
        ctk.CTkButton(filters_inner, text="Limpar", height=28, width=70,
                      fg_color="transparent", border_width=1, border_color=self.colors["border"],
                      text_color=self.colors["text_muted"], command=self._clear_history_filters).pack(side="left")
        
        # Contador de resultados
        self.history_count_label = ctk.CTkLabel(self.tab_history_frame, text="", font=font(11), text_color=self.colors["text_muted"])
        self.history_count_label.pack(anchor="w", pady=(0, 8))
        
        # Container do histórico
        self.history_container = ctk.CTkFrame(self.tab_history_frame, fg_color="transparent")
        self.history_container.pack(fill="both", expand=True)
        
        # Placeholder inicial
        self.history_placeholder = ctk.CTkLabel(
            self.history_container,
            text="Selecione um estudante para ver o histórico",
            font=font(14), text_color=self.colors["text_muted"]
        )
        self.history_placeholder.pack(pady=50)
    
    def _create_stats_panel(self):
        """Cria o painel de estatísticas"""
        self.stats_container = ctk.CTkFrame(self.tab_stats_frame, fg_color="transparent")
        self.stats_container.pack(fill="both", expand=True)
        
        # Placeholder inicial
        ctk.CTkLabel(
            self.stats_container,
            text="Carregando estatísticas...",
            font=font(14), text_color=self.colors["text_muted"]
        ).pack(pady=50)
    
    def _clear_history_filters(self):
        """Limpa os filtros do histórico"""
        if hasattr(self, 'entry_history_search'):
            self.entry_history_search.delete(0, "end")
        if hasattr(self, 'entry_history_date_from'):
            self.entry_history_date_from.delete(0, "end")
        if hasattr(self, 'entry_history_date_to'):
            self.entry_history_date_to.delete(0, "end")
        self._load_history()
    
    # ==================== LÓGICA DE NEGÓCIO ====================
    
    def _load_students(self):
        """Carrega a lista de estudantes"""
        def fetch():
            res = self.servico_estudante.listar_estudantes()
            self.after(0, lambda: self._render_students(res))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _render_students(self, res):
        """Renderiza a lista de estudantes"""
        for w in self.scroll_alunos.winfo_children():
            w.destroy()
        
        students = []
        if res.get('success'):
            data = res.get('data', [])
            if isinstance(data, dict):
                students = data.get('students', []) or data.get('results', [])
            elif isinstance(data, list):
                students = data
        else:
            # Mostrar erro de conexão
            error_msg = res.get('error', 'Erro desconhecido ao carregar estudantes')
            ctk.CTkLabel(
                self.scroll_alunos, 
                text=f"⚠️ Erro ao carregar alunos:\n{error_msg}", 
                font=font(11), 
                text_color="red",
                wraplength=200,
                justify="center"
            ).pack(pady=20)
            return
        
        if not students:
            ctk.CTkLabel(
                self.scroll_alunos, 
                text="Nenhum aluno encontrado\n\nVerifique se há alunos\ncadastrados no banco de dados", 
                font=font(11), 
                text_color=self.colors["text_muted"],
                wraplength=200,
                justify="center"
            ).pack(pady=20)
            return
        
        self._students_list = students
        for st in students:
            self._create_student_card(st)
    
    def _create_student_card(self, student: Dict):
        """Cria um card de estudante"""
        nome = student.get('name', 'N/A')
        course = student.get('course', 'Curso N/A')
        student_id = student.get('id') or student.get('pk')
        
        card = ctk.CTkFrame(self.scroll_alunos, fg_color=self.colors["card"], corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        card.pack(fill="x", pady=4, padx=2)
        
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=15, pady=10)
        
        # Iniciais
        initials = "".join([n[0] for n in nome.split()[:2]]).upper()
        
        avatar = ctk.CTkFrame(info, width=36, height=36, fg_color=self.colors["purple_light"], corner_radius=18)
        avatar.pack(side="left", padx=(0, 10))
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=initials, font=font(12, "bold"), text_color=self.colors["primary"]).place(relx=0.5, rely=0.5, anchor="center")
        
        # Textos
        text_frame = ctk.CTkFrame(info, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(text_frame, text=nome, font=font(13, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=course, font=font(11), text_color=self.colors["text_muted"]).pack(anchor="w")
        
        # Bind para seleção
        card.bind("<Button-1>", lambda e, s=student, c=card: self._select_student(s, c))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda e, s=student, c=card: self._select_student(s, c))
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e, s=student, c=card: self._select_student(s, c))
    
    def _select_student(self, student: Dict, card: ctk.CTkFrame):
        """Seleciona um estudante"""
        self.selected_student = student
        self.selected_student_id = student.get('id') or student.get('pk')
        
        nome = student.get('name', 'Aluno')
        self.subtitle_label.configure(text=f"Criando orientação para: {nome}")
        
        # Atualizar visual
        for w in self.scroll_alunos.winfo_children():
            w.configure(fg_color=self.colors["card"])
        card.configure(fg_color=self.colors["purple_light"])
        
        # Carregar histórico se na tab de histórico
        if self.current_tab == "history":
            self._load_history()
    
    def _filter_students(self):
        """Filtra a lista de estudantes"""
        query = (self.entry_busca.get() or "").lower().strip()
        
        if not hasattr(self, '_students_list'):
            return
        
        for w in self.scroll_alunos.winfo_children():
            w.destroy()
        
        filtered = [s for s in self._students_list if query in (s.get('name', '')).lower()]
        
        if not filtered:
            ctk.CTkLabel(self.scroll_alunos, text="Nenhum resultado", font=font(12), text_color=self.colors["text_muted"]).pack(pady=20)
            return
        
        for st in filtered:
            self._create_student_card(st)
    
    def _switch_tab(self, tab: str):
        """Alterna entre as tabs"""
        self.current_tab = tab
        
        # Resetar estilos de todos os botões
        self.btn_tab_new.configure(fg_color="transparent", text_color=self.colors["text_muted"])
        self.btn_tab_history.configure(fg_color="transparent", text_color=self.colors["text_muted"])
        self.btn_tab_stats.configure(fg_color="transparent", text_color=self.colors["text_muted"])
        
        # Esconder todos os frames
        self.tab_new_frame.pack_forget()
        self.tab_history_frame.pack_forget()
        self.tab_stats_frame.pack_forget()
        
        if tab == "new":
            self.btn_tab_new.configure(fg_color=self.colors["card"], text_color=self.colors["text"])
            self.tab_new_frame.pack(fill="both", expand=True)
        elif tab == "history":
            self.btn_tab_history.configure(fg_color=self.colors["card"], text_color=self.colors["text"])
            self.tab_history_frame.pack(fill="both", expand=True)
            self._load_history()
        elif tab == "stats":
            self.btn_tab_stats.configure(fg_color=self.colors["card"], text_color=self.colors["text"])
            self.tab_stats_frame.pack(fill="both", expand=True)
            self._load_stats()
    
    def _apply_preset(self, preset_key: str):
        """Aplica um preset de modelo"""
        preset = self.servico_orientacoes.get_preset(preset_key)
        if not preset:
            return
        
        # Limpar componentes anteriores
        self.dynamic_components = []
        
        # Adicionar componentes do preset
        for comp in preset.get('components', []):
            self.dynamic_components.append({
                'id': f"{comp['id']}_{datetime.now().timestamp()}",
                'type': comp['type'],
                'label': comp['label']
            })
        
        self._render_preview()
    
    def _add_dynamic_field(self):
        """Adiciona um campo dinâmico"""
        type_map = {
            "Texto Curto": "text",
            "Texto Longo": "textarea",
            "Tarefa/Checkbox": "checkbox",
            "Data": "date"
        }
        
        field_type = type_map.get(self.combo_field_type.get(), "text")
        field_label = self.entry_field_label.get().strip() or "Campo"
        
        self.dynamic_components.append({
            'id': f"f_{datetime.now().timestamp()}",
            'type': field_type,
            'label': field_label
        })
        
        self._render_preview()
        self.entry_field_label.delete(0, "end")
    
    def _render_preview(self):
        """Renderiza o preview dos campos dinâmicos"""
        # Limpar container
        for w in self.preview_container.winfo_children():
            w.destroy()
        
        # Limpar referências de widgets anteriores
        self.dynamic_widgets = {}
        
        if not self.dynamic_components:
            self.empty_preview_label = ctk.CTkLabel(
                self.preview_container,
                text="Adicione campos abaixo ou selecione um modelo...",
                font=font(13), text_color=self.colors["text_muted"]
            )
            self.empty_preview_label.pack(pady=30)
            return
        
        # Renderizar cada componente
        for i, comp in enumerate(self.dynamic_components):
            row = ctk.CTkFrame(self.preview_container, fg_color="white", corner_radius=8)
            row.pack(fill="x", pady=4, padx=8)
            
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=10, pady=8)
            
            comp_id = comp['id']
            
            if comp['type'] == 'text':
                entry = ctk.CTkEntry(inner, placeholder_text=comp['label'], width=300)
                entry.pack(side="left", fill="x", expand=True)
                # Restaurar valor se existir
                if comp.get('value'):
                    entry.insert(0, comp['value'])
                self.dynamic_widgets[comp_id] = {'widget': entry, 'type': 'text', 'label': comp['label']}
            elif comp['type'] == 'textarea':
                # CTkTextbox não suporta placeholder_text, então usamos um label acima
                textarea_frame = ctk.CTkFrame(inner, fg_color="transparent")
                textarea_frame.pack(side="left", fill="x", expand=True)
                ctk.CTkLabel(textarea_frame, text=comp['label'], font=font(10), 
                            text_color=self.colors["text_muted"]).pack(anchor="w")
                text = ctk.CTkTextbox(textarea_frame, height=60)
                text.pack(fill="x", expand=True)
                # Restaurar valor se existir
                if comp.get('value'):
                    text.insert("0.0", comp['value'])
                self.dynamic_widgets[comp_id] = {'widget': text, 'type': 'textarea', 'label': comp['label']}
            elif comp['type'] == 'checkbox':
                check = ctk.CTkCheckBox(inner, text=comp['label'])
                check.pack(side="left")
                # Restaurar estado se existir
                if comp.get('checked'):
                    check.select()
                self.dynamic_widgets[comp_id] = {'widget': check, 'type': 'checkbox', 'label': comp['label']}
            elif comp['type'] == 'date':
                entry = ctk.CTkEntry(inner, placeholder_text=comp['label'])
                entry.pack(side="left", fill="x", expand=True)
                # Restaurar valor se existir
                if comp.get('value'):
                    entry.insert(0, comp['value'])
                self.dynamic_widgets[comp_id] = {'widget': entry, 'type': 'date', 'label': comp['label']}
            
            # Botão remover
            btn_remove = ctk.CTkButton(
                inner, text="X", width=30, height=30,
                fg_color="transparent", text_color=self.colors["text_muted"],
                command=lambda idx=i: self._remove_component(idx)
            )
            btn_remove.pack(side="right")
    
    def _remove_component(self, index: int):
        """Remove um componente dinâmico"""
        if 0 <= index < len(self.dynamic_components):
            self.dynamic_components.pop(index)
            self._render_preview()
    
    def _load_history(self):
        """Carrega o histórico de orientações do estudante selecionado"""
        if not self.selected_student_id:
            if hasattr(self, 'history_container') and self.history_container:
                for w in self.history_container.winfo_children():
                    w.destroy()
                ctk.CTkLabel(
                    self.history_container,
                    text="Selecione um estudante para ver o histórico",
                    font=font(14), text_color=self.colors["text_muted"]
                ).pack(pady=50)
            return
        
        # Coletar filtros
        search = ""
        date_from = None
        date_to = None
        
        if hasattr(self, 'entry_history_search'):
            search = self.entry_history_search.get().strip()
        if hasattr(self, 'entry_history_date_from'):
            date_from_str = self.entry_history_date_from.get().strip()
            if date_from_str:
                try:
                    date_from = datetime.strptime(date_from_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    pass
        if hasattr(self, 'entry_history_date_to'):
            date_to_str = self.entry_history_date_to.get().strip()
            if date_to_str:
                try:
                    date_to = datetime.strptime(date_to_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                except:
                    pass
        
        def fetch():
            res = self.servico_orientacoes.listar_orientacoes(
                id_estudante=self.selected_student_id,
                tema=search if search else None
            )
            self.after(0, lambda: self._render_history(res))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _load_stats(self):
        """Carrega as estatísticas de orientações"""
        def fetch():
            res = self.servico_orientacoes.obter_estatisticas(self.selected_student_id)
            self.after(0, lambda: self._render_stats(res))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _render_stats(self, res: Dict):
        """Renderiza o painel de estatísticas"""
        if not self.stats_container:
            return
        
        for w in self.stats_container.winfo_children():
            w.destroy()
        
        if not res.get('success'):
            ctk.CTkLabel(self.stats_container, text="Erro ao carregar estatísticas", 
                        font=font(12), text_color="red").pack(pady=20)
            return
        
        data = res.get('data', {})
        total = data.get('total', 0)
        by_theme = data.get('by_theme', [])
        by_month = data.get('by_month', [])
        
        # Cards de estatísticas em linha
        cards_row = ctk.CTkFrame(self.stats_container, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 16))
        
        # Card Total
        total_card = ctk.CTkFrame(cards_row, fg_color=self.colors["primary"], corner_radius=RADIUS["card"])
        total_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        total_inner = ctk.CTkFrame(total_card, fg_color="transparent")
        total_inner.pack(fill="both", expand=True, padx=20, pady=16)
        
        ctk.CTkLabel(total_inner, text=str(total), font=font(32, "bold"), 
                    text_color="white").pack(anchor="w")
        ctk.CTkLabel(total_inner, text="Total de Orientações", font=font(12), 
                    text_color="white").pack(anchor="w")
        
        # Card Por Tema
        theme_card = ctk.CTkFrame(cards_row, fg_color=self.colors["card"], corner_radius=RADIUS["card"], 
                                  border_width=1, border_color=self.colors["border"])
        theme_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        theme_inner = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_inner.pack(fill="both", expand=True, padx=20, pady=16)
        
        ctk.CTkLabel(theme_inner, text="Por Tema", font=font(14, "bold"), 
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 8))
        
        for item in by_theme[:5]:
            row = ctk.CTkFrame(theme_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=item.get('theme', 'Sem tema'), font=font(11),
                        text_color=self.colors["text_muted"]).pack(side="left")
            ctk.CTkLabel(row, text=str(item.get('count', 0)), font=font(11, "bold"),
                        text_color=self.colors["primary"]).pack(side="right")
        
        # Card Por Mês
        month_card = ctk.CTkFrame(cards_row, fg_color=self.colors["card"], corner_radius=RADIUS["card"],
                                  border_width=1, border_color=self.colors["border"])
        month_card.pack(side="left", fill="both", expand=True)
        
        month_inner = ctk.CTkFrame(month_card, fg_color="transparent")
        month_inner.pack(fill="both", expand=True, padx=20, pady=16)
        
        ctk.CTkLabel(month_inner, text="Por Mês", font=font(14, "bold"),
                    text_color=self.colors["text"]).pack(anchor="w", pady=(0, 8))
        
        for item in by_month[:6]:
            row = ctk.CTkFrame(month_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            month_str = item.get('month', '')
            if month_str:
                try:
                    month_date = datetime.fromisoformat(month_str)
                    month_label = month_date.strftime("%b/%Y")
                except:
                    month_label = month_str
            else:
                month_label = "-"
            ctk.CTkLabel(row, text=month_label, font=font(11),
                        text_color=self.colors["text_muted"]).pack(side="left")
            ctk.CTkLabel(row, text=str(item.get('count', 0)), font=font(11, "bold"),
                        text_color=self.colors["primary"]).pack(side="right")
    
    def _render_history(self, res: Dict):
        """Renderiza o histórico de orientações"""
        if not self.history_container:
            return
        
        for w in self.history_container.winfo_children():
            w.destroy()
        
        if not res.get('success'):
            ctk.CTkLabel(self.history_container, text="Erro ao carregar histórico", font=font(12), text_color="red").pack(pady=20)
            return
        
        orientations = res.get('data', {}).get('orientations', [])
        total_count = res.get('data', {}).get('pagination', {}).get('total', len(orientations))
        
        # Atualizar contador
        if hasattr(self, 'history_count_label'):
            self.history_count_label.configure(text=f"{total_count} orientação(ões) encontrada(s)")
        
        if not orientations:
            ctk.CTkLabel(
                self.history_container, 
                text="Nenhuma orientação encontrada\nComece criando uma nova orientação.",
                font=font(13), text_color=self.colors["text_muted"]
            ).pack(pady=50)
            return
        
        for o in orientations:
            self._create_history_card(o)
    
    def _create_history_card(self, orientation: Dict):
        """Cria um card de orientação no histórico"""
        card = ctk.CTkFrame(self.history_container, fg_color="white", corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card.pack(fill="x", pady=8)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=12)
        
        # Data
        date_str = orientation.get('session_date', '')
        day = '?'
        if date_str:
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', ''))
                day = str(date_obj.day)
            except:
                day = '?'
        
        date_circle = ctk.CTkFrame(inner, width=40, height=40, fg_color=self.colors["purple_light"], corner_radius=20)
        date_circle.pack(side="left", padx=(0, 12))
        date_circle.pack_propagate(False)
        ctk.CTkLabel(date_circle, text=str(day), font=font(14, "bold"), text_color=self.colors["primary"]).place(relx=0.5, rely=0.5, anchor="center")
        
        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(info, text=orientation.get('title', 'Orientação'), font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        # Tags
        tags_frame = ctk.CTkFrame(info, fg_color="transparent")
        tags_frame.pack(anchor="w")
        
        theme = orientation.get('theme', 'Geral')
        ctk.CTkLabel(tags_frame, text=theme, font=font(10), 
                    text_color=self.colors["primary"], 
                    fg_color=self.colors["purple_light"],
                    corner_radius=4, padx=6, pady=2).pack(side="left", padx=(0, 8))
        
        # Preview do conteúdo
        content = orientation.get('content', '')
        if content:
            preview = content[:100] + "..." if len(content) > 100 else content
            ctk.CTkLabel(info, text=preview, font=font(10), 
                        text_color=self.colors["text_muted"], 
                        wraplength=300, justify="left").pack(anchor="w", pady=(4, 0))
        
        # Container de botões
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(side="right")
        
        orientation_id = orientation.get('id')
        
        # Botão Ver
        btn_view = ctk.CTkButton(
            btn_frame, text="Ver", width=50, height=28,
            fg_color=self.colors["bg_alt"], text_color=self.colors["primary"],
            font=font(10),
            command=lambda o=orientation: self._view_orientation(o)
        )
        btn_view.pack(side="left", padx=(0, 4))
        
        # Botão Editar
        btn_edit = ctk.CTkButton(
            btn_frame, text="Editar", width=50, height=28,
            fg_color=self.colors["primary"], text_color="white",
            font=font(10),
            command=lambda o=orientation: self._edit_orientation(o)
        )
        btn_edit.pack(side="left", padx=(0, 4))
        
        # Botão Duplicar
        btn_duplicate = ctk.CTkButton(
            btn_frame, text="Duplicar", width=55, height=28,
            fg_color=self.colors["bg_alt"], text_color="green",
            font=font(10),
            command=lambda o_id=orientation_id: self._duplicate_orientation(o_id) if o_id else None
        )
        btn_duplicate.pack(side="left", padx=(0, 4))
        
        # Botão Excluir
        btn_delete = ctk.CTkButton(
            btn_frame, text="Excluir", width=55, height=28,
            fg_color="transparent", text_color="red",
            font=font(10), border_width=1, border_color=self.colors["border"],
            command=lambda o_id=orientation_id: self._confirm_delete_orientation(o_id) if o_id else None
        )
        btn_delete.pack(side="left")
    
    def _view_orientation(self, orientation: Dict):
        """Mostra uma orientação em um modal de visualização"""
        # Criar modal
        modal = ctk.CTkToplevel(self)
        modal.title("Visualizar Orientação")
        modal.geometry("700x600")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        
        # Container com scroll
        scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(scroll, text=orientation.get('title', 'Orientação'), 
                    font=font(18, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        # Tags
        tags_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        tags_frame.pack(anchor="w", pady=(8, 0))
        
        theme = orientation.get('theme', 'Geral')
        ctk.CTkLabel(tags_frame, text=theme, font=font(10),
                    text_color=self.colors["primary"],
                    fg_color=self.colors["purple_light"],
                    corner_radius=4, padx=6, pady=2).pack(side="left", padx=(0, 8))
        
        date_str = orientation.get('session_date', '')
        if date_str:
            try:
                date_obj = datetime.fromisoformat(date_str.replace('Z', ''))
                formatted_date = date_obj.strftime("%d/%m/%Y")
                ctk.CTkLabel(tags_frame, text=f"📅 {formatted_date}", font=font(10),
                            text_color=self.colors["text_muted"]).pack(side="left")
            except:
                pass
        
        # Mensagem motivacional
        motivational = orientation.get('motivational_message', '')
        if motivational:
            msg_frame = ctk.CTkFrame(scroll, fg_color="#e0f2fe", corner_radius=8)
            msg_frame.pack(fill="x", pady=(16, 0))
            ctk.CTkLabel(msg_frame, text=f'"{motivational}"', font=font(12),
                        text_color="#0369a1", wraplength=650).pack(padx=16, pady=12)
        
        # Conteúdo
        content = orientation.get('content', '')
        if content:
            ctk.CTkLabel(scroll, text="Conteúdo", font=font(12, "bold"),
                        text_color=self.colors["text"]).pack(anchor="w", pady=(16, 8))
            content_frame = ctk.CTkFrame(scroll, fg_color=self.colors["bg_alt"], corner_radius=8)
            content_frame.pack(fill="x")
            ctk.CTkLabel(content_frame, text=content, font=font(11),
                        text_color=self.colors["text"], wraplength=650,
                        justify="left").pack(padx=16, pady=12)
        
        # Plano de ação
        action_plan = orientation.get('action_plan', [])
        if action_plan:
            ctk.CTkLabel(scroll, text="Plano de Ação", font=font(12, "bold"),
                        text_color=self.colors["text"]).pack(anchor="w", pady=(16, 8))
            
            for item in action_plan:
                task_text = item.get('text', '') if isinstance(item, dict) else str(item)
                done = item.get('done', False) if isinstance(item, dict) else False
                
                task_frame = ctk.CTkFrame(scroll, fg_color=self.colors["bg_alt"], corner_radius=6)
                task_frame.pack(fill="x", pady=2)
                
                check = ctk.CTkCheckBox(task_frame, text=task_text, font=font(11),
                                       state="disabled" if done else "normal")
                if done:
                    check.select()
                check.pack(padx=12, pady=8)
        
        # Botão fechar
        ctk.CTkButton(modal, text="Fechar", width=100,
                     fg_color=self.colors["text"],
                     command=modal.destroy).pack(pady=16)
    
    def _duplicate_orientation(self, orientation_id: int):
        """Duplica uma orientação"""
        def duplicate():
            res = self.servico_orientacoes.duplicar_orientacao(orientation_id)
            self.after(0, lambda: self._on_duplicate_result(res))
        
        threading.Thread(target=duplicate, daemon=True).start()
    
    def _on_duplicate_result(self, res: Dict):
        """Callback após duplicar"""
        if res.get('success'):
            self._show_message("Orientação duplicada com sucesso!")
            self._load_history()
        else:
            self._show_message(f"Erro ao duplicar: {res.get('message', 'Erro')}")
    
    def _confirm_delete_orientation(self, orientation_id: int):
        """Mostra confirmação antes de deletar"""
        # Criar modal de confirmação
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar Exclusão")
        modal.geometry("400x200")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        
        # Centralizar
        modal.update_idletasks()
        
        # Conteúdo
        ctk.CTkLabel(modal, text="Confirmar Exclusão", font=font(16, "bold"),
                    text_color=self.colors["text"]).pack(pady=(20, 8))
        
        ctk.CTkLabel(modal, text="Esta ação não pode ser desfeita.\nDeseja realmente excluir esta orientação?",
                    font=font(12), text_color=self.colors["text_muted"]).pack(pady=(0, 20))
        
        # Botões
        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack()
        
        def on_confirm():
            modal.destroy()
            self._delete_orientation(orientation_id)
        
        ctk.CTkButton(btn_frame, text="Cancelar", width=100,
                     fg_color=self.colors["bg_alt"], text_color=self.colors["text"],
                     command=modal.destroy).pack(side="left", padx=8)
        
        ctk.CTkButton(btn_frame, text="Excluir", width=100,
                     fg_color="red", text_color="white",
                     command=on_confirm).pack(side="left", padx=8)
    
    def _save_orientation(self):
        """Salva ou atualiza a orientação"""
        if not self.selected_student_id:
            self._show_message("Selecione um estudante primeiro.")
            return
        
        # Coletar dados do formulário
        titulo = self.entry_titulo.get().strip() if self.entry_titulo else ""
        if not titulo:
            titulo = f"Orientação - {datetime.now().strftime('%d/%m/%Y')}"
        
        tema = self.entry_tema.get().strip() if self.entry_tema else ""
        
        # Coletar conteúdo dos textboxes (remover espaços em branco extras)
        content = ""
        if self.text_conteudo:
            content = self.text_conteudo.get("0.0", "end-1c").strip()
        
        motivational_message = ""
        if self.text_mensagem:
            motivational_message = self.text_mensagem.get("0.0", "end-1c").strip()
        
        # CTkCheckBox.get() retorna int (0 ou 1), converter para boolean
        is_markdown = bool(self.check_markdown.get()) if self.check_markdown else False
        
        # Coletar valores dos componentes dinâmicos e montar action_plan
        action_plan = []
        for comp in self.dynamic_components:
            comp_id = comp['id']
            if comp_id in self.dynamic_widgets:
                widget_info = self.dynamic_widgets[comp_id]
                widget = widget_info['widget']
                widget_type = widget_info['type']
                label = widget_info['label']
                
                if widget_type == 'text':
                    value = widget.get().strip() if hasattr(widget, 'get') else ""
                    if value:
                        action_plan.append({'text': f"{label}: {value}", 'done': False})
                elif widget_type == 'textarea':
                    value = widget.get("0.0", "end-1c").strip() if hasattr(widget, 'get') else ""
                    if value:
                        action_plan.append({'text': f"{label}: {value}", 'done': False})
                elif widget_type == 'checkbox':
                    checked = bool(widget.get()) if hasattr(widget, 'get') else False
                    action_plan.append({'text': label, 'done': checked})
                elif widget_type == 'date':
                    value = widget.get().strip() if hasattr(widget, 'get') else ""
                    if value:
                        action_plan.append({'text': f"{label}: {value}", 'done': False})
        
        dados = {
            'student_id': self.selected_student_id,
            'title': titulo,
            'theme': tema,
            'session_date': datetime.now().strftime('%Y-%m-%d'),
            'content': content,
            'is_markdown': is_markdown,
            'motivational_message': motivational_message,
            'action_plan': action_plan
        }
        
        # Log para debug
        print(f"[DEBUG] Salvando orientação: is_editing={self.is_editing}, editing_id={self.editing_orientation_id}")
        print(f"[DEBUG] Dados: {dados}")
        
        def save():
            if self.is_editing and self.editing_orientation_id:
                # Atualizar orientação existente
                res = self.servico_orientacoes.atualizar_orientacao(self.editing_orientation_id, dados)
            else:
                # Criar nova orientação
                res = self.servico_orientacoes.criar_orientacao(dados)
            self.after(0, lambda: self._on_save_result(res))
        
        threading.Thread(target=save, daemon=True).start()
    
    def _on_save_result(self, res: Dict):
        """Callback após salvar"""
        if res.get('success'):
            if self.is_editing:
                self._show_message("Orientação atualizada com sucesso!")
            else:
                self._show_message("Orientação salva com sucesso!")
            self._reset_form()
            # Recarregar histórico se visível
            if self.current_tab == "history":
                self._load_history()
        else:
            self._show_message(f"Erro ao salvar: {res.get('message', 'Erro desconhecido')}")
    
    def _delete_orientation(self, orientation_id: int):
        """Deleta uma orientação"""
        if not orientation_id:
            return
        
        def delete():
            res = self.servico_orientacoes.deletar_orientacao(orientation_id)
            self.after(0, lambda: self._on_delete_result(res))
        
        threading.Thread(target=delete, daemon=True).start()
    
    def _edit_orientation(self, orientation: Dict):
        """Carrega uma orientação existente para edição"""
        orientation_id = orientation.get('id')
        if not orientation_id:
            return
        
        # Define estado de edição
        self.editing_orientation_id = orientation_id
        self.is_editing = True
        
        # Muda para a tab de nova orientação
        self._switch_tab("new")
        
        # Atualiza o botão salvar para mostrar que está editando
        self.btn_salvar.configure(text="Atualizar Orientação")
        
        # Preenche o formulário com os dados existentes
        self._populate_form(orientation)
        
        # Atualiza o subtítulo
        if self.selected_student:
            nome = self.selected_student.get('name', 'Aluno')
            self.subtitle_label.configure(text=f"Editando orientação para: {nome}")
    
    def _populate_form(self, orientation: Dict):
        """Preenche o formulário com dados de uma orientação existente"""
        # NOTA: NÃO chamar _reset_form() aqui porque ele reseta o estado de edição!
        # Apenas limpa os campos de texto manualmente
        
        # Limpa campos de texto (sem resetar estado de edição)
        if self.entry_titulo:
            self.entry_titulo.delete(0, "end")
        if self.entry_tema:
            self.entry_tema.delete(0, "end")
        if self.text_mensagem:
            self.text_mensagem.delete("0.0", "end")
        if self.text_conteudo:
            self.text_conteudo.delete("0.0", "end")
        
        # Limpa componentes dinâmicos e referências de widgets
        self.dynamic_components = []
        self.action_plan = []
        self.dynamic_widgets = {}
        
        # Preenche título
        titulo = orientation.get('title', '')
        if titulo and self.entry_titulo:
            self.entry_titulo.insert(0, titulo)
        
        # Preenche tema
        tema = orientation.get('theme', '')
        if tema and self.entry_tema:
            self.entry_tema.insert(0, tema)
        
        # Preenche data
        session_date = orientation.get('session_date', '')
        if session_date and self.entry_data:
            try:
                # Converte de YYYY-MM-DD para DD/MM/YYYY
                date_obj = datetime.fromisoformat(session_date.replace('Z', ''))
                formatted_date = date_obj.strftime('%d/%m/%Y')
                self.entry_data.delete(0, "end")
                self.entry_data.insert(0, formatted_date)
            except:
                pass
        
        # Preenche mensagem motivacional
        motivational_message = orientation.get('motivational_message', '')
        if motivational_message and self.text_mensagem:
            self.text_mensagem.insert("0.0", motivational_message)
        
        # Preenche conteúdo
        content = orientation.get('content', '')
        if content and self.text_conteudo:
            self.text_conteudo.insert("0.0", content)
        
        # Preenche checkbox markdown
        is_markdown = orientation.get('is_markdown', False)
        if self.check_markdown:
            if is_markdown:
                self.check_markdown.select()
            else:
                self.check_markdown.deselect()
        
        # Carrega action plan se existir
        action_plan_data = orientation.get('action_plan', [])
        if action_plan_data:
            try:
                if isinstance(action_plan_data, str):
                    self.action_plan = json.loads(action_plan_data)
                else:
                    self.action_plan = action_plan_data
            except:
                self.action_plan = []
        
        # Carrega componentes dinâmicos do action_plan
        self._load_action_plan_as_components()
    
    def _load_action_plan_as_components(self):
        """Converte o action_plan em componentes dinâmicos para visualização"""
        self.dynamic_components = []
        for i, item in enumerate(self.action_plan):
            task_text = item.get('text', '') if isinstance(item, dict) else str(item)
            self.dynamic_components.append({
                'id': f"task_{i}",
                'type': 'checkbox',
                'label': task_text,
                'checked': item.get('done', False) if isinstance(item, dict) else False
            })
        self._render_preview()
    
    def _on_delete_result(self, res: Dict):
        """Callback após deletar"""
        if res.get('success'):
            self._show_message("Orientação deletada!")
            self._load_history()
        else:
            self._show_message(f"Erro ao deletar: {res.get('message', 'Erro')}")
    
    def _reset_form(self):
        """Reseta o formulário e o estado de edição"""
        # Limpa campos de texto
        if self.entry_titulo:
            self.entry_titulo.delete(0, "end")
        if self.entry_tema:
            self.entry_tema.delete(0, "end")
        if self.text_mensagem:
            self.text_mensagem.delete("0.0", "end")
        if self.text_conteudo:
            self.text_conteudo.delete("0.0", "end")
        
        # Limpa componentes dinâmicos e referências de widgets
        self.dynamic_components = []
        self.action_plan = []
        self.dynamic_widgets = {}
        self._render_preview()
        
        # Reseta estado de edição
        self.editing_orientation_id = None
        self.is_editing = False
        
        # Reseta texto do botão
        self.btn_salvar.configure(text="Salvar Orientação")
        
        # Atualiza subtítulo
        if self.selected_student:
            nome = self.selected_student.get('name', 'Aluno')
            self.subtitle_label.configure(text=f"Criando orientação para: {nome}")
    
    def _export_json(self):
        """Exporta os dados como JSON"""
        data = {
            'student_id': self.selected_student_id,
            'components': self.dynamic_components,
            'exported_at': datetime.now().isoformat()
        }
        
        # Salvar em arquivo
        filename = f"orientacao_{self.selected_student_id or 'template'}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._show_message(f"Exportado para {filename}")
        except Exception as e:
            self._show_message(f"Erro ao exportar: {e}")
    
    def _choose_files(self):
        """Abre diálogo para escolher arquivos"""
        # No customtkinter, precisamos usar tkinter.filedialog
        from tkinter import filedialog
        
        files = filedialog.askopenfilenames(
            title="Selecionar Arquivos",
            filetypes=[
                ("Todos os arquivos", "*.*"),
                ("PDF", "*.pdf"),
                ("Imagens", "*.png *.jpg *.jpeg"),
                ("Documentos", "*.doc *.docx")
            ]
        )
        
        if files:
            self.label_files.configure(text=f"{len(files)} arquivo(s) selecionado(s)")
            self._selected_files = files
    
    def _show_message(self, message: str):
        """Mostra uma mensagem para o usuário"""
        # Criar um toast/notificação simples
        toast = ctk.CTkFrame(self, fg_color=self.colors["text"], corner_radius=8)
        toast.place(relx=0.5, rely=0.1, anchor="n")
        
        label = ctk.CTkLabel(toast, text=message, font=font(12), text_color="white")
        label.pack(padx=20, pady=10)
        
        # Remover após 3 segundos
        self.after(3000, lambda: toast.destroy())
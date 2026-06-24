from future import annotations
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime, date
import threading
import json
import logging
from typing import Any
from services.orientacoes import servico_orientacoes
from services.estudantes import ServicoEstudante
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    PrimaryButton,
    GhostButton,
    Badge,
)
logger = logging.getLogger("apps.desktop")
═══════════════════════════════════════════════════════════════════════════════
 Paleta dedicada
═══════════════════════════════════════════════════════════════════════════════
ORIENTACOES_COLORS: dictstr, str = {
    "bg":            THEME"bg",
    "card":          THEME"card",
    "card_alt":      THEME"bg_alt",
    "border":        THEME"border",
    "border_strong": THEME"border_strong",
    "primary":       THEME"primary",
    "primary_light": THEME"primary_light",
    "primary_soft":  THEME"primary_soft",
    "text":          THEME"text",
    "text_muted":    THEME"text_muted",
    "text_secondary":THEME"text_secondary",
    "danger":        THEME"danger",
    "danger_soft":   THEME"danger_soft",
    "success":       THEME"success",
    "success_soft":  THEME"success_soft",
    "warning":       THEME"warning",
    "warning_soft":  THEME"warning_soft",
}
═══════════════════════════════════════════════════════════════════════════════
 Componentes de apoio
═══════════════════════════════════════════════════════════════════════════════
class StudentCard(ctk.CTkFrame):
    """Card compacto de estudante para a lista lateral."""
def __init__(self, parent, student: dict[str, Any], on_select):
    super().__init__(
        parent,
        fg_color=ORIENTACOES_COLORS["card"],
        corner_radius=RADIUS["input"],
        border_width=1,
        border_color=ORIENTACOES_COLORS["border"],
    )
    self._student = student
    self._on_select = on_select
    self._selected = False
    self._build()
def _build(self):
    nome = self._student.get("name", "N/A")
    course = self._student.get("course", "Curso N/A")
    initials = "".join([n[0] for n in nome.split()[:2]]).upper()
    inner = ctk.CTkFrame(self, fg_color="transparent")
    inner.pack(fill="x", padx=14, pady=10)
    avatar = ctk.CTkFrame(
        inner, width=36, height=36,
        fg_color=ORIENTACOES_COLORS["primary_soft"],
        corner_radius=18,
    )
    avatar.pack(side="left", padx=(0, 10))
    avatar.pack_propagate(False)
    ctk.CTkLabel(
        avatar, text=initials, font=font(12, "bold"),
        text_color=ORIENTACOES_COLORS["primary"],
    ).place(relx=0.5, rely=0.5, anchor="center")
    txt = ctk.CTkFrame(inner, fg_color="transparent")
    txt.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(txt, text=nome, font=font(13, "bold"),
                 text_color=ORIENTACOES_COLORS["text"]).pack(anchor="w")
    ctk.CTkLabel(txt, text=course, font=font(11),
                 text_color=ORIENTACOES_COLORS["text_muted"]).pack(anchor="w")
    for w in (self, inner):
        w.bind("<Button-1>", lambda _: self._on_select(self._student, self))
def set_selected(self, selected: bool) -> None:
    self._selected = selected
    self.configure(
        fg_color=ORIENTACOES_COLORS["primary_soft"]
        if selected else ORIENTACOES_COLORS["card"]
    )
class TabButton(ctk.CTkButton):
    """Botão de tab com estilo ativo/inativo."""
def __init__(self, parent, text: str, command, initial: bool = False):
    super().__init__(
        parent,
        text=text,
        fg_color=ORIENTACOES_COLORS["card"] if initial else "transparent",
        text_color=ORIENTACOES_COLORS["text"] if initial else ORIENTACOES_COLORS["text_muted"],
        font=font(12, "bold" if initial else "normal"),
        width=140,
        height=32,
        corner_radius=6,
        command=command,
    )
class OrientationHistoryCard(ctk.CTkFrame):
    """Card de orientação exibido no histórico."""
def __init__(self, parent, orientation: dict[str, Any], on_view, on_edit, on_duplicate, on_delete):
    super().__init__(
        parent,
        fg_color="white",
        corner_radius=RADIUS["card"],
        border_width=1,
        border_color=ORIENTACOES_COLORS["border"],
    )
    self._orientation = orientation
    self._on_view = on_view
    self._on_edit = on_edit
    self._on_duplicate = on_duplicate
    self._on_delete = on_delete
    self._build()
def _build(self):
    inner = ctk.CTkFrame(self, fg_color="transparent")
    inner.pack(fill="x", padx=16, pady=12)
    # Data (círculo)
    date_str = self._orientation.get("session_date", "")
    day = "?"
    if date_str:
        try:
            day = datetime.fromisoformat(date_str.replace("Z", "")).day
        except Exception:
            pass
    date_circle = ctk.CTkFrame(
        inner, width=40, height=40,
        fg_color=ORIENTACOES_COLORS["primary_soft"],
        corner_radius=20,
    )
    date_circle.pack(side="left", padx=(0, 12))
    date_circle.pack_propagate(False)
    ctk.CTkLabel(
        date_circle, text=str(day), font=font(14, "bold"),
        text_color=ORIENTACOES_COLORS["primary"],
    ).place(relx=0.5, rely=0.5, anchor="center")
    # Info
    info = ctk.CTkFrame(inner, fg_color="transparent")
    info.pack(side="left", fill="x", expand=True)
    title = self._orientation.get("title", "Orientação")
    ctk.CTkLabel(info, text=title, font=font(14, "bold"),
                 text_color=ORIENTACOES_COLORS["text"]).pack(anchor="w")
    theme = self._orientation.get("theme", "Geral")
    Badge(info, text=theme, color=ORIENTACOES_COLORS["primary"]).pack(anchor="w", pady=(4, 0))
    content = self._orientation.get("content", "")
    if content:
        preview = content[:120] + ("..." if len(content) > 120 else "")
        ctk.CTkLabel(
            info, text=preview, font=font(10),
            text_color=ORIENTACOES_COLORS["text_muted"],
            wraplength=320, justify="left",
        ).pack(anchor="w", pady=(4, 0))
    # Ações
    btns = ctk.CTkFrame(inner, fg_color="transparent")
    btns.pack(side="right")
    orientation_id = self._orientation.get("id")
    GhostButton(btns, text="Ver", command=lambda: self._on_view(self._orientation),
                width=52, height=28).pack(side="left", padx=(0, 4))
    PrimaryButton(btns, text="Editar", command=lambda: self._on_edit(self._orientation),
                  width=52, height=28).pack(side="left", padx=(0, 4))
    GhostButton(btns, text="Duplicar",
                command=lambda o=orientation_id: self._on_duplicate(o),
                width=64, height=28).pack(side="left", padx=(0, 4))
    GhostButton(
        btns, text="Excluir",
        command=lambda o=orientation_id: self._on_delete(o),
        width=56, height=28,
        text_color=ORIENTACOES_COLORS["danger"],
        hover_color=ORIENTACOES_COLORS["danger_soft"],
    ).pack(side="left")
═══════════════════════════════════════════════════════════════════════════════
 Modais
═══════════════════════════════════════════════════════════════════════════════
class ViewOrientationModal(ctk.CTkToplevel):
    def init(self, parent, orientation: dictstr, Any):
        super().init(parent)
        self.title("Visualizar Orientação")
        self.geometry("720x620")
        self.configure(fg_color=ORIENTACOES_COLORS"card")
        self.withdraw()
        self._center(parent, 720, 620)
    scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=24, pady=24)
    ctk.CTkLabel(
        scroll, text=orientation.get("title", "Orientação"),
        font=themed_font("h3", "bold"), text_color=ORIENTACOES_COLORS["text"],
    ).pack(anchor="w", pady=(0, 12))
    tags = ctk.CTkFrame(scroll, fg_color="transparent")
    tags.pack(anchor="w", pady=(0, 12))
    theme = orientation.get("theme", "Geral")
    Badge(tags, text=theme, color=ORIENTACOES_COLORS["primary"]).pack(side="left", padx=(0, 8))
    session_date = orientation.get("session_date", "")
    if session_date:
        try:
            d = datetime.fromisoformat(session_date.replace("Z", ""))
            ctk.CTkLabel(
                tags, text=f"📅 {d.strftime('%d/%m/%Y')}",
                font=themed_font("overline"), text_color=ORIENTACOES_COLORS["text_muted"],
            ).pack(side="left")
        except Exception:
            pass
    motivational = orientation.get("motivational_message", "")
    if motivational:
        frame = Card(scroll, padding=(16, 12))
        frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            frame.body, text=f'"{motivational}"',
            font=themed_font("body"), text_color=ORIENTACOES_COLORS["primary"],
            wraplength=640, justify="left",
        ).pack(anchor="w")
    content = orientation.get("content", "")
    if content:
        ctk.CTkLabel(scroll, text="Conteúdo", font=themed_font("caption", "bold"),
                     text_color=ORIENTACOES_COLORS["text"]).pack(anchor="w", pady=(8, 4))
        content_frame = Card(scroll, padding=(16, 12))
        content_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            content_frame.body, text=content,
            font=themed_font("body"), text_color=ORIENTACOES_COLORS["text"],
            wraplength=640, justify="left",
        ).pack(anchor="w")
    action_plan = orientation.get("action_plan", [])
    if action_plan:
        ctk.CTkLabel(scroll, text="Plano de Ação", font=themed_font("caption", "bold"),
                     text_color=ORIENTACOES_COLORS["text"]).pack(anchor="w", pady=(8, 4))
        for item in action_plan:
            task_text = item.get("text", "") if isinstance(item, dict) else str(item)
            done = item.get("done", False) if isinstance(item, dict) else False
            task_frame = Card(scroll, padding=(12, 8))
            task_frame.pack(fill="x", pady=(0, 6))
            cb = ctk.CTkCheckBox(task_frame.body, text=task_text,
                                 font=themed_font("body"),
                                 state="disabled" if done else "normal")
            cb.pack(anchor="w")
            if done:
                cb.select()
    PrimaryButton(scroll, text="Fechar", command=self.destroy, width=140).pack(pady=(16, 0))
    self.deiconify()
    self.grab_set()
def _center(self, parent, w, h):
    self.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
    self.geometry(f"+{x}+{y}")
class ConfirmDeleteModal(ctk.CTkToplevel):
    def init(self, parent, orientation_id: int, on_confirm):
        super().init(parent)
        self._on_confirm = on_confirm
        self.title("Confirmar Exclusão")
        self.geometry("420x220")
        self.configure(fg_color=ORIENTACOES_COLORS"card")
        self.withdraw()
        self._center(parent, 420, 220)
    inner = ctk.CTkFrame(self, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=24, pady=24)
    ctk.CTkLabel(inner, text="Confirmar Exclusão",
                 font=themed_font("h3", "bold"),
                 text_color=ORIENTACOES_COLORS["text"]).pack(pady=(0, 8))
    ctk.CTkLabel(
        inner,
        text="Esta ação não pode ser desfeita.\nDeseja realmente excluir esta orientação?",
        font=themed_font("body"), text_color=ORIENTACOES_COLORS["text_muted"],
        justify="center",
    ).pack(pady=(0, 20))
    btns = ctk.CTkFrame(inner, fg_color="transparent")
    btns.pack()
    GhostButton(btns, text="Cancelar", command=self.destroy, width=120).pack(side="left", padx=(0, 8))
    PrimaryButton(btns, text="Excluir", width=120,
                  command=lambda: self._confirm(orientation_id)).pack(side="left")
    self.deiconify()
    self.grab_set()
def _center(self, parent, w, h):
    self.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
    self.geometry(f"+{x}+{y}")
def _confirm(self, orientation_id: int) -> None:
    self.destroy()
    self._on_confirm(orientation_id)
═══════════════════════════════════════════════════════════════════════════════
 Frame principal
═══════════════════════════════════════════════════════════════════════════════
class OrientacoesFrame(ctk.CTkFrame):
    def init(self, parent, controller):
        super().init(parent, fg_color=ORIENTACOES_COLORS"bg")
        self.controller = controller
        self.servico_estudante = ServicoEstudante()
    self.selected_student: dict[str, Any] | None = None
    self.selected_student_id: int | None = None
    self.current_tab: str = "new"
    self.dynamic_components: list[dict[str, Any]] = []
    self.action_plan: list[dict[str, Any]] = []
    self.editing_orientation_id: int | None = None
    self.is_editing: bool = False
    self.dynamic_widgets: dict[str, Any] = {}
    self._students_list: list[dict[str, Any]] = []
    self.grid_rowconfigure(0, weight=0)
    self.grid_rowconfigure(1, weight=0)
    self.grid_rowconfigure(2, weight=1)
    self.grid_columnconfigure(0, weight=1)
    self._build()
    self._load_students()
# ── layout ---------------------------------------------------------------
def _build(self):
    self._build_header()
    self.main_container = ctk.CTkFrame(self, fg_color="transparent")
    self.main_container.grid(row=1, column=0, sticky="nsew",
                             padx=SPACING["page_x"], pady=(0, 12))
    self.main_container.grid_rowconfigure(0, weight=1)
    self.main_container.grid_columnconfigure(0, weight=1, minsize=280)
    self.main_container.grid_columnconfigure(1, weight=4, minsize=600)
    self._build_students_panel()
    self._build_builder_panel()
def _build_header(self):
    header = PageHeader(
        self,
        title="Orientações",
        subtitle="Gerencie orientações e acompanhamentos",
    )
    header.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 12))
    self.subtitle_label = ctk.CTkLabel(
        header, text="Selecione um estudante para começar",
        font=themed_font("body"), text_color=ORIENTACOES_COLORS["text_muted"],
    )
    self.subtitle_label.pack(side="left", padx=(12, 0))
    self.btn_salvar = PrimaryButton(
        header, text="Salvar Orientação",
        command=self._save_orientation, width=160,
    )
    self.btn_salvar.pack(side="right")
def _build_students_panel(self):
    container = Card(self.main_container)
    container.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
    container.grid_rowconfigure(1, weight=1)
    container.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        container.body, text="Estudantes",
        font=themed_font("h4", "bold"), text_color=ORIENTACOES_COLORS["text"],
    ).pack(anchor="w", padx=16, pady=(14, 6))
    search = ctk.CTkFrame(
        container.body, fg_color=ORIENTACOES_COLORS["card_alt"],
        corner_radius=RADIUS["input"], border_width=1,
        border_color=ORIENTACOES_COLORS["border"], height=36,
    )
    search.pack(fill="x", padx=16, pady=(0, 8))
    search.pack_propagate(False)
    ctk.CTkLabel(search, text="🔍", font=themed_font("body"),
                 text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="left", padx=10)
    self.entry_busca = ctk.CTkEntry(
        search, placeholder_text="Filtrar alunos...",
        fg_color="transparent", border_width=0, font=themed_font("body"),
    )
    self.entry_busca.pack(side="left", fill="both", expand=True)
    self.entry_busca.bind("<KeyRelease>", lambda _: self._filter_students())
    self.scroll_alunos = ctk.CTkScrollableFrame(container.body, fg_color="transparent")
    self.scroll_alunos.pack(fill="both", expand=True, padx=10, pady=(0, 10))
def _build_builder_panel(self):
    container = Card(self.main_container)
    container.grid(row=0, column=1, sticky="nsew")
    container.grid_rowconfigure(1, weight=1)
    container.grid_columnconfigure(0, weight=1)
    tabs = ctk.CTkFrame(
        container.body, fg_color=ORIENTACOES_COLORS["card_alt"],
        corner_radius=RADIUS["input"], border_width=1,
        border_color=ORIENTACOES_COLORS["border"], height=42,
    )
    tabs.pack(fill="x", padx=16, pady=(16, 8))
    tabs.pack_propagate(False)
    self.btn_tab_new = TabButton(tabs, "Nova Orientação", lambda: self._switch_tab("new"), initial=True)
    self.btn_tab_new.pack(side="left", padx=4, pady=4)
    self.btn_tab_history = TabButton(tabs, "Histórico", lambda: self._switch_tab("history"))
    self.btn_tab_history.pack(side="left", padx=4, pady=4)
    self.btn_tab_stats = TabButton(tabs, "Estatísticas", lambda: self._switch_tab("stats"))
    self.btn_tab_stats.pack(side="left", padx=4, pady=4)
    self.content_scroll = ctk.CTkScrollableFrame(container.body, fg_color="transparent")
    self.content_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))
    self.tab_new = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
    self.tab_new.pack(fill="both", expand=True)
    self._build_new_tab()
    self.tab_history = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
    self._build_history_tab()
    self.tab_stats = ctk.CTkFrame(self.content_scroll, fg_color="transparent")
    self._build_stats_tab()
# ── nova orientação ------------------------------------------------------
def _build_new_tab(self):
    frm = self.tab_new
    self.entry_titulo = FormField(frm, "Título da Orientação",
                                  placeholder="Ex: Planejamento de Estudos Semanal")
    self.entry_titulo.pack(fill="x", pady=(0, 10))
    row = ctk.CTkFrame(frm, fg_color="transparent")
    row.pack(fill="x", pady=(0, 8))
    self.entry_data = FormField(row, "Data da Sessão",
                                initial=date.today().strftime("%d/%m/%Y"), width=200)
    self.entry_data.pack(side="left", padx=(0, 8))
    self.entry_tema = FormField(row, "Tema / Categoria",
                                placeholder="Ex: Organização, Ansiedade, Rotina")
    self.entry_tema.pack(side="left", padx=(12, 0))
    presets = ctk.CTkFrame(frm, fg_color="transparent")
    presets.pack(fill="x", pady=(0, 8))
    ctk.CTkLabel(presets, text="Modelos Rápidos:",
                 font=themed_font("caption", "bold"),
                 text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="left", padx=(0, 8))
    for key, preset in servico_orientacoes.get_presets().items():
        GhostButton(presets, text=preset["label"],
                    command=lambda k=key: self._apply_preset(k), width=120).pack(side="left", padx=(0, 6))
    self.text_mensagem = FormField(frm, "Mensagem Motivacional (Destaque)",
                                   placeholder="Escreva uma mensagem de apoio...",
                                   multiline=True, height=70)
    self.text_mensagem.pack(fill="x", pady=(0, 10))
    ctk.CTkFrame(frm, height=1, fg_color=ORIENTACOES_COLORS["border"]).pack(fill="x", pady=(0, 12))
    header_dyn = ctk.CTkFrame(frm, fg_color="transparent")
    header_dyn.pack(fill="x", pady=(0, 6))
    ctk.CTkLabel(header_dyn, text="Conteúdo Dinâmico",
                 font=themed_font("h4", "bold"),
                 text_color=ORIENTACOES_COLORS["text"]).pack(side="left")
    GhostButton(header_dyn, text="Exportar JSON", command=self._export_json, width=110).pack(side="right")
    self.preview_container = ctk.CTkFrame(
        frm, fg_color=ORIENTACOES_COLORS["card_alt"],
        corner_radius=RADIUS["card"], border_width=1,
        border_color=ORIENTACOES_COLORS["border"],
    )
    self.preview_container.pack(fill="x", pady=(0, 10))
    self.empty_preview = ctk.CTkLabel(
        self.preview_container,
        text="Adicione campos abaixo ou selecione um modelo...",
        font=themed_font("body"), text_color=ORIENTACOES_COLORS["text_muted"],
    )
    self.empty_preview.pack(pady=20)
    controls = ctk.CTkFrame(frm, fg_color=ORIENTACOES_COLORS["card_alt"],
                            corner_radius=RADIUS["input"])
    controls.pack(fill="x", pady=(0, 10))
    inner = ctk.CTkFrame(controls, fg_color="transparent")
    inner.pack(fill="x", padx=12, pady=10)
    ctk.CTkLabel(inner, text="Tipo:", font=themed_font("caption", "bold"),
                 text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="left")
    self.combo_field_type = ctk.CTkOptionMenu(
        inner, values=["Texto Curto", "Texto Longo", "Tarefa/Checkbox", "Data"],
        fg_color="white", button_color="white", width=120, height=28,
        font=themed_font("body"),
    )
    self.combo_field_type.pack(side="left", padx=(6, 12))
    self.entry_field_label = ctk.CTkEntry(
        inner, placeholder_text="Rótulo do campo...",
        width=180, height=28, font=themed_font("body"),
    )
    self.entry_field_label.pack(side="left", padx=(0, 8))
    PrimaryButton(inner, text="Adicionar", command=self._add_dynamic_field,
                  width=90, height=28).pack(side="left")
    self.text_conteudo = FormField(frm, "Conteúdo Principal",
                                   placeholder="Conteúdo da orientação...",
                                   multiline=True, height=120)
    self.text_conteudo.pack(fill="x", pady=(0, 10))
    self.check_markdown = ctk.CTkCheckBox(
        frm, text="Usar Markdown", font=themed_font("body"),
        checkbox_width=18, checkbox_height=18,
    )
    self.check_markdown.pack(anchor="w", pady=(0, 12))
    attach = ctk.CTkFrame(frm, fg_color=ORIENTACOES_COLORS["card_alt"],
                          corner_radius=RADIUS["card"])
    attach.pack(fill="x", pady=(0, 12))
    attach_inner = ctk.CTkFrame(attach, fg_color="transparent")
    attach_inner.pack(fill="x", padx=14, pady=12)
    ctk.CTkLabel(attach_inner, text="Anexos e Documentos",
                 font=themed_font("caption", "bold"),
                 text_color=ORIENTACOES_COLORS["text"]).pack(anchor="w", pady=(0, 8))
    btns_attach = ctk.CTkFrame(attach_inner, fg_color="transparent")
    btns_attach.pack(fill="x")
    self.btn_anexos = GhostButton(btns_attach, text="Escolher Arquivos",
                                   command=self._choose_files, width=120)
    self.btn_anexos.pack(side="left")
    self.label_files = ctk.CTkLabel(
        btns_attach, text="Nenhum arquivo selecionado",
        font=themed_font("caption"), text_color=ORIENTACOES_COLORS["text_muted"],
    )
    self.label_files.pack(side="left", padx=8)
    ctk.CTkFrame(frm, height=1, fg_color=ORIENTACOES_COLORS["border"]).pack(fill="x", pady=(0, 12))
    actions = ctk.CTkFrame(frm, fg_color="transparent")
    actions.pack(fill="x", pady=(0, 12))
    PrimaryButton(actions, text="Salvar Orientação", command=self._save_orientation,
                  width=160, height=40).pack(side="left")
    GhostButton(actions, text="Resetar", command=self._reset_form, width=100, height=40).pack(side="left", padx=12)
# ── histórico ------------------------------------------------------------
def _build_history_tab(self):
    self.tab_history.grid_rowconfigure(2, weight=1)
    self.tab_history.grid_columnconfigure(0, weight=1)
    filters = Card(self.tab_history, padding=(16, 12))
    filters.grid(row=0, column=0, sticky="ew", pady=(0, 12))
    row = ctk.CTkFrame(filters.body, fg_color="transparent")
    row.pack(fill="x")
    ctk.CTkLabel(row, text="Buscar:", font=themed_font("caption", "bold"),
                 text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="left")
    self.entry_history_search = ctk.CTkEntry(
        row, placeholder_text="Título, tema ou conteúdo...",
        width=200, height=30, font=themed_font("body"),
    )
    self.entry_history_search.pack(side="left", padx=(6, 16))
    self.entry_history_search.bind("<Return>", lambda _: self._load_history())
    ctk.CTkLabel(row, text="De:", font=themed_font("caption", "bold"),
                 text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="left")
    self.entry_history_date_from = ctk.CTkEntry(
        row, placeholder_text="DD/MM/AAAA", width=100, height=30, font=themed_font("body"),
    )
    self.entry_history_date_from.pack(side="left", padx=(6, 16))
    ctk.CTkLabel(row, text="Até:", font=themed_font("caption", "bold"),
                 text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="left")
    self.entry_history_date_to = ctk.CTkEntry(
        row, placeholder_text="DD/MM/AAAA", width=100, height=30, font=themed_font("body"),
    )
    self.entry_history_date_to.pack(side="left", padx=(6, 16))
    PrimaryButton(row, text="Filtrar", command=self._load_history, width=70, height=30).pack(side="left", padx=(0, 4))
    GhostButton(row, text="Limpar", command=self._clear_history_filters, width=70, height=30).pack(side="left")
    self.history_count_label = ctk.CTkLabel(
        self.tab_history, text="", font=themed_font("body"),
        text_color=ORIENTACOES_COLORS["text_muted"],
    )
    self.history_count_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))
    self.history_container = ctk.CTkScrollableFrame(self.tab_history, fg_color="transparent")
    self.history_container.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
    self.history_placeholder = ctk.CTkLabel(
        self.history_container,
        text="Selecione um estudante para ver o histórico",
        font=themed_font("h4"), text_color=ORIENTACOES_COLORS["text_muted"],
    )
    self.history_placeholder.pack(pady=60)
# ── estatísticas ----------------------------------------------------------
def _build_stats_tab(self):
    self.tab_stats.grid_rowconfigure(0, weight=1)
    self.tab_stats.grid_columnconfigure(0, weight=1)
    self.stats_container = ctk.CTkFrame(self.tab_stats, fg_color="transparent")
    self.stats_container.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
    ctk.CTkLabel(
        self.stats_container,
        text="Selecione um estudante para ver estatísticas",
        font=themed_font("h4"), text_color=ORIENTACOES_COLORS["text_muted"],
    ).pack(pady=60)
# ── estudantes -----------------------------------------------------------
def _load_students(self):
    def fetch():
        res = self.servico_estudante.listar_estudantes()
        self.after(0, lambda: self._render_students(res))
    threading.Thread(target=fetch, daemon=True).start()
def _render_students(self, res):
    try:
        if not self.scroll_alunos.winfo_exists():
            return
    except Exception:
        return
    for w in self.scroll_alunos.winfo_children():
        w.destroy()
    students: list[dict[str, Any]] = []
    if isinstance(res, dict):
        if res.get("success") is False:
            ctk.CTkLabel(
                self.scroll_alunos,
                text=f"Erro ao carregar alunos:\n{res.get('message', '')}",
                font=themed_font("body"), text_color=ORIENTACOES_COLORS["danger"],
                wraplength=220, justify="center",
            ).pack(pady=20)
            return
        data = res.get("data", [])
        if isinstance(data, dict):
            students = data.get("students", []) or data.get("results", [])
        elif isinstance(data, list):
            students = data
    elif isinstance(res, list):
        students = res
    if not students:
        ctk.CTkLabel(
            self.scroll_alunos, text="Nenhum aluno encontrado",
            font=themed_font("body"), text_color=ORIENTACOES_COLORS["text_muted"],
            wraplength=220, justify="center",
        ).pack(pady=20)
        return
    self._students_list = students
    for st in students:
        StudentCard(self.scroll_alunos, st, self._select_student).pack(fill="x", pady=3, padx=2)
def _select_student(self, student: dict[str, Any], card: StudentCard):
    self.selected_student = student
    self.selected_student_id = student.get("id") or student.get("pk")
    nome = student.get("name", "Aluno")
    self.subtitle_label.configure(text=f"Criando orientação para: {nome}")
    for w in self.scroll_alunos.winfo_children():
        if isinstance(w, StudentCard):
            w.set_selected(False)
    card.set_selected(True)
    if self.current_tab == "history":
        self._load_history()
    elif self.current_tab == "stats":
        self._load_stats()
def _filter_students(self):
    query = (self.entry_busca.get() or "").lower().strip()
    for w in self.scroll_alunos.winfo_children():
        w.destroy()
    filtered = [s for s in self._students_list if query in (s.get("name", "")).lower()]
    if not filtered:
        ctk.CTkLabel(self.scroll_alunos, text="Nenhum resultado",
                     font=themed_font("body"),
                     text_color=ORIENTACOES_COLORS["text_muted"]).pack(pady=20)
        return
    for st in filtered:
        StudentCard(self.scroll_alunos, st, self._select_student).pack(fill="x", pady=3, padx=2)
# ── tabs -----------------------------------------------------------------
def _switch_tab(self, tab: str):
    self.current_tab = tab
    for btn in (self.btn_tab_new, self.btn_tab_history, self.btn_tab_stats):
        btn.configure(fg_color="transparent", text_color=ORIENTACOES_COLORS["text_muted"])
    for frame in (self.tab_new, self.tab_history, self.tab_stats):
        frame.pack_forget()
    if tab == "new":
        self.btn_tab_new.configure(fg_color=ORIENTACOES_COLORS["card"],
                                   text_color=ORIENTACOES_COLORS["text"])
        self.tab_new.pack(fill="both", expand=True)
    elif tab == "history":
        self.btn_tab_history.configure(fg_color=ORIENTACOES_COLORS["card"],
                                       text_color=ORIENTACOES_COLORS["text"])
        self.tab_history.pack(fill="both", expand=True)
        self._load_history()
    elif tab == "stats":
        self.btn_tab_stats.configure(fg_color=ORIENTACOES_COLORS["card"],
                                     text_color=ORIENTACOES_COLORS["text"])
        self.tab_stats.pack(fill="both", expand=True)
        self._load_stats()
# ── conteúdo dinâmico ----------------------------------------------------
def _apply_preset(self, preset_key: str):
    preset = servico_orientacoes.get_preset(preset_key)
    if not preset:
        return
    self.dynamic_components = []
    for comp in preset.get("components", []):
        self.dynamic_components.append({
            "id": f"{comp['id']}_{datetime.now().timestamp()}",
            "type": comp["type"],
            "label": comp["label"],
        })
    self._render_preview()
def _add_dynamic_field(self):
    type_map = {
        "Texto Curto": "text",
        "Texto Longo": "textarea",
        "Tarefa/Checkbox": "checkbox",
        "Data": "date",
    }
    field_type = type_map.get(self.combo_field_type.get(), "text")
    field_label = self.entry_field_label.get().strip() or "Campo"
    self.dynamic_components.append({
        "id": f"f_{datetime.now().timestamp()}",
        "type": field_type,
        "label": field_label,
    })
    self._render_preview()
    self.entry_field_label.delete(0, "end")
def _render_preview(self):
    try:
        if not self.preview_container.winfo_exists():
            return
    except Exception:
        return
    for w in self.preview_container.winfo_children():
        w.destroy()
    self.dynamic_widgets = {}
    if not self.dynamic_components:
        self.empty_preview = ctk.CTkLabel(
            self.preview_container,
            text="Adicione campos abaixo ou selecione um modelo...",
            font=themed_font("body"), text_color=ORIENTACOES_COLORS["text_muted"],
        )
        self.empty_preview.pack(pady=20)
        return
    for i, comp in enumerate(self.dynamic_components):
        row = ctk.CTkFrame(
            self.preview_container, fg_color="white",
            corner_radius=8, border_width=1, border_color=ORIENTACOES_COLORS["border"],
        )
        row.pack(fill="x", pady=4, padx=8)
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        comp_id = comp["id"]
        if comp["type"] == "text":
            entry = ctk.CTkEntry(inner, placeholder_text=comp["label"], width=300,
                                 font=themed_font("body"))
            entry.pack(side="left", fill="x", expand=True)
            if comp.get("value"):
                entry.insert(0, comp["value"])
            self.dynamic_widgets[comp_id] = {"widget": entry, "type": "text", "label": comp["label"]}
        elif comp["type"] == "textarea":
            tf = ctk.CTkFrame(inner, fg_color="transparent")
            tf.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(tf, text=comp["label"], font=themed_font("caption"),
                         text_color=ORIENTACOES_COLORS["text_muted"]).pack(anchor="w")
            text = ctk.CTkTextbox(tf, height=60, font=themed_font("body"))
            text.pack(fill="x", expand=True)
            if comp.get("value"):
                text.insert("1.0", comp["value"])
            self.dynamic_widgets[comp_id] = {"widget": text, "type": "textarea", "label": comp["label"]}
        elif comp["type"] == "checkbox":
            cb = ctk.CTkCheckBox(inner, text=comp["label"], font=themed_font("body"))
            cb.pack(side="left")
            if comp.get("checked"):
                cb.select()
            self.dynamic_widgets[comp_id] = {"widget": cb, "type": "checkbox", "label": comp["label"]}
        elif comp["type"] == "date":
            entry = ctk.CTkEntry(inner, placeholder_text=comp["label"], width=160,
                                 font=themed_font("body"))
            entry.pack(side="left", fill="x", expand=True)
            if comp.get("value"):
                entry.insert(0, comp["value"])
            self.dynamic_widgets[comp_id] = {"widget": entry, "type": "date", "label": comp["label"]}
        GhostButton(inner, text="X",
                    command=lambda idx=i: self._remove_component(idx),
                    width=30, height=30,
                    text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="right")
def _remove_component(self, index: int):
    if 0 <= index < len(self.dynamic_components):
        self.dynamic_components.pop(index)
        self._render_preview()
# ── histórico ------------------------------------------------------------
def _clear_history_filters(self):
    for field in ("entry_history_search", "entry_history_date_from", "entry_history_date_to"):
        if hasattr(self, field):
            getattr(self, field).delete(0, "end")
    self._load_history()
def _load_history(self):
    if not self.selected_student_id:
        for w in self.history_container.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.history_container,
            text="Selecione um estudante para ver o histórico",
            font=themed_font("h4"), text_color=ORIENTACOES_COLORS["text_muted"],
        ).pack(pady=60)
        return
    search = ""
    date_from = None
    date_to = None
    if hasattr(self, "entry_history_search"):
        search = self.entry_history_search.get().strip()
    if hasattr(self, "entry_history_date_from"):
        df = self.entry_history_date_from.get().strip()
        if df:
            try:
                date_from = datetime.strptime(df, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                pass
    if hasattr(self, "entry_history_date_to"):
        dt = self.entry_history_date_to.get().strip()
        if dt:
            try:
                date_to = datetime.strptime(dt, "%d/%m/%Y").strftime("%Y-%m-%d")
            except Exception:
                pass
    def fetch():
        res = servico_orientacoes.listar_orientacoes(
            id_estudante=self.selected_student_id,
            tema=search or None,
        )
        self.after(0, lambda: self._render_history(res))
    threading.Thread(target=fetch, daemon=True).start()
def _render_history(self, res):
    try:
        if not self.history_container.winfo_exists():
            return
    except Exception:
        return
    for w in self.history_container.winfo_children():
        w.destroy()
    if not isinstance(res, dict) or res.get("success") is False:
        ctk.CTkLabel(
            self.history_container, text="Erro ao carregar histórico",
            font=themed_font("body"), text_color=ORIENTACOES_COLORS["danger"],
        ).pack(pady=20)
        return
    data = res.get("data", {})
    orientations = data.get("orientations", [])
    total_count = data.get("pagination", {}).get("total", len(orientations))
    if hasattr(self, "history_count_label"):
        self.history_count_label.configure(text=f"{total_count} orientação(ões) encontrada(s)")
    if not orientations:
        ctk.CTkLabel(
            self.history_container,
            text="Nenhuma orientação encontrada\nComece criando uma nova orientação.",
            font=themed_font("body"), text_color=ORIENTACOES_COLORS["text_muted"],
        ).pack(pady=50)
        return
    for o in orientations:
        OrientationHistoryCard(
            self.history_container, o,
            on_view=self._view_orientation,
            on_edit=self._edit_orientation,
            on_duplicate=self._duplicate_orientation,
            on_delete=self._confirm_delete_orientation,
        ).pack(fill="x", pady=(0, 10))
# ── estatísticas ---------------------------------------------------------
def _load_stats(self):
    if not self.selected_student_id:
        return
    def fetch():
        res = servico_orientacoes.obter_estatisticas(self.selected_student_id)
        self.after(0, lambda: self._render_stats(res))
    threading.Thread(target=fetch, daemon=True).start()
def _render_stats(self, res):
    try:
        if not self.stats_container.winfo_exists():
            return
    except Exception:
        return
    for w in self.stats_container.winfo_children():
        w.destroy()
    if not isinstance(res, dict) or res.get("success") is False:
        ctk.CTkLabel(
            self.stats_container, text="Erro ao carregar estatísticas",
            font=themed_font("body"), text_color=ORIENTACOES_COLORS["danger"],
        ).pack(pady=20)
        return
    data = res.get("data", {})
    total = data.get("total", 0)
    by_theme = data.get("by_theme", [])
    by_month = data.get("by_month", [])
    row = ctk.CTkFrame(self.stats_container, fg_color="transparent")
    row.pack(fill="x", pady=(0, 16))
    # Total
    total_card = ctk.CTkFrame(row, fg_color=ORIENTACOES_COLORS["primary"],
                              corner_radius=RADIUS["card"])
    total_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
    inner = ctk.CTkFrame(total_card, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=20, pady=16)
    ctk.CTkLabel(inner, text=str(total), font=font(32, "bold"),
                 text_color="white").pack(anchor="w")
    ctk.CTkLabel(inner, text="Total de Orientações", font=font(12),
                 text_color="white").pack(anchor="w")
    # Por tema
    theme_card = ctk.CTkFrame(row, fg_color=ORIENTACOES_COLORS["card"],
                               corner_radius=RADIUS["card"],
                               border_width=1, border_color=ORIENTACOES_COLORS["border"])
    theme_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
    inner_t = ctk.CTkFrame(theme_card, fg_color="transparent")
    inner_t.pack(fill="both", expand=True, padx=20, pady=16)
    ctk.CTkLabel(inner_t, text="Por Tema", font=font(14, "bold"),
                 text_color=ORIENTACOES_COLORS["text"]).pack(anchor="w", pady=(0, 8))
    for item in by_theme[:5]:
        r = ctk.CTkFrame(inner_t, fg_color="transparent")
        r.pack(fill="x", pady=2)
        ctk.CTkLabel(r, text=item.get("theme", "Sem tema"), font=font(11),
                     text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="left")
        ctk.CTkLabel(r, text=str(item.get("count", 0)), font=font(11, "bold"),
                     text_color=ORIENTACOES_COLORS["primary"]).pack(side="right")
    # Por mês
    month_card = ctk.CTkFrame(row, fg_color=ORIENTACOES_COLORS["card"],
                               corner_radius=RADIUS["card"],
                               border_width=1, border_color=ORIENTACOES_COLORS["border"])
    month_card.pack(side="left", fill="both", expand=True)
    inner_m = ctk.CTkFrame(month_card, fg_color="transparent")
    inner_m.pack(fill="both", expand=True, padx=20, pady=16)
    ctk.CTkLabel(inner_m, text="Por Mês", font=font(14, "bold"),
                 text_color=ORIENTACOES_COLORS["text"]).pack(anchor="w", pady=(0, 8))
    for item in by_month[:6]:
        r = ctk.CTkFrame(inner_m, fg_color="transparent")
        r.pack(fill="x", pady=2)
        month_str = item.get("month", "")
        label = "-"
        if month_str:
            try:
                label = datetime.fromisoformat(month_str).strftime("%b/%Y")
            except Exception:
                label = month_str
        ctk.CTkLabel(r, text=label, font=font(11),
                     text_color=ORIENTACOES_COLORS["text_muted"]).pack(side="left")
        ctk.CTkLabel(r, text=str(item.get("count", 0)), font=font(11, "bold"),
                     text_color=ORIENTACOES_COLORS["primary"]).pack(side="right")
# ── ações ----------------------------------------------------------------
def _view_orientation(self, orientation: dict[str, Any]):
    ViewOrientationModal(self, orientation)
def _edit_orientation(self, orientation: dict[str, Any]):
    orientation_id = orientation.get("id")
    if not orientation_id:
        return
    self.editing_orientation_id = orientation_id
    self.is_editing = True
    self._switch_tab("new")
    self.btn_salvar.configure(text="Atualizar Orientação")
    self._populate_form(orientation)
    nome = self.selected_student.get("name", "Aluno") if self.selected_student else "Aluno"
    self.subtitle_label.configure(text=f"Editando orientação para: {nome}")
def _duplicate_orientation(self, orientation_id: int | None):
    if not orientation_id:
        return
    def duplicate():
        res = servico_orientacoes.duplicar_orientacao(orientation_id)
        self.after(0, lambda: self._on_duplicate_result(res))
    threading.Thread(target=duplicate, daemon=True).start()
def _on_duplicate_result(self, res: dict[str, Any]):
    if res.get("success"):
        self._show_message("Orientação duplicada com sucesso!")
        self._load_history()
    else:
        self._show_message(f"Erro ao duplicar: {res.get('message', 'Erro')}")
def _confirm_delete_orientation(self, orientation_id: int | None):
    if not orientation_id:
        return
    ConfirmDeleteModal(self, orientation_id, self._delete_orientation)
def _delete_orientation(self, orientation_id: int):
    def delete():
        res = servico_orientacoes.deletar_orientacao(orientation_id)
        self.after(0, lambda: self._on_delete_result(res))
    threading.Thread(target=delete, daemon=True).start()
def _on_delete_result(self, res: dict[str, Any]):
    if res.get("success"):
        self._show_message("Orientação deletada!")
        self._load_history()
    else:
        self._show_message(f"Erro ao deletar: {res.get('message', 'Erro')}")
# ── salvar ---------------------------------------------------------------
def _save_orientation(self):
    if not self.selected_student_id:
        self._show_message("Selecione um estudante primeiro.")
        return
    titulo = self.entry_titulo.get().strip() if self.entry_titulo else ""
    if not titulo:
        titulo = f"Orientação - {date.today().strftime('%d/%m/%Y')}"
    tema = self.entry_tema.get().strip() if self.entry_tema else ""
    content = self.text_conteudo.get().strip() if self.text_conteudo else ""
    motivational_message = self.text_mensagem.get().strip() if self.text_mensagem else ""
    is_markdown = bool(self.check_markdown.get()) if self.check_markdown else False
    action_plan = []
    for comp in self.dynamic_components:
        comp_id = comp["id"]
        if comp_id in self.dynamic_widgets:
            info = self.dynamic_widgets[comp_id]
            widget = info["widget"]
            tipo = info["type"]
            label = info["label"]
            if tipo == "text":
                value = widget.get().strip() if hasattr(widget, "get") else ""
                if value:
                    action_plan.append({"text": f"{label}: {value}", "done": False})
            elif tipo == "textarea":
                value = widget.get("1.0", "end").strip() if hasattr(widget, "get") else ""
                if value:
                    action_plan.append({"text": f"{label}: {value}", "done": False})
            elif tipo == "checkbox":
                checked = bool(widget.get()) if hasattr(widget, "get") else False
                action_plan.append({"text": label, "done": checked})
            elif tipo == "date":
                value = widget.get().strip() if hasattr(widget, "get") else ""
                if value:
                    action_plan.append({"text": f"{label}: {value}", "done": False})
    dados = {
        "student_id": self.selected_student_id,
        "title": titulo,
        "theme": tema,
        "session_date": date.today().strftime("%Y-%m-%d"),
        "content": content,
        "is_markdown": is_markdown,
        "motivational_message": motivational_message,
        "action_plan": action_plan,
    }
    def save():
        if self.is_editing and self.editing_orientation_id:
            res = servico_orientacoes.atualizar_orientacao(self.editing_orientation_id, dados)
        else:
            res = servico_orientacoes.criar_orientacao(dados)
        self.after(0, lambda: self._on_save_result(res))
    threading.Thread(target=save, daemon=True).start()
def _on_save_result(self, res: dict[str, Any]):
    if res.get("success"):
        self._show_message("Orientação salva com sucesso!" if not self.is_editing
                            else "Orientação atualizada com sucesso!")
        self._reset_form()
        if self.current_tab == "history":
            self._load_history()
    else:
        self._show_message(f"Erro ao salvar: {res.get('message', 'Erro desconhecido')}")
# ── preencher formulário -------------------------------------------------
def _populate_form(self, orientation: dict[str, Any]):
    if self.entry_titulo:
        self.entry_titulo.delete(0, "end")
        self.entry_titulo.insert(0, orientation.get("title", ""))
    if self.entry_tema:
        self.entry_tema.delete(0, "end")
        self.entry_tema.insert(0, orientation.get("theme", ""))
    if self.text_mensagem:
        self.text_mensagem.delete(0, "end")
        self.text_mensagem.insert(0, orientation.get("motivational_message", ""))
    if self.text_conteudo:
        self.text_conteudo.delete(0, "end")
        self.text_conteudo.insert(0, orientation.get("content", ""))
    session_date = orientation.get("session_date", "")
    if session_date and hasattr(self, "entry_data"):
        try:
            d = datetime.fromisoformat(session_date.replace("Z", ""))
            self.entry_data.delete(0, "end")
            self.entry_data.insert(0, d.strftime("%d/%m/%Y"))
        except Exception:
            pass
    is_markdown = orientation.get("is_markdown", False)
    if self.check_markdown:
        if is_markdown:
            self.check_markdown.select()
        else:
            self.check_markdown.deselect()
    action_plan_data = orientation.get("action_plan", [])
    if action_plan_data:
        try:
            self.action_plan = json.loads(action_plan_data) if isinstance(action_plan_data, str) else action_plan_data
        except Exception:
            self.action_plan = []
    else:
        self.action_plan = []
    self.dynamic_components = []
    self._load_action_plan_as_components()
def _load_action_plan_as_components(self):
    self.dynamic_components = []
    for i, item in enumerate(self.action_plan):
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        self.dynamic_components.append({
            "id": f"task_{i}",
            "type": "checkbox",
            "label": text,
            "checked": item.get("done", False) if isinstance(item, dict) else False,
        })
    self._render_preview()
# ── reset ----------------------------------------------------------------
def _reset_form(self):
    for field in (self.entry_titulo, self.entry_tema):
        if field:
            field.delete(0, "end")
    for field in (self.text_mensagem, self.text_conteudo):
        if field:
            field.delete(0, "end")
    self.dynamic_components = []
    self.action_plan = []
    self.dynamic_widgets = {}
    self._render_preview()
    self.editing_orientation_id = None
    self.is_editing = False
    self.btn_salvar.configure(text="Salvar Orientação")
    nome = self.selected_student.get("name", "Aluno") if self.selected_student else "Aluno"
    self.subtitle_label.configure(text=f"Criando orientação para: {nome}")
# ── exportação -----------------------------------------------------------
def _export_json(self):
    data = {
        "student_id": self.selected_student_id,
        "components": self.dynamic_components,
        "exported_at": datetime.now().isoformat(),
    }
    filename = f"orientacao_{self.selected_student_id or 'template'}.json"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._show_message(f"Exportado para {filename}")
    except Exception as e:
        self._show_message(f"Erro ao exportar: {e}")
def _choose_files(self):
    files = filedialog.askopenfilenames(
        title="Selecionar Arquivos",
        filetypes=[
            ("Todos os arquivos", "*.*"),
            ("PDF", "*.pdf"),
            ("Imagens", "*.png *.jpg *.jpeg"),
            ("Documentos", "*.doc *.docx"),
        ],
    )
    if files:
        self.label_files.configure(text=f"{len(files)} arquivo(s) selecionado(s)")
        self._selected_files = files
# ── toast ----------------------------------------------------------------
def _show_message(self, message: str):
    toast = ctk.CTkFrame(self, fg_color=ORIENTACOES_COLORS["text"], corner_radius=8)
    toast.place(relx=0.5, rely=0.08, anchor="n")
    ctk.CTkLabel(toast, text=message, font=themed_font("body"),
                 text_color="white").pack(padx=20, pady=10)
    self.after(3000, toast.destroy)
import logging
import os
import shutil
import time
import tkinter.filedialog as fd
import mimetypes
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from PIL import Image as PILImage

import customtkinter as ctk

from ser_pleno.ui.components.ui_components import (
    Avatar,
    BaseModal,
    Chip,
    Divider,
    EmptyState,
    FormField,
    Toast,
    bind_clickable,
    clear_children,
)
from ser_pleno.ui.views.base import _ErrorModal
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.theme import RADIUS, SPACING, THEME, font, themed_font
from ser_pleno.ui.theme_extensions import extend_theme, spacing
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.avatar_utils import get_avatar_color
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger("apps.desktop")

O = extend_theme(
    THEME,
    {
        "card_radius": RADIUS["card"],
        "card_bg": THEME["surface"],
        "card_border": THEME["border"],
        "danger_hover": "#B91C1C",
        "text_light": THEME["text_muted"],
        "input_border": THEME["border"],
        "input_error": THEME["danger"],
        "input_error_soft": THEME["danger_soft"],
        "sidebar_bg": THEME["surface"],
        "sidebar_border": THEME["border"],
        "student_bg": THEME["bg_alt"],
        "student_hover": THEME["primary_soft"],
        "student_active": THEME["primary_soft"],
        "av_colors": [
            "#4F46E5",
            "#7C3AED",
            "#059669",
            "#D97706",
            "#DC2626",
            "#0891B2",
        ],
        "temas": {
            "Geral": ("#4F46E5", "#EEF2FF"),
            "Acadêmico": ("#2563EB", "#DBEAFE"),
            "Emocional": ("#DB2777", "#FCE7F3"),
            "Social": ("#0891B2", "#CCFBF1"),
            "Familiar": ("#EA580C", "#FFEDD5"),
            "Vocacional": ("#7C3AED", "#EDE9FE"),
        },
    },
)

_TEMA_DEFAULT = ("#4F46E5", "#EEF2FF")
_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def _get_attachment_icon_symbol(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in _IMAGE_EXTENSIONS:
        return "▣"
    if ext == ".pdf":
        return ICONS["pdf"]
    if ext in {".doc", ".docx", ".txt", ".rtf", ".odt"}:
        return ICONS["file_text"]
    if ext in {".xls", ".xlsx", ".csv", ".ods"}:
        return ICONS["spreadsheet"]
    if ext in {".zip", ".rar", ".7z", ".tar", ".gz"}:
        return ICONS["zip"]
    return ICONS["attach"]


class StudentCard(ctk.CTkFrame):
    def __init__(
        self, parent: Any, student: Dict[str, Any], on_select: Callable
    ):
        super().__init__(
            parent,
            fg_color=O["student_bg"],
            corner_radius=10,
            cursor="hand2",
        )
        self._student = student
        self._on_select = on_select
        self._selected = False
        self._build()

    def _build(self) -> None:
        nome = self._student.get("name", "N/A")
        course = self._student.get("course", "Sem curso")
        av_color = get_avatar_color(nome)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)

        av = Avatar(inner, initials=nome[:2], size=38, color=av_color)
        av.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(
            inner,
            text=nome,
            font=font(size=13, weight="bold"),
            text_color=O["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner,
            text=course,
            font=font(size=11),
            text_color=O["text_muted"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w")

        self.bind(
            "<Enter>",
            lambda e: (
                self.configure(fg_color=O["student_hover"])
                if not self._selected
                else None
            ),
        )
        self.bind(
            "<Leave>",
            lambda e: self.configure(
                fg_color=(
                    O["student_active"] if self._selected else O["student_bg"]
                )
            ),
        )
        bind_clickable(self, lambda: self._on_select(self._student, self))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.configure(
            fg_color=O["student_active"] if selected else O["student_bg"]
        )


class OrientationHistoryCard(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        orientation: Dict[str, Any],
        on_view: Callable,
        on_edit: Callable,
        on_duplicate: Callable,
        on_delete: Callable,
    ):
        super().__init__(
            parent,
            fg_color=O["card_bg"],
            corner_radius=O["card_radius"],
            border_width=1,
            border_color=O["card_border"],
        )
        self._o = orientation
        self._on_view = on_view
        self._on_edit = on_edit
        self._on_duplicate = on_duplicate
        self._on_delete = on_delete
        self._build()

    def _build(self) -> None:
        tema = self._o.get("theme", "Geral")
        color, soft = O["temas"].get(tema, _TEMA_DEFAULT)

        ctk.CTkFrame(self, width=4, corner_radius=0, fg_color=color).pack(
            side="left", fill="y"
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=spacing("md"), pady=spacing("md")
        )

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))

        date_str = self._o.get("session_date", "")
        day_txt = "?"
        if date_str:
            try:
                day_txt = str(
                    datetime.fromisoformat(date_str.replace("Z", "")).day
                )
            except Exception:
                pass

        day_bg = ctk.CTkFrame(
            top, width=46, height=46, corner_radius=12, fg_color=soft
        )
        day_bg.pack(side="left", padx=(0, 14))
        day_bg.pack_propagate(False)
        ctk.CTkLabel(
            day_bg,
            text=day_txt,
            font=font(size=17, weight="bold"),
            text_color=color,
        ).place(relx=0.5, rely=0.5, anchor="center")

        meta = ctk.CTkFrame(top, fg_color="transparent")
        meta.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            meta,
            text=self._o.get("title", "Orientação"),
            font=font(size=13, weight="bold"),
            text_color=O["text"],
            anchor="w",
        ).pack(anchor="w")

        color, soft = O["temas"].get(tema, _TEMA_DEFAULT)
        Chip(meta, text=tema, fg_color=soft, text_color=color, corner_radius=RADIUS["sm"]).pack(anchor="w", pady=(4, 0))

        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.pack(side="right", anchor="n")

        actions = [
            (
                f"{ICONS['view']}  Ver",
                lambda: self._on_view(self._o),
                O["accent_soft"],
                O["accent"],
            ),
            (
                f"{ICONS['edit']}  Editar",
                lambda: self._on_edit(self._o),
                O["accent"],
                THEME["text_on_primary"],
            ),
            (
                f"{ICONS['duplicate']}  Dup.",
                lambda: self._on_duplicate(self._o.get("id")),
                O["divider"],
                O["text_muted"],
            ),
            (
                f"{ICONS['delete']}  Excluir",
                lambda: self._on_delete(self._o.get("id")),
                O["danger_soft"],
                O["danger"],
            ),
        ]

        for label, cmd, accent, txt_color in actions:
            ctk.CTkButton(
                acts,
                text=label,
                command=cmd,
                height=28,
                width=90,
                corner_radius=8,
                fg_color=accent,
                hover_color=accent,
                text_color=txt_color,
                font=font(size=11, weight="bold"),
            ).pack(side="left", padx=(0, 4))

        content = self._o.get("content", "")
        if content:
            Divider(body)
            preview = (
                content[:220] + "..." if len(content) > 220 else content
            )
            ctk.CTkLabel(
                body,
                text=preview,
                font=font(size=12),
                text_color=O["text_muted"],
                wraplength=900,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(8, 0), fill="x")


class OrientacoesFrame(ctk.CTkFrame):
    def __init__(self, parent: Any, controller: Any):
        self._t0 = time.perf_counter()
        super().__init__(parent, fg_color=O["page_bg"])
        self.controller = controller
        self.servico_orientacoes = getattr(controller, "servico_orientacoes", None)
        self._selected_student: Optional[Dict[str, Any]] = None
        self._selected_card: Optional[StudentCard] = None
        self._orientacao_editando_id: Optional[int] = None
        self._anexos_selecionados: List[Dict[str, Any]] = []
        self._anexos_existentes_ids: List[int] = []
        self._todos_estudantes: List[Dict[str, Any]] = []
        self._todas_orientacoes: List[Dict[str, Any]] = []
        self._por_estudante: Dict[Any, List[Dict[str, Any]]] = {}
        self._action_plan_itens: List[Dict[str, Any]] = []
        self._toast: Optional[Toast] = None
        self._orientacoes_page_size = 20
        self._orientacoes_rendered_count = 0
        self._btn_mais: Optional[ctk.CTkButton] = None
        self._form_nova_built = False
        self._estatisticas_built = False
        self._filtros_built = False
        self._templates_cache = []
        self._themes_cache = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._criar_conteudo()
        self.after_idle(self._build_form_nova_lazy)
        self.after_idle(self._build_area_estatisticas_lazy)
        self.after_idle(self._build_area_filtros_lazy)
        self._carregar_dados()
        self._carregar_estudantes()
        log_view_init_ms("orientacoes", self._t0, widget_ref=self)

    def _criar_conteudo(self) -> None:
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("lg")
        )
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=5)
        wrap.grid_rowconfigure(0, weight=1)

        self._criar_sidebar_estudantes(wrap)
        self._criar_painel_principal(wrap)

    def _show_error(
        self, message: str, title: str = "Não foi possível concluir"
    ) -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _show_success(self, message: str, duration: int = 3000) -> None:
        try:
            if self._toast and self._toast.winfo_exists():
                self._toast.destroy()
            self._toast = Toast(
                self.winfo_toplevel(),
                message=message,
                status="success",
                duration=duration,
            )
        except Exception:
            pass

    def _criar_sidebar_estudantes(self, parent: Any) -> None:
        sidebar = ctk.CTkFrame(
            parent,
            fg_color=O["sidebar_bg"],
            corner_radius=O["card_radius"],
            border_width=1,
            border_color=O["sidebar_border"],
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(sidebar, fg_color="transparent")
        hdr.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=spacing("md"),
            pady=(spacing("md"), spacing("item_gap")),
        )
        ctk.CTkLabel(
            hdr,
            text="Estudantes",
            font=font(size=13, weight="bold"),
            text_color=O["text"],
        ).pack(side="left")

        search_wrap = ctk.CTkFrame(
            sidebar, fg_color=THEME["bg_alt"], corner_radius=10
        )
        search_wrap.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=spacing("sm"),
            pady=(0, spacing("item_gap")),
        )

        ctk.CTkLabel(
            search_wrap,
            text=ICONS["search"],
            font=font(size=13),
            text_color=O["text_light"],
        ).pack(side="left", padx=(10, 0))

        self._entry_busca = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Buscar estudante...",
            fg_color=THEME["bg_alt"],
            border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=font(size=13),
            height=36,
        )
        self._entry_busca.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self._entry_busca.bind("<KeyRelease>", self._filtrar_estudantes)

        ctk.CTkFrame(sidebar, height=1, fg_color=O["divider"]).grid(
            row=1, column=0, sticky="sew", padx=0, pady=(42, 0)
        )

        self._scroll_students = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self._scroll_students.grid(row=2, column=0, sticky="nsew")

        self._students_placeholder = ctk.CTkLabel(
            self._scroll_students,
            text="Carregando estudantes...",
            font=font(size=12),
            text_color=O["text_muted"],
        )
        self._students_placeholder.pack(pady=20)

    def _criar_painel_principal(self, parent: Any) -> None:
        self._painel = ctk.CTkFrame(parent, fg_color="transparent")
        self._painel.grid(row=0, column=1, sticky="nsew")
        self._painel.grid_rowconfigure(1, weight=1)
        self._painel.grid_columnconfigure(0, weight=1)

        self._tab_bar = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._tab_ativo = "historico"
        self._tab_btns: Dict[str, ctk.CTkButton] = {}

        tabs = [
            ("historico", f"{ICONS['chart']}  Histórico"),
            ("nova", f"{ICONS['add']}  Nova Orientação"),
            ("estatisticas", f"{ICONS['chart']}  Estatísticas"),
            ("filtros", f"{ICONS['search']}  Filtros"),
        ]

        for key, label in tabs:
            btn = ctk.CTkButton(
                self._tab_bar,
                text=label,
                command=lambda k=key: self._mudar_tab(k),
                height=36,
                width=170,
                corner_radius=10,
                font=font(size=12, weight="bold"),
                fg_color=(
                    O["accent"] if key == "historico" else O["accent_soft"]
                ),
                hover_color=O["accent_hover"],
                text_color=(
                    THEME["text_on_primary"]
                    if key == "historico"
                    else O["accent"]
                ),
            )
            btn.pack(side="left", padx=(0, 8))
            self._tab_btns[key] = btn

        self._area_historico = ctk.CTkScrollableFrame(
            self._painel,
            fg_color="transparent",
            scrollbar_button_color="#C7D2FE",
        )
        self._area_historico.grid(row=1, column=0, sticky="nsew")

        self._area_nova = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._area_nova.grid(row=1, column=0, sticky="nsew")
        self._area_nova.grid_remove()

        self._area_estatisticas = ctk.CTkFrame(
            self._painel, fg_color="transparent"
        )
        self._area_estatisticas.grid(row=1, column=0, sticky="nsew")
        self._area_estatisticas.grid_remove()

        self._area_filtros = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._area_filtros.grid(row=1, column=0, sticky="nsew")
        self._area_filtros.grid_remove()

        self._hist_placeholder = ctk.CTkLabel(
            self._area_historico,
            text="Selecione um estudante para ver as orientações",
            font=font(size=13),
            text_color=O["text_muted"],
        )
        self._hist_placeholder.pack(pady=40)

    def _mudar_tab(self, key: str) -> None:
        self._tab_ativo = key
        for k, btn in self._tab_btns.items():
            ativo = k == key
            btn.configure(
                fg_color=O["accent"] if ativo else O["accent_soft"],
                text_color=THEME["text_on_primary"] if ativo else O["accent"],
            )
        if self._area_nova is not None and self._area_nova.winfo_exists():
            self._area_nova.grid_remove()
        if self._area_historico is not None and self._area_historico.winfo_exists():
            self._area_historico.grid_remove()
        if self._area_estatisticas is not None and self._area_estatisticas.winfo_exists():
            self._area_estatisticas.grid_remove()
        if self._area_filtros is not None and self._area_filtros.winfo_exists():
            self._area_filtros.grid_remove()

        if key == "historico":
            if self._area_historico is not None and self._area_historico.winfo_exists():
                self._area_historico.grid()
        elif key == "nova":
            if not self._form_nova_built:
                self._build_form_nova_lazy()
            if self._area_nova is not None and self._area_nova.winfo_exists():
                self._area_nova.grid()
        elif key == "estatisticas":
            if not self._estatisticas_built:
                self._build_area_estatisticas_lazy()
            if self._area_estatisticas is not None and self._area_estatisticas.winfo_exists():
                self._area_estatisticas.grid()
            self._carregar_estatisticas()
        elif key == "filtros":
            if not self._filtros_built:
                self._build_area_filtros_lazy()
            if self._area_filtros is not None and self._area_filtros.winfo_exists():
                self._area_filtros.grid()

    def _construir_form_nova(self, parent: Any) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=O["card_bg"],
            corner_radius=O["card_radius"],
            border_width=1,
            border_color=O["card_border"],
        )
        card.pack(fill="both", expand=True)

        banner = ctk.CTkFrame(
            card, fg_color=O["accent_soft"], corner_radius=0, height=56
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=spacing("xl"))

        ib = ctk.CTkFrame(
            bi, width=34, height=34, corner_radius=9, fg_color=O["accent"]
        )
        ib.pack(side="left", padx=(0, spacing("md")))
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text=ICONS["chart"], font=font(size=15)).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(
            ts,
            text="Registrar Orientação",
            font=font(size=13, weight="bold"),
            text_color=O["accent"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            ts,
            text="Preencha os dados do atendimento",
            font=font(size=10),
            text_color=O["text_muted"],
        ).pack(anchor="w")

        body = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
        )
        body.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("md")
        )

        self._badge_estudante = ctk.CTkFrame(
            body,
            fg_color=O["input_bg"],
            corner_radius=10,
            border_width=1,
            border_color=O["input_border"],
        )
        self._badge_estudante.pack(fill="x", pady=(0, 10))
        self._badge_estudante_content = ctk.CTkFrame(
            self._badge_estudante, fg_color="transparent"
        )
        self._badge_estudante_content.pack(
            fill="x", padx=spacing("md"), pady=spacing("sm")
        )
        self._atualizar_badge_estudante()

        templates_row = ctk.CTkFrame(body, fg_color="transparent")
        templates_row.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            templates_row,
            text=f"{ICONS['file_text']}  Modelos Rápidos:",
            font=font(size=12),
            text_color=O["text_muted"],
            anchor="w",
        ).pack(side="left")
        ctk.CTkButton(
            templates_row,
            text="Selecionar Modelo",
            command=self._abrir_dialogo_templates,
            height=30,
            width=160,
            corner_radius=8,
            fg_color=O["accent_soft"],
            hover_color=O["accent"],
            text_color=O["accent"],
            font=font(size=11, weight="bold"),
        ).pack(side="right")

        self.f_titulo = FormField(
            body, f"{ICONS['chart']}Título", placeholder="Título da orientação"
        )
        self.f_titulo.pack(fill="x", pady=(0, 10))

        self.f_conteudo = FormField(
            body,
            f"{ICONS['file']}  Conteúdo",
            placeholder="Descreva a orientação...",
            multiline=True,
            height=100,
        )
        self.f_conteudo.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        row.grid_columnconfigure((0, 1), weight=1)

        self.f_tema = FormField(
            row,
            f"{ICONS['pin']}  Tema",
            values=["Geral"],
            initial="Geral",
        )
        self.f_tema.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self._carregar_themes()

        self.f_data = FormField(
            row,
            f"{ICONS['calendar']}  Data da Sessão",
            placeholder="YYYY-MM-DD",
            icon=ICONS["calendar"],
        )
        self.f_data.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.f_mensagem = FormField(
            body,
            f"{ICONS['heart']}  Mensagem Motivacional",
            placeholder="Mensagem de apoio ao estudante...",
        )
        self.f_mensagem.pack(fill="x", pady=(0, 10))

        self.f_encaminhamento = FormField(
            body,
            f"{ICONS['search']}  Encaminhamento",
            placeholder="Serviço ou profissional indicado",
        )
        self.f_encaminhamento.pack(fill="x", pady=(0, 10))

        self.f_obs = FormField(
            body,
            f"{ICONS['chat']}  Observações",
            multiline=True,
            height=70,
        )
        self.f_obs.pack(fill="x", pady=(0, 10))

        self._anexos_frame = ctk.CTkFrame(body, fg_color="transparent")
        self._anexos_frame.pack(fill="x", pady=(0, 10))

        anexos_header = ctk.CTkFrame(self._anexos_frame, fg_color="transparent")
        anexos_header.pack(fill="x")
        ctk.CTkLabel(
            anexos_header,
            text=f"{ICONS['attach']}  Anexos",
            font=font(size=12),
            text_color=O["text_muted"],
            anchor="w",
        ).pack(side="left")
        ctk.CTkButton(
            anexos_header,
            text="Anexar arquivo",
            command=self._adicionar_anexo,
            height=30,
            width=140,
            corner_radius=8,
            fg_color=O["accent_soft"],
            hover_color=O["accent"],
            text_color=O["accent"],
            font=font(size=11, weight="bold"),
        ).pack(side="right")

        self._anexos_lista = ctk.CTkScrollableFrame(
            self._anexos_frame,
            fg_color="transparent",
            height=100,
            scrollbar_button_color=THEME["border_strong"],
        )
        self._anexos_lista.pack(fill="x", pady=(4, 0))

        self._criar_secao_plano_acao(body)

        ctk.CTkFrame(card, height=1, fg_color=O["divider"]).pack(fill="x")
        footer = ctk.CTkFrame(card, fg_color="transparent", height=58)
        footer.pack(fill="x", padx=spacing("xl"))
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=self._limpar_e_voltar_historico,
            height=36,
            width=110,
            corner_radius=10,
            fg_color=O["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
            border_width=1,
            border_color=O["card_border"],
            font=font(size=12),
        ).pack(side="left", pady=spacing("md"))

        ctk.CTkButton(
            footer,
            text=f"{ICONS['check']}  Salvar Orientação",
            command=self._salvar_orientacao,
            height=36,
            width=180,
            corner_radius=10,
            fg_color=O["accent"],
            hover_color=O["accent_hover"],
            text_color="white",
            font=font(size=13, weight="bold"),
        ).pack(side="right", pady=spacing("md"))

    def _limpar_e_voltar_historico(self) -> None:
        self._orientacao_editando_id = None
        self._anexos_existentes_ids.clear()
        self._anexos_selecionados.clear()
        self._action_plan_itens.clear()
        self._mudar_tab("historico")

    def _criar_secao_plano_acao(self, parent: Any) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 10))

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            header,
            text=f"{ICONS['check_circle']}  Plano de Ação",
            font=font(size=12, weight="bold"),
            text_color=O["text"],
            anchor="w",
        ).pack(side="left")

        self._action_plan_frame = ctk.CTkScrollableFrame(
            frame,
            fg_color="transparent",
            height=120,
            scrollbar_button_color=THEME["border_strong"],
        )
        self._action_plan_frame.pack(fill="x", pady=(0, 4))

        self._action_plan_var = ctk.StringVar(value="")
        ap_entry_row = ctk.CTkFrame(frame, fg_color="transparent")
        ap_entry_row.pack(fill="x")
        self._ap_entry = ctk.CTkEntry(
            ap_entry_row,
            textvariable=self._action_plan_var,
            placeholder_text="Nova tarefa do plano de ação...",
            fg_color=O["input_bg"],
            border_width=1,
            border_color=O["input_border"],
            text_color=O["text"],
            font=font(size=12),
            height=34,
        )
        self._ap_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._ap_entry.bind(
            "<Return>", lambda e: self._adicionar_item_plano_acao()
        )

        ctk.CTkButton(
            ap_entry_row,
            text="Adicionar",
            command=self._adicionar_item_plano_acao,
            height=34,
            width=90,
            corner_radius=8,
            fg_color=O["accent_soft"],
            hover_color=O["accent"],
            text_color=O["accent"],
            font=font(size=11, weight="bold"),
        ).pack(side="right")

    def _adicionar_item_plano_acao(
        self, texto: str = "", done: bool = False
    ) -> None:
        txt = texto.strip() or self._action_plan_var.get().strip()
        if not txt:
            return
        self._action_plan_var.set("")
        self._action_plan_itens.append({"text": txt, "done": done})
        self._renderizar_plano_acao()

    def _remover_item_plano_acao(self, index: int) -> None:
        if 0 <= index < len(self._action_plan_itens):
            self._action_plan_itens.pop(index)
            self._renderizar_plano_acao()

    def _toggle_item_plano_acao(self, index: int) -> None:
        if 0 <= index < len(self._action_plan_itens):
            self._action_plan_itens[index]["done"] = not self._action_plan_itens[
                index
            ]["done"]
            self._renderizar_plano_acao()

    def _renderizar_plano_acao(self) -> None:
        clear_children(self._action_plan_frame)
        if not self._action_plan_itens:
            ctk.CTkLabel(
                self._action_plan_frame,
                text="Nenhuma tarefa adicionada",
                font=font(size=11),
                text_color=O["text_light"],
            ).pack(pady=8, anchor="w")
            return

        for i, item in enumerate(self._action_plan_itens):
            row = ctk.CTkFrame(
                self._action_plan_frame,
                fg_color=O["input_bg"],
                corner_radius=8,
                border_width=1,
                border_color=O["input_border"],
            )
            row.pack(fill="x", pady=2)

            cb = ctk.CTkCheckBox(
                row,
                text="",
                command=lambda idx=i: self._toggle_item_plano_acao(idx),
                fg_color=O["accent"],
                hover_color=O["accent_hover"],
                border_color=O["input_border"],
                width=24,
            )
            if item.get("done"):
                cb.select()
            cb.pack(side="left", padx=(8, 4), pady=4)

            text_c = O["text_muted"] if item.get("done") else O["text"]
            weight_c = "normal" if item.get("done") else "bold"
            ctk.CTkLabel(
                row,
                text=item.get("text", ""),
                font=font(size=12, weight=weight_c),
                text_color=text_c,
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=(4, 4), pady=4)

            ctk.CTkButton(
                row,
                text=ICONS["close"],
                width=24,
                height=24,
                corner_radius=6,
                fg_color="transparent",
                hover_color=O["danger_soft"],
                text_color=O["danger"],
                font=font(size=12),
                command=lambda idx=i: self._remover_item_plano_acao(idx),
            ).pack(side="right", padx=(0, 6))

    def _atualizar_badge_estudante(self) -> None:
        if self._badge_estudante_content is None or not self._badge_estudante_content.winfo_exists():
            return
        clear_children(self._badge_estudante_content)
        if not self._selected_student:
            ctk.CTkLabel(
                self._badge_estudante_content,
                text=f"{ICONS['users']}  Nenhum estudante selecionado",
                font=font(size=12),
                text_color=O["text_muted"],
            ).pack(anchor="w")
            return

        nome = self._selected_student.get("name", "N/A")
        course = self._selected_student.get("course", "")
        av_color = get_avatar_color(nome)

        row = ctk.CTkFrame(self._badge_estudante_content, fg_color="transparent")
        row.pack(fill="x")

        Avatar(row, initials=nome[:2], size=28, color=av_color).pack(
            side="left", padx=(0, 8)
        )

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            info,
            text=nome,
            font=font(size=12, weight="bold"),
            text_color=O["text"],
            anchor="w",
        ).pack(anchor="w")

        if course:
            ctk.CTkLabel(
                info,
                text=course,
                font=font(size=10),
                text_color=O["text_muted"],
                anchor="w",
            ).pack(anchor="w")

        ctk.CTkButton(
            row,
            text="Limpar",
            command=self._limpar_selecao_estudante,
            height=26,
            width=60,
            corner_radius=8,
            fg_color="transparent",
            hover_color=O["danger_soft"],
            text_color=O["danger"],
            font=font(size=10, weight="bold"),
        ).pack(side="right")

    def _limpar_selecao_estudante(self) -> None:
        if self._selected_card:
            self._selected_card.set_selected(False)
        self._selected_card = None
        self._selected_student = None
        self._atualizar_badge_estudante()
        self._mostrar_orientacoes(self._todas_orientacoes)

    def _construir_area_estatisticas(self, parent: Any) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=O["card_bg"],
            corner_radius=O["card_radius"],
            border_width=1,
            border_color=O["card_border"],
        )
        card.pack(fill="both", expand=True)

        banner = ctk.CTkFrame(
            card, fg_color=O["accent_soft"], corner_radius=0, height=56
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=spacing("xl"))
        ctk.CTkLabel(
            bi,
            text=f"{ICONS['chart']}  Estatísticas de Orientações",
            font=font(size=13, weight="bold"),
            text_color=O["accent"],
        ).pack(side="left")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("md")
        )

        self._stats_total_frame = ctk.CTkFrame(
            body, fg_color=O["accent_soft"], corner_radius=12
        )
        self._stats_total_frame.pack(fill="x", pady=(0, 12))
        self._stats_total_label = ctk.CTkLabel(
            self._stats_total_frame,
            text="Carregando estatísticas...",
            font=font(size=18, weight="bold"),
            text_color=O["accent"],
        )
        self._stats_total_label.pack(
            padx=spacing("xl"), pady=spacing("md")
        )

        row_charts = ctk.CTkFrame(body, fg_color="transparent")
        row_charts.pack(fill="both", expand=True)
        row_charts.grid_columnconfigure((0, 1), weight=1)

        tema_frame = ctk.CTkFrame(
            row_charts,
            fg_color=O["input_bg"],
            corner_radius=12,
            border_width=1,
            border_color=O["input_border"],
        )
        tema_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ctk.CTkLabel(
            tema_frame,
            text="Por Tema",
            font=font(size=12, weight="bold"),
            text_color=O["text"],
        ).pack(anchor="w", padx=spacing("md"), pady=(spacing("md"), 4))
        self._stats_tema_canvas = ctk.CTkCanvas(
            tema_frame, height=200, bg=O["card_bg"], highlightthickness=0
        )
        self._stats_tema_canvas.pack(
            fill="both", expand=True, padx=spacing("md"), pady=(0, spacing("md"))
        )

        mes_frame = ctk.CTkFrame(
            row_charts,
            fg_color=O["input_bg"],
            corner_radius=12,
            border_width=1,
            border_color=O["input_border"],
        )
        mes_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ctk.CTkLabel(
            mes_frame,
            text="Por Mês (últimos 12)",
            font=font(size=12, weight="bold"),
            text_color=O["text"],
        ).pack(anchor="w", padx=spacing("md"), pady=(spacing("md"), 4))
        self._stats_mes_canvas = ctk.CTkCanvas(
            mes_frame, height=200, bg=O["card_bg"], highlightthickness=0
        )
        self._stats_mes_canvas.pack(
            fill="both", expand=True, padx=spacing("md"), pady=(0, spacing("md"))
        )

    def _carregar_estatisticas(self) -> None:
        if not getattr(self, "_estatisticas_built", False):
            self._build_area_estatisticas_lazy()
        if self._stats_total_label is None or not self._stats_total_label.winfo_exists():
            return
        aluno_id = (
            self._selected_student.get("id") if self._selected_student else None
        )

        def fetch() -> Dict[str, Any]:
            return self.servico_orientacoes.obter_estatisticas(aluno_id)

        def on_success(resultado: Dict[str, Any]) -> None:
            if not self.winfo_exists():
                return
            data = resultado.get("data") if isinstance(resultado, dict) else {}
            self._stats_total_label.configure(
                text=f"Total de Orientações: {data.get('total', 0)}"
            )
            self._desenhar_grafico_tema(data.get("by_theme", []))
            self._desenhar_grafico_mes(data.get("by_month", []))

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao carregar estatísticas: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _desenhar_grafico_tema(self, dados: List[Dict[str, Any]]) -> None:
        canvas = self._stats_tema_canvas
        canvas.delete("all")
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw < 80 or ch < 80:
            canvas.after(100, lambda: self._desenhar_grafico_tema(dados))
            return

        font_family = THEME.get("font_family", "Segoe UI")
        if not dados:
            canvas.create_text(
                cw // 2,
                ch // 2,
                text="Sem dados",
                font=(font_family, 11),
                fill=O["text_light"],
            )
            return

        top = sorted(dados, key=lambda x: x.get("count", 0), reverse=True)[:6]
        max_count = max((x.get("count", 0) for x in top), default=1)
        margin_x, margin_y = 80, 16
        bar_h = max(10, (ch - 2 * margin_y) // len(top) - 8)
        chart_w = cw - margin_x - 20

        for i, item in enumerate(top):
            count = item.get("count", 0)
            theme = item.get("theme", "?")
            color = O["temas"].get(theme, _TEMA_DEFAULT)[0]
            bar_w = max(4, (count / max_count) * chart_w)
            y = margin_y + i * (bar_h + 8)

            canvas.create_text(
                margin_x - 8,
                y + bar_h // 2,
                text=theme[:10],
                font=(font_family, 9),
                fill=O["text_muted"],
                anchor="e",
            )
            canvas.create_rectangle(
                margin_x,
                y,
                margin_x + bar_w,
                y + bar_h,
                fill=color,
                outline="",
            )
            canvas.create_text(
                margin_x + bar_w + 6,
                y + bar_h // 2,
                text=str(count),
                font=(font_family, 9, "bold"),
                fill=O["text"],
                anchor="w",
            )

    def _desenhar_grafico_mes(self, dados: List[Dict[str, Any]]) -> None:
        canvas = self._stats_mes_canvas
        canvas.delete("all")
        cw, ch = canvas.winfo_width(), canvas.winfo_height()
        if cw < 80 or ch < 80:
            canvas.after(100, lambda: self._desenhar_grafico_mes(dados))
            return

        font_family = THEME.get("font_family", "Segoe UI")
        if not dados:
            canvas.create_text(
                cw // 2,
                ch // 2,
                text="Sem dados",
                font=(font_family, 11),
                fill=O["text_light"],
            )
            return

        dados_rev = list(reversed(dados))[:12]
        max_count = max((x.get("count", 0) for x in dados_rev), default=1)
        margin_x, margin_y = 50, 20
        chart_w, chart_h = cw - margin_x - 10, ch - 2 * margin_y
        bar_w = max(4, chart_w // max(len(dados_rev), 1) - 6)

        for i, item in enumerate(dados_rev):
            count = item.get("count", 0)
            month = item.get("month", "?")[5:]
            bar_h = max(4, (count / max_count) * chart_h)
            x = margin_x + i * (bar_w + 6)
            y = ch - margin_y - bar_h

            canvas.create_rectangle(
                x,
                y,
                x + bar_w,
                ch - margin_y,
                fill=O["accent"],
                outline="",
                stipple="gray50",
            )
            canvas.create_rectangle(
                x, y, x + bar_w, ch - margin_y, fill=O["accent"], outline=""
            )
            canvas.create_text(
                x + bar_w // 2,
                ch - margin_y + 10,
                text=month,
                font=(font_family, 8),
                fill=O["text_muted"],
                anchor="n",
            )
            canvas.create_text(
                x + bar_w // 2,
                y - 6,
                text=str(count),
                font=(font_family, 8, "bold"),
                fill=O["text"],
                anchor="s",
            )

    def _construir_area_filtros(self, parent: Any) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=O["card_bg"],
            corner_radius=O["card_radius"],
            border_width=1,
            border_color=O["card_border"],
        )
        card.pack(fill="both", expand=True)

        banner = ctk.CTkFrame(
            card, fg_color=O["accent_soft"], corner_radius=0, height=56
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)
        ctk.CTkLabel(
            banner,
            text=f"{ICONS['search']}  Filtros de Histórico",
            font=font(size=13, weight="bold"),
            text_color=O["accent"],
        ).pack(side="left", padx=spacing("xl"))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("md")
        )

        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        row1.grid_columnconfigure((0, 1, 2), weight=1)

        self._f_tema_filtro = FormField(
            row1,
            f"{ICONS['pin']}  Tema",
            values=[
                "Todos",
                "Geral",
                "Acadêmico",
                "Emocional",
                "Social",
                "Familiar",
                "Vocacional",
            ],
            initial="Todos",
        )
        self._f_tema_filtro.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self._f_data_inicio = FormField(
            row1,
            f"{ICONS['calendar']}  Data Início",
            placeholder="YYYY-MM-DD",
            icon=ICONS["calendar"],
        )
        self._f_data_inicio.grid(row=0, column=1, sticky="ew", padx=6)

        self._f_data_fim = FormField(
            row1,
            f"{ICONS['calendar']}  Data Fim",
            placeholder="YYYY-MM-DD",
            icon=ICONS["calendar"],
        )
        self._f_data_fim.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))
        row2.grid_columnconfigure(0, weight=1)

        self._f_busca_historico = FormField(
            row2,
            f"{ICONS['search']}  Buscar (título, tema, conteúdo)",
            placeholder="Digite para buscar...",
        )
        self._f_busca_historico.grid(row=0, column=0, sticky="ew")

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(
            btn_row,
            text="Aplicar Filtros",
            command=self._aplicar_filtros,
            height=36,
            width=160,
            corner_radius=10,
            fg_color=O["accent"],
            hover_color=O["accent_hover"],
            text_color="white",
            font=font(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Limpar Filtros",
            command=self._limpar_filtros,
            height=36,
            width=140,
            corner_radius=10,
            fg_color=O["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
            border_width=1,
            border_color=O["card_border"],
            font=font(size=12),
        ).pack(side="left")

        self._filtros_info = ctk.CTkLabel(
            body, text="", font=font(size=11), text_color=O["text_light"]
        )
        self._filtros_info.pack(anchor="w")

    def _aplicar_filtros(self) -> None:
        if not self._filtros_built:
            self._build_area_filtros_lazy()
        if self._f_tema_filtro is None or not self._f_tema_filtro.winfo_exists():
            return
        tema = self._f_tema_filtro.get()
        data_inicio = self._f_data_inicio.get().strip()
        data_fim = self._f_data_fim.get().strip()
        busca = self._f_busca_historico.get().strip()
        aluno_id = (
            self._selected_student.get("id") if self._selected_student else None
        )

        def fetch() -> Dict[str, Any]:
            return self.servico_orientacoes.listar_orientacoes(
                id_estudante=aluno_id,
                tema=tema if tema and tema != "Todos" else None,
                date_from=data_inicio or None,
                date_to=data_fim or None,
                search=busca or None,
            )

        def on_success(resultado: Dict[str, Any]) -> None:
            if not self.winfo_exists():
                return
            self._renderizar(resultado)
            ors = (resultado.get("data") or {}).get("orientations") or []
            self._filtros_info.configure(
                text=f"{len(ors)} orientação(ões) encontrada(s)"
            )

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao filtrar orientações: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _limpar_filtros(self) -> None:
        if not self._filtros_built:
            self._build_area_filtros_lazy()
        if self._f_tema_filtro is not None and self._f_tema_filtro.winfo_exists():
            self._f_tema_filtro.widget.set("Todos")
        if self._f_data_inicio is not None and self._f_data_inicio.winfo_exists():
            self._f_data_inicio.delete(0, "end")
        if self._f_data_fim is not None and self._f_data_fim.winfo_exists():
            self._f_data_fim.delete(0, "end")
        if self._f_busca_historico is not None and self._f_busca_historico.winfo_exists():
            self._f_busca_historico.delete(0, "end")
        if self._filtros_info is not None and self._filtros_info.winfo_exists():
            self._filtros_info.configure(text="")
        self._carregar_dados()

    def _carregar_dados(self) -> None:
        self._show_skeleton()

        def fetch() -> Dict[str, Any]:
            return self.servico_orientacoes.listar_orientacoes()

        def on_success(resultado: Dict[str, Any]) -> None:
            self._hide_skeleton()
            self._renderizar(resultado)

        def on_error(exc: Exception) -> None:
            self._hide_skeleton()
            logger.error("Erro ao carregar orientações: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _show_skeleton(self) -> None:
        clear_children(self._area_historico)
        for _ in range(8):
            s = ctk.CTkFrame(
                self._area_historico,
                fg_color=O["card_bg"],
                corner_radius=O["card_radius"],
                height=90,
            )
            s.pack(fill="x", pady=(0, 10), padx=4)
            s.pack_propagate(False)
            ctk.CTkFrame(
                s, width=4, corner_radius=0, fg_color=THEME["border"]
            ).pack(side="left", fill="y")
            ctk.CTkFrame(s, fg_color="transparent").pack(
                side="left",
                fill="both",
                expand=True,
                padx=spacing("md"),
                pady=spacing("md"),
            )

    def _hide_skeleton(self) -> None:
        clear_children(self._area_historico)

    def _carregar_estudantes(self) -> None:
        def fetch() -> Dict[str, Any]:
            return self.servico_orientacoes.listar_estudantes()

        def on_success(resultado: Dict[str, Any]) -> None:
            if resultado.get("success"):
                estudantes = resultado.get("data", [])
                self._todos_estudantes = estudantes
                self._popular_sidebar(estudantes)

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao carregar estudantes: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _renderizar(self, resultado: Dict[str, Any]) -> None:
        clear_children(self._area_historico)

        orientacoes = []
        if resultado.get("success"):
            orientacoes = (resultado.get("data") or {}).get("orientations") or []

        estudantes_vistos = set()
        estudantes = []
        por_estudante: Dict[Any, List[Dict[str, Any]]] = {}

        for o in orientacoes:
            sid = (
                o.get("student_id")
                or o.get("student", {}).get("id")
                or o.get("student_name")
            )
            if sid not in estudantes_vistos:
                estudantes_vistos.add(sid)
                estudantes.append(
                    {
                        "id": sid,
                        "name": o.get("student_name")
                        or o.get("student", {}).get("name", "Estudante"),
                        "course": o.get("student_course", ""),
                    }
                )
            por_estudante.setdefault(sid, []).append(o)

        self._todos_estudantes = estudantes
        self._todas_orientacoes = orientacoes
        self._por_estudante = por_estudante

        if not orientacoes:
            EmptyState(
                self._area_historico,
                icon=ICONS["chart"],
                title="Nenhuma orientação registrada",
                subtitle="Crie uma nova orientação para começar",
                action_text=" + Nova Orientação",
                action_command=lambda: self._mudar_tab("nova"),
            ).pack(pady=30)
        else:
            self._mostrar_orientacoes(orientacoes)

    def _popular_sidebar(self, estudantes: List[Dict[str, Any]]) -> None:
        clear_children(self._scroll_students)

        if not estudantes:
            EmptyState(
                self._scroll_students,
                icon=ICONS["mood_bad"],
                title="Nenhum estudante",
                subtitle="",
            ).pack(pady=20)
            return

        todos_row = ctk.CTkFrame(
            self._scroll_students,
            fg_color=O["accent_soft"],
            corner_radius=10,
            cursor="hand2",
        )
        todos_row.pack(fill="x", pady=(0, spacing("xs")), padx=spacing("xs"))
        ctk.CTkLabel(
            todos_row,
            text=f"{ICONS['group']}  Todos os estudantes",
            font=font(size=12, weight="bold"),
            text_color=O["accent"],
        ).pack(padx=spacing("md"), pady=spacing("sm"))
        bind_clickable(
            todos_row, lambda: self._mostrar_orientacoes(self._todas_orientacoes)
        )

        batch = WidgetBatchBuilder(parent=self._scroll_students, batch_size=20)
        for st in estudantes:
            batch.add(lambda st=st: self._criar_student_card(st))
        batch.execute()

    def _criar_student_card(self, student: Dict[str, Any]) -> StudentCard:
        card = StudentCard(
            self._scroll_students,
            student,
            on_select=self._selecionar_estudante,
        )
        card.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))
        return card

    def _filtrar_estudantes(self, _=None) -> None:
        termo = (
            self._entry_busca.get().lower()
            if hasattr(self, "_entry_busca")
            else ""
        )
        filtrados = [
            s
            for s in getattr(self, "_todos_estudantes", [])
            if termo in s.get("name", "").lower()
        ]
        self._popular_sidebar(filtrados)

    def _selecionar_estudante(
        self, student: Dict[str, Any], card_widget: StudentCard
    ) -> None:
        if self._selected_card:
            self._selected_card.set_selected(False)
        self._selected_card = card_widget
        card_widget.set_selected(True)
        self._selected_student = student
        self._atualizar_badge_estudante()

        self._mostrar_orientacoes(
            self._por_estudante.get(student.get("id"), [])
        )

    def _mostrar_orientacoes(self, orientacoes: List[Dict[str, Any]]) -> None:
        clear_children(self._area_historico)

        if not orientacoes:
            ctk.CTkLabel(
                self._area_historico,
                text=f"{ICONS['chart']}  Nenhuma orientação para este estudante",
                font=font(size=13),
                text_color=O["text_muted"],
            ).pack(pady=30)
            return

        self._orientacoes_lista_completa = list(orientacoes)
        self._orientacoes_rendered_count = 0

        if self._btn_mais:
            self._btn_mais.destroy()
            self._btn_mais = None

        self._carregar_mais_orientacoes()

    def _carregar_mais_orientacoes(self) -> None:
        if not hasattr(self, "_orientacoes_lista_completa"):
            return

        start = self._orientacoes_rendered_count
        end = min(
            start + self._orientacoes_page_size,
            len(self._orientacoes_lista_completa),
        )
        page = self._orientacoes_lista_completa[start:end]

        if not page and start == 0:
            return

        batch = WidgetBatchBuilder(parent=self._area_historico, batch_size=8)
        for o in page:
            batch.add(
                lambda o=o: OrientationHistoryCard(
                    self._area_historico,
                    orientation=o,
                    on_view=self._ver_orientacao,
                    on_edit=self._editar_orientacao,
                    on_duplicate=self._duplicar_orientacao,
                    on_delete=self._excluir_orientacao,
                ).pack(fill="both", expand=True, pady=(0, 10))
            )
        batch.execute()

        self._orientacoes_rendered_count = end
        faltam = len(self._orientacoes_lista_completa) - end

        if faltam > 0 and self.winfo_exists():
            self._btn_mais = ctk.CTkButton(
                self._area_historico,
                text=f"Carregar mais ({faltam})",
                command=self._carregar_mais_orientacoes,
                height=36,
                width=220,
                corner_radius=10,
                fg_color=O["accent_soft"],
                hover_color=O["accent"],
                text_color=O["accent"],
                font=font(size=12, weight="bold"),
            )
            self._btn_mais.pack(pady=12)

    def _salvar_orientacao(self) -> None:
        if not self._form_nova_built:
            self._build_form_nova_lazy()
        if self.f_titulo is None or not self.f_titulo.winfo_exists():
            return
        titulo = self.f_titulo.get().strip()
        if not titulo:
            self.f_titulo.set_error("Título é obrigatório")
            return

        dados = {
            "title": titulo,
            "content": self.f_conteudo.get().strip() if self.f_conteudo is not None and self.f_conteudo.winfo_exists() else "",
            "theme": self.f_tema.get() if self.f_tema is not None and self.f_tema.winfo_exists() else "Geral",
            "session_date": self.f_data.get().strip() if self.f_data is not None and self.f_data.winfo_exists() else "",
            "referral": self.f_encaminhamento.get().strip() if self.f_encaminhamento is not None and self.f_encaminhamento.winfo_exists() else "",
            "notes": self.f_obs.get().strip() if self.f_obs is not None and self.f_obs.winfo_exists() else "",
            "motivational_message": self.f_mensagem.get().strip() if self.f_mensagem is not None and self.f_mensagem.winfo_exists() else "",
            "student_id": (
                self._selected_student.get("id")
                if self._selected_student
                else None
            ),
            "action_plan": [
                {
                    "text": item.get("text", ""),
                    "done": bool(item.get("done", False)),
                }
                for item in self._action_plan_itens
            ],
        }

        def save():
            if self._orientacao_editando_id is not None:
                res = self.servico_orientacoes.atualizar_orientacao(
                    self._orientacao_editando_id, dados
                )
                return res, self._orientacao_editando_id
            res = self.servico_orientacoes.criar_orientacao(dados)
            oid = (
                res.get("data", {}).get("id") if isinstance(res, dict) else None
            )
            return res, oid

        def on_ok(result_oid):
            resultado, oid = result_oid
            if resultado.get("success") and oid:
                novos = [
                    a
                    for a in self._anexos_selecionados
                    if a.get("caminho") and not a.get("_existente") and os.path.exists(a["caminho"])
                ]
                if novos:
                    self._upload_anexos(oid, novos)
            self._limpar_e_voltar_historico()
            self._carregar_dados()

        AsyncRunner.run(
            task=save,
            on_success=on_ok,
            on_error=lambda e: self._show_error(str(e)),
            widget_ref=self,
        )

    def _adicionar_anexo(self) -> None:
        caminhos = fd.askopenfilenames(
            title="Selecionar arquivos",
            filetypes=[
                ("Todos os arquivos", "*.*"),
                ("Imagens", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Documentos", "*.pdf *.doc *.docx *.txt *.rtf *.odt"),
                ("Planilhas", "*.xls *.xlsx *.csv *.ods"),
                ("Compactados", "*.zip *.rar *.7z *.tar *.gz"),
            ],
        )
        if not caminhos:
            return

        for caminho in caminhos:
            tamanho = os.path.getsize(caminho)
            if tamanho > 10 * 1024 * 1024:
                self._show_error(
                    f"Arquivo muito grande (>10MB): {os.path.basename(caminho)}"
                )
                continue
            mime_type, _ = mimetypes.guess_type(caminho)
            self._anexos_selecionados.append(
                {
                    "caminho": caminho,
                    "nome": os.path.basename(caminho),
                    "tamanho": tamanho,
                    "mime_type": mime_type or "application/octet-stream",
                }
            )
        self._renderizar_anexos_selecionados()

    def _remover_anexo_selecionado(self, index: int) -> None:
        if 0 <= index < len(self._anexos_selecionados):
            self._anexos_selecionados.pop(index)
            self._renderizar_anexos_selecionados()

    def _renderizar_anexos_selecionados(self) -> None:
        if self._anexos_lista is None or not self._anexos_lista.winfo_exists():
            return
        clear_children(self._anexos_lista)
        if not self._anexos_selecionados:
            ctk.CTkLabel(
                self._anexos_lista,
                text="Nenhum anexo selecionado",
                font=font(size=11),
                text_color=O["text_light"],
            ).pack(pady=8)
            return

        for i, anexo in enumerate(self._anexos_selecionados):
            row = ctk.CTkFrame(
                self._anexos_lista,
                fg_color=O["input_bg"],
                corner_radius=8,
                border_width=1,
                border_color=O["input_border"],
            )
            row.pack(fill="x", pady=2)

            icon_lbl = ctk.CTkLabel(
                row,
                text=_get_attachment_icon_symbol(anexo["nome"]),
                font=font(size=16),
                width=34,
            )
            icon_lbl.pack(side="left", padx=(8, 4), pady=6)

            caminho = anexo.get("caminho")
            ext = os.path.splitext(anexo["nome"])[1].lower()
            if caminho and os.path.exists(caminho) and ext in _IMAGE_EXTENSIONS:
                try:
                    pil_img = PILImage.open(caminho)
                    pil_img.thumbnail((28, 28))
                    ctk_img = ctk.CTkImage(light_image=pil_img, size=(28, 28))
                    icon_lbl.configure(image=ctk_img, text="")
                    icon_lbl._img_ref = ctk_img
                except Exception:
                    pass

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=4, pady=4)
            ctk.CTkLabel(
                info,
                text=anexo["nome"],
                font=font(size=11, weight="bold"),
                text_color=O["text"],
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                info,
                text=f"{self._formatar_tamanho(anexo['tamanho'])}  •  {anexo.get('mime_type', 'application/octet-stream')}",
                font=font(size=10),
                text_color=O["text_light"],
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkButton(
                row,
                text=ICONS["close"],
                width=28,
                height=28,
                corner_radius=8,
                fg_color="transparent",
                hover_color=O["danger_soft"],
                text_color=O["danger"],
                font=font(size=14),
                command=lambda idx=i: self._remover_anexo_selecionado(idx),
            ).pack(side="right", padx=(0, 6))

    def _upload_anexos(
        self, orientation_id: int, anexos: List[Dict[str, Any]]
    ) -> None:
        app = self.winfo_toplevel()
        usuario_id = (
            getattr(self.master.master, "usuario_logado_id", None)
            or getattr(app, "usuario_logado_id", None)
            or 1
        )

        def upload_task():
            return [
                self.servico_orientacoes.adicionar_anexo(
                    orientation_id, a["caminho"], usuario_id
                )
                for a in anexos
            ]

        def on_done(_):
            if self.winfo_exists():
                self._anexos_selecionados.clear()
                self._renderizar_anexos_selecionados()

        AsyncRunner.run(
            task=upload_task,
            on_success=on_done,
            on_error=lambda e: logger.warning("Erro no upload de anexos: %s", e),
            widget_ref=self,
        )

    def _formatar_tamanho(self, tamanho_bytes: int) -> str:
        if not tamanho_bytes:
            return "0 B"
        unidades = ["B", "KB", "MB", "GB"]
        i = 0
        tamanho = float(tamanho_bytes)
        while tamanho >= 1024 and i < len(unidades) - 1:
            tamanho /= 1024
            i += 1
        return f"{tamanho:.1f} {unidades[i]}"

    def _abrir_dialogo_templates(self) -> None:
        if not self._form_nova_built:
            self._build_form_nova_lazy()
        if self.f_titulo is None or not self.f_titulo.winfo_exists():
            return

        modal = BaseModal(self, "Selecionar Modelo", 420, 320)
        ctk.CTkLabel(
            modal,
            text=f"{ICONS['file_text']}  Modelos de Orientação",
            font=font(size=13, weight="bold"),
            text_color=O["text"],
        ).pack(anchor="w", padx=spacing("xl"), pady=(spacing("xl"), 8))

        scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("sm")
        )

        loading_lbl = ctk.CTkLabel(
            scroll,
            text="Carregando modelos...",
            font=font(size=12),
            text_color=O["text_muted"],
        )
        loading_lbl.pack(pady=20)

        student_id = (
            self._selected_student.get("id") if self._selected_student else None
        )

        def aplicar_template(template_id: str):
            res = self.servico_orientacoes.usar_template(template_id, student_id)
            if res and res.get("success"):
                data = res.get("data", {})
                if self.f_titulo is not None and self.f_titulo.winfo_exists():
                    self.f_titulo.delete(0, "end")
                    self.f_titulo.insert(0, data.get("title", ""))
                if self.f_conteudo is not None and self.f_conteudo.winfo_exists():
                    self.f_conteudo.delete("1.0", "end")
                    self.f_conteudo.insert("1.0", data.get("content", ""))
                if self.f_tema is not None and self.f_tema.winfo_exists():
                    self.f_tema.widget.set(data.get("theme", "Geral"))
                if self.f_data is not None and self.f_data.winfo_exists():
                    self.f_data.delete(0, "end")
                    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
                    self.f_data.insert(0, hoje)
            modal.destroy()

        def renderizar_templates(templates):
            clear_children(scroll)
            if not templates:
                ctk.CTkLabel(
                    scroll,
                    text="Nenhum modelo disponível",
                    font=font(size=12),
                    text_color=O["text_muted"],
                ).pack(pady=20)
                return
            for t in templates:
                tid = t.get("id") if isinstance(t, dict) else t
                label = t.get("label", tid) if isinstance(t, dict) else str(t)
                ctk.CTkButton(
                    scroll,
                    text=f"{ICONS['file_text']}  {label}",
                    command=lambda x=tid: aplicar_template(x),
                    height=40,
                    corner_radius=10,
                    anchor="w",
                    fg_color=O["accent_soft"],
                    hover_color=O["accent"],
                    text_color=O["accent"],
                    font=font(size=12, weight="bold"),
                ).pack(fill="x", pady=3)

        def fetch():
            return self.servico_orientacoes.listar_templates()

        def on_success(resultado):
            if not modal.winfo_exists():
                return
            data = resultado.get("data", []) if isinstance(resultado, dict) else []
            self._templates_cache = data
            renderizar_templates(data)

        def on_error(exc):
            logger.error("Erro ao carregar templates: %s", exc)
            if modal.winfo_exists():
                clear_children(scroll)
                ctk.CTkLabel(
                    scroll,
                    text="Erro ao carregar modelos",
                    font=font(size=12),
                    text_color=O["danger"],
                ).pack(pady=20)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=modal,
        )

        ctk.CTkButton(
            modal,
            text="Cancelar",
            command=modal.destroy,
            height=36,
            width=120,
            corner_radius=10,
            fg_color=O["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
            border_width=1,
            border_color=O["card_border"],
            font=font(size=12),
        ).pack(pady=spacing("md"))

    def _carregar_themes(self) -> None:
        def fetch():
            return self.servico_orientacoes.listar_themes()

        def on_success(resultado):
            if not self.winfo_exists():
                return
            data = resultado.get("data", []) if isinstance(resultado, dict) else []
            self._themes_cache = data
            if not data or self.f_tema is None or not self.f_tema.winfo_exists():
                return
            values = []
            for t in data:
                v = t.get("value") if isinstance(t, dict) else str(t)
                values.append(v)
            if not values:
                values = ["Geral"]
            self.f_tema.widget.configure(values=values)
            current = self.f_tema.get()
            if current not in values:
                self.f_tema.widget.set(values[0])

        def on_error(exc):
            logger.error("Erro ao carregar themes: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _carregar_anexos_edicao(self, orientation_id: int) -> None:
        def fetch():
            return self.servico_orientacoes.listar_anexos(orientation_id)

        def on_success(resultado):
            if not self.winfo_exists():
                return
            anexos = resultado.get("data", []) if isinstance(resultado, dict) else []
            for anexo in anexos:
                caminho_arquivo = anexo.get("file", "")
                tamanho = 0
                if caminho_arquivo and os.path.exists(caminho_arquivo):
                    tamanho = os.path.getsize(caminho_arquivo)
                mime_type = anexo.get("mime_type") or "application/octet-stream"
                self._anexos_selecionados.append(
                    {
                        "file_id": anexo.get("id"),
                        "nome": anexo.get("file_name", "arquivo"),
                        "tamanho": tamanho,
                        "mime_type": mime_type,
                        "_existente": True,
                        "caminho": caminho_arquivo,
                    }
                )
                self._anexos_existentes_ids.append(anexo.get("id"))
            self._renderizar_anexos_selecionados()

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=lambda e: logger.error(
                "Erro ao carregar anexos para edição: %s", e
            ),
            widget_ref=self,
        )

    def _ver_orientacao(self, o: Dict[str, Any]) -> None:
        self._modal_detalhe(o)

    def _editar_orientacao(self, o: Dict[str, Any]) -> None:
        if not self._form_nova_built:
            self._build_form_nova_lazy()
        self._orientacao_editando_id = o.get("id")
        self._anexos_existentes_ids.clear()
        self._anexos_selecionados.clear()
        self._action_plan_itens.clear()

        if self.f_titulo is not None and self.f_titulo.winfo_exists():
            self.f_titulo.delete(0, "end")
            self.f_titulo.insert(0, o.get("title", ""))
        if self.f_conteudo is not None and self.f_conteudo.winfo_exists():
            self.f_conteudo.delete("1.0", "end")
            self.f_conteudo.insert("1.0", o.get("content", ""))
        if self.f_tema is not None and self.f_tema.winfo_exists():
            self.f_tema.widget.set(o.get("theme", "Geral"))
        if self.f_data is not None and self.f_data.winfo_exists():
            self.f_data.delete(0, "end")
            self.f_data.insert(0, (o.get("session_date") or "")[:10])
        if self.f_encaminhamento is not None and self.f_encaminhamento.winfo_exists():
            self.f_encaminhamento.delete(0, "end")
            self.f_encaminhamento.insert(0, o.get("referral", "") or "")
        if self.f_obs is not None and self.f_obs.winfo_exists():
            self.f_obs.delete("1.0", "end")
            self.f_obs.insert("1.0", o.get("notes", "") or "")
        if self.f_mensagem is not None and self.f_mensagem.winfo_exists():
            self.f_mensagem.delete(0, "end")
            self.f_mensagem.insert(0, o.get("motivational_message", "") or "")

        ap = o.get("action_plan", [])
        if isinstance(ap, list):
            self._action_plan_itens = [
                {"text": t.get("text", ""), "done": bool(t.get("done", False))}
                for t in ap
                if isinstance(t, dict) and t.get("text")
            ]
        self._renderizar_plano_acao()

        if self._orientacao_editando_id:
            self._carregar_anexos_edicao(self._orientacao_editando_id)

        self._mudar_tab("nova")

    def _duplicar_orientacao(self, oid: int) -> None:
        if not self._confirmar("Duplicar esta orientação?"):
            return

        def fetch():
            return self.servico_orientacoes.duplicar_orientacao(oid)

        def on_success(resultado):
            if not self.winfo_exists():
                return
            if resultado.get("success"):
                self._carregar_dados()
            self._show_success(
                resultado.get("message", "Orientação duplicada"), duration=4000
            )

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=lambda e: self._show_error(str(e)),
            widget_ref=self,
        )

    def _excluir_orientacao(self, oid: int) -> None:
        if not self._confirmar("Excluir esta orientação?"):
            return

        def delete():
            return self.servico_orientacoes.deletar_orientacao(oid)

        AsyncRunner.run(
            task=delete,
            on_success=lambda _: self._carregar_dados(),
            on_error=lambda e: self._show_error(str(e)),
            widget_ref=self,
        )

    def _modal_detalhe(self, o: Dict[str, Any]) -> None:
        modal = ctk.CTkToplevel(self)
        modal.title("Orientação")
        modal.configure(fg_color=O["card_bg"])
        modal.resizable(False, False)

        w, h = 600, 680
        modal.update_idletasks()
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        tema = o.get("theme", "Geral")
        color, soft = O["temas"].get(tema, _TEMA_DEFAULT)

        banner = ctk.CTkFrame(modal, fg_color=soft, corner_radius=0, height=70)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=spacing("xl"))

        ib = ctk.CTkFrame(
            bi, width=42, height=42, corner_radius=12, fg_color=color
        )
        ib.pack(side="left", padx=(0, 12))
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text=ICONS["chart"], font=font(size=18)).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(
            ts,
            text=o.get("title", "Orientação"),
            font=font(size=14, weight="bold"),
            text_color=O["text"],
        ).pack(anchor="w")

        chip = ctk.CTkFrame(ts, fg_color=color, corner_radius=6)
        chip.pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(
            chip,
            text=tema,
            font=font(size=10, weight="bold"),
            text_color=THEME["text_on_primary"],
        ).pack(padx=spacing("sm"), pady=spacing("xs"))

        student = o.get("student", {})
        student_name = student.get("name", "") if isinstance(student, dict) else ""
        if student_name:
            ctk.CTkLabel(
                ts,
                text=f"{ICONS['users']}  {student_name}",
                font=font(size=10),
                text_color=O["text_muted"],
            ).pack(anchor="w", pady=(2, 0))

        body = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("md")
        )

        detalhes_list = [
            (f"{ICONS['calendar']}  Data", (o.get("session_date") or "—")[:10]),
            (f"{ICONS['pin']}  Tema", tema),
            (f"{ICONS['search']}  Encaminhamento", o.get("referral") or "—"),
        ]

        for label, value in detalhes_list:
            row = ctk.CTkFrame(body, fg_color=THEME["bg_alt"], corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row,
                text=label,
                width=170,
                font=font(size=12),
                text_color=O["text_muted"],
                anchor="w",
            ).pack(side="left", padx=spacing("md"), pady=spacing("md"))
            ctk.CTkLabel(
                row,
                text=value,
                font=font(size=12, weight="bold"),
                text_color=O["text"],
            ).pack(side="left")

        msg = o.get("motivational_message", "")
        if msg:
            ctk.CTkFrame(body, height=1, fg_color=O["divider"]).pack(
                fill="x", pady=(10, 8)
            )
            ctk.CTkLabel(
                body,
                text=f"{ICONS['heart']}  Mensagem Motivacional",
                font=font(size=12, weight="bold"),
                text_color=O["accent"],
            ).pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(
                body,
                text=msg,
                font=font(size=12),
                text_color=O["text"],
                wraplength=460,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(0, 8))

        ctk.CTkFrame(body, height=1, fg_color=O["divider"]).pack(
            fill="x", pady=(10, 8)
        )
        ctk.CTkLabel(
            body,
            text=o.get("content", ""),
            font=font(size=12),
            text_color=O["text_muted"],
            wraplength=460,
            justify="left",
            anchor="w",
        ).pack(anchor="w")

        ap = o.get("action_plan", [])
        if isinstance(ap, list) and ap:
            ctk.CTkFrame(body, height=1, fg_color=O["divider"]).pack(
                fill="x", pady=(10, 8)
            )
            ctk.CTkLabel(
                body,
                text=f"{ICONS['check_circle']}  Plano de Ação",
                font=font(size=12, weight="bold"),
                text_color=O["text"],
            ).pack(anchor="w", pady=(0, 6))

            for t in ap:
                item_text = t.get("text", "") if isinstance(t, dict) else str(t)
                if item_text:
                    prefix = (
                        f"{ICONS['check_circle']} "
                        if (isinstance(t, dict) and t.get("done"))
                        else f"{ICONS['circle']} "
                    )
                    ctk.CTkLabel(
                        body,
                        text=f"{prefix}{item_text}",
                        font=font(size=12),
                        text_color=O["text_muted"],
                        wraplength=460,
                        anchor="w",
                    ).pack(anchor="w", pady=2)

        orientation_id = o.get("id")
        if orientation_id:
            ctk.CTkFrame(body, height=1, fg_color=O["divider"]).pack(
                fill="x", pady=(10, 8)
            )
            ctk.CTkLabel(
                body,
                text=f"{ICONS['attach']}  Anexos",
                font=font(size=12, weight="bold"),
                text_color=O["text"],
            ).pack(anchor="w", pady=(0, 6))
            self._carregar_anexos_detalhe(body, orientation_id)

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text=f"{ICONS['edit']}  Editar",
            command=lambda: (modal.destroy(), self._editar_orientacao(o)),
            height=38,
            corner_radius=10,
            width=120,
            fg_color=O["accent_soft"],
            hover_color=O["accent"],
            text_color=O["accent"],
            font=font(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Fechar",
            command=modal.destroy,
            height=38,
            corner_radius=10,
            width=120,
            fg_color=O["accent"],
            hover_color=O["accent_hover"],
            text_color="white",
            font=font(size=13, weight="bold"),
        ).pack(side="right")

    def _carregar_anexos_detalhe(self, parent: Any, orientation_id: int) -> None:
        def fetch():
            return self.servico_orientacoes.listar_anexos(orientation_id)

        def on_success(resultado):
            if not parent.winfo_exists():
                return
            for w in parent.winfo_children():
                if getattr(w, "_is_anexo_section", False):
                    w.destroy()

            section = ctk.CTkFrame(parent, fg_color="transparent")
            section._is_anexo_section = True
            section.pack(fill="x", pady=(0, 4))

            anexos = (
                resultado.get("data", []) if isinstance(resultado, dict) else []
            )
            if not anexos:
                ctk.CTkLabel(
                    section,
                    text="Nenhum anexo",
                    font=font(size=11),
                    text_color=O["text_light"],
                ).pack(pady=4)
                return

            for anexo in anexos:
                row = ctk.CTkFrame(
                    section,
                    fg_color=O["input_bg"],
                    corner_radius=8,
                    border_width=1,
                    border_color=O["input_border"],
                )
                row.pack(fill="x", pady=2)

                nome_anexo = anexo.get("file_name", "")
                icon_lbl = ctk.CTkLabel(
                    row,
                    text=_get_attachment_icon_symbol(nome_anexo),
                    font=font(size=16),
                    width=34,
                )
                icon_lbl.pack(side="left", padx=(8, 4), pady=6)

                caminho = anexo.get("file")
                ext = os.path.splitext(nome_anexo)[1].lower()
                if (
                    caminho
                    and os.path.exists(caminho)
                    and ext in _IMAGE_EXTENSIONS
                ):
                    try:
                        pil_img = PILImage.open(caminho)
                        pil_img.thumbnail((28, 28))
                        ctk_img = ctk.CTkImage(light_image=pil_img, size=(28, 28))
                        icon_lbl.configure(image=ctk_img, text="")
                        icon_lbl._img_ref = ctk_img
                    except Exception:
                        pass

                info = ctk.CTkFrame(row, fg_color="transparent")
                info.pack(side="left", fill="x", expand=True, padx=4, pady=4)
                ctk.CTkLabel(
                    info,
                    text=nome_anexo,
                    font=font(size=11, weight="bold"),
                    text_color=O["text"],
                    anchor="w",
                ).pack(anchor="w")

                created = anexo.get("created_at", "")
                created_str = (
                    str(created)[:19].replace("T", " ") if created else ""
                )
                ctk.CTkLabel(
                    info,
                    text=created_str,
                    font=font(size=10),
                    text_color=O["text_light"],
                    anchor="w",
                ).pack(anchor="w")

                acts = ctk.CTkFrame(row, fg_color="transparent")
                acts.pack(side="right", padx=(0, 4))

                ctk.CTkButton(
                    acts,
                    text=ICONS["download"],
                    width=28,
                    height=28,
                    corner_radius=8,
                    fg_color="transparent",
                    hover_color=O["accent_soft"],
                    text_color=O["accent"],
                    font=font(size=14),
                    command=lambda a=anexo: self._baixar_anexo(a),
                ).pack(side="left", padx=(0, 2))

                ctk.CTkButton(
                    acts,
                    text=ICONS["delete"],
                    width=28,
                    height=28,
                    corner_radius=8,
                    fg_color="transparent",
                    hover_color=O["danger_soft"],
                    text_color=O["danger"],
                    font=font(size=14),
                    command=lambda aid=anexo.get("id"): self._excluir_anexo(
                        aid, orientation_id
                    ),
                ).pack(side="left")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=lambda e: logger.error("Erro ao carregar anexos: %s", e),
            widget_ref=parent,
        )

    def _baixar_anexo(self, anexo: Dict[str, Any]) -> None:
        caminho = anexo.get("file")
        nome = anexo.get("file_name", "arquivo")

        if caminho and isinstance(caminho, str) and caminho.startswith(("http://", "https://")):
            destino = fd.asksaveasfilename(
                title="Salvar anexo",
                initialfile=nome,
                filetypes=[("Todos os arquivos", "*.*")],
            )
            if not destino:
                return

            def download_task():
                session = self.servico_orientacoes._get_session()
                headers = self.servico_orientacoes._get_headers()
                response = session.get(caminho, headers=headers, timeout=15)
                if response.ok:
                    with open(destino, "wb") as f:
                        f.write(response.content)
                    return True
                raise RuntimeError(f"Erro HTTP {response.status_code}")

            def on_ok(_):
                if self.winfo_exists():
                    self._show_success(
                        f"Arquivo salvo em:\n{destino}", duration=4000
                    )

            AsyncRunner.run(
                task=download_task,
                on_success=on_ok,
                on_error=lambda e: self._show_error(f"Falha ao baixar: {e}"),
                widget_ref=self,
            )
            return

        if not caminho or not os.path.exists(caminho):
            self._show_error(
                "Arquivo não encontrado localmente.", title="Informação"
            )
            return

        destino = fd.asksaveasfilename(
            title="Salvar anexo",
            initialfile=nome,
            filetypes=[("Todos os arquivos", "*.*")],
        )
        if destino:
            try:
                shutil.copy2(caminho, destino)
                self._show_success(
                    f"Arquivo salvo em:\n{destino}", duration=4000
                )
            except Exception as e:
                self._show_error(f"Falha ao salvar: {e}")

    def _excluir_anexo(self, attachment_id: int, orientation_id: int) -> None:
        if not self._confirmar("Excluir este anexo?"):
            return

        def delete():
            return self.servico_orientacoes.deletar_anexo(attachment_id)

        def on_ok(_):
            if attachment_id in self._anexos_existentes_ids:
                self._anexos_existentes_ids.remove(attachment_id)
            self._anexos_selecionados = [
                a
                for a in self._anexos_selecionados
                if a.get("file_id") != attachment_id
            ]
            self._renderizar_anexos_selecionados()
            self._carregar_dados()

        AsyncRunner.run(
            task=delete,
            on_success=on_ok,
            on_error=lambda e: self._show_error(str(e)),
            widget_ref=self,
        )

    def _build_form_nova_lazy(self) -> None:
        if self._form_nova_built:
            return
        self._form_nova_built = True
        if self._area_nova is not None and self._area_nova.winfo_exists():
            self._construir_form_nova(self._area_nova)

    def _build_area_estatisticas_lazy(self) -> None:
        if self._estatisticas_built:
            return
        self._estatisticas_built = True
        if self._area_estatisticas is not None and self._area_estatisticas.winfo_exists():
            self._construir_area_estatisticas(self._area_estatisticas)

    def _build_area_filtros_lazy(self) -> None:
        if self._filtros_built:
            return
        self._filtros_built = True
        if self._area_filtros is not None and self._area_filtros.winfo_exists():
            self._construir_area_filtros(self._area_filtros)

    def _confirmar(self, mensagem: str) -> bool:
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 420, 200
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        resultado = {"ok": False}

        ctk.CTkLabel(
            modal,
            text=mensagem,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
            wraplength=360,
            justify="center",
        ).pack(pady=(24, 16))

        botoes = ctk.CTkFrame(modal, fg_color="transparent")
        botoes.pack(pady=(0, 20))

        def _fechar(confirmado: bool):
            resultado["ok"] = confirmado
            modal.destroy()

        ctk.CTkButton(
            botoes,
            text="Cancelar",
            width=110,
            height=36,
            fg_color=THEME["bg_alt"],
            hover_color=THEME["border"],
            text_color=THEME["text"],
            command=lambda: _fechar(False),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            botoes,
            text="Confirmar",
            width=110,
            height=36,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_on_primary"],
            command=lambda: _fechar(True),
        ).pack(side="right")

        modal.wait_window(modal)
        return resultado.get("ok", False)
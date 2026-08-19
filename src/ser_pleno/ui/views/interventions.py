import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import customtkinter as ctk

from ser_pleno.features.interventions.service import ServicoIntervencoes
from ser_pleno.ui.components.ui_components import (
    Avatar,
    Card,
    DangerButton,
    Divider,
    EmptyState,
    FormField,
    GhostButton,
    PrimaryButton,
    bind_clickable,
    clear_children,
)
from ser_pleno.ui.views.base import _ErrorModal
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.theme import (
    RADIUS,
    SPACING,
    THEME,
    font,
    themed_font,
)
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.avatar_utils import get_avatar_color
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger("apps.desktop")

I = {
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
    "accent": THEME["primary"],
    "accent_soft": THEME["primary_soft"],
    "accent_hover": THEME["primary_hover"],
    "divider": THEME["divider"],
    "danger": THEME["danger"],
    "danger_soft": THEME["danger_soft"],
    "success": THEME["success"],
    "success_soft": THEME["success_soft"],
    "warning": THEME["warning"],
    "text": THEME["text"],
    "text_muted": THEME["text_muted"],
    "text_secondary": THEME["text_secondary"],
    "page_bg": THEME["bg"],
    "input_bg": THEME["input_bg"],
}

_TIPOS_INTERVENCAO = {
    "counseling": ("Aconselhamento", THEME["primary"]),
    "academic_support": ("Apoio Academico", "#2563EB"),
    "emotional_support": ("Apoio Emocional", "#DB2777"),
    "crisis_intervention": ("Intervencao em Crise", THEME["danger"]),
    "family_meeting": ("Reuniao com Familia", "#D97706"),
    "referral": ("Encaminhamento", "#0891B2"),
    "follow_up": ("Acompanhamento", "#7C3AED"),
    "group_session": ("Sessao em Grupo", "#059669"),
    "phone_call": ("Ligacao Telefonica", THEME["text_muted"]),
    "other": ("Outro", THEME["text_muted"]),
}


class StudentCardIntervention(ctk.CTkFrame):
    def __init__(self, parent: Any, student: Dict[str, Any], on_select: Any):
        super().__init__(
            parent,
            fg_color=I["student_bg"],
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
            text_color=I["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner,
            text=course,
            font=font(size=11),
            text_color=I["text_muted"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w")

        self.bind(
            "<Enter>",
            lambda e: (
                self.configure(fg_color=I["student_hover"])
                if not self._selected
                else None
            ),
        )
        self.bind(
            "<Leave>",
            lambda e: self.configure(
                fg_color=I["student_active"] if self._selected else I["student_bg"]
            ),
        )
        bind_clickable(self, lambda: self._on_select(self._student, self))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.configure(
            fg_color=I["student_active"] if selected else I["student_bg"]
        )


class InterventionCard(ctk.CTkFrame):
    def __init__(
        self,
        parent: Any,
        intervention: Dict[str, Any],
        on_view: Any,
        on_delete: Any,
    ):
        super().__init__(
            parent,
            fg_color=I["card_bg"],
            corner_radius=I["card_radius"],
            border_width=1,
            border_color=I["card_border"],
        )
        self._iv = intervention
        self._on_view = on_view
        self._on_delete = on_delete
        self._build()

    def _build(self) -> None:
        itype = self._iv.get("intervention_type", "other")
        tipo_label, tipo_color = _TIPOS_INTERVENCAO.get(itype, ("Outro", I["text_muted"]))

        ctk.CTkFrame(self, width=4, corner_radius=0, fg_color=tipo_color).pack(
            side="left", fill="y"
        )

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=spacing("md"), pady=spacing("md")
        )

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))

        date_str = self._iv.get("date", "")
        day_txt = "?"
        if date_str:
            try:
                day_txt = str(datetime.fromisoformat(date_str).day)
            except Exception:
                pass

        day_bg = ctk.CTkFrame(
            top, width=46, height=46, corner_radius=12, fg_color=THEME["bg_alt"]
        )
        day_bg.pack(side="left", padx=(0, 14))
        day_bg.pack_propagate(False)
        ctk.CTkLabel(
            day_bg,
            text=day_txt,
            font=font(size=17, weight="bold"),
            text_color=tipo_color,
        ).place(relx=0.5, rely=0.5, anchor="center")

        meta = ctk.CTkFrame(top, fg_color="transparent")
        meta.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            meta,
            text=tipo_label,
            font=font(size=13, weight="bold"),
            text_color=I["text"],
            anchor="w",
        ).pack(anchor="w")

        chip_bg = THEME["bg_alt"]
        ctk.CTkFrame(
            meta, fg_color=chip_bg, corner_radius=RADIUS["sm"], height=24
        ).pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(
            meta,
            text=f"{ICONS['users']}  {self._iv.get('student_name', 'Estudante')}",
            font=font(size=10),
            text_color=I["text_muted"],
            anchor="w",
        ).pack(anchor="w")

        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.pack(side="right", anchor="n")

        ctk.CTkButton(
            acts,
            text=f"{ICONS['view']}  Ver",
            command=lambda: self._on_view(self._iv),
            height=28,
            width=80,
            corner_radius=8,
            fg_color=I["accent_soft"],
            hover_color=I["accent"],
            text_color=I["accent"],
            font=font(size=11, weight="bold"),
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            acts,
            text=f"{ICONS['delete']}  Excluir",
            command=lambda: self._on_delete(self._iv.get("id")),
            height=28,
            width=80,
            corner_radius=8,
            fg_color=I["danger_soft"],
            hover_color=I["danger"],
            text_color=I["danger"],
            font=font(size=11, weight="bold"),
        ).pack(side="left")

        notes = self._iv.get("notes", "")
        if notes:
            Divider(body)
            preview = notes[:220] + "..." if len(notes) > 220 else notes
            ctk.CTkLabel(
                body,
                text=preview,
                font=font(size=12),
                text_color=I["text_muted"],
                wraplength=900,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(8, 0), fill="x")


class IntervencoesFrame(ctk.CTkFrame):
    def __init__(self, parent: Any, controller: Any):
        self._t0 = time.perf_counter()
        super().__init__(parent, fg_color=I["page_bg"])
        self.controller = controller
        self.servico_intervencoes = getattr(controller, "servico_intervencoes", None)
        self._selected_student: Optional[Dict[str, Any]] = None
        self._selected_card: Optional[StudentCardIntervention] = None
        self._todas_intervencoes: List[Dict[str, Any]] = []
        self._todos_estudantes: List[Dict[str, Any]] = []
        self._form_built = False
        self._filtros_built = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._criar_conteudo()
        self.after_idle(self._build_form_lazy)
        self.after_idle(self._build_filtros_lazy)
        self._carregar_estudantes()
        self._carregar_intervencoes()
        log_view_init_ms("intervencoes", self._t0, widget_ref=self)

    def _criar_conteudo(self) -> None:
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("lg")
        )
        wrap.grid_columnconfigure(0, weight=3)
        wrap.grid_columnconfigure(1, weight=7)
        wrap.grid_rowconfigure(0, weight=1)

        self._criar_sidebar_estudantes(wrap)
        self._criar_painel_principal(wrap)

    def _show_error(
        self, message: str, title: str = "Nao foi possivel concluir"
    ) -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _show_success(self, message: str, duration: int = 3000) -> None:
        try:
            Toast = __import__("ser_pleno.ui.components.ui_components", fromlist=["Toast"]).Toast
            toast = Toast(
                self.winfo_toplevel(),
                message=message,
                status="success",
                duration=duration,
            )
        except Exception:
            pass

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

        ctk.CTkButton(
            botoes,
            text="Cancelar",
            width=110,
            height=36,
            fg_color=THEME["bg_alt"],
            hover_color=THEME["border"],
            text_color=THEME["text"],
            command=lambda: modal.destroy(),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            botoes,
            text="Confirmar",
            width=110,
            height=36,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_on_primary"],
            command=lambda: self._confirmar_callback(modal, resultado),
        ).pack(side="right")

        modal.wait_window(modal)
        return resultado.get("ok", False)

    def _confirmar_callback(self, modal: ctk.CTkToplevel, resultado: dict) -> None:
        resultado["ok"] = True
        modal.destroy()

    def _criar_sidebar_estudantes(self, parent: Any) -> None:
        sidebar = ctk.CTkFrame(
            parent,
            fg_color=I["sidebar_bg"],
            corner_radius=I["card_radius"],
            border_width=1,
            border_color=I["sidebar_border"],
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
            text_color=I["text"],
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
            text_color=I["text_light"],
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
            text_color=I["text_muted"],
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
            ("historico", f"{ICONS['chart']}  Historico"),
            ("nova", f"{ICONS['add']}  Nova Intervencao"),
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
                fg_color=I["accent"] if key == "historico" else I["accent_soft"],
                hover_color=I["accent_hover"],
                text_color=(
                    THEME["text_on_primary"] if key == "historico" else I["accent"]
                ),
            )
            btn.pack(side="left", padx=(0, 8))
            self._tab_btns[key] = btn

        self._area_historico = ctk.CTkScrollableFrame(
            self._painel,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self._area_historico.grid(row=1, column=0, sticky="nsew")

        self._area_nova = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._area_nova.grid(row=1, column=0, sticky="nsew")
        self._area_nova.grid_remove()

        self._area_filtros = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._area_filtros.grid(row=1, column=0, sticky="nsew")
        self._area_filtros.grid_remove()

        self._hist_placeholder = ctk.CTkLabel(
            self._area_historico,
            text="Selecione um estudante para ver as intervencoes",
            font=font(size=13),
            text_color=I["text_muted"],
        )
        self._hist_placeholder.pack(pady=40)

    def _mudar_tab(self, key: str) -> None:
        self._tab_ativo = key
        for k, btn in self._tab_btns.items():
            ativo = k == key
            btn.configure(
                fg_color=I["accent"] if ativo else I["accent_soft"],
                text_color=THEME["text_on_primary"] if ativo else I["accent"],
            )
        if self._area_nova is not None and self._area_nova.winfo_exists():
            self._area_nova.grid_remove()
        if self._area_historico is not None and self._area_historico.winfo_exists():
            self._area_historico.grid_remove()
        if self._area_filtros is not None and self._area_filtros.winfo_exists():
            self._area_filtros.grid_remove()

        if key == "historico":
            if self._area_historico is not None and self._area_historico.winfo_exists():
                self._area_historico.grid()
        elif key == "nova":
            if not self._form_built:
                self._build_form_lazy()
            if self._area_nova is not None and self._area_nova.winfo_exists():
                self._area_nova.grid()
        elif key == "filtros":
            if not self._filtros_built:
                self._build_filtros_lazy()
            if self._area_filtros is not None and self._area_filtros.winfo_exists():
                self._area_filtros.grid()

    def _build_form_lazy(self) -> None:
        if self._form_built:
            return
        self._form_built = True
        if self._area_nova is not None and self._area_nova.winfo_exists():
            self._construir_form_nova(self._area_nova)

    def _build_filtros_lazy(self) -> None:
        if self._filtros_built:
            return
        self._filtros_built = True
        if self._area_filtros is not None and self._area_filtros.winfo_exists():
            self._construir_area_filtros(self._area_filtros)

    def _construir_form_nova(self, parent: Any) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=I["card_bg"],
            corner_radius=I["card_radius"],
            border_width=1,
            border_color=I["card_border"],
        )
        card.pack(fill="both", expand=True)

        banner = ctk.CTkFrame(
            card, fg_color=I["accent_soft"], corner_radius=0, height=56
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=spacing("xl"))

        ib = ctk.CTkFrame(
            bi, width=34, height=34, corner_radius=9, fg_color=I["accent"]
        )
        ib.pack(side="left", padx=(0, spacing("md")))
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text=ICONS["heart"], font=font(size=15)).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(
            ts,
            text="Registrar Intervencao",
            font=font(size=13, weight="bold"),
            text_color=I["accent"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            ts,
            text="Preencha os dados da intervencao",
            font=font(size=10),
            text_color=I["text_muted"],
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
            fg_color=I["input_bg"],
            corner_radius=10,
            border_width=1,
            border_color=I["input_border"],
        )
        self._badge_estudante.pack(fill="x", pady=(0, 10))
        self._badge_estudante_content = ctk.CTkFrame(
            self._badge_estudante, fg_color="transparent"
        )
        self._badge_estudante_content.pack(
            fill="x", padx=spacing("md"), pady=spacing("sm")
        )
        self._atualizar_badge_estudante()

        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        row1.grid_columnconfigure((0, 1), weight=1)

        self.f_tipo = FormField(
            row1,
            f"{ICONS['pin']}  Tipo",
            values=[v for _, v in ServicoIntervencoes.get_tipos_intervencao()],
            initial="Aconselhamento",
        )
        self.f_tipo.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.f_data = FormField(
            row1,
            f"{ICONS['calendar']}  Data",
            placeholder="YYYY-MM-DD",
            icon=ICONS["calendar"],
        )
        self.f_data.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.f_data.insert(0, datetime.now().strftime("%Y-%m-%d"))

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))
        row2.grid_columnconfigure((0, 1), weight=1)

        self.f_duracao = FormField(
            row2,
            f"{ICONS['clock']}  Duracao (min)",
            placeholder="Ex: 45",
        )
        self.f_duracao.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.f_resultado = FormField(
            row2,
            f"{ICONS['check']}  Resultado",
            values=[v for _, v in ServicoIntervencoes.get_resultados_intervencao()],
            initial="Pendente",
        )
        self.f_resultado.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.f_notas = FormField(
            body,
            f"{ICONS['file']}  Anotacoes",
            placeholder="Descreva a intervencao...",
            multiline=True,
            height=100,
        )
        self.f_notas.pack(fill="x", pady=(0, 10))

        self.f_obs_resultado = FormField(
            body,
            f"{ICONS['chat']}  Observacoes do Resultado",
            placeholder="Notas adicionais sobre o resultado...",
            multiline=True,
            height=70,
        )
        self.f_obs_resultado.pack(fill="x", pady=(0, 10))

        ctk.CTkFrame(card, height=1, fg_color=I["divider"]).pack(fill="x")
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
            fg_color=I["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
            border_width=1,
            border_color=I["card_border"],
            font=font(size=12),
        ).pack(side="left", pady=spacing("md"))

        ctk.CTkButton(
            footer,
            text=f"{ICONS['check']}  Salvar Intervencao",
            command=self._salvar_intervencao,
            height=36,
            width=180,
            corner_radius=10,
            fg_color=I["accent"],
            hover_color=I["accent_hover"],
            text_color="white",
            font=font(size=13, weight="bold"),
        ).pack(side="right", pady=spacing("md"))

    def _limpar_e_voltar_historico(self) -> None:
        self._mudar_tab("historico")

    def _atualizar_badge_estudante(self) -> None:
        if self._badge_estudante_content is None or not self._badge_estudante_content.winfo_exists():
            return
        clear_children(self._badge_estudante_content)
        if not self._selected_student:
            ctk.CTkLabel(
                self._badge_estudante_content,
                text=f"{ICONS['users']}  Nenhum estudante selecionado",
                font=font(size=12),
                text_color=I["text_muted"],
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
            text_color=I["text"],
            anchor="w",
        ).pack(anchor="w")

        if course:
            ctk.CTkLabel(
                info,
                text=course,
                font=font(size=10),
                text_color=I["text_muted"],
                anchor="w",
            ).pack(anchor="w")

    def _construir_area_filtros(self, parent: Any) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=I["card_bg"],
            corner_radius=I["card_radius"],
            border_width=1,
            border_color=I["card_border"],
        )
        card.pack(fill="both", expand=True)

        banner = ctk.CTkFrame(
            card, fg_color=I["accent_soft"], corner_radius=0, height=56
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)
        ctk.CTkLabel(
            banner,
            text=f"{ICONS['search']}  Filtros de Intervencoes",
            font=font(size=13, weight="bold"),
            text_color=I["accent"],
        ).pack(side="left", padx=spacing("xl"))

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("md")
        )

        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        row1.grid_columnconfigure((0, 1, 2), weight=1)

        tipos = [v for _, v in ServicoIntervencoes.get_tipos_intervencao()]
        self._f_tipo = FormField(
            row1,
            f"{ICONS['pin']}  Tipo",
            values=["Todos"] + tipos,
            initial="Todos",
        )
        self._f_tipo.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self._f_data_inicio = FormField(
            row1,
            f"{ICONS['calendar']}  Data Inicio",
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

        self._f_busca = FormField(
            row2,
            f"{ICONS['search']}  Buscar (tipo, anotacoes)",
            placeholder="Digite para buscar...",
        )
        self._f_busca.grid(row=0, column=0, sticky="ew")

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(
            btn_row,
            text="Aplicar Filtros",
            command=self._aplicar_filtros,
            height=36,
            width=160,
            corner_radius=10,
            fg_color=I["accent"],
            hover_color=I["accent_hover"],
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
            fg_color=I["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
            border_width=1,
            border_color=I["card_border"],
            font=font(size=12),
        ).pack(side="left")

        self._filtros_info = ctk.CTkLabel(
            body, text="", font=font(size=11), text_color=I["text_light"]
        )
        self._filtros_info.pack(anchor="w")

    def _aplicar_filtros(self) -> None:
        if not self._filtros_built:
            self._build_filtros_lazy()
        if self._f_tipo is None or not self._f_tipo.winfo_exists():
            return
        tipo = self._f_tipo.get()
        data_inicio = self._f_data_inicio.get().strip()
        data_fim = self._f_data_fim.get().strip()
        busca = self._f_busca.get().strip()
        aluno_id = (
            self._selected_student.get("id") if self._selected_student else None
        )

        def fetch() -> Dict[str, Any]:
            return self.servico_intervencoes.listar_intervencoes(
                student_id=aluno_id,
                date_from=data_inicio or None,
                date_to=data_fim or None,
                intervention_type=None if tipo == "Todos" else tipo,
                search=busca or None,
            )

        def on_success(resultado: Dict[str, Any]) -> None:
            if not self.winfo_exists():
                return
            self._renderizar(resultado)
            ors = (resultado.get("data") or {}).get("interventions") or []
            self._filtros_info.configure(
                text=f"{len(ors)} intervencao(oes) encontrada(s)"
            )

        def on_error(exc: Exception) -> None:
            logger.error("Erro ao filtrar intervencoes: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _limpar_filtros(self) -> None:
        if not self._filtros_built:
            self._build_filtros_lazy()
        if self._f_tipo is not None and self._f_tipo.winfo_exists():
            self._f_tipo.widget.set("Todos")
        if self._f_data_inicio is not None and self._f_data_inicio.winfo_exists():
            self._f_data_inicio.delete(0, "end")
        if self._f_data_fim is not None and self._f_data_fim.winfo_exists():
            self._f_data_fim.delete(0, "end")
        if self._f_busca is not None and self._f_busca.winfo_exists():
            self._f_busca.delete(0, "end")
        if self._filtros_info is not None and self._filtros_info.winfo_exists():
            self._filtros_info.configure(text="")
        self._carregar_intervencoes()

    def _carregar_estudantes(self) -> None:
        def fetch() -> Dict[str, Any]:
            from ser_pleno.features.estudantes.service import servico_estudante
            return servico_estudante.listar_estudantes()

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

    def _carregar_intervencoes(self) -> None:
        self._show_skeleton()

        def fetch() -> Dict[str, Any]:
            aluno_id = (
                self._selected_student.get("id") if self._selected_student else None
            )
            return self.servico_intervencoes.listar_intervencoes(student_id=aluno_id)

        def on_success(resultado: Dict[str, Any]) -> None:
            self._hide_skeleton()
            self._renderizar(resultado)

        def on_error(exc: Exception) -> None:
            self._hide_skeleton()
            logger.error("Erro ao carregar intervencoes: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _show_skeleton(self) -> None:
        clear_children(self._area_historico)
        for _ in range(6):
            s = ctk.CTkFrame(
                self._area_historico,
                fg_color=I["card_bg"],
                corner_radius=I["card_radius"],
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
            fg_color=I["accent_soft"],
            corner_radius=10,
            cursor="hand2",
        )
        todos_row.pack(fill="x", pady=(0, spacing("xs")), padx=spacing("xs"))
        ctk.CTkLabel(
            todos_row,
            text=f"{ICONS['group']}  Todos os estudantes",
            font=font(size=12, weight="bold"),
            text_color=I["accent"],
        ).pack(padx=spacing("md"), pady=spacing("sm"))
        bind_clickable(
            todos_row, lambda: self._mostrar_intervencoes(self._todas_intervencoes)
        )

        batch = WidgetBatchBuilder(parent=self._scroll_students, batch_size=20)
        for st in estudantes:
            batch.add(lambda st=st: self._criar_student_card(st))
        batch.execute()

    def _criar_student_card(self, student: Dict[str, Any]) -> StudentCardIntervention:
        card = StudentCardIntervention(
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
        self, student: Dict[str, Any], card_widget: StudentCardIntervention
    ) -> None:
        if self._selected_card:
            self._selected_card.set_selected(False)
        self._selected_card = card_widget
        card_widget.set_selected(True)
        self._selected_student = student
        self._atualizar_badge_estudante()
        self._carregar_intervencoes()

    def _mostrar_intervencoes(self, intervencoes: List[Dict[str, Any]]) -> None:
        clear_children(self._area_historico)

        if not intervencoes:
            ctk.CTkLabel(
                self._area_historico,
                text=f"{ICONS['heart']}  Nenhuma intervencao para este estudante",
                font=font(size=13),
                text_color=I["text_muted"],
            ).pack(pady=30)
            return

        self._todas_intervencoes = list(intervencoes)

        batch = WidgetBatchBuilder(parent=self._area_historico, batch_size=20)
        for iv in intervencoes:
            batch.add(
                lambda iv=iv: InterventionCard(
                    self._area_historico,
                    intervention=iv,
                    on_view=self._ver_intervencao,
                    on_delete=self._excluir_intervencao,
                ).pack(fill="both", expand=True, pady=(0, 10))
            )
        batch.execute()

    def _renderizar(self, resultado: Dict[str, Any]) -> None:
        clear_children(self._area_historico)

        intervencoes = []
        if resultado.get("success"):
            intervencoes = (resultado.get("data") or {}).get("interventions") or []

        self._todas_intervencoes = intervencoes

        if not intervencoes:
            EmptyState(
                self._area_historico,
                icon=ICONS["heart"],
                title="Nenhuma intervencao registrada",
                subtitle="Registre uma nova intervencao para comecar",
                action_text=" + Nova Intervencao",
                action_command=lambda: self._mudar_tab("nova"),
            ).pack(pady=30)
        else:
            self._mostrar_intervencoes(intervencoes)

    def _salvar_intervencao(self) -> None:
        if not self._form_built:
            self._build_form_lazy()
        if self.f_tipo is None or not self.f_tipo.winfo_exists():
            return

        tipo_raw = self.f_tipo.get()
        tipo_map = {v: k for k, v in ServicoIntervencoes.get_tipos_intervencao()}
        intervention_type = tipo_map.get(tipo_raw, "counseling")

        resultado_raw = self.f_resultado.get()
        resultado_map = {v: k for k, v in ServicoIntervencoes.get_resultados_intervencao()}
        outcome = resultado_map.get(resultado_raw, "pending")

        dados = {
            "student_id": (
                self._selected_student.get("id")
                if self._selected_student
                else None
            ),
            "date": self.f_data.get().strip() if self.f_data is not None and self.f_data.winfo_exists() else "",
            "intervention_type": intervention_type,
            "duration_minutes": int(self.f_duracao.get().strip() or 0) if self.f_duracao is not None and self.f_duracao.winfo_exists() else None,
            "notes": self.f_notas.get().strip() if self.f_notas is not None and self.f_notas.winfo_exists() else "",
            "outcome": outcome,
            "outcome_notes": self.f_obs_resultado.get().strip() if self.f_obs_resultado is not None and self.f_obs_resultado.winfo_exists() else "",
            "follow_up_required": outcome == "needs_followup",
        }

        if not dados["student_id"]:
            self._show_error("Selecione um estudante primeiro.", title="Atencao")
            return
        if not dados["date"]:
            self._show_error("Informe a data da intervencao.", title="Atencao")
            return
        if not dados["notes"]:
            self._show_error("Preencha as anotacoes da intervencao.", title="Atencao")
            return

        def save():
            return self.servico_intervencoes.adicionar_intervencao(dados)

        def on_ok(resultado):
            if resultado.get("success"):
                self._limpar_e_voltar_historico()
                self._carregar_intervencoes()
                self._show_success("Intervencao registrada com sucesso")
            else:
                self._show_error(
                    resultado.get("error", resultado.get("message", "Falha ao registrar intervencao."))
                )

        AsyncRunner.run(
            task=save,
            on_success=on_ok,
            on_error=lambda e: self._show_error(str(e)),
            widget_ref=self,
        )

    def reload(self) -> None:
        self._carregar_intervencoes()

    def _ver_intervencao(self, iv: Dict[str, Any]) -> None:
        self._modal_detalhe(iv)

    def _excluir_intervencao(self, iid: int) -> None:
        if not self._confirmar("Excluir esta intervencao?"):
            return

        def delete():
            return self.servico_intervencoes.deletar_intervencao(iid)

        AsyncRunner.run(
            task=delete,
            on_success=lambda _: self._carregar_intervencoes(),
            on_error=lambda e: self._show_error(str(e)),
            widget_ref=self,
        )

    def _modal_detalhe(self, iv: Dict[str, Any]) -> None:
        modal = ctk.CTkToplevel(self)
        modal.title("Intervencao")
        modal.configure(fg_color=I["card_bg"])
        modal.resizable(False, False)

        w, h = 600, 520
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        itype = iv.get("intervention_type", "other")
        tipo_label, tipo_color = _TIPOS_INTERVENCAO.get(itype, ("Outro", I["text_muted"]))

        banner = ctk.CTkFrame(modal, fg_color=THEME["bg_alt"], corner_radius=0, height=70)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=spacing("xl"))

        ib = ctk.CTkFrame(
            bi, width=42, height=42, corner_radius=12, fg_color=tipo_color
        )
        ib.pack(side="left", padx=(0, 12))
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text=ICONS["heart"], font=font(size=18)).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(
            ts,
            text=tipo_label,
            font=font(size=14, weight="bold"),
            text_color=I["text"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            ts,
            text=f"{ICONS['users']}  {iv.get('student_name', 'Estudante')}",
            font=font(size=10),
            text_color=I["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        body = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        body.pack(
            fill="both", expand=True, padx=spacing("xl"), pady=spacing("md")
        )

        detalhes_list = [
            (f"{ICONS['calendar']}  Data", (iv.get("date") or "—")[:10]),
            (f"{ICONS['pin']}  Tipo", tipo_label),
            (f"{ICONS['clock']}  Duracao", f"{iv.get('duration_minutes') or '—'} min"),
            (f"{ICONS['check']}  Resultado", iv.get("outcome") or "—"),
        ]

        for label, value in detalhes_list:
            row = ctk.CTkFrame(body, fg_color=THEME["bg_alt"], corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row,
                text=label,
                width=170,
                font=font(size=12),
                text_color=I["text_muted"],
                anchor="w",
            ).pack(side="left", padx=spacing("md"), pady=spacing("md"))
            ctk.CTkLabel(
                row,
                text=str(value),
                font=font(size=12, weight="bold"),
                text_color=I["text"],
            ).pack(side="left")

        notes = iv.get("notes", "")
        if notes:
            ctk.CTkFrame(body, height=1, fg_color=I["divider"]).pack(
                fill="x", pady=(10, 8)
            )
            ctk.CTkLabel(
                body,
                text=f"{ICONS['file']}  Anotacoes",
                font=font(size=12, weight="bold"),
                text_color=I["accent"],
            ).pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(
                body,
                text=notes,
                font=font(size=12),
                text_color=I["text"],
                wraplength=460,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(0, 8))

        outcome_notes = iv.get("outcome_notes", "")
        if outcome_notes:
            ctk.CTkFrame(body, height=1, fg_color=I["divider"]).pack(
                fill="x", pady=(10, 8)
            )
            ctk.CTkLabel(
                body,
                text=f"{ICONS['chat']}  Observacoes do Resultado",
                font=font(size=12, weight="bold"),
                text_color=I["accent"],
            ).pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(
                body,
                text=outcome_notes,
                font=font(size=12),
                text_color=I["text"],
                wraplength=460,
                justify="left",
                anchor="w",
            ).pack(anchor="w", pady=(0, 8))

        btn_row = ctk.CTkFrame(modal, fg_color="transparent")
        btn_row.pack(pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="Fechar",
            command=modal.destroy,
            height=38,
            corner_radius=10,
            width=120,
            fg_color=I["accent"],
            hover_color=I["accent_hover"],
            text_color="white",
            font=font(size=13, weight="bold"),
        ).pack(side="right")

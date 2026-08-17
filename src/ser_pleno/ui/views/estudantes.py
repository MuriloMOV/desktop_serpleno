import logging
import time as _time
from datetime import datetime

import customtkinter as ctk

from ser_pleno.features.agenda.service import ServicoAgendamento
from ser_pleno.features.estudantes.service import ServicoEstudante
from ser_pleno.features.orientacoes.service import ServicoOrientacoes
from ser_pleno.infrastructure.db.query_helpers import fetch_one
from ser_pleno.ui.components.ui_components import (
    Avatar,
    Card,
    DangerButton,
    EmptyState,
    FormField,
    GhostButton,
    PrimaryButton,
    SkeletonLoader,
    bind_clickable,
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


class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        self._t0 = _time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_estudantes = ServicoEstudante(
            auth_service=getattr(controller, "auth_service", None)
        )
        self.servico_orientacoes = ServicoOrientacoes(
            auth_service=getattr(controller, "auth_service", None)
        )
        self.servico_agenda = ServicoAgendamento(
            auth_service=getattr(controller, "auth_service", None)
        )
        self._todos_estudantes: list = []
        self._selecionado: dict | None = None
        self._item_widgets: dict = {}
        self._filter_after_id = None
        self._current_user_role: str | None = None
        self._detail_panel_ready = False
        self.btn_editar = None
        self.btn_bloquear = None
        self.btn_desbloquear = None
        self.btn_suspicious = None
        self.btn_log = None
        self.lbl_nome_det = None
        self.lbl_curso_det = None
        self.status_bar = None
        self.lbl_status_icon = None
        self.lbl_status_det = None
        self.tabs = None
        self.tab_perfil = None
        self.tab_intervencoes = None
        self.tab_agenda = None
        self._av_slot = None
        self._hero_av = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._criar_toolbar_acoes()
        self._criar_conteudo()

        self.after_idle(self._build_detail_panel_lazy)
        self.after_idle(self.load_data)
        log_view_init_ms("estudantes", self._t0, widget_ref=self)

    def _get_current_user_role(self) -> str | None:
        if self._current_user_role is not None:
            return self._current_user_role
        try:
            auth_service = getattr(self.controller, "auth_service", None)
            if not auth_service or not getattr(auth_service, "user", None):
                return None
            user_id = auth_service.user.get("id")
            if not user_id:
                return None
            row = fetch_one(
                "SELECT role FROM user_profile WHERE user_id = %s AND"
                " is_active_profile = 1",
                (user_id,),
            )
            role = row.get("role") if row else None
            self._current_user_role = role
            return role
        except Exception:
            return None

    def _is_sensitive_field_visible(self) -> bool:
        role = self._get_current_user_role()
        return role in ("psicologo", "admin")

    def _criar_toolbar_acoes(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["page_x"],
            pady=(SPACING["page_y"], 4),
        )

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        PrimaryButton(
            right,
            text=f"{ICONS['add']}  Novo Estudante",
            command=self.novo_estudante_click,
            height=40,
            width=168,
        ).pack()

    def _criar_conteudo(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=SPACING["page_x"],
            pady=SPACING["section_gap"],
        )
        wrap.grid_columnconfigure(1, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        self._criar_sidebar(wrap)
        self._detail_panel_placeholder = ctk.CTkFrame(wrap, fg_color="transparent")
        self._detail_panel_placeholder.grid(row=0, column=1, sticky="nsew")

    def _build_detail_panel_lazy(self):
        if self._detail_panel_ready:
            return
        self._detail_panel_ready = True
        placeholder = getattr(self, "_detail_panel_placeholder", None)
        if placeholder is not None and placeholder.winfo_exists():
            placeholder.destroy()
        parent = placeholder.master if placeholder is not None else None
        if parent is None:
            return
        self._criar_painel_detalhes(parent)

    def _criar_sidebar(self, parent):
        sidebar = Card(parent, width=320)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["grid_gap"]))
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        search_wrap = ctk.CTkFrame(
            sidebar, fg_color=THEME["bg_alt"], corner_radius=RADIUS["input"]
        )
        search_wrap.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["card_pad"],
            pady=(SPACING["card_pad"], SPACING["item_gap"]),
        )

        ctk.CTkLabel(
            search_wrap,
            text=ICONS["search"],
            font=themed_font("body"),
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(10, 0))

        self.entry_busca = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Buscar estudante...",
            fg_color=THEME["bg_alt"],
            border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=themed_font("body"),
            height=36,
        )
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.entry_busca.bind("<KeyRelease>", self._filtrar)

        f_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        f_row.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=SPACING["card_pad"],
            pady=(0, SPACING["item_gap"]),
        )
        f_row.grid_columnconfigure((0, 1), weight=1)

        opt_style = dict(
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=32,
            corner_radius=RADIUS["button"],
            font=themed_font("caption"),
        )

        self.f_laudo = ctk.CTkOptionMenu(
            f_row,
            values=["Todos", "Com laudo", "Sem laudo"],
            command=lambda _: self._aplicar_filtros(),
            **opt_style,
        )
        self.f_laudo.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.f_aten = ctk.CTkOptionMenu(
            f_row,
            values=["Todos", "Em atenção"],
            command=lambda _: self._aplicar_filtros(),
            **opt_style,
        )
        self.f_aten.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        self.scroll_list = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.scroll_list.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=SPACING["xs"],
            pady=SPACING["xs"],
        )

        self.lbl_count = ctk.CTkLabel(
            sidebar,
            text="0 estudantes",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        )
        self.lbl_count.grid(row=3, column=0, pady=(4, 10))

    def _criar_painel_detalhes(self, parent):
        panel = Card(parent, auto_body=False)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(panel, fg_color="transparent")
        hero.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 0))

        self._av_slot = ctk.CTkFrame(
            hero, width=60, height=60, fg_color="transparent"
        )
        self._av_slot.pack(side="left", padx=(0, 16))
        self._av_slot.pack_propagate(False)
        _av = Avatar(
            self._av_slot, initials="??", size=60, color=THEME["primary"]
        )
        _av.pack(expand=True)
        self._hero_av = _av

        meta = ctk.CTkFrame(hero, fg_color="transparent")
        meta.pack(side="left", fill="both", expand=True)

        self.lbl_nome_det = ctk.CTkLabel(
            meta,
            text="Selecione um estudante",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        )
        self.lbl_nome_det.pack(anchor="w")

        self.lbl_curso_det = ctk.CTkLabel(
            meta,
            text="—",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        )
        self.lbl_curso_det.pack(anchor="w", pady=(2, 0))

        actions = ctk.CTkFrame(hero, fg_color="transparent")
        actions.pack(side="right", anchor="ne")

        row1 = ctk.CTkFrame(actions, fg_color="transparent")
        row1.pack(anchor="e", pady=(0, 6))

        self.btn_editar = PrimaryButton(
            row1,
            text=f"{ICONS['edit']}  Editar",
            command=self._editar_estudante,
            height=34,
            width=90,
            fg_color=THEME["primary_soft"],
            hover_color=THEME["primary"],
            text_color=THEME["primary"],
        )
        self.btn_editar.pack(side="left", padx=(0, 6))

        DangerButton(
            row1,
            text=f"{ICONS['delete']}  Excluir",
            command=self._excluir_estudante,
            height=34,
            width=90,
        ).pack(side="left")

        row2 = ctk.CTkFrame(actions, fg_color="transparent")
        row2.pack(anchor="e")

        self.btn_bloquear = PrimaryButton(
            row2,
            text=f"{ICONS['lock']}  Bloquear",
            command=self._bloquear_minigames,
            height=34,
            width=100,
            fg_color=THEME["danger_soft"],
            hover_color=THEME["danger"],
            text_color=THEME["danger"],
        )
        self.btn_bloquear.pack(side="left", padx=(0, 6))

        self.btn_desbloquear = PrimaryButton(
            row2,
            text=f"{ICONS['check']}  Desbloquear",
            command=self._desbloquear_minigames,
            height=34,
            width=100,
            fg_color=THEME["success_soft"],
            hover_color=THEME["success"],
            text_color=THEME["success"],
        )

        self.btn_suspicious = GhostButton(
            row2,
            text=f"{ICONS['bolt']}  Suspeita",
            command=self._verificar_comportamento_suspeito,
            height=34,
            width=95,
            text_color=THEME["warning"],
        )
        self.btn_suspicious.pack(side="left", padx=(0, 6))

        self.btn_log = GhostButton(
            row2,
            text=f"{ICONS['clock']}  Log",
            command=self._mostrar_log_bloqueio,
            height=34,
            width=70,
            text_color=THEME["text_secondary"],
        )
        self.btn_log.pack(side="left")

        ctk.CTkFrame(panel, height=1, fg_color=THEME["divider"]).pack(
            fill="x",
            padx=SPACING["card_pad"],
            pady=(SPACING["item_gap"], SPACING["xs"]),
        )

        self.tabs = ctk.CTkTabview(
            panel,
            fg_color="transparent",
            segmented_button_fg_color=THEME["bg_alt"],
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            text_color=THEME["text_secondary"],
            text_color_disabled=THEME["text_muted"],
            corner_radius=RADIUS["lg"],
        )
        self.tabs.pack(
            fill="both",
            expand=True,
            padx=SPACING["card_pad"],
            pady=(0, SPACING["xs"]),
        )

        self.tab_perfil = self.tabs.add("Perfil")
        self.tab_intervencoes = self.tabs.add("Intervenções")
        self.tab_agenda = self.tabs.add("Agenda")

        self._construir_tab_perfil()
        self._construir_tab_intervencoes()
        self._construir_tab_agenda()

        self.status_bar = ctk.CTkFrame(
            panel,
            fg_color=THEME["success_soft"],
            corner_radius=0,
            height=40,
        )
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        status_inner = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        status_inner.pack(fill="both", expand=True, padx=SPACING["card_pad"])

        self.lbl_status_icon = ctk.CTkLabel(
            status_inner,
            text="●",
            font=themed_font("body"),
            text_color=THEME["success"],
        )
        self.lbl_status_icon.pack(side="left", padx=(0, 6))

        self.lbl_status_det = ctk.CTkLabel(
            status_inner,
            text="Selecione um estudante para ver o status",
            font=themed_font("body", "bold"),
            text_color=THEME["success"],
        )
        self.lbl_status_det.pack(side="left")

    def _construir_tab_perfil(self):
        scroll_tab = ctk.CTkScrollableFrame(
            self.tab_perfil, fg_color="transparent"
        )
        scroll_tab.pack(fill="both", expand=True)

        grid = ctk.CTkFrame(scroll_tab, fg_color="transparent")
        grid.pack(fill="x", pady=(0, SPACING["item_gap"]))
        grid.grid_columnconfigure((0, 1), weight=1)

        cfg = [
            ("Contato", "--", ICONS["chart"], 0, 0, "card_email"),
            ("Telefone", "--", ICONS["location"], 0, 1, "card_phone"),
            ("Idade", "--", ICONS["cake"], 1, 0, "card_idade"),
            ("Curso / Turma", "--", ICONS["group"], 1, 1, "card_curso"),
            (
                "Professor Responsável",
                "--",
                ICONS["user"],
                2,
                0,
                "card_professor",
            ),
            ("Status", "--", ICONS["check"], 2, 1, "card_status"),
            ("Laudo Médico", "--", ICONS["file"], 3, 0, "card_laudo"),
            (
                "Nível de Prioridade",
                "--",
                ICONS["bolt"],
                3,
                1,
                "card_prioridade",
            ),
        ]
        for label, value, icon, r, c, attr in cfg:
            lbl = self._info_box(grid, label, value, icon, r, c)
            setattr(self, attr, lbl)

        if self._is_sensitive_field_visible():
            extra = ctk.CTkFrame(scroll_tab, fg_color="transparent")
            extra.pack(fill="x", pady=(0, SPACING["item_gap"]))
            extra.grid_columnconfigure((0, 1), weight=1)

            at = self._info_box(
                extra, "Motivo da Atenção", "—", ICONS["alert"], 0, 0
            )
            setattr(self, "card_atencao", at)

            gn = self._info_box(
                extra, "Observações Gerais", "—", ICONS["file"], 0, 1
            )
            setattr(self, "card_obs", gn)

        ctk.CTkFrame(scroll_tab, height=1, fg_color=THEME["divider"]).pack(
            fill="x", pady=SPACING["item_gap"]
        )

        em_frame = ctk.CTkFrame(scroll_tab, fg_color="transparent")
        em_frame.pack(fill="x", pady=(0, SPACING["item_gap"]))
        em_frame.grid_columnconfigure((0, 1), weight=1)

        ec = self._info_box(
            em_frame, "Contato de Emergência", "—", ICONS["alert"], 0, 0
        )
        setattr(self, "card_emergency_contact", ec)

        ep = self._info_box(
            em_frame, "Telefone de Emergência", "—", ICONS["phone"], 0, 1
        )
        setattr(self, "card_emergency_phone", ep)

    def _info_box(
        self, parent, label: str, value: str, icon: str, r: int, c: int
    ) -> ctk.CTkLabel:
        box = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        box.grid(
            row=r,
            column=c,
            padx=SPACING["grid_gap"] // 2,
            pady=SPACING["grid_gap"] // 2,
            sticky="nsew",
        )

        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(
            fill="both",
            expand=True,
            padx=SPACING["card_pad"],
            pady=SPACING["item_gap"],
        )

        hdr = ctk.CTkFrame(inner, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 6))

        icon_bg = ctk.CTkFrame(
            hdr,
            fg_color=THEME["primary_soft"],
            corner_radius=RADIUS["sm"],
            width=28,
            height=28,
        )
        icon_bg.pack(side="left", padx=(0, 8))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon, font=themed_font("body")).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ctk.CTkLabel(
            hdr,
            text=label,
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(side="left")

        val_lbl = ctk.CTkLabel(
            inner,
            text=value,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
            anchor="w",
        )
        val_lbl.pack(anchor="w")
        return val_lbl

    def _construir_tab_intervencoes(self):
        self.tab_int_inner = ctk.CTkScrollableFrame(
            self.tab_intervencoes,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.tab_int_inner.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.tab_int_inner,
            text="Selecione um estudante para ver as intervenções",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).pack(pady=30)

    def _construir_tab_agenda(self):
        self.tab_ag_inner = ctk.CTkScrollableFrame(
            self.tab_agenda,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.tab_ag_inner.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.tab_ag_inner,
            text="Selecione um estudante para ver a agenda",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).pack(pady=30)

    def load_data(self):
        def fetch():
            return self.servico_estudantes.listar_estudantes()

        def on_success(result):
            self.render_list(result)

        def on_error(exc):
            self._show_error(f"Falha ao carregar estudantes.\n{exc}")
            self._set_status_erro()

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _show_error(
        self, message: str, title: str = "Não foi possível concluir"
    ) -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
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

    def _confirmar_callback(
        self, modal: ctk.CTkToplevel, resultado: dict
    ) -> None:
        resultado["ok"] = True
        modal.destroy()

    def render_list(self, result):
        if not self.winfo_exists():
            return
        self._mostrar_skeletons_lista()

        def apply():
            if not self.winfo_exists():
                return
            students = []
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, dict):
                    students = (
                        data.get("students") or data.get("results") or []
                    )
                elif isinstance(data, list):
                    students = data

            self._todos_estudantes = students
            self._renderizar_estudantes(students)

        self.after(60, apply)

    def _renderizar_estudantes(self, lista: list):
        for w in self.scroll_list.winfo_children():
            w.destroy()

        if not lista:
            EmptyState(
                self.scroll_list,
                icon=ICONS["mood_bad"],
                title="Nenhum estudante encontrado",
                subtitle="Tente ajustar os filtros de busca",
            ).pack(pady=24)
            self.lbl_count.configure(text="0 estudantes")
            return

        self.lbl_count.configure(
            text=f"{len(lista)} estudante{'s' if len(lista) != 1 else ''}"
        )

        batch = WidgetBatchBuilder(parent=self.scroll_list, batch_size=40)
        for st in lista:
            if not isinstance(st, dict):
                continue
            batch.add(lambda s=st: self._criar_item_estudante(s))
        batch.execute()

    def _mostrar_skeletons_lista(self):
        for w in self.scroll_list.winfo_children():
            w.destroy()
        batch = WidgetBatchBuilder(parent=self.scroll_list, batch_size=20)
        for _ in range(8):
            batch.add(
                lambda: SkeletonLoader(
                    self.scroll_list, width=260, height=56, variant="card"
                ).pack(fill="x", pady=4, padx=4)
            )
        batch.execute()

    def _criar_item_estudante(self, st: dict):
        nome = st.get("name", "??")
        curso = st.get("course", "Sem curso")
        atenção = st.get("requires_attention", False)
        laudo = st.get("has_medical_report", False)
        sid = st.get("id", nome)

        row = ctk.CTkFrame(
            self.scroll_list,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))
        row.st_data = st

        bind_clickable(row, lambda: self.selecionar_estudante(st, row))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)

        av_color = get_avatar_color(nome)
        av = Avatar(inner, initials=nome[:2], size=40, color=av_color)
        av.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(
            inner,
            text=nome,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner,
            text=curso,
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w")

        ind = ctk.CTkFrame(inner, fg_color="transparent")
        ind.grid(row=0, column=2, rowspan=2, padx=(6, 0))

        if laudo:
            laudo_badge = ctk.CTkFrame(
                ind, fg_color=THEME["primary_soft"], corner_radius=RADIUS["sm"]
            )
            laudo_badge.pack(side="left", padx=(0, 3))
            ctk.CTkLabel(
                laudo_badge,
                text=f"{ICONS['file']} ",
                font=themed_font("caption"),
                text_color=THEME["primary"],
            ).pack(padx=spacing("xs"), pady=spacing("xs"))

        if atenção:
            ate_badge = ctk.CTkFrame(
                ind, fg_color=THEME["danger_soft"], corner_radius=RADIUS["sm"]
            )
            ate_badge.pack(side="left")
            ctk.CTkLabel(
                ate_badge,
                text=f"{ICONS['bolt']} ",
                font=themed_font("caption"),
                text_color=THEME["danger"],
            ).pack(padx=spacing("xs"), pady=spacing("xs"))

        row.bind(
            "<Enter>",
            lambda e, r=row: (
                r.configure(fg_color=THEME["primary_soft"])
                if self._selecionado != st
                else None
            ),
        )
        row.bind(
            "<Leave>",
            lambda e, r=row, s=st: r.configure(
                fg_color=THEME["primary_soft"]
                if self._selecionado == s
                else THEME["bg_alt"]
            ),
        )

        self._item_widgets[sid] = row

    def _filtrar(self, _=None):
        if self._filter_after_id:
            self.after_cancel(self._filter_after_id)
        self._filter_after_id = self.after(180, self._aplicar_filtros)

    def _aplicar_filtros(self):
        termo = (
            self.entry_busca.get().lower()
            if hasattr(self, "entry_busca")
            else ""
        )
        laudo = self.f_laudo.get()
        aten = self.f_aten.get()

        def ok(st):
            nome_ok = termo in st.get("name", "").lower() or not termo
            laudo_ok = (
                laudo == "Todos"
                or (laudo == "Com laudo" and st.get("has_medical_report"))
                or (laudo == "Sem laudo" and not st.get("has_medical_report"))
            )
            aten_ok = aten == "Todos" or (
                aten == "Em atenção" and st.get("requires_attention")
            )
            return nome_ok and laudo_ok and aten_ok

        filtrados = [s for s in self._todos_estudantes if ok(s)]
        self._renderizar_estudantes(filtrados)

    def filtrar_estudantes(self, termo: str):
        if hasattr(self, "entry_busca"):
            self.entry_busca.delete(0, "end")
            self.entry_busca.insert(0, termo)
        self._aplicar_filtros()

    def _set_status_erro(self):
        self.status_bar.configure(fg_color=THEME["danger_soft"])
        self.lbl_status_icon.configure(
            text=ICONS["status_dot"], text_color=THEME["danger"]
        )
        self.lbl_status_det.configure(
            text="Erro ao carregar dados",
            text_color=THEME["danger"],
        )

    def selecionar_estudante(self, st: dict, widget=None):
        self._selecionado = st
        for w in self.scroll_list.winfo_children():
            w.configure(fg_color=THEME["bg_alt"])
        if widget:
            widget.configure(fg_color=THEME["primary_soft"])

        if not getattr(self, "_detail_panel_ready", False):
            self._build_detail_panel_lazy()

        if getattr(self, "_detail_panel_ready", False):
            self._atualizar_painel_detalhes(st)
        else:
            self.after_idle(lambda: self._atualizar_painel_detalhes(st))

    def _atualizar_painel_detalhes(self, st: dict):
        if not self.winfo_exists():
            return
        if not getattr(self, "_detail_panel_ready", False):
            return
        if self._selecionado != st:
            return

        nome = st.get("name", "N/A")
        curso = st.get("course", "Sem curso")
        atenção = st.get("requires_attention", False)
        sid = st.get("id")

        av_color = get_avatar_color(nome)
        if self._av_slot is not None and self._av_slot.winfo_exists():
            for w in self._av_slot.winfo_children():
                w.destroy()
            av = Avatar(self._av_slot, initials=nome[:2], size=60, color=av_color)
            av.pack(expand=True)
            self._hero_av = av

        if self.lbl_nome_det is not None and self.lbl_nome_det.winfo_exists():
            self.lbl_nome_det.configure(text=nome)
        if self.lbl_curso_det is not None and self.lbl_curso_det.winfo_exists():
            self.lbl_curso_det.configure(text=curso)

        def apply_detail(detail):
            if not self.winfo_exists():
                return
            if not detail or not detail.get("success"):
                return
            d = detail.get("data") or {}

            if hasattr(self, "card_email"):
                self.card_email.configure(
                    text=d.get("contact") or st.get("contact", "—")
                )
            if hasattr(self, "card_phone"):
                self.card_phone.configure(text=d.get("phone") or "—")
            if hasattr(self, "card_idade"):
                self.card_idade.configure(
                    text=f"{d.get('age') or st.get('age') or '—'} anos"
                )
            if hasattr(self, "card_curso"):
                self.card_curso.configure(text=d.get("course") or curso)
            if hasattr(self, "card_professor"):
                self.card_professor.configure(
                    text=d.get("professor_responsavel") or "—"
                )
            if hasattr(self, "card_status"):
                self.card_status.configure(text=d.get("status") or "—")
            if hasattr(self, "card_laudo"):
                self.card_laudo.configure(
                    text=(
                        f"{ICONS['check']}  Sim"
                        if d.get("has_medical_report")
                        else f"{ICONS['cross']}  Não"
                    ),
                    text_color=(
                        THEME["success"]
                        if d.get("has_medical_report")
                        else THEME["text_secondary"]
                    ),
                )
            if hasattr(self, "card_prioridade"):
                self.card_prioridade.configure(
                    text=str(d.get("priority_level") or 0)
                )
            if (
                hasattr(self, "card_atencao")
                and self._is_sensitive_field_visible()
            ):
                self.card_atencao.configure(
                    text=d.get("attention_reason") or "—"
                )
            if hasattr(self, "card_obs") and self._is_sensitive_field_visible():
                self.card_obs.configure(text=d.get("general_notes") or "—")
            if hasattr(self, "card_emergency_contact"):
                self.card_emergency_contact.configure(
                    text=d.get("emergency_contact") or "—"
                )
            if hasattr(self, "card_emergency_phone"):
                self.card_emergency_phone.configure(
                    text=d.get("emergency_phone") or "—"
                )

            if d.get("minigame_blocked"):
                if self.status_bar is not None and self.status_bar.winfo_exists():
                    self.status_bar.configure(fg_color=THEME["danger_soft"])
                if self.lbl_status_icon is not None and self.lbl_status_icon.winfo_exists():
                    self.lbl_status_icon.configure(
                        text=ICONS["status_dot"], text_color=THEME["danger"]
                    )
                if self.lbl_status_det is not None and self.lbl_status_det.winfo_exists():
                    self.lbl_status_det.configure(
                        text="Minigames bloqueados",
                        text_color=THEME["danger"],
                    )
                if self.btn_bloquear is not None and self.btn_bloquear.winfo_exists():
                    self.btn_bloquear.pack_forget()
                if self.btn_desbloquear is not None and self.btn_desbloquear.winfo_exists():
                    self.btn_desbloquear.pack(side="left", padx=(0, 6))
            else:
                if atenção:
                    if self.status_bar is not None and self.status_bar.winfo_exists():
                        self.status_bar.configure(fg_color=THEME["danger_soft"])
                    if self.lbl_status_icon is not None and self.lbl_status_icon.winfo_exists():
                        self.lbl_status_icon.configure(
                            text=ICONS["status_dot"], text_color=THEME["danger"]
                        )
                    if self.lbl_status_det is not None and self.lbl_status_det.winfo_exists():
                        self.lbl_status_det.configure(
                            text="Requer atendimento prioritário",
                            text_color=THEME["danger"],
                        )
                else:
                    if self.status_bar is not None and self.status_bar.winfo_exists():
                        self.status_bar.configure(fg_color=THEME["success_soft"])
                    if self.lbl_status_icon is not None and self.lbl_status_icon.winfo_exists():
                        self.lbl_status_icon.configure(
                            text=ICONS["status_dot"], text_color=THEME["success"]
                        )
                    if self.lbl_status_det is not None and self.lbl_status_det.winfo_exists():
                        self.lbl_status_det.configure(
                            text="Sem alertas — situação normal",
                            text_color=THEME["success"],
                        )
                if self.btn_desbloquear is not None and self.btn_desbloquear.winfo_exists():
                    self.btn_desbloquear.pack_forget()
                if self.btn_bloquear is not None and self.btn_bloquear.winfo_exists():
                    self.btn_bloquear.pack(side="left", padx=(0, 6))

        def fetch_detail():
            return self.servico_estudantes.obter_estudante(sid)

        def on_detail_success(res):
            apply_detail(res)
            self._carregar_aba_intervencoes(sid)
            self._carregar_aba_agenda(sid)

        def on_detail_error(exc):
            logging.error(f"Falha ao obter detalhes do estudante: {exc}")

        AsyncRunner.run(
            task=fetch_detail,
            on_success=on_detail_success,
            on_error=on_detail_error,
            widget_ref=self,
        )

        if atenção:
            if self.status_bar is not None and self.status_bar.winfo_exists():
                self.status_bar.configure(fg_color=THEME["danger_soft"])
            if self.lbl_status_icon is not None and self.lbl_status_icon.winfo_exists():
                self.lbl_status_icon.configure(
                    text=ICONS["status_dot"], text_color=THEME["danger"]
                )
            if self.lbl_status_det is not None and self.lbl_status_det.winfo_exists():
                self.lbl_status_det.configure(
                    text="Requer atendimento prioritário",
                    text_color=THEME["danger"],
                )
        else:
            if self.status_bar is not None and self.status_bar.winfo_exists():
                self.status_bar.configure(fg_color=THEME["success_soft"])
            if self.lbl_status_icon is not None and self.lbl_status_icon.winfo_exists():
                self.lbl_status_icon.configure(
                    text=ICONS["status_dot"], text_color=THEME["success"]
                )
            if self.lbl_status_det is not None and self.lbl_status_det.winfo_exists():
                self.lbl_status_det.configure(
                    text="Sem alertas — situação normal",
                    text_color=THEME["success"],
                )

        if self.btn_desbloquear is not None and self.btn_desbloquear.winfo_exists():
            self.btn_desbloquear.pack_forget()
        if self.btn_bloquear is not None and self.btn_bloquear.winfo_exists():
            self.btn_bloquear.pack(side="left", padx=(0, 6))

    def _carregar_aba_intervencoes(self, student_id: int):
        for w in self.tab_int_inner.winfo_children():
            w.destroy()

        def fetch():
            return self.servico_orientacoes.listar_orientacoes(
                id_estudante=student_id
            )

        def on_success(res):
            if not self.winfo_exists():
                return
            orientacoes = []
            if isinstance(res, dict):
                data = res.get("data") or {}
                orientacoes = data.get("orientations") or []

            if not orientacoes:
                EmptyState(
                    self.tab_int_inner,
                    icon=ICONS["mood_bad"],
                    title="Nenhuma intervenção registrada",
                    subtitle="As orientações aparecerão aqui",
                ).pack(pady=24)
                return

            batch = WidgetBatchBuilder(parent=self.tab_int_inner, batch_size=20)
            for ori in orientacoes:
                batch.add(lambda o=ori: self._criar_item_intervencao(o))
            batch.execute()

        def on_error(exc):
            if not self.winfo_exists():
                return
            ctk.CTkLabel(
                self.tab_int_inner,
                text="Erro ao carregar intervenções",
                font=themed_font("body"),
                text_color=THEME["danger"],
            ).pack(pady=30)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _criar_item_intervencao(self, ori: dict):
        row = ctk.CTkFrame(
            self.tab_int_inner,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            inner,
            text=ori.get("title", "Sem título"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            inner,
            text=ori.get("theme", ""),
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        ctk.CTkLabel(
            inner,
            text=ori.get("session_date") or "—",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

    def _carregar_aba_agenda(self, student_id: int):
        for w in self.tab_ag_inner.winfo_children():
            w.destroy()

        def fetch():
            return self.servico_agenda.listar_agendamentos()

        def on_success(res):
            if not self.winfo_exists():
                return
            agendamentos = []
            if isinstance(res, list):
                agendamentos = [
                    a for a in res if a.get("id_aluno") == student_id
                ]

            if not agendamentos:
                EmptyState(
                    self.tab_ag_inner,
                    icon=ICONS["calendar"],
                    title="Nenhum agendamento encontrado",
                    subtitle="Os agendamentos aparecerão aqui",
                ).pack(pady=24)
                return

            batch = WidgetBatchBuilder(parent=self.tab_ag_inner, batch_size=20)
            for ag in agendamentos:
                batch.add(lambda a=ag: self._criar_item_agenda(a))
            batch.execute()

        def on_error(exc):
            if not self.winfo_exists():
                return
            ctk.CTkLabel(
                self.tab_ag_inner,
                text="Erro ao carregar agenda",
                font=themed_font("body"),
                text_color=THEME["danger"],
            ).pack(pady=30)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _criar_item_agenda(self, ag: dict):
        row = ctk.CTkFrame(
            self.tab_ag_inner,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)

        data_hora = ag.get("data_hora")
        data_str = (
            data_hora.strftime("%d/%m/%Y %H:%M")
            if hasattr(data_hora, "strftime")
            else str(data_hora or "—")
        )

        ctk.CTkLabel(
            inner,
            text=ag.get("nome", "Agendamento"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            inner,
            text=data_str,
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        status = ag.get("status", "")
        status_colors = {
            "agendado": THEME["primary"],
            "confirmado": THEME["primary"],
            "concluido": THEME["success"],
            "cancelado": THEME["danger"],
        }
        st_color = status_colors.get(status, THEME["text_muted"])
        st_lbl = ctk.CTkLabel(
            inner,
            text=status or "—",
            font=themed_font("caption", "bold"),
            text_color=st_color,
            anchor="e",
        )
        st_lbl.grid(row=0, column=1, sticky="e")

    def _editar_estudante(self):
        if not getattr(self, "_selecionado", None):
            self._show_error("Selecione um estudante primeiro.", title="Atenção")
            return
        st = self._selecionado
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Estudante")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 620, 780
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(
            modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"]
        )
        card.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            card,
            text="Editar Estudante",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        en_nome = FormField(
            scroll,
            "Nome Completo",
            "Ex: Ana Silva",
            icon=ICONS["user"],
            helper="Nome completo do estudante",
        )
        en_nome.pack(fill="x", pady=(0, 12))
        en_nome.insert(0, st.get("name", ""))

        en_email = FormField(
            scroll,
            "Email de Contato",
            "email@exemplo.com",
            icon=ICONS["chart"],
            helper="Email institucional ou pessoal",
        )
        en_email.pack(fill="x", pady=(0, 12))
        en_email.insert(0, st.get("contact", ""))

        row_mid = ctk.CTkFrame(scroll, fg_color="transparent")
        row_mid.pack(fill="x", pady=(0, 12))
        row_mid.grid_columnconfigure((0, 1), weight=1)

        en_curso = FormField(
            row_mid, "Curso / Turma", "Ex: Psicologia", icon=ICONS["group"]
        )
        en_curso.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        en_curso.insert(0, st.get("course", ""))

        en_idade = FormField(row_mid, "Idade", "Ex: 22", icon=ICONS["cake"])
        en_idade.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        en_idade.insert(0, str(st.get("age", "")))

        en_phone = FormField(
            scroll, "Telefone", "(00) 00000-0000", icon=ICONS["location"]
        )
        en_phone.pack(fill="x", pady=(0, 12))
        en_phone.insert(0, st.get("phone", ""))

        en_emergency_contact = FormField(
            scroll,
            "Contato de Emergência",
            "Nome do contato",
            icon=ICONS["alert"],
        )
        en_emergency_contact.pack(fill="x", pady=(0, 12))
        en_emergency_contact.insert(0, st.get("emergency_contact", ""))

        en_emergency_phone = FormField(
            scroll,
            "Telefone de Emergência",
            "(00) 00000-0000",
            icon=ICONS["location"],
        )
        en_emergency_phone.pack(fill="x", pady=(0, 12))
        en_emergency_phone.insert(0, st.get("emergency_phone", ""))

        en_professor = FormField(
            scroll,
            "Professor Responsável",
            "Ex: Dr. Silva",
            icon=ICONS["user"],
        )
        en_professor.pack(fill="x", pady=(0, 12))
        en_professor.insert(0, st.get("professor_responsavel", ""))

        row_pri = ctk.CTkFrame(scroll, fg_color="transparent")
        row_pri.pack(fill="x", pady=(0, 12))
        row_pri.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            row_pri,
            text="Status",
            font=font(size=12),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._edit_status = ctk.CTkOptionMenu(
            row_pri,
            values=["ativo", "inativo", "trancado"],
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            height=40,
            corner_radius=RADIUS["input"],
        )
        self._edit_status.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self._edit_status.set(st.get("status", "ativo"))

        ctk.CTkLabel(
            row_pri,
            text="Nível de Prioridade",
            font=font(size=12),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self._edit_priority = ctk.CTkEntry(
            row_pri,
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            text_color=THEME["text"],
            font=font(size=13),
            height=40,
        )
        self._edit_priority.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        self._edit_priority.insert(0, str(st.get("priority_level", 0)))

        sw_frame = ctk.CTkFrame(
            scroll,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        sw_frame.pack(fill="x", pady=(0, 16))

        var_laudo = ctk.StringVar(
            value="Sim" if st.get("has_medical_report") else "Não"
        )
        ctk.CTkSwitch(
            sw_frame,
            text="Possui laudo médico",
            variable=var_laudo,
            onvalue="Sim",
            offvalue="Não",
            fg_color=THEME["border"],
            progress_color=THEME["primary"],
            button_color=THEME["surface"],
            button_hover_color=THEME["bg_alt"],
        ).pack(anchor="w", padx=SPACING["card_pad"], pady=(10, 0))

        ctk.CTkFrame(sw_frame, height=1, fg_color=THEME["divider"]).pack(
            fill="x", pady=10
        )

        var_aten = ctk.StringVar(
            value="Sim" if st.get("requires_attention") else "Não"
        )
        ctk.CTkSwitch(
            sw_frame,
            text="Requer atendimento prioritário",
            variable=var_aten,
            onvalue="Sim",
            offvalue="Não",
            fg_color=THEME["border"],
            progress_color=THEME["danger"],
            button_color=THEME["surface"],
            button_hover_color=THEME["bg_alt"],
        ).pack(anchor="w", padx=SPACING["card_pad"], pady=(0, 10))

        if self._is_sensitive_field_visible():
            en_atencao = FormField(
                scroll,
                "Motivo da Atenção",
                "Descreva o motivo",
                icon=ICONS["alert"],
            )
            en_atencao.pack(fill="x", pady=(0, 12))
            en_atencao.insert(0, st.get("attention_reason", ""))

            en_obs = FormField(
                scroll,
                "Observações Gerais",
                "Anotações gerais",
                icon=ICONS["file"],
            )
            en_obs.pack(fill="x", pady=(0, 12))
            en_obs.insert(0, st.get("general_notes", ""))
        else:
            en_atencao = None
            en_obs = None

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 0))

        def _salvar():
            dados = {
                "name": en_nome.get().strip(),
                "contact": en_email.get().strip(),
                "course": en_curso.get().strip(),
                "age": en_idade.get().strip(),
                "phone": en_phone.get().strip(),
                "emergency_contact": en_emergency_contact.get().strip(),
                "emergency_phone": en_emergency_phone.get().strip(),
                "professor_responsavel": en_professor.get().strip(),
                "status": self._edit_status.get(),
                "priority_level": int(self._edit_priority.get() or 0),
                "has_medical_report": var_laudo.get() == "Sim",
                "requires_attention": var_aten.get() == "Sim",
            }
            if en_atencao is not None:
                dados["attention_reason"] = en_atencao.get().strip()
            if en_obs is not None:
                dados["general_notes"] = en_obs.get().strip()

            try:
                res = self.servico_estudantes.atualizar_estudante(
                    st.get("id"), dados
                )
                if res.get("success"):
                    modal.destroy()
                    self.load_data()
                else:
                    self._show_error(
                        res.get("error", "Falha ao atualizar estudante.")
                    )
            except Exception as e:
                self._show_error(f"Falha ao atualizar estudante.\n{e}")

        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            width=110,
            height=36,
            corner_radius=10,
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            footer,
            text=f"{ICONS['check']}  Salvar",
            command=_salvar,
            width=140,
            height=36,
            corner_radius=10,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color="white",
            font=themed_font("button", "bold"),
        ).pack(side="right")

    def _excluir_estudante(self):
        if not getattr(self, "_selecionado", None):
            self._show_error("Selecione um estudante primeiro.", title="Atenção")
            return
        st = self._selecionado
        if not self._confirmar(f'Excluir o estudante "{st.get("name")}"?'):
            return
        try:
            res = self.servico_estudantes.deletar_estudante(st.get("id"))
            if res.get("success"):
                self._selecionado = None
                self.load_data()
            else:
                self._show_error(
                    res.get("error", "Falha ao excluir estudante.")
                )
        except Exception as e:
            self._show_error(f"Falha ao excluir estudante.\n{e}")

    def novo_estudante_click(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Novo Estudante")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 620, 780
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        banner = ctk.CTkFrame(
            modal,
            fg_color=THEME["primary_soft"],
            corner_radius=0,
            height=72,
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)

        b_inner = ctk.CTkFrame(banner, fg_color="transparent")
        b_inner.pack(fill="both", expand=True, padx=SPACING["page_x"])

        icon_bg = ctk.CTkFrame(
            b_inner,
            width=42,
            height=42,
            corner_radius=RADIUS["lg"],
            fg_color=THEME["primary"],
        )
        icon_bg.pack(side="left", padx=(0, 12))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=ICONS["user"], font=themed_font("h3")).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        title_stack = ctk.CTkFrame(b_inner, fg_color="transparent")
        title_stack.pack(side="left")
        ctk.CTkLabel(
            title_stack,
            text="Novo Estudante",
            font=themed_font("h4", "bold"),
            text_color=THEME["primary"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_stack,
            text="Preencha os dados do estudante",
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=20)

        scroll = ctk.CTkScrollableFrame(body, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        en_nome = FormField(
            scroll,
            "Nome Completo",
            "Ex: Ana Silva",
            icon=ICONS["user"],
            helper="Nome completo do estudante",
        )
        en_nome.pack(fill="x", pady=(0, 12))

        en_email = FormField(
            scroll,
            "Email de Contato",
            "email@exemplo.com",
            icon=ICONS["chart"],
            helper="Email institucional ou pessoal",
        )
        en_email.pack(fill="x", pady=(0, 12))

        row_mid = ctk.CTkFrame(scroll, fg_color="transparent")
        row_mid.pack(fill="x", pady=(0, 12))
        row_mid.grid_columnconfigure((0, 1), weight=1)

        en_curso = FormField(
            row_mid, "Curso / Turma", "Ex: Psicologia", icon=ICONS["group"]
        )
        en_curso.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        en_idade = FormField(row_mid, "Idade", "Ex: 22", icon=ICONS["cake"])
        en_idade.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        en_phone = FormField(
            scroll, "Telefone", "(00) 00000-0000", icon=ICONS["location"]
        )
        en_phone.pack(fill="x", pady=(0, 12))

        en_emergency_contact = FormField(
            scroll,
            "Contato de Emergência",
            "Nome do contato",
            icon=ICONS["alert"],
        )
        en_emergency_contact.pack(fill="x", pady=(0, 12))

        en_emergency_phone = FormField(
            scroll,
            "Telefone de Emergência",
            "(00) 00000-0000",
            icon=ICONS["location"],
        )
        en_emergency_phone.pack(fill="x", pady=(0, 12))

        en_professor = FormField(
            scroll,
            "Professor Responsável",
            "Ex: Dr. Silva",
            icon=ICONS["user"],
        )
        en_professor.pack(fill="x", pady=(0, 12))

        row_pri = ctk.CTkFrame(scroll, fg_color="transparent")
        row_pri.pack(fill="x", pady=(0, 12))
        row_pri.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            row_pri,
            text="Status",
            font=font(size=12),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        self._new_status = ctk.CTkOptionMenu(
            row_pri,
            values=["ativo", "inativo", "trancado"],
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            height=40,
            corner_radius=RADIUS["input"],
        )
        self._new_status.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self._new_status.set("ativo")

        ctk.CTkLabel(
            row_pri,
            text="Nível de Prioridade",
            font=font(size=12),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))
        self._new_priority = ctk.CTkEntry(
            row_pri,
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            text_color=THEME["text"],
            font=font(size=13),
            height=40,
        )
        self._new_priority.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        self._new_priority.insert(0, "0")

        sw_frame = ctk.CTkFrame(
            scroll,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        sw_frame.pack(fill="x", pady=(0, 16))

        sw_laudo = self._switch_row(
            sw_frame,
            ICONS["file"],
            "Possui laudo médico",
            "Estudante possui documentação médica",
            THEME["primary"],
        )
        ctk.CTkFrame(sw_frame, height=1, fg_color=THEME["divider"]).pack(
            fill="x"
        )
        sw_aten = self._switch_row(
            sw_frame,
            ICONS["bolt"],
            "Requer atendimento prioritário",
            "Estudante necessita de atenção especial",
            THEME["danger"],
        )

        ctk.CTkFrame(modal, height=1, fg_color=THEME["divider"]).pack(fill="x")

        footer = ctk.CTkFrame(modal, fg_color="transparent", height=64)
        footer.pack(fill="x", padx=SPACING["page_x"])
        footer.pack_propagate(False)

        GhostButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            height=38,
            width=120,
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=13)

        def salvar():
            en_nome.clear_error()
            if not en_nome.get().strip():
                en_nome.set_error("Nome é obrigatório")
                return
            dados = {
                "nome": en_nome.get().strip(),
                "email": en_email.get().strip(),
                "has_medical_report": sw_laudo.get(),
                "requires_attention": sw_aten.get(),
                "course": en_curso.get().strip(),
                "age": en_idade.get().strip(),
                "phone": en_phone.get().strip(),
                "emergency_contact": en_emergency_contact.get().strip(),
                "emergency_phone": en_emergency_phone.get().strip(),
                "professor_responsavel": en_professor.get().strip(),
                "status": self._new_status.get(),
                "priority_level": int(self._new_priority.get() or 0),
            }
            res = self.servico_estudantes.criar_estudante(dados)
            if res.get("success"):
                modal.destroy()
                self.load_data()
            else:
                self._show_error(res.get("error", "Falha ao criar estudante."))

        PrimaryButton(
            footer,
            text=f"{ICONS['check']}  Salvar Estudante",
            command=salvar,
            height=38,
            width=180,
        ).pack(side="right", pady=13)

    def _switch_row(
        self, parent, icon: str, label: str, sub: str, color: str
    ) -> ctk.CTkSwitch:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["card_pad"], pady=10)

        icon_bg = ctk.CTkFrame(
            row,
            width=32,
            height=32,
            corner_radius=RADIUS["button"],
            fg_color=THEME["primary_soft"],
        )
        icon_bg.pack(side="left", padx=(0, 10))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon, font=themed_font("body")).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        txt_col = ctk.CTkFrame(row, fg_color="transparent")
        txt_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            txt_col,
            text=label,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            txt_col,
            text=sub,
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(anchor="w")

        sw = ctk.CTkSwitch(
            row,
            text="",
            fg_color=THEME["border"],
            progress_color=color,
            button_color=THEME["surface"],
            button_hover_color=THEME["bg_alt"],
            width=44,
        )
        sw.pack(side="right")
        return sw

    def _bloquear_minigames(self):
        if not getattr(self, "_selecionado", None):
            self._show_error("Selecione um estudante primeiro.", title="Atenção")
            return
        st = self._selecionado
        modal = ctk.CTkToplevel(self)
        modal.title("Bloquear Minigames")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 480, 260
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(
            modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"]
        )
        card.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            card,
            text=f"Bloquear minigames — {st.get('name')}",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text="Motivo do bloqueio",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 4))

        entry_motivo = ctk.CTkEntry(
            card,
            placeholder_text="Informe o motivo",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            text_color=THEME["text"],
            font=themed_font("body"),
            height=40,
        )
        entry_motivo.pack(fill="x", pady=(0, 16))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", pady=(8, 0))

        def confirmar():
            motivo = entry_motivo.get().strip()
            if not motivo:
                self._show_error("Informe o motivo do bloqueio.", title="Atenção")
                return
            try:
                res = self.servico_estudantes.bloquear_minigames(
                    st.get("id"), motivo
                )
                if res.get("success"):
                    modal.destroy()
                    self.load_data()
                else:
                    self._show_error(
                        res.get("error", "Falha ao bloquear minigames.")
                    )
            except Exception as e:
                self._show_error(f"Falha ao bloquear minigames.\n{e}")

        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            width=110,
            height=36,
            corner_radius=10,
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            footer,
            text=f"{ICONS['block']}  Bloquear",
            command=confirmar,
            width=140,
            height=36,
            corner_radius=10,
            fg_color=THEME["danger"],
            hover_color=THEME["danger"],
            text_color="white",
            font=themed_font("button", "bold"),
        ).pack(side="right")

    def _desbloquear_minigames(self):
        if not getattr(self, "_selecionado", None):
            self._show_error("Selecione um estudante primeiro.", title="Atenção")
            return
        st = self._selecionado
        if not self._confirmar(f'Desbloquear minigames para "{st.get("name")}"?'):
            return
        try:
            res = self.servico_estudantes.desbloquear_minigames(st.get("id"))
            if res.get("success"):
                self.load_data()
            else:
                self._show_error(
                    res.get("error", "Falha ao desbloquear minigames.")
                )
        except Exception as e:
            self._show_error(f"Falha ao desbloquear minigames.\n{e}")

    def _verificar_comportamento_suspeito(self):
        if not getattr(self, "_selecionado", None):
            self._show_error("Selecione um estudante primeiro.", title="Atenção")
            return
        st = self._selecionado
        sid = st.get("id")

        def fetch():
            return self.servico_estudantes.verificar_comportamento_suspeito(sid)

        def on_success(res):
            if not self.winfo_exists():
                return
            if not res or not res.get("success"):
                self._show_error("Falha ao verificar comportamento suspeito.")
                return
            suspicious = res.get("suspicious", False)
            data = res.get("data") or {}
            reasons = data.get("reasons", [])
            if suspicious:
                msg = "Comportamento suspeito detectado:\n\n" + "\n".join(
                    f"- {r}" for r in reasons
                )
                self._show_error(msg, title="Comportamento Suspeito")

        def on_error(exc):
            self._show_error(
                f"Falha ao verificar comportamento suspeito.\n{exc}"
            )

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _mostrar_log_bloqueio(self):
        if not getattr(self, "_selecionado", None):
            self._show_error("Selecione um estudante primeiro.", title="Atenção")
            return
        st = self._selecionado
        sid = st.get("id")

        modal = ctk.CTkToplevel(self)
        modal.title(f"Log de Bloqueio — {st.get('name')}")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 560, 420
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(
            modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"]
        )
        card.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            card,
            text="Histórico de Bloqueio de Minigames",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text="Carregando...",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).pack(pady=30)

        def fetch():
            return self.servico_estudantes.obter_log_bloqueio(sid)

        def on_success(res):
            if not self.winfo_exists() or not modal.winfo_exists():
                return
            for w in scroll.winfo_children():
                w.destroy()

            logs = []
            if isinstance(res, dict):
                data = res.get("data") or []
                logs = data if isinstance(data, list) else []

            if not logs:
                EmptyState(
                    scroll,
                    icon=ICONS["history"],
                    title="Nenhum registro encontrado",
                    subtitle="O histórico de bloqueios aparecerá aqui",
                ).pack(pady=24)
                return

            batch = WidgetBatchBuilder(parent=scroll, batch_size=20)
            for log in logs:
                batch.add(lambda l=log, p=scroll: self._criar_item_log(p, l))
            batch.execute()

        def on_error(exc):
            if not self.winfo_exists() or not modal.winfo_exists():
                return
            for w in scroll.winfo_children():
                w.destroy()
            ctk.CTkLabel(
                scroll,
                text="Erro ao carregar log de bloqueio",
                font=themed_font("body"),
                text_color=THEME["danger"],
            ).pack(pady=30)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _criar_item_log(self, parent, log: dict):
        row = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)

        acao = log.get("action", "")
        acao_display = {
            "block": "Bloqueio",
            "unblock": "Desbloqueio",
            "alert": "Alerta",
        }.get(acao, acao)

        acao_colors = {
            "block": THEME["danger"],
            "unblock": THEME["success"],
            "alert": THEME["warning"],
        }
        ac_color = acao_colors.get(acao, THEME["text_muted"])

        ctk.CTkLabel(
            inner,
            text=acao_display,
            font=themed_font("body", "bold"),
            text_color=ac_color,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            inner,
            text=log.get("reason") or "—",
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w")

        by = log.get("performed_by") or (
            "Sistema" if log.get("auto_detected") else "—"
        )
        ctk.CTkLabel(
            inner,
            text=by,
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

        created = log.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                created = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass
        ctk.CTkLabel(
            inner,
            text=created,
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
            anchor="e",
        ).grid(row=1, column=1, sticky="e")
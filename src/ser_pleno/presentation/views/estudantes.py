import logging
import customtkinter as ctk
from datetime import datetime
from ser_pleno.application.controllers.estudantes import EstudantesController
from ser_pleno.utils.async_runner import AsyncRunner

from ser_pleno.ui.theme import (
    THEME, SPACING, RADIUS, ELEVATION, TYPO, ANIMATION, FONT_FAMILY,
    font, themed_font, mono_font, blend_color, darken, lighten, shift_hue,
)
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.presentation.components.ui_components import (
    Card, PrimaryButton, DangerButton, GhostButton, Avatar,
    Divider, Badge, Pill, Tabs, ClickableFrame, bind_clickable,
    SkeletonLoader,
)
from ser_pleno.ui.components.icons import ICONS, IconLabel
from ser_pleno.utils.avatar_utils import get_avatar_color
from ser_pleno.utils.widget_batch import WidgetBatchBuilder
from ser_pleno.utils.async_runner import log_view_init_ms



# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Componente: campo de entrada inline
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Componente: campo de entrada inline
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class _Field(ctk.CTkFrame):
    def __init__(self, parent, label: str, placeholder: str = "",
                 icon: str = "", password: bool = False, helper: str = ""):
        super().__init__(parent, fg_color="transparent")

        ctk.CTkLabel(
            self, text=label,
            font=font(size=12),
            text_color=THEME["text_secondary"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        box = ctk.CTkFrame(
            self, fg_color=THEME["input_bg"],
            corner_radius=RADIUS["input"], border_width=1,
            border_color=THEME["input_border"],
        )
        box.pack(fill="x")

        if icon:
            ctk.CTkLabel(box, text=icon,
                         font=font(size=14),
                         text_color=THEME["text_secondary"],
                         width=34).pack(side="left", padx=(8, 0))

        self.entry = ctk.CTkEntry(
            box,
            placeholder_text=placeholder,
            placeholder_text_color=THEME["text_muted"],
            fg_color=THEME["input_bg"],
            border_width=0,
            text_color=THEME["text"],
            font=font(size=13),
            height=40,
            show="●" if password else "",
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.entry.bind("<FocusIn>",  lambda e: box.configure(border_color=THEME["input_border_focus"]))
        self.entry.bind("<FocusOut>", lambda e: box.configure(border_color=THEME["input_border"]))

        self._err = ctk.CTkLabel(
            self, text=helper if helper else "",
            font=font(size=11),
            text_color=THEME["text_secondary"], anchor="w",
        )
        self._err.pack(fill="x", pady=(3, 0))

    def get(self) -> str:
        return self.entry.get()

    def set_error(self, msg: str):
        self._err.configure(text=f"{ICONS['bolt']}   {msg}", text_color=THEME["danger"])

    def clear_error(self):
        self._err.configure(text="", text_color=THEME["text_secondary"])


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  EstudantesFrame
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        import time as _time
        self._t0 = _time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller        = controller
        self.controller_estudantes = EstudantesController()
        self._todos_estudantes: list = []
        self._selecionado: dict | None = None
        self._item_widgets: dict = {}   # id → frame widget
        self._filter_after_id = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._criar_toolbar_acoes()
        self._criar_conteudo()

        self.load_data()
        log_view_init_ms("estudantes", self._t0, widget_ref=self)

    # ••••••••••••••••••••••••••••••••••
    #  Toolbar de ações
    # ••••••••••••••••••••••••••••••••••
    def _criar_toolbar_acoes(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 4))

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        PrimaryButton(
            right, text=f"{ICONS['add']}  Novo Estudante",
            command=self.novo_estudante_click,
            height=40, width=168,
        ).pack()

    # ••••••••••••••••••••••••••••••••••
    #  LAYOUT PRINCIPAL
    # ••••••••••••••••••••••••••••••••••
    def _criar_conteudo(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=SPACING["section_gap"])
        wrap.grid_columnconfigure(1, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        self._criar_sidebar(wrap)
        self._criar_painel_detalhes(wrap)

    # ••••••••••••••••••••••••••••••••••••••
    #  SIDEBAR —“ lista de estudantes
    # ••••••••••••••••••••••••••••••••••••••
    def _criar_sidebar(self, parent):
        sidebar = Card(parent, width=300)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["grid_gap"]))
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        # —— Busca —————————————————————————————————————————————————
        search_wrap = ctk.CTkFrame(sidebar, fg_color=THEME["bg_alt"], corner_radius=RADIUS["input"])
        search_wrap.grid(row=0, column=0, sticky="ew", padx=SPACING["card_pad"], pady=(SPACING["page_y"], SPACING["item_gap"]))

        ctk.CTkLabel(search_wrap, text=ICONS["search"],
                     font=themed_font("body"),
                     text_color=THEME["text_muted"]).pack(side="left", padx=(10, 0))

        self.entry_busca = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Buscar estudante...",
            fg_color=THEME["bg_alt"], border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=themed_font("body"),
            height=36,
        )
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.entry_busca.bind("<KeyRelease>", self._filtrar)

        # —— Filtros ———————————————————————————————————————————————
        f_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        f_row.grid(row=1, column=0, sticky="ew", padx=SPACING["card_pad"], pady=(0, SPACING["item_gap"]))
        f_row.grid_columnconfigure((0, 1), weight=1)

        opt_style = dict(
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=32, corner_radius=RADIUS["button"],
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

        # Divider
        ctk.CTkFrame(sidebar, height=1, fg_color=THEME["divider"]).grid(
            row=1, column=0, sticky="sew", padx=0, pady=(40, 0)
        )

        # —— Lista —————————————————————————————————————————————————
        self.scroll_list = ctk.CTkScrollableFrame(
            sidebar, fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.scroll_list.grid(row=2, column=0, sticky="nsew")

        # Contador
        self.lbl_count = ctk.CTkLabel(
            sidebar, text="0 estudantes",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        )
        self.lbl_count.grid(row=3, column=0, pady=(4, 10))

    # ••••••••••••••••••••••••••••••••••••••
    #  PAINEL DE DETALHES
    # ••••••••••••••••••••••••••••••••••••••
    def _criar_painel_detalhes(self, parent):
        panel = Card(parent, auto_body=False)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(2, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # —— Hero do estudante ——————————————————————————————————————
        hero = ctk.CTkFrame(panel, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="ew", padx=SPACING["card_pad"], pady=(SPACING["page_y"], 0))

        # Avatar grande
        self._av_slot = ctk.CTkFrame(hero, width=60, height=60, fg_color="transparent")
        self._av_slot.pack(side="left", padx=(0, 16))
        self._av_slot.pack_propagate(False)
        _av = Avatar(self._av_slot, initials="??", size=60, color=THEME["primary"])
        _av.pack(expand=True)
        self._hero_av = _av

        # Nome + curso
        meta = ctk.CTkFrame(hero, fg_color="transparent")
        meta.pack(side="left", fill="both", expand=True)

        self.lbl_nome_det = ctk.CTkLabel(
            meta, text="Selecione um estudante",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        )
        self.lbl_nome_det.pack(anchor="w")

        self.lbl_curso_det = ctk.CTkLabel(
            meta, text="—”",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        )
        self.lbl_curso_det.pack(anchor="w", pady=(2, 0))

        # Botões de ação
        actions = ctk.CTkFrame(hero, fg_color="transparent")
        actions.pack(side="right", anchor="n")

        self.btn_editar = PrimaryButton(
            actions, text=f"{ICONS['edit']}  Editar",
            command=self._editar_estudante,
            height=36, width=100,
            fg_color=THEME["primary_soft"],
            hover_color=THEME["primary"],
            text_color=THEME["primary"],
        )
        self.btn_editar.pack(side="left", padx=(0, 8))

        DangerButton(
            actions, text=f"{ICONS['delete']}  Excluir",
            command=self._excluir_estudante,
            height=36, width=100,
        ).pack(side="left")

        ctk.CTkFrame(panel, height=1, fg_color=THEME["divider"]).grid(
            row=1, column=0, sticky="ew", padx=SPACING["card_pad"], pady=(SPACING["section_gap"], 0)
        )

        # —— Tabs ——————————————————————————————————————————————————
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
        self.tabs.grid(row=2, column=0, sticky="nsew", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))

        self.tab_perfil       = self.tabs.add("Perfil")
        self.tab_intervencoes = self.tabs.add("Intervenções")
        self.tab_agenda       = self.tabs.add("Agenda")

        self._construir_tab_perfil()
        self._construir_tab_intervencoes()
        self._construir_tab_agenda()

        # —— Status bar na base ————————————————————————————————————
        self.status_bar = ctk.CTkFrame(
            panel, fg_color=THEME["success_soft"],
            corner_radius=0,
            height=44,
        )
        self.status_bar.grid(row=3, column=0, sticky="ew")
        self.status_bar.grid_propagate(False)
        self.status_bar.grid_columnconfigure(0, weight=1)

        status_inner = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        status_inner.pack(fill="both", expand=True, padx=SPACING["card_pad"])

        self.lbl_status_icon = ctk.CTkLabel(
            status_inner, text="●",
            font=themed_font("body"),
            text_color=THEME["success"],
        )
        self.lbl_status_icon.pack(side="left", padx=(0, 6))

        self.lbl_status_det = ctk.CTkLabel(
            status_inner, text="Selecione um estudante para ver o status",
            font=themed_font("body", "bold"),
            text_color=THEME["success"],
        )
        self.lbl_status_det.pack(side="left")

    # —— Tab: Perfil —————————————————————————————————————————————————————————
    def _construir_tab_perfil(self):
        grid = ctk.CTkFrame(self.tab_perfil, fg_color="transparent")
        grid.pack(fill="both", expand=True, pady=SPACING["item_gap"])
        grid.grid_columnconfigure((0, 1), weight=1)

        cfg = [
            ("Contato",       "--", ICONS["chart"], 0, 0, "card_email"),
            ("Idade",         "--", ICONS["cake"], 0, 1, "card_idade"),
            ("Curso / Turma", "--", ICONS["group"], 1, 0, "card_curso"),
            ("Laudo Médico",  "--", ICONS["file"], 1, 1, "card_laudo"),
        ]
        for label, value, icon, r, c, attr in cfg:
            lbl = self._info_box(grid, label, value, icon, r, c)
            setattr(self, attr, lbl)

    def _info_box(self, parent, label: str, value: str, icon: str,
                  r: int, c: int) -> ctk.CTkLabel:
        box = ctk.CTkFrame(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        box.grid(row=r, column=c, padx=SPACING["grid_gap"] // 2, pady=SPACING["grid_gap"] // 2, sticky="nsew")

        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["item_gap"])

        hdr = ctk.CTkFrame(inner, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 6))

        # Ícone em pill
        icon_bg = ctk.CTkFrame(hdr, fg_color=THEME["primary_soft"],
                               corner_radius=RADIUS["sm"], width=28, height=28)
        icon_bg.pack(side="left", padx=(0, 8))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon,
                     font=themed_font("body")).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            hdr, text=label,
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(side="left")

        val_lbl = ctk.CTkLabel(
            inner, text=value,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"], anchor="w",
        )
        val_lbl.pack(anchor="w")
        return val_lbl

    # —— Tab: Intervenções ———————————————————————————————————————————————————
    def _construir_tab_intervencoes(self):
        self.tab_int_inner = ctk.CTkScrollableFrame(
            self.tab_intervencoes, fg_color="transparent",
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

    # —— Tab: Agenda —————————————————————————————————————————————————————————
    def _construir_tab_agenda(self):
        self.tab_ag_inner = ctk.CTkScrollableFrame(
            self.tab_agenda, fg_color="transparent",
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

    # ••••••••••••••••••••••••••••••••••••••
    #  Dados
    # ••••••••••••••••••••••••••••••••••••••
    def load_data(self):
        def fetch():
            return self.controller_estudantes.listar_estudantes()

        def on_success(result):
            self.render_list(result)

        def on_error(exc):
            import tkinter.messagebox as mb
            mb.showerror("Erro", f"Falha ao carregar estudantes.\n{exc}")
            self._set_status_erro()

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

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
                    students = data.get("students") or data.get("results") or []
                elif isinstance(data, list):
                    students = data

            self._todos_estudantes = students
            self._renderizar_estudantes(students)

        # Pequeno delay para o skeleton aparecer antes da renderização
        self.after(60, apply)

    def _renderizar_estudantes(self, lista: list):
        for w in self.scroll_list.winfo_children():
            w.destroy()

        if not lista:
            EmptyState(
                self.scroll_list, icon=ICONS["mood_bad"], title="Nenhum estudante encontrado",
                subtitle="Tente ajustar os filtros de busca"
            ).pack(pady=24)
            self.lbl_count.configure(text="0 estudantes")
            return

        self.lbl_count.configure(text=f"{len(lista)} estudante{'s' if len(lista) != 1 else ''}")

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
            batch.add(lambda: SkeletonLoader(self.scroll_list, width=260, height=56, variant="card").pack(
                fill="x", pady=4, padx=4
            ))
        batch.execute()

    def _criar_item_estudante(self, st: dict):
        nome    = st.get("name", "??")
        curso   = st.get("course", "Sem curso")
        atenção = st.get("requires_attention", False)
        sid     = st.get("id", nome)

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

        # Avatar
        av_color = get_avatar_color(nome)
        av = Avatar(inner, initials=nome[:2], size=40, color=av_color)
        av.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")

        # Nome
        ctk.CTkLabel(
            inner, text=nome,
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).grid(row=0, column=1, sticky="w")

        # Curso
        ctk.CTkLabel(
            inner, text=curso,
            font=themed_font("caption"),
            text_color=THEME["text_secondary"], anchor="w",
        ).grid(row=1, column=1, sticky="w")

        # Badge de atenção
        if atenção:
            badge = ctk.CTkFrame(inner, fg_color=THEME["danger_soft"], corner_radius=RADIUS["sm"])
            badge.grid(row=0, column=2, rowspan=2, padx=(6, 0))
            ctk.CTkLabel(
                badge, text=f"{ICONS['bolt']} ",
                font=themed_font("caption"),
                text_color=THEME["danger"],
            ).pack(padx=spacing("sm"), pady=spacing("xs"))

        # Hover e seleção
        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=THEME["primary_soft"])
                 if self._selecionado != st else None)
        row.bind("<Leave>", lambda e, r=row, s=st: r.configure(
            fg_color=THEME["primary_soft"] if self._selecionado == s else THEME["bg_alt"]
        ))

        self._item_widgets[sid] = row

    # ••••••••••••••••••••••••••••••••••••••
    #  Filtros
    # ••••••••••••••••••••••••••••••••••••••
    def _filtrar(self, _=None):
        if self._filter_after_id:
            self.after_cancel(self._filter_after_id)
        self._filter_after_id = self.after(180, self._aplicar_filtros)

    def _aplicar_filtros(self):
        termo  = self.entry_busca.get().lower() if hasattr(self, "entry_busca") else ""
        laudo  = self.f_laudo.get()
        aten   = self.f_aten.get()

        def ok(st):
            nome_ok  = termo in st.get("name", "").lower() or not termo
            laudo_ok = (laudo == "Todos" or
                        (laudo == "Com laudo"  and st.get("has_medical_report")) or
                        (laudo == "Sem laudo"  and not st.get("has_medical_report")))
            aten_ok  = (aten == "Todos" or
                        (aten == "Em atenção"  and st.get("requires_attention")))
            return nome_ok and laudo_ok and aten_ok

        filtrados = [s for s in self._todos_estudantes if ok(s)]
        self._renderizar_estudantes(filtrados)

    # Alias legado
    def filtrar_estudantes(self, termo: str):
        if hasattr(self, "entry_busca"):
            self.entry_busca.delete(0, "end")
            self.entry_busca.insert(0, termo)
        self._aplicar_filtros()

    # ••••••••••••••••••••••••••••••••••••••
    #  Selecionar estudante
    # ••••••••••••••••••••••••••••••••••••••
    def selecionar_estudante(self, st: dict, widget=None):
        # Limpa seleção anterior
        for w in self.scroll_list.winfo_children():
            w.configure(fg_color=THEME["bg_alt"])
        if widget:
            widget.configure(fg_color=THEME["primary_soft"])

        self._selecionado = st
        nome   = st.get("name", "N/A")
        curso  = st.get("course", "Sem curso")
        atenção = st.get("requires_attention", False)

        # Atualiza avatar hero
        av_color = get_avatar_color(nome)
        for w in self._av_slot.winfo_children():
            w.destroy()
        av = Avatar(self._av_slot, initials=nome[:2], size=60, color=av_color)
        av.pack(expand=True)

        self.lbl_nome_det.configure(text=nome)
        self.lbl_curso_det.configure(text=curso)

        # Info boxes
        if self.card_email:
            self.card_email.configure(text=st.get("contact", "—”"))
        if self.card_idade:
            self.card_idade.configure(text=f"{st.get('age', '—”')} anos")
        if self.card_curso:
            self.card_curso.configure(text=curso)
        if self.card_laudo:
            self.card_laudo.configure(
                text=f"{ICONS['check']}  Sim" if st.get("has_medical_report") else f"{ICONS['cross']}  Não",
                text_color=THEME["success"] if st.get("has_medical_report") else THEME["text_secondary"],
            )

        # Status bar
        if atenção:
            self.status_bar.configure(fg_color=THEME["danger_soft"])
            self.lbl_status_icon.configure(text=ICONS["status_dot"], text_color=THEME["danger"])
            self.lbl_status_det.configure(
                text="Requer atendimento prioritário",
                text_color=THEME["danger"],
            )
        else:
            self.status_bar.configure(fg_color=THEME["success_soft"])
            self.lbl_status_icon.configure(text=ICONS["status_dot"], text_color=THEME["success"])
            self.lbl_status_det.configure(
                text="Sem alertas —” situação normal",
                text_color=THEME["success"],
            )

    # ••••••••••••••••••••••••••••••••••••••
    # •••••••••••••••••••••••••••••••••••••••
    #  Ações do estudante selecionado
    # •••••••••••••••••••••••••••••••••••••••
    def _editar_estudante(self):
        if not getattr(self, "_selecionado", None):
            messagebox.showinfo("Atenção", "Selecione um estudante primeiro.")
            return
        st = self._selecionado
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Estudante")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 560, 680
        sx = modal.winfo_screenwidth()  // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"])
        card.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(card, text="Editar Estudante",
                     font=themed_font("h2", "bold"),
                     text_color=THEME["text"]).pack(anchor="w", pady=(0, 16))

        entry_nome = ctk.CTkEntry(card, placeholder_text="Nome completo")
        entry_nome.insert(0, st.get("name", ""))
        entry_nome.pack(fill="x", pady=(0, 10))

        entry_email = ctk.CTkEntry(card, placeholder_text="Email")
        entry_email.insert(0, st.get("contact", ""))
        entry_email.pack(fill="x", pady=(0, 10))

        entry_curso = ctk.CTkEntry(card, placeholder_text="Curso/Turma")
        entry_curso.insert(0, st.get("course", ""))
        entry_curso.pack(fill="x", pady=(0, 10))

        entry_idade = ctk.CTkEntry(card, placeholder_text="Idade")
        entry_idade.insert(0, str(st.get("age", "")))
        entry_idade.pack(fill="x", pady=(0, 10))

        var_laudo = ctk.StringVar(value="Sim" if st.get("has_medical_report") else "Não")
        ctk.CTkSwitch(card, text="Possui laudo médico",
                      variable=var_laudo, onvalue="Sim", offvalue="Não").pack(anchor="w", pady=(0, 10))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 0))

        def _salvar():
            dados = {
                "name": entry_nome.get().strip(),
                "contact": entry_email.get().strip(),
                "course": entry_curso.get().strip(),
                "age": entry_idade.get().strip(),
                "has_medical_report": var_laudo.get() == "Sim",
            }
            try:
                res = self.controller_estudantes.atualizar_estudante(st.get("id"), dados)
                messagebox.showinfo("Sucesso", "Estudante atualizado com sucesso.")
                modal.destroy()
                self._carregar_estudantes()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao atualizar estudante.\n{e}")

        ctk.CTkButton(footer, text="Cancelar", command=modal.destroy,
                      width=110, height=36, corner_radius=10,
                      fg_color=THEME["divider"], hover_color=THEME["border"],
                      text_color=THEME["text_muted"]).pack(side="left", padx=(0, 8))
        ctk.CTkButton(footer, text=f"{ICONS['check']}  Salvar",
                      command=_salvar, width=140, height=36, corner_radius=10,
                      fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                      text_color="white", font=themed_font("button", "bold")).pack(side="right")

    def _excluir_estudante(self):
        if not getattr(self, "_selecionado", None):
            messagebox.showinfo("Atenção", "Selecione um estudante primeiro.")
            return
        st = self._selecionado
        if not messagebox.askyesno("Confirmar", f'Excluir o estudante "{st.get("name")}"?'):
            return
        try:
            self.controller_estudantes.deletar_estudante(st.get("id"))
            messagebox.showinfo("Sucesso", "Estudante excluído.")
            self._selecionado = None
            self._carregar_estudantes()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao excluir estudante.\n{e}")

    #  MODAL: Novo Estudante
    # ••••••••••••••••••••••••••••••••••••••
    def novo_estudante_click(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Novo Estudante")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 560, 680
        sx = modal.winfo_screenwidth()  // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        # —— Banner de topo ——————————————————————————————————————————
        banner = ctk.CTkFrame(modal, fg_color=THEME["primary_soft"],
                              corner_radius=0, height=72)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        b_inner = ctk.CTkFrame(banner, fg_color="transparent")
        b_inner.pack(fill="both", expand=True, padx=SPACING["page_x"])

        icon_bg = ctk.CTkFrame(b_inner, width=42, height=42,
                               corner_radius=RADIUS["lg"], fg_color=THEME["primary"])
        icon_bg.pack(side="left", padx=(0, 12))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=ICONS["user"],
                     font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")

        title_stack = ctk.CTkFrame(b_inner, fg_color="transparent")
        title_stack.pack(side="left")
        ctk.CTkLabel(title_stack, text="Novo Estudante",
                     font=themed_font("h4", "bold"),
                     text_color=THEME["primary"]).pack(anchor="w")
        ctk.CTkLabel(title_stack, text="Preencha os dados do estudante",
                     font=themed_font("caption"),
                     text_color=THEME["text_secondary"]).pack(anchor="w")

        # —— Corpo ———————————————————————————————————————————————————
        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=20)

        en_nome = _Field(body, "Nome Completo", "Ex: Ana Silva", icon=ICONS["user"],
                         helper="Nome completo do estudante")
        en_nome.pack(fill="x", pady=(0, 12))

        en_email = _Field(body, "Email de Contato", "email@exemplo.com", icon=ICONS["chart"],
                          helper="Email institucional ou pessoal")
        en_email.pack(fill="x", pady=(0, 12))

        row_mid = ctk.CTkFrame(body, fg_color="transparent")
        row_mid.pack(fill="x", pady=(0, 12))
        row_mid.grid_columnconfigure((0, 1), weight=1)

        en_curso = _Field(row_mid, "Curso / Turma", "Ex: Psicologia", icon=ICONS["group"])
        en_curso.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        en_idade = _Field(row_mid, "Idade", "Ex: 22", icon=ICONS["cake"])
        en_idade.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        # Switches
        sw_frame = ctk.CTkFrame(body, fg_color=THEME["bg_alt"],
                                corner_radius=RADIUS["lg"], border_width=1,
                                border_color=THEME["border"])
        sw_frame.pack(fill="x", pady=(0, 16))

        sw_laudo = self._switch_row(
            sw_frame, ICONS["file"], "Possui laudo médico",
            "Estudante possui documentação médica", THEME["primary"]
        )
        ctk.CTkFrame(sw_frame, height=1, fg_color=THEME["divider"]).pack(fill="x")
        sw_aten = self._switch_row(
            sw_frame, ICONS["bolt"], "Requer atendimento prioritário",
            "Estudante necessita de atenção especial", THEME["danger"]
        )

        # —— Rodapé ——————————————————————————————————————————————————
        ctk.CTkFrame(modal, height=1, fg_color=THEME["divider"]).pack(fill="x")

        footer = ctk.CTkFrame(modal, fg_color="transparent", height=64)
        footer.pack(fill="x", padx=SPACING["page_x"])
        footer.pack_propagate(False)

        GhostButton(
            footer, text="Cancelar",
            command=modal.destroy,
            height=38, width=120,
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=13)

        def salvar():
            en_nome.clear_error()
            if not en_nome.get().strip():
                en_nome.set_error("Nome é obrigatório")
                return
            dados = {
                "nome":                en_nome.get().strip(),
                "email":               en_email.get().strip(),
                "has_medical_report":  sw_laudo.get(),
                "requires_attention":  sw_aten.get(),
                "course":              en_curso.get().strip(),
                "age":                 en_idade.get().strip(),
            }
            res = self.controller_estudantes.criar_estudante(dados)
            if res.get("success"):
                modal.destroy()
                self.load_data()

        PrimaryButton(
            footer, text=f"{ICONS['check']}  Salvar Estudante",
            command=salvar,
            height=38, width=180,
        ).pack(side="right", pady=13)

    def _switch_row(self, parent, icon: str, label: str, sub: str,
                    color: str) -> ctk.CTkSwitch:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["card_pad"], pady=10)

        icon_bg = ctk.CTkFrame(row, width=32, height=32, corner_radius=RADIUS["button"],
                               fg_color=THEME["primary_soft"])
        icon_bg.pack(side="left", padx=(0, 10))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon,
                     font=themed_font("body")).place(relx=0.5, rely=0.5, anchor="center")

        txt_col = ctk.CTkFrame(row, fg_color="transparent")
        txt_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(txt_col, text=label,
                     font=themed_font("body", "bold"),
                     text_color=THEME["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(txt_col, text=sub,
                     font=themed_font("caption"),
                     text_color=THEME["text_secondary"], anchor="w").pack(anchor="w")

        sw = ctk.CTkSwitch(
            row, text="",
            fg_color=THEME["border"],
            progress_color=color,
            button_color=THEME["surface"],
            button_hover_color=THEME["bg_alt"],
            width=44,
        )
        sw.pack(side="right")
        return sw

    # Aliases legados
    def criar_cabecalho(self):
        pass

    def criar_area_conteudo(self):
        pass

    def criar_sidebar(self, parent):
        pass

    def criar_detalhes(self, parent):
        pass

    def criar_info_box(self, parent, label, value, icon, r, c):
        return self._info_box(parent, label, value, icon, r, c)


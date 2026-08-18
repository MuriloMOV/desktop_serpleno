# -*- coding: utf-8 -*-
"""View de Compartilhamento de Dados Clínicos."""

from __future__ import annotations

import logging
import customtkinter as ctk
from datetime import datetime

from ser_pleno.features.compartilhamento.service import ServicoCompartilhamentoDadosClinicos
from ser_pleno.utils.async_runner import AsyncRunner

from ser_pleno.ui.theme import (
    THEME,
    SPACING,
    RADIUS,
    ELEVATION,
    TYPO,
    ANIMATION,
    FONT_FAMILY,
    font,
    themed_font,
    mono_font,
    blend_color,
    darken,
    lighten,
    shift_hue,
)
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.views.base import _ErrorModal
from ser_pleno.ui.components.ui_components import (
    Card,
    PrimaryButton,
    DangerButton,
    GhostButton,
    Avatar,
    Divider,
    Badge,
    Pill,
    Tabs,
    ClickableFrame,
    bind_clickable,
    SkeletonLoader,
    EmptyState,
    KPICard,
    Toast,
    BaseModal,
)
from ser_pleno.ui.components.icons import ICONS, IconLabel
from ser_pleno.utils.avatar_utils import get_avatar_color
from ser_pleno.utils.widget_batch import WidgetBatchBuilder
from ser_pleno.utils.async_runner import log_view_init_ms


logger = logging.getLogger(__name__)


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  CompartilhamentoDadosFrame
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class CompartilhamentoDadosFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        import time as _time

        self._t0 = _time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_compartilhamento = ServicoCompartilhamentoDadosClinicos(auth_service=getattr(controller, 'auth_service', None))
        self._compartilhamentos: list = []
        self._selecionados: set = set()
        self._item_widgets: dict = {}
        self._filter_after_id = None
        self._active_tab = "lista"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._criar_toolbar_acoes()
        self._criar_conteudo()

        self.load_data()
        log_view_init_ms("compartilhamento_dados", self._t0, widget_ref=self)

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  Toolbar de ações
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def _criar_toolbar_acoes(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 4))

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        self.btn_compartilhar = PrimaryButton(
            right,
            text=f"{ICONS['send']}  Compartilhar",
            command=self._abrir_modal_compartilhar,
            height=40,
            width=168,
        )
        self.btn_compartilhar.pack(side="left", padx=(0, 8))

        self.btn_descompartilhar = DangerButton(
            right,
            text=f"{ICONS['close']}  Descompartilhar",
            command=self._descompartilhar_selecionados,
            height=40,
            width=168,
            state="disabled",
        )
        self.btn_descompartilhar.pack(side="left", padx=(0, 8))

        self.btn_bulk_share = PrimaryButton(
            right,
            text=f"{ICONS['group']}  Bulk Share",
            command=self._abrir_modal_bulk_share,
            height=40,
            width=140,
        )
        self.btn_bulk_share.pack(side="left", padx=(0, 8))

        self.btn_bulk_unshare = DangerButton(
            right,
            text=f"{ICONS['group']}  Bulk Unshare",
            command=self._abrir_modal_bulk_unshare,
            height=40,
            width=150,
        )
        self.btn_bulk_unshare.pack(side="left")

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  Layout principal
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def _criar_conteudo(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.grid(
            row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=SPACING["section_gap"]
        )
        wrap.grid_columnconfigure(1, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        self._criar_sidebar(wrap)
        self._criar_painel_principal(wrap)

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  SIDEBAR — filtros e lista
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def _criar_sidebar(self, parent):
        sidebar = Card(parent, width=300)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["grid_gap"]))
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        search_wrap = ctk.CTkFrame(sidebar, fg_color=THEME["bg_alt"], corner_radius=RADIUS["input"])
        search_wrap.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=SPACING["card_pad"],
            pady=(SPACING["page_y"], SPACING["item_gap"]),
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
            row=1, column=0, sticky="ew", padx=SPACING["card_pad"], pady=(0, SPACING["item_gap"])
        )
        f_row.grid_columnconfigure(0, weight=1)

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

        self.f_tipo = ctk.CTkOptionMenu(
            f_row,
            values=[
                "Todos",
                "medical_report",
                "academic_record",
                "attendance",
                "intervention",
                "psychological",
            ],
            command=lambda _: self._aplicar_filtros(),
            **opt_style,
        )
        self.f_tipo.grid(row=0, column=0, sticky="ew")

        ctk.CTkFrame(sidebar, height=1, fg_color=THEME["divider"]).grid(
            row=1, column=0, sticky="sew", padx=0, pady=(40, 0)
        )

        self.scroll_list = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.scroll_list.grid(row=2, column=0, sticky="nsew")

        self.lbl_count = ctk.CTkLabel(
            sidebar,
            text="0 compartilhamentos",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        )
        self.lbl_count.grid(row=3, column=0, pady=(4, 10))

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  PAINEL PRINCIPAL
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def _criar_painel_principal(self, parent):
        panel = Card(parent, auto_body=False)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(0, weight=1)
        panel.grid_columnconfigure(0, weight=1)

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
            fill="both", expand=True, padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0)
        )

        self.tab_lista = self.tabs.add("Lista")
        self.tab_historico = self.tabs.add("Histórico")
        self.tab_relatorio = self.tabs.add("Relatório")

        self._construir_tab_lista()
        self._construir_tab_historico()
        self._construir_tab_relatorio()

    def _construir_tab_lista(self):
        self.tab_lista_inner = ctk.CTkScrollableFrame(
            self.tab_lista,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.tab_lista_inner.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.tab_lista_inner,
            text="Selecione um compartilhamento para ver detalhes",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).pack(pady=30)

    def _construir_tab_historico(self):
        self.tab_historico_inner = ctk.CTkScrollableFrame(
            self.tab_historico,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.tab_historico_inner.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.tab_historico_inner,
            text="Selecione um estudante para ver o histórico",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).pack(pady=30)

    def _construir_tab_relatorio(self):
        self.tab_relatorio_inner = ctk.CTkScrollableFrame(
            self.tab_relatorio,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.tab_relatorio_inner.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.tab_relatorio_inner,
            text="Carregando relatório...",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).pack(pady=30)

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  Dados
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def load_data(self):
        self._carregar_lista()
        self._carregar_relatorio()

    def _carregar_lista(self):
        def fetch():
            return self.servico_compartilhamento.listar_compartilhamentos()

        def on_success(result):
            self.render_list(result)

        def on_error(exc):
            self._show_error(f"Falha ao carregar compartilhamentos.\n{exc}")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _carregar_relatorio(self):
        def fetch():
            return self.servico_compartilhamento.obter_relatorio()

        def on_success(result):
            self.render_relatorio(result)

        def on_error(exc):
            self._show_error(f"Falha ao carregar relatório.\n{exc}")

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
            compartilhamentos = []
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, dict):
                    compartilhamentos = data.get("results") or data.get("data") or []
                elif isinstance(data, list):
                    compartilhamentos = data

            self._compartilhamentos = compartilhamentos
            self._renderizar_compartilhamentos(compartilhamentos)

        self.after(60, apply)

    def _mostrar_skeletons_lista(self):
        for w in self.tab_lista_inner.winfo_children():
            w.destroy()
        batch = WidgetBatchBuilder(parent=self.tab_lista_inner, batch_size=20)
        for _ in range(6):
            batch.add(
                lambda: SkeletonLoader(
                    self.tab_lista_inner, width=260, height=56, variant="card"
                ).pack(fill="x", pady=4, padx=4)
            )
        batch.execute()

    def _renderizar_compartilhamentos(self, lista: list):
        for w in self.tab_lista_inner.winfo_children():
            w.destroy()

        if not lista:
            EmptyState(
                self.tab_lista_inner,
                icon=ICONS["empty"],
                title="Nenhum compartilhamento encontrado",
                subtitle="Ajuste os filtros ou realize um novo compartilhamento",
            ).pack(pady=24)
            self.lbl_count.configure(text="0 compartilhamentos")
            return

        self.lbl_count.configure(
            text=f"{len(lista)} compartilhamento{'s' if len(lista) != 1 else ''}"
        )

        batch = WidgetBatchBuilder(parent=self.tab_lista_inner, batch_size=40)
        for comp in lista:
            if not isinstance(comp, dict):
                continue
            batch.add(lambda c=comp: self._criar_item_compartilhamento(c))
        batch.execute()

    def _criar_item_compartilhamento(self, comp: dict):
        student = comp.get("student", {})
        student_name = student.get("name", "??")
        student_id = student.get("id")
        data_type = comp.get("data_type", "")
        created_at = comp.get("created_at", "")
        shared_with = comp.get("shared_with_user", {})
        shared_with_name = shared_with.get("name", "??")
        shared_with_role = shared_with.get("role", "")

        row = ctk.CTkFrame(
            self.tab_lista_inner,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))
        row.comp_data = comp
        row.student_id = student_id

        bind_clickable(row, lambda c=comp, r=row: self.selecionar_compartilhamento(c, r))
        row.bind("<Double-Button-1>", lambda e, sid=student_id: self._carregar_historico(sid))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            inner,
            text=ICONS["file"],
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            width=34,
        ).grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(
            inner,
            text=student_name,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner,
            text=f"{data_type} → {shared_with_name} ({shared_with_role})",
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(2, 0))

        if created_at:
            ctk.CTkLabel(
                inner,
                text=created_at,
                font=themed_font("caption"),
                text_color=THEME["text_muted"],
                anchor="w",
            ).grid(row=0, column=2, sticky="e", padx=(10, 0))

        check_var = ctk.BooleanVar(value=comp.get("id") in self._selecionados)
        ctk.CTkCheckBox(
            inner,
            text="",
            variable=check_var,
            command=lambda cid=comp.get("id"), var=check_var: self._toggle_selecao(cid, var),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            width=20,
        ).grid(row=0, column=3, rowspan=2, padx=(10, 0), sticky="ns")

        row.bind(
            "<Enter>",
            lambda e, r=row, cid=comp.get("id"): (
                r.configure(fg_color=THEME["primary_soft"])
                if cid not in self._selecionados
                else None
            ),
        )
        row.bind(
            "<Leave>",
            lambda e, r=row, c=comp: r.configure(
                fg_color=THEME["primary_soft"]
                if c.get("id") in self._selecionados
                else THEME["bg_alt"]
            ),
        )

        self._item_widgets[comp.get("id")] = row

    def _toggle_selecao(self, comp_id, var=None):
        if comp_id in self._selecionados:
            self._selecionados.discard(comp_id)
            if var:
                var.set(False)
        else:
            self._selecionados.add(comp_id)
            if var:
                var.set(True)
        self._atualizar_estado_botoes()

    def _atualizar_estado_botoes(self):
        estado = "normal" if self._selecionados else "disabled"
        self.btn_descompartilhar.configure(state=estado)

    def selecionar_compartilhamento(self, comp: dict, widget=None):
        for w in self.tab_lista_inner.winfo_children():
            w.configure(fg_color=THEME["bg_alt"])
        if widget:
            widget.configure(fg_color=THEME["primary_soft"])

        self._selecionados = {comp.get("id")}
        self._atualizar_estado_botoes()

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  Filtros
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def _filtrar(self, _=None):
        if self._filter_after_id:
            self.after_cancel(self._filter_after_id)
        self._filter_after_id = self.after(180, self._aplicar_filtros)

    def _aplicar_filtros(self):
        termo = self.entry_busca.get().lower() if hasattr(self, "entry_busca") else ""
        tipo = self.f_tipo.get()

        def ok(comp):
            student = comp.get("student", {})
            nome_ok = termo in student.get("name", "").lower() or not termo
            tipo_ok = tipo == "Todos" or comp.get("data_type") == tipo
            return nome_ok and tipo_ok

        filtrados = [c for c in self._compartilhamentos if ok(c)]
        self._renderizar_compartilhamentos(filtrados)

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  Ações
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def _abrir_modal_compartilhar(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Compartilhar Dados Clínicos")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 560, 500
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"])
        card.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            card,
            text="Compartilhar Dados Clínicos",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkLabel(
            card,
            text="Estudante",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.combo_estudante = ctk.CTkComboBox(
            card,
            values=["Selecione um estudante"],
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
        )
        self.combo_estudante.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text="Tipo de Dado",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.combo_tipo = ctk.CTkComboBox(
            card,
            values=[
                "medical_report",
                "academic_record",
                "attendance",
                "intervention",
                "psychological",
            ],
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
        )
        self.combo_tipo.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text="Compartilhar com (usuário)",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.combo_usuario = ctk.CTkComboBox(
            card,
            values=["Selecione um usuário"],
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
        )
        self.combo_usuario.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text="Função",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.entry_funcao = ctk.CTkEntry(
            card,
            placeholder_text="Ex: professor, psicólogo",
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=themed_font("body"),
            height=36,
        )
        self.entry_funcao.pack(fill="x", pady=(0, 16))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 0))

        GhostButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            height=38,
            width=120,
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=13)

        def compartilhar():
            estudante = self.combo_estudante.get()
            tipo = self.combo_tipo.get()
            usuario = self.combo_usuario.get()
            funcao = self.entry_funcao.get().strip()

            if not estudante or estudante == "Selecione um estudante":
                self._show_error("Selecione um estudante.", title="Atenção")
                return
            if not tipo:
                self._show_error("Selecione um tipo de dado.", title="Atenção")
                return
            if not usuario or usuario == "Selecione um usuário":
                self._show_error("Selecione um usuário.", title="Atenção")
                return
            if not funcao:
                self._show_error("Informe a função.", title="Atenção")
                return

            student_id = int(estudante.split(" - ")[0])
            shared_with_user_id = int(usuario.split(" - ")[0])

            dados = {
                "student_id": student_id,
                "data_type": tipo,
                "shared_with_user_id": shared_with_user_id,
                "shared_with_role": funcao,
            }

            res = self.servico_compartilhamento.compartilhar(dados)
            if res.get("success"):
                self._show_toast("Dados compartilhados com sucesso.", "success")
                modal.destroy()
                self._carregar_lista()
            else:
                self._show_toast(
                    f"Falha ao compartilhar: {res.get('error', res.get('message', ''))}", "danger"
                )

        PrimaryButton(
            footer,
            text=f"{ICONS['send']}  Compartilhar",
            command=compartilhar,
            height=38,
            width=180,
        ).pack(side="right", pady=13)

        self._carregar_combos(modal)

    def _abrir_modal_bulk_share(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Bulk Share")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 560, 500
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"])
        card.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            card, text="Bulk Share", font=themed_font("h3", "bold"), text_color=THEME["text"]
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkLabel(
            card,
            text="Tipo de Dado",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.bulk_combo_tipo = ctk.CTkComboBox(
            card,
            values=[
                "medical_report",
                "academic_record",
                "attendance",
                "intervention",
                "psychological",
            ],
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
        )
        self.bulk_combo_tipo.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text="Compartilhar com (usuário)",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.bulk_combo_usuario = ctk.CTkComboBox(
            card,
            values=["Selecione um usuário"],
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
        )
        self.bulk_combo_usuario.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text="Função",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.bulk_entry_funcao = ctk.CTkEntry(
            card,
            placeholder_text="Ex: professor, psicólogo",
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=themed_font("body"),
            height=36,
        )
        self.bulk_entry_funcao.pack(fill="x", pady=(0, 16))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 0))

        GhostButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            height=38,
            width=120,
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=13)

        def bulk_share():
            tipo = self.bulk_combo_tipo.get()
            usuario = self.bulk_combo_usuario.get()
            funcao = self.bulk_entry_funcao.get().strip()

            if not tipo:
                self._show_error("Selecione um tipo de dado.", title="Atenção")
                return
            if not usuario or usuario == "Selecione um usuário":
                self._show_error("Selecione um usuário.", title="Atenção")
                return
            if not funcao:
                self._show_error("Informe a função.", title="Atenção")
                return

            if self._selecionados:
                student_ids = [
                    c.get("student", {}).get("id")
                    for c in self._compartilhamentos
                    if isinstance(c, dict) and c.get("id") in self._selecionados
                ]
            else:
                student_ids = [
                    c.get("student", {}).get("id")
                    for c in self._compartilhamentos
                    if isinstance(c, dict)
                ]

            if not student_ids:
                self._show_error("Nenhum estudante disponível para bulk share.", title="Atenção")
                return

            shared_with_user_id = int(usuario.split(" - ")[0])

            dados = {
                "student_ids": student_ids,
                "data_type": tipo,
                "shared_with_user_id": shared_with_user_id,
                "shared_with_role": funcao,
            }

            res = self.servico_compartilhamento.compartilhamento_massa(dados)
            if res.get("success"):
                self._show_toast(res.get("message", "Bulk share realizado com sucesso."), "success")
                modal.destroy()
                self._selecionados.clear()
                self._atualizar_estado_botoes()
                self._carregar_lista()
            else:
                self._show_toast(
                    f"Falha ao realizar bulk share: {res.get('error', res.get('message', ''))}",
                    "danger",
                )

        PrimaryButton(
            footer,
            text=f"{ICONS['send']}  Bulk Share",
            command=bulk_share,
            height=38,
            width=180,
        ).pack(side="right", pady=13)

        self._carregar_combos_bulk(modal)

    def _abrir_modal_bulk_unshare(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Bulk Unshare")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)

        w, h = 560, 400
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"])
        card.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            card, text="Bulk Unshare", font=themed_font("h3", "bold"), text_color=THEME["text"]
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkLabel(
            card,
            text="Tipo de Dado",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.bulk_unshare_combo_tipo = ctk.CTkComboBox(
            card,
            values=[
                "medical_report",
                "academic_record",
                "attendance",
                "intervention",
                "psychological",
            ],
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
        )
        self.bulk_unshare_combo_tipo.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card,
            text="Compartilhar com (usuário)",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.bulk_unshare_combo_usuario = ctk.CTkComboBox(
            card,
            values=["Selecione um usuário"],
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            font=themed_font("body"),
            height=36,
        )
        self.bulk_unshare_combo_usuario.pack(fill="x", pady=(0, 12))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 0))

        GhostButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            height=38,
            width=120,
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=13)

        def bulk_unshare():
            tipo = self.bulk_unshare_combo_tipo.get()
            usuario = self.bulk_unshare_combo_usuario.get()

            if not tipo:
                self._show_error("Selecione um tipo de dado.", title="Atenção")
                return
            if not usuario or usuario == "Selecione um usuário":
                self._show_error("Selecione um usuário.", title="Atenção")
                return

            if self._selecionados:
                student_ids = [
                    c.get("student", {}).get("id")
                    for c in self._compartilhamentos
                    if isinstance(c, dict) and c.get("id") in self._selecionados
                ]
            else:
                student_ids = [
                    c.get("student", {}).get("id")
                    for c in self._compartilhamentos
                    if isinstance(c, dict)
                ]

            if not student_ids:
                self._show_error("Nenhum estudante disponível para bulk unshare.", title="Atenção")
                return

            shared_with_user_id = int(usuario.split(" - ")[0])

            dados = {
                "student_ids": student_ids,
                "data_type": tipo,
                "shared_with_user_id": shared_with_user_id,
            }

            res = self.servico_compartilhamento.descompartilhamento_massa(dados)
            if res.get("success"):
                self._show_toast(
                    res.get("message", "Bulk unshare realizado com sucesso."), "success"
                )
                modal.destroy()
                self._selecionados.clear()
                self._atualizar_estado_botoes()
                self._carregar_lista()
            else:
                self._show_toast(
                    f"Falha ao realizar bulk unshare: {res.get('error', res.get('message', ''))}",
                    "danger",
                )

        DangerButton(
            footer,
            text=f"{ICONS['close']}  Bulk Unshare",
            command=bulk_unshare,
            height=38,
            width=180,
        ).pack(side="right", pady=13)

        self._carregar_combos_bulk_unshare(modal)

    def _descompartilhar_selecionados(self):
        if not self._selecionados:
            self._show_toast("Selecione ao menos um compartilhamento.", "warning")
            return

        if not self._confirmar(f"Descompartilhar {len(self._selecionados)} item(s)?"):
            return

        for comp_id in list(self._selecionados):
            comp = next((c for c in self._compartilhamentos if c.get("id") == comp_id), None)
            if comp:
                dados = {
                    "student_id": comp.get("student", {}).get("id"),
                    "shared_with_user_id": comp.get("shared_with_user", {}).get("id"),
                    "data_type": comp.get("data_type", ""),
                }
                res = self.servico_compartilhamento.descompartilhar(dados)
                if not res.get("success"):
                    self._show_toast(
                        f"Falha ao descompartilhar: {res.get('error', res.get('message', ''))}",
                        "danger",
                    )

        self._selecionados.clear()
        self._atualizar_estado_botoes()
        self._carregar_lista()

    def _carregar_combos(self, modal):
        def fetch():
            return self.servico_compartilhamento.listar_estudantes_compartilhados()

        def on_success(result):
            if not modal.winfo_exists():
                return
            estudantes = []
            usuarios = []
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, list):
                    estudantes = data
                    usuarios = [
                        {"id": s.get("id"), "name": s.get("name", "")}
                        for s in data
                        if s.get("id") is not None
                    ]

            valores_estudantes = [f"{s.get('id')} - {s.get('name', '')}" for s in estudantes]
            self.combo_estudante.configure(
                values=valores_estudantes or ["Nenhum estudante encontrado"]
            )

            valores_usuarios = [f"{u.get('id')} - {u.get('name', '')}" for u in usuarios]
            self.combo_usuario.configure(values=valores_usuarios or ["Nenhum usuário encontrado"])

        def on_error(exc):
            pass

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=modal,
        )

    def _carregar_combos_bulk(self, modal):
        def fetch():
            return self.servico_compartilhamento.listar_estudantes_compartilhados()

        def on_success(result):
            if not modal.winfo_exists():
                return
            usuarios = []
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, list):
                    usuarios = [
                        {"id": s.get("id"), "name": s.get("name", "")}
                        for s in data
                        if s.get("id") is not None
                    ]

            valores_usuarios = [f"{u.get('id')} - {u.get('name', '')}" for u in usuarios]
            self.bulk_combo_usuario.configure(
                values=valores_usuarios or ["Nenhum usuário encontrado"]
            )

        def on_error(exc):
            pass

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=modal,
        )

    def _carregar_combos_bulk_unshare(self, modal):
        def fetch():
            return self.servico_compartilhamento.listar_estudantes_compartilhados()

        def on_success(result):
            if not modal.winfo_exists():
                return
            usuarios = []
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, list):
                    usuarios = [
                        {"id": s.get("id"), "name": s.get("name", "")}
                        for s in data
                        if s.get("id") is not None
                    ]

            valores_usuarios = [f"{u.get('id')} - {u.get('name', '')}" for u in usuarios]
            self.bulk_unshare_combo_usuario.configure(
                values=valores_usuarios or ["Nenhum usuário encontrado"]
            )

        def on_error(exc):
            pass

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=modal,
        )

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  Histórico
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def _carregar_historico(self, student_id: int):
        for w in self.tab_historico_inner.winfo_children():
            w.destroy()

        def fetch():
            return self.servico_compartilhamento.obter_historico(student_id)

        def on_success(result):
            if not self.winfo_exists():
                return
            history = []
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, list):
                    history = data

            if not history:
                EmptyState(
                    self.tab_historico_inner,
                    icon=ICONS["empty"],
                    title="Nenhum histórico encontrado",
                    subtitle="Este estudante não possui histórico de compartilhamento",
                ).pack(pady=24)
                return

            batch = WidgetBatchBuilder(parent=self.tab_historico_inner, batch_size=40)
            for h in history:
                if not isinstance(h, dict):
                    continue
                batch.add(lambda h_item=h: self._criar_item_historico(h_item))
            batch.execute()

        def on_error(exc):
            self._show_error(f"Falha ao carregar histórico.\n{exc}")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _criar_item_historico(self, h: dict):
        action = h.get("action", "")
        data_type = h.get("data_type", "")
        shared_by = h.get("shared_by", {})
        shared_with = h.get("shared_with_user", {})
        created_at = h.get("created_at", "")

        row = ctk.CTkFrame(
            self.tab_historico_inner,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)

        icon = ICONS["send"] if action == "share" else ICONS["close"]
        color = THEME["success"] if action == "share" else THEME["danger"]

        ctk.CTkLabel(
            inner,
            text=icon,
            font=themed_font("body"),
            text_color=color,
            width=34,
        ).grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(
            inner,
            text=f"{action.capitalize()} - {data_type}",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner,
            text=f"De: {shared_by.get('name', '??')} Para: {shared_with.get('name', '??')} ({shared_with.get('role', '')})",
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(2, 0))

        if created_at:
            ctk.CTkLabel(
                inner,
                text=created_at,
                font=themed_font("caption"),
                text_color=THEME["text_muted"],
                anchor="w",
            ).grid(row=0, column=2, sticky="e", padx=(10, 0))

    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    #  Relatório
    # •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
    def render_relatorio(self, result):
        if not self.winfo_exists():
            return

        for w in self.tab_relatorio_inner.winfo_children():
            w.destroy()

        report = {}
        if result.get("success"):
            data = result.get("data", {})
            if isinstance(data, dict):
                report = data

        if not report:
            EmptyState(
                self.tab_relatorio_inner,
                icon=ICONS["empty"],
                title="Nenhum dado de relatório",
                subtitle="Não foi possível carregar o relatório",
            ).pack(pady=24)
            return

        total = report.get("total_compartilhamentos", 0)
        total_estudantes = report.get("total_estudantes", 0)
        total_usuarios = report.get("total_usuarios_compartilhados", 0)
        por_tipo = report.get("por_tipo", {})

        kpi_row = ctk.CTkFrame(self.tab_relatorio_inner, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, SPACING["item_gap"]))
        kpi_row.grid_columnconfigure((0, 1, 2), weight=1)

        KPICard(
            kpi_row,
            title="Total Compartilhamentos",
            value=str(total),
            icon=ICONS["send"],
            size="md",
        ).grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        KPICard(
            kpi_row, title="Estudantes", value=str(total_estudantes), icon=ICONS["group"], size="md"
        ).grid(row=0, column=1, padx=(8, 8), sticky="nsew")
        KPICard(
            kpi_row,
            title="Usuários Compartilhados",
            value=str(total_usuarios),
            icon=ICONS["users"],
            size="md",
        ).grid(row=0, column=2, padx=(8, 0), sticky="nsew")

        if por_tipo:
            ctk.CTkLabel(
                self.tab_relatorio_inner,
                text="Compartilhamentos por Tipo",
                font=themed_font("h3", "bold"),
                text_color=THEME["text"],
            ).pack(anchor="w", pady=(SPACING["item_gap"], 8))

            for tipo, count in por_tipo.items():
                row = ctk.CTkFrame(
                    self.tab_relatorio_inner,
                    fg_color=THEME["bg_alt"],
                    corner_radius=RADIUS["lg"],
                )
                row.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))

                inner = ctk.CTkFrame(row, fg_color="transparent")
                inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
                inner.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    inner,
                    text=ICONS["file"],
                    font=themed_font("body"),
                    text_color=THEME["text_secondary"],
                    width=34,
                ).grid(row=0, column=0, padx=(0, 10), sticky="ns")

                ctk.CTkLabel(
                    inner,
                    text=tipo,
                    font=themed_font("body", "bold"),
                    text_color=THEME["text"],
                    anchor="w",
                ).grid(row=0, column=1, sticky="w")

                ctk.CTkLabel(
                    inner,
                    text=str(count),
                    font=themed_font("h4", "bold"),
                    text_color=THEME["primary"],
                ).grid(row=0, column=2, sticky="e")

    # Aliases legados
    def criar_cabecalho(self):
        pass

    def criar_area_conteudo(self):
        pass

    def _show_toast(self, message: str, status: str = "success"):
        try:
            Toast(self, message=message, status=status, duration=3000)
        except Exception:
            pass

    def _show_error(self, message: str, title: str = "Não foi possível concluir") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _show_success(self, message: str, duration: int = 3000) -> None:
        try:
            if hasattr(self, "_toast") and self._toast and self._toast.winfo_exists():
                self._toast.destroy()
            self._toast = Toast(
                self.winfo_toplevel(), message=message, status="success", duration=duration
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

    def _confirmar_callback(self, modal: ctk.CTkToplevel, resultado: dict):
        resultado["ok"] = True
        modal.destroy()

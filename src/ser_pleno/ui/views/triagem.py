import customtkinter as ctk

from ser_pleno.ui.theme import (
    THEME,
    SPACING,
    RADIUS,
    TYPO,
    FONT_FAMILY,
    font,
    themed_font,
    mono_font,
)
from ser_pleno.ui.theme_extensions import extend_theme
from ser_pleno.ui.components.ui_components import (
    Card,
    PrimaryButton,
    GhostButton,
    Divider,
    KPICard,
    BaseModal,
    EmptyState,
    Avatar,
    Toast,
)
from ser_pleno.ui.views.base import _ErrorModal
from ser_pleno.ui.components.icons import ICONS, IconLabel
from ser_pleno.utils.avatar_utils import get_avatar_color
from ser_pleno.features.triagem.service import ServicoTriagem
from ser_pleno.features.estudantes.service import ServicoEstudante
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder
import json

# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Design tokens — mapeamentos semânticos específicos da triagem
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

_PRIORITY_CFG = {
    "Urgente": (THEME["critico"], THEME["critico_soft"]),
    "Alta": (THEME["alto"], THEME["alto_soft"]),
    "Média": (THEME["medio"], THEME["medio_soft"]),
    "Baixa": (THEME["normal"], THEME["normal_soft"]),
}
_STATUS_CFG = {
    "Pendente": (THEME["warning"], THEME["warning_soft"]),
    "Em Andamento": (THEME["info"], THEME["info_soft"]),
    "Concluída": (THEME["success"], THEME["success_soft"]),
    "Cancelada": (THEME["text_muted"], THEME["bg_alt"]),
}
_COL_HEADERS = ["Estudante", "Formulário", "Data", "Prioridade", "Status", "Ações"]
_COL_WEIGHTS = [3, 3, 2, 2, 2, 1]


# Helpers


def _chip(parent, text: str, color: str, soft: str) -> ctk.CTkFrame:
    f = ctk.CTkFrame(parent, fg_color=soft, corner_radius=RADIUS["xs"])
    ctk.CTkLabel(f, text=text, font=themed_font("body_sm", "bold"), text_color=color).pack(
        padx=SPACING["icon_gap"], pady=SPACING["label_gap"] // 2
    )
    return f


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Campo de entrada leve
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class _DateField(ctk.CTkFrame):
    def __init__(self, parent, placeholder: str):
        super().__init__(
            parent,
            fg_color=THEME["input_bg"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["input_border"],
        )
        IconLabel(
            self,
            icon=ICONS["calendar"],
            size=20,
            fg_color="transparent",
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=(SPACING["icon_gap"], 0))
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            fg_color=THEME["input_bg"],
            border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=themed_font("body"),
            height=36,
        )
        self.entry.pack(
            side="left", fill="x", expand=True, padx=(SPACING["label_gap"], SPACING["icon_gap"])
        )
        self.entry.bind(
            "<FocusIn>", lambda e: self.configure(border_color=THEME["input_border_focus"])
        )
        self.entry.bind("<FocusOut>", lambda e: self.configure(border_color=THEME["input_border"]))

    def get(self) -> str:
        return self.entry.get()

    def delete(self, a, b):
        self.entry.delete(a, b)


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  TriagemFrame
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class TriagemFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        import time as _time

        self._t0 = _time.perf_counter()
        super().__init__(
            parent,
            fg_color=THEME["page_bg"],
            scrollbar_button_color=THEME["primary_medium"],
            scrollbar_button_hover_color=THEME["primary"],
        )
        self.controller = controller
        self.servico_triagem = ServicoTriagem()
        self.servico_estudantes = ServicoEstudante()
        self.data_master = []
        self._estudantes = []
        self._formularios = []
        self._perguntas_widgets = {}

        self._criar_toolbar_acoes()
        self._criar_kpis()
        self._criar_filtros()
        self._criar_tabela()
        self._carregar_triagens()
        self._carregar_estudantes()
        self._carregar_formularios()
        log_view_init_ms("triagem", self._t0, widget_ref=self)

    # •••••••••••••••••••••••••••••••••••••••••••
    #  CABEÇALHO
    # •••••••••••••••••••••••••••••••••••••••••••
    def _criar_toolbar_acoes(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], SPACING["label_gap"]))

        PrimaryButton(
            bar,
            text=f"{ICONS['add']}  Nova Triagem",
            command=self.abrir_nova_triagem,
            height=40,
            corner_radius=RADIUS["button"],
            width=160,
        ).pack(side="right")

        GhostButton(
            bar,
            text=f"{ICONS['list']}  Formulários",
            command=self._modal_listar_formularios,
            height=40,
            corner_radius=RADIUS["button"],
            width=160,
        ).pack(side="right", padx=(0, SPACING["icon_gap"]))

    # •••••••••••••••••••••••••••••••••••••••••••
    #  KPIs
    # •••••••••••••••••••••••••••••••••••••••••••
    def _criar_kpis(self):
        self._kpi_widgets = []
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

        kpis = [
            (
                "Total de Triagens",
                "0",
                ICONS["chart"],
                THEME["kpi_blue"],
                THEME["kpi_blue_soft"],
                "Registros",
            ),
            (
                "Pendentes",
                "0",
                ICONS["hourglass"],
                THEME["kpi_amber"],
                THEME["kpi_amber_soft"],
                "Aguardando",
            ),
            (
                "Concluídas",
                "0",
                ICONS["check"],
                THEME["kpi_green"],
                THEME["kpi_green_soft"],
                "Finalizadas",
            ),
            (
                "Alta Prioridade",
                "0",
                f"{ICONS['bolt']} ",
                THEME["kpi_red"],
                THEME["kpi_red_soft"],
                "Urgente ou Alta",
            ),
        ]
        for i, (title, val, icon, accent, soft, sub) in enumerate(kpis):
            row.grid_columnconfigure(i, weight=1)
            card = KPICard(
                row,
                title=title,
                value=val,
                icon=icon,
                accent=accent,
                unit="",
                size="md",
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["icon_gap"] // 2)
            self._kpi_widgets.append(card._value_label if hasattr(card, "_value_label") else None)

    def _atualizar_kpis(self, data_list: list):
        total = len(data_list)
        pendentes = sum(1 for d in data_list if d["status"] == "Pendente")
        concluidas = sum(1 for d in data_list if d["status"] == "Concluída")
        alta_p = sum(1 for d in data_list if d["priority"] in ("Alta", "Urgente"))
        valores = [str(total), str(pendentes), str(concluidas), str(alta_p)]
        for lbl, val in zip(self._kpi_widgets, valores):
            if lbl is not None:
                lbl.configure(text=val)

    # •••••••••••••••••••••••••••••••••••••••••••
    #  FILTROS
    # •••••••••••••••••••••••••••••••••••••••••••
    def _criar_filtros(self):
        card = Card(self, auto_body=False)
        card.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))
        ctk.CTkLabel(
            hdr,
            text=f"{ICONS['search']}  Filtrar Triagens",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["card_pad"], pady=SPACING["item_gap"])
        for i in range(5):
            row.grid_columnconfigure(i, weight=1)

        opt_style = dict(
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=38,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )

        self.filtro_busca = ctk.CTkEntry(
            row,
            placeholder_text="Buscar estudante ou formulário...",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=themed_font("body"),
            height=38,
        )
        self.filtro_busca.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["icon_gap"] // 2))

        self.filtro_status = ctk.CTkOptionMenu(
            row,
            values=["Todos", "Pendente", "Em Andamento", "Concluída", "Cancelada"],
            command=lambda _: self.aplicar_filtros(),
            **opt_style,
        )
        self.filtro_status.grid(row=0, column=1, sticky="ew", padx=SPACING["icon_gap"] // 2)

        self.filtro_prioridade = ctk.CTkOptionMenu(
            row,
            values=["Todas", "Baixa", "Média", "Alta", "Urgente"],
            command=lambda _: self.aplicar_filtros(),
            **opt_style,
        )
        self.filtro_prioridade.grid(row=0, column=2, sticky="ew", padx=SPACING["icon_gap"] // 2)

        self.data_inicial = _DateField(row, "Data inicial  dd/mm/aaaa")
        self.data_inicial.grid(row=0, column=3, sticky="ew", padx=SPACING["icon_gap"] // 2)

        self.data_final = _DateField(row, "Data final  dd/mm/aaaa")
        self.data_final.grid(row=0, column=4, sticky="ew", padx=(SPACING["icon_gap"] // 2, 0))

        # Botões
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["item_gap"]))

        GhostButton(
            btn_row,
            text="Limpar filtros",
            command=self.limpar_filtros,
            height=34,
            corner_radius=RADIUS["button"],
            text_color=THEME["text_secondary"],
        ).pack(side="right", padx=(SPACING["icon_gap"], 0))

        PrimaryButton(
            btn_row,
            text="Aplicar filtros",
            command=self.aplicar_filtros,
            height=34,
            corner_radius=RADIUS["button"],
            width=140,
        ).pack(side="right")

    # •••••••••••••••••••••••••••••••••••••••••••
    #  TABELA
    # •••••••••••••••••••••••••••••••••••••••••••
    def _criar_tabela(self):
        card = Card(self, auto_body=False)
        card.pack(
            fill="both",
            expand=True,
            padx=SPACING["page_x"],
            pady=(SPACING["section_gap"], SPACING["page_y"]),
        )

        # Cabeçalho da tabela
        hdr_outer = ctk.CTkFrame(card, fg_color="transparent")
        hdr_outer.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))

        ctk.CTkLabel(
            hdr_outer,
            text="Lista de Triagens",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        self._lbl_count = ctk.CTkLabel(
            hdr_outer,
            text=f"{len(self.data_master)} registros",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        )
        self._lbl_count.pack(side="right")

        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))

        # Header de colunas
        col_hdr = ctk.CTkFrame(
            card, fg_color=THEME["bg_alt"], corner_radius=RADIUS["none"], height=38
        )
        col_hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))
        col_hdr.pack_propagate(False)
        col_hdr.grid_columnconfigure(list(range(len(_COL_HEADERS))), weight=1)
        for i, (h, w) in enumerate(zip(_COL_HEADERS, _COL_WEIGHTS)):
            col_hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(
                col_hdr,
                text=h,
                font=themed_font("body_sm", "bold"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).grid(
                row=0,
                column=i,
                sticky="w",
                padx=(SPACING["card_pad"] if i == 0 else SPACING["icon_gap"], 0),
                pady=SPACING["icon_gap"],
            )

        # Corpo scrollável
        self.lista_triagens = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.lista_triagens.pack(
            fill="both",
            expand=True,
            padx=SPACING["icon_gap"],
            pady=(SPACING["label_gap"], SPACING["icon_gap"]),
        )

        self.renderizar_tabela(self.data_master)

    def renderizar_tabela(self, data_list: list):
        for w in self.lista_triagens.winfo_children():
            w.destroy()

        if hasattr(self, "_lbl_count"):
            self._lbl_count.configure(
                text=f"{len(data_list)} registro{'s' if len(data_list) != 1 else ''}"
            )

        if not data_list:
            EmptyState(
                self.lista_triagens,
                icon=ICONS["empty"],
                title="Nenhuma triagem encontrada",
                subtitle="",
            ).pack(pady=SPACING["section_gap"])
            return

        batch = WidgetBatchBuilder(parent=self, batch_size=20)
        for item in data_list:
            batch.add(lambda item=item: self._criar_row(item))
        batch.execute()

    def _criar_row(self, item: dict):
        row = ctk.CTkFrame(
            self.lista_triagens, fg_color=THEME["row_bg"], corner_radius=RADIUS["button"]
        )
        row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
        row.grid_columnconfigure(list(range(len(_COL_HEADERS))), weight=1)
        for i, w in enumerate(_COL_WEIGHTS):
            row.grid_columnconfigure(i, weight=w)

        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=THEME["row_hover"]))
        row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=THEME["row_bg"]))

        nome = item["student"]
        av_color = get_avatar_color(nome)
        form_nome = item.get("form_name", "—")

        # Col 0 — Estudante (avatar + nome)
        name_cell = ctk.CTkFrame(row, fg_color="transparent")
        name_cell.grid(
            row=0, column=0, sticky="w", padx=(SPACING["icon_gap"], 0), pady=SPACING["item_gap"]
        )
        av = Avatar(name_cell, initials=nome[:2], size=34, color=av_color)
        av.pack(side="left", padx=(0, SPACING["icon_gap"]))
        ctk.CTkLabel(
            name_cell, text=nome, font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack(side="left")

        # Col 1 — Formulário
        ctk.CTkLabel(
            row, text=form_nome, font=themed_font("body_sm"), text_color=THEME["text_secondary"]
        ).grid(row=0, column=1, sticky="w", padx=SPACING["icon_gap"])

        # Col 2 — Data
        ctk.CTkLabel(
            row, text=item["date"], font=themed_font("body_sm"), text_color=THEME["text_secondary"]
        ).grid(row=0, column=2, sticky="w", padx=SPACING["icon_gap"])

        # Col 3 — Prioridade (chip)
        p_color, p_soft = _PRIORITY_CFG.get(
            item["priority"], (THEME["text_secondary"], THEME["divider"])
        )
        chip_p = _chip(row, item["priority"], p_color, p_soft)
        chip_p.grid(row=0, column=3, sticky="w", padx=SPACING["icon_gap"], pady=SPACING["item_gap"])

        # Col 4 — Status (chip)
        s_color, s_soft = _STATUS_CFG.get(
            item["status"], (THEME["text_secondary"], THEME["divider"])
        )
        chip_s = _chip(row, item["status"], s_color, s_soft)
        chip_s.grid(row=0, column=4, sticky="w", padx=SPACING["icon_gap"], pady=SPACING["item_gap"])

        # Col 5 — Ações
        acts = ctk.CTkFrame(row, fg_color="transparent")
        acts.grid(
            row=0, column=5, sticky="e", padx=(0, SPACING["icon_gap"]), pady=SPACING["icon_gap"]
        )
        for icon, cmd, tip in [
            (ICONS["view"], lambda s=item: self._ver_detalhe(s), "Ver detalhe"),
            (ICONS["edit"], lambda s=item: self._editar(s), "Editar"),
            (ICONS["delete"], lambda s=item: self._excluir_triagem(s), "Excluir"),
        ]:
            GhostButton(
                acts,
                icon=icon,
                tooltip=tip,
                width=30,
                height=30,
                corner_radius=RADIUS["xs"],
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=cmd,
            ).pack(side="left", padx=SPACING["label_gap"] // 2)

    # •••••••••••••••••••••••••••••••••••••••••••
    #  Filtros
    # •••••••••••••••••••••••••••••••••••••••••••
    def aplicar_filtros(self):
        st = self.filtro_status.get()
        pr = self.filtro_prioridade.get()
        busca = self.filtro_busca.get().strip()
        filtered = [
            d
            for d in self.data_master
            if (st == "Todos" or d["status"] == st)
            and (pr == "Todas" or d["priority"] == pr)
            and (
                not busca
                or busca.lower() in d["student"].lower()
                or busca.lower() in d.get("form_name", "").lower()
            )
        ]
        self._atualizar_kpis(filtered)
        self.renderizar_tabela(filtered)

    def limpar_filtros(self):
        self.filtro_busca.delete(0, "end")
        self.filtro_status.set("Todos")
        self.filtro_prioridade.set("Todas")
        self.data_inicial.delete(0, "end")
        self.data_final.delete(0, "end")
        self._atualizar_kpis(self.data_master)
        self.renderizar_tabela(self.data_master)

    # •••••••••••••••••••••••••••••••••••••••••••
    #  Ações de linha
    # •••••••••••••••••••••••••••••••••••••••••••
    def _excluir_triagem(self, item: dict):
        nome = item.get("student", "este item")
        if not self._confirmar(f"Deseja excluir a triagem de {nome}?"):
            return

        def _task():
            return self.servico_triagem.deletar_triagem(item.get("id"))

        def _on_ok(_):
            self._carregar_triagens()

        def _on_err(e):
            self._show_error(f"Falha ao excluir triagem.\n{e}")

        AsyncRunner.run(task=_task, on_success=_on_ok, on_error=_on_err, widget_ref=self)

    # •••••••••••••••••••••••••••••••••••••••••••
    #  MODAL: Nova Triagem
    # •••••••••••••••••••••••••••••••••••••••••••
    def abrir_nova_triagem(self):
        modal = BaseModal(self, title="Nova Triagem", width=560, height=720)
        modal.configure(fg_color=THEME["surface_elevated"])

        # Banner
        banner = ctk.CTkFrame(
            modal, fg_color=THEME["primary_soft"], corner_radius=RADIUS["none"], height=68
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)
        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=SPACING["card_pad"])

        ib = ctk.CTkFrame(
            bi, width=40, height=40, corner_radius=RADIUS["button"], fg_color=THEME["primary"]
        )
        ib.pack(side="left", padx=(0, SPACING["icon_gap"]))
        ib.pack_propagate(False)
        IconLabel(
            ib,
            icon=ICONS["chart"],
            size=22,
            fg_color="transparent",
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(
            ts, text="Nova Triagem", font=themed_font("h3", "bold"), text_color=THEME["primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            ts,
            text="Preencha os dados da triagem",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

        # Corpo scrollável
        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["section_gap"])

        def field(parent, label, placeholder, icon=""):
            wrap = ctk.CTkFrame(parent, fg_color="transparent")
            wrap.pack(fill="x", pady=(0, SPACING["item_gap"]))
            ctk.CTkLabel(
                wrap,
                text=label,
                font=themed_font("body"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).pack(fill="x", pady=(0, SPACING["label_gap"]))
            box = ctk.CTkFrame(
                wrap,
                fg_color=THEME["input_bg"],
                corner_radius=RADIUS["input"],
                border_width=1,
                border_color=THEME["input_border"],
            )
            box.pack(fill="x")
            if icon:
                ctk.CTkLabel(
                    box,
                    text=icon,
                    font=themed_font("body"),
                    text_color=THEME["text_muted"],
                    width=32,
                ).pack(side="left", padx=(SPACING["icon_gap"], 0))
            en = ctk.CTkEntry(
                box,
                placeholder_text=placeholder,
                fg_color=THEME["input_bg"],
                border_width=0,
                text_color=THEME["text"],
                placeholder_text_color=THEME["text_muted"],
                font=themed_font("body"),
                height=40,
            )
            en.pack(
                side="left", fill="x", expand=True, padx=(SPACING["label_gap"], SPACING["icon_gap"])
            )
            en.bind("<FocusIn>", lambda e: box.configure(border_color=THEME["input_border_focus"]))
            en.bind("<FocusOut>", lambda e: box.configure(border_color=THEME["input_border"]))
            return en

        estudantes_map = {
            f"{e.get('nome', '')} ({e.get('id_aluno', '')})": e.get("id_aluno")
            for e in self._estudantes
        }
        estudantes_lista = (
            sorted(estudantes_map.keys()) if estudantes_map else ["Nenhum estudante encontrado"]
        )

        om_estudante = ctk.CTkOptionMenu(
            body,
            values=estudantes_lista,
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        om_estudante.pack(fill="x", pady=(0, SPACING["item_gap"]))

        formularios_map = {
            f.get("name", ""): f.get("id") for f in self._formularios if f.get("is_active")
        }
        formularios_lista = (
            sorted(formularios_map.keys()) if formularios_map else ["Nenhum formulário ativo"]
        )

        om_formulario = ctk.CTkOptionMenu(
            body,
            values=formularios_lista,
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        om_formulario.pack(fill="x", pady=(0, SPACING["item_gap"]))

        en_data = field(body, "Data da Triagem", "dd/mm/aaaa", ICONS["calendar"])

        opt_style = dict(
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, SPACING["item_gap"]))
        row2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            row2, text="Prioridade", font=themed_font("body"), text_color=THEME["text_secondary"]
        ).grid(row=0, column=0, sticky="w", padx=(0, SPACING["icon_gap"] // 2))
        ctk.CTkLabel(
            row2, text="Status", font=themed_font("body"), text_color=THEME["text_secondary"]
        ).grid(row=0, column=1, sticky="w", padx=(SPACING["icon_gap"] // 2, 0))

        om_prioridade = ctk.CTkOptionMenu(
            row2, values=["Baixa", "Média", "Alta", "Urgente"], **opt_style
        )
        om_prioridade.grid(row=1, column=0, sticky="ew", padx=(0, SPACING["icon_gap"] // 2))

        om_status = ctk.CTkOptionMenu(
            row2, values=["Pendente", "Em Andamento", "Concluída", "Cancelada"], **opt_style
        )
        om_status.grid(row=1, column=1, sticky="ew", padx=(SPACING["icon_gap"] // 2, 0))

        lbl_perguntas = ctk.CTkLabel(
            body,
            text="Perguntas do Formulário",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        )
        lbl_perguntas.pack(anchor="w", pady=(SPACING["item_gap"], SPACING["label_gap"]))

        perguntas_scroll = ctk.CTkScrollableFrame(body, fg_color="transparent", height=180)
        perguntas_scroll.pack(fill="x", pady=(0, SPACING["item_gap"]))
        self._perguntas_widgets = {}

        def renderizar_perguntas(nome_formulario: str):
            for w in perguntas_scroll.winfo_children():
                w.destroy()
            self._perguntas_widgets.clear()
            formulario = next(
                (
                    f
                    for f in self._formularios
                    if f.get("name") == nome_formulario and f.get("is_active")
                ),
                None,
            )
            if not formulario:
                return
            questions = formulario.get("questions", [])
            if isinstance(questions, str):
                try:
                    questions = json.loads(questions)
                except json.JSONDecodeError:
                    questions = []
            for q in questions:
                qid = q.get("id") or q.get("text", "pergunta")
                qtext = q.get("text", "Pergunta")
                qtype = q.get("type", "text")
                wrap = ctk.CTkFrame(perguntas_scroll, fg_color="transparent")
                wrap.pack(fill="x", pady=(0, SPACING["item_gap"]))
                ctk.CTkLabel(
                    wrap,
                    text=qtext,
                    font=themed_font("body"),
                    text_color=THEME["text_secondary"],
                    anchor="w",
                ).pack(fill="x", pady=(0, SPACING["label_gap"]))
                box = ctk.CTkFrame(
                    wrap,
                    fg_color=THEME["input_bg"],
                    corner_radius=RADIUS["input"],
                    border_width=1,
                    border_color=THEME["input_border"],
                )
                box.pack(fill="x")
                if qtype == "select":
                    opts = q.get("options", [])
                    if isinstance(opts, str):
                        opts = [opts]
                    widget = ctk.CTkOptionMenu(
                        box,
                        values=opts if opts else ["Opção 1"],
                        fg_color=THEME["input_bg"],
                        button_color=THEME["primary"],
                        button_hover_color=THEME["primary_hover"],
                        text_color=THEME["text"],
                        dropdown_fg_color=THEME["surface"],
                        dropdown_text_color=THEME["text"],
                        height=36,
                        corner_radius=RADIUS["input"],
                        font=themed_font("body"),
                    )
                    widget.pack(fill="x", padx=SPACING["label_gap"], pady=SPACING["icon_gap"])
                elif qtype == "textarea":
                    widget = ctk.CTkTextbox(
                        box,
                        height=80,
                        corner_radius=RADIUS["input"],
                        border_width=0,
                        fg_color=THEME["input_bg"],
                        text_color=THEME["text"],
                        font=themed_font("body"),
                    )
                    widget.pack(fill="x", padx=SPACING["label_gap"], pady=SPACING["icon_gap"])
                else:
                    widget = ctk.CTkEntry(
                        box,
                        placeholder_text="Resposta...",
                        fg_color=THEME["input_bg"],
                        border_width=0,
                        text_color=THEME["text"],
                        placeholder_text_color=THEME["text_muted"],
                        font=themed_font("body"),
                        height=36,
                    )
                    widget.pack(fill="x", padx=SPACING["label_gap"], pady=SPACING["icon_gap"])
                self._perguntas_widgets[qid] = widget

        om_formulario.configure(command=lambda selected: renderizar_perguntas(selected))

        en_obs = ctk.CTkTextbox(
            body,
            height=80,
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["input_border"],
            fg_color=THEME["input_bg"],
            text_color=THEME["text"],
            font=themed_font("body"),
        )
        en_obs.pack(fill="x")
        en_obs.insert("0.0", "Observações...")

        # Rodapé
        Divider(modal).pack(fill="x")
        footer = ctk.CTkFrame(modal, fg_color="transparent", height=62)
        footer.pack(fill="x", padx=SPACING["card_pad"])
        footer.pack_propagate(False)

        GhostButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            height=38,
            width=110,
            corner_radius=RADIUS["button"],
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=SPACING["item_gap"])

        def salvar():
            estudante_key = om_estudante.get()
            formulario_nome = om_formulario.get()
            nome = estudantes_map.get(estudante_key, "")
            student_id = nome if isinstance(nome, int) else None
            if not student_id:
                self._show_error("Selecione um estudante válido.", title="Atenção")
                return
            form_id = formularios_map.get(formulario_nome)
            if not form_id:
                self._show_error("Selecione um formulário válido.", title="Atenção")
                return
            data = en_data.get().strip()
            responses = {}
            for qid, widget in self._perguntas_widgets.items():
                if isinstance(widget, ctk.CTkTextbox):
                    responses[qid] = widget.get("0.0", "end").strip()
                elif isinstance(widget, ctk.CTkOptionMenu):
                    responses[qid] = widget.get()
                else:
                    responses[qid] = widget.get().strip()
            novo = {
                "student_id": student_id,
                "form_id": form_id,
                "scheduled_date": data or "—",
                "priority": om_prioridade.get(),
                "status": om_status.get(),
                "responses": json.dumps(responses),
                "observations": en_obs.get("0.0", "end").strip(),
            }

            def _task():
                return self.servico_triagem.criar_triagem(novo)

            def _on_ok(_):
                modal.destroy()
                self._carregar_triagens()

            def _on_err(e):
                self._show_error(f"Falha ao salvar triagem.\n{e}")

            AsyncRunner.run(task=_task, on_success=_on_ok, on_error=_on_err, widget_ref=self)

        PrimaryButton(
            footer,
            text=f"{ICONS['save']}  Salvar",
            command=salvar,
            height=38,
            width=140,
            corner_radius=RADIUS["button"],
        ).pack(side="right", pady=SPACING["item_gap"])

    # •••••••••••••••••••••••••••••••••••••••••••
    #  MODAL: Editar Triagem
    # •••••••••••••••••••••••••••••••••••••••••••
    def _modal_editar_triagem(self, item: dict):
        triagem_id = item.get("id")
        modal = BaseModal(self, title="Editar Triagem", width=560, height=720)
        modal.configure(fg_color=THEME["surface_elevated"])

        banner = ctk.CTkFrame(
            modal, fg_color=THEME["primary_soft"], corner_radius=RADIUS["none"], height=68
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)
        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=SPACING["card_pad"])

        ib = ctk.CTkFrame(
            bi, width=40, height=40, corner_radius=RADIUS["button"], fg_color=THEME["primary"]
        )
        ib.pack(side="left", padx=(0, SPACING["icon_gap"]))
        ib.pack_propagate(False)
        IconLabel(
            ib,
            icon=ICONS["chart"],
            size=22,
            fg_color="transparent",
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(
            ts, text="Editar Triagem", font=themed_font("h3", "bold"), text_color=THEME["primary"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            ts,
            text="Atualize os dados da triagem",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["section_gap"])

        estudantes_map = {
            f"{e.get('nome', '')} ({e.get('id_aluno', '')})": e.get("id_aluno")
            for e in self._estudantes
        }
        estudantes_lista = (
            sorted(estudantes_map.keys()) if estudantes_map else ["Nenhum estudante encontrado"]
        )

        om_estudante = ctk.CTkOptionMenu(
            body,
            values=estudantes_lista,
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        om_estudante.pack(fill="x", pady=(0, SPACING["item_gap"]))

        formularios_map = {
            f.get("name", ""): f.get("id") for f in self._formularios if f.get("is_active")
        }
        formularios_lista = (
            sorted(formularios_map.keys()) if formularios_map else ["Nenhum formulário ativo"]
        )

        om_formulario = ctk.CTkOptionMenu(
            body,
            values=formularios_lista,
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        om_formulario.pack(fill="x", pady=(0, SPACING["item_gap"]))

        def field(parent, label, placeholder, icon=""):
            wrap = ctk.CTkFrame(parent, fg_color="transparent")
            wrap.pack(fill="x", pady=(0, SPACING["item_gap"]))
            ctk.CTkLabel(
                wrap,
                text=label,
                font=themed_font("body"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).pack(fill="x", pady=(0, SPACING["label_gap"]))
            box = ctk.CTkFrame(
                wrap,
                fg_color=THEME["input_bg"],
                corner_radius=RADIUS["input"],
                border_width=1,
                border_color=THEME["input_border"],
            )
            box.pack(fill="x")
            if icon:
                ctk.CTkLabel(
                    box,
                    text=icon,
                    font=themed_font("body"),
                    text_color=THEME["text_muted"],
                    width=32,
                ).pack(side="left", padx=(SPACING["icon_gap"], 0))
            en = ctk.CTkEntry(
                box,
                placeholder_text=placeholder,
                fg_color=THEME["input_bg"],
                border_width=0,
                text_color=THEME["text"],
                placeholder_text_color=THEME["text_muted"],
                font=themed_font("body"),
                height=40,
            )
            en.pack(
                side="left", fill="x", expand=True, padx=(SPACING["label_gap"], SPACING["icon_gap"])
            )
            en.bind("<FocusIn>", lambda e: box.configure(border_color=THEME["input_border_focus"]))
            en.bind("<FocusOut>", lambda e: box.configure(border_color=THEME["input_border"]))
            return en

        en_data = field(body, "Data da Triagem", "dd/mm/aaaa", ICONS["calendar"])
        en_data.insert(0, item.get("date", ""))

        opt_style = dict(
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, SPACING["item_gap"]))
        row2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            row2, text="Prioridade", font=themed_font("body"), text_color=THEME["text_secondary"]
        ).grid(row=0, column=0, sticky="w", padx=(0, SPACING["icon_gap"] // 2))
        ctk.CTkLabel(
            row2, text="Status", font=themed_font("body"), text_color=THEME["text_secondary"]
        ).grid(row=0, column=1, sticky="w", padx=(SPACING["icon_gap"] // 2, 0))

        om_prioridade = ctk.CTkOptionMenu(
            row2, values=["Baixa", "Média", "Alta", "Urgente"], **opt_style
        )
        om_prioridade.set(item.get("priority", "Média"))
        om_prioridade.grid(row=1, column=0, sticky="ew", padx=(0, SPACING["icon_gap"] // 2))

        om_status = ctk.CTkOptionMenu(
            row2, values=["Pendente", "Em Andamento", "Concluída", "Cancelada"], **opt_style
        )
        om_status.set(item.get("status", "Pendente"))
        om_status.grid(row=1, column=1, sticky="ew", padx=(SPACING["icon_gap"] // 2, 0))

        lbl_perguntas = ctk.CTkLabel(
            body,
            text="Perguntas do Formulário",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        )
        lbl_perguntas.pack(anchor="w", pady=(SPACING["item_gap"], SPACING["label_gap"]))

        perguntas_scroll = ctk.CTkScrollableFrame(body, fg_color="transparent", height=180)
        perguntas_scroll.pack(fill="x", pady=(0, SPACING["item_gap"]))
        self._perguntas_widgets = {}

        existing_responses = {}
        if item.get("responses") and isinstance(item["responses"], dict):
            existing_responses = item["responses"]

        def renderizar_perguntas_edicao(nome_formulario: str):
            for w in perguntas_scroll.winfo_children():
                w.destroy()
            self._perguntas_widgets.clear()
            formulario = next(
                (
                    f
                    for f in self._formularios
                    if f.get("name") == nome_formulario and f.get("is_active")
                ),
                None,
            )
            if not formulario:
                return
            questions = formulario.get("questions", [])
            if isinstance(questions, str):
                try:
                    questions = json.loads(questions)
                except json.JSONDecodeError:
                    questions = []
            for q in questions:
                qid = q.get("id") or q.get("text", "pergunta")
                qtext = q.get("text", "Pergunta")
                qtype = q.get("type", "text")
                wrap = ctk.CTkFrame(perguntas_scroll, fg_color="transparent")
                wrap.pack(fill="x", pady=(0, SPACING["item_gap"]))
                ctk.CTkLabel(
                    wrap,
                    text=qtext,
                    font=themed_font("body"),
                    text_color=THEME["text_secondary"],
                    anchor="w",
                ).pack(fill="x", pady=(0, SPACING["label_gap"]))
                box = ctk.CTkFrame(
                    wrap,
                    fg_color=THEME["input_bg"],
                    corner_radius=RADIUS["input"],
                    border_width=1,
                    border_color=THEME["input_border"],
                )
                box.pack(fill="x")
                valor_existente = existing_responses.get(qid, "")
                if qtype == "select":
                    opts = q.get("options", [])
                    if isinstance(opts, str):
                        opts = [opts]
                    widget = ctk.CTkOptionMenu(
                        box,
                        values=opts if opts else ["Opção 1"],
                        fg_color=THEME["input_bg"],
                        button_color=THEME["primary"],
                        button_hover_color=THEME["primary_hover"],
                        text_color=THEME["text"],
                        dropdown_fg_color=THEME["surface"],
                        dropdown_text_color=THEME["text"],
                        height=36,
                        corner_radius=RADIUS["input"],
                        font=themed_font("body"),
                    )
                    widget.pack(fill="x", padx=SPACING["label_gap"], pady=SPACING["icon_gap"])
                    if valor_existente in opts:
                        widget.set(valor_existente)
                elif qtype == "textarea":
                    widget = ctk.CTkTextbox(
                        box,
                        height=80,
                        corner_radius=RADIUS["input"],
                        border_width=0,
                        fg_color=THEME["input_bg"],
                        text_color=THEME["text"],
                        font=themed_font("body"),
                    )
                    widget.pack(fill="x", padx=SPACING["label_gap"], pady=SPACING["icon_gap"])
                    if valor_existente:
                        widget.insert("0.0", valor_existente)
                else:
                    widget = ctk.CTkEntry(
                        box,
                        placeholder_text="Resposta...",
                        fg_color=THEME["input_bg"],
                        border_width=0,
                        text_color=THEME["text"],
                        placeholder_text_color=THEME["text_muted"],
                        font=themed_font("body"),
                        height=36,
                    )
                    widget.pack(fill="x", padx=SPACING["label_gap"], pady=SPACING["icon_gap"])
                    if valor_existente:
                        widget.insert(0, valor_existente)
                self._perguntas_widgets[qid] = widget

        om_formulario.configure(command=lambda selected: renderizar_perguntas_edicao(selected))

        en_obs = ctk.CTkTextbox(
            body,
            height=80,
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["input_border"],
            fg_color=THEME["input_bg"],
            text_color=THEME["text"],
            font=themed_font("body"),
        )
        en_obs.pack(fill="x")
        if item.get("observations"):
            en_obs.insert("0.0", item.get("observations"))

        # Rodapé
        Divider(modal).pack(fill="x")
        footer = ctk.CTkFrame(modal, fg_color="transparent", height=62)
        footer.pack(fill="x", padx=SPACING["card_pad"])
        footer.pack_propagate(False)

        GhostButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            height=38,
            width=110,
            corner_radius=RADIUS["button"],
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=SPACING["item_gap"])

        def salvar():
            estudante_key = om_estudante.get()
            formulario_nome = om_formulario.get()
            student_id = estudantes_map.get(estudante_key)
            if not student_id:
                self._show_error("Selecione um estudante válido.", title="Atenção")
                return
            form_id = formularios_map.get(formulario_nome)
            if not form_id:
                self._show_error("Selecione um formulário válido.", title="Atenção")
                return
            data = en_data.get().strip()
            responses = {}
            for qid, widget in self._perguntas_widgets.items():
                if isinstance(widget, ctk.CTkTextbox):
                    responses[qid] = widget.get("0.0", "end").strip()
                elif isinstance(widget, ctk.CTkOptionMenu):
                    responses[qid] = widget.get()
                else:
                    responses[qid] = widget.get().strip()
            dados = {
                "student_id": student_id,
                "form_id": form_id,
                "scheduled_date": data or "—",
                "priority": om_prioridade.get(),
                "status": om_status.get(),
                "responses": json.dumps(responses),
                "observations": en_obs.get("0.0", "end").strip(),
            }

            def _task():
                return self.servico_triagem.atualizar_triagem(triagem_id, dados)

            def _on_ok(_):
                modal.destroy()
                self._carregar_triagens()

            def _on_err(e):
                self._show_error(f"Falha ao atualizar triagem.\n{e}")

            AsyncRunner.run(task=_task, on_success=_on_ok, on_error=_on_err, widget_ref=self)

        PrimaryButton(
            footer,
            text=f"{ICONS['save']}  Salvar",
            command=salvar,
            height=38,
            width=140,
            corner_radius=RADIUS["button"],
        ).pack(side="right", pady=SPACING["item_gap"])

    def _carregar_triagens(self):
        """Carrega a lista de triagens via controller."""

        def fetch():
            return self.servico_triagem.listar_triagens()

        def on_success(result):
            if not self.winfo_exists():
                return
            triagens = []
            if result.get("success"):
                data = result.get("data", [])
                if isinstance(data, list):
                    triagens = [
                        {
                            "id": t.get("id"),
                            "student": t.get("student_name", "Estudante"),
                            "form_name": t.get("form_name", "—"),
                            "date": t.get("scheduled_date", "—"),
                            "priority": t.get("priority", "Média"),
                            "status": t.get("status", "Pendente"),
                            "responses": t.get("responses"),
                            "observations": t.get("observations"),
                        }
                        for t in data
                    ]
            self.data_master = triagens
            self._atualizar_kpis(triagens)
            self.renderizar_tabela(triagens)

        def on_error(exc):
            self._show_error(f"Falha ao carregar triagens.\n{exc}")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _show_error(self, message: str, title: str = "Não foi possível concluir") -> None:
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

    def _confirmar_callback(self, modal: ctk.CTkToplevel, resultado: dict) -> None:
        resultado["ok"] = True
        modal.destroy()

    def _carregar_estudantes(self):
        def fetch():
            return self.servico_estudantes.listar_estudantes()

        def on_success(result):
            if not self.winfo_exists():
                return
            if result.get("success"):
                self._estudantes = result.get("data", [])

        def on_error(exc):
            pass

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _carregar_formularios(self):
        def fetch():
            return self.servico_triagem.listar_formularios()

        def on_success(result):
            if not self.winfo_exists():
                return
            if result.get("success"):
                self._formularios = result.get("data", [])

        def on_error(exc):
            pass

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _modal_detalhe(self, item: dict):
        modal = BaseModal(self, title="Detalhe da Triagem", width=420, height=340)
        modal.configure(fg_color=THEME["surface_elevated"])

        nome = item["student"]
        av_color = get_avatar_color(nome)

        # Banner
        banner = ctk.CTkFrame(
            modal, fg_color=THEME["primary_soft"], corner_radius=RADIUS["none"], height=80
        )
        banner.pack(fill="x")
        banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=SPACING["card_pad"])

        av = Avatar(bi, initials=nome[:2], size=46, color=av_color)
        av.pack(side="left", padx=(0, SPACING["icon_gap"]))

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(ts, text=nome, font=themed_font("h4", "bold"), text_color=THEME["text"]).pack(
            anchor="w"
        )
        ctk.CTkLabel(
            ts,
            text=f"Triagem registrada em {item['date']}",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["item_gap"])

        def info_row(label, value, color=None):
            r = ctk.CTkFrame(body, fg_color=THEME["bg_alt"], corner_radius=RADIUS["button"])
            r.pack(fill="x", pady=SPACING["label_gap"])
            ctk.CTkLabel(
                r,
                text=label,
                width=120,
                font=themed_font("body"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).pack(side="left", padx=SPACING["card_pad"], pady=SPACING["icon_gap"])
            ctk.CTkLabel(
                r, text=value, font=themed_font("body", "bold"), text_color=color or THEME["text"]
            ).pack(side="left")

        p_color, _ = _PRIORITY_CFG.get(item["priority"], (THEME["text_secondary"], ""))
        s_color, _ = _STATUS_CFG.get(item["status"], (THEME["text_secondary"], ""))

        info_row("Prioridade", item["priority"], p_color)
        info_row("Status", item["status"], s_color)
        info_row("Data", item["date"])
        info_row("Formulário", item.get("form_name", "—"))

        PrimaryButton(
            modal,
            text="Fechar",
            command=modal.destroy,
            height=38,
            corner_radius=RADIUS["button"],
        ).pack(pady=(0, SPACING["item_gap"]))

    def _modal_listar_formularios(self):
        modal = BaseModal(self, title="Formulários de Triagem", width=520, height=420)
        modal.configure(fg_color=THEME["surface_elevated"])

        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["section_gap"])

        if not self._formularios:
            ctk.CTkLabel(
                body,
                text="Nenhum formulário disponível.",
                font=themed_font("body"),
                text_color=THEME["text_muted"],
            ).pack(pady=SPACING["section_gap"])
        else:
            scroll = ctk.CTkScrollableFrame(body, fg_color="transparent")
            scroll.pack(fill="both", expand=True)
            for f in self._formularios:
                if not f.get("is_active"):
                    continue
                card = Card(scroll, title=f.get("name", "Sem nome"), auto_body=False)
                card.pack(fill="x", pady=SPACING["icon_gap"])
                desc = f.get("description") or "Sem descrição"
                ctk.CTkLabel(
                    card,
                    text=desc,
                    font=themed_font("body_sm"),
                    text_color=THEME["text_secondary"],
                    anchor="w",
                ).pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["item_gap"]))

        PrimaryButton(
            modal,
            text="Fechar",
            command=modal.destroy,
            height=38,
            corner_radius=RADIUS["button"],
        ).pack(pady=(0, SPACING["item_gap"]))

    # Aliases para callbacks da tabela
    def _ver_detalhe(self, item: dict):
        self._modal_detalhe(item)

    def _editar(self, item: dict):
        self._modal_editar_triagem(item)

    # Aliases legados
    def criar_cabecalho(self):
        pass

    def criar_cards_metricas(self):
        pass

    def criar_filtros(self):
        pass

    def criar_area_conteudo(self):
        pass

    def get_priority_color(self, p: str) -> str:
        return _PRIORITY_CFG.get(p, (THEME["text_secondary"], ""))[0]

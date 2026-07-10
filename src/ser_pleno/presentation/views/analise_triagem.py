import customtkinter as ctk

from ser_pleno.ui.theme import (
    THEME, SPACING, RADIUS, TYPO, FONT_FAMILY,
    font, themed_font, mono_font,
)
from ser_pleno.ui.theme_extensions import extend_theme
from ser_pleno.presentation.components.ui_components import (
    Card, PrimaryButton, GhostButton, Divider, KPICard, BaseModal, EmptyState
)
from ser_pleno.presentation.components.icons import IconLabel, ICONS
from ser_pleno.utils.avatar_utils import get_avatar_color
from ser_pleno.application.controllers.analise_triagem import AnaliseTriagemController
from ser_pleno.utils.async_runner import AsyncRunner
from tkinter import messagebox

# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Design tokens —“ mapeamentos semânticos específicos da triagem
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

TRI_TOKENS = extend_theme(THEME, {
    "kpi_size": "md",
})

_PRIORITY_CFG = {
    "Urgente": (THEME["critico"],       THEME["critico_soft"]),
    "Alta":    (THEME["alto"],          THEME["alto_soft"]),
    "Média":   (THEME["medio"],         THEME["medio_soft"]),
    "Baixa":   (THEME["normal"],        THEME["normal_soft"]),
}
_STATUS_CFG = {
    "Pendente":     (THEME["warning"],     THEME["warning_soft"]),
    "Em Andamento": (THEME["info"],        THEME["info_soft"]),
    "Concluída":    (THEME["success"],     THEME["success_soft"]),
    "Cancelada":    (THEME["text_muted"],  THEME["bg_alt"]),
}
_COL_HEADERS = ["Estudante", "Data", "Prioridade", "Status", "Ações"]
_COL_WEIGHTS = [3, 2, 2, 2, 1]


# Helpers
# Avatares usam utils.avatar_utils.get_avatar_color centralizado.


def _chip(parent, text: str, color: str, soft: str) -> ctk.CTkFrame:
    f = ctk.CTkFrame(parent, fg_color=soft, corner_radius=RADIUS["xs"])
    ctk.CTkLabel(f, text=text,
                 font=themed_font("body_sm", "bold"),
                 text_color=color).pack(padx=SPACING["icon_gap"], pady=SPACING["label_gap"] // 2)
    return f


def _avatar(parent, initials: str, color: str, size: int = 36) -> ctk.CTkFrame:
    av = ctk.CTkFrame(parent, width=size, height=size,
                      corner_radius=size // 2, fg_color=color)
    av.pack_propagate(False)
    ctk.CTkLabel(av, text=initials[:2].upper(),
                 font=font(size=max(10, size // 3), weight="bold", family=FONT_FAMILY),
                 text_color=THEME["text_on_primary"]).place(relx=0.5, rely=0.5, anchor="center")
    return av




# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Campo de entrada leve
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class _DateField(ctk.CTkFrame):
    def __init__(self, parent, placeholder: str):
        super().__init__(parent, fg_color=THEME["input_bg"],
                         corner_radius=RADIUS["input"], border_width=1,
                         border_color=THEME["input_border"])
        IconLabel(
            self, icon=ICONS["calendar"], size=20,
            fg_color="transparent", text_color=THEME["text_secondary"],
        ).pack(side="left", padx=(SPACING["icon_gap"], 0))
        self.entry = ctk.CTkEntry(
            self, placeholder_text=placeholder,
            fg_color=THEME["input_bg"], border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=themed_font("body"), height=36,
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(SPACING["label_gap"], SPACING["icon_gap"]))
        self.entry.bind("<FocusIn>",  lambda e: self.configure(border_color=THEME["input_border_focus"]))
        self.entry.bind("<FocusOut>", lambda e: self.configure(border_color=THEME["input_border"]))

    def get(self) -> str:
        return self.entry.get()

    def delete(self, a, b):
        self.entry.delete(a, b)


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  AnaliseTriagemFrame
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class AnaliseTriagemFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["page_bg"],
                         scrollbar_button_color=THEME["primary_medium"],
                         scrollbar_button_hover_color=THEME["primary"])
        self.controller = controller
        self.controller_triagem = AnaliseTriagemController()
        self.data_master = []

        self._criar_toolbar_acoes()
        self._criar_kpis()
        self._criar_filtros()
        self._criar_tabela()
        self._carregar_triagens()

    # ••••••••••••••••••••••••••••••••••••••••••
    #  CABEÇALHO
    # ••••••••••••••••••••••••••••••••••••••••••
    def _criar_toolbar_acoes(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], SPACING["label_gap"]))

        PrimaryButton(
            bar, text=f"{ICONS['add']}  Nova Triagem",
            command=self.abrir_nova_triagem,
            height=40, corner_radius=RADIUS["button"], width=160,
        ).pack(side="right")

    # ••••••••••••••••••••••••••••••••••
    #  KPIs
    # ••••••••••••••••••••••••••••••••••••••••••
    def _criar_kpis(self):
        total     = len(self.data_master)
        pendentes = sum(1 for d in self.data_master if d["status"] == "Pendente")
        concluidas= sum(1 for d in self.data_master if d["status"] == "Concluída")
        alta_p    = sum(1 for d in self.data_master
                        if d["priority"] in ("Alta", "Urgente"))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

        kpis = [
            ("Total de Triagens", str(total),     ICONS["chart"], THEME["kpi_blue"],  THEME["kpi_blue_soft"],  "Registros"),

            ("Pendentes",         str(pendentes),  ICONS["hourglass"], THEME["kpi_amber"], THEME["kpi_amber_soft"], "Aguardando"),

            ("Concluídas",        str(concluidas), ICONS["check"], THEME["kpi_green"], THEME["kpi_green_soft"], "Finalizadas"),

            ("Alta Prioridade",   str(alta_p),     f"{ICONS['bolt']} ", THEME["kpi_red"],   THEME["kpi_red_soft"],   "Urgente ou Alta"),
        ]
        self._kpi_widgets = []
        for i, (title, val, icon, accent, soft, sub) in enumerate(kpis):
            row.grid_columnconfigure(i, weight=1)
            card = KPICard(
                row, title=title, value=val, icon=icon,
                accent=accent, unit="", size=TRI_TOKENS.get("kpi_size", "md"),
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["icon_gap"] // 2)
            self._kpi_widgets.append(card._value_label if hasattr(card, "_value_label") else None)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  FILTROS
    # ••••••••••••••••••••••••••••••••••••••••••
    def _criar_filtros(self):
        card = Card(self)
        card.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))
        ctk.CTkLabel(hdr, text=f"{ICONS['search']}  Filtrar Triagens",
                     font=themed_font("body", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["card_pad"], pady=SPACING["item_gap"])
        for i in range(4):
            row.grid_columnconfigure(i, weight=1)

        opt_style = dict(
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            height=38, corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )

        self.filtro_status = ctk.CTkOptionMenu(
            row,
            values=["Todos", "Pendente", "Em Andamento", "Concluída", "Cancelada"],
            command=lambda _: self.aplicar_filtros(),
            **opt_style,
        )
        self.filtro_status.grid(row=0, column=0, sticky="ew", padx=(0, SPACING["icon_gap"] // 2))

        self.filtro_prioridade = ctk.CTkOptionMenu(
            row,
            values=["Todas", "Baixa", "Média", "Alta", "Urgente"],
            command=lambda _: self.aplicar_filtros(),
            **opt_style,
        )
        self.filtro_prioridade.grid(row=0, column=1, sticky="ew", padx=SPACING["icon_gap"] // 2)

        self.data_inicial = _DateField(row, "Data inicial  dd/mm/aaaa")
        self.data_inicial.grid(row=0, column=2, sticky="ew", padx=SPACING["icon_gap"] // 2)

        self.data_final = _DateField(row, "Data final  dd/mm/aaaa")
        self.data_final.grid(row=0, column=3, sticky="ew", padx=(SPACING["icon_gap"] // 2, 0))

        # Botões
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["item_gap"]))

        GhostButton(
            btn_row, text="Limpar filtros", command=self.limpar_filtros,
            height=34, corner_radius=RADIUS["button"],
            text_color=THEME["text_secondary"],
        ).pack(side="right", padx=(SPACING["icon_gap"], 0))

        PrimaryButton(
            btn_row, text="Aplicar filtros", command=self.aplicar_filtros,
            height=34, corner_radius=RADIUS["button"], width=140,
        ).pack(side="right")

    # ••••••••••••••••••••••••••••••••••••••••••
    #  TABELA
    # ••••••••••••••••••••••••••••••••••••••••••
    def _criar_tabela(self):
        card = Card(self)
        card.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(SPACING["section_gap"], SPACING["page_y"]))

        # Cabeçalho da tabela
        hdr_outer = ctk.CTkFrame(card, fg_color="transparent")
        hdr_outer.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))

        ctk.CTkLabel(hdr_outer, text="Lista de Triagens",
                     font=themed_font("body", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        self._lbl_count = ctk.CTkLabel(
            hdr_outer, text=f"{len(self.data_master)} registros",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"])
        self._lbl_count.pack(side="right")

        Divider(card).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))

        # Header de colunas
        col_hdr = ctk.CTkFrame(card, fg_color=THEME["bg_alt"],
                               corner_radius=RADIUS["none"], height=38)
        col_hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["label_gap"], 0))
        col_hdr.pack_propagate(False)
        col_hdr.grid_columnconfigure(list(range(len(_COL_HEADERS))),
                                     weight=1)
        for i, (h, w) in enumerate(zip(_COL_HEADERS, _COL_WEIGHTS)):
            col_hdr.grid_columnconfigure(i, weight=w)
            ctk.CTkLabel(col_hdr, text=h,
                         font=themed_font("body_sm", "bold"),
                         text_color=THEME["text_secondary"], anchor="w").grid(
                row=0, column=i, sticky="w", padx=(SPACING["card_pad"] if i == 0 else SPACING["icon_gap"], 0), pady=SPACING["icon_gap"])

        # Corpo scrollável
        self.lista_triagens = ctk.CTkScrollableFrame(
            card, fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.lista_triagens.pack(fill="both", expand=True,
                                 padx=SPACING["icon_gap"], pady=(SPACING["label_gap"], SPACING["icon_gap"]))

        self.renderizar_tabela(self.data_master)

    def renderizar_tabela(self, data_list: list):
        for w in self.lista_triagens.winfo_children():
            w.destroy()

        if hasattr(self, "_lbl_count"):
            self._lbl_count.configure(text=f"{len(data_list)} registro{'s' if len(data_list) != 1 else ''}")

        if not data_list:
            EmptyState(
                self.lista_triagens, icon=ICONS["empty"], title="Nenhuma triagem encontrada",
                subtitle=""
            ).pack(pady=SPACING["section_gap"])
            return

        for item in data_list:
            self._criar_row(item)

    def _criar_row(self, item: dict):
        row = ctk.CTkFrame(self.lista_triagens,
                           fg_color=THEME["row_bg"], corner_radius=RADIUS["button"])
        row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
        row.grid_columnconfigure(list(range(len(_COL_HEADERS))), weight=1)
        for i, w in enumerate(_COL_WEIGHTS):
            row.grid_columnconfigure(i, weight=w)

        row.bind("<Enter>",  lambda e, r=row: r.configure(fg_color=THEME["row_hover"]))
        row.bind("<Leave>",  lambda e, r=row: r.configure(fg_color=THEME["row_bg"]))

        nome     = item["student"]
        av_color = get_avatar_color(nome)

        # Col 0 —“ Estudante (avatar + nome)
        name_cell = ctk.CTkFrame(row, fg_color="transparent")
        name_cell.grid(row=0, column=0, sticky="w", padx=(SPACING["icon_gap"], 0), pady=SPACING["item_gap"])
        av = _avatar(name_cell, nome[:2], av_color, 34)
        av.pack(side="left", padx=(0, SPACING["icon_gap"]))
        ctk.CTkLabel(name_cell, text=nome,
                     font=themed_font("body", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        # Col 1 —“ Data
        ctk.CTkLabel(row, text=item["date"],
                     font=themed_font("body_sm"),
                     text_color=THEME["text_secondary"]).grid(
            row=0, column=1, sticky="w", padx=SPACING["icon_gap"])

        # Col 2 —“ Prioridade (chip)
        p_color, p_soft = _PRIORITY_CFG.get(item["priority"],
                                             (THEME["text_secondary"], THEME["divider"]))
        chip_p = _chip(row, item["priority"], p_color, p_soft)
        chip_p.grid(row=0, column=2, sticky="w", padx=SPACING["icon_gap"], pady=SPACING["item_gap"])

        # Col 3 —“ Status (chip)
        s_color, s_soft = _STATUS_CFG.get(item["status"],
                                            (THEME["text_secondary"], THEME["divider"]))
        chip_s = _chip(row, item["status"], s_color, s_soft)
        chip_s.grid(row=0, column=3, sticky="w", padx=SPACING["icon_gap"], pady=SPACING["item_gap"])

        # Col 4 —“ Ações
        acts = ctk.CTkFrame(row, fg_color="transparent")
        acts.grid(row=0, column=4, sticky="e", padx=(0, SPACING["icon_gap"]), pady=SPACING["icon_gap"])
        for icon, cmd, tip in [(ICONS["view"], lambda s=item: self._ver_detalhe(s), "Ver detalhe"),
                                (ICONS["edit"], lambda s=item: self._editar(s), "Editar"),
                                (ICONS["delete"], lambda s=item: self._excluir_triagem(s), "Excluir")]:
            GhostButton(
                acts, icon=icon, tooltip=tip, width=30, height=30,
                corner_radius=RADIUS["xs"],
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=cmd,
            ).pack(side="left", padx=SPACING["label_gap"] // 2)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Filtros
    # ••••••••••••••••••••••••••••••••••••••••••
    def aplicar_filtros(self):
        st = self.filtro_status.get()
        pr = self.filtro_prioridade.get()
        filtered = [
            d for d in self.data_master
            if (st == "Todos"  or d["status"]   == st) and
               (pr == "Todas"  or d["priority"] == pr)
        ]
        self.renderizar_tabela(filtered)

    def limpar_filtros(self):
        self.filtro_status.set("Todos")
        self.filtro_prioridade.set("Todas")
        self.data_inicial.delete(0, "end")
        self.data_final.delete(0, "end")
        self.renderizar_tabela(self.data_master)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Ações de linha
    # ••••••••••••••••••••••••••••••••••••••••••
    def _ver_detalhe(self, item: dict):
        self._modal_detalhe(item)

    def _editar(self, item: dict):
        self._modal_editar_triagem(item)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  MODAL: Nova Triagem
    # ••••••••••••••••••••••••••••••••••••••••••
    def abrir_nova_triagem(self):
        modal = BaseModal(self, title="Nova Triagem", width=520, height=580)
        modal.configure(fg_color=THEME["surface_elevated"])

        # Banner
        banner = ctk.CTkFrame(modal, fg_color=THEME["primary_soft"],
                              corner_radius=RADIUS["none"], height=68)
        banner.pack(fill="x"); banner.pack_propagate(False)
        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=SPACING["card_pad"])

        ib = ctk.CTkFrame(bi, width=40, height=40,
                          corner_radius=RADIUS["button"], fg_color=THEME["primary"])
        ib.pack(side="left", padx=(0, SPACING["icon_gap"])); ib.pack_propagate(False)
        IconLabel(
            ib, icon=ICONS["chart"], size=22,
            fg_color="transparent", text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(ts, text="Nova Triagem",
                     font=themed_font("h3", "bold"),
                     text_color=THEME["primary"]).pack(anchor="w")
        ctk.CTkLabel(ts, text="Preencha os dados da triagem",
                     font=themed_font("body_sm"),
                     text_color=THEME["text_secondary"]).pack(anchor="w")

        # Corpo
        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["section_gap"])

        def field(parent, label, placeholder, icon=""):
            wrap = ctk.CTkFrame(parent, fg_color="transparent")
            wrap.pack(fill="x", pady=(0, SPACING["item_gap"]))
            ctk.CTkLabel(wrap, text=label,
                         font=themed_font("body"),
                         text_color=THEME["text_secondary"], anchor="w").pack(fill="x", pady=(0, SPACING["label_gap"]))
            box = ctk.CTkFrame(wrap, fg_color=THEME["input_bg"],
                               corner_radius=RADIUS["input"], border_width=1,
                               border_color=THEME["input_border"])
            box.pack(fill="x")
            if icon:
                ctk.CTkLabel(box, text=icon,
                             font=themed_font("body"),
                             text_color=THEME["text_muted"],
                             width=32).pack(side="left", padx=(SPACING["icon_gap"], 0))
            en = ctk.CTkEntry(box, placeholder_text=placeholder,
                              fg_color=THEME["input_bg"], border_width=0,
                              text_color=THEME["text"],
                              placeholder_text_color=THEME["text_muted"],
                              font=themed_font("body"), height=40)
            en.pack(side="left", fill="x", expand=True, padx=(SPACING["label_gap"], SPACING["icon_gap"]))
            en.bind("<FocusIn>",  lambda e: box.configure(border_color=THEME["input_border_focus"]))
            en.bind("<FocusOut>", lambda e: box.configure(border_color=THEME["input_border"]))
            return en

        en_nome  = field(body, "Nome do Estudante", "Ex: Ana Silva", ICONS["view"])
        en_data  = field(body, "Data da Triagem",   "dd/mm/aaaa",   ICONS["calendar"])

        opt_style = dict(
            fg_color=THEME["primary_soft"], button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"], text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"], dropdown_text_color=THEME["text"],
            height=40, corner_radius=RADIUS["input"], font=themed_font("body"),
        )

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, SPACING["item_gap"]))
        row2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(row2, text="Prioridade",
                     font=themed_font("body"),
                     text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, SPACING["icon_gap"] // 2))
        ctk.CTkLabel(row2, text="Status",
                     font=themed_font("body"),
                     text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(SPACING["icon_gap"] // 2, 0))

        om_prioridade = ctk.CTkOptionMenu(
            row2, values=["Baixa", "Média", "Alta", "Urgente"], **opt_style)
        om_prioridade.grid(row=1, column=0, sticky="ew", padx=(0, SPACING["icon_gap"] // 2))

        om_status = ctk.CTkOptionMenu(
            row2, values=["Pendente", "Em Andamento", "Concluída", "Cancelada"],
            **opt_style)
        om_status.grid(row=1, column=1, sticky="ew", padx=(SPACING["icon_gap"] // 2, 0))

        en_obs = ctk.CTkTextbox(body, height=80, corner_radius=RADIUS["input"],
                                border_width=1, border_color=THEME["input_border"],
                                fg_color=THEME["input_bg"], text_color=THEME["text"],
                                font=themed_font("body"))
        en_obs.pack(fill="x")
        en_obs.insert("0.0", "Observações...")

        # Rodapé
        Divider(modal).pack(fill="x")
        footer = ctk.CTkFrame(modal, fg_color="transparent", height=62)
        footer.pack(fill="x", padx=SPACING["card_pad"]); footer.pack_propagate(False)

        GhostButton(
            footer, text="Cancelar", command=modal.destroy,
            height=38, width=110, corner_radius=RADIUS["button"],
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=SPACING["item_gap"])

        def salvar():
            nome = en_nome.get().strip()
            data = en_data.get().strip()
            if not nome:
                return
            novo = {
                "student":  nome,
                "date":     data or "—”",
                "priority": om_prioridade.get(),
                "status":   om_status.get(),
            }
            self.data_master.append(novo)
            modal.destroy()
            self.renderizar_tabela(self.data_master)

        PrimaryButton(
            footer, text=f"{ICONS['save']}  Salvar", command=salvar,
            height=38, width=140, corner_radius=RADIUS["button"],
        ).pack(side="right", pady=SPACING["item_gap"])

    # ••••••••••••••••••••••••••••••••••••••••••
    #  MODAL: Detalhe
    # ••••••••••••••••••••••••••••••••••••••••••
    def _modal_editar_triagem(self, item: dict):
        triagem_id = item.get("id")
        modal = BaseModal(self, title="Editar Triagem", width=520, height=580)
        modal.configure(fg_color=THEME["surface_elevated"])

        banner = ctk.CTkFrame(modal, fg_color=THEME["primary_soft"],
                              corner_radius=RADIUS["none"], height=68)
        banner.pack(fill="x"); banner.pack_propagate(False)
        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=SPACING["card_pad"])

        ib = ctk.CTkFrame(bi, width=40, height=40,
                          corner_radius=RADIUS["button"], fg_color=THEME["primary"])
        ib.pack(side="left", padx=(0, SPACING["icon_gap"])); ib.pack_propagate(False)
        IconLabel(
            ib, icon=ICONS["chart"], size=22,
            fg_color="transparent", text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(ts, text="Editar Triagem",
                     font=themed_font("h3", "bold"),
                     text_color=THEME["primary"]).pack(anchor="w")
        ctk.CTkLabel(ts, text="Atualize os dados da triagem",
                     font=themed_font("body_sm"),
                     text_color=THEME["text_secondary"]).pack(anchor="w")

        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["section_gap"])

        def field(parent, label, placeholder, icon=""):
            wrap = ctk.CTkFrame(parent, fg_color="transparent")
            wrap.pack(fill="x", pady=(0, SPACING["item_gap"]))
            ctk.CTkLabel(wrap, text=label,
                         font=themed_font("body"),
                         text_color=THEME["text_secondary"], anchor="w").pack(fill="x", pady=(0, SPACING["label_gap"]))
            box = ctk.CTkFrame(wrap, fg_color=THEME["input_bg"],
                               corner_radius=RADIUS["input"], border_width=1,
                               border_color=THEME["input_border"])
            box.pack(fill="x")
            if icon:
                ctk.CTkLabel(box, text=icon,
                             font=themed_font("body"),
                             text_color=THEME["text_muted"],
                             width=32).pack(side="left", padx=(SPACING["icon_gap"], 0))
            en = ctk.CTkEntry(box, placeholder_text=placeholder,
                              fg_color=THEME["input_bg"], border_width=0,
                              text_color=THEME["text"],
                              placeholder_text_color=THEME["text_muted"],
                              font=themed_font("body"), height=40)
            en.pack(side="left", fill="x", expand=True, padx=(SPACING["label_gap"], SPACING["icon_gap"]))
            en.bind("<FocusIn>",  lambda e: box.configure(border_color=THEME["input_border_focus"]))
            en.bind("<FocusOut>", lambda e: box.configure(border_color=THEME["input_border"]))
            return en

        en_nome  = field(body, "Nome do Estudante", "Ex: Ana Silva", ICONS["view"])
        en_nome.insert(0, item.get("student", ""))
        en_data  = field(body, "Data da Triagem", "dd/mm/aaaa", ICONS["calendar"])
        en_data.insert(0, item.get("date", ""))

        opt_style = dict(
            fg_color=THEME["primary_soft"], button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"], text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"], dropdown_text_color=THEME["text"],
            height=40, corner_radius=RADIUS["input"], font=themed_font("body"),
        )

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, SPACING["item_gap"]))
        row2.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(row2, text="Prioridade",
                     font=themed_font("body"),
                     text_color=THEME["text_secondary"]).grid(row=0, column=0, sticky="w", padx=(0, SPACING["icon_gap"] // 2))
        ctk.CTkLabel(row2, text="Status",
                     font=themed_font("body"),
                     text_color=THEME["text_secondary"]).grid(row=0, column=1, sticky="w", padx=(SPACING["icon_gap"] // 2, 0))

        om_prioridade = ctk.CTkOptionMenu(
            row2, values=["Baixa", "Média", "Alta", "Urgente"], **opt_style)
        om_prioridade.set(item.get("priority", "Média"))
        om_prioridade.grid(row=1, column=0, sticky="ew", padx=(0, SPACING["icon_gap"] // 2))

        om_status = ctk.CTkOptionMenu(
            row2, values=["Pendente", "Em Andamento", "Concluída", "Cancelada"],
            **opt_style)
        om_status.set(item.get("status", "Pendente"))
        om_status.grid(row=1, column=1, sticky="ew", padx=(SPACING["icon_gap"] // 2, 0))

        en_obs = ctk.CTkTextbox(body, height=80, corner_radius=RADIUS["input"],
                                border_width=1, border_color=THEME["input_border"],
                                fg_color=THEME["input_bg"], text_color=THEME["text"],
                                font=themed_font("body"))
        en_obs.pack(fill="x")

        # Rodapé
        Divider(modal).pack(fill="x")
        footer = ctk.CTkFrame(modal, fg_color="transparent", height=62)
        footer.pack(fill="x", padx=SPACING["card_pad"]); footer.pack_propagate(False)

        GhostButton(
            footer, text="Cancelar", command=modal.destroy,
            height=38, width=110, corner_radius=RADIUS["button"],
            text_color=THEME["text_secondary"],
        ).pack(side="left", pady=SPACING["item_gap"])

        def salvar():
            nome = en_nome.get().strip()
            data = en_data.get().strip()
            if not nome:
                return
            dados = {
                "student_name": nome,
                "scheduled_date": data or "—",
                "priority": om_prioridade.get(),
                "status": om_status.get(),
            }
            def _task():
                return self.controller_triagem.atualizar_triagem(triagem_id, dados)
            def _on_ok(_):
                modal.destroy()
                self._carregar_triagens()
            def _on_err(e):
                messagebox.showerror("Erro", f"Falha ao atualizar triagem.\n{e}")
            AsyncRunner.run(task=_task, on_success=_on_ok, on_error=_on_err, widget_ref=self)

        PrimaryButton(
            footer, text=f"{ICONS['save']}  Salvar", command=salvar,
            height=38, width=140, corner_radius=RADIUS["button"],
        ).pack(side="right", pady=SPACING["item_gap"])

    def _carregar_triagens(self):
        """Carrega a lista de triagens via controller."""
        def fetch():
            return self.controller_triagem.listar_triagens()

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
                            "date": t.get("scheduled_date", "—"),
                            "priority": t.get("priority", "Média"),
                            "status": t.get("status", "Pendente"),
                        }
                        for t in data
                    ]
            self.data_master = triagens
            self.renderizar_tabela(triagens)

        def on_error(exc):
            messagebox.showerror("Erro", f"Falha ao carregar triagens.\n{exc}")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _modal_detalhe(self, item: dict):
        modal = BaseModal(self, title="Detalhe da Triagem", width=420, height=340)
        modal.configure(fg_color=THEME["surface_elevated"])

        nome     = item["student"]
        av_color = get_avatar_color(nome)

        # Banner
        banner = ctk.CTkFrame(modal, fg_color=THEME["primary_soft"],
                              corner_radius=RADIUS["none"], height=80)
        banner.pack(fill="x"); banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=SPACING["card_pad"])

        av = _avatar(bi, nome[:2], av_color, 46)
        av.pack(side="left", padx=(0, SPACING["icon_gap"]))

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(ts, text=nome,
                     font=themed_font("h4", "bold"),
                     text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(ts, text=f"Triagem registrada em {item['date']}",
                     font=themed_font("body_sm"),
                     text_color=THEME["text_secondary"]).pack(anchor="w")

        body = ctk.CTkFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["item_gap"])

        def info_row(label, value, color=None):
            r = ctk.CTkFrame(body, fg_color=THEME["bg_alt"], corner_radius=RADIUS["button"])
            r.pack(fill="x", pady=SPACING["label_gap"])
            ctk.CTkLabel(r, text=label, width=120,
                         font=themed_font("body"),
                         text_color=THEME["text_secondary"], anchor="w").pack(
                side="left", padx=SPACING["card_pad"], pady=SPACING["icon_gap"])
            ctk.CTkLabel(r, text=value,
                         font=themed_font("body", "bold"),
                         text_color=color or THEME["text"]).pack(side="left")

        p_color, _ = _PRIORITY_CFG.get(item["priority"], (THEME["text_secondary"], ""))
        s_color, _ = _STATUS_CFG.get(item["status"],     (THEME["text_secondary"], ""))

        info_row("Prioridade", item["priority"], p_color)
        info_row("Status",     item["status"],   s_color)
        info_row("Data",       item["date"])

        PrimaryButton(modal, text="Fechar", command=modal.destroy,
                      height=38, corner_radius=RADIUS["button"],
        ).pack(pady=(0, SPACING["item_gap"]))

    # Aliases legados
    def criar_cabecalho(self):       pass
    def criar_cards_metricas(self):  pass
    def criar_filtros(self):         pass
    def criar_area_conteudo(self):   pass

    def get_priority_color(self, p: str) -> str:
        return _PRIORITY_CFG.get(p, (THEME["text_secondary"], ""))[0]



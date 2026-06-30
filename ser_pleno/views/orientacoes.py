import logging
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import Any

from utils.async_runner import AsyncRunner
from services.orientacoes import servico_orientacoes
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from ui_theme_extensions import extend_theme

logger = logging.getLogger("apps.desktop")


# ══════════════════════════════════════════════════════════════════════════════
#  Design tokens — herdando do THEME global
# ══════════════════════════════════════════════════════════════════════════════
O = extend_theme(THEME, {
    "card_radius":  RADIUS["card"],
    "danger_hover": "#B91C1C",
    "text_light":   "#9CA3AF",
    "input_border": "#E5E7EB",
    "sidebar_bg":   "#FFFFFF",
    "sidebar_border": "#E5E7EB",
    "student_bg":   "#FAFAFA",
    "card_border":  THEME["border"],
    "card_bg":      THEME["surface"],
})

_TEMA_DEFAULT = ("#4F46E5", "#EEF2FF")


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _av_color(name: str) -> str:
    return O["av_colors"][sum(ord(c) for c in name) % len(O["av_colors"])]


def _card(parent, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(parent, fg_color=O["card_bg"],
                        corner_radius=O["card_radius"],
                        border_width=1, border_color=O["card_border"], **kw)


def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=O["divider"]).pack(fill="x")


def _avatar(parent, initials: str, color: str, size: int = 38) -> ctk.CTkFrame:
    av = ctk.CTkFrame(parent, width=size, height=size,
                      corner_radius=size // 2, fg_color=color)
    av.pack_propagate(False)
    ctk.CTkLabel(av, text=initials[:2].upper(),
                 font=font(size=size // 3, weight="bold"),
                 text_color="#FFFFFF").place(relx=0.5, rely=0.5, anchor="center")
    return av


def _chip(parent, text: str, tema: str = "") -> ctk.CTkFrame:
    color, soft = O["temas"].get(tema, _TEMA_DEFAULT)
    f = ctk.CTkFrame(parent, fg_color=soft, corner_radius=7)
    ctk.CTkLabel(f, text=text,
                 font=font(size=11, weight="bold"),
                 text_color=color).pack(padx=9, pady=3)
    return f


# ══════════════════════════════════════════════════════════════════════════════
#  FormField
# ══════════════════════════════════════════════════════════════════════════════
class FormField(ctk.CTkFrame):
    def __init__(self, parent, label: str, placeholder: str = "",
                 icon: str = "", password: bool = False,
                 initial: str = "", multiline: bool = False,
                 height: int | None = None, values: list[str] | None = None):
        super().__init__(parent, fg_color="transparent")

        self._label = ctk.CTkLabel(
            self, text=label,
            font=font(size=12),
            text_color=O["text_muted"], anchor="w",
        )
        self._label.pack(fill="x", pady=(0, 4))

        self._box = ctk.CTkFrame(self, corner_radius=10,
                                  fg_color=O["input_bg"],
                                  border_width=1, border_color=O["input_border"])
        self._box.pack(fill="x")
        self._box.grid_columnconfigure(1, weight=1)

        col = 0
        if icon and not values:
            ctk.CTkLabel(self._box, text=icon,
                         font=font(size=14),
                         text_color=O["text_light"], width=34).grid(
                row=0, column=0, padx=(8, 0), pady=8)
            col = 1

        if values is not None:
            self.widget = ctk.CTkComboBox(
                self._box, values=values,
                fg_color=O["input_bg"], border_width=0,
                button_color=O["accent"],
                button_hover_color=O["accent_hover"],
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color=O["text"],
                font=font(size=13),
                height=height or 38,
            )
            if initial: self.widget.set(initial)
            self.widget.grid(row=0, column=col, columnspan=2-col,
                             sticky="ew", padx=(8 if col==0 else 4, 8), pady=4)
        elif multiline:
            self.widget = ctk.CTkTextbox(
                self._box, height=height or 100,
                fg_color=O["input_bg"], border_width=0,
                font=font(size=13),
                corner_radius=0, text_color=O["text"],
            )
            if initial: self.widget.insert("1.0", initial)
            self.widget.grid(row=0, column=col, columnspan=2-col,
                             sticky="nsew", padx=(8 if col==0 else 4, 8), pady=4)
        else:
            self.widget = ctk.CTkEntry(
                self._box,
                placeholder_text=placeholder,
                placeholder_text_color=O["text_light"],
                fg_color=O["input_bg"], border_width=0,
                text_color=O["text"],
                font=font(size=13),
                height=height or 40,
                show="●" if password else "",
            )
            if initial: self.widget.insert(0, initial)
            self.widget.grid(row=0, column=col, columnspan=2-col,
                             sticky="ew", padx=(8 if col==0 else 4, 8), pady=4)

        self.widget.bind("<FocusIn>",  self._on_focus_in)
        self.widget.bind("<FocusOut>", self._on_focus_out)

    def get(self) -> str:
        if isinstance(self.widget, ctk.CTkTextbox):
            return self.widget.get("1.0", "end").strip()
        return self.widget.get()

    def insert(self, index, value: str):
        if isinstance(self.widget, ctk.CTkComboBox):
            self.widget.set(value)
        elif isinstance(self.widget, ctk.CTkTextbox):
            self.widget.insert("1.0", value)
        else:
            self.widget.insert(0, value)

    def delete(self, first, last=None):
        if isinstance(self.widget, ctk.CTkComboBox):
            self.widget.set("")
        elif isinstance(self.widget, ctk.CTkTextbox):
            self.widget.delete("1.0", "end")
        else:
            self.widget.delete(0, "end")

    def set_error(self, _=""):
        self._box.configure(border_color=O["input_error"],
                            fg_color=O["input_error_soft"])
        self._label.configure(text_color=O["danger"])

    def clear_state(self):
        self._box.configure(border_color=O["input_border"], fg_color=O["input_bg"])
        self._label.configure(text_color=O["text_muted"])

    def _on_focus_in(self, _=None):
        self._box.configure(border_color=O["input_focus"], fg_color="#FFFFFF")
        self._label.configure(text_color=O["accent"])

    def _on_focus_out(self, _=None):
        self._box.configure(border_color=O["input_border"], fg_color=O["input_bg"])
        self._label.configure(text_color=O["text_muted"])


# ══════════════════════════════════════════════════════════════════════════════
#  StudentCard – item da lista lateral
# ══════════════════════════════════════════════════════════════════════════════
class StudentCard(ctk.CTkFrame):
    def __init__(self, parent, student: dict[str, Any], on_select):
        super().__init__(parent, fg_color=O["student_bg"],
                         corner_radius=10, cursor="hand2")
        self._student   = student
        self._on_select = on_select
        self._selected  = False
        self._build()

    def _build(self):
        nome    = self._student.get("name", "N/A")
        course  = self._student.get("course", "Sem curso")
        av_color = _av_color(nome)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        inner.grid_columnconfigure(1, weight=1)

        av = _avatar(inner, nome[:2], av_color, 38)
        av.grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")

        ctk.CTkLabel(inner, text=nome,
                     font=font(size=13, weight="bold"),
                     text_color=O["text"], anchor="w").grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(inner, text=course,
                     font=font(size=11),
                     text_color=O["text_muted"], anchor="w").grid(row=1, column=1, sticky="w")

        self.bind("<Enter>",    lambda e: self.configure(fg_color=O["student_hover"])
                                if not self._selected else None)
        self.bind("<Leave>",    lambda e: self.configure(
            fg_color=O["student_active"] if self._selected else O["student_bg"]))
        self.bind("<Button-1>", lambda _: self._on_select(self._student, self))
        for child in inner.winfo_children():
            child.bind("<Button-1>", lambda _: self._on_select(self._student, self))

    def set_selected(self, selected: bool):
        self._selected = selected
        self.configure(fg_color=O["student_active"] if selected else O["student_bg"])


# ══════════════════════════════════════════════════════════════════════════════
#  OrientationHistoryCard – card de orientação no histórico
# ══════════════════════════════════════════════════════════════════════════════
class OrientationHistoryCard(ctk.CTkFrame):
    def __init__(self, parent, orientation: dict[str, Any],
                 on_view, on_edit, on_duplicate, on_delete):
        super().__init__(parent, fg_color=O["card_bg"],
                         corner_radius=O["card_radius"],
                         border_width=1, border_color=O["card_border"])
        self._o          = orientation
        self._on_view    = on_view
        self._on_edit    = on_edit
        self._on_duplicate = on_duplicate
        self._on_delete  = on_delete
        self._build()

    def _build(self):
        tema  = self._o.get("theme", "Geral")
        color, soft = O["temas"].get(tema, _TEMA_DEFAULT)

        # Barra lateral colorida pelo tema
        ctk.CTkFrame(self, width=4, corner_radius=0,
                     fg_color=color).pack(side="left", fill="y")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=12)

        # ── Topo: círculo de data + info + ações ─────────────────────────────
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", pady=(0, 8))

        # Círculo com o dia
        date_str = self._o.get("session_date", "")
        day_txt  = "?"
        if date_str:
            try:
                day_txt = str(datetime.fromisoformat(
                    date_str.replace("Z", "")).day)
            except Exception:
                pass

        day_bg = ctk.CTkFrame(top, width=46, height=46,
                               corner_radius=12, fg_color=soft)
        day_bg.pack(side="left", padx=(0, 14))
        day_bg.pack_propagate(False)
        ctk.CTkLabel(day_bg, text=day_txt,
                     font=font(size=17, weight="bold"),
                     text_color=color).place(relx=0.5, rely=0.5, anchor="center")

        # Título + tema chip
        meta = ctk.CTkFrame(top, fg_color="transparent")
        meta.pack(side="left", fill="x", expand=True)

        title = self._o.get("title", "Orientação")
        ctk.CTkLabel(meta, text=title,
                     font=font(size=13, weight="bold"),
                     text_color=O["text"], anchor="w").pack(anchor="w")

        chip = _chip(meta, tema, tema)
        chip.pack(anchor="w", pady=(4, 0))

        # Ações à direita
        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.pack(side="right", anchor="n")

        for label, cmd, accent, s in [
            ("👁  Ver",      lambda: self._on_view(self._o),
             O["accent_soft"], O["accent"]),
            ("✏  Editar",   lambda: self._on_edit(self._o),
             O["accent"],     "#FFFFFF"),
            ("⧉  Duplicar", lambda: self._on_duplicate(self._o.get("id")),
             O["divider"],    O["text_muted"]),
            ("🗑  Excluir",  lambda: self._on_delete(self._o.get("id")),
             O["danger_soft"], O["danger"]),
        ]:
            ctk.CTkButton(acts, text=label, command=cmd,
                          height=28, width=90, corner_radius=8,
                          fg_color=accent, hover_color=accent,
                          text_color=s,
                          font=font(size=11, weight="bold")).pack(
                side="left", padx=(0, 4))

        # ── Prévia do conteúdo ───────────────────────────────────────────────
        content = self._o.get("content", "")
        if content:
            _divider(body)
            preview = content[:160] + ("…" if len(content) > 160 else "")
            ctk.CTkLabel(body, text=preview,
                         font=font(size=12),
                         text_color=O["text_muted"],
                         wraplength=640, justify="left", anchor="w").pack(
                anchor="w", pady=(8, 0))


# ══════════════════════════════════════════════════════════════════════════════
#  OrientacoesFrame – frame principal
# ══════════════════════════════════════════════════════════════════════════════
class OrientacoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=O["page_bg"],
                         scrollbar_button_color="#C7D2FE",
                         scrollbar_button_hover_color="#A5B4FC")
        self.controller          = controller
        self.servico_orientacoes = servico_orientacoes
        self._selected_student: dict | None = None
        self._selected_card: StudentCard | None = None

        self._criar_cabecalho()
        self._criar_conteudo()
        self._carregar_dados()

    # ══════════════════════════════════════════
    #  CABEÇALHO
    # ══════════════════════════════════════════
    def _criar_cabecalho(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=28, pady=(20, 4))

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="Orientações",
                     font=font(size=22, weight="bold"),
                     text_color=O["text"]).pack(anchor="w")
        ctk.CTkLabel(left, text="Fluxo de apoio e encaminhamentos",
                     font=font(size=13),
                     text_color=O["text_muted"]).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            bar, text="＋  Nova Orientação",
            command=self._nova_orientacao,
            height=40, corner_radius=12, width=170,
            font=font(size=13, weight="bold"),
            fg_color=O["accent"], hover_color=O["accent_hover"],
            text_color="white",
        ).pack(side="right")

        ctk.CTkFrame(self, height=1,
                     fg_color=O["card_border"] if "card_border" in O else O["card_border"]).pack(
            fill="x", padx=28, pady=(12, 0))

    # ══════════════════════════════════════════
    #  LAYOUT: sidebar + painel
    # ══════════════════════════════════════════
    def _criar_conteudo(self):
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=28, pady=16)
        wrap.grid_columnconfigure(1, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        self._criar_sidebar_estudantes(wrap)
        self._criar_painel_principal(wrap)

    # ── Sidebar de estudantes ────────────────────────────────────────────────
    def _criar_sidebar_estudantes(self, parent):
        sidebar = ctk.CTkFrame(parent, fg_color=O["sidebar_bg"],
                                corner_radius=O["card_radius"],
                                border_width=1, border_color=O["sidebar_border"],
                                width=280)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        # Título
        hdr = ctk.CTkFrame(sidebar, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        ctk.CTkLabel(hdr, text="Estudantes",
                     font=font(size=13, weight="bold"),
                     text_color=O["text"]).pack(side="left")

        # Busca
        search_wrap = ctk.CTkFrame(sidebar, fg_color="#F3F4F6", corner_radius=10)
        search_wrap.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        ctk.CTkLabel(search_wrap, text="🔍",
                     font=font(size=13),
                     text_color=O["text_light"]).pack(side="left", padx=(10, 0))

        self._entry_busca = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Buscar estudante...",
            fg_color="#F3F4F6", border_width=0,
            text_color=O["text"],
            placeholder_text_color=O["text_light"],
            font=font(size=13), height=36,
        )
        self._entry_busca.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self._entry_busca.bind("<KeyRelease>", self._filtrar_estudantes)

        ctk.CTkFrame(sidebar, height=1, fg_color=O["divider"]).grid(
            row=1, column=0, sticky="sew", padx=0, pady=(42, 0))

        # Lista
        self._scroll_students = ctk.CTkScrollableFrame(
            sidebar, fg_color="transparent",
            scrollbar_button_color="#D1D5DB",
            scrollbar_button_hover_color="#9CA3AF",
        )
        self._scroll_students.grid(row=2, column=0, sticky="nsew")

        # Placeholder de carregamento
        self._students_placeholder = ctk.CTkLabel(
            self._scroll_students,
            text="Carregando estudantes...",
            font=font(size=12),
            text_color=O["text_muted"],
        )
        self._students_placeholder.pack(pady=20)

    # ── Painel principal ─────────────────────────────────────────────────────
    def _criar_painel_principal(self, parent):
        self._painel = ctk.CTkFrame(parent, fg_color="transparent")
        self._painel.grid(row=0, column=1, sticky="nsew")
        self._painel.grid_rowconfigure(1, weight=1)
        self._painel.grid_columnconfigure(0, weight=1)

        # Barra de tabs
        self._tab_bar = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._tab_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self._tab_ativo = "historico"
        self._tab_btns: dict[str, ctk.CTkButton] = {}

        for key, label in [("historico", "📋  Histórico"),
                           ("nova",      "＋  Nova Orientação")]:
            btn = ctk.CTkButton(
                self._tab_bar, text=label,
                command=lambda k=key: self._mudar_tab(k),
                height=36, width=170, corner_radius=10,
                font=font(size=12, weight="bold"),
                fg_color=O["accent"]      if key == "historico" else O["accent_soft"],
                hover_color=O["accent_hover"],
                text_color="#FFFFFF"      if key == "historico" else O["accent"],
            )
            btn.pack(side="left", padx=(0, 8))
            self._tab_btns[key] = btn

        # Área de conteúdo das tabs
        self._area_historico = ctk.CTkScrollableFrame(
            self._painel, fg_color="transparent",
            scrollbar_button_color="#C7D2FE",
        )
        self._area_historico.grid(row=1, column=0, sticky="nsew")

        self._area_nova = ctk.CTkFrame(self._painel, fg_color="transparent")
        self._area_nova.grid(row=1, column=0, sticky="nsew")
        self._area_nova.grid_remove()

        self._construir_form_nova(self._area_nova)

        # Placeholder inicial
        self._hist_placeholder = ctk.CTkLabel(
            self._area_historico,
            text="Selecione um estudante para ver as orientações",
            font=font(size=13),
            text_color=O["text_muted"],
        )
        self._hist_placeholder.pack(pady=40)

    def _mudar_tab(self, key: str):
        self._tab_ativo = key
        for k, btn in self._tab_btns.items():
            ativo = k == key
            btn.configure(
                fg_color=O["accent"]      if ativo else O["accent_soft"],
                text_color="#FFFFFF"      if ativo else O["accent"],
            )
        if key == "historico":
            self._area_nova.grid_remove()
            self._area_historico.grid()
        else:
            self._area_historico.grid_remove()
            self._area_nova.grid()

    # ── Formulário de nova orientação ────────────────────────────────────────
    def _construir_form_nova(self, parent):
        card = ctk.CTkFrame(parent, fg_color=O["card_bg"],
                            corner_radius=O["card_radius"],
                            border_width=1, border_color=O["card_border"])
        card.pack(fill="both", expand=True)

        # Banner
        banner = ctk.CTkFrame(card, fg_color=O["accent_soft"],
                              corner_radius=0, height=56)
        banner.pack(fill="x"); banner.pack_propagate(False)
        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=20)

        ib = ctk.CTkFrame(bi, width=34, height=34, corner_radius=9, fg_color=O["accent"])
        ib.pack(side="left", padx=(0, 10)); ib.pack_propagate(False)
        ctk.CTkLabel(ib, text="📋",
                     font=font(size=15)).place(relx=0.5, rely=0.5, anchor="center")
        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(ts, text="Registrar Orientação",
                     font=font(size=13, weight="bold"),
                     text_color=O["accent"]).pack(anchor="w")
        ctk.CTkLabel(ts, text="Preencha os dados do atendimento",
                     font=font(size=10),
                     text_color=O["text_muted"]).pack(anchor="w")

        body = ctk.CTkScrollableFrame(card, fg_color="transparent",
                                       scrollbar_button_color="#D1D5DB")
        body.pack(fill="both", expand=True, padx=20, pady=14)

        self.f_titulo = FormField(body, "📝  Título", placeholder="Título da orientação")
        self.f_titulo.pack(fill="x", pady=(0, 10))

        self.f_conteudo = FormField(body, "📄  Conteúdo",
                                     placeholder="Descreva a orientação...",
                                     multiline=True, height=100)
        self.f_conteudo.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        row.grid_columnconfigure((0, 1), weight=1)

        self.f_tema = FormField(row, "🏷  Tema",
                                 values=["Acadêmico","Emocional","Social",
                                         "Familiar","Vocacional","Geral"],
                                 initial="Geral")
        self.f_tema.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.f_data = FormField(row, "📅  Data da Sessão",
                                 placeholder="YYYY-MM-DD", icon="📅")
        self.f_data.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.f_encaminhamento = FormField(body, "🔗  Encaminhamento",
                                           placeholder="Serviço ou profissional indicado")
        self.f_encaminhamento.pack(fill="x", pady=(0, 10))

        self.f_obs = FormField(body, "💬  Observações",
                                multiline=True, height=70)
        self.f_obs.pack(fill="x", pady=(0, 10))

        # Rodapé
        ctk.CTkFrame(card, height=1, fg_color=O["divider"]).pack(fill="x")
        footer = ctk.CTkFrame(card, fg_color="transparent", height=58)
        footer.pack(fill="x", padx=20); footer.pack_propagate(False)

        ctk.CTkButton(footer, text="Cancelar",
                      command=lambda: self._mudar_tab("historico"),
                      height=36, width=110, corner_radius=10,
                      fg_color=O["divider"], hover_color="#E5E7EB",
                      text_color=O["text_muted"],
                      border_width=1, border_color=O["card_border"],
                      font=font(size=12)).pack(side="left", pady=11)

        ctk.CTkButton(footer, text="✔  Salvar Orientação",
                      command=self._salvar_orientacao,
                      height=36, width=180, corner_radius=10,
                      fg_color=O["accent"], hover_color=O["accent_hover"],
                      text_color="white",
                      font=font(size=13, weight="bold")).pack(side="right", pady=11)

    # ══════════════════════════════════════════
    #  Dados
    # ══════════════════════════════════════════
    def _carregar_dados(self):
        def fetch():
            return self.servico_orientacoes.listar_orientacoes()

        def on_success(resultado):
            self._renderizar(resultado)

        def on_error(exc):
            logger.error("Erro ao carregar orientações: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _renderizar(self, resultado):
        # Limpa placeholder de histórico
        for w in self._area_historico.winfo_children():
            w.destroy()

        orientacoes = []
        if resultado.get("success"):
            data = resultado.get("data") or {}
            orientacoes = data.get("orientations") or []

        # Popula sidebar de estudantes com estudantes únicos do histórico
        estudantes_vistos: set = set()
        estudantes: list[dict] = []
        for o in orientacoes:
            sid = o.get("student_id") or o.get("student_name")
            if sid not in estudantes_vistos:
                estudantes_vistos.add(sid)
                estudantes.append({
                    "id":     sid,
                    "name":   o.get("student_name", "Estudante"),
                    "course": o.get("student_course", ""),
                    "_all_orientations": [x for x in orientacoes
                                          if x.get("student_id") == sid or
                                          x.get("student_name") == o.get("student_name")],
                })

        self._todos_estudantes = estudantes
        self._todas_orientacoes = orientacoes
        self._popular_sidebar(estudantes)

        # Mostra todas se não há seleção
        if not orientacoes:
            ctk.CTkLabel(self._area_historico,
                         text="📋  Nenhuma orientação registrada",
                         font=font(size=13),
                         text_color=O["text_muted"]).pack(pady=30)
        else:
            self._mostrar_orientacoes(orientacoes)

    def _popular_sidebar(self, estudantes: list):
        for w in self._scroll_students.winfo_children():
            w.destroy()

        if not estudantes:
            ctk.CTkLabel(self._scroll_students,
                         text="Nenhum estudante",
                         font=font(size=12),
                         text_color=O["text_muted"]).pack(pady=20)
            return

        # Item "Todos"
        todos_row = ctk.CTkFrame(self._scroll_students,
                                  fg_color=O["accent_soft"], corner_radius=10,
                                  cursor="hand2")
        todos_row.pack(fill="x", pady=(0, 4), padx=4)
        ctk.CTkLabel(todos_row, text="📋  Todos os estudantes",
                     font=font(size=12, weight="bold"),
                     text_color=O["accent"]).pack(padx=14, pady=10)
        todos_row.bind("<Button-1>",
                       lambda _: self._mostrar_orientacoes(self._todas_orientacoes))

        for st in estudantes:
            card = StudentCard(self._scroll_students, st,
                               on_select=self._selecionar_estudante)
            card.pack(fill="x", pady=2, padx=4)

    def _filtrar_estudantes(self, _=None):
        termo = self._entry_busca.get().lower() if hasattr(self, "_entry_busca") else ""
        if not hasattr(self, "_todos_estudantes"):
            return
        filtrados = [s for s in self._todos_estudantes
                     if termo in s.get("name", "").lower()]
        self._popular_sidebar(filtrados)

    def _selecionar_estudante(self, student: dict, card_widget: StudentCard):
        if self._selected_card:
            self._selected_card.set_selected(False)
        self._selected_card = card_widget
        card_widget.set_selected(True)
        self._selected_student = student

        ors = student.get("_all_orientations",
                          [o for o in self._todas_orientacoes
                           if o.get("student_name") == student.get("name")])
        self._mostrar_orientacoes(ors)

    def _mostrar_orientacoes(self, orientacoes: list):
        for w in self._area_historico.winfo_children():
            w.destroy()

        if not orientacoes:
            ctk.CTkLabel(self._area_historico,
                         text="📋  Nenhuma orientação para este estudante",
                         font=font(size=13),
                         text_color=O["text_muted"]).pack(pady=30)
            return

        for o in orientacoes:
            OrientationHistoryCard(
                self._area_historico, orientation=o,
                on_view=self._ver_orientacao,
                on_edit=self._editar_orientacao,
                on_duplicate=self._duplicar_orientacao,
                on_delete=self._excluir_orientacao,
            ).pack(fill="x", pady=(0, 10))

    # ══════════════════════════════════════════
    #  Ações
    # ══════════════════════════════════════════
    def _nova_orientacao(self):
        self._mudar_tab("nova")

    def _salvar_orientacao(self):
        titulo  = self.f_titulo.get().strip()
        conteudo = self.f_conteudo.get().strip()
        if not titulo:
            self.f_titulo.set_error("Título é obrigatório")
            return
        dados = {
            "title":        titulo,
            "content":      conteudo,
            "theme":        self.f_tema.get(),
            "session_date": self.f_data.get().strip(),
            "referral":     self.f_encaminhamento.get().strip(),
            "notes":        self.f_obs.get().strip(),
            "student_id":   (self._selected_student.get("id")
                             if self._selected_student else None),
        }
        def save():
            return self.servico_orientacoes.criar_orientacao(dados)

        def on_ok(_):
            self._mudar_tab("historico")
            self._carregar_dados()

        def on_err(e):
            messagebox.showerror("Erro", str(e))

        AsyncRunner.run(task=save, on_success=on_ok,
                        on_error=on_err, widget_ref=self)

    def _ver_orientacao(self, o: dict):
        self._modal_detalhe(o)

    def _editar_orientacao(self, o: dict):
        # Popula o form com os dados da orientação e abre a tab
        self.f_titulo.delete(0, "end")
        self.f_titulo.insert(0, o.get("title", ""))
        self.f_conteudo.delete("1.0", "end")
        self.f_conteudo.insert("1.0", o.get("content", ""))
        self.f_tema.widget.set(o.get("theme", "Geral"))
        self.f_data.delete(0, "end")
        self.f_data.insert(0, (o.get("session_date") or "")[:10])
        self.f_encaminhamento.delete(0, "end")
        self.f_encaminhamento.insert(0, o.get("referral", "") or "")
        self.f_obs.delete("1.0", "end")
        self.f_obs.insert("1.0", o.get("notes", "") or "")
        self._mudar_tab("nova")

    def _duplicar_orientacao(self, oid):
        logger.info("Duplicar orientação %s", oid)

    def _excluir_orientacao(self, oid):
        if not messagebox.askyesno("Confirmar", "Excluir esta orientação?"):
            return

        def delete(): return self.servico_orientacoes.excluir_orientacao(oid)
        def on_ok(_): self._carregar_dados()
        def on_err(e): messagebox.showerror("Erro", str(e))

        AsyncRunner.run(task=delete, on_success=on_ok,
                        on_error=on_err, widget_ref=self)

    # ══════════════════════════════════════════
    #  Modal de detalhe
    # ══════════════════════════════════════════
    def _modal_detalhe(self, o: dict):
        modal = ctk.CTkToplevel(self)
        modal.title("Orientação")
        modal.configure(fg_color=O["card_bg"])
        modal.resizable(False, False)

        w, h = 540, 480
        modal.update_idletasks()
        sx = modal.winfo_screenwidth()  // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        tema  = o.get("theme", "Geral")
        color, soft = O["temas"].get(tema, _TEMA_DEFAULT)

        # Banner
        banner = ctk.CTkFrame(modal, fg_color=soft, corner_radius=0, height=70)
        banner.pack(fill="x"); banner.pack_propagate(False)
        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=24)

        ib = ctk.CTkFrame(bi, width=42, height=42, corner_radius=12, fg_color=color)
        ib.pack(side="left", padx=(0, 12)); ib.pack_propagate(False)
        ctk.CTkLabel(ib, text="📋",
                     font=font(size=18)).place(relx=0.5, rely=0.5, anchor="center")

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(ts, text=o.get("title", "Orientação"),
                     font=font(size=14, weight="bold"),
                     text_color=O["text"]).pack(anchor="w")

        chip = ctk.CTkFrame(ts, fg_color=color, corner_radius=6)
        chip.pack(anchor="w", pady=(3, 0))
        ctk.CTkLabel(chip, text=tema,
                     font=font(size=10, weight="bold"),
                     text_color="#FFFFFF").pack(padx=8, pady=2)

        # Corpo
        body = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=14)

        for label, value in [
            ("📅  Data",          (o.get("session_date") or "—")[:10]),
            ("🏷  Tema",          tema),
            ("🔗  Encaminhamento", o.get("referral") or "—"),
        ]:
            row = ctk.CTkFrame(body, fg_color="#FAFAFA", corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=160,
                         font=font(size=12),
                         text_color=O["text_muted"], anchor="w").pack(
                side="left", padx=12, pady=8)
            ctk.CTkLabel(row, text=value,
                         font=font(size=12, weight="bold"),
                         text_color=O["text"]).pack(side="left")

        # Conteúdo completo
        ctk.CTkFrame(body, height=1, fg_color=O["divider"]).pack(fill="x", pady=(10, 8))
        ctk.CTkLabel(body, text=o.get("content", ""),
                     font=font(size=12),
                     text_color=O["text_muted"],
                     wraplength=460, justify="left", anchor="w").pack(anchor="w")

        ctk.CTkButton(modal, text="Fechar", command=modal.destroy,
                      height=38, corner_radius=10, width=120,
                      fg_color=O["accent"], hover_color=O["accent_hover"],
                      text_color="white",
                      font=font(size=13, weight="bold")).pack(pady=(0, 16))
import logging
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime, date
from typing import Any
from utils.async_runner import AsyncRunner
from services.orientacoes import servico_orientacoes
from services.estudantes import ServicoEstudante
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    PrimaryButton,
    GhostButton,
    Badge,
    EmptyState,
)

logger = logging.getLogger("apps.desktop")

# ============================================================================
#  Paleta dedicada
# ============================================================================

# ============================================================================
#  Componentes de apoio
# ============================================================================
class FormField(ctk.CTkFrame):
    """Campo de formulário com label, ícone e estados normal/foco/erro."""

    _BORDER_NORMAL = THEME["border"]
    _BORDER_FOCUS  = THEME["primary"]
    _BORDER_ERROR  = THEME["danger"]
    _BG_NORMAL     = THEME["bg_alt"]
    _BG_FOCUS      = THEME["surface"]

    def __init__(self, parent, label: str, placeholder: str = "",
                 icon: str = "", password: bool = False,
                 initial: str = "", multiline: bool = False,
                 height: int | None = None, values: list[str] | None = None):
        super().__init__(parent, fg_color="transparent")

        self._label = ctk.CTkLabel(
            self, text=label,
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
            anchor="w",
        )
        self._label.pack(fill="x", pady=(0, 4))

        box = ctk.CTkFrame(
            self,
            corner_radius=RADIUS["md"],
            fg_color=self._BG_NORMAL,
            border_width=1,
            border_color=self._BORDER_NORMAL,
        )
        box.pack(fill="x")
        box.grid_columnconfigure(1, weight=1)
        self._box = box

        if icon and not values:
            ctk.CTkLabel(
                box, text=icon,
                font=themed_font("body"),
                text_color=THEME["text_muted"],
                width=36,
            ).grid(row=0, column=0, padx=(10, 4), pady=8)

        if values is not None:
            self.widget = ctk.CTkComboBox(
                box, values=values,
                fg_color="transparent", border_width=0,
                font=themed_font("body"), height=height or 36,
            )
            self.widget.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
            if initial:
                self.widget.set(initial)
        elif multiline:
            self.widget = ctk.CTkTextbox(
                box, height=height or 120,
                fg_color="transparent", border_width=0,
                font=themed_font("body"), corner_radius=0,
            )
            self.widget.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=4)
            if initial:
                self.widget.insert("1.0", initial)
        else:
            self.widget = ctk.CTkEntry(
                box,
                placeholder_text=placeholder,
                fg_color="transparent",
                border_width=0,
                font=themed_font("body"),
                height=height or 36,
                show="●" if password else "",
            )
            self.widget.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
            if initial:
                self.widget.insert(0, initial)

        self.widget.bind("<FocusIn>",  self._on_focus_in)
        self.widget.bind("<FocusOut>", self._on_focus_out)

    def get(self) -> str:
        if isinstance(self.widget, ctk.CTkTextbox):
            return self.widget.get("1.0", "end").strip()
        return self.widget.get()

    def insert(self, index: str, value: str) -> None:
        if isinstance(self.widget, ctk.CTkComboBox):
            self.widget.set(value)
        elif isinstance(self.widget, ctk.CTkTextbox):
            self.widget.insert(index, value)
        else:
            self.widget.insert(0 if index == "end" else index, value)

    def delete(self, first: str, last: str | None = None) -> None:
        if isinstance(self.widget, ctk.CTkComboBox):
            self.widget.set("")
        elif isinstance(self.widget, ctk.CTkTextbox):
            self.widget.delete("1.0", "end")
        else:
            self.widget.delete(0, "end")

    def set_error(self, msg: str = ""):
        self._box.configure(
            border_color=self._BORDER_ERROR,
            fg_color=THEME["danger_soft"],
        )
        self._label.configure(text_color=THEME["danger"])

    def clear_state(self):
        self._box.configure(
            border_color=self._BORDER_NORMAL,
            fg_color=self._BG_NORMAL,
        )
        self._label.configure(text_color=THEME["text_muted"])

    def _on_focus_in(self, _=None):
        self._box.configure(
            border_color=self._BORDER_FOCUS,
            fg_color=self._BG_FOCUS,
        )
        self._label.configure(text_color=THEME["primary"])

    def _on_focus_out(self, _=None):
        self._box.configure(
            border_color=self._BORDER_NORMAL,
            fg_color=self._BG_NORMAL,
        )
        self._label.configure(text_color=THEME["text_muted"])

class StudentCard(ctk.CTkFrame):
    """Card compacto de estudante para a lista lateral."""

    def __init__(self, parent, student: dict[str, Any], on_select):
        super().__init__(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["border"],
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
            fg_color=THEME["primary_soft"],
            corner_radius=18,
        )
        avatar.pack(side="left", padx=(0, 10))
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar, text=initials, font=font(12, "bold"),
            text_color=THEME["primary"],
        ).place(relx=0.5, rely=0.5, anchor="center")
        txt = ctk.CTkFrame(inner, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(txt, text=nome, font=font(13, "bold"),
                     text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(txt, text=course, font=font(11),
                     text_color=THEME["text_muted"]).pack(anchor="w")
        for w in (self, inner):
            w.bind("<Button-1>", lambda _: self._on_select(self._student, self))

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.configure(
            fg_color=THEME["primary_soft"]
            if selected else THEME["surface"]
        )

class TabButton(ctk.CTkButton):
    """Botão de tab com estilo ativo/inativo."""

    def __init__(self, parent, text: str, command, initial: bool = False):
        super().__init__(
            parent,
            text=text,
            fg_color=THEME["surface"] if initial else "transparent",
            text_color=THEME["text"] if initial else THEME["text_muted"],
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
            border_color=THEME["border"],
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
            fg_color=THEME["primary_soft"],
            corner_radius=20,
        )
        date_circle.pack(side="left", padx=(0, 12))
        date_circle.pack_propagate(False)
        ctk.CTkLabel(
            date_circle, text=str(day), font=font(14, "bold"),
            text_color=THEME["primary"],
        ).place(relx=0.5, rely=0.5, anchor="center")
        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)
        title = self._orientation.get("title", "Orientação")
        ctk.CTkLabel(info, text=title, font=font(14, "bold"),
                     text_color=THEME["text"]).pack(anchor="w")
        theme = self._orientation.get("theme", "Geral")
        Badge(info, text=theme, color=THEME["primary"]).pack(anchor="w", pady=(4, 0))
        content = self._orientation.get("content", "")
        if content:
            preview = content[:120] + ("..." if len(content) > 120 else "")
            ctk.CTkLabel(
                info, text=preview, font=font(10),
                text_color=THEME["text_muted"],
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
            text_color=THEME["danger"],
            hover_color=THEME["danger_soft"],
        ).pack(side="left")

class OrientacoesFrame(ctk.CTkScrollableFrame):
    """Frame principal da página Orientações."""

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_orientacoes = servico_orientacoes

        self.grid_columnconfigure(0, weight=1)

        self._criar_cabecalho()
        self._criar_conteudo()

        self._carregar_dados()

    def _criar_cabecalho(self):
        PageHeader(self, title="Orientações", subtitle="Fluxo de apoio e encaminhamentos").pack(
            fill="x",
            padx=SPACING["page_x"],
            pady=(SPACING["page_y"], 16),
        )

    def _criar_conteudo(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(0, 24))
        wrapper.grid_columnconfigure(0, weight=1)

        self._placeholder = ctk.CTkLabel(
            wrapper,
            text="Carregando orientações...",
            font=font(12),
            text_color=THEME["text_muted"],
        )
        self._placeholder.grid(row=0, column=0, pady=20)

        self._lista_container = ctk.CTkFrame(wrapper, fg_color="transparent")

    def _carregar_dados(self):
        def fetch():
            return self.servico_orientacoes.listar_orientacoes()

        def on_success(resultado):
            self._renderizar(resultado)

        def on_error(exc):
            ctk.CTkMessagebox(
                self, title="Erro",
                message=f"Não foi possível carregar orientações.\n{exc}",
                icon="error",
            )

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _renderizar(self, resultado):
        if not self._placeholder.winfo_exists():
            return

        self._placeholder.destroy()
        self._lista_container.grid(row=0, column=0, sticky="nsew")

        orientacoes = []
        if resultado.get("success"):
            data = resultado.get("data") or {}
            orientacoes = data.get("orientations") or []

        if not orientacoes:
            EmptyState(
                self._lista_container,
                icon="📄",
                title="Nenhuma orientação registrada",
                subtitle="As orientações aparecerão aqui",
            ).pack(pady=20)
            return

        for orientacao in orientacoes:
            OrientationHistoryCard(
                self._lista_container,
                orientation=orientacao,
                on_view=self._ver_orientacao,
                on_edit=self._editar_orientacao,
                on_duplicate=self._duplicar_orientacao,
                on_delete=self._excluir_orientacao,
            ).pack(fill="x", pady=4)

    def _ver_orientacao(self, orientacao_id: int):
        print(f"Ver orientação {orientacao_id}")

    def _editar_orientacao(self, orientacao: dict):
        print(f"Editar orientação {orientacao.get('id')}")

    def _duplicar_orientacao(self, orientacao_id: int):
        print(f"Duplicar orientação {orientacao_id}")

    def _excluir_orientacao(self, orientacao_id: int):
        print(f"Excluir orientação {orientacao_id}")

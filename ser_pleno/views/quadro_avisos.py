from __future__ import annotations

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import datetime
import html
import threading
import logging
from typing import Any

from services.mural import servico_mural
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    PrimaryButton,
    GhostButton,
    EmptyState,
    Badge,
)

logger = logging.getLogger("apps.desktop")


# ═══════════════════════════════════════════════════════════════════════════════
#  Paleta dedicada
# ═══════════════════════════════════════════════════════════════════════════════
AVISOS_COLORS: dict[str, str] = {
    "bg":            THEME["bg"],
    "card":          THEME["card"],
    "card_alt":      THEME["bg_alt"],
    "border":        THEME["border"],
    "border_strong": THEME["border_strong"],
    "primary":       THEME["primary"],
    "primary_light": THEME["primary_light"],
    "primary_soft":  THEME["primary_soft"],
    "text":          THEME["text"],
    "text_muted":    THEME["text_muted"],
    "text_secondary":THEME["text_secondary"],
    "danger":        THEME["danger"],
    "danger_soft":   THEME["danger_soft"],
    "success":       THEME["success"],
    "success_soft":  THEME["success_soft"],
    "warning":       THEME["warning"],
    "warning_soft":  THEME["warning_soft"],
}


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════
def escape_html(s: str | None) -> str:
    if s is None:
        return ""
    return html.escape(str(s))


# ═══════════════════════════════════════════════════════════════════════════════
#  Componentes reutilizáveis da tela de avisos
# ═══════════════════════════════════════════════════════════════════════════════
class FormField(ctk.CTkFrame):
    """
    Campo de formulário com label, ícone e estados
    normal / foco / erro (similar ao LoginInputField).
    """

    _BORDER_NORMAL = THEME["border"]
    _BORDER_FOCUS  = THEME["primary"]
    _BORDER_ERROR  = THEME["danger"]
    _BG_NORMAL     = THEME["bg_alt"]
    _BG_FOCUS      = THEME["card"]

    def __init__(self, parent, label: str, placeholder: str = "",
                 icon: str = "", password: bool = False,
                 initial: str = "", multiline: bool = False,
                 height: int | None = None, values: list[str] | None = None):
        super().__init__(parent, fg_color="transparent")

        self._label = ctk.CTkLabel(
            self, text=label,
            font=themed_font("caption", "bold"),
            text_color=AVISOS_COLORS["text_muted"],
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
                text_color=AVISOS_COLORS["text_muted"],
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

    # API ---------------------------------------------------------------------
    def get(self) -> str:
        if isinstance(self.widget, ctk.CTkTextbox):
            return self.widget.get("1.0", "end").strip()
        return self.widget.get()

    def insert(self, index: str, value: str) -> None:
        if isinstance(self.widget, ctk.CTkTextbox):
            self.widget.insert(index, value)
        else:
            self.widget.insert(0 if index == "end" else index, value)

    def delete(self, first: str, last: str | None = None) -> None:
        if isinstance(self.widget, ctk.CTkTextbox):
            self.widget.delete("1.0", "end")
        else:
            self.widget.delete(0, "end")

    def set_error(self, msg: str = ""):
        self._box.configure(
            border_color=self._BORDER_ERROR,
            fg_color=AVISOS_COLORS["danger_soft"],
        )
        self._label.configure(text_color=AVISOS_COLORS["danger"])

    def clear_state(self):
        self._box.configure(
            border_color=self._BORDER_NORMAL,
            fg_color=self._BG_NORMAL,
        )
        self._label.configure(text_color=AVISOS_COLORS["text_muted"])

    # Internos ----------------------------------------------------------------
    def _on_focus_in(self, _=None):
        self._box.configure(
            border_color=self._BORDER_FOCUS,
            fg_color=self._BG_FOCUS,
        )
        self._label.configure(text_color=AVISOS_COLORS["primary"])

    def _on_focus_out(self, _=None):
        self._box.configure(
            border_color=self._BORDER_NORMAL,
            fg_color=self._BG_NORMAL,
        )
        self._label.configure(text_color=AVISOS_COLORS["text_muted"])


class PublicacaoModal(ctk.CTkToplevel):
    """
    Modal de publicação/edição de aviso.
    Esquerda: formulário | Direita: pré-visualização
    """

    def __init__(self, parent, on_publish, on_cancel):
        super().__init__(parent)
        self.on_publish = on_publish
        self.on_cancel = on_cancel

        self.title("Publicação do Mural")
        self.resizable(False, False)
        self.configure(fg_color=AVISOS_COLORS["card"])
        self.withdraw()

        largura, altura = 940, 720
        self.geometry(f"{largura}x{altura}")
        try:
            self.transient(parent.master)
        except Exception:
            pass
        self._center(parent, largura, altura)

        self._build(largura, altura)

    def _center(self, parent, w, h):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _build(self, w, h):
        outer = ctk.CTkFrame(
            self,
            fg_color=AVISOS_COLORS["card_alt"],
            corner_radius=RADIUS["xl"],
            width=w - 20, height=h - 20,
            border_width=0,
        )
        outer.place(relx=0.5, rely=0.5, anchor="center")

        container = ctk.CTkFrame(
            outer,
            fg_color=AVISOS_COLORS["card"],
            corner_radius=RADIUS["lg"],
            width=w - 40, height=h - 40,
            border_width=1, border_color=AVISOS_COLORS["border"],
        )
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Header
        stripe = ctk.CTkFrame(container, fg_color=AVISOS_COLORS["primary_light"], height=56, corner_radius=RADIUS["lg"])
        stripe.place(relx=0.02, rely=0.02, relwidth=0.96)

        ctk.CTkLabel(
            stripe, text="📝  Nova Publicação",
            font=themed_font("h3", "bold"),
            text_color=AVISOS_COLORS["primary"],
        ).place(relx=0.025, rely=0.18)
        ctk.CTkLabel(
            stripe, text="Campos à esquerda · pré-visualização à direita",
            font=themed_font("overline"),
            text_color=AVISOS_COLORS["text_muted"],
        ).place(relx=0.025, rely=0.58)

        ctk.CTkButton(
            stripe, text="✕", width=36, height=36,
            fg_color="white", text_color=AVISOS_COLORS["text_muted"],
            hover_color=AVISOS_COLORS["border"],
            corner_radius=RADIUS["sm"],
            command=self._fechar,
        ).place(relx=0.95, rely=0.1, anchor="ne")

        # Colunas
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.place(relx=0.02, rely=0.12, relwidth=0.58, relheight=0.86)

        right = ctk.CTkFrame(container, fg_color="transparent")
        right.place(relx=0.62, rely=0.12, relwidth=0.36, relheight=0.86)

        self._build_form(left, w, h)
        self._build_preview(right)

    def _build_form(self, parent, w, h):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        frm = scroll

        self.f_titulo       = FormField(frm, "Título", placeholder="Digite o título", icon="📝")
        self.f_titulo.pack(fill="x", pady=(0, 10))

        self.f_conteudo     = FormField(frm, "Conteúdo", placeholder="Digite o conteúdo", multiline=True, height=130)
        self.f_conteudo.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(frm, fg_color="transparent")
        row.pack(fill="x", pady=(6, 8))
        self.f_categoria = FormField(row, "Categoria", values=["informativo", "aviso", "aula", "urgente", "evento"], initial="informativo")
        self.f_categoria.pack(side="left", padx=(0, 8))
        self.f_autor    = FormField(row, "Autor", placeholder="Nome do autor")
        self.f_autor.pack(side="left", padx=(12, 0))

        row2 = ctk.CTkFrame(frm, fg_color="transparent")
        row2.pack(fill="x", pady=(8, 8))
        self.f_local  = FormField(row2, "Local Físico", placeholder="Ex: Auditório")
        self.f_local.pack(side="left", padx=(0, 8))
        self.f_link   = FormField(row2, "Link Externo", placeholder="https://...")
        self.f_link.pack(side="left", padx=(12, 0))

        row3 = ctk.CTkFrame(frm, fg_color="transparent")
        row3.pack(fill="x", pady=(8, 8))
        self.f_data_ag       = FormField(row3, "Data Agendamento (YYYY-MM-DD)", placeholder="YYYY-MM-DD")
        self.f_data_ag.pack(side="left", padx=(0, 8))
        self.f_horario_evento= FormField(row3, "Horário Evento (YYYY-MM-DD HH:MM)", placeholder="YYYY-MM-DD HH:MM")
        self.f_horario_evento.pack(side="left", padx=(12, 0))

        self.f_layout = FormField(frm, "Layout", values=["single", "grid-2", "grid-3", "grid-4"], initial="single")
        self.f_layout.pack(fill="x", pady=(10, 8))

        ctk.CTkLabel(frm, text="Blocos (apenas para layouts grid-*):",
                     font=themed_font("body", "bold"),
                     text_color=AVISOS_COLORS["text"]).pack(anchor="w", pady=(6, 4))

        self.blocos_container = ctk.CTkScrollableFrame(
            frm, fg_color=AVISOS_COLORS["card_alt"],
            corner_radius=RADIUS["md"],
            border_width=1, border_color=AVISOS_COLORS["border"],
            height=180,
        )
        self.blocos_container.pack(fill="x", pady=(0, 8))

        helper = ctk.CTkFrame(frm, fg_color="transparent")
        helper.pack(fill="x", pady=(6, 10))
        PrimaryButton(helper, text="Adicionar Bloco", command=self._on_add_block, width=190).pack(side="left", padx=(0, 8))
        GhostButton(helper, text="Resetar Blocos", command=lambda: self._on_reset_blocks("single", []), width=130).pack(side="left")

        # Footer
        footer = ctk.CTkFrame(parent, fg_color="transparent", height=56)
        footer.pack(side="bottom", fill="x", pady=(6, 8))
        footer.pack_propagate(False)

        GhostButton(footer, text="Cancelar", command=self._fechar, width=140).pack(side="left", padx=(12, 6), pady=10)
        self._btn_publicar = PrimaryButton(footer, text="Publicar", command=self._on_save, width=140)
        self._btn_publicar.pack(side="right", padx=(12, 6), pady=10)

        # Bindings para preview
        self._bind_preview_updates()

    def _build_preview(self, parent):
        ctk.CTkLabel(parent, text="Pré-visualização",
                     font=themed_font("h3", "bold"),
                     text_color=AVISOS_COLORS["text"]).pack(anchor="nw", pady=(6, 6), padx=6)

        self.preview_area = Card(parent, elevated=True)
        self.preview_area.pack(fill="both", expand=True, padx=8, pady=6)

        self._prev_title = ctk.CTkLabel(self.preview_area.body, text="Título da Publicação",
                                         font=themed_font("h3", "bold"), text_color=AVISOS_COLORS["text"])
        self._prev_title.pack(anchor="nw", pady=(14, 6), padx=14)

        self._prev_author = ctk.CTkLabel(self.preview_area.body, text="Analista SerPleno",
                                          font=themed_font("overline"), text_color=AVISOS_COLORS["text_muted"])
        self._prev_author.pack(anchor="nw", padx=14)

        self._prev_content = ctk.CTkLabel(self.preview_area.body,
                                           text="O conteúdo aparecerá aqui enquanto você digita...",
                                           wraplength=260, justify="left",
                                           font=themed_font("body"), text_color=AVISOS_COLORS["text_secondary"])
        self._prev_content.pack(anchor="nw", pady=(10, 8), padx=14)

        self._prev_blocks = ctk.CTkFrame(self.preview_area.body, fg_color="transparent")
        self._prev_blocks.pack(fill="x", padx=14, pady=(6, 12))

    def _bind_preview_updates(self):
        widgets = [
            self.f_titulo.widget, self.f_conteudo.widget,
            self.f_categoria.widget, self.f_autor.widget,
            self.f_local.widget, self.f_link.widget,
            self.f_data_ag.widget, self.f_horario_evento.widget,
            self.f_layout.widget,
        ]
        for w in widgets:
            try:
                w.bind("<KeyRelease>", lambda _: self._update_preview())
            except Exception:
                pass
            try:
                w.bind("<<ComboboxSelected>>", lambda _: self._update_preview())
            except Exception:
                pass

    # ── ações públicas ────────────────────────────────────────────────────────
    def show(self):
        self.deiconify()
        self.lift()
        try:
            self.grab_set()
        except Exception:
            pass
        self._update_preview()

    def close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    # ── callbacks internos ────────────────────────────────────────────────────
    def _fechar(self):
        self.close()
        if self.on_cancel:
            self.on_cancel()

    def _on_save(self):
        payload = {
            "titulo": self.f_titulo.get().strip(),
            "conteudo": self.f_conteudo.get().strip(),
            "categoria": self.f_categoria.get() or "informativo",
            "autor": self.f_autor.get().strip() or None,
            "local_fisico": self.f_local.get().strip() or None,
            "link_externo": self.f_link.get().strip() or None,
            "data_agendamento": self.f_data_ag.get().strip() or None,
            "horario_evento": None,
            "layout": self.f_layout.get() or "single",
            "blocos": self._collect_blocks(),
            "ativo": True,
        }
        he = self.f_horario_evento.get().strip()
        if he:
            try:
                payload["horario_evento"] = datetime.datetime.strptime(he, "%Y-%m-%d %H:%M").isoformat()
            except Exception:
                payload["horario_evento"] = he

        if not payload["titulo"] or (payload["layout"] == "single" and not payload["conteudo"]):
            messagebox.showwarning("Atenção", "Preencha título e conteúdo ou adicione blocos para layout grid.")
            return

        self._btn_publicar.configure(state="disabled")
        self.on_publish(payload, self._on_publish_success, self._on_publish_error)

    def _on_publish_success(self, _):
        try:
            self._btn_publicar.configure(state="normal")
        except Exception:
            pass
        self.close()

    def _on_publish_error(self, err):
        try:
            self._btn_publicar.configure(state="normal")
        except Exception:
            pass
        messagebox.showerror("Erro ao salvar publicação", f"{err.get('message') if isinstance(err, dict) else err}")

    def _on_add_block(self):
        cur = self.f_layout.get() or "single"
        if cur == "single":
            self.f_layout.widget.set("grid-2")
            cur = "grid-2"
        cols = int(cur.split("-")[1])
        existing = [{"titulo": b["title"].get(), "conteudo": b["content"].get("1.0", "end").strip(), "icon": b["icon"].get()}
                    for b in self._block_editors]
        existing.append({"titulo": "", "conteudo": "", "icon": ""})
        self._render_block_editors(cols, existing)
        self._update_preview()

    def _on_reset_blocks(self, layout, existing):
        self._render_block_editors(1 if layout == "single" else int(layout.split("-"))[1], existing)
        self._update_preview()

    def _render_block_editors(self, cols: int, existing: list[dict[str, str]]):
        for w in self.blocos_container.winfo_children():
            w.destroy()
        self._block_editors: list[dict[str, Any]] = []

        if cols <= 1:
            return

        icons = ["", "phone", "mail", "clock", "calendar", "help-circle",
                 "user", "users", "alert-triangle", "info", "check", "x",
                 "external-link", "link"]

        for i in range(cols):
            ex = existing[i] if existing and i < len(existing) else {}
            card = Card(self.blocos_container)
            card.pack(fill="x", pady=4, padx=4)

            ctk.CTkLabel(card.body, text=f"Bloco #{i + 1} - Título",
                         font=themed_font("body", "bold"), text_color=AVISOS_COLORS["text"]).pack(anchor="w", pady=(6, 0), padx=8)
            entry_t = ctk.CTkEntry(card.body, placeholder_text="Título",
                                   height=32, corner_radius=RADIUS["sm"],
                                   fg_color=AVISOS_COLORS["card_alt"], border_width=1, border_color=AVISOS_COLORS["border"])
            entry_t.pack(fill="x", padx=8, pady=(0, 6))
            entry_t.insert(0, ex.get("titulo", ""))

            ctk.CTkLabel(card.body, text="Conteúdo do Bloco",
                         font=themed_font("body"), text_color=AVISOS_COLORS["text"]).pack(anchor="w", padx=8)
            txt = ctk.CTkTextbox(card.body, height=70, corner_radius=RADIUS["sm"],
                                 fg_color=AVISOS_COLORS["card_alt"], border_width=1, border_color=AVISOS_COLORS["border"])
            txt.pack(fill="x", padx=8, pady=(0, 6))
            txt.insert("1.0", ex.get("conteudo", ""))

            ctk.CTkLabel(card.body, text="Ícone (Lucide)",
                         font=themed_font("body"), text_color=AVISOS_COLORS["text"]).pack(anchor="w", padx=8)
            comb = ctk.CTkComboBox(card.body, values=icons, width=200,
                                   fg_color=AVISOS_COLORS["card_alt"], button_color=AVISOS_COLORS["border"],
                                   dropdown_fg_color=AVISOS_COLORS["card"])
            comb.pack(anchor="w", padx=8, pady=(4, 8))
            comb.set(ex.get("icon", ""))

            row = ctk.CTkFrame(card.body, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=(0, 8))
            ctk.CTkButton(row, text="↑", width=32, height=24, command=lambda f=card: self._move_block(f, -1)).pack(side="left", padx=(0, 4))
            ctk.CTkButton(row, text="↓", width=32, height=24, command=lambda f=card: self._move_block(f, 1)).pack(side="left", padx=(0, 8))
            GhostButton(row, text="Remover", command=lambda f=card: self._remove_block(f), width=90).pack(side="right")

            self._block_editors.append({"frame": card, "title": entry_t, "content": txt, "icon": comb})

    def _move_block(self, frame, direction: int):
        parent = self.blocos_container
        children = list(parent.children.values())
        try:
            idx = children.index(frame)
        except ValueError:
            return
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(children):
            return
        frame.pack_forget()
        if direction < 0:
            children[new_idx].pack_forget()
            children[new_idx].pack(before=frame)
            frame.pack()
        else:
            frame.pack(before=children[new_idx])
        self._update_preview()

    def _remove_block(self, frame):
        frame.destroy()
        self._reindex()
        self._update_preview()

    def _reindex(self):
        new_editors = []
        kids = [w for w in self.blocos_container.winfo_children()]
        for f in kids:
            title = content = icon = None
            for child in f.winfo_children():
                if isinstance(child, ctk.CTkEntry) and title is None:
                    title = child
                if isinstance(child, ctk.CTkTextbox) and content is None:
                    content = child
                if isinstance(child, ctk.CTkComboBox) and icon is None:
                    icon = child
            if title and content and icon:
                new_editors.append({"frame": f, "title": title, "content": content, "icon": icon})
        self._block_editors = new_editors

    def _collect_blocks(self) -> list[dict[str, str]]:
        arr = []
        for be in self._block_editors:
            titulo = be["title"].get().strip()
            conteudo = be["content"].get("1.0", "end").strip()
            icon = be["icon"].get() if hasattr(be["icon"], "get") else ""
            if titulo or conteudo or icon:
                arr.append({"titulo": titulo, "conteudo": conteudo, "icon": icon})
        return arr

    def populate(self, data: dict[str, Any]):
        self.f_titulo.delete(0, "end")
        self.f_titulo.insert(0, data.get("titulo") or data.get("title", "") or "")
        self.f_conteudo.delete("1.0", "end")
        self.f_conteudo.insert("1.0", data.get("conteudo") or data.get("content", "") or "")
        self.f_categoria.widget.set(data.get("categoria") or data.get("category") or "informativo")
        self.f_autor.delete(0, "end")
        self.f_autor.insert(0, data.get("autor") or data.get("author", "") or "")
        self.f_local.delete(0, "end")
        self.f_local.insert(0, data.get("local_fisico", "") or "")
        self.f_link.delete(0, "end")
        self.f_link.insert(0, data.get("link_externo", "") or "")

        dag = data.get("data_agendamento") or ""
        if dag:
            try:
                self.f_data_ag.delete(0, "end")
                self.f_data_ag.insert(0, dag.split("T")[0])
            except Exception:
                self.f_data_ag.delete(0, "end")
                self.f_data_ag.insert(0, dag)
        else:
            self.f_data_ag.delete(0, "end")

        he = data.get("horario_evento") or ""
        if he:
            try:
                dt = he.replace("T", " ").split("+")[0].split("Z")[0][:16]
                self.f_horario_evento.delete(0, "end")
                self.f_horario_evento.insert(0, dt)
            except Exception:
                self.f_horario_evento.delete(0, "end")
                self.f_horario_evento.insert(0, he)
        else:
            self.f_horario_evento.delete(0, "end")

        layout = data.get("layout") or "single"
        self.f_layout.widget.set(layout)
        self._render_block_editors(int(layout.split("-")[1]) if layout.startswith("grid-") else 0,
                                   data.get("blocos") or [])
        self._update_preview()

    def _update_preview(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        title = self.f_titulo.get().strip() or "Título da Publicação"
        author = self.f_autor.get().strip() or "Analista SerPleno"
        content = self.f_conteudo.get().strip() or "O conteúdo aparecerá aqui enquanto você digita..."

        self._prev_title.configure(text=title)
        self._prev_author.configure(text=author)

        layout = self.f_layout.get() or "single"
        if layout == "single":
            self._prev_content.configure(text=content)
            for w in self._prev_blocks.winfo_children():
                w.destroy()
        else:
            self._prev_content.configure(text="")
            for w in self._prev_blocks.winfo_children():
                w.destroy()
            cols = 1
            try:
                cols = int(layout.split("-")[1])
            except Exception:
                cols = 1
            blocks = self._collect_blocks()
            n = min(cols, 4)
            wrap = tk.Frame(self._prev_blocks, bg="white")
            wrap.pack(fill="both", padx=2)
            for i in range(n):
                b = blocks[i] if i < len(blocks) else {"titulo": "", "conteudo": ""}
                frame = tk.Frame(wrap, bg="white", bd=1, relief="flat",
                                 highlightthickness=1, highlightbackground=AVISOS_COLORS["border"])
                frame.grid(row=0, column=i, padx=6, pady=6, sticky="n")
                tk.Label(frame, text=b.get("titulo", ""), font=("Segoe UI", 10, "bold"),
                         bg="white", anchor="w").pack(fill="x", padx=10, pady=(8, 2))
                tk.Label(frame, text=b.get("conteudo", ""), font=("Segoe UI", 9),
                         bg="white", fg=AVISOS_COLORS["text_secondary"],
                         justify="left", wraplength=200).pack(fill="both", padx=10, pady=(0, 10))
            for i in range(n):
                wrap.grid_columnconfigure(i, weight=1)


# ═══════════════════════════════════════════════════════════════════════════════
#  Frame principal
# ═══════════════════════════════════════════════════════════════════════════════
class QuadroAvisosFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=AVISOS_COLORS["bg"])
        self.app = app
        self.pack(fill="both", expand=True)

        self.posts: list[dict[str, Any]] = []
        self.editing_post: dict[str, Any] | None = None
        self._modal: PublicacaoModal | None = None
        self._modal_loading = False

        self._build_header()
        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=20)

        self.carregar_avisos_async()

    # ── header -----------------------------------------------------------------
    def _build_header(self):
        header = PageHeader(
            self,
            title="Quadro de Avisos",
            subtitle="Gerencie publicações e comunicados do sistema",
        )
        header.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 10))

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right")
        PrimaryButton(actions, text="+ Novo Aviso", command=self._abrir_modal_novo, width=150).pack(side="right")

    # ── thread helper ----------------------------------------------------------
    def _run_in_thread(self, fn, callback=None, err_callback=None):
        def _worker():
            try:
                res = fn()
                if callback:
                    self.after(0, lambda r=res: callback(r))
            except Exception as e:
                logger.exception("Erro em thread: %s", e)
                if err_callback:
                    self.after(0, lambda exc=e: err_callback(exc))
                else:
                    self.after(0, lambda exc=e: messagebox.showerror("Erro", str(exc)))

        threading.Thread(target=_worker, daemon=True).start()

    # ── carregar publicações ---------------------------------------------------
    def carregar_avisos_async(self):
        self._limpar_lista()
        ctk.CTkLabel(self.lista, text="Carregando publicações...",
                     text_color=AVISOS_COLORS["text_muted"]).pack(pady=12)

        self._run_in_thread(
            servico_mural.listar_mensagens,
            callback=self._on_load_success,
            err_callback=self._on_load_error,
        )

    def _limpar_lista(self):
        try:
            if self.lista.winfo_exists():
                for w in self.lista.winfo_children():
                    w.destroy()
        except Exception:
            pass

    def _on_load_success(self, res):
        self._limpar_lista()
        posts = self._parse_posts(res)
        self.posts = posts

        if not posts:
            EmptyState(self.lista, icon="📭", title="Nenhuma publicação encontrada",
                       subtitle="Crie um novo aviso para começar").pack(pady=20)
            return

        for post in reversed(posts):
            if not isinstance(post, dict):
                continue
            self._criar_card(
                post.get("id"),
                post.get("titulo") or post.get("title") or "(sem título)",
                post.get("conteudo") or post.get("content") or "",
                post.get("autor") or post.get("author") or "Sistema",
                post.get("publicado_em") or post.get("created_at") or "",
            )

    def _on_load_error(self, e):
        self._limpar_lista()
        ctk.CTkLabel(self.lista, text=f"Erro ao carregar avisos: {e}",
                     text_color=AVISOS_COLORS["danger"]).pack(pady=12)

    def _parse_posts(self, res) -> list[dict[str, Any]]:
        if isinstance(res, dict):
            if res.get("success") is False:
                return []
            if "data" in res and isinstance(res["data"], list):
                return res["data"]
            if res.get("id"):
                return [res]
        if isinstance(res, list):
            return res
        return []

    # ── card ------------------------------------------------------------------
    def _criar_card(self, aviso_id, titulo, descricao, autor, data):
        card = Card(self.lista, elevated=True)
        card.pack(fill="x", pady=(0, 12))

        top = ctk.CTkFrame(card.body, fg_color="transparent")
        top.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(top, text=escape_html(titulo or ""),
                     font=themed_font("h3", "bold"),
                     text_color=AVISOS_COLORS["text"]).pack(side="left")

        btns = ctk.CTkFrame(top, fg_color="transparent")
        btns.pack(side="right")
        GhostButton(btns, text="Editar", command=lambda i=aviso_id: self._on_edit(i), width=90).pack(side="left", padx=6)
        GhostButton(btns, text="Excluir", command=lambda i=aviso_id: self._on_delete(i), width=90).pack(side="left")

        if descricao:
            ctk.CTkLabel(card.body, text=escape_html(descricao or ""),
                         wraplength=780, justify="left",
                         font=themed_font("body"), text_color=AVISOS_COLORS["text_secondary"]).pack(anchor="w", pady=(0, 10))

        footer = ctk.CTkFrame(card.body, fg_color="transparent")
        footer.pack(fill="x")
        ctk.CTkLabel(footer, text=f"{escape_html(autor)} • {escape_html(data)}",
                     font=themed_font("overline"),
                     text_color=AVISOS_COLORS["text_muted"]).pack(side="left")

    # ── editar ----------------------------------------------------------------
    def _on_edit(self, post_id):
        def _fetch():
            return servico_mural.obter_mensagem(post_id)

        def _on_res(res):
            if isinstance(res, dict) and res.get("success") is False:
                messagebox.showerror("Erro", f"Erro ao carregar publicação: {res.get('message')}")
                return
            data = res.get("data", res) if isinstance(res, dict) else res
            if not isinstance(data, dict):
                messagebox.showerror("Erro", "Resposta inválida do servidor.")
                return
            self.editing_post = data
            self._abrir_modal_edicao(data)

        def _on_err(e):
            messagebox.showerror("Erro", f"Erro ao carregar publicação: {e}")

        self._run_in_thread(_fetch, callback=_on_res, err_callback=_on_err)

    # ── excluir ---------------------------------------------------------------
    def _on_delete(self, post_id):
        if not messagebox.askyesno("Confirmação", "Excluir esta publicação permanentemente?"):
            return

        def _on_ok(_):
            self.carregar_avisos_async()

        def _on_fail(err):
            messagebox.showerror("Erro ao excluir", f"{err.get('message') if isinstance(err, dict) else err}")

        self._run_in_thread(
            lambda: servico_mural.deletar_mensagem(post_id),
            callback=_on_ok,
            err_callback=_on_fail,
        )

    # ── modal ----------------------------------------------------------------
    def _abrir_modal_novo(self):
        self.editing_post = None
        self._open_modal()

    def _abrir_modal_edicao(self, data: dict[str, Any]):
        self._open_modal(populate_data=data)

    def _open_modal(self, populate_data: dict[str, Any] | None = None):
        if self._modal is not None:
            try:
                self._modal.close()
            except Exception:
                pass

        self._modal = PublicacaoModal(
            self,
            on_publish=self._on_modal_publish,
            on_cancel=self._on_modal_cancel,
        )

        if populate_data:
            self._modal.populate(populate_data)

        self._modal.show()

    def _on_modal_publish(self, payload, on_success, on_error):
        def _send():
            if self.editing_post and self.editing_post.get("id"):
                return servico_mural.atualizar_mensagem(self.editing_post["id"], payload)
            return servico_mural.criar_mensagem(payload)

        def _cb(res):
            if isinstance(res, dict) and res.get("success") is False:
                on_error(res)
                messagebox.showerror("Erro", f"Erro ao publicar: {res.get('message')}")
                return
            on_success(res)
            self.carregar_avisos_async()

        def _err(e):
            on_error({"success": False, "message": str(e)})
            messagebox.showerror("Erro", f"Erro ao publicar: {e}")

        self._run_in_thread(_send, callback=_cb, err_callback=_err)

    def _on_modal_cancel(self):
        self._modal = None
        self.editing_post = None

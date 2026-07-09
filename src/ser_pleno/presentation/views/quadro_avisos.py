from __future__ import annotations

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import datetime
import html
import threading
import logging
from typing import Any

from ser_pleno.infrastructure.api.mural import servico_mural
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font
from ser_pleno.ui.theme_extensions import extend_theme, spacing
from ser_pleno.presentation.components.icons import IconLabel, ICONS
from ser_pleno.presentation.components.ui_components import BaseModal

logger = logging.getLogger("apps.desktop")


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Design tokens —” herdando do THEME global
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
Q = extend_theme(THEME, {
    "input_border":     "#E5E7EB",
    "text_light":       "#9CA3AF",
    "danger_hover":     "#B91C1C",
    "block_bg":         "#F5F3FF",
    "block_border":     "#C7D2FE",
    "card_radius":      RADIUS["card"],
    "card_bg":          THEME["surface"],
    "card_border":      THEME["border"],
    "modal_bg":         THEME["surface"],
    "preview_bg":       THEME["bg_alt"],
    "cat": {
        "informativo": ("#4F46E5", "#EEF2FF"),
        "aviso":       ("#D97706", "#FEF3C7"),
        "aula":        ("#059669", "#D1FAE5"),
        "urgente":     ("#DC2626", "#FEE2E2"),
        "evento":      ("#7C3AED", "#EDE9FE"),
    },
})

_CAT_DEFAULT = ("#4F46E5", "#EEF2FF")


# ——————————————————————————————————————————————————————————————————————————————
#  Helpers
# ——————————————————————————————————————————————————————————————————————————————
def escape_html(s: str | None) -> str:
    return html.escape(str(s)) if s else ""


def _chip(parent, text: str, cat: str) -> ctk.CTkFrame:
    color, soft = Q["cat"].get(cat, _CAT_DEFAULT)
    f = ctk.CTkFrame(parent, fg_color=soft, corner_radius=7)
    ctk.CTkLabel(f, text=text.capitalize(),
                 font=font(size=11, weight="bold"),
                  text_color=color).pack(padx=spacing("sm"), pady=spacing("xs"))
    return f


def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=Q["divider"]).pack(fill="x")


def _card(parent, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(parent, fg_color=Q["card_bg"],
                        corner_radius=Q["card_radius"],
                        border_width=1, border_color=Q["card_border"], **kw)


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  FormField —“ campo de formulário redesenhado
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class FormField(ctk.CTkFrame):
    def __init__(self, parent, label: str, placeholder: str = "",
                 icon: str = "", password: bool = False,
                 initial: str = "", multiline: bool = False,
                 height: int | None = None, values: list[str] | None = None):
        super().__init__(parent, fg_color="transparent")

        self._label = ctk.CTkLabel(
            self, text=label,
            font=font(size=12),
            text_color=Q["text_muted"], anchor="w",
        )
        self._label.pack(fill="x", pady=(0, 4))

        self._box = ctk.CTkFrame(
            self, corner_radius=10,
            fg_color=Q["input_bg"],
            border_width=1, border_color=Q["input_border"],
        )
        self._box.pack(fill="x")
        self._box.grid_columnconfigure(1, weight=1)

        if icon and not values:
            ctk.CTkLabel(
                self._box, text=icon,
                font=font(size=14),
                text_color=Q["text_light"], width=34,
            ).grid(row=0, column=0, padx=(8, 0), pady=8)

        col = 1 if (icon and not values) else 0
        colspan = 1

        if values is not None:
            self.widget = ctk.CTkComboBox(
                self._box, values=values,
                fg_color=Q["input_bg"], border_width=0,
                button_color=Q["accent"],
                button_hover_color=Q["accent_hover"],
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color=Q["text"],
                font=font(size=13),
                height=height or 38,
            )
            if initial:
                self.widget.set(initial)
            self.widget.grid(row=0, column=col, columnspan=colspan,
                             sticky="ew", padx=(8 if col == 0 else 4, 8), pady=4)
        elif multiline:
            self.widget = ctk.CTkTextbox(
                self._box, height=height or 110,
                fg_color=Q["input_bg"], border_width=0,
                font=font(size=13),
                corner_radius=0, text_color=Q["text"],
            )
            if initial:
                self.widget.insert("1.0", initial)
            self.widget.grid(row=0, column=col, columnspan=colspan,
                             sticky="nsew", padx=(8 if col == 0 else 4, 8), pady=4)
        else:
            self.widget = ctk.CTkEntry(
                self._box,
                placeholder_text=placeholder,
                placeholder_text_color=Q["text_light"],
                fg_color=Q["input_bg"], border_width=0,
                text_color=Q["text"],
                font=font(size=13),
                height=height or 40,
                show="●" if password else "",
            )
            if initial:
                self.widget.insert(0, initial)
            self.widget.grid(row=0, column=col, columnspan=colspan,
                             sticky="ew", padx=(8 if col == 0 else 4, 8), pady=4)

        self.widget.bind("<FocusIn>",  self._on_focus_in)
        self.widget.bind("<FocusOut>", self._on_focus_out)

    # API —————————————————————————————————————————————————————————————————————
    def get(self) -> str:
        if isinstance(self.widget, ctk.CTkTextbox):
            return self.widget.get("1.0", "end").strip()
        return self.widget.get()

    def insert(self, index, value: str):
        if isinstance(self.widget, ctk.CTkTextbox):
            self.widget.insert("1.0" if index in (0, "end", "0") else index, value)
        else:
            self.widget.insert(0, value)

    def delete(self, first, last=None):
        if isinstance(self.widget, ctk.CTkTextbox):
            self.widget.delete("1.0", "end")
        else:
            self.widget.delete(0, "end")

    def set_error(self, msg: str = ""):
        self._box.configure(border_color=Q["input_error"],
                            fg_color=Q["input_error_soft"])
        self._label.configure(text_color=Q["danger"])

    def clear_state(self):
        self._box.configure(border_color=Q["input_border"],
                            fg_color=Q["input_bg"])
        self._label.configure(text_color=Q["text_muted"])

    def _on_focus_in(self, _=None):
        self._box.configure(border_color=Q["input_focus"],
                            fg_color="#FFFFFF")
        self._label.configure(text_color=Q["accent"])

    def _on_focus_out(self, _=None):
        self._box.configure(border_color=Q["input_border"],
                            fg_color=Q["input_bg"])
        self._label.configure(text_color=Q["text_muted"])


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  PublicacaoModal
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class PublicacaoModal(BaseModal):
    def __init__(self, parent, on_publish, on_cancel, W=980, H=700):
        self.on_publish = on_publish
        self.on_cancel  = on_cancel
        self._block_editors: list[dict[str, Any]] = []
        super().__init__(parent, title="Publicação do Mural", width=W, height=H)
        self.configure(fg_color=Q["modal_bg"])
        self._build(W, H)

    def _build(self, W, H):
        # —— Banner de topo ——————————————————————————————————————————————————
        banner = ctk.CTkFrame(self, fg_color=Q["accent_soft"],
                              corner_radius=0, height=62)
        banner.pack(fill="x"); banner.pack_propagate(False)

        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=spacing("xl"))

        ib = ctk.CTkFrame(bi, width=38, height=38, corner_radius=10, fg_color=Q["accent"])
        ib.pack(side="left", padx=(0, 12)); ib.pack_propagate(False)
        ctk.CTkLabel(ib, text=ICONS["chart"],
                     font=font(size=17)).place(relx=0.5, rely=0.5, anchor="center")

        ts = ctk.CTkFrame(bi, fg_color="transparent")
        ts.pack(side="left")
        ctk.CTkLabel(ts, text="Nova Publicação",
                     font=font(size=14, weight="bold"),
                     text_color=Q["accent"]).pack(anchor="w")
        ctk.CTkLabel(ts, text="Formulário à esquerda · pré-visualização à direita",
                     font=font(size=10),
                     text_color=Q["text_muted"]).pack(anchor="w")

        # Botão fechar
        ctk.CTkButton(bi, text=ICONS["close"], width=32, height=32, corner_radius=8,
                      fg_color=Q["card_bg"], hover_color=THEME["border_strong"],
                      text_color=Q["text_muted"],
                      font=font(size=13),
                      command=self._fechar).pack(side="right")

        # —— Divisor —————————————————————————————————————————————————————————
        ctk.CTkFrame(self, height=1, fg_color=Q["divider"]).pack(fill="x")

        # —— Corpo: esquerda + direita ————————————————————————————————————————
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=6)
        body.grid_columnconfigure(1, weight=4)
        body.grid_rowconfigure(0, weight=1)

        left  = ctk.CTkFrame(body, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew")

        sep = ctk.CTkFrame(body, width=1, fg_color=Q["divider"])
        sep.grid(row=0, column=1, sticky="ns", padx=0)
        # trick: a thin frame as vertical divider

        right = ctk.CTkFrame(body, fg_color=Q["preview_bg"])
        right.grid(row=0, column=2, sticky="nsew")
        body.grid_columnconfigure(2, weight=3)

        self._build_form(left)
        self._build_preview(right)

    def _build_form(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                        scrollbar_button_color="#D1D5DB")
        scroll.pack(fill="both", expand=True, padx=spacing("xl"), pady=spacing("md"))

        self.f_titulo   = FormField(scroll, f"{ICONS['chart']}Título", placeholder="Título da publicação")
        self.f_titulo.pack(fill="x", pady=(0, 10))

        self.f_conteudo = FormField(scroll, f"{ICONS['file']}  Conteúdo",
                                    placeholder="Conteúdo da publicação",
                                    multiline=True, height=110)
        self.f_conteudo.pack(fill="x", pady=(0, 10))

        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        row1.grid_columnconfigure((0, 1), weight=1)

        self.f_categoria = FormField(row1, f"{ICONS['pin']}  Categoria",
                                     values=["informativo","aviso","aula","urgente","evento"],
                                     initial="informativo")
        self.f_categoria.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.f_autor = FormField(row1, f"{ICONS['view']}  Autor", placeholder="Nome do autor")
        self.f_autor.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))
        row2.grid_columnconfigure((0, 1), weight=1)

        self.f_local = FormField(row2, f"{ICONS['location']} Local", placeholder="Ex: Auditório")
        self.f_local.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.f_link  = FormField(row2, f"{ICONS['search']}  Link externo", placeholder="https://...")
        self.f_link.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        row3 = ctk.CTkFrame(scroll, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 10))
        row3.grid_columnconfigure((0, 1), weight=1)

        self.f_data_ag = FormField(row3, f"{ICONS['calendar']}  Agendamento", placeholder="YYYY-MM-DD")
        self.f_data_ag.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.f_horario_evento = FormField(row3, f"{ICONS['chart']}  Horário evento",
                                          placeholder="YYYY-MM-DD HH:MM")
        self.f_horario_evento.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.f_layout = FormField(scroll, f"{ICONS['layout']}  Layout",
                                  values=["single","grid-2","grid-3","grid-4"],
                                  initial="single")
        self.f_layout.pack(fill="x", pady=(0, 10))

        # Blocos
        ctk.CTkLabel(scroll, text="Blocos de conteúdo (para layouts grid)",
                     font=font(size=12, weight="bold"),
                     text_color=Q["text"], anchor="w").pack(anchor="w", pady=(4, 6))

        self.blocos_container = ctk.CTkScrollableFrame(
            scroll, fg_color=Q["block_bg"],
            corner_radius=12, border_width=1,
            border_color=Q["block_border"],
            height=180,
            scrollbar_button_color="#C7D2FE",
        )
        self.blocos_container.pack(fill="x", pady=(0, 8))

        blk_btns = ctk.CTkFrame(scroll, fg_color="transparent")
        blk_btns.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            blk_btns, text="+  Adicionar Bloco",
            command=self._on_add_block,
            height=34, corner_radius=9, width=160,
            fg_color=Q["accent_soft"], hover_color=Q["accent"],
            text_color=Q["accent"],
            font=font(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            blk_btns, text="Resetar",
            command=lambda: self._on_reset_blocks("single", []),
            height=34, corner_radius=9, width=100,
            fg_color=Q["divider"], hover_color="#E5E7EB",
            text_color=Q["text_muted"],
            font=font(size=12),
        ).pack(side="left")

        # Rodapé
        ctk.CTkFrame(parent, height=1, fg_color=Q["divider"]).pack(fill="x")
        footer = ctk.CTkFrame(parent, fg_color="transparent", height=60)
        footer.pack(fill="x", padx=spacing("xl")); footer.pack_propagate(False)

        ctk.CTkButton(
            footer, text="Cancelar", command=self._fechar,
            height=38, width=120, corner_radius=10,
            fg_color=Q["divider"], hover_color="#E5E7EB",
            text_color=Q["text_muted"],
            border_width=1, border_color=Q["card_border"],
            font=font(size=12),
        ).pack(side="left", pady=11)

        self._btn_publicar = ctk.CTkButton(
            footer, text=f"{ICONS['check']}  Publicar",
            command=self._on_save,
            height=38, width=140, corner_radius=10,
            fg_color=Q["accent"], hover_color=Q["accent_hover"],
            text_color="white",
            font=font(size=13, weight="bold"),
        )
        self._btn_publicar.pack(side="right", pady=11)

        self._bind_preview_updates()

    def _build_preview(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=spacing("lg"), pady=(spacing("md"), spacing("item_gap")))

        ctk.CTkLabel(hdr, text="Pré-visualização",
                     font=font(size=13, weight="bold"),
                     text_color=Q["text"]).pack(side="left")

        ctk.CTkFrame(parent, height=1, fg_color=Q["divider"]).pack(fill="x", padx=spacing("lg"))

        prev_card = ctk.CTkFrame(
            parent,
            fg_color=Q["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=Q["card_border"],
        )
        prev_card.pack(fill="both", expand=True, padx=spacing("lg"), pady=spacing("md"))

        inner = ctk.CTkFrame(prev_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("lg"), pady=spacing("md"))

        # Chip de categoria (atualizado dinamicamente)
        self._prev_cat_frame = ctk.CTkFrame(inner, fg_color=Q["accent_soft"], corner_radius=6)
        self._prev_cat_frame.pack(anchor="w", pady=(0, spacing("item_gap")))
        self._prev_cat_lbl = ctk.CTkLabel(
            self._prev_cat_frame, text="Informativo",
            font=font(size=10, weight="bold"),
            text_color=Q["accent"],
        )
        self._prev_cat_lbl.pack(padx=spacing("sm"), pady=spacing("xs"))

        self._prev_title = ctk.CTkLabel(
            inner, text="Título da Publicação",
            font=font(size=14, weight="bold"),
            text_color=Q["text"], anchor="w", wraplength=260,
        )
        self._prev_title.pack(anchor="w", pady=(0, 4))

        self._prev_author = ctk.CTkLabel(
            inner, text="Analista SerPleno",
            font=font(size=10),
            text_color=Q["text_light"], anchor="w",
        )
        self._prev_author.pack(anchor="w", pady=(0, 8))

        ctk.CTkFrame(inner, height=1, fg_color=Q["divider"]).pack(fill="x", pady=(0, 8))

        self._prev_content = ctk.CTkLabel(
            inner,
            text="O conteúdo aparecerá aqui enquanto você digita...",
            wraplength=260, justify="left",
            font=font(size=12),
            text_color=Q["text_muted"], anchor="w",
        )
        self._prev_content.pack(anchor="w")

        self._prev_blocks = ctk.CTkFrame(inner, fg_color="transparent")
        self._prev_blocks.pack(fill="x", pady=(8, 0))

    def _bind_preview_updates(self):
        for w in [self.f_titulo.widget, self.f_conteudo.widget,
                  self.f_categoria.widget, self.f_autor.widget,
                  self.f_local.widget, self.f_link.widget,
                  self.f_data_ag.widget, self.f_horario_evento.widget,
                  self.f_layout.widget]:
            try:
                w.bind("<KeyRelease>",        lambda _: self._update_preview())
                w.bind("<<ComboboxSelected>>", lambda _: self._update_preview())
            except Exception:
                pass

    # —— Públicos ——————————————————————————————————————————————————————————————
    def show(self):
        self.deiconify(); self.lift()
        try: self.grab_set()
        except Exception: pass
        self._update_preview()

    def close(self):
        try: self.grab_release()
        except Exception: pass
        try: self.destroy()
        except Exception: pass

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

        for attr, key in [("f_data_ag", "data_agendamento"),
                          ("f_horario_evento", "horario_evento")]:
            raw = data.get(key) or ""
            field = getattr(self, attr)
            field.delete(0, "end")
            if raw:
                try:
                    val = raw.replace("T", " ").split("+")[0].split("Z")[0][:16]
                    field.insert(0, val)
                except Exception:
                    field.insert(0, raw)

        layout = data.get("layout") or "single"
        self.f_layout.widget.set(layout)
        cols = int(layout.split("-")[1]) if layout.startswith("grid-") else 0
        self._render_block_editors(cols, data.get("blocos") or [])
        self._update_preview()

    # —— Callbacks internos ————————————————————————————————————————————————————
    def _fechar(self):
        self.close()
        if self.on_cancel:
            self.on_cancel()

    def _on_save(self):
        payload = {
            "titulo":         self.f_titulo.get().strip(),
            "conteudo":       self.f_conteudo.get().strip(),
            "categoria":      self.f_categoria.get() or "informativo",
            "autor":          self.f_autor.get().strip() or None,
            "local_fisico":   self.f_local.get().strip() or None,
            "link_externo":   self.f_link.get().strip() or None,
            "data_agendamento": self.f_data_ag.get().strip() or None,
            "horario_evento": None,
            "layout":         self.f_layout.get() or "single",
            "blocos":         self._collect_blocks(),
            "ativo":          True,
        }
        he = self.f_horario_evento.get().strip()
        if he:
            try:
                payload["horario_evento"] = datetime.datetime.strptime(
                    he, "%Y-%m-%d %H:%M").isoformat()
            except Exception:
                payload["horario_evento"] = he

        if not payload["titulo"] or (payload["layout"] == "single" and not payload["conteudo"]):
            messagebox.showwarning("Atenção", "Preencha título e conteúdo.")
            return

        self._btn_publicar.configure(state="disabled")
        self.on_publish(payload, self._on_publish_success, self._on_publish_error)

    def _on_publish_success(self, _):
        try: self._btn_publicar.configure(state="normal")
        except Exception: pass
        self.close()

    def _on_publish_error(self, err):
        try: self._btn_publicar.configure(state="normal")
        except Exception: pass
        messagebox.showerror("Erro", f"{err.get('message') if isinstance(err, dict) else err}")

    # —— Blocos ————————————————————————————————————————————————————————————————
    def _on_add_block(self):
        cur = self.f_layout.get() or "single"
        if cur == "single":
            self.f_layout.widget.set("grid-2"); cur = "grid-2"
        cols = int(cur.split("-")[1])
        existing = [{"titulo": b["title"].get(),
                     "conteudo": b["content"].get("1.0", "end").strip(),
                     "icon": b["icon"].get()} for b in self._block_editors]
        existing.append({"titulo": "", "conteudo": "", "icon": ""})
        self._render_block_editors(cols, existing)
        self._update_preview()

    def _on_reset_blocks(self, layout, existing):
        self._render_block_editors(0, [])
        self._update_preview()

    def _render_block_editors(self, cols: int, existing: list[dict]):
        for w in self.blocos_container.winfo_children():
            w.destroy()
        self._block_editors = []
        if cols <= 1:
            return

        icons = ["", "phone", "mail", "clock", "calendar", "help-circle",
                 "user", "users", "alert-triangle", "info", "check", "x",
                 "external-link", "link"]

        for i in range(cols):
            ex = existing[i] if existing and i < len(existing) else {}

            card = ctk.CTkFrame(
                self.blocos_container,
                fg_color=Q["card_bg"],
                corner_radius=10, border_width=1,
                border_color=Q["block_border"],
            )
            card.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))

            hdr = ctk.CTkFrame(card, fg_color=Q["block_bg"],
                               corner_radius=0, height=30)
            hdr.pack(fill="x"); hdr.pack_propagate(False)
            ctk.CTkLabel(hdr, text=f"  Bloco #{i + 1}",
                         font=font(size=11, weight="bold"),
                         text_color=Q["accent"]).pack(side="left", pady=spacing("sm"))

            body = ctk.CTkFrame(card, fg_color="transparent")
            body.pack(fill="x", padx=spacing("md"), pady=spacing("md"))

            ctk.CTkLabel(body, text="Título",
                         font=font(size=11),
                         text_color=Q["text_muted"], anchor="w").pack(anchor="w")
            entry_t = ctk.CTkEntry(body, height=34, corner_radius=8,
                                   fg_color=Q["input_bg"], border_width=1,
                                   border_color=Q["input_border"],
                                   text_color=Q["text"],
                                   placeholder_text="Título do bloco",
                                   placeholder_text_color=Q["text_light"],
                                   font=font(size=12))
            entry_t.pack(fill="x", pady=(2, 8))
            entry_t.insert(0, ex.get("titulo", ""))

            ctk.CTkLabel(body, text="Conteúdo",
                         font=font(size=11),
                         text_color=Q["text_muted"], anchor="w").pack(anchor="w")
            txt = ctk.CTkTextbox(body, height=60, corner_radius=8,
                                 fg_color=Q["input_bg"], border_width=1,
                                 border_color=Q["input_border"],
                                 text_color=Q["text"],
                                 font=font(size=12))
            txt.pack(fill="x", pady=(2, 8))
            txt.insert("1.0", ex.get("conteudo", ""))

            ctk.CTkLabel(body, text="Ícone",
                         font=font(size=11),
                         text_color=Q["text_muted"], anchor="w").pack(anchor="w")
            comb = ctk.CTkComboBox(body, values=icons, width=200,
                                   fg_color=Q["input_bg"],
                                   button_color=Q["accent"],
                                   button_hover_color=Q["accent_hover"],
                                   dropdown_fg_color="#FFFFFF",
                                   dropdown_text_color=Q["text"],
                                   font=font(size=12))
            comb.pack(anchor="w", pady=(2, 8))
            comb.set(ex.get("icon", ""))

            acts = ctk.CTkFrame(body, fg_color="transparent")
            acts.pack(fill="x")
            for txt_btn, cmd in [("â†‘", lambda f=card: self._move_block(f, -1)),
                                  ("â†“", lambda f=card: self._move_block(f,  1))]:
                ctk.CTkButton(acts, text=txt_btn, width=30, height=28,
                              corner_radius=7, fg_color=Q["accent_soft"],
                              hover_color=Q["accent"], text_color=Q["accent"],
                              font=font(size=12, weight="bold"),
                              command=cmd).pack(side="left", padx=(0, 4))
            ctk.CTkButton(acts, text="Remover",
                          command=lambda f=card: self._remove_block(f),
                          height=28, width=90, corner_radius=7,
                          fg_color=Q["danger_soft"], hover_color=Q["danger_hover"],
                          text_color=Q["danger"],
                          font=font(size=11, weight="bold")).pack(side="right")

            self._block_editors.append({"frame": card, "title": entry_t,
                                        "content": txt, "icon": comb})

    def _move_block(self, frame, direction: int):
        parent   = self.blocos_container
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
        for f in self.blocos_container.winfo_children():
            title = content = icon = None
            for child in f.winfo_children():
                if isinstance(child, ctk.CTkEntry)   and title   is None: title   = child
                if isinstance(child, ctk.CTkTextbox) and content is None: content = child
                if isinstance(child, ctk.CTkComboBox)and icon    is None: icon    = child
            if title and content and icon:
                new_editors.append({"frame": f, "title": title,
                                    "content": content, "icon": icon})
        self._block_editors = new_editors

    def _collect_blocks(self) -> list[dict]:
        arr = []
        for be in self._block_editors:
            t = be["title"].get().strip()
            c = be["content"].get("1.0", "end").strip()
            i = be["icon"].get() if hasattr(be["icon"], "get") else ""
            if t or c or i:
                arr.append({"titulo": t, "conteudo": c, "icon": i})
        return arr

    def _update_preview(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        title   = self.f_titulo.get().strip()   or "Título da Publicação"
        author  = self.f_autor.get().strip()     or "Analista SerPleno"
        content = self.f_conteudo.get().strip()  or "O conteúdo aparecerá aqui..."
        cat     = self.f_categoria.get()         or "informativo"

        self._prev_title.configure(text=title)
        self._prev_author.configure(text=author)

        # Chip de categoria
        color, soft = Q["cat"].get(cat, _CAT_DEFAULT)
        self._prev_cat_frame.configure(fg_color=soft)
        self._prev_cat_lbl.configure(text=cat.capitalize(), text_color=color)

        layout = self.f_layout.get() or "single"
        if layout == "single":
            self._prev_content.configure(text=content)
            for w in self._prev_blocks.winfo_children():
                w.destroy()
        else:
            self._prev_content.configure(text="")
            for w in self._prev_blocks.winfo_children():
                w.destroy()
            try:
                cols = int(layout.split("-")[1])
            except Exception:
                cols = 1
            blocks = self._collect_blocks()
            wrap = tk.Frame(self._prev_blocks, bg="#F8F7FF")
            wrap.pack(fill="both", padx=spacing("xs"))
            for i in range(min(cols, 4)):
                b = blocks[i] if i < len(blocks) else {}
                f = tk.Frame(wrap, bg="white", bd=1, relief="flat",
                             highlightthickness=1, highlightbackground="#E5E7EB")
                f.grid(row=0, column=i, padx=spacing("xs"), pady=spacing("xs"), sticky="n")
                tk.Label(f, text=b.get("titulo", f"Bloco {i+1}"),
                         font=("Segoe UI", 9, "bold"),
                         bg="white", fg="#111827", anchor="w").pack(
                    fill="x", padx=spacing("sm"), pady=(spacing("sm"), spacing("xs")))
                tk.Label(f, text=b.get("conteudo", ""),
                         font=("Segoe UI", 8), bg="white", fg="#6B7280",
                         justify="left", wraplength=160).pack(
                    fill="both", padx=spacing("sm"), pady=(0, spacing("md")))
                wrap.grid_columnconfigure(i, weight=1)


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  QuadroAvisosFrame —“ frame principal
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class QuadroAvisosFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color=Q["page_bg"])
        self.app = app
        self.pack(fill="both", expand=True)

        self.posts: list[dict[str, Any]] = []
        self.editing_post: dict[str, Any] | None = None
        self._modal: PublicacaoModal | None = None

        self.lista = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color="#C7D2FE",
            scrollbar_button_hover_color="#A5B4FC",
        )
        self.lista.pack(fill="both", expand=True, padx=spacing("xl"), pady=(0, spacing("xl")))

        self.carregar_avisos_async()

    # —— Cabeçalho —————————————————————————————————————————————————————————————
    def _build_header(self):
        raise NotImplementedError

    # —— Thread helper ——————————————————————————————————————————————————————————
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

    # —— Carregar ———————————————————————————————————————————————————————————————
    def carregar_avisos_async(self):
        self._limpar_lista()
        ctk.CTkLabel(self.lista,
                      text=f"{ICONS['hourglass']}  Carregando publicações...",
                     font=font(size=13),
                     text_color=Q["text_muted"]).pack(pady=20)

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
            ctk.CTkLabel(self.lista,
                          text=f"{ICONS['empty']}  Nenhuma publicação encontrada",
                         font=font(size=13),
                         text_color=Q["text_muted"]).pack(pady=30)
            return

        for post in reversed(posts):
            if not isinstance(post, dict):
                continue
            self._criar_card(
                post.get("id"),
                post.get("titulo")    or post.get("title")      or "(sem título)",
                post.get("conteudo")  or post.get("content")    or "",
                post.get("autor")     or post.get("author")     or "Sistema",
                post.get("publicado_em") or post.get("created_at") or "",
                post.get("categoria") or post.get("category")   or "informativo",
            )

    def _on_load_error(self, e):
        self._limpar_lista()
        ctk.CTkLabel(self.lista,
                      text=f"{ICONS['bolt']}   Erro ao carregar avisos: {e}",
                     font=font(size=12),
                     text_color=Q["danger"]).pack(pady=20)

    def _parse_posts(self, res) -> list[dict[str, Any]]:
        if isinstance(res, dict):
            if res.get("success") is False: return []
            if "data" in res and isinstance(res["data"], list): return res["data"]
            if res.get("id"): return [res]
        if isinstance(res, list):
            return res
        return []

    # —— Card de aviso ——————————————————————————————————————————————————————————
    def _criar_card(self, aviso_id, titulo, descricao, autor, data, categoria="informativo"):
        card = _card(self.lista)
        card.pack(fill="x", pady=(0, 12))

        # Barra lateral colorida
        color, _ = Q["cat"].get(categoria, _CAT_DEFAULT)
        ctk.CTkFrame(card, width=4, corner_radius=0,
                     fg_color=color).pack(side="left", fill="y")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=spacing("lg"), pady=spacing("md"))

        # Topo: chip + título + ações
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x", pady=(0, spacing("item_gap")))

        chip_frame = ctk.CTkFrame(top, fg_color=Q["cat"].get(categoria, _CAT_DEFAULT)[1],
                                  corner_radius=6)
        chip_frame.pack(side="left", padx=(0, spacing("md")))
        ctk.CTkLabel(chip_frame, text=categoria.capitalize(),
                     font=font(size=10, weight="bold"),
                     text_color=color).pack(padx=spacing("sm"), pady=spacing("xs"))

        ctk.CTkLabel(top, text=escape_html(titulo or ""),
                     font=font(size=14, weight="bold"),
                     text_color=Q["text"]).pack(side="left")

        # Botões de ação
        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.pack(side="right")

        ctk.CTkButton(
            acts, text=f"{ICONS['edit']}  Editar",
            command=lambda i=aviso_id: self._on_edit(i),
            height=30, width=90, corner_radius=8,
            fg_color=Q["accent_soft"], hover_color=Q["accent"],
            text_color=Q["accent"],
            font=font(size=11, weight="bold"),
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            acts, text=f"{ICONS['delete']}  Excluir",
            command=lambda i=aviso_id: self._on_delete(i),
            height=30, width=90, corner_radius=8,
            fg_color=Q["danger_soft"], hover_color=Q["danger_hover"],
            text_color=Q["danger"],
            font=font(size=11, weight="bold"),
        ).pack(side="left")

        # Conteúdo
        if descricao:
            ctk.CTkLabel(body,
                         text=escape_html(descricao or ""),
                         wraplength=820, justify="left",
                         font=font(size=12),
                         text_color=Q["text_muted"],
                         anchor="w").pack(anchor="w", pady=(0, 10))

        # Rodapé do card
        ctk.CTkFrame(body, height=1, fg_color=Q["divider"]).pack(fill="x", pady=(0, 8))

        footer_row = ctk.CTkFrame(body, fg_color="transparent")
        footer_row.pack(fill="x")

        for icon, val in [(ICONS["view"], autor), (ICONS["chart"], data)]:
            if val:
                lbl_row = ctk.CTkFrame(footer_row, fg_color="transparent")
                lbl_row.pack(side="left", padx=(0, 16))
                ctk.CTkLabel(lbl_row, text=f"{icon}  {escape_html(val)}",
                             font=font(size=11),
                             text_color=Q["text_light"]).pack(side="left")

    # —— Editar / Excluir ———————————————————————————————————————————————————————
    def _on_edit(self, post_id):
        def _fetch(): return servico_mural.obter_mensagem(post_id)
        def _on_res(res):
            if isinstance(res, dict) and res.get("success") is False:
                messagebox.showerror("Erro", str(res.get("message", "")))
                return
            data = res.get("data", res) if isinstance(res, dict) else res
            if not isinstance(data, dict):
                messagebox.showerror("Erro", "Resposta inválida do servidor.")
                return
            self.editing_post = data
            self._abrir_modal_edicao(data)
        def _on_err(e): messagebox.showerror("Erro", str(e))
        self._run_in_thread(_fetch, callback=_on_res, err_callback=_on_err)

    def _on_delete(self, post_id):
        if not messagebox.askyesno("Confirmação",
                                   "Excluir esta publicação permanentemente?"):
            return
        def _on_ok(_): self.carregar_avisos_async()
        def _on_fail(e):
            messagebox.showerror("Erro ao excluir",
                                 f"{e.get('message') if isinstance(e, dict) else e}")
        self._run_in_thread(
            lambda: servico_mural.deletar_mensagem(post_id),
            callback=_on_ok, err_callback=_on_fail,
        )

    # —— Modal ——————————————————————————————————————————————————————————————————
    def _abrir_modal_novo(self):
        self.editing_post = None
        self._open_modal()

    def _abrir_modal_edicao(self, data: dict[str, Any]):
        self._open_modal(populate_data=data)

    def _open_modal(self, populate_data: dict[str, Any] | None = None):
        if self._modal is not None:
            try: self._modal.close()
            except Exception: pass

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
                messagebox.showerror("Erro", str(res.get("message", "")))
                return
            on_success(res)
            self.carregar_avisos_async()

        def _err(e):
            on_error({"success": False, "message": str(e)})
            messagebox.showerror("Erro", str(e))

        self._run_in_thread(_send, callback=_cb, err_callback=_err)

    def _on_modal_cancel(self):
        self._modal = None
        self.editing_post = None


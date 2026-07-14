# -*- coding: utf-8 -*-
"""
icons.py — Sistema centralizado de ícones (SerPleno)
=====================================================

Fonte única da verdade para ícones usados como texto na aplicação.
Antes, emojis eram espalhados como strings literais em dezenas de views;
agora todas as referências passam por este módulo, permitindo:

  - alterar o símbolo de um conceito num único lugar;
  - trocar emoji por imagem/SVG no futuro sem tocar nas views;
  - tipografia e spacing consistentes via componentes dedicados.

Componentes
-----------
- IconLabel      : rótulo inline com ícone + texto opcional.
- IconBadge      : selo circular/quadrado com ícone e fundo semântico.
- IconButton     : botão compacto (só ícone) com tooltip opcional.
- MOOD_EMOJIS    : mapeamento oficial de humores (1..5) — substitui o
                   dicionário corrompido em theme.py.
"""

from __future__ import annotations

from typing import Callable, Optional, Literal

import customtkinter as ctk

from ser_pleno.ui.theme import (
    THEME, SPACING, RADIUS, TYPO, FONT_FAMILY,
    themed_font, font, blend_color, readable_text_color,
)

# ——————————————————————————————————————————————————————————————————————————
#  Dicionário de ícones
# ——————————————————————————————————————————————————————————————————————————
# Chaves semânticas: use estas chaves no código das views.
ICONS: dict[str, str] = {
    "arrow_forward":   "→",
    "arrow_left":      "←",
    "arrow_right":     "→",
    # Ações
    "add":             "➕",
    "edit":            "✏️",
    "delete":          "🗑️",
    "save":            "💾",
    "close":           "✕",
    "clear":           "✕",
    "view":            "👁",
    "download":        "📥",
    "duplicate":       "🗂",
    "send":            "📤",
    "attach":          "📎",
    "emoji":           "😀",
    "settings":        "⚙️",
    "search":          "🔍",
    "notifications":   "🔔",
    "notification":    "🔔",
    "bell":            "🔔",
    "help":            "❓",
    "calendar":        "📅",
    "users":           "👥",
    "user":            "👤",
    "chart":           "📊",
    "analytics":       "📊",
    "document":        "📄",
    "file_text":       "📝",
    "file":            "📄",
    "folder":          "📁",
    "video":           "🎥",
    "audio":           "🎵",
    "spreadsheet":     "📊",
    "presentation":    "📊",
    "zip":             "🗜",
    "code":            "💻",
    "terminal":        "💻",
    "location":        "📍",
    "heart":           "❤️",
    "pin":             "📌",
    "chat":            "💬",
    "message":         "💬",
    "clock":           "🕒",
    "hourglass":       "⏳",
    "check":           "✓",
    "check_circle":    "✅",
    "check_single":    "✓",
    "alert":           "⚡",
    "bolt":            "⚡",
    "priority_high":   "⚠️",
    "hourglass":       "⏳",
    "danger":          "🔴",
    "mail":            "📧",
    "info":            "ℹ️",
    "cake":            "🎂",
    "export":          "📤",
    "import":          "📥",
    "pdf":             "📄",
    "cross":           "✗",
    "status_dot":      "●",
    "empty":           "📋",
    "layout":          "⊞",
    "clip":            "📎",
    "send_plane":      "📫",
    "group":           "👥",
    "mood_good":       "😄",
    "mood_bad":        "😟",
    "mood_neutral":    "😐",
    "lock":            "🔒",
    "key":             "🔑",
    "hide":            "🙈",
    "music":           "🎵",
    "dashboard":       "📊",
    "heart_blue":      "💙",
    "compass":         "🧭",
    "megaphone":       "📢",
    "moon":            "🌙",
    "sun":             "☀️",
    "brain":           "🧠",
}

# ——————————————————————————————————————————————————————————————————————————
#  Emojis de humor (substitui o dict corrompido em theme.py)
# ——————————————————————————————————————————————————————————————————————————
MOOD_EMOJIS: dict[int, str] = {
    1: "😟",
    2: "🙁",
    3: "😐",
    4: "😊",
    5: "😄",
}
MOOD_LABELS: dict[int, str] = {
    1: "Muito triste",
    2: "Triste",
    3: "Neutro",
    4: "Bem",
    5: "Ótimo",
}
MOOD_COLORS: dict[int, str] = {
    1: "danger",
    2: "alto",
    3: "medio",
    4: "success",
    5: "primary",
}


# ——————————————————————————————————————————————————————————————————————————
#  Helpers
# ——————————————————————————————————————————————————————————————————————————
def get_icon(key: str, fallback: str = "") -> str:
    """Retorna o ícone cadastrado ou o fallback se a chave não existir."""
    return ICONS.get(key, fallback)


def icon_text(key: str, fallback: str = "", separator: str = "  ") -> str:
    """Retorna o ícone com separador, útil para rótulos compostos."""
    icon = get_icon(key, fallback)
    return icon if not separator else f"{icon}{separator}"


# ——————————————————————————————————————————————————————————————————————————
#  Componentes
# ——————————————————————————————————————————————————————————————————————————
class IconLabel(ctk.CTkLabel):
    """Rótulo inline que combina ícone + texto opcional com spacing consistente."""

    def __init__(self, parent, icon: str = "", text: str = "",
                 icon_size: Literal["overline", "caption", "body", "h3", "h2"] = "body",
                 text_size: Literal["overline", "caption", "body", "body_sm", "h4", "h3", "h2", "h1", "display"] = "body",
                 color: Optional[str] = None,
                 icon_color: Optional[str] = None,
                 separator: str = "  ",
                 **kwargs):
        display = ""
        if icon:
            display = icon
        if text:
            display = f"{display}{separator}{text}" if display else text

        kwargs.setdefault("text", display)
        kwargs.setdefault("font", themed_font(text_size or "body"))
        kwargs.setdefault("text_color", color or THEME["text"])
        super().__init__(parent, **kwargs)


class IconBadge(ctk.CTkFrame):
    """Selo compacto com ícone centralizado e fundo semântico."""

    def __init__(self, parent, icon: str, size: int = 36,
                 color: Optional[str] = None, variant: str = "soft"):
        color = color or THEME["primary"]
        bg = blend_color(color, 0.18) if variant == "soft" else color
        text_c = readable_text_color(bg) if variant == "soft" else THEME["text_on_primary"]

        super().__init__(parent, fg_color=bg, width=size, height=size,
                         corner_radius=RADIUS["pill"])
        self.pack_propagate(False)

        icon_size = max(14, size // 2)
        ctk.CTkLabel(self, text=icon, font=font(size=icon_size),
                     text_color=text_c).place(relx=0.5, rely=0.5, anchor="center")


class IconButton(ctk.CTkButton):
    """Botão compacto apenas com ícone e tooltip opcional."""

    def __init__(self, parent, icon: str, size: int = 36,
                 command=None, tooltip: str = "", color: Optional[str] = None,
                 hover_color: Optional[str] = None, **kwargs):
        self._tooltip_text = tooltip
        self._tooltip = None

        kwargs.setdefault("text", icon)
        kwargs.setdefault("width", size)
        kwargs.setdefault("height", size)
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", hover_color or THEME["bg_alt"])
        kwargs.setdefault("text_color", color or THEME["text_secondary"])
        kwargs.setdefault("font", font(size=max(16, size // 2)))
        kwargs.setdefault("corner_radius", RADIUS["sm"])
        kwargs.setdefault("cursor", "hand2")
        kwargs.setdefault("border_width", 0)
        super().__init__(parent, command=command, **kwargs)

        if tooltip:
            self._bind_tooltip()

    def _bind_tooltip(self):
        self.bind("<Enter>", self._show_tooltip)
        self.bind("<Leave>", self._hide_tooltip)

    def _show_tooltip(self, _=None):
        if self._tooltip or not self._tooltip_text:
            return
        self._tooltip = ctk.CTkToplevel(self)
        self._tooltip.overrideredirect(True)
        self._tooltip.attributes("-topmost", True)
        lbl = ctk.CTkLabel(
            self._tooltip, text=self._tooltip_text,
            font=themed_font("caption", "bold"),
            text_color=THEME["text_on_primary"], fg_color=THEME["overlay"],
            corner_radius=RADIUS["xs"], padx=10, pady=6,
        )
        lbl.pack()
        x = self.winfo_pointerx() + 14
        y = self.winfo_pointery() + 14
        self._tooltip.geometry(f"+{x}+{y}")

    def _hide_tooltip(self, _=None):
        if self._tooltip:
            try:
                self._tooltip.destroy()
            except Exception:
                pass
            self._tooltip = None

    def destroy(self) -> None:
        self._hide_tooltip()
        super().destroy()

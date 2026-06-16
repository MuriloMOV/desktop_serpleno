import customtkinter as ctk
from tkinter import messagebox
from ui_theme import THEME, SPACING, RADIUS, ELEVATION, TYPO, font, themed_font


# ============================================================
# Componentes visuais reutilizáveis — SerPleno
# ============================================================

class PageHeader(ctk.CTkFrame):
    """Cabeçalho padrão de página com título, subtítulo e área de ações à direita."""

    def __init__(self, parent, title: str, subtitle: str = "", actions: list[ctk.CTkButton] | None = None):
        super().__init__(parent, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        self._build(title, subtitle, actions or [])

    def _build(self, title: str, subtitle: str, actions: list[ctk.CTkButton]) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING["card_pad"], pady=16)

        txt = ctk.CTkFrame(inner, fg_color="transparent")
        txt.pack(side="left", fill="y")
        ctk.CTkLabel(txt, text=title, font=themed_font("h2", "bold"), text_color=THEME["text"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(txt, text=subtitle, font=themed_font("body"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))

        if actions:
            actions_frame = ctk.CTkFrame(inner, fg_color="transparent")
            actions_frame.pack(side="right")
            for btn in actions:
                btn.configure(corner_radius=RADIUS["button"])
                btn.pack(side="left", padx=6)


class SectionHeader(ctk.CTkFrame):
    """Cabeçalho de seção simples, usado antes de cards ou listas."""

    def __init__(self, parent, title: str, subtitle: str = "", action_text: str = "", action_command=None):
        super().__init__(parent, fg_color="transparent")
        self._build(title, subtitle, action_text, action_command)

    def _build(self, title: str, subtitle: str, action_text: str, action_command) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y")
        ctk.CTkLabel(left, text=title, font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(left, text=subtitle, font=themed_font("caption"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))

        if action_text and action_command:
            ctk.CTkButton(
                self,
                text=action_text,
                width=120,
                height=32,
                fg_color=THEME["primary"],
                hover_color=THEME["primary_hover"],
                text_color=THEME["text_on_primary"],
                font=themed_font("caption", "bold"),
                corner_radius=RADIUS["button"],
                command=action_command,
            ).pack(side="right")


class Card(ctk.CTkFrame):
    """Container base padronizado para cards de conteúdo."""

    def __init__(self, parent, title: str = "", padding: tuple[int, int] | None = None):
        super().__init__(
            parent,
            fg_color=THEME["card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
        )
        self._padding = padding or (SPACING["card_pad"], SPACING["card_pad"])
        if title:
            self._build_with_title(title)
        else:
            self._build_empty()

    def _build_with_title(self, title: str) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=self._padding[0], pady=(self._padding[1], 0))
        ctk.CTkLabel(header, text=title, font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")
        ctk.CTkFrame(self, height=1, fg_color=THEME["divider"]).pack(fill="x", padx=self._padding[0], pady=(8, 0))
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=self._padding[0], pady=(8, self._padding[1]))

    def _build_empty(self) -> None:
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=self._padding[0], pady=self._padding[1])

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body


class KPICard(ctk.CTkFrame):
    """Card de indicador KPI com ícone, título e valor em destaque."""

    def __init__(self, parent, title: str, value: str, icon: str, accent: str, trend: str = ""):
        super().__init__(
            parent,
            fg_color=THEME["card"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
        )
        self.accent = accent
        self._build(title, value, icon, trend)

    def _build(self, title: str, value: str, icon: str, trend: str) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        txt = ctk.CTkFrame(content, fg_color="transparent")
        txt.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(txt, text=title, font=themed_font("caption"), text_color=THEME["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(txt, text=value, font=themed_font("h1", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(4, 0))
        if trend:
            ctk.CTkLabel(txt, text=trend, font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))

        icon_bg = _soft_bg(hex_c=self.accent, alpha=0.12)
        ctk.CTkLabel(
            content,
            text=icon,
            font=themed_font("h2"),
            text_color=self.accent,
            fg_color=icon_bg,
            width=52,
            height=52,
            corner_radius=RADIUS["lg"],
        ).pack(side="right")


class PrimaryButton(ctk.CTkButton):
    """Botão primário padronizado."""

    def __init__(self, parent, text: str, command=None, width: int = 140, height: int = 42, icon: str = "", **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_on_primary"],
            font=themed_font("body", "bold"),
            corner_radius=RADIUS["button"],
            **kwargs,
        )
        if icon:
            # Em apps com suporte a imagens, aqui pode-se usar CTkImage com ícone.
            # Mantendo compatibilidade com emoji por enquanto.
            self.configure(text=f"{icon}  {text}")


class SecondaryButton(ctk.CTkButton):
    """Botão secundário / outline."""

    def __init__(self, parent, text: str, command=None, width: int = 120, height: int = 38, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            fg_color="transparent",
            hover_color=THEME["primary_light"],
            text_color=THEME["primary"],
            font=themed_font("body", "bold"),
            corner_radius=RADIUS["button"],
            border_width=1,
            border_color=THEME["primary_soft"],
            **kwargs,
        )


class GhostButton(ctk.CTkButton):
    """Botão fantasma para ações menos relevantes."""

    def __init__(self, parent, text: str, command=None, width: int = 100, height: int = 36, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            fg_color="transparent",
            hover_color=THEME["bg_alt"],
            text_color=THEME["text_secondary"],
            font=themed_font("caption", "bold"),
            corner_radius=RADIUS["button"],
            **kwargs,
        )


class DangerButton(ctk.CTkButton):
    """Botão de ação destrutiva."""

    def __init__(self, parent, text: str, command=None, width: int = 120, height: int = 38, **kwargs):
        super().__init__(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            fg_color=THEME["danger"],
            hover_color=THEME["danger_strong"],
            text_color=THEME["text_on_primary"],
            font=themed_font("body", "bold"),
            corner_radius=RADIUS["button"],
            **kwargs,
        )


class InputField(ctk.CTkFrame):
    """Campo de entrada com rótulo, ícone e estado de foco consistente."""

    def __init__(self, parent, label: str, placeholder: str = "", icon: str = "", password: bool = False):
        super().__init__(parent, fg_color="transparent")
        self._build(label, placeholder, icon, password)

    def _build(self, label: str, placeholder: str, icon: str, password: bool) -> None:
        ctk.CTkLabel(self, text=label, font=themed_font("caption", "bold"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(0, SPACING["label_gap"]))

        inner = ctk.CTkFrame(
            self,
            fg_color=THEME["input_bg"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["input_border"],
            height=42,
        )
        inner.pack(fill="x")
        inner.pack_propagate(False)

        if icon:
            ctk.CTkLabel(inner, text=icon, font=themed_font("body")).pack(side="left", padx=(12, 6))

        self.entry = ctk.CTkEntry(
            inner,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            font=themed_font("body"),
            show="•" if password else "",
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Estado visual de foco
        self.entry.bind("<FocusIn>", lambda e: inner.configure(border_color=THEME["input_border_focus"]))
        self.entry.bind("<FocusOut>", lambda e: inner.configure(border_color=THEME["input_border"]))

    def get(self) -> str:
        return self.entry.get()

    def insert(self, index: str, value: str) -> None:
        self.entry.insert(index, value)

    def delete(self, first: str, last: str | None = None) -> None:
        self.entry.delete(first, last)


class SearchField(ctk.CTkFrame):
    """Campo de busca com ícone e placeholder."""

    def __init__(self, parent, placeholder: str = "Buscar...", command=None):
        super().__init__(parent, fg_color=THEME["bg_alt"], corner_radius=RADIUS["input"], border_width=1, border_color=THEME["border"], height=40)
        self._command = command
        self._build(placeholder)
        self.pack_propagate(False)

    def _build(self, placeholder: str) -> None:
        ctk.CTkLabel(self, text="🔍", font=themed_font("body"), text_color=THEME["text_muted"]).pack(side="left", padx=(12, 8))
        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            font=themed_font("body"),
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 10))
        if self._command:
            self.entry.bind("<KeyRelease>", lambda e: self._command(self.entry.get()))

    def get(self) -> str:
        return self.entry.get()

    def clear(self) -> None:
        self.entry.delete(0, "end")


class Badge(ctk.CTkLabel):
    """Badge numérico ou textual para notificações e status."""

    def __init__(self, parent, text: str, color: str = THEME["danger"], text_color: str = THEME["text_on_primary"]):
        super().__init__(
            parent,
            text=str(text),
            font=themed_font("overline", "bold"),
            text_color=text_color,
            fg_color=color,
            width=20,
            height=20,
            corner_radius=RADIUS["pill"],
        )
        self.pack_propagate(False)


class Pill(ctk.CTkFrame):
    """Pill / tag textual curta."""

    def __init__(self, parent, text: str, color: str = THEME["primary_soft"], text_color: str = THEME["primary"]):
        super().__init__(parent, fg_color=color, corner_radius=RADIUS["pill"])
        ctk.CTkLabel(self, text=text, font=themed_font("overline", "bold"), text_color=text_color).pack(padx=10, pady=3)


class EmptyState(ctk.CTkFrame):
    """Estado vazio padronizado para listas e áreas sem conteúdo."""

    def __init__(self, parent, icon: str, title: str, subtitle: str = "", action_text: str = "", action_command=None):
        super().__init__(parent, fg_color="transparent")
        self._build(icon, title, subtitle, action_text, action_command)

    def _build(self, icon: str, title: str, subtitle: str, action_text: str, action_command) -> None:
        ctk.CTkLabel(self, text=icon, font=themed_font("display")).pack(pady=(20, 10))
        ctk.CTkLabel(self, text=title, font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(pady=(0, 6))
        if subtitle:
            ctk.CTkLabel(self, text=subtitle, font=themed_font("body"), text_color=THEME["text_muted"]).pack(pady=(0, 12))
        if action_text and action_command:
            PrimaryButton(self, text=action_text, command=action_command, width=180).pack(pady=8)


class Divider(ctk.CTkFrame):
    """Linha divisória sutil."""

    def __init__(self, parent):
        super().__init__(parent, height=1, fg_color=THEME["divider"])
        self.pack(fill="x", pady=8)


# ============================================================
# Helpers
# ============================================================

def _soft_bg(hex_c: str, alpha: float) -> str:
    r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
    return f"#{int(r * alpha + 255 * (1 - alpha)):02x}{int(g * alpha + 255 * (1 - alpha)):02x}{int(b * alpha + 255 * (1 - alpha)):02x}"


def blend_color(hex_c: str, alpha: float) -> str:
    return _soft_bg(hex_c, alpha)

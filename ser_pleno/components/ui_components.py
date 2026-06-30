import customtkinter as ctk
from tkinter import messagebox
from ui_theme import (
    THEME, SPACING, RADIUS, ELEVATION, TYPO, ANIMATION, STATUS_COLORS, FONT_FAMILY,
    font, themed_font, mono_font, blend_color, darken, lighten, shift_hue
)
from typing import Optional, Callable, Tuple
import math


class PageHeader(ctk.CTkFrame):
    """Page header with title, subtitle, mega menu button, breadcrumb and action area."""

    def __init__(self, parent, title: str, subtitle: str = "",
                 actions: list[ctk.CTkButton] | None = None,
                 show_breadcrumb: bool = True,
                 breadcrumb_parts: list[str] | None = None):
        super().__init__(parent, fg_color=THEME["surface"], corner_radius=RADIUS["card"],
                         border_width=1, border_color=THEME["border"])
        self._build(title, subtitle, actions or [], show_breadcrumb, breadcrumb_parts)

    def _build(self, title, subtitle, actions, show_breadcrumb, breadcrumb_parts):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 14))

        if show_breadcrumb:
            bc = ctk.CTkFrame(inner, fg_color="transparent")
            bc.pack(anchor="w", pady=(0, 6))
            parts = breadcrumb_parts or ["Home", "Dashboard"]
            for i, part in enumerate(parts):
                ctk.CTkLabel(bc, text=part, font=themed_font("overline"),
                             text_color=THEME["text_disabled"] if i > 0 else THEME["text_secondary"]
                             ).pack(side="left")
                if i < len(parts) - 1:
                    ctk.CTkLabel(bc, text="/", font=themed_font("overline"),
                                 text_color=THEME["text_disabled"]).pack(side="left", padx=6)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        txt = ctk.CTkFrame(top, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(txt, text=title, font=themed_font("h2", "bold"),
                     text_color=THEME["text"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(txt, text=subtitle, font=themed_font("body"),
                         text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))

        if actions:
            rf = ctk.CTkFrame(top, fg_color="transparent")
            rf.pack(side="right")
            for btn in actions:
                btn.configure(corner_radius=RADIUS["button"])
                btn.pack(side="left", padx=6)


class SectionHeader(ctk.CTkFrame):
    """Section header with optional icon, description and action button."""

    def __init__(self, parent, title: str, subtitle: str = "",
                 action_text: str = "", action_command=None,
                 icon: str = ""):
        super().__init__(parent, fg_color="transparent")
        self._build(title, subtitle, action_text, action_command, icon)

    def _build(self, title, subtitle, action_text, action_command, icon):
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y")
        if icon:
            ctk.CTkLabel(left, text=icon, font=themed_font("h3")).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(left, text=title, font=themed_font("h3", "bold"),
                     text_color=THEME["text"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(left, text=subtitle, font=themed_font("body_sm"),
                         text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))

        if action_text and action_command:
            ctk.CTkButton(
                self, text=action_text, width=120, height=32,
                fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                text_color=THEME["text_on_primary"], font=themed_font("caption", "bold"),
                corner_radius=RADIUS["button"], command=action_command
            ).pack(side="right")


class Card(ctk.CTkFrame):
    """Professional card with header/body/footer slots and status bar."""

    def __init__(self, parent, title: str = "", padding: Tuple[int, int] | None = None,
                 elevated: bool = False, status: str | None = None):
        super().__init__(
            parent,
            fg_color=THEME["surface_elevated"] if elevated else THEME["surface"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
        )
        self._padding = padding or (SPACING["card_pad"], SPACING["card_pad"])
        if status:
            self._build_with_status(title, status)
        elif title:
            self._build_with_title(title)
        else:
            self._build_empty()

    def _build_with_title(self, title):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=self._padding[0], pady=(self._padding[1], 0))
        ctk.CTkLabel(header, text=title, font=themed_font("h3", "bold"),
                     text_color=THEME["text"]).pack(side="left")
        ctk.CTkFrame(self, height=1, fg_color=THEME["divider"]).pack(
            fill="x", padx=self._padding[0], pady=(10, 0)
        )
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=self._padding[0], pady=(10, self._padding[1]))

    def _build_with_status(self, title, status):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=self._padding[0], pady=(self._padding[1], 6))
        ctk.CTkLabel(header, text=title, font=themed_font("h3", "bold"),
                     text_color=THEME["text"]).pack(side="left")
        color = STATUS_COLORS.get(status.lower(), STATUS_COLORS["active"])
        status_pill = ctk.CTkFrame(header, fg_color=blend_color(color, 0.12),
                                   corner_radius=RADIUS["pill"], height=24)
        status_pill.pack(side="right", padx=(8, 0))
        status_pill.pack_propagate(False)
        ctk.CTkLabel(status_pill, text=status.capitalize(), font=themed_font("overline", "bold"),
                     text_color=color).pack(padx=10, pady=2)
        ctk.CTkFrame(self, height=1, fg_color=THEME["divider"]).pack(
            fill="x", padx=self._padding[0], pady=(0, 10)
        )
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=self._padding[0], pady=(0, self._padding[1]))

    def _build_empty(self):
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=self._padding[0], pady=self._padding[1])

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body

    @property
    def footer(self):
        if not hasattr(self, "_footer"):
            self._footer = ctk.CTkFrame(self, fg_color="transparent")
            self._footer.pack(fill="x", padx=self._padding[0], pady=(0, self._padding[1]))
        return self._footer


class KPICard(ctk.CTkFrame):
    """KPI card with icon, value, label and optional trend indicator.
    Variants: sm (compact), md (default), lg (prominent).
    """

    _SIZE_MAP = {
        "sm": {"icon": 40, "value": "h3", "title": "caption", "sub": "overline", "pad": 14},
        "md": {"icon": 52, "value": "h1", "title": "body", "sub": "caption", "pad": SPACING["card_pad"]},
        "lg": {"icon": 64, "value": "display", "title": "h3", "sub": "body", "pad": 28},
    }

    def __init__(self, parent, title: str, value: str, icon: str,
                 accent: str = THEME["primary"], trend: str = "",
                 unit: str = "", size: str = "md"):
        if size not in self._SIZE_MAP:
            size = "md"
        self._size_cfg = self._SIZE_MAP[size]
        super().__init__(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
        )
        self.accent = accent
        self._size = size
        self._build(title, value, icon, trend, unit)

    def _build(self, title, value, icon, trend, unit):
        pad = self._size_cfg["pad"]
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=pad, pady=pad)

        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill="x")

        txt = ctk.CTkFrame(row1, fg_color="transparent")
        txt.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(txt, text=title, font=themed_font(self._size_cfg["title"]),
                     text_color=THEME["text_muted"]).pack(anchor="w")

        value_frame = ctk.CTkFrame(txt, fg_color="transparent")
        value_frame.pack(anchor="w", pady=(4, 0))
        self._value_label = ctk.CTkLabel(value_frame, text=value, font=themed_font(self._size_cfg["value"], "bold"),
                      text_color=THEME["text"])
        self._value_label.pack(side="left")
        if unit:
            ctk.CTkLabel(value_frame, text=unit, font=themed_font(self._size_cfg["sub"]),
                         text_color=THEME["text_muted"]).pack(side="left", padx=(6, 0), pady=(4, 0))

        if trend:
            ctk.CTkLabel(txt, text=trend, font=themed_font(self._size_cfg["sub"]),
                         text_color=THEME["text_muted"]).pack(anchor="w", pady=(4, 0))

        icon_size = self._size_cfg["icon"]
        icon_bg = blend_color(self.accent, 0.15)
        icon_container = ctk.CTkFrame(row1, fg_color=icon_bg,
                                      width=icon_size, height=icon_size, corner_radius=RADIUS["lg"])
        icon_container.pack(side="right")
        icon_container.pack_propagate(False)
        ctk.CTkLabel(icon_container, text=icon, font=themed_font("h2"),
                     text_color=self.accent).place(relx=0.5, rely=0.5, anchor="center")

        if self._size == "wide":
            pbar = ctk.CTkProgressBar(content, height=4, progress_color=self.accent,
                                      fg_color=THEME["bg_alt"])
            pbar.pack(fill="x", pady=(14, 0))
            pbar.set(0.65)

    def set_value(self, value: str):
        self._value_label.configure(text=value)


class MetricCard(ctk.CTkFrame):
    """Professional large metric card with sparkline area."""

    def __init__(self, parent, title: str, value: str, change: str,
                 change_type: str = "positive", icon: str = "",
                 sparkline: list[float] | None = None,
                 accent: str = THEME["primary"]):
        super().__init__(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
        )
        self.accent = accent
        self._build(title, value, change, change_type, icon, sparkline)

    def _build(self, title, value, change, change_type, icon, sparkline):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["card_pad"])

        hdr = ctk.CTkFrame(content, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(hdr, text=title, font=themed_font("body_sm"),
                     text_color=THEME["text_muted"]).pack(side="left")
        ctk.CTkLabel(hdr, text=icon, font=themed_font("h3")).pack(side="right")

        val_f = ctk.CTkFrame(content, fg_color="transparent")
        val_f.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(val_f, text=value, font=themed_font("h1", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        ch_color = THEME["success"] if change_type == "positive" else (
            THEME["danger"] if change_type == "negative" else THEME["text_muted"]
        )
        ctk.CTkLabel(val_f, text=change, font=themed_font("body", "bold"),
                     text_color=ch_color).pack(side="left", padx=(12, 0), pady=(6, 0))

        if sparkline and len(sparkline) > 1:
            canvas = ctk.CTkCanvas(content, height=48, bg=THEME["surface"],
                                   highlightthickness=0)
            canvas.pack(fill="x")

            def draw(event=None):
                if event:
                    w, h = event.width, 48
                else:
                    w = 200
                    h = 48

                step = w / (len(sparkline) - 1)
                mn = min(sparkline)
                mx = max(sparkline)
                rng = mx - mn if mx != mn else 1

                points = []
                for i, v in enumerate(sparkline):
                    x = i * step
                    y = h - ((v - mn) / rng) * (h - 10) - 4
                    points.append((x, y))

                canvas.delete("all")
                for i in range(len(points) - 1):
                    canvas.create_line(points[i][0], points[i][1],
                                       points[i + 1][0], points[i + 1][1],
                                       fill=self.accent, width=2, smooth=True)

                for x, y in points:
                    canvas.create_oval(x - 3, y - 3, x + 3, y + 3,
                                       fill=self.accent, outline=THEME["surface"], width=1)

            canvas.bind("<Configure>", draw)
            self._spark_canvas = canvas


class ListCard(ctk.CTkFrame):
    """Professional card with header, status chip, icon and body."""

    def __init__(self, parent, title: str, description: str = "",
                 icon: str = "", status: str = "",
                 status_color: str = THEME["success"],
                 avatar_text: str = "", avatar_color: str = THEME["primary_soft"],
                 elevated: bool = False):
        super().__init__(
            parent,
            fg_color=THEME["surface_elevated"] if elevated else THEME["surface"],
            corner_radius=RADIUS["card"],
            border_width=1,
            border_color=THEME["border"],
        )
        self._build(title, description, icon, status, status_color, avatar_text, avatar_color)

    def _build(self, title, description, icon, status, status_color, avatar_text, avatar_color):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["card_pad"])
        inner.grid_columnconfigure(1, weight=1)

        if avatar_text:
            av = ctk.CTkFrame(inner, fg_color=avatar_color, width=44, height=44,
                              corner_radius=RADIUS["avatar"])
            av.grid(row=0, column=0, rowspan=2, padx=(0, 14))
            av.pack_propagate(False)
            ctk.CTkLabel(av, text=avatar_text, font=themed_font("h3", "bold"),
                         text_color=THEME["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(title_frame, text=title, font=themed_font("h4", "bold"),
                     text_color=THEME["text"]).pack(side="left")

        if icon:
            ctk.CTkLabel(title_frame, text=icon, font=themed_font("h3")).pack(side="right")

        if status:
            sp = ctk.CTkFrame(inner, fg_color=blend_color(status_color, 0.12),
                              corner_radius=RADIUS["pill"], height=22)
            sp.grid(row=0, column=2, padx=(10, 0), sticky="ns")
            sp.grid_propagate(False)
            ctk.CTkLabel(sp, text=status, font=themed_font("overline", "bold"),
                         text_color=status_color).pack(padx=10, pady=2)

        if description:
            ctk.CTkLabel(inner, text=description, font=themed_font("body_sm"),
                         text_color=THEME["text_muted"]).grid(row=1, column=1, sticky="w", pady=(4, 0))


class _BaseIconButton(ctk.CTkButton):
    """Base para botões que suportam texto, ícone e tooltip."""

    def __init__(self, parent, text: str = "", icon: str = "", tooltip: str = "", **kwargs):
        self._icon_only = bool(icon and not text)
        display = icon if self._icon_only else f"{icon}  {text}" if icon else text
        super().__init__(parent, text=display, **kwargs)
        self._tooltip_text = tooltip or text
        self._tooltip = None
        if self._icon_only and tooltip:
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

    @property
    def button_text(self) -> str:
        return self._icon_only and "" or self.cget("text")


class PrimaryButton(ctk.CTkButton):
    """Primary button with optional icon, size variants and loading state."""

    def __init__(self, parent, text: str = "", command=None, width: int = 140,
                 height: int = 42, icon: str = "", size: str = "md",
                 loading: bool = False, **kwargs):
        self._loading = loading
        self._original_command = command
        self._text = text
        self._icon = icon

        corner = kwargs.pop("corner_radius", RADIUS["button"])
        fg = kwargs.pop("fg_color", THEME["primary"])
        hover = kwargs.pop("hover_color", THEME["primary_hover"])
        txtc = kwargs.pop("text_color", THEME["text_on_primary"])

        h = {"sm": 34, "md": 42, "lg": 50}.get(size, 42)
        f = kwargs.pop("font", themed_font("button", "bold"))

        super().__init__(
            parent, text=text, command=self._handle_click,
            width=width, height=h, fg_color=fg, hover_color=hover,
            text_color=txtc, font=f, corner_radius=corner, **kwargs,
        )
        if icon:
            self._set_text_with_icon()
        if loading:
            self._show_loading()

    @property
    def button_text(self) -> str:
        return self._text

    def _set_text_with_icon(self):
        self.configure(text=f"{self._icon}  {self._text}" if self._loading is False else self._icon)

    def _handle_click(self):
        if self._loading:
            return
        if self._original_command:
            self._original_command()

    def set_loading(self, loading: bool):
        self._loading = loading
        if loading:
            self._show_loading()
        else:
            self.configure(text=f"{self._icon}  {self._text}" if self._icon else self._text, state="normal")

    def _show_loading(self):
        self.configure(text="⏳", state="disabled")
        self._animate_loading()

    def _animate_loading(self):
        if not self._loading:
            return
        current = self.cget("text")
        if current == "⏳":
            self.configure(text="⌛")
        elif current == "⌛":
            self.configure(text="⏳")
        if self._loading:
            self.after(250, self._animate_loading)


class SecondaryButton(_BaseIconButton):
    """Secondary / outlined button with icon and optional tooltip."""

    def __init__(self, parent, text: str = "", command=None, width: int = 120,
                 height: int = 38, icon: str = "", tooltip: str = "", **kwargs):
        corner = kwargs.pop("corner_radius", RADIUS["button"])
        fg = kwargs.pop("fg_color", "transparent")
        hover = kwargs.pop("hover_color", THEME["primary_soft"])
        txtc = kwargs.pop("text_color", THEME["primary"])
        f = kwargs.pop("font", themed_font("body", "bold"))
        bw = kwargs.pop("border_width", 1)
        bc = kwargs.pop("border_color", THEME["primary_medium"])
        super().__init__(
            parent, text=text, icon=icon, tooltip=tooltip, command=command,
            width=width, height=height,
            fg_color=fg, hover_color=hover, text_color=txtc,
            font=f, corner_radius=corner, border_width=bw, border_color=bc, **kwargs,
        )


class GhostButton(_BaseIconButton):
    """Ghost button for low-emphasis actions with optional tooltip."""

    def __init__(self, parent, text: str = "", command=None, width: int = 100,
                 height: int = 36, icon: str = "", tooltip: str = "", **kwargs):
        corner = kwargs.pop("corner_radius", RADIUS["button"])
        fg = kwargs.pop("fg_color", "transparent")
        hover = kwargs.pop("hover_color", THEME["bg_alt"])
        txtc = kwargs.pop("text_color", THEME["text_secondary"])
        f = kwargs.pop("font", themed_font("caption", "bold"))
        super().__init__(
            parent, text=text, icon=icon, tooltip=tooltip, command=command,
            width=width, height=height,
            fg_color=fg, hover_color=hover, text_color=txtc,
            font=f, corner_radius=corner, **kwargs,
        )


class DangerButton(_BaseIconButton):
    """Destructive action button with optional icon and tooltip."""

    def __init__(self, parent, text: str = "", command=None, width: int = 120,
                 height: int = 38, icon: str = "", tooltip: str = "", **kwargs):
        corner = kwargs.pop("corner_radius", RADIUS["button"])
        fg = kwargs.pop("fg_color", THEME["danger"])
        hover = kwargs.pop("hover_color", THEME["danger_strong"])
        txtc = kwargs.pop("text_color", THEME["text_on_primary"])
        f = kwargs.pop("font", themed_font("body", "bold"))

        display_text = f"{icon}  {text}" if icon else text

        super().__init__(
            parent, text=text, icon=icon, tooltip=tooltip, command=command,
            width=width, height=height,
            fg_color=fg, hover_color=hover, text_color=txtc, font=f,
            corner_radius=corner, **kwargs,
        )


class InputField(ctk.CTkFrame):
    """Modern input with float label animation, icon, validation indicator and helper."""

    def __init__(self, parent, label: str, placeholder: str = "", icon: str = "",
                 password: bool = False, helper: str = "", error: str = ""):
        super().__init__(parent, fg_color="transparent")
        self.placeholder = placeholder
        self.helper_text = helper
        self.label_text = label
        self._error = error
        self._icon = icon
        self._password = password
        self._build()

    def _build(self):
        self._labelframe = ctk.CTkFrame(self, fg_color="transparent")
        self._labelframe.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(self._labelframe, text=self.label_text, font=themed_font("overline", "bold"),
                     text_color=THEME["text_secondary"]).pack(anchor="w", side="left")

        self._status_icon = ctk.CTkLabel(self._labelframe, text="", font=themed_font("body"))

        inner = ctk.CTkFrame(
            self,
            fg_color=THEME["input_bg"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["input_border"],
            height=44,
        )
        inner.pack(fill="x")
        inner.pack_propagate(False)

        if self._icon:
            ctk.CTkLabel(inner, text=self._icon, font=themed_font("body")).pack(
                side="left", padx=(14, 8)
            )

        self.entry = ctk.CTkEntry(
            inner,
            placeholder_text=self.placeholder,
            fg_color="transparent",
            border_width=0,
            font=themed_font("body"),
            show="•" if self._password else "",
            height=36,
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 14))

        self.entry.bind("<FocusIn>", lambda e: inner.configure(
            border_color=THEME["input_border_focus"], border_width=2))
        self.entry.bind("<FocusOut>", lambda e: inner.configure(
            border_color=THEME["input_border"], border_width=1))

        if self._error:
            self._show_error(str(self._error))
        elif self.helper_text:
            self._show_helper()

    def _show_error(self, msg: str):
        self._status_icon.configure(text="⚠", text_color=THEME["danger"])
        self._status_icon.pack(side="right", padx=(8, 0))
        err = ctk.CTkLabel(self, text=msg, font=themed_font("overline"),
                           text_color=THEME["danger"])
        err.pack(anchor="w", pady=(4, 0))

    def _show_helper(self):
        if self._status_icon.cget("text"):
            self._status_icon.configure(text="ℹ", text_color=THEME["info"])
            self._status_icon.pack(side="right", padx=(8, 0))
        hlp = ctk.CTkLabel(self, text=self.helper_text, font=themed_font("overline"),
                           text_color=THEME["text_muted"])
        hlp.pack(anchor="w", pady=(4, 0))

    def set_error(self, msg: str = ""):
        self._destroy_aux()
        self._error = bool(msg)
        if msg:
            self._show_error(msg)

    def set_success(self):
        self._destroy_aux()
        self._error = False
        self._status_icon.configure(text="✔", text_color=THEME["success"])
        self._status_icon.pack(side="right", padx=(8, 0))

    def _destroy_aux(self):
        for w in self.winfo_children():
            if w != self._labelframe and w != self.entry.master:
                w.destroy()

    def get(self) -> str:
        return self.entry.get()

    def insert(self, index: str, value: str) -> None:
        self.entry.insert(index, value)

    def delete(self, first: str, last: str | None = None) -> None:
        self.entry.delete(first, last)


class SearchField(ctk.CTkFrame):
    """Search field with clear button and optional debounce."""

    def __init__(self, parent, placeholder: str = "Buscar...",
                 command: Optional[Callable] = None, debounce_ms: int = 300):
        super().__init__(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["input"],
            border_width=1,
            border_color=THEME["border"],
            height=42,
        )
        self._command = command
        self._debounce_ms = debounce_ms
        self._debounce_job = None
        self._build(placeholder)

    def _build(self, placeholder):
        self.pack_propagate(False)

        ctk.CTkLabel(self, text="🔍", font=themed_font("body"),
                     text_color=THEME["text_muted"]).pack(side="left", padx=(14, 8))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            fg_color="transparent",
            border_width=0,
            font=themed_font("body"),
        )
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self._clear = ctk.CTkButton(self, text="✕", width=22, height=22,
                                    fg_color=THEME["border"], hover_color=THEME["border_strong"],
                                    text_color=THEME["text"], font=themed_font("caption"),
                                    corner_radius=4, command=self.clear)
        self._clear.place(relx=1.0, x=-36, rely=0.5, anchor="w")

        if self._command:
            self.entry.bind("<KeyRelease>", self._on_key)

    def _on_key(self, event):
        if self._debounce_job:
            self.after_cancel(self._debounce_job)
        self._debounce_job = self.after(self._debounce_ms, lambda: self._command(self.entry.get()))

    def get(self) -> str:
        return self.entry.get()

    def clear(self) -> None:
        self.entry.delete(0, "end")


class Badge(ctk.CTkFrame):
    """Badge / chip for notifications and statuses."""

    def __init__(self, parent, text: str, color: str = THEME["danger"],
                 text_color: str = THEME["text_on_primary"], outline: bool = False):
        bg = color if outline else blend_color(color, 0.15)
        super().__init__(parent, fg_color=bg, corner_radius=RADIUS["pill"])
        ctk.CTkLabel(self, text=str(text), font=themed_font("overline", "bold"),
                     text_color=color).pack(padx=10, pady=4)
        if outline:
            self.configure(border_width=1, border_color=color, fg_color="transparent")


class Pill(ctk.CTkFrame):
    """Status pill / tag."""

    def __init__(self, parent, text: str, color: str = THEME["primary"],
                 text_color: str = THEME["primary"], variant: str = "soft"):
        c = blend_color(color, 0.15) if variant == "soft" else color
        tc = color if variant == "soft" else THEME["text_on_primary"]
        super().__init__(parent, fg_color=c, corner_radius=RADIUS["pill"])
        ctk.CTkLabel(self, text=text, font=themed_font("overline", "bold"),
                     text_color=tc).pack(padx=10, pady=3)


class EmptyState(ctk.CTkFrame):
    """Professional empty state with icon, title, subtitle and CTA."""

    def __init__(self, parent, icon: str, title: str, subtitle: str = "",
                 action_text: str = "", action_command=None):
        super().__init__(parent, fg_color="transparent")
        self._build(icon, title, subtitle, action_text, action_command)

    def _build(self, icon, title, subtitle, action_text, action_command):
        ctk.CTkLabel(self, text=icon, font=themed_font("display")).pack(pady=(28, 12))
        ctk.CTkLabel(self, text=title, font=themed_font("h3", "bold"),
                     text_color=THEME["text"]).pack(pady=(0, 6))
        if subtitle:
            ctk.CTkLabel(self, text=subtitle, font=themed_font("body"),
                         text_color=THEME["text_muted"]).pack(pady=(0, 18), ipadx=60)
        if action_text and action_command:
            PrimaryButton(self, text=action_text, command=action_command, width=200).pack(pady=12)


class Divider(ctk.CTkFrame):
    """Divider line with optional label."""

    def __init__(self, parent, label: str = ""):
        super().__init__(parent, height=1, fg_color=THEME["divider"])
        self.pack(fill="x", pady=12)
        if label:
            lbl = ctk.CTkLabel(self, text=label, font=themed_font("overline"),
                               text_color=THEME["text_muted"], bg_color=THEME["bg"])
            lbl.place(relx=0.5, y=0, anchor="n")


class Toast(ctk.CTkFrame):
    """Toast notification with auto-hide."""

    def __init__(self, parent, message: str, status: str = "info",
                 duration: int = 4000, on_action: Optional[Callable] = None):
        super().__init__(parent, fg_color=THEME["surface"], corner_radius=RADIUS["lg"],
                         border_width=1, border_color=THEME["border"])
        self._on_action = on_action
        colors = {
            "info": THEME["info"], "success": THEME["success"],
            "warning": THEME["warning"], "danger": THEME["danger"],
        }
        c = colors.get(status, THEME["info"])

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["item_gap"])

        ind = ctk.CTkFrame(inner, fg_color=c, width=4, corner_radius=2)
        ind.pack(side="left", padx=(0, 14), pady=6)
        ind.pack_propagate(False)

        lbl = ctk.CTkLabel(inner, text=message, font=themed_font("body"),
                           text_color=THEME["text"], anchor="w")
        lbl.pack(side="left", fill="both", expand=True)

        self._close(inner).pack(side="right", padx=(8, 0))

        self.place(relx=1.0, x=-20, y=20, anchor="ne")
        if duration > 0:
            self.after(duration, self.destroy)

    def _close(self, parent) -> ctk.CTkButton:
        btn = ctk.CTkButton(parent, text="✕", width=24, height=24,
                            fg_color="transparent", hover_color=THEME["bg_alt"],
                            text_color=THEME["text_muted"], font=themed_font("caption"),
                            corner_radius=RADIUS["xs"], command=self.destroy)
        return btn


class Tabs(ctk.CTkFrame):
    """Custom sleek tabs with pill indicator."""

    def __init__(self, parent, tabs: list[str], on_select: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")
        self.tabs = tabs
        self.on_select = on_select
        self._active = 0
        self._build()

    def _build(self):
        bg = ctk.CTkFrame(self, fg_color=THEME["bg_alt"], corner_radius=RADIUS["button"])
        bg.pack(fill="x")
        self._buttons = []
        for i, name in enumerate(self.tabs):
            btn = ctk.CTkButton(
                bg, text=name, fg_color="transparent", hover_color=THEME["bg_alt"],
                text_color=THEME["text_secondary"], font=themed_font("caption", "bold"),
                corner_radius=RADIUS["button"], command=lambda idx=i: self._select(idx),
            )
            btn.pack(side="left", expand=True, pady=3, padx=3)
            self._buttons.append(btn)
        self._update_style()

    def _select(self, idx: int):
        self._active = idx
        self._update_style()
        if self.on_select:
            self.on_select(idx)

    def _update_style(self):
        for i, btn in enumerate(self._buttons):
            if i == self._active:
                btn.configure(fg_color=THEME["surface"], text_color=THEME["primary"],
                              hover_color=THEME["surface"])
            else:
                btn.configure(fg_color="transparent", text_color=THEME["text_muted"],
                              hover_color=THEME["bg_alt"])


class Toggle(ctk.CTkSwitch):
    """Modern toggle switch with label."""

    def __init__(self, parent, text: str, command=None, initial: bool = False):
        super().__init__(
            parent, text="", width=44, height=24,
            command=command,
            variable=ctk.StringVar(value="on" if initial else "off"),
            onvalue="on", offvalue="off",
            progress_color=THEME["primary"] if initial else THEME["border_strong"],
            button_color=THEME["surface"], button_hover_color=THEME["bg_alt"],
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["pill"],
        )
        self._lbl = ctk.CTkLabel(parent, text=text, font=themed_font("body"),
                                 text_color=THEME["text"])


class SkeletonLoader(ctk.CTkFrame):
    """Skeleton loading placeholder."""

    def __init__(self, parent, width: int = 200, height: int = 16, variant: str = "text"):
        super().__init__(parent, fg_color="transparent")
        self._build(width, height, variant)

    def _build(self, width, height, variant):
        if variant == "avatar":
            f = ctk.CTkFrame(self, width=height, height=height,
                             corner_radius=RADIUS["avatar"], fg_color=THEME["bg_alt"])
            f.pack()
            f.pack_propagate(False)
        elif variant == "card":
            f = ctk.CTkFrame(self, width=width, height=100,
                             corner_radius=RADIUS["card"], fg_color=THEME["bg_alt"])
            f.pack()
            f.pack_propagate(False)
        else:
            f = ctk.CTkFrame(self, width=width, height=height,
                             corner_radius=RADIUS["button"], fg_color=THEME["bg_alt"])
            f.pack()
            f.pack_propagate(False)
        self._shimmer(f)

    def _shimmer(self, widget):
        try:
            bg = widget.cget("fg_color")
        except Exception:
            bg = THEME["bg_alt"]

        def animate(idx=0):
            t = idx % 20
            offset = int((t / 20) * widget.cget("width"))
            if offset > widget.cget("width"):
                return
            shade = darken(bg, 0.08) if t % 2 == 0 else lighten(bg, 0.03)
            widget.configure(fg_color=shade if shade != "#000000" else THEME["bg_alt"])
            self.after(60, lambda: animate(idx + 1))

        animate()


class Avatar(ctk.CTkFrame):
    """Avatar with optional status indicator."""

    def __init__(self, parent, initials: str, size: int = 44,
                 color: str = THEME["primary"], text_color: str = THEME["text_on_primary"],
                 status: str = ""):
        super().__init__(parent, fg_color=color, width=size, height=size,
                         corner_radius=RADIUS["avatar"])
        self.pack_propagate(False)
        half = size // 2
        ctk.CTkLabel(self, text=initials[:2].upper(),
                     font=font(size=max(10, half // 2), weight="bold", family=FONT_FAMILY),
                     text_color=text_color).place(relx=0.5, rely=0.5, anchor="center")

        if status:
            self._status = ctk.CTkFrame(self, fg_color=STATUS_COLORS.get(status.lower(), THEME["success"]),
                                        width=max(10, size // 5), height=max(10, size // 5),
                                        corner_radius=RADIUS["avatar"], border_width=2,
                                        border_color=THEME["surface"])
            self._status.place(relx=1.0, rely=1.0, anchor="se", x=-2, y=-2)


class SegmentedButton(ctk.CTkFrame):
    """Segmented control with pill active state."""

    def __init__(self, parent, options: list[str], on_change: Optional[Callable] = None,
                 initial: int = 0):
        super().__init__(parent, fg_color=THEME["bg_alt"], corner_radius=RADIUS["button"])
        self.options = options
        self.on_change = on_change
        self._selected = initial
        self._build()

    def _build(self):
        for i, opt in enumerate(self.options):
            btn = ctk.CTkButton(
                self, text=opt, fg_color="transparent", hover_color=THEME["bg_alt"],
                text_color=THEME["text_secondary"], font=themed_font("body", "bold"),
                corner_radius=RADIUS["button"], anchor="center",
                command=lambda idx=i: self._select(idx),
            )
            btn.pack(side="left", expand=True, fill="both", padx=3, pady=3)
        self._update()

    def _select(self, idx: int):
        self._selected = idx
        self._update()
        if self.on_change:
            self.on_change(idx)

    def _update(self):
        for i, btn in enumerate(self.winfo_children()):
            if i == self._selected:
                btn.configure(fg_color=THEME["surface"], text_color=THEME["primary"],
                              hover_color=THEME["surface"])
            else:
                btn.configure(fg_color="transparent", text_color=THEME["text_muted"],
                              hover_color=THEME["bg_alt"])


class Dropdown(ctk.CTkOptionMenu):
    """Styled option menu with fixed width."""

    def __init__(self, parent, values: list[str], initial: str = "", width: int = 180, **kwargs):
        super().__init__(
            parent,
            values=values,
            fg_color=THEME["bg_alt"],
            button_color=THEME["border"],
            button_hover_color=THEME["border_strong"],
            dropdown_fg_color=THEME["surface"],
            dropdown_hover_color=THEME["bg_alt"],
            dropdown_text_color=THEME["text"],
            dropdown_font=themed_font("body"),
            font=themed_font("body"),
            width=width,
            height=36,
            corner_radius=RADIUS["input"],
        )
        if initial and initial in values:
            self.set(initial)


class Checkbox(ctk.CTkCheckBox):
    """Styled checkbox."""

    def __init__(self, parent, text: str, initial: bool = False, **kwargs):
        super().__init__(
            parent, text=text,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            border_color=THEME["border_strong"],
            checkmark_color=THEME["text_on_primary"],
            font=themed_font("body"), **kwargs,
        )
        if initial:
            self.select()


class RadioGroup(ctk.CTkFrame):
    """Custom radio button group."""

    def __init__(self, parent, options: list[str], initial: str = "", label: str = ""):
        super().__init__(parent, fg_color="transparent")
        self._val = ctk.StringVar(value=initial or options[0])
        if label:
            ctk.CTkLabel(self, text=label, font=themed_font("caption", "bold"),
                         text_color=THEME["text_secondary"]).pack(anchor="w", pady=(0, 4))
        for opt in options:
            rb = ctk.CTkRadioButton(self, text=opt, variable=self._val, value=opt,
                                    fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                                    font=themed_font("body"))
            rb.pack(anchor="w", pady=2)

    @property
    def value(self) -> str:
        return self._val.get()


class Tooltip:
    """Lightweight tooltip that tracks a widget."""

    def __init__(self, parent, text: str, delay: int = 600):
        self.parent = parent
        self.text = text
        self.delay = delay
        self._job = None
        self._win = None
        parent.bind("<Enter>", self._on_enter)
        parent.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        self._job = self.parent.after(self.delay, self._show)

    def _on_leave(self, event):
        if self._job:
            self.parent.after_cancel(self._job)
            self._job = None
        self._hide()

    def _show(self):
        if self._win:
            return
        x = self.parent.winfo_pointerx() + 16
        y = self.parent.winfo_pointery() + 16
        self._win = ctk.CTkToplevel(self.parent)
        self._win.overrideredirect(True)
        self._win.attributes("-topmost", True)
        lbl = ctk.CTkLabel(self._win, text=self.text, font=themed_font("caption", "bold"),
                           text_color=THEME["text_on_primary"], fg_color=THEME["overlay"],
                           corner_radius=RADIUS["sm"], padx=10, pady=6)
        lbl.pack()
        self._win.geometry(f"+{x}+{y}")

    def _hide(self):
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None


class ThemedScrollableFrame(ctk.CTkScrollableFrame):
    """ScrollableFrame com estilos do tema já aplicados."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
            **kwargs,
        )


class BaseModal(ctk.CTkToplevel):
    """Modal base centralizado, transient e com grab_set."""

    def __init__(self, parent, title: str, width: int, height: int,
                 fg_color: str = THEME["surface"]):
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=fg_color)
        self.resizable(False, False)

        sx = self.winfo_screenwidth() // 2 - width // 2
        sy = self.winfo_screenheight() // 2 - height // 2
        self.geometry(f"{width}x{height}+{sx}+{sy}")

        self.transient(self.winfo_toplevel())
        self.grab_set()


class ClickableFrame(ctk.CTkFrame):
    """Frame clicável com suporte a mouse e teclado (<Return>, <space>)."""

    def __init__(self, parent, on_click, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_click = on_click
        self.configure(cursor="hand2")
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Return>", lambda e: self._on_click())
        self.bind("<space>", lambda e: self._on_click())


def bind_clickable(widget, on_click):
    """Aplica comportamento clicável (mouse + teclado) a qualquer widget."""
    widget.configure(cursor="hand2")
    widget.bind("<Button-1>", lambda e: on_click())
    widget.bind("<Return>", lambda e: on_click())
    widget.bind("<space>", lambda e: on_click())

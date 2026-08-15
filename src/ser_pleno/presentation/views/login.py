from __future__ import annotations

import ctypes
import logging
import math
import random
import time
from collections import OrderedDict
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

from ser_pleno.application.controllers.autenticacao import AutenticacaoController
from ser_pleno.presentation.components.ui_components import (
    Divider,
    PrimaryButton,
)
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.theme import RADIUS, THEME, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.utils.async_runner import AsyncRunner

logger = logging.getLogger("apps.desktop")

_IS_WINDOWS = hasattr(ctypes, "windll")


# —————————————————————————————————————————————
#  Paleta dedicada à tela de login
# —————————————————————————————————————————————
_LOGIN_PALETTE = {
    "grad_top_left": "#1E1B4B",
    "grad_top_right": "#312E81",
    "grad_bottom_left": "#4338CA",
    "grad_bottom": "#6D5CE8",
    "card_bg": "#FFFFFF",
    "card_border": "#E2E8F0",
    "input_bg": "#F8FAFC",
    "input_border": "#CBD5E1",
    "card_shadow": THEME["overlay"],
    "accent": THEME["primary"],
    "accent_hover": THEME["primary_hover"],
    "accent_soft": THEME["primary_soft"],
    "accent_medium": THEME["primary_medium"],
    "text_primary": "#14162B",
    "text_muted": "#5B5E76",
    "text_light": "#7C7F97",
    "success": THEME["success"],
    "danger": THEME["danger"],
    "warning": THEME["warning"],
}


def _hex_to_rgb(hex_c: str):
    h = hex_c.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_color(c1_hex: str, c2_hex: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1_hex)
    r2, g2, b2 = _hex_to_rgb(c2_hex)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _criar_imagem_arredondada(largura: int, altura: int, raio: int, cor: str) -> ImageTk.PhotoImage:
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, largura - 1, altura - 1], radius=raio, fill=cor)
    return ImageTk.PhotoImage(img)


CARD_W, CARD_H = 444, 720
_CARD_CORNER_RADIUS = 20
_BUBBLE_COUNT = 16
_GRADIENT_STEP_PX = 4
_GRADIENT_CACHE_MAX = 3
_LAZY_SIZES = [(1024, 768), (1280, 720), (800, 600)]
_BUBBLE_WOBBLE_SPEED = 0.025
_BUBBLE_SPEED_MIN = 0.10
_BUBBLE_SPEED_MAX = 0.45
_BUBBLE_WOBBLE_AMP_MIN = 0.2
_BUBBLE_WOBBLE_AMP_MAX = 0.7
_BUBBLE_SIZE_MIN = 14
_BUBBLE_SIZE_MAX = 80
_BUBBLE_ALPHA_MIN = 0.05
_BUBBLE_ALPHA_MAX = 0.18
_SHAKE_STEPS = 8
_SHAKE_INTERVAL_MS = 38
_SHAKE_OFFSET_PX = 5
_MUSIC_BTN_SIZE = 64
_MUSIC_BTN_INNER_SIZE = 48
_MUSIC_BTN_RADIUS = 24
_MUSIC_BTN_MARGIN = 16
_BG_RESIZE_DEBOUNCE_MS = 120
_BG_DRAW_WARN_THRESHOLD_MS = 40
_ANIMATION_FPS = 33
_GLOW_RADIUS_FACTOR = 0.55
_GRADIENT_TWEEN_POWER = 0.8
_ICON_BG_SIZE = 68
_MODAL_ICON_BG_SIZE = 52
_TITLE_GAP = 12
_MODAL_WIDTH_POLICY = 440
_MODAL_HEIGHT_POLICY = 360
_MODAL_WIDTH_TERMS = 480
_MODAL_HEIGHT_TERMS = 420
_MUSIC_FILE_RELATIVE = Path("assets") / "Music" / "background_music.mp3"
_ICON_TEXT_COLOR = "#7C3AED"
_ENTRY_ICON_WIDTH = 36
_EYE_BTN_WIDTH = 36
_EYE_BTN_HEIGHT = 36
_EYE_BTN_PADX = (0, 6)
_EYE_BTN_PADY = 4
_ENTRY_GRID_PADX = (4, 0)
_ENTRY_GRID_PADY = 4
_ERRO_WRAPLENGTH = 340
_BUBBLE_OUTLINE_WIDTH = 1.2
_CHIP_HEIGHT = 30


# —————————————————————————————————————————————
#  Campo de entrada refinado (Ajustado para cores claras)
# —————————————————————————————————————————————
class LoginInputField(ctk.CTkFrame):
    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        label: str,
        placeholder: str = "",
        icon: str = "",
        password: bool = False,
    ) -> None:
        super().__init__(parent, fg_color="transparent")
        self._password = password
        self._show_pass = False
        self._border_normal = _LOGIN_PALETTE["input_border"]
        self._border_focus = _LOGIN_PALETTE["accent"]
        self._border_error = THEME["danger"]
        self._border_success = THEME["success"]
        self._bg_normal = _LOGIN_PALETTE["input_bg"]
        self._bg_focus = _LOGIN_PALETTE["card_bg"]
        self._state = "normal"

        self._label = ctk.CTkLabel(
            self,
            text=label,
            font=themed_font("caption", "bold"),
            text_color=_LOGIN_PALETTE["text_primary"],
            anchor="w",
        )
        self._label.pack(fill="x", padx=spacing("sm"), pady=(0, spacing("label_gap")))

        self._box = ctk.CTkFrame(
            self,
            corner_radius=RADIUS["input"],
            fg_color=self._bg_normal,
            border_width=1,
            border_color=self._border_normal,
        )
        self._box.pack(fill="x")
        self._box.grid_columnconfigure(1, weight=1)

        if icon:
            ctk.CTkLabel(
                self._box,
                text=icon,
                font=themed_font("body"),
                text_color=_LOGIN_PALETTE["text_muted"],
                width=_ENTRY_ICON_WIDTH,
            ).grid(row=0, column=0, padx=(spacing("sm"), 0), pady=spacing("md"))

        self.entry = ctk.CTkEntry(
            self._box,
            placeholder_text=placeholder,
            placeholder_text_color=_LOGIN_PALETTE["text_light"],
            fg_color="transparent",
            border_width=0,
            text_color=_LOGIN_PALETTE["text_primary"],
            font=themed_font("body"),
            height=42,
            show="●" if password else "",
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=_ENTRY_GRID_PADX, pady=_ENTRY_GRID_PADY)

        if password:
            self._eye_btn = ctk.CTkButton(
                self._box,
                text=ICONS["view"],
                width=_EYE_BTN_WIDTH,
                height=_EYE_BTN_HEIGHT,
                fg_color="transparent",
                hover_color=_LOGIN_PALETTE["accent_soft"],
                text_color=_LOGIN_PALETTE["text_muted"],
                font=themed_font("body"),
                command=self._toggle_show,
                corner_radius=RADIUS["button"],
                cursor="hand2",
            )
            self._eye_btn.grid(row=0, column=2, padx=_EYE_BTN_PADX, pady=_EYE_BTN_PADY)
            self._eye_btn.bind("<Return>", lambda _: self._toggle_show())
            self._eye_btn.bind("<space>", lambda _: self._toggle_show())

        self._msg = ctk.CTkLabel(
            self,
            text="",
            anchor="w",
            font=themed_font("caption"),
            text_color=THEME["danger"],
        )
        self._msg.pack(fill="x", padx=spacing("sm"), pady=(spacing("xs"), 0))

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def get(self) -> str:
        return self.entry.get()

    def set_error(self, msg: str = "") -> None:
        self._state = "error"
        self._box.configure(border_color=self._border_error, fg_color=THEME["danger_soft"])
        self._label.configure(text_color=THEME["danger"])
        self._msg.configure(
            text=f"{ICONS['alert']}   {msg}" if msg else "", text_color=THEME["danger"]
        )

    def set_success(self) -> None:
        self._state = "success"
        self._box.configure(border_color=self._border_success, fg_color=THEME["success_soft"])
        self._label.configure(text_color=THEME["success"])
        self._msg.configure(text="")

    def clear_state(self) -> None:
        self._state = "normal"
        self._box.configure(border_color=self._border_normal, fg_color=self._bg_normal)
        self._label.configure(text_color=_LOGIN_PALETTE["text_primary"])
        self._msg.configure(text="")

    def _on_focus_in(self, _=None) -> None:
        self._box.configure(border_color=self._border_focus, fg_color=self._bg_focus)
        self._label.configure(text_color=_LOGIN_PALETTE["accent"])

    def _on_focus_out(self, _=None) -> None:
        if self._state == "error":
            self._box.configure(border_color=self._border_error, fg_color=THEME["danger_soft"])
            self._label.configure(text_color=THEME["danger"])
        elif self._state == "success":
            self._box.configure(border_color=self._border_success, fg_color=THEME["success_soft"])
            self._label.configure(text_color=THEME["success"])
        else:
            self._box.configure(border_color=self._border_normal, fg_color=self._bg_normal)
            self._label.configure(text_color=_LOGIN_PALETTE["text_primary"])

    def _toggle_show(self) -> None:
        self._show_pass = not self._show_pass
        self.entry.configure(show="" if self._show_pass else "●")
        self._eye_btn.configure(text=ICONS["hide"] if self._show_pass else ICONS["view"])


# —————————————————————————————————————————————
#  Frame principal de login
# —————————————————————————————————————————————
class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkBaseClass, controller: "App") -> None:
        self.palette = _LOGIN_PALETTE
        super().__init__(parent, fg_color=self.palette["grad_top_left"])

        self.controller = controller
        self.controller_autenticacao = AutenticacaoController()
        self.bolhas: list[dict] = []
        self._is_loading = False
        self._music_playing = False
        self._alive = True
        self._shake_active = False
        self._bg_draw_job: int | None = None
        self._last_bg_size = (0, 0)
        self._gradient_cache: OrderedDict[tuple[int, int], ImageTk.PhotoImage] = OrderedDict()
        self._t_draw_start = 0.0

        self.bind("<Destroy>", self._on_destroy)

        self.canvas = ctk.CTkCanvas(self, highlightthickness=0, bd=0)
        self.canvas.place(relwidth=1, relheight=1)

        self._criar_bolhas()
        self._schedule_lazy_gradient_preload()
        self._criar_music_toggle()
        self._criar_card_login()

        self.bind("<Configure>", self._on_configure)
        if hasattr(self, "_music_btn_frame"):
            self._music_btn_frame.bind("<Configure>", self._ajustar_botao_musica)
        self.after_idle(self._posicionar_card)
        self._animar_bolhas()

    def _on_destroy(self, _event=None) -> None:
        self._alive = False

    def _posicionar_card(self) -> None:
        if getattr(self, "_shake_active", False):
            return
        if hasattr(self, "card"):
            self.card.place(relx=0.5, rely=0.5, anchor="center")

    def _on_configure(self, event=None) -> None:
        if self._bg_draw_job:
            self.after_cancel(self._bg_draw_job)
        self._bg_draw_job = self.after(_BG_RESIZE_DEBOUNCE_MS, self._desenhar_fundo)
        self.after_idle(self._posicionar_card)

    def _get_or_create_gradient(self, w: int, h: int) -> ImageTk.PhotoImage:
        key = (w, h)
        cached = self._gradient_cache.get(key)
        if cached is not None:
            self._gradient_cache.move_to_end(key)
            return cached

        pil_img = self._generate_gradient_pil(w, h)
        photo = ImageTk.PhotoImage(pil_img)
        if len(self._gradient_cache) >= _GRADIENT_CACHE_MAX:
            self._gradient_cache.popitem(last=False)
        self._gradient_cache[key] = photo
        return photo

    def _generate_gradient_pil(self, w: int, h: int) -> "Image.Image":
        top_l = self.palette["grad_top_left"]
        top_r = self.palette["grad_top_right"]
        bot = self.palette["grad_bottom"]
        c_top = _lerp_color(top_l, top_r, 0.5)

        img = Image.new("RGB", (w, h))
        step = _GRADIENT_STEP_PX
        for y in range(0, h, step):
            t = y / h
            color = _lerp_color(c_top, bot, t**_GRADIENT_TWEEN_POWER)
            img.paste(color, (0, y, w, min(y + step, h)))
        return img

    def _show_bg_placeholder(self, w: int, h: int) -> None:
        self.canvas.delete("bg")
        self.canvas.create_rectangle(
            0, 0, w, h, fill=self.palette["grad_top_left"], outline="", tags="bg"
        )
        self.canvas.tag_lower("bg")
        self.canvas.tag_raise("bubble")
        self._elevar_elementos()

    def _apply_gradient(self, w: int, h: int, photo: ImageTk.PhotoImage) -> None:
        self.canvas.delete("bg")
        self.canvas.create_image(0, 0, anchor="nw", image=photo, tags="bg")
        self.canvas.image_bg = photo

        glow_r = int(w * _GLOW_RADIUS_FACTOR)
        self.canvas.create_oval(
            w - glow_r,
            -glow_r // 2,
            w + glow_r // 2,
            glow_r,
            fill=self.palette["grad_bottom"],
            outline="",
            tags="bg",
        )
        self.canvas.create_oval(
            -glow_r // 3,
            h - glow_r // 2,
            glow_r // 1.5,
            h + glow_r // 3,
            fill=self.palette["grad_bottom_left"],
            outline="",
            tags="bg",
        )

        self.canvas.tag_lower("bg")
        self.canvas.tag_raise("bubble")
        self._elevar_elementos()

        try:
            draw_ms = (time.perf_counter() - self._t_draw_start) * 1000
            if draw_ms > _BG_DRAW_WARN_THRESHOLD_MS:
                logger.warning("PERF login_grad_draw_ms=%.1f size=%dx%d", draw_ms, w, h)
        except Exception:
            pass

    def _desenhar_fundo(self, event=None) -> None:
        self._bg_draw_job = None
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return
        if (w, h) == self._last_bg_size:
            self._posicionar_card()
            return
        self._last_bg_size = (w, h)

        self._t_draw_start = time.perf_counter()
        self._show_bg_placeholder(w, h)

        cached = self._gradient_cache.get((w, h))
        if cached is not None:
            self._apply_gradient(w, h, cached)
            return

        def _generate() -> "Image.Image":
            return self._generate_gradient_pil(w, h)

        def _on_ready(pil_img: "Image.Image") -> None:
            if not self._alive or not self.winfo_exists():
                return
            current_size = (self.winfo_width(), self.winfo_height())
            if current_size != (w, h):
                return
            photo = ImageTk.PhotoImage(pil_img)
            self._gradient_cache[(w, h)] = photo
            if len(self._gradient_cache) > _GRADIENT_CACHE_MAX:
                self._gradient_cache.popitem(last=False)
            self._apply_gradient(w, h, photo)

        def _on_error(exc: Exception) -> None:
            logger.warning("Falha ao gerar gradiente em background: %s", exc)

        AsyncRunner.run(
            task=_generate,
            on_success=_on_ready,
            on_error=_on_error,
            widget_ref=self,
        )

    def _schedule_lazy_gradient_preload(self) -> None:
        common_sizes = [(1024, 768), (1280, 720), (800, 600)]
        self._lazy_gradient_sizes: list[tuple[int, int]] = common_sizes
        self._lazy_gradient_index: int = 0
        self.after_idle(self._generate_next_gradient)

    def _generate_next_gradient(self) -> None:
        if self._lazy_gradient_index >= len(self._lazy_gradient_sizes):
            return
        if not self._alive or not self.winfo_exists():
            return

        w, h = self._lazy_gradient_sizes[self._lazy_gradient_index]
        key = (w, h)
        if key not in self._gradient_cache:

            def _gen() -> "Image.Image":
                return self._generate_gradient_pil(w, h)

            def _on_ready(pil_img, size=(w, h)):
                if not self._alive or not self.winfo_exists():
                    return
                photo = ImageTk.PhotoImage(pil_img)
                self._gradient_cache[size] = photo

            AsyncRunner.run(task=_gen, on_success=_on_ready, widget_ref=self)

        self._lazy_gradient_index += 1
        if self._lazy_gradient_index < len(self._lazy_gradient_sizes):
            self.after_idle(self._generate_next_gradient)

    def _elevar_elementos(self) -> None:
        for b in self.bolhas:
            if b.get("id"):
                self.canvas.tag_raise(b["id"])
        if hasattr(self, "_music_btn_frame"):
            self._music_btn_frame.lift()
        if hasattr(self, "card"):
            self.card.lift()

    def _criar_bolhas(self) -> None:
        for _ in range(_BUBBLE_COUNT):
            x = random.randint(0, 1400)
            y = random.randint(50, 900)
            size = random.randint(_BUBBLE_SIZE_MIN, _BUBBLE_SIZE_MAX)
            a = random.uniform(_BUBBLE_ALPHA_MIN, _BUBBLE_ALPHA_MAX)

            w_val = min(255, int(200 + 55 * a))
            fill = f"#{w_val:02x}{w_val:02x}{w_val:02x}"

            bid = self.canvas.create_oval(
                x,
                y,
                x + size,
                y + size,
                outline=fill,
                width=_BUBBLE_OUTLINE_WIDTH,
                fill="",
                tags="bubble",
            )
            rx, ry, rs = x + size * 0.2, y + size * 0.15, size * 0.18
            rid = self.canvas.create_oval(
                rx,
                ry,
                rx + rs,
                ry + rs,
                fill=fill,
                outline="",
                tags="bubble",
            )

            self.bolhas.append(
                {
                    "id": bid,
                    "reflex_id": rid,
                    "x": float(x),
                    "y": float(y),
                    "size": size,
                    "speed": random.uniform(_BUBBLE_SPEED_MIN, _BUBBLE_SPEED_MAX),
                    "wobble": random.uniform(0, 2 * math.pi),
                    "wobble_amp": random.uniform(_BUBBLE_WOBBLE_AMP_MIN, _BUBBLE_WOBBLE_AMP_MAX),
                }
            )

    def _animar_bolhas(self) -> None:
        if not self._alive or not self.winfo_exists():
            return

        w, h = self.winfo_width(), self.winfo_height()
        if w > 1 and h > 1:
            for b in self.bolhas:
                prev_x, prev_y = b["x"], b["y"]
                b["y"] -= b["speed"]
                b["wobble"] += _BUBBLE_WOBBLE_SPEED
                b["x"] += math.sin(b["wobble"]) * b["wobble_amp"]

                wrapped = False
                if b["y"] + b["size"] < -20:
                    b["y"] = float(h + b["size"] + random.randint(10, 80))
                    b["x"] = float(random.randint(-30, w + 30))
                    wrapped = True
                if b["x"] < -80:
                    b["x"] = float(w + 20)
                    wrapped = True
                elif b["x"] > w + 80:
                    b["x"] = -20.0
                    wrapped = True

                x, y, s = b["x"], b["y"], b["size"]
                if wrapped:
                    self.canvas.coords(b["id"], x, y, x + s, y + s)
                else:
                    self.canvas.move(b["id"], x - prev_x, y - prev_y)

                rx, ry, rs = x + s * 0.2, y + s * 0.15, s * 0.18
                prev_rx = prev_x + s * 0.2
                prev_ry = prev_y + s * 0.15
                if wrapped:
                    self.canvas.coords(b["reflex_id"], rx, ry, rx + rs, ry + rs)
                else:
                    self.canvas.move(b["reflex_id"], rx - prev_rx, ry - prev_ry)

        self.after(_ANIMATION_FPS, self._animar_bolhas)

    def _criar_card_login(self) -> None:
            """Cria o frame do card de login e seu conteúdo interno de forma organizada."""
            # Container principal do Card com cantos arredondados nativos
            self.card = ctk.CTkFrame(
                self,
                width=CARD_W,
                height=CARD_H,
                fg_color=self.palette["card_bg"],
                corner_radius=_CARD_CORNER_RADIUS,
                border_width=1,
                border_color=self.palette["card_border"],
            )
            self.card.place(relx=0.5, rely=0.5, anchor="center")
            self.card.pack_propagate(False)
            self.card.lift()

            self._card = self.card

            # Frame interno com padding para afastar os elementos das bordas
            inner = ctk.CTkFrame(self.card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=32, pady=28)

            # ---------------------------------------------------------
            # HEADER (Badge, Ícone, Título e Subtítulo)
            # ---------------------------------------------------------
            header = ctk.CTkFrame(inner, fg_color="transparent")
            header.pack(fill="x", pady=(0, 12))

            badge = ctk.CTkFrame(
                header,
                corner_radius=RADIUS["pill"],
                fg_color=self.palette["accent_soft"],
            )
            badge.pack(pady=(0, 10))
            ctk.CTkLabel(
                badge,
                text="Acesso seguro · Plataforma SerPleno",
                font=themed_font("caption", "bold"),
                text_color=self.palette["accent"],
            ).pack(padx=16, pady=6)

            icon_bg = ctk.CTkFrame(
                header,
                width=_ICON_BG_SIZE,
                height=_ICON_BG_SIZE,
                corner_radius=RADIUS["avatar"],
                fg_color=self.palette["accent_soft"],
            )
            icon_bg.pack(pady=(0, 8))
            icon_bg.pack_propagate(False)
            ctk.CTkLabel(
                icon_bg, text=ICONS["brain"], font=themed_font("h2"), text_color=_ICON_TEXT_COLOR
            ).place(relx=0.5, rely=0.5, anchor="center")

            ctk.CTkLabel(
                header,
                text="SerPleno",
                font=themed_font("h2", "bold"),
                text_color=self.palette["text_primary"],
            ).pack(pady=(0, 2))

            ctk.CTkLabel(
                header,
                text="Bem-estar, acompanhamento escolar e comunicação integrada",
                font=themed_font("caption"),
                text_color=self.palette["text_muted"],
                wraplength=360,
                justify="center",
            ).pack(pady=(0, 10))

            # ---------------------------------------------------------
            # CHIPS DE INFORMAÇÃO
            # ---------------------------------------------------------
            info_row = ctk.CTkFrame(inner, fg_color="transparent")
            info_row.pack(pady=(0, 12))

            for text in [
                f"{ICONS['lock']} LGPD",
                f"{ICONS['alert']} Rápido",
                f"{ICONS['user']} Apoio",
            ]:
                chip = ctk.CTkFrame(
                    info_row,
                    height=_CHIP_HEIGHT,
                    corner_radius=RADIUS["pill"],
                    fg_color=self.palette["input_bg"],
                )
                chip.pack(side="left", padx=4)
                ctk.CTkLabel(
                    chip, text=text, font=themed_font("caption"), text_color=self.palette["text_muted"]
                ).pack(padx=10, pady=4)

            Divider(inner).pack(fill="x", pady=(0, 16))

            # ---------------------------------------------------------
            # CAMPOS DE FORMULÁRIO E AÇÕES
            # ---------------------------------------------------------
            self.input_user = LoginInputField(
                inner, "Usuário", placeholder="Seu nome de usuário", icon=ICONS["user"]
            )
            self.input_user.pack(fill="x", pady=(0, 12))

            self.input_pass = LoginInputField(
                inner, "Senha", placeholder="Sua senha", icon=ICONS["lock"], password=True
            )
            self.input_pass.pack(fill="x", pady=(0, 8))

            self.lbl_erro = ctk.CTkLabel(
                inner,
                text="",
                text_color=self.palette["danger"],
                font=themed_font("caption"),
                anchor="center",
                wraplength=_ERRO_WRAPLENGTH,
            )
            self.lbl_erro.pack(fill="x", pady=(0, 8))

            self.btn_entrar = PrimaryButton(
                inner,
                text="Entrar",
                command=self._fazer_login,
                height=46,
                corner_radius=RADIUS["lg"],
            )
            self.btn_entrar.pack(fill="x", pady=(0, 8))

            _termos_btn = ctk.CTkButton(
                inner,
                text=f"{ICONS['lock']} Termos de Privacidade",
                command=self._abrir_termos,
                fg_color="transparent",
                hover_color=self.palette["accent_soft"],
                text_color=self.palette["accent"],
                border_width=1,
                border_color=self.palette["accent_medium"],
                corner_radius=RADIUS["button"],
                height=36,
                font=themed_font("caption", "bold"),
                anchor="center",
            )
            _termos_btn.pack(fill="x")

            # Mapeamento e atalhos
            self.entry_user = self.input_user.entry
            self.entry_pass = self.input_pass.entry
            self.entry_user.bind("<Return>", lambda _: self._fazer_login())
            self.entry_pass.bind("<Return>", lambda _: self._fazer_login())
            self.entry_user.focus_set()

            
    def _criar_music_toggle(self) -> None:
        self.music_var = ctk.StringVar(value="off")
        self._music_btn_frame = ctk.CTkFrame(
            self,
            fg_color=self.palette["card_bg"],
            corner_radius=_MUSIC_BTN_RADIUS,
            width=_MUSIC_BTN_SIZE,
            height=_MUSIC_BTN_SIZE,
        )
        self._music_btn_frame.place(
            relx=1.0, rely=1.0, anchor="se", x=-_MUSIC_BTN_MARGIN, y=-_MUSIC_BTN_MARGIN
        )
        self._music_btn_frame.pack_propagate(False)

        self._music_btn = ctk.CTkButton(
            self._music_btn_frame,
            text=ICONS["music"],
            width=_MUSIC_BTN_INNER_SIZE,
            height=_MUSIC_BTN_INNER_SIZE,
            corner_radius=RADIUS["button"],
            font=themed_font("h3"),
            fg_color="transparent",
            hover_color=self.palette["accent_soft"],
            text_color=self.palette["text_muted"],
            border_width=0,
            command=self._toggle_music,
            cursor="hand2",
        )
        self._music_btn.place(relx=0.5, rely=0.5, anchor="center")

        if not _IS_WINDOWS:
            from ser_pleno.presentation.components.ui_components import Tooltip

            Tooltip(self._music_btn, "Música de fundo disponível apenas no Windows")

    def _ajustar_botao_musica(self, event=None) -> None:
        if hasattr(self, "_music_btn_frame") and self._music_btn_frame.winfo_exists():
            w = self._music_btn_frame.winfo_width()
            h = self._music_btn_frame.winfo_height()
            if w > 1 and h > 1:
                try:
                    self._music_btn.place(relx=0.5, rely=0.5, anchor="center")
                except Exception:
                    pass

    def _toggle_music(self) -> None:
        if not _IS_WINDOWS:
            return
        is_playing = getattr(self, "_music_playing", False)
        if not is_playing:
            path = _MUSIC_FILE_RELATIVE
            if not path.is_absolute():
                path = Path(__file__).resolve().parent.parent.parent / path
            if not path.exists():
                logger.warning("Arquivo de música não encontrado em %s", path)
                return
            try:
                self._mci_send(f'open "{path}" type mpegvideo alias serpleno_bgm')
                self._mci_send("play serpleno_bgm repeat")
                self._music_playing = True
                self._music_btn.configure(text=ICONS["music"], text_color=self.palette["accent"])
            except Exception as e:
                logger.warning("Erro ao tocar música: %s", e)
        else:
            try:
                self._mci_send("stop serpleno_bgm")
                self._mci_send("close serpleno_bgm")
                self._music_playing = False
                self._music_btn.configure(text=ICONS["music"], text_color=self.palette["text_muted"])
            except Exception:
                pass

    def _mci_send(self, cmd: str) -> None:
        ctypes.windll.winmm.mciSendStringA(cmd.encode("utf-8"), None, 0, None)

    def fazer_login(self) -> None:
        self._fazer_login()

    def _fazer_login(self) -> None:
        if self._is_loading:
            return

        username = self.input_user.get().strip()
        password = self.input_pass.get().strip()

        self.input_user.clear_state()
        self.input_pass.clear_state()
        self.lbl_erro.configure(text="")

        has_error = False
        if not username:
            self.input_user.set_error("Campo obrigatório")
            has_error = True
        if not password:
            self.input_pass.set_error("Campo obrigatório")
            has_error = True
        if has_error:
            self.lbl_erro.configure(
                text="Preencha todos os campos para continuar.", text_color=self.palette["danger"]
            )
            self._shake_card()
            return

        self._is_loading = True
        self.btn_entrar.configure(text="Aguarde...", state="disabled")
        self.update_idletasks()

        login_start = time.perf_counter()

        def _task() -> dict:
            return self.controller_autenticacao.login(username, password)

        def _on_success(result: dict) -> None:
            success = result.get("success", False)
            user = result.get("user", {})
            if success:
                self._on_login_success(user, login_start)
            else:
                msg = result.get("message", "Erro ao fazer login")
                self._on_login_failure(msg)

        def _on_error(exc: Exception) -> None:
            self._on_login_failure(f"Erro de conexão: {exc}")

        AsyncRunner.run(
            task=_task,
            on_success=_on_success,
            on_error=_on_error,
            widget_ref=self,
        )

    def _shake_card(self) -> None:
        self._shake_active = True

        def shake(step: int = 0) -> None:
            if not self.winfo_exists():
                self._shake_active = False
                return
            if step >= _SHAKE_STEPS:
                self.card.place(relx=0.5, rely=0.5, anchor="center", x=0, y=0)
                self._shake_active = False
                return
            offset = -_SHAKE_OFFSET_PX if step % 2 == 0 else _SHAKE_OFFSET_PX
            self.card.place(relx=0.5, rely=0.5, anchor="center", x=offset, y=0)
            self.after(_SHAKE_INTERVAL_MS, lambda: shake(step + 1))

        shake()

    def _on_login_success(self, user: dict, login_start: float | None = None) -> None:
        self._is_loading = False
        self._set_idle_state()
        self.lbl_erro.configure(text="")
        self.controller.iniciar_sistema(
            user, auth_service=self.controller_autenticacao.auth_service, login_start=login_start
        )

    def _on_login_failure(self, msg: str) -> None:
        self._is_loading = False
        self._set_idle_state()
        self.lbl_erro.configure(text=f"{ICONS['cross']}•  {msg}", text_color=self.palette["danger"])
        self.input_pass.set_error("Credenciais inválidas")
        self.input_pass.entry.delete(0, "end")
        self._shake_card()

    def _set_idle_state(self) -> None:
        self.btn_entrar.configure(text="Entrar", state="normal")

    def _abrir_modal(self, titulo: str, texto: str, largura: int, altura: int) -> None:
        top = ctk.CTkToplevel(self)
        top.title(titulo)
        top.geometry(f"{largura}x{altura}")
        top.configure(fg_color=THEME["surface"])
        top.resizable(False, False)
        top.transient(self.winfo_toplevel())
        top.grab_set()
        top.after(
            50,
            lambda: top.geometry(
                f"{largura}x{altura}+{self.winfo_screenwidth() // 2 - largura // 2}"
                f"+{self.winfo_screenheight() // 2 - altura // 2}"
            ),
        )

        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("modal"), pady=spacing("modal"))

        icon_bg = ctk.CTkFrame(
            inner,
            width=_MODAL_ICON_BG_SIZE,
            height=_MODAL_ICON_BG_SIZE,
            corner_radius=RADIUS["avatar"],
            fg_color=self.palette["accent_soft"],
        )
        icon_bg.pack(pady=(0, 14))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=ICONS["lock"], font=themed_font("h3")).place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ctk.CTkLabel(
            inner,
            text=titulo,
            font=themed_font("h4", "bold"),
            text_color=self.palette["text_primary"],
        ).pack(pady=(0, _TITLE_GAP))

        ctk.CTkLabel(
            inner,
            text=texto,
            font=themed_font("body"),
            text_color=self.palette["text_muted"],
            justify="center",
        ).pack(pady=(0, 20))

        PrimaryButton(
            inner,
            text="Entendi",
            command=top.destroy,
            height=40,
            corner_radius=RADIUS["button"],
            width=160,
        ).pack()

    def _abrir_politica(self) -> None:
        self._abrir_modal(
            titulo="Política de Privacidade",
            texto=(
                "O SerPleno trata seus dados com responsabilidade e em\n"
                "conformidade com a LGPD. Esta política garante a proteção\n"
                "de informações pessoais e acadêmicas durante o uso da\n"
                "plataforma."
            ),
            largura=_MODAL_WIDTH_POLICY,
            altura=_MODAL_HEIGHT_POLICY,
        )

    def _abrir_termos(self) -> None:
        self._abrir_modal(
            titulo="Termos de Privacidade",
            texto=(
                "Estes termos regem o uso da plataforma SerPleno e o tratamento\n"
                "de dados pessoais e acadêmicos. Ao acessar o sistema, você concorda\n"
                "com as práticas descritas na Política de Privacidade e com o uso\n"
                "responsável das informações compartilhadas."
            ),
            largura=_MODAL_WIDTH_TERMS,
            altura=_MODAL_HEIGHT_TERMS,
        )
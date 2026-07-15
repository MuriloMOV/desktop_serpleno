import os
import math
import ctypes
import logging
import time
import random
import threading

import customtkinter as ctk
from tkinter import PhotoImage
from PIL import Image, ImageTk, ImageDraw, ImageFilter

from ser_pleno.application.controllers.autenticacao import AutenticacaoController
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font, blend_color
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.presentation.components.ui_components import (
    PrimaryButton, GhostButton, SecondaryButton, InputField, Badge, Divider
)
from ser_pleno.ui.components.icons import ICONS

logger = logging.getLogger("apps.desktop")

_IS_WINDOWS = hasattr(ctypes, "windll")


# —————————————————————————————————————————————
#  Paleta dedicada A  tela de login
# (gradiente e bolhas mantêm identidade própria)
# —————————————————————————————————————————————
_LOGIN_PALETTE = {
    # Gradiente
    "grad_top_left":   "#1E1B4B",
    "grad_top_right":  "#312E81",
    "grad_bottom_left":"#4338CA",
    "grad_bottom":     "#6D5CE8",

        # Card
        "card_bg":     THEME["surface"],
        "card_border": THEME["border"],
        "card_shadow": THEME["overlay"],

        # Acento
        "accent":       THEME["primary"],
        "accent_hover": THEME["primary_hover"],
        "accent_soft":  THEME["primary_soft"],
        "accent_medium":THEME["primary_medium"],

        # Texto
        "text_primary": THEME["text"],
        "text_muted":   THEME["text_secondary"],
        "text_light":   THEME["text_muted"],

        # Estados
        "success": THEME["success"],
        "danger":  THEME["danger"],
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


CARD_W, CARD_H = 444, 640


# —————————————————————————————————————————————
#  Campo de entrada refinado (label flutuante + estados visuais)
# —————————————————————————————————————————————
class LoginInputField(ctk.CTkFrame):
    """Campo de entrada com label, ícone e estados normal/foco/erro/sucesso."""

    def __init__(self, parent, label: str, placeholder: str = "",
                 icon: str = "", password: bool = False):
        super().__init__(parent, fg_color="transparent")
        self._password = password
        self._show_pass = False
        # Resolvidas em tempo de execução (não como atributo de classe) para
        # sempre refletir o tema ativo, mesmo depois de um toggle de modo.
        self._border_normal = THEME["border"]
        self._border_focus = THEME["primary"]
        self._border_error = THEME["danger"]
        self._border_success = THEME["success"]
        self._bg_normal = THEME["bg_alt"]
        self._bg_focus = THEME["surface"]
        self._state = "normal"  # normal | error | success

        self._label = ctk.CTkLabel(
            self, text=label,
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
            anchor="w",
        )
        self._label.pack(fill="x", padx=spacing("sm"), pady=(0, spacing("label_gap")))

        self._box = ctk.CTkFrame(
            self, corner_radius=RADIUS["input"],
            fg_color=self._bg_normal,
            border_width=1,
            border_color=self._border_normal,
        )
        self._box.pack(fill="x")
        self._box.grid_columnconfigure(1, weight=1)

        if icon:
            ctk.CTkLabel(
                self._box, text=icon,
                font=themed_font("body"),
                text_color=THEME["text_secondary"],
                width=36,
            ).grid(row=0, column=0, padx=(spacing("sm"), 0), pady=spacing("md"))

        self.entry = ctk.CTkEntry(
            self._box,
            placeholder_text=placeholder,
            placeholder_text_color=THEME["text_muted"],
            fg_color=self._bg_normal,
            border_width=0,
            text_color=THEME["text"],
            font=themed_font("body"),
            height=42,
            show="●" if password else "",
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=4)

        if password:
            self._eye_btn = ctk.CTkButton(
                self._box, text=ICONS["view"], width=36, height=36,
                fg_color="transparent", hover_color=self._bg_normal,
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=self._toggle_show,
                corner_radius=RADIUS["button"],
                cursor="hand2",
            )
            self._eye_btn.grid(row=0, column=2, padx=(0, 6), pady=4)
            self._eye_btn.bind("<Return>", lambda _: self._toggle_show())
            self._eye_btn.bind("<space>", lambda _: self._toggle_show())
            self._eye_btn.bind("<Return>", lambda _: self._toggle_show())
            self._eye_btn.bind("<space>", lambda _: self._toggle_show())

        self._msg = ctk.CTkLabel(
            self, text="", anchor="w",
            font=themed_font("caption"),
            text_color=THEME["danger"],
        )
        self._msg.pack(fill="x", padx=spacing("sm"), pady=(spacing("xs"), 0))

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    # —— API pública ———————————————————————————————————————————————
    def get(self) -> str:
        return self.entry.get()

    def set_error(self, msg: str = ""):
        self._state = "error"
        self._box.configure(border_color=self._border_error, fg_color=THEME["danger_soft"])
        self._label.configure(text_color=THEME["danger"])
        self._msg.configure(text=f"{ICONS['alert']}   {msg}" if msg else "", text_color=THEME["danger"])

    def set_success(self):
        self._state = "success"
        self._box.configure(border_color=self._border_success, fg_color=THEME["success_soft"])
        self._label.configure(text_color=THEME["success"])
        self._msg.configure(text="")

    def clear_state(self):
        self._state = "normal"
        self._box.configure(border_color=self._border_normal, fg_color=self._bg_normal)
        self._label.configure(text_color=THEME["text_secondary"])
        self._msg.configure(text="")

    # —— Internos ——————————————————————————————————————————————————
    def _on_focus_in(self, _=None):
        self._box.configure(border_color=self._border_focus, fg_color=self._bg_focus)
        self._label.configure(text_color=THEME["primary"])

    def _on_focus_out(self, _=None):
        # Ao perder o foco, só volta ao estado "normal" se não houver um
        # erro/sucesso pendente —” antes disso era resetado incondicionalmente,
        # fazendo o aviso de campo obrigatório sumir visualmente assim que o
        # usuário clicava para fora, mesmo com o campo ainda vazio/inválido.
        if self._state == "error":
            self._box.configure(border_color=self._border_error, fg_color=THEME["danger_soft"])
            self._label.configure(text_color=THEME["danger"])
        elif self._state == "success":
            self._box.configure(border_color=self._border_success, fg_color=THEME["success_soft"])
            self._label.configure(text_color=THEME["success"])
        else:
            self._box.configure(border_color=self._border_normal, fg_color=self._bg_normal)
            self._label.configure(text_color=THEME["text_secondary"])

    def _toggle_show(self):
        self._show_pass = not self._show_pass
        self.entry.configure(show="" if self._show_pass else "●")
        self._eye_btn.configure(text=ICONS["hide"] if self._show_pass else ICONS["view"])


# —————————————————————————————————————————————
#  Frame principal de login
# —————————————————————————————————————————————
class LoginFrame(ctk.CTkFrame):
    _GRADIENT_CACHE_MAX = 3

    def __init__(self, parent, controller):
        self.palette = _LOGIN_PALETTE
        super().__init__(parent, fg_color=self.palette["grad_top_left"])

        self.controller = controller
        self.controller_autenticacao = AutenticacaoController()
        self.bolhas: list[dict] = []
        self._is_loading = False
        self._music_playing = False
        self._alive = True
        self._resize_job = None
        self._bg_draw_job = None
        self._last_bg_size = (0, 0)
        self._gradient_cache: dict[tuple[int, int], ImageTk.PhotoImage] = {}
        self._t_draw_start = 0.0

        self.bind("<Destroy>", self._on_destroy)

        # Canvas de fundo (gradiente + bolhas + sombra e card arredondado via PIL)
        self.canvas = ctk.CTkCanvas(self, highlightthickness=0, bd=0)
        self.canvas.place(relwidth=1, relheight=1)

        self._criar_bolhas()
        self._criar_music_toggle()
        # Card arredondado desenhado no canvas via PIL
        card_img = self._criar_imagem_card()
        self._card_img = card_img
        self._card_img_id = self.canvas.create_image(0, 0, anchor="nw", image=card_img, tags="card_img")
        self.canvas.image_card = card_img
        self._criar_card_login()

        self.bind("<Configure>", self._on_configure)
        # Handler especial para redimensionamento do frame do botão de música
        if hasattr(self, "_music_btn_frame"):
            self._music_btn_frame.bind("<Configure>", self._ajustar_botao_musica)
        # Garante posicionamento inicial do card após a janela ser exibida
        self.after_idle(self._posicionar_card)
        self._animar_bolhas()

    def _on_destroy(self, event):
        # Corta a recursão do after() de animação assim que o frame morre —”
        # antes, o loop de bolhas continuava se reagendando indefinidamente
        # mesmo depois do LoginFrame ser destruído (ex.: após login bem
        # sucedido), pois só adiava a checagem em vez de parar de fato.
        #
        # NOTA: CustomTkinter implementa CTkFrame sobre um canvas interno,
        # então o bind("<Destroy>", ...) feito em `self` na verdade recebe
        # esse widget interno como event.widget —” não dá para comparar com
        # `is self`. Como só existe esta única inscrição, qualquer disparo
        # dela já indica que este LoginFrame está sendo destruído.
        self._alive = False

    # ••••••••••••••••••••••••••••••••••••••
    #  FUNDO —” gradiente diagonal (com debounce de redimensionamento)
    # ••••••••••••••••••••••••••••••••••••••
    def _posicionar_card(self):
        if hasattr(self, "_card_img_id") and hasattr(self, "_card_img"):
            w = self.winfo_width()
            h = self.winfo_height()
            if w > 1 and h > 1:
                card_w, card_h = 444, 720
                card_x = (w - card_w) / 2
                card_y = (h - card_h) / 2
                self.canvas.coords(self._card_img_id, card_x, card_y)

    def _criar_imagem_card_redimensionada(self, width: int, height: int) -> ImageTk.PhotoImage:
        """Cria imagem do card redimensionada para as dimensões especificadas."""
        tamanho_original = (444, 720)
        tamanho_destino = (width, height)

        # Cria nova imagem com fundo branco
        img_original = Image.new("RGBA", tamanho_destino, (255, 255, 255, 255))

        # Aplica bordas arredondadas
        draw = ImageDraw.Draw(img_original)
        draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=20, fill=(255, 255, 255, 255))

        return ImageTk.PhotoImage(img_original)

    def _on_configure(self, event=None):
        if self._bg_draw_job:
            self.after_cancel(self._bg_draw_job)
        self._bg_draw_job = self.after(120, self._desenhar_fundo)
        # Garante posicionamento do card imediatamente, sem esperar redesenho completo
        self.after_idle(self._posicionar_card)

    def _posicionar_card(self):
        if hasattr(self, "_card_img_id") and hasattr(self, "_card_img"):
            w = self.winfo_width()
            h = self.winfo_height()
            if w > 1 and h > 1:
                card_w, card_h = 444, 720
                card_x = (w - card_w) / 2
                card_y = (h - card_h) / 2
                self.canvas.coords(self._card_img_id, card_x, card_y)

    def _criar_imagem_card_redimensionada(self, width: int, height: int) -> ImageTk.PhotoImage:
        """Cria imagem do card redimensionada para as dimensões especificadas."""
        tamanho_original = (444, 720)
        tamanho_destino = (width, height)

        # Cria nova imagem com fundo branco
        img_original = Image.new("RGBA", tamanho_destino, (255, 255, 255, 255))

        # Aplica bordas arredondadas
        draw = ImageDraw.Draw(img_original)
        draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=20, fill=(255, 255, 255, 255))

        return ImageTk.PhotoImage(img_original)

    def _get_or_create_gradient(self, w: int, h: int) -> ImageTk.PhotoImage:
        key = (w, h)
        if key in self._gradient_cache:
            return self._gradient_cache[key]

        top_l = self.palette["grad_top_left"]
        top_r = self.palette["grad_top_right"]
        bot = self.palette["grad_bottom"]
        c_top = _lerp_color(top_l, top_r, 0.5)

        img = Image.new("RGB", (w, h))
        step = 4
        for y in range(0, h, step):
            t = y / h
            color = _lerp_color(c_top, bot, t ** 0.8)
            img.paste(color, (0, y, w, min(y + step, h)))

        photo = ImageTk.PhotoImage(img)
        if len(self._gradient_cache) >= self._GRADIENT_CACHE_MAX:
            self._gradient_cache.pop(next(iter(self._gradient_cache)))
        self._gradient_cache[key] = photo
        return photo

    def _desenhar_fundo(self, event=None):
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
        self.canvas.delete("bg")

        photo = self._get_or_create_gradient(w, h)
        self.canvas.create_image(0, 0, anchor="nw", image=photo, tags="bg")
        self.canvas.create_image(0, 0, anchor="nw", image=photo, tags="bg")
        self.canvas.image_bg = photo

        glow_r = int(w * 0.55)
        self.canvas.create_oval(
            w - glow_r, -glow_r // 2, w + glow_r // 2, glow_r,
            fill=self.palette["grad_bottom"], outline="", tags="bg",
        )
        self.canvas.create_oval(
            -glow_r // 3, h - glow_r // 2, glow_r // 1.5, h + glow_r // 3,
            fill=self.palette["grad_bottom_left"], outline="", tags="bg",
        )

        # Atualiza card redimensionado se necessário
        if hasattr(self, "_card_img_id") and hasattr(self, "_card"):
            card_x = (w - 444) / 2
            card_y = (h - 720) / 2
            self.canvas.coords(self._card_img_id, card_x, card_y)

        # Garante que os elementos de UI fiquem por cima
        self.canvas.tag_lower("bg")
        # Eleva card_img acima do fundo, mas abaixo dos widgets
        if hasattr(self, "_card_img_id"):
            self.canvas.tag_raise("card_img")
            self.canvas.tag_raise("bubble")
        self._elevar_elementos()

        try:
            draw_ms = (time.perf_counter() - self._t_draw_start) * 1000
            if draw_ms > 40:
                logger.warning("PERF login_grad_draw_ms=%.1f size=%dx%d", draw_ms, w, h)
        except Exception:
            pass

    def _elevar_elementos(self):
        for b in self.bolhas:
            if b.get("id"):
                self.canvas.tag_raise(b["id"])
        # Eleva o frame do botão de música para garantir que fique acima das bolhas
        if hasattr(self, "_music_btn_frame"):
            self._music_btn_frame.lift()
        if hasattr(self, "card"):
            self.card.lift()

    # ••••••••••••••••••••••••••••••••••
    #  BOLHAS flutuantes —“ mais delicadas
    # ••••••••••••••••••••••••••••••••••
    def _criar_bolhas(self):
        for _ in range(28):
            x = random.randint(0, 1400)
            y = random.randint(50, 900)
            size = random.randint(14, 80)
            a = random.uniform(0.05, 0.18)

            w_val = min(255, int(200 + 55 * a))
            fill = f"#{w_val:02x}{w_val:02x}{w_val:02x}"

            bid = self.canvas.create_oval(
                x, y, x + size, y + size,
                outline=fill, width=1.2, fill="", tags="bubble",
            )
            rx, ry, rs = x + size * 0.2, y + size * 0.15, size * 0.18
            rid = self.canvas.create_oval(
                rx, ry, rx + rs, ry + rs, fill=fill, outline="", tags="bubble",
            )

            self.bolhas.append({
                "id": bid, "reflex_id": rid,
                "x": float(x), "y": float(y), "size": size,
                "speed": random.uniform(0.10, 0.45),
                "wobble": random.uniform(0, 2 * math.pi),
                "wobble_amp": random.uniform(0.2, 0.7),
            })

    def _animar_bolhas(self):
        if not self._alive or not self.winfo_exists():
            return  # não reagenda —” encerra o loop de vez

        w, h = self.winfo_width(), self.winfo_height()
        if w > 1 and h > 1:
            for b in self.bolhas:
                b["y"] -= b["speed"]
                b["wobble"] += 0.025
                b["x"] += math.sin(b["wobble"]) * b["wobble_amp"]

                if b["y"] + b["size"] < -20:
                    b["y"] = float(h + b["size"] + random.randint(10, 80))
                    b["x"] = float(random.randint(-30, w + 30))
                if b["x"] < -80:
                    b["x"] = float(w + 20)
                elif b["x"] > w + 80:
                    b["x"] = -20.0

                x, y, s = b["x"], b["y"], b["size"]
                self.canvas.coords(b["id"], x, y, x + s, y + s)
                rx, ry, rs = x + s * 0.2, y + s * 0.15, s * 0.18
                self.canvas.coords(b["reflex_id"], rx, ry, rx + rs, ry + rs)

        self.after(22, self._animar_bolhas)

    # ••••••••••••••••••••••••••••••••••••••
    #  CARD DE LOGIN
    # ••••••••••••••••••••••••••••••••••••••
    # ••••••••••••••••••••••••••••••••••••••
    #  CARD DE LOGIN —“ arredondamento no canvas via PIL
    # ••••••••••••••••••••••••••••••••••••••
    def _criar_imagem_card(self):
        """Cria imagem do card com bordas arredondadas usando PIL."""
        tamanho = (444, 720)
        img = Image.new("RGBA", tamanho, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([0, 0, 443, 719], radius=20, fill=(255, 255, 255, 255))
        return ImageTk.PhotoImage(img)

    def _criar_card_login(self):
        # Mantém fundo branco no CTk; o arredondamento visual vem da imagem PIL no canvas
        self.card = ctk.CTkFrame(
            self, width=444, height=720,
            corner_radius=20,
            fg_color=_LOGIN_PALETTE["card_bg"],
            bg_color=_LOGIN_PALETTE["card_bg"],
            border_width=0,
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)
        self.card.lift()

        # Atualiza referência do card para uso no _desenhar_fundo
        self._card = self.card

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("xxl"), pady=spacing("xl"))

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))

        badge = ctk.CTkFrame(
            header, corner_radius=RADIUS["pill"],
            fg_color=self.palette["accent_soft"],
        )
        badge.pack(pady=(0, 10))
        ctk.CTkLabel(
            badge, text="Acesso seguro · Plataforma SerPleno",
            font=themed_font("caption", "bold"),
            text_color=self.palette["accent"],
        ).pack(padx=(16, 16), pady=(6, 6))

        icon_bg = ctk.CTkFrame(
            header, width=68, height=68,
            corner_radius=RADIUS["avatar"],
            fg_color=self.palette["accent_soft"],
        )
        icon_bg.pack(pady=(0, 10))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=ICONS["brain"], font=themed_font("h2"), text_color="#7C3AED").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            header, text="SerPleno", font=themed_font("h2", "bold"),
            text_color=self.palette["text_primary"],
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            header,
            text="Bem-estar, acompanhamento escolar e comunicação integrada",
            font=themed_font("body"),
            text_color=self.palette["text_muted"],
        ).pack()

        info_row = ctk.CTkFrame(inner, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 16))
        for text in [f"{ICONS['lock']} LGPD", f"{ICONS['alert']} Acesso rápido", f"{ICONS['user']} Apoio contínuo"]:
            chip = ctk.CTkFrame(info_row, height=30, corner_radius=RADIUS["pill"], fg_color=THEME["bg_alt"])
            chip.pack(side="left", padx=(0, 8))
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=text, font=themed_font("caption"),
                         text_color=THEME["text_secondary"]).place(relx=0.5, rely=0.5, anchor="center")

        Divider(inner).pack(fill="x", pady=(0, 20))

        self.input_user = LoginInputField(inner, "Usuário", placeholder="Seu nome de usuário", icon=ICONS["user"])
        self.input_user.pack(fill="x", pady=(0, 12))

        self.input_pass = LoginInputField(inner, "Senha", placeholder="Sua senha", icon=ICONS["lock"], password=True)
        self.input_pass.pack(fill="x", pady=(0, 4))

        self.lbl_erro = ctk.CTkLabel(
            inner, text="", text_color=self.palette["danger"],
            font=themed_font("body"), anchor="center", wraplength=340,
        )
        self.lbl_erro.pack(pady=(12, 0))

        self.btn_entrar = PrimaryButton(
            inner, text="Entrar", command=self._fazer_login,
            height=48, corner_radius=RADIUS["lg"],
        )
        self.btn_entrar.pack(fill="x", pady=(14, 8))

        _termos_btn = ctk.CTkButton(
            inner, text=f"{ICONS['lock']}  Termos de Privacidade",
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
        _termos_btn.pack(fill="x", pady=(6, 0))

        self.entry_user = self.input_user.entry
        self.entry_pass = self.input_pass.entry
        self.entry_user.bind("<Return>", lambda _: self._fazer_login())
        self.entry_pass.bind("<Return>", lambda _: self._fazer_login())
        self.entry_user.focus_set()

    # ••••••••••••••••••••••••••••••••••••••
    #  TOGGLE DE MÚSICA (canto inferior direito)
    # ••••••••••••••••••••••••••••••••••••••
    def _criar_music_toggle(self):
        self.music_var = ctk.StringVar(value="off")
        self._music_btn_frame = ctk.CTkFrame(
            self,
            fg_color="transparent",
            width=64,
            height=64
        )
        self._music_btn_frame.pack(
            side="right",
            padx=(16, 16),
            pady=(0, 16),
            anchor="se"
        )
        self._music_btn_frame.pack_propagate(False)

        # Botão circular: corner_radius = metade da largura/altura (48/2 = 24).
        # border_width=0 evita artefatos de renderização no Windows.
        self._music_btn = ctk.CTkButton(
            self._music_btn_frame,
            text=ICONS["music"],
            width=48,
            height=48,
            corner_radius=24,
            font=themed_font("h3"),
            fg_color=_LOGIN_PALETTE["card_bg"],
            hover_color=_LOGIN_PALETTE["accent_soft"],
            text_color=_LOGIN_PALETTE["text_muted"],
            border_width=0,
            command=self._toggle_music,
            cursor="hand2",
        )
        self._music_btn.place(relx=0.5, rely=0.5, anchor="center")
        if not _IS_WINDOWS:
            # Playback via winmm só existe no Windows. Em vez de deixar o
            # botão quebrar o app com AttributeError em Linux/Mac (o código
            # original chamava ctypes.windll incondicionalmente), avisamos
            # visualmente que o recurso é indisponível nesta plataforma.
            from ser_pleno.presentation.components.ui_components import Tooltip
            Tooltip(self._music_btn, "Música de fundo disponível apenas no Windows")

    def _ajustar_botao_musica(self, event=None):
        if hasattr(self, "_music_btn_frame") and self._music_btn_frame.winfo_exists():
            w = self._music_btn_frame.winfo_width()
            h = self._music_btn_frame.winfo_height()
            if w > 1 and h > 1:
                try:
                    self._music_btn.place(relx=0.5, rely=0.5, anchor="center")
                except Exception:
                    pass

    def _toggle_music(self):
        if not _IS_WINDOWS:
            return
        is_playing = getattr(self, "_music_playing", False)
        if not is_playing:
            path = "assets/Music/background_music.mp3"
            if not os.path.exists(path):
                logger.warning("Arquivo de música não encontrado em %s", path)
                return
            try:
                self._mci_send(f'open "{path}" type mpegvideo alias serpleno_bgm')
                self._mci_send("play serpleno_bgm repeat")
                self._music_playing = True
                self._music_btn.configure(text=ICONS["music"], text_color=THEME["primary"])
            except Exception as e:
                logger.warning("Erro ao tocar música: %s", e)
        else:
            try:
                self._mci_send("stop serpleno_bgm")
                self._mci_send("close serpleno_bgm")
                self._music_playing = False
                self._music_btn.configure(text=ICONS["music"], text_color=THEME["text_secondary"])
            except Exception:
                pass

    def _mci_send(self, cmd: str) -> None:
        import ctypes
        ctypes.windll.winmm.mciSendStringA(cmd.encode("utf-8"), None, 0, None)

    # ••••••••••••••••••••••••••••••••••••••
    #  LÓGICA DE LOGIN
    # ••••••••••••••••••••••••••••••••••••••
    def fazer_login(self):
        self._fazer_login()

    def _fazer_login(self):
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
            self.lbl_erro.configure(text="Preencha todos os campos para continuar.",
                                     text_color=self.palette["danger"])
            self._shake_card()
            return

        self._is_loading = True
        self.btn_entrar.configure(text="Aguarde...", state="disabled")
        self.update_idletasks()

        def run_login():
            try:
                result = self.controller_autenticacao.login(username, password)
                success = result.get("success", False)
                user = result.get("user", {})
                if success:
                    self.after(0, lambda: self._on_login_success(user))
                else:
                    msg = result.get("message", "Erro ao fazer login")
                    self.after(0, lambda: self._on_login_failure(msg))
            except Exception as e:
                self.after(0, lambda: self._on_login_failure(f"Erro de conexão: {e}"))

        threading.Thread(target=run_login, daemon=True).start()

    def _shake_card(self):
        def shake(step=0):
            if not self.winfo_exists():
                return
            if step >= 8:
                self.card.place(relx=0.5, rely=0.5, anchor="center", x=0, y=0)
                return
            offset = -5 if step % 2 == 0 else 5
            self.card.place(relx=0.5, rely=0.5, anchor="center", x=offset, y=0)
            self.after(38, lambda: shake(step + 1))
        shake()

    def _ajustar_botao_musica(self, event=None):
        """Garante posicionamento correto do botão de música após redimensionamento."""
        if hasattr(self, "_music_btn_frame"):
            w = self._music_btn_frame.winfo_width()
            h = self._music_btn_frame.winfo_height()
            if w > 1 and h > 1:
                try:
                    self._music_btn.place(relx=0.5, rely=0.5, anchor="center")
                except Exception:
                    pass
        return "break"  # Impede propagação do evento

    def _on_login_success(self, user):
        self._is_loading = False
        self._set_idle_state()
        self.lbl_erro.configure(text="")
        self.controller.iniciar_sistema(user, auth_service=self.controller_autenticacao.auth_service)

    def _on_login_failure(self, msg):
        self._is_loading = False
        self._set_idle_state()
        self.lbl_erro.configure(text=f"{ICONS['cross']}•  {msg}", text_color=self.palette["danger"])
        self.input_pass.set_error("Credenciais inválidas")
        self.input_pass.entry.delete(0, "end")
        self._shake_card()

    def _set_idle_state(self):
        self.btn_entrar.configure(text="Entrar", state="normal")

    # ••••••••••••••••••••••••••••••••••••••
    #  POLÍTICA DE PRIVACIDADE
    # ••••••••••••••••••••••••••••••••••••••
    def _abrir_politica(self):
        top = ctk.CTkToplevel(self)
        top.title("Política de Privacidade")
        top.geometry("440x360")
        top.configure(fg_color=THEME["surface"])
        top.resizable(False, False)
        top.transient(self.winfo_toplevel())
        top.grab_set()
        top.after(50, lambda: top.geometry(
            f"440x360+{self.winfo_screenwidth() // 2 - 220}+{self.winfo_screenheight() // 2 - 180}"
        ))

        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("modal"), pady=spacing("modal"))

        icon_bg = ctk.CTkFrame(inner, width=52, height=52, corner_radius=RADIUS["avatar"],
                               fg_color=self.palette["accent_soft"])
        icon_bg.pack(pady=(0, 14))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=ICONS["lock"], font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text="Política de Privacidade", font=themed_font("h4", "bold"),
            text_color=self.palette["text_primary"],
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            inner,
            text=(
                "O SerPleno trata seus dados com responsabilidade e em\n"
                "conformidade com a LGPD. Esta política garante a proteção\n"
                "de informações pessoais e acadêmicas durante o uso da\n"
                "plataforma."
            ),
            font=themed_font("body"),
            text_color=self.palette["text_muted"],
            justify="center",
        ).pack(pady=(0, 20))

        PrimaryButton(inner, text="Entendi", command=top.destroy, height=40,
                      corner_radius=RADIUS["button"], width=160).pack()

    def _abrir_termos(self):
        top = ctk.CTkToplevel(self)
        top.title("Termos de Privacidade")
        top.geometry("480x420")
        top.configure(fg_color=THEME["surface"])
        top.resizable(False, False)
        top.transient(self.winfo_toplevel())
        top.grab_set()
        top.after(50, lambda: top.geometry(
            f"480x420+{self.winfo_screenwidth() // 2 - 240}+{self.winfo_screenheight() // 2 - 210}"
        ))

        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("modal"), pady=spacing("modal"))

        icon_bg = ctk.CTkFrame(inner, width=52, height=52, corner_radius=RADIUS["avatar"],
                               fg_color=self.palette["accent_soft"])
        icon_bg.pack(pady=(0, 14))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=ICONS["lock"], font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text="Termos de Privacidade", font=themed_font("h4", "bold"),
            text_color=self.palette["text_primary"],
        ).pack(pady=(0, 12))

        ctk.CTkLabel(
            inner,
            text=(
                "Estes termos regem o uso da plataforma SerPleno e o tratamento\n"
                "de dados pessoais e acadêmicos. Ao acessar o sistema, você concorda\n"
                "com as práticas descritas na Política de Privacidade e com o uso\n"
                "responsável das informações compartilhadas."
            ),
            font=themed_font("body"),
            text_color=self.palette["text_muted"],
            justify="center",
        ).pack(pady=(0, 20))

        PrimaryButton(inner, text="Entendi", command=top.destroy, height=40,
                      corner_radius=RADIUS["button"], width=160).pack()


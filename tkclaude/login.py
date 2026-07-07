import os
import logging
import math
import platform
import random
import threading

import customtkinter as ctk
from tkinter import PhotoImage
from PIL import Image, ImageTk, ImageDraw, ImageFilter

from services.autenticacao import ServicoAutenticacao
from services.agendamentos import set_auth_service as set_auth_service_agendamentos
from services.api import set_auth_service as set_auth_service_api
from ui_theme import THEME, RADIUS, themed_font
from components.ui_components import PrimaryButton, GhostButton, Divider

logger = logging.getLogger("apps.desktop")

_IS_WINDOWS = platform.system() == "Windows"


def _build_login_palette() -> dict:
    """Monta a paleta da tela de login lendo o THEME *no momento da chamada*.

    Antes este dicionário era construído uma única vez no nível do módulo
    (na importação), então se o usuário alternasse para o modo escuro e
    voltasse à tela de login, ela continuaria usando cores antigas para
    sempre — o mesmo problema de "valor padrão congelado" corrigido em
    ui_components.py, só que em formato de dicionário de módulo.
    """
    return {
        # Gradiente — identidade própria da tela de login, não segue o tema
        "grad_top_left":    "#1E1B4B",
        "grad_top_right":   "#312E81",
        "grad_bottom_left": "#4338CA",
        "grad_bottom":      "#6D5CE8",

        # Card
        "card_bg":     THEME["surface"],
        "card_border": THEME["border"],
        "card_shadow": THEME["overlay"],

        # Acento
        "accent":       THEME["primary"],
        "accent_hover": THEME["primary_hover"],
        "accent_soft":  THEME["primary_soft"],

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


CARD_W, CARD_H = 444, 582


# ─────────────────────────────────────────────
#  Campo de entrada refinado (label flutuante + estados visuais)
# ─────────────────────────────────────────────
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
        self._label.pack(fill="x", padx=2, pady=(0, 4))

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
            ).grid(row=0, column=0, padx=(10, 0), pady=10)

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
                self._box, text="👁", width=36, height=36,
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

        self._msg = ctk.CTkLabel(
            self, text="", anchor="w",
            font=themed_font("caption"),
            text_color=THEME["danger"],
        )
        self._msg.pack(fill="x", padx=2, pady=(3, 0))

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    # ── API pública ───────────────────────────────────────────────
    def get(self) -> str:
        return self.entry.get()

    def set_error(self, msg: str = ""):
        self._state = "error"
        self._box.configure(border_color=self._border_error, fg_color=THEME["danger_soft"])
        self._label.configure(text_color=THEME["danger"])
        self._msg.configure(text=f"⚠  {msg}" if msg else "", text_color=THEME["danger"])

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

    # ── Internos ──────────────────────────────────────────────────
    def _on_focus_in(self, _=None):
        self._box.configure(border_color=self._border_focus, fg_color=self._bg_focus)
        self._label.configure(text_color=THEME["primary"])

    def _on_focus_out(self, _=None):
        # Ao perder o foco, só volta ao estado "normal" se não houver um
        # erro/sucesso pendente — antes disso era resetado incondicionalmente,
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
        self._eye_btn.configure(text="🙈" if self._show_pass else "👁")


# ─────────────────────────────────────────────
#  Frame principal de login
# ─────────────────────────────────────────────
class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        self.palette = _build_login_palette()
        super().__init__(parent, fg_color=self.palette["grad_top_left"])

        self.controller = controller
        self.servico_autenticacao = ServicoAutenticacao()
        self.bolhas: list[dict] = []
        self._is_loading = False
        self._music_playing = False
        self._alive = True
        self._resize_job = None
        self._last_bg_size = (0, 0)

        self.bind("<Destroy>", self._on_destroy)

        self.canvas = ctk.CTkCanvas(self, highlightthickness=0, bd=0)
        self.canvas.place(relwidth=1, relheight=1)

        self._criar_bolhas()
        self._criar_music_toggle()

        # Imagem do card (com sombra suave) é fixa em tamanho — criada uma
        # única vez, nunca recriada em resize (antes era regenerada via PIL
        # a cada evento <Configure>, sempre com o mesmo tamanho constante,
        # ou seja, refazendo um trabalho idêntico repetidamente à toa).
        self._card_img = self._criar_imagem_card()
        self._card_img_id = self.canvas.create_image(0, 0, anchor="nw", image=self._card_img, tags="card_img")

        self._criar_card_login()

        self.bind("<Configure>", self._on_resize)
        if hasattr(self, "_music_btn_frame"):
            self._music_btn_frame.bind("<Configure>", self._ajustar_botao_musica)

        self.after_idle(self._desenhar_fundo)
        self._animar_bolhas()

    def _on_destroy(self, event):
        # Corta a recursão do after() de animação assim que o frame morre —
        # antes, o loop de bolhas continuava se reagendando indefinidamente
        # mesmo depois do LoginFrame ser destruído (ex.: após login bem
        # sucedido), pois só adiava a checagem em vez de parar de fato.
        #
        # NOTA: CustomTkinter implementa CTkFrame sobre um canvas interno,
        # então o bind("<Destroy>", ...) feito em `self` na verdade recebe
        # esse widget interno como event.widget — não dá para comparar com
        # `is self`. Como só existe esta única inscrição, qualquer disparo
        # dela já indica que este LoginFrame está sendo destruído.
        self._alive = False

    # ══════════════════════════════════════
    #  FUNDO — gradiente diagonal (com debounce de redimensionamento)
    # ══════════════════════════════════════
    def _on_resize(self, event=None):
        # O evento <Configure> dispara continuamente durante um arraste de
        # redimensionamento da janela. Recalcular o gradiente pixel-a-pixel
        # a cada disparo travava visivelmente a UI; agora só redesenhamos
        # ~80ms depois que o usuário parar de redimensionar.
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(80, self._desenhar_fundo)

    def _posicionar_card(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w > 1 and h > 1:
            self.canvas.coords(self._card_img_id, (w - CARD_W) / 2, (h - CARD_H) / 2)

    def _desenhar_fundo(self):
        self._resize_job = None
        if not self._alive or not self.winfo_exists():
            return
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            return
        if (w, h) == self._last_bg_size:
            self._posicionar_card()
            return
        self._last_bg_size = (w, h)

        self.canvas.delete("bg")

        top_l = self.palette["grad_top_left"]
        top_r = self.palette["grad_top_right"]
        bot = self.palette["grad_bottom"]
        c_top = _lerp_color(top_l, top_r, 0.5)

        img = PhotoImage(width=w, height=h)
        # Passo de 2px: reduz pela metade o custo do laço em janelas grandes
        # sem perda visível de suavidade no gradiente.
        step = 2 if h > 700 else 1
        for y in range(0, h, step):
            t = y / h
            color = _lerp_color(c_top, bot, t ** 0.8)
            img.put(color, to=(0, y, w, min(y + step, h)))

        self.canvas.create_image(0, 0, anchor="nw", image=img, tags="bg")
        self.canvas.image = img  # mantém referência viva

        glow_r = int(w * 0.55)
        self.canvas.create_oval(
            w - glow_r, -glow_r // 2, w + glow_r // 2, glow_r,
            fill=self.palette["grad_bottom"], outline="", tags="bg",
        )
        self.canvas.create_oval(
            -glow_r // 3, h - glow_r // 2, glow_r // 1.5, h + glow_r // 3,
            fill=self.palette["grad_bottom_left"], outline="", tags="bg",
        )

        self.canvas.tag_lower("bg")
        self.canvas.tag_raise("card_img")
        self.canvas.tag_raise("bubble")
        self._posicionar_card()
        self._elevar_elementos()

    def _elevar_elementos(self):
        for b in self.bolhas:
            if b.get("id"):
                self.canvas.tag_raise(b["id"])
        if hasattr(self, "_music_btn_frame"):
            self._music_btn_frame.lift()
        if hasattr(self, "card"):
            self.card.lift()

    # ══════════════════════════════════
    #  BOLHAS flutuantes
    # ══════════════════════════════════
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
            return  # não reagenda — encerra o loop de vez

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

    # ══════════════════════════════════════
    #  CARD DE LOGIN
    # ══════════════════════════════════════
    def _criar_imagem_card(self) -> ImageTk.PhotoImage:
        """Card branco com bordas arredondadas e sombra suave (desenhada uma
        única vez com PIL). Antes a sombra era só mencionada em comentário —
        `ImageFilter` estava importado mas nunca usado."""
        padding = 24  # espaço extra para a sombra não ser cortada
        total_w, total_h = CARD_W + padding * 2, CARD_H + padding * 2

        shadow = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.rounded_rectangle(
            [padding, padding + 8, padding + CARD_W, padding + CARD_H + 8],
            radius=20, fill=(15, 15, 35, 70),
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(14))

        card = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        cdraw = ImageDraw.Draw(card)
        cdraw.rounded_rectangle([0, 0, CARD_W - 1, CARD_H - 1], radius=20, fill=(255, 255, 255, 255))
        shadow.alpha_composite(card, (padding, padding))

        self._card_offset = padding
        return ImageTk.PhotoImage(shadow)

    def _criar_card_login(self):
        self.card = ctk.CTkFrame(
            self, width=CARD_W, height=CARD_H,
            corner_radius=0,
            fg_color=self.palette["card_bg"],
            bg_color=self.palette["card_bg"],
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)
        self.card.lift()

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40, pady=36)

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))

        badge = ctk.CTkFrame(
            header, height=32, corner_radius=RADIUS["pill"],
            fg_color=self.palette["accent_soft"],
        )
        badge.pack(pady=(0, 10))
        badge.pack_propagate(False)
        ctk.CTkLabel(
            badge, text="Acesso seguro · Plataforma SerPleno",
            font=themed_font("caption", "bold"),
            text_color=self.palette["accent"],
        ).place(relx=0.5, rely=0.5, anchor="center")

        icon_bg = ctk.CTkFrame(
            header, width=68, height=68,
            corner_radius=RADIUS["avatar"],
            fg_color=self.palette["accent_soft"],
        )
        icon_bg.pack(pady=(0, 10))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="🧠", font=themed_font("h2")).place(relx=0.5, rely=0.5, anchor="center")

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
        for text in ["🔒 LGPD", "⚡ Acesso rápido", "🤝 Apoio contínuo"]:
            chip = ctk.CTkFrame(info_row, height=30, corner_radius=RADIUS["pill"], fg_color=THEME["bg_alt"])
            chip.pack(side="left", padx=(0, 8))
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=text, font=themed_font("caption"),
                         text_color=THEME["text_secondary"]).place(relx=0.5, rely=0.5, anchor="center")

        Divider(inner).pack(fill="x", pady=(0, 20))

        self.input_user = LoginInputField(inner, "Usuário", placeholder="Seu nome de usuário", icon="👤")
        self.input_user.pack(fill="x", pady=(0, 12))

        self.input_pass = LoginInputField(inner, "Senha", placeholder="Sua senha", icon="🔒", password=True)
        self.input_pass.pack(fill="x", pady=(0, 4))

        self.lbl_erro = ctk.CTkLabel(
            inner, text="", text_color=self.palette["danger"],
            font=themed_font("body"), anchor="center",
        )
        self.lbl_erro.pack(pady=(8, 0))

        self.btn_entrar = PrimaryButton(
            inner, text="Entrar", command=self._fazer_login,
            height=48, corner_radius=RADIUS["lg"],
        )
        self.btn_entrar.pack(fill="x", pady=(14, 8))

        GhostButton(
            inner, text="🔒  Política de Privacidade", command=self._abrir_politica,
            height=34, corner_radius=RADIUS["button"], text_color=self.palette["text_muted"],
        ).pack(fill="x")

        self.entry_user = self.input_user.entry
        self.entry_pass = self.input_pass.entry
        self.entry_user.bind("<Return>", lambda _: self._fazer_login())
        self.entry_pass.bind("<Return>", lambda _: self._fazer_login())
        self.entry_user.focus_set()

    # ══════════════════════════════════════
    #  TOGGLE DE MÚSICA (canto inferior direito)
    # ══════════════════════════════════════
    def _criar_music_toggle(self):
        self._music_btn_frame = ctk.CTkFrame(self, fg_color="transparent", width=64, height=64)
        self._music_btn_frame.pack(side="right", padx=(16, 16), pady=(0, 16), anchor="se")
        self._music_btn_frame.pack_propagate(False)

        # corner_radius baixo e border_width=0 evitam um bug conhecido do
        # CustomTkinter no Windows (artefatos pretos nas bordas quando
        # corner_radius e border_width são combinados).
        self._music_btn = ctk.CTkButton(
            self._music_btn_frame,
            text="♪",
            width=48, height=48, corner_radius=8,
            font=themed_font("h3"),
            fg_color="white",
            hover_color=self.palette["accent_soft"],
            text_color=THEME["text_secondary"],
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
            from components.ui_components import Tooltip
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
                self._music_btn.configure(text="♬", text_color=THEME["primary"])
            except Exception as e:
                logger.warning("Erro ao tocar música: %s", e)
        else:
            try:
                self._mci_send("stop serpleno_bgm")
                self._mci_send("close serpleno_bgm")
                self._music_playing = False
                self._music_btn.configure(text="♪", text_color=THEME["text_secondary"])
            except Exception:
                pass

    def _mci_send(self, cmd: str) -> None:
        import ctypes
        ctypes.windll.winmm.mciSendStringA(cmd.encode("utf-8"), None, 0, None)

    # ══════════════════════════════════════
    #  LÓGICA DE LOGIN
    # ══════════════════════════════════════
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
        self.lbl_erro.configure(text="Autenticando...", text_color=self.palette["text_muted"])
        self.btn_entrar.configure(text="Aguarde...", state="disabled")
        self.update_idletasks()

        def run_login():
            try:
                result = self.servico_autenticacao.login(username, password)
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

    def _on_login_success(self, user):
        self._is_loading = False
        self._set_idle_state()
        self.lbl_erro.configure(text="")
        set_auth_service_agendamentos(self.servico_autenticacao)
        set_auth_service_api(self.servico_autenticacao)
        self.controller.iniciar_sistema(user)

    def _on_login_failure(self, msg):
        self._is_loading = False
        self._set_idle_state()
        self.lbl_erro.configure(text=f"✕  {msg}", text_color=self.palette["danger"])
        self.input_pass.set_error("Credenciais inválidas")
        self.input_pass.entry.delete(0, "end")
        self._shake_card()

    def _set_idle_state(self):
        self.btn_entrar.configure(text="Entrar", state="normal")

    # ══════════════════════════════════════
    #  POLÍTICA DE PRIVACIDADE
    # ══════════════════════════════════════
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
        inner.pack(fill="both", expand=True, padx=32, pady=32)

        icon_bg = ctk.CTkFrame(inner, width=52, height=52, corner_radius=RADIUS["avatar"],
                               fg_color=self.palette["accent_soft"])
        icon_bg.pack(pady=(0, 14))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="🔒", font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")

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

import os
import ctypes
import customtkinter as ctk
import random
import math
import threading
import tkinter
from tkinter import PhotoImage

from services.autenticacao import ServicoAutenticacao
from services.agendamentos import set_auth_service as set_auth_service_agendamentos
from services.api import set_auth_service as set_auth_service_api
from ui_theme import THEME, SPACING, RADIUS, font, themed_font, blend_color
from components.ui_components import (
    PrimaryButton, GhostButton, InputField, Badge, Divider
)


# ─────────────────────────────────────────────
#  Paleta dedicada à tela de login
# (gradiente e bolhas mantêm identidade própria)
# ─────────────────────────────────────────────
_LOGIN_PALETTE = {
    # Gradiente
    "grad_top_left":   "#1E1B4B",
    "grad_top_right":  "#312E81",
    "grad_bottom_left":"#4338CA",
    "grad_bottom":     "#6D5CE8",

    # Card
    "card_bg":         THEME["surface"],
    "card_border":     THEME["border"],
    "card_shadow":     THEME["overlay"],

    # Acento
    "accent":          THEME["primary"],
    "accent_hover":    THEME["primary_hover"],
    "accent_soft":     THEME["primary_soft"],

    # Texto (usa tokens globais)
    "text_primary":    THEME["text"],
    "text_muted":      THEME["text_secondary"],
    "text_light":      THEME["text_muted"],

    # Estados
    "success":         THEME["success"],
    "danger":          THEME["danger"],
    "warning":         THEME["warning"],
}


def _hex_to_rgb(hex_c: str):
    h = hex_c.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_color(c1_hex, c2_hex, t):
    r1, g1, b1 = _hex_to_rgb(c1_hex)
    r2, g2, b2 = _hex_to_rgb(c2_hex)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ─────────────────────────────────────────────
#  Campos de entrada refinados
# ─────────────────────────────────────────────
class LoginInputField(ctk.CTkFrame):
    """
    Campo de entrada com label flutuante, ícone e
    estados visuais (normal / foco / erro / sucesso).
    """
    _BORDER_NORMAL  = THEME["border"]
    _BORDER_FOCUS   = THEME["primary"]
    _BORDER_ERROR   = THEME["danger"]
    _BORDER_SUCCESS = THEME["success"]
    _BG             = THEME["bg_alt"]
    _BG_FOCUS       = THEME["surface"]

    def __init__(self, parent, label: str, placeholder: str = "",
                 icon: str = "", password: bool = False):
        super().__init__(parent, fg_color="transparent")
        self._password = password
        self._show_pass = False

        # ── Label topo ──────────────────────────────────────────────
        self._label = ctk.CTkLabel(
            self, text=label,
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
            anchor="w",
        )
        self._label.pack(fill="x", padx=2, pady=(0, 4))

        # ── Container do campo ──────────────────────────────────────
        self._box = ctk.CTkFrame(
            self, corner_radius=RADIUS["input"],
            fg_color=self._BG,
            border_width=1,
            border_color=self._BORDER_NORMAL,
        )
        self._box.pack(fill="x")
        self._box.grid_columnconfigure(1, weight=1)

        # Ícone esquerdo
        if icon:
            ctk.CTkLabel(
                self._box, text=icon,
                font=themed_font("body"),
                text_color=THEME["text_secondary"],
                width=36,
            ).grid(row=0, column=0, padx=(10, 0), pady=10)

        # Entry
        self.entry = ctk.CTkEntry(
            self._box,
            placeholder_text=placeholder,
            placeholder_text_color=THEME["text_muted"],
            fg_color=THEME["bg_alt"],
            border_width=0,
            text_color=THEME["text"],
            font=themed_font("body"),
            height=42,
            show="" if not password else "●",
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=4)

        # Botão mostrar/ocultar senha
        if password:
            self._eye_btn = ctk.CTkButton(
                self._box, text="👁", width=36, height=36,
                fg_color="transparent", hover_color=THEME["bg_alt"],
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=self._toggle_show,
                corner_radius=RADIUS["button"],
            )
            self._eye_btn.grid(row=0, column=2, padx=(0, 6), pady=4)

        # ── Mensagem de erro/ajuda ───────────────────────────────────
        self._msg = ctk.CTkLabel(
            self, text="", anchor="w",
            font=themed_font("caption"),
            text_color=THEME["danger"],
        )
        self._msg.pack(fill="x", padx=2, pady=(3, 0))

        # Foco
        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    # ── API ────────────────────────────────────────────────────────
    def get(self) -> str:
        return self.entry.get()

    def set_error(self, msg: str = ""):
        self._box.configure(border_color=self._BORDER_ERROR, fg_color=THEME["danger_soft"])
        self._label.configure(text_color=THEME["danger"])
        self._msg.configure(text=f"⚠  {msg}" if msg else "", text_color=THEME["danger"])

    def set_success(self):
        self._box.configure(border_color=self._BORDER_SUCCESS, fg_color=THEME["success_soft"])
        self._label.configure(text_color=THEME["success"])
        self._msg.configure(text="")

    def clear_state(self):
        self._box.configure(border_color=self._BORDER_NORMAL, fg_color=self._BG)
        self._label.configure(text_color=THEME["text_secondary"])
        self._msg.configure(text="")

    # ── Internos ───────────────────────────────────────────────────
    def _on_focus_in(self, _=None):
        self._box.configure(border_color=self._BORDER_FOCUS, fg_color=self._BG_FOCUS)
        self._label.configure(text_color=THEME["primary"])

    def _on_focus_out(self, _=None):
        # Volta ao normal a menos que esteja em estado de erro/sucesso
        self._box.configure(border_color=self._BORDER_NORMAL, fg_color=self._BG)
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
        super().__init__(parent, fg_color=_LOGIN_PALETTE["grad_top_left"])

        self.controller  = controller
        self.servico_autenticacao = ServicoAutenticacao()
        self.bolhas: list[dict] = []
        self._is_loading = False
        self._music_playing = False

        # Canvas de fundo (gradiente + bolhas)
        self.canvas = ctk.CTkCanvas(self, highlightthickness=0, bd=0)
        self.canvas.place(relwidth=1, relheight=1)

        self._criar_bolhas()
        self._criar_card_login()
        self._criar_music_toggle()

        self.bind("<Configure>", self._desenhar_fundo)
        self._animar_bolhas()

    # ══════════════════════════════════════
    #  FUNDO – gradiente diagonal suave (pré-renderizado)
    # ══════════════════════════════════════
    def _desenhar_fundo(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return

        self.canvas.delete("bg")

        top_l  = _LOGIN_PALETTE["grad_top_left"]
        top_r  = _LOGIN_PALETTE["grad_top_right"]
        bot    = _LOGIN_PALETTE["grad_bottom"]

        # Pré-renderiza gradiente em buffer para evitar retângulos individuais
        img = PhotoImage(width=w, height=h)
        for y in range(h):
            t = y / h
            c_top = _lerp_color(top_l, top_r, 0.5)
            color = _lerp_color(c_top, bot, t ** 0.8)
            img.put(color, to=(0, y, w, y + 1))

        self.canvas.create_image(0, 0, anchor="nw", image=img)
        self.canvas.image = img  # mantém referência viva

        # Elipse decorativa (brilho suave no canto superior direito)
        glow_r = int(w * 0.55)
        self.canvas.create_oval(
            w - glow_r, -glow_r // 2,
            w + glow_r // 2, glow_r,
            fill=_LOGIN_PALETTE["grad_bottom"], outline="", tags="bg"
        )
        # Segundo brilho inferior esquerdo
        self.canvas.create_oval(
            -glow_r // 3, h - glow_r // 2,
            glow_r // 1.5, h + glow_r // 3,
            fill=_LOGIN_PALETTE["grad_bottom_left"], outline="", tags="bg"
        )

        # Garante que os elementos de UI fiquem por cima
        self.canvas.tag_lower("bg")
        self._elevar_elementos()

    def _elevar_elementos(self):
        for b in self.bolhas:
            if b.get("id"):
                self.canvas.tag_raise(b["id"])
        if hasattr(self, "card"):
            self.card.lift()
        if hasattr(self, "music_frame"):
            self.music_frame.lift()

    # ══════════════════════════════════════
    #  BOLHAS flutuantes – mais delicadas
    # ══════════════════════════════════════
    def _criar_bolhas(self):
        for _ in range(28):
            x    = random.randint(0, 1400)
            y    = random.randint(50, 900)
            size = random.randint(14, 80)
            a    = random.uniform(0.05, 0.18)

            # Borda branca levemente transparente
            w_val = min(255, int(200 + 55 * a))
            fill  = f"#{w_val:02x}{w_val:02x}{w_val:02x}"

            bid = self.canvas.create_oval(
                x, y, x + size, y + size,
                outline=fill, width=1.2, fill="",
                tags="bubble",
            )
            # Reflexo interno (bolinha menor)
            rx, ry, rs = x + size * 0.2, y + size * 0.15, size * 0.18
            rid = self.canvas.create_oval(
                rx, ry, rx + rs, ry + rs,
                fill=fill, outline="", tags="bubble",
            )

            self.bolhas.append({
                "id": bid, "reflex_id": rid,
                "x": float(x), "y": float(y), "size": size,
                "speed": random.uniform(0.10, 0.45),
                "wobble": random.uniform(0, 2 * math.pi),
                "wobble_amp": random.uniform(0.2, 0.7),
            })

    def _animar_bolhas(self):
        if not self.winfo_exists():
            self.after(30, self._animar_bolhas)
            return

        w = self.winfo_width()
        h = self.winfo_height()

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

                rx = x + s * 0.2
                ry = y + s * 0.15
                rs = s * 0.18
                self.canvas.coords(b["reflex_id"], rx, ry, rx + rs, ry + rs)

        self.after(22, self._animar_bolhas)

    # ══════════════════════════════════════
    #  CARD DE LOGIN
    # ══════════════════════════════════════
    def _criar_card_login(self):
        # Sombra simulada (frame ligeiramente maior, mais escuro)
        shadow = ctk.CTkFrame(
            self, width=448, height=588,
            corner_radius=RADIUS["2xl"],
            fg_color=_LOGIN_PALETTE["card_shadow"],
            border_width=0,
            bg_color=_LOGIN_PALETTE["grad_top_left"],
        )
        shadow.place(relx=0.5, rely=0.5, anchor="center", x=4, y=6)

        # Card principal
        self.card = ctk.CTkFrame(
            self, width=444, height=582,
            corner_radius=RADIUS["2xl"],
            fg_color=_LOGIN_PALETTE["card_bg"],
            border_width=1,
            border_color=_LOGIN_PALETTE["card_border"],
            bg_color=_LOGIN_PALETTE["grad_top_left"],
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)
        self.card.lift()

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40, pady=36)

        # ── Cabeçalho ─────────────────────────────────────────────
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))

        badge = ctk.CTkFrame(
            header, height=32, corner_radius=RADIUS["pill"],
            fg_color=_LOGIN_PALETTE["accent_soft"],
        )
        badge.pack(pady=(0, 10))
        badge.pack_propagate(False)
        ctk.CTkLabel(
            badge, text="Acesso seguro · Plataforma SerPleno",
            font=themed_font("caption", "bold"),
            text_color=_LOGIN_PALETTE["accent"],
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Ícone num círculo
        icon_bg = ctk.CTkFrame(
            header, width=68, height=68,
            corner_radius=RADIUS["avatar"],
            fg_color=_LOGIN_PALETTE["accent_soft"],
        )
        icon_bg.pack(pady=(0, 10))
        icon_bg.pack_propagate(False)

        ctk.CTkLabel(
            icon_bg, text="🧠",
            font=themed_font("h2"),
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            header,
            text="SerPleno",
            font=themed_font("h2", "bold"),
            text_color=_LOGIN_PALETTE["text_primary"],
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            header,
            text="Bem-estar, acompanhamento escolar e comunicação integrada",
            font=themed_font("body"),
            text_color=_LOGIN_PALETTE["text_muted"],
        ).pack()

        info_row = ctk.CTkFrame(inner, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 16))
        for text in ["🔒 LGPD", "⚡ Acesso rápido", "🤝 Apoio contínuo"]:
            chip = ctk.CTkFrame(info_row, height=30, corner_radius=RADIUS["pill"], fg_color=THEME["bg_alt"])
            chip.pack(side="left", padx=(0, 8))
            chip.pack_propagate(False)
            ctk.CTkLabel(chip, text=text, font=themed_font("caption"), text_color=THEME["text_secondary"]).place(relx=0.5, rely=0.5, anchor="center")

        # ── Divider sutil ──────────────────────────────────────────
        Divider(inner).pack(fill="x", pady=(0, 20))

        # ── Campos ────────────────────────────────────────────────
        self.input_user = LoginInputField(
            inner, "Usuário",
            placeholder="Seu nome de usuário",
            icon="👤",
        )
        self.input_user.pack(fill="x", pady=(0, 12))

        self.input_pass = LoginInputField(
            inner, "Senha",
            placeholder="Sua senha",
            icon="🔒",
            password=True,
        )
        self.input_pass.pack(fill="x", pady=(0, 4))

        # ── Mensagem de erro global ────────────────────────────────
        self.lbl_erro = ctk.CTkLabel(
            inner, text="",
            text_color=_LOGIN_PALETTE["danger"],
            font=themed_font("body"),
            anchor="center",
        )
        self.lbl_erro.pack(pady=(8, 0))

        # ── Botão principal ────────────────────────────────────────
        self.btn_entrar = PrimaryButton(
            inner,
            text="Entrar",
            command=self._fazer_login,
            height=48,
            corner_radius=RADIUS["lg"],
        )
        self.btn_entrar.pack(fill="x", pady=(14, 8))

        # ── Link privacidade ───────────────────────────────────────
        GhostButton(
            inner,
            text="🔒  Política de Privacidade",
            command=self._abrir_politica,
            height=34,
            corner_radius=RADIUS["button"],
            text_color=_LOGIN_PALETTE["text_muted"],
        ).pack(fill="x")

        # Referências rápidas
        self.entry_user = self.input_user.entry
        self.entry_pass = self.input_pass.entry

        # Enter aciona login
        self.entry_user.bind("<Return>", lambda _: self._fazer_login())
        self.entry_pass.bind("<Return>", lambda _: self._fazer_login())

    # ══════════════════════════════════════
    #  TOGGLE DE MÚSICA (canto inferior direito)
    # ══════════════════════════════════════
    def _criar_music_toggle(self):
        self.music_frame = ctk.CTkFrame(
            self, width=52, height=52,
            corner_radius=RADIUS["avatar"],
            fg_color="white",
            border_width=1,
            border_color=_LOGIN_PALETTE["card_border"],
            bg_color=_LOGIN_PALETTE["grad_top_left"],
        )
        self.music_frame.place(relx=0.97, rely=0.97, anchor="se")

        self.music_var = ctk.StringVar(value="off")
        self._music_btn = ctk.CTkButton(
            self.music_frame,
            text="♪",
            width=44, height=44,
            corner_radius=RADIUS["avatar"],
            font=themed_font("h3"),
            fg_color="transparent",
            hover_color=_LOGIN_PALETTE["accent_soft"],
            text_color=_LOGIN_PALETTE["text_muted"],
            command=self._toggle_music,
        )
        self._music_btn.place(relx=0.5, rely=0.5, anchor="center")

    # ══════════════════════════════════════
    #  LÓGICA DE LOGIN
    # ══════════════════════════════════════
    def fazer_login(self):
        self._fazer_login()

    def _fazer_login(self):
        username = self.input_user.get().strip()
        password = self.input_pass.get().strip()

        # Limpa estados anteriores
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
            self.lbl_erro.configure(text="Preencha todos os campos para continuar.")
            self._shake_card()
            return

        # Feedback visual de carregamento
        self._is_loading = True
        self.lbl_erro.configure(
            text="Autenticando...",
            text_color=_LOGIN_PALETTE["text_muted"],
        )
        self.btn_entrar.configure(text="Aguarde...", state="disabled")
        self.update_idletasks()

        def run_login():
            try:
                result  = self.servico_autenticacao.login(username, password)
                success = result.get("success", False)
                user    = result.get("user", {})
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
        self.lbl_erro.configure(
            text=f"✕  {msg}",
            text_color=_LOGIN_PALETTE["danger"],
        )
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
            f"440x360+{self.winfo_screenwidth()//2-220}+{self.winfo_screenheight()//2-180}"
        ))

        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=32)

        # Ícone
        icon_bg = ctk.CTkFrame(inner, width=52, height=52, corner_radius=RADIUS["avatar"],
                               fg_color=_LOGIN_PALETTE["accent_soft"])
        icon_bg.pack(pady=(0, 14))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="🔒",
                     font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text="Política de Privacidade",
            font=themed_font("h4", "bold"),
            text_color=_LOGIN_PALETTE["text_primary"],
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
            text_color=_LOGIN_PALETTE["text_muted"],
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

    # ══════════════════════════════════════
    #  TOGGLE DE MÚSICA
    # ══════════════════════════════════════
    def _toggle_music(self):
        is_playing = getattr(self, "_music_playing", False)
        if not is_playing:
            path = "assets/Music/background_music.mp3"
            if not os.path.exists(path):
                print(f"Erro: arquivo de música não encontrado em {path}")
                return
            try:
                self._mci_send(f'open "{path}" type mpegvideo alias serpleno_bgm')
                self._mci_send("play serpleno_bgm repeat")
                self._music_playing = True
                self._music_btn.configure(
                    text="♬",
                    text_color=THEME["primary"],
                )
            except Exception as e:
                print(f"Erro ao tocar música: {e}")
        else:
            try:
                self._mci_send("stop serpleno_bgm")
                self._mci_send("close serpleno_bgm")
                self._music_playing = False
                self._music_btn.configure(
                    text="♪",
                    text_color=_LOGIN_PALETTE["text_muted"],
                )
            except Exception:
                pass

    def _mci_send(self, cmd: str) -> None:
        _winmm = ctypes.windll.winmm
        _winmm.mciSendStringA(cmd.encode("utf-8"), None, 0, None)

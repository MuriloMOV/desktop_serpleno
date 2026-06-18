import os
import customtkinter as ctk
import random
import math
import colorsys
from services.autenticacao import ServicoAutenticacao
from services.agendamentos import set_auth_service as set_auth_service_agendamentos
from services.api import set_auth_service as set_auth_service_api
import threading
from pygame import mixer

from ui_theme import THEME, SPACING, RADIUS, ELEVATION, font, themed_font, blend_color, _hex_to_rgb
from components.ui_components import (
    PrimaryButton, SecondaryButton, InputField, EmptyState, Divider, Card, Pill
)


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["brand_accent"])

        self.controller = controller
        self.servico_autenticacao = ServicoAutenticacao()

        self.bolhas = []
        self.background_drawn = False
        self._load_attempted = False

        os.environ['SDL_AUDIODRIVER'] = 'directsound'
        mixer.init()

        self.canvas = ctk.CTkCanvas(self, highlightthickness=0)
        self.canvas.place(relwidth=1, relheight=1)

        self.criar_bolhas()
        self.criar_card_login()
        self.criar_music_toggle()

        self.bind("<Configure>", self.desenhar_gradiente)
        self.animar_bolhas()

    # ================= GRADIENTE SUAVE =================
    def cor_para_canvas(self, hex_c):
        return hex_c

    def desenhar_gradiente(self, event=None):
        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1:
            return

        hex_clrs = [THEME["brand_gradient_start"], THEME["brand_gradient_mid"], THEME["brand_gradient_end"]]
        steps = max(1, height)
        for i in range(steps):
            t = i / steps
            row_h = 1
            color = self._gradient_color(hex_clrs, t)
            self.canvas.create_rectangle(0, i, width, i + row_h, fill=color, outline="", tags="bg_rect")

        self.background_drawn = True

        if hasattr(self, "card"):
            self.card.lift()
        if hasattr(self, "music_frame"):
            self.music_frame.lift()
        for b in self.bolhas:
            self.canvas.tag_raise(b["id"])
            if b.get("text_id"):
                self.canvas.tag_raise(b["text_id"])

    def _gradient_color(self, hex_colors, t):
        segments = len(hex_colors) - 1
        idx = min(int(t * segments), segments - 1)
        local_t = (t * segments) - idx
        c1 = self._hex_to_rgb(hex_colors[idx])
        c2 = self._hex_to_rgb(hex_colors[idx + 1])
        r = int(c1[0] + (c2[0] - c1[0]) * local_t)
        g = int(c1[1] + (c2[1] - c1[1]) * local_t)
        b = int(c1[2] + (c2[2] - c1[2]) * local_t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _hex_to_rgb(self, hex_c):
        hex_c = hex_c.lstrip("#")
        return (int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16))

    # ================= BOLHAS FLUTUANTES =================
    def criar_bolhas(self):
        chars = [''] * 22
        for i in range(35):
            x = random.randint(0, 1400)
            y = random.randint(50, 900)
            size = random.randint(20, 110)
            alpha = random.uniform(0.12, 0.28)
            fill_rgba = self._compute_bubble_fill(alpha)
            bolha_id = self.canvas.create_oval(x, y, x + size, y + size, outline="", fill=fill_rgba, tags="bubble")

            char = chars[i] if i < len(chars) else ""
            text_id = None
            if char:
                text_id = self.canvas.create_text(x + size / 2, y + size / 2, text=char,
                                                  fill=self._compute_text_fill(alpha), font=("Segoe UI", int(size / 3), "bold"))

            self.bolhas.append({
                "id": bolha_id,
                "text_id": text_id,
                "x": x, "y": y, "size": size,
                "speed": random.uniform(0.15, 0.6),
                "wobble": random.uniform(0, 2 * math.pi),
            })

    def _compute_bubble_fill(self, a):
        w = min(255, int(255 * a + 200 * (1 - a)))
        return f"#{w:02x}{w:02x}{w:02x}"

    def _compute_text_fill(self, a):
        w = max(30, int(255 * a))
        return f"#{w:02x}{w:02x}{w:02x}"

    def animar_bolhas(self):
        if not self.winfo_exists():
            self.after(30, self.animar_bolhas)
            return
        width = self.winfo_width()
        height = self.winfo_height()

        if width > 1 and height > 1:
            for b in self.bolhas:
                b["y"] -= b["speed"]
                b["wobble"] += 0.03
                dx = math.sin(b["wobble"]) * 0.4
                b["x"] += dx

                if b["y"] + b["size"] < -10:
                    b["y"] = height + b["size"] + random.randint(10, 60)
                    b["x"] = random.randint(-20, width + 20)

                if b["x"] < -60:
                    b["x"] = width + 20

                self.canvas.coords(b["id"], b["x"], b["y"], b["x"] + b["size"], b["y"] + b["size"])
                if b.get("text_id"):
                    self.canvas.coords(b["text_id"], b["x"] + b["size"] / 2, b["y"] + b["size"] / 2)

        self.after(25, self.animar_bolhas)

    # ================= CARD DE LOGIN =================
    def criar_card_login(self):
        self.card = ctk.CTkFrame(
            self, width=440, height=600, corner_radius=RADIUS["2xl"],
            fg_color=THEME["surface"], border_width=1, border_color=THEME["border"],
            bg_color=THEME["brand_accent"],
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.lift()
        self.card.pack_propagate(False)

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=36, pady=32)

        icon_bg = ctk.CTkFrame(inner, width=76, height=76, corner_radius=38,
                               fg_color=THEME["primary"])
        icon_bg.pack(pady=(8, 16))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="🧠", font=themed_font("h1"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text="SerPleno", font=themed_font("h1", "bold"),
                     text_color=THEME["text"]).pack(pady=(0, 2))
        ctk.CTkLabel(inner, text="Bem-estar e acompanhamento escolar",
                     font=themed_font("body_sm"), text_color=THEME["text_muted"]).pack(pady=(0, 22))

        self.input_user = InputField(inner, "Usuário", placeholder="Seu nome de usuário",
                                     icon="👤", helper="Use seu usuário institucional")
        self.input_user.pack(fill="x", pady=SPACING["input_y"])

        self.input_pass = InputField(inner, "Senha", placeholder="Sua senha", icon="🔒",
                                     password=True)
        self.input_pass.pack(fill="x", pady=SPACING["input_y"])

        self.entry_user = self.input_user.entry
        self.entry_pass = self.input_pass.entry

        self.lbl_erro = ctk.CTkLabel(inner, text="", text_color=THEME["danger"],
                                     font=themed_font("overline"))
        self.lbl_erro.pack(pady=(6, 0))

        self.btn_entrar = PrimaryButton(
            inner, text="Entrar", command=self.fazer_login,
            width=220, height=48, icon="→", size="lg", loading=False
        )
        self.btn_entrar.pack(fill="x", pady=(16, 10))

        self.btn_privacidade = SecondaryButton(
            inner, text="Política de Privacidade", command=self.abrir_politica,
            width=220, icon="🔒"
        )
        self.btn_privacidade.pack(pady=4)

    # ================= TOGGLE DE MÚSICA =================
    def criar_music_toggle(self):
        self.music_frame = ctk.CTkFrame(
            self, width=48, height=48, corner_radius=RADIUS["pill"],
            fg_color=THEME["surface"], border_width=1, border_color=THEME["border"],
            bg_color=THEME["brand_accent"],
        )
        self.music_frame.place(relx=0.98, rely=0.98, anchor="se")

        self.music_var = ctk.StringVar(value="off")
        self.music_switch = ctk.CTkSwitch(
            self.music_frame, text="♫", width=40, height=24,
            command=self.toggle_music, variable=self.music_var,
            onvalue="on", offvalue="off",
            progress_color=THEME["primary"], button_color=THEME["surface"],
            button_hover_color=THEME["bg_alt"], fg_color=THEME["border"],
        )
        self.music_switch.place(relx=0.5, rely=0.5, anchor="center")

    # ================= AÇÕES =================
    def fazer_login(self):
        username = self.input_user.get().strip()
        password = self.input_pass.get().strip()

        if not username or not password:
            self.lbl_erro.configure(text="⚠ Preencha usuário e senha para continuar")
            for field, lbl in ((self.input_user, None), (self.input_pass, self.lbl_erro)):
                if not field.get().strip():
                    field.set_error("Campo obrigatório")
                else:
                    field.set_success()
            return

        self.lbl_erro.configure(text="Autenticando...", text_color=THEME["text_secondary"])
        self.update_idletasks()

        self.input_user.set_success()
        self.input_pass.set_success()

        self.btn_entrar.set_loading(True)

        def run_login():
            try:
                result = self.servico_autenticacao.login(username, password)
                success = result.get('success', False)
                user = result.get('user', {})
                if success:
                    self.after(0, lambda: self._on_login_success(user))
                else:
                    msg = result.get('message', 'Erro ao fazer login')
                    self.after(0, lambda: self._on_login_failure(msg))
            except Exception as e:
                self.after(0, lambda: self._on_login_failure(f"Erro de conexão: {e}"))

        threading.Thread(target=run_login, daemon=True).start()

    def _on_login_success(self, user):
        self.btn_entrar.set_loading(False)
        self.lbl_erro.configure(text="")
        set_auth_service_agendamentos(self.servico_autenticacao)
        set_auth_service_api(self.servico_autenticacao)
        self.controller.iniciar_sistema(user)

    def _on_login_failure(self, msg):
        self.btn_entrar.set_loading(False)
        self.lbl_erro.configure(text=f"✕ {msg}", text_color=THEME["danger"])
        self.input_pass.set_error("Credenciais inválidas")
        self.input_pass.entry.delete(0, "end")

    def abrir_politica(self):
        top = ctk.CTkToplevel(self)
        top.title("Política de Privacidade")
        top.geometry("420x340")
        top.configure(fg_color=THEME["surface"])
        top.resizable(False, False)

        top.transient(self.winfo_toplevel())
        top.grab_set()
        top.after(50, lambda: top.geometry(f"420x340+{self.winfo_screenwidth()//2-210}+{self.winfo_screenheight()//2-170}"))

        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=28)
        ctk.CTkLabel(inner, text="🔒  Política de Privacidade",
                     font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(pady=(0, 14))
        ctk.CTkLabel(inner, text=(
            "O SerPleno trata seus dados com responsabilidade e em conformidade com a LGPD."
            " Esta política garante a proteção de informações pessoais e acadêmicas durante o uso da plataforma."
        ), font=themed_font("body"), text_color=THEME["text_muted"], wraplength=340, justify="left").pack()
        SecondaryButton(inner, text="Entendi", command=top.destroy, width=140, icon="✔").pack(pady=(20, 0))

    def toggle_music(self):
        status = self.music_var.get()
        if status == "on":
            try:
                caminho_musica = "assets/Music/background_music.mp3"
                if os.path.exists(caminho_musica):
                    mixer.music.load(caminho_musica)
                    mixer.music.play(loops=-1, fade_ms=800)
                else:
                    print(f"Erro: Arquivo não encontrado em {caminho_musica}")
                    self.music_var.set("off")
            except Exception as e:
                print(f"Erro ao tocar música: {e}")
                self.music_var.set("off")
        else:
            try:
                mixer.music.fadeout(600)
            except Exception:
                pass

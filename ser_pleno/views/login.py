import os
import customtkinter as ctk
import random
import math
from services.autenticacao import ServicoAutenticacao
from services.agendamentos import set_auth_service as set_auth_service_agendamentos
from services.api import set_auth_service as set_auth_service_api
import threading
from pygame import mixer

from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PrimaryButton,
    SecondaryButton,
    InputField,
    EmptyState,
    Divider,
)


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["brand_accent"])

        self.controller = controller
        self.servico_autenticacao = ServicoAutenticacao()

        self.bolhas = []
        self.background_drawn = False

        os.environ['SDL_AUDIODRIVER'] = 'directsound'
        mixer.init()

        self.canvas = ctk.CTkCanvas(self, highlightthickness=0)
        self.canvas.place(relwidth=1, relheight=1)

        self.criar_bolhas()
        self.criar_card_login()
        self.criar_music_toggle()

        self.bind("<Configure>", self.desenhar_gradiente)
        self.animar_bolhas()

    # ================= FUNDO GRADIENTE =================
    def desenhar_gradiente(self, event=None):
        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1:
            return

        cor_fundo_solida = THEME["brand_accent"]
        self.configure(fg_color=cor_fundo_solida)
        if hasattr(self, 'card'):
            self.card.configure(bg_color=cor_fundo_solida)
        if hasattr(self, 'music_frame'):
            self.music_frame.configure(bg_color=cor_fundo_solida)

        if not self.background_drawn:
            self.canvas.delete("bg_rect")
            self.canvas.create_rectangle(0, 0, width, height, fill=cor_fundo_solida, outline="", tags="bg_rect")
            self.background_drawn = True
        else:
            self.canvas.coords("bg_rect", 0, 0, width, height)

        for b in self.bolhas:
            self.canvas.tag_raise(b["id"])
            if b.get("text_id") is not None:
                self.canvas.tag_raise(b["text_id"])

    # ================= BOLHAS FLUTUANTES =================
    def criar_bolhas(self):
        chars = [''] * 22
        for i in range(25):
            x = random.randint(0, 1200)
            y = random.randint(100, 800)
            size = random.randint(40, 130)

            bolha_id = self.canvas.create_oval(x, y, x + size, y + size, outline="#dfdada", width=1, tags="bubble")

            char = chars[i] if i < len(chars) else ""
            text_id = None
            if char:
                text_id = self.canvas.create_text(x + size / 2, y + size / 2, text=char, fill="white", font=("Segoe UI", int(size / 3), "bold"))

            self.bolhas.append({
                "id": bolha_id,
                "text_id": text_id,
                "x": x,
                "y": y,
                "size": size,
                "speed": random.uniform(0.3, 1.2),
                "wobble": random.uniform(0, 2 * math.pi),
            })

    def animar_bolhas(self):
        width = self.winfo_width()
        height = self.winfo_height()

        if width > 1:
            for b in self.bolhas:
                b["y"] -= b["speed"]
                b["wobble"] += 0.05
                dx = math.sin(b["wobble"]) * 0.5
                b["x"] += dx

                if b["y"] + b["size"] < 0:
                    b["y"] = height + b["size"]
                    b["x"] = random.randint(0, width)

                self.canvas.coords(b["id"], b["x"], b["y"], b["x"] + b["size"], b["y"] + b["size"])
                if b["text_id"]:
                    self.canvas.coords(b["text_id"], b["x"] + b["size"] / 2, b["y"] + b["size"] / 2)

        self.after(25, self.animar_bolhas)

    def criar_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        return None

    def desenhar_elementos_bg(self):
        self.canvas.delete("card_bg")
        self.canvas.delete("toggle_bg")

    # ================= CARD CENTRAL DE LOGIN =================
    def criar_card_login(self):
        self.card = ctk.CTkFrame(
            self,
            width=420,
            height=560,
            corner_radius=RADIUS["xl"],
            fg_color=THEME["card"],
            border_width=1,
            border_color=THEME["border"],
            bg_color=THEME["brand_accent"],
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=32, pady=28)

        # Ícone / marca
        icon_bg = ctk.CTkFrame(inner, width=80, height=80, corner_radius=40, fg_color=THEME["primary"])
        icon_bg.pack(pady=(16, 16))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="🧠", font=themed_font("h1"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        # Título
        ctk.CTkLabel(inner, text="SerPleno", font=themed_font("h1", "bold"), text_color=THEME["text"]).pack(pady=(0, 4))
        ctk.CTkLabel(inner, text="Bem-estar e acompanhamento escolar", font=themed_font("body"), text_color=THEME["text_muted"]).pack(pady=(0, 24))

        # Formulário
        self.input_user = InputField(inner, "Usuário", placeholder="Seu nome de usuário", icon="👤")
        self.input_user.pack(fill="x", pady=SPACING["input_y"])

        self.input_pass = InputField(inner, "Senha", placeholder="Sua senha", icon="🔒", password=True)
        self.input_pass.pack(fill="x", pady=SPACING["input_y"])

        # Guardar referência antiga para compatibilidade
        self.entry_user = self.input_user.entry
        self.entry_pass = self.input_pass.entry

        self.lbl_erro = ctk.CTkLabel(inner, text="", text_color=THEME["danger"], font=themed_font("overline"))
        self.lbl_erro.pack(pady=(4, 0))

        PrimaryButton(inner, text="Entrar", command=self.fazer_login, width=220, height=46).pack(fill="x", pady=(14, 10))
        SecondaryButton(inner, text="Política de Privacidade", command=self.abrir_politica, width=220).pack(pady=4)

    # ================= TOGGLE DE MÚSICA =================
    def criar_music_toggle(self):
        self.music_frame = ctk.CTkFrame(self, fg_color=THEME["card_music"], corner_radius=RADIUS["pill"], border_width=2, border_color=THEME["border_music"], bg_color=THEME["brand_accent"])
        self.music_frame.place(relx=0.98, rely=0.98, anchor="se")

        self.music_var = ctk.StringVar(value="off")
        self.music_switch = ctk.CTkSwitch(
            self.music_frame,
            text="",
            width=50,
            height=26,
            command=self.toggle_music,
            variable=self.music_var,
            onvalue="on",
            offvalue="off",
            progress_color=THEME["primary"],
            button_color=THEME["bg_alt"],
            button_hover_color=THEME["border"],
            fg_color=THEME["info"],
        )
        self.music_switch.pack(padx=12, pady=12)

    # ================= AÇÕES =================
    def fazer_login(self):
        username = self.input_user.get()
        password = self.input_pass.get()

        if username and password:
            self.lbl_erro.configure(text="Autenticando...", text_color=THEME["text_muted"])
            self.update_idletasks()

            def run_login():
                result = self.servico_autenticacao.login(username, password)
                if result['success']:
                    self.lbl_erro.configure(text="")
                    set_auth_service_agendamentos(self.servico_autenticacao)
                    set_auth_service_api(self.servico_autenticacao)
                    self.after(0, lambda: self.controller.iniciar_sistema(result['user']))
                else:
                    msg = result.get('message', 'Erro ao fazer login')
                    self.after(0, lambda: self.lbl_erro.configure(text=msg, text_color=THEME["danger"]))

            threading.Thread(target=run_login, daemon=True).start()
        else:
            self.lbl_erro.configure(text="Preencha usuário e senha")

    def abrir_politica(self):
        top = ctk.CTkToplevel(self)
        top.title("Política de Privacidade")
        top.geometry("420x320")
        top.configure(fg_color=THEME["card"])
        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=24)
        ctk.CTkLabel(inner, text="Política de Privacidade", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(pady=(0, 12))
        ctk.CTkLabel(inner, text="Este texto é uma representação simulada da política de privacidade do SerPleno.", font=themed_font("body"), text_color=THEME["text_muted"], wraplength=340, justify="left").pack()

    # Lógica de tocar música
    def toggle_music(self):
        status = self.music_var.get()

        if status == "on":
            try:
                caminho_musica = "assets/Music/background_music.mp3"

                if os.path.exists(caminho_musica):
                    print("Music Playing...")
                    mixer.music.load(caminho_musica)
                    mixer.music.play(loops=-1)
                else:
                    print(f"Erro: Arquivo não encontrado em {caminho_musica}")
                    self.music_var.set("off")
            except Exception as e:
                print(f"Erro ao tocar música: {e}")
        else:
            print("Music Stopped...")
            mixer.music.stop()

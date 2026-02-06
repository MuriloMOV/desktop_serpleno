import os
import customtkinter as ctk
import random
import math
from services.autenticacao import ServicoAutenticacao
# Compat alias para testes que esperam o nome em inglês
AuthService = ServicoAutenticacao
import threading
from pygame import mixer

from ui_theme import THEME, RADIUS, font


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["brand_accent"])

        self.controller = controller
        # Use the compatível AuthService alias aqui para facilitar testes (e permitir mock)
        self.servico_autenticacao = AuthService()

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
            # Preenche o canvas com a cor sólida UMA VEZ
            # Mas na verdade nem precisa do retângulo se o self.bg já for azul e canvas transparente.
            # Como segurança, desenhamos um retângulo que cobre tudo
            self.canvas.delete("bg_rect")
            self.canvas.create_rectangle(0, 0, width, height, fill=cor_fundo_solida, outline="", tags="bg_rect")
            self.background_drawn = True
        else:
            # Se redimensionar, atualiza o retângulo
            self.canvas.coords("bg_rect", 0, 0, width, height)
        
        # Trazer bolhas para frente do gradiente
        for b in self.bolhas:
            self.canvas.tag_raise(b["id"])
            if b.get("text_id") is not None:
                self.canvas.tag_raise(b["text_id"])
        

    # ================= BOLHAS FLUTUANTES (BUBBLES) =================
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
                # Movimento para cima
                b["y"] -= b["speed"]
                
                # Movimento lateral (senoidal)
                b["wobble"] += 0.05
                dx = math.sin(b["wobble"]) * 0.5
                b["x"] += dx
                
                # Reset se sair da tela (topo)
                if b["y"] + b["size"] < 0:
                    b["y"] = height + b["size"]
                    b["x"] = random.randint(0, width)
                
                # Atualizar coords
                self.canvas.coords(b["id"], b["x"], b["y"], b["x"] + b["size"], b["y"] + b["size"])
                if b["text_id"]:
                    self.canvas.coords(b["text_id"], b["x"] + b["size"]/2, b["y"] + b["size"]/2)

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
            height=520,
            corner_radius=24,
            fg_color=THEME["card"],
            border_width=1,
            border_color=THEME["border"],
            bg_color=THEME["brand_accent"],
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        inner = ctk.CTkFrame(self.card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=22)

        # 1. Ícone Coração (Gradient Circle)
        # Simulando o gradiente com uma cor sólida azul vibrante por limitação do CTK
        icon_bg = ctk.CTkFrame(inner, width=80, height=80, corner_radius=40, fg_color=THEME["primary"])
        icon_bg.pack(pady=(40, 15))
        icon_bg.pack_propagate(False)
        
        # Coração (Usando emoji ou texto, já que não temos o SVG 'heart' do lucide facilmente renderizável aqui)
        heart_label = ctk.CTkLabel(icon_bg, text="🤍", font=font(40), text_color="white")
        heart_label.place(relx=0.5, rely=0.5, anchor="center")

        # 2. Título "Ser Pleno"
        title_label = ctk.CTkLabel(
            inner,
            text="Ser Pleno",
            font=font(28, "bold"),
            text_color=THEME["text"]
        )
        title_label.pack(pady=(0, 5))

        # 3. Subtítulo
        subtitle_label = ctk.CTkLabel(inner, text="Sua jornada de bem-estar começa aqui", font=font(12), text_color=THEME["text_muted"])
        subtitle_label.pack(pady=(0, 25))

        # 4. Formulário
        # Usuario
        self.user_frame = ctk.CTkFrame(inner, fg_color=THEME["bg_alt"], corner_radius=RADIUS["input"], border_width=1, border_color=THEME["border"], height=40)
        self.user_frame.pack(fill="x", pady=8)
        self.user_frame.pack_propagate(False)

        ctk.CTkLabel(self.user_frame, text="👤", font=font(14), text_color=THEME["text_muted"]).pack(side="left", padx=12)

        self.entry_user = ctk.CTkEntry(
            self.user_frame,
            placeholder_text="Seu nome",
            height=34,
            border_width=0,
            fg_color="transparent",
            text_color=THEME["text"],
            justify="center",
            font=font(13)
        )
        self.entry_user.pack(side="left", fill="both", expand=True, padx=(0, 12))
        
        
        # Senha
        self.pass_frame = ctk.CTkFrame(inner, fg_color=THEME["bg_alt"], corner_radius=RADIUS["input"], border_width=1, border_color=THEME["border"], height=40)
        self.pass_frame.pack(fill="x", pady=8)
        self.pass_frame.pack_propagate(False)

        ctk.CTkLabel(self.pass_frame, text="🔒", font=font(14), text_color=THEME["text_muted"]).pack(side="left", padx=12)

        self.entry_pass = ctk.CTkEntry(
            self.pass_frame,
            placeholder_text="Sua senha",
            show="•",
            height=34,
            border_width=0,
            fg_color="transparent",
            text_color=THEME["text"],
            justify="center",
            font=font(13)
        )
        self.entry_pass.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Mensagem de erro
        self.lbl_erro = ctk.CTkLabel(inner, text="", text_color="#ef4444", font=font(11))
        self.lbl_erro.pack(pady=2)

        # Botão Entrar
        self.btn_entrar = ctk.CTkButton(inner, text="Entrar", height=46, corner_radius=RADIUS["button"], fg_color=THEME["primary"], hover_color=THEME["primary_hover"], font=font(14, "bold"), command=self.fazer_login)
        self.btn_entrar.pack(fill="x", pady=(12, 10))

        # Link Política
        self.btn_politica = ctk.CTkButton(inner, text="🛡️ Política de Privacidade", fg_color="transparent", text_color=THEME["primary"], hover_color=THEME["primary_light"], font=font(12), height=30, command=self.abrir_politica)
        self.btn_politica.pack(pady=10)

    # ================= TOGGLE DE MÚSICA =================
    def criar_music_toggle(self):
        # Container menor no canto inferior direito
        self.music_frame = ctk.CTkFrame(self, fg_color=THEME["card_music"], corner_radius=20, border_width=2, border_color=THEME["border_music"], bg_color=THEME["brand_accent"])
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
            fg_color=THEME["info"]
        )
        self.music_switch.pack(padx=12, pady=12)

    # ================= AÇÕES =================
    def fazer_login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
        if username and password:
            self.lbl_erro.configure(text="Autenticando...", text_color="white")
            self.update_idletasks()
            
            # Simple threading to prevent UI freeze
            def run_login():
                result = self.servico_autenticacao.login(username, password)
                if result['success']:
                    self.lbl_erro.configure(text="")
                    # Must schedule UI update on main thread
                    self.after(0, self.controller.iniciar_sistema)
                else:
                    msg = result.get('message', 'Erro ao fazer login')
                    self.after(0, lambda: self.lbl_erro.configure(text=msg, text_color="red"))

            threading.Thread(target=run_login, daemon=True).start()
        else:
            self.lbl_erro.configure(text="Preencha usuário e senha")

    def abrir_politica(self):
        top = ctk.CTkToplevel(self)
        top.title("Política de Privacidade")
        top.geometry("400x300")
        lb = ctk.CTkLabel(top, text="Política de Privacidade\n\n(Texto Simulado)", font=font(14))
        lb.pack(expand=True)

    # Lógica de tocar música 
    def toggle_music(self):
        status = self.music_var.get()
        
        if status == "on":
            try:
                # 1. Verifica se o arquivo existe para não crashar o app
                caminho_musica = "assets/Music/background_music.mp3"
                
                if os.path.exists(caminho_musica):
                    print("Music Playing...")
                    mixer.music.load(caminho_musica)
                    # 2. O parâmetro loops=-1 faz a música repetir infinitamente
                    mixer.music.play(loops=-1) 
                else:
                    print(f"Erro: Arquivo não encontrado em {caminho_musica}")
                    self.music_var.set("off") # Volta o switch para desligado
            except Exception as e:
                print(f"Erro ao tocar música: {e}")
        else:
            print("Music Stopped...")
            mixer.music.stop()
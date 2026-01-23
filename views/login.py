import customtkinter as ctk
import random
import math

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="black")  # Base color until gradient draws

        self.controller = controller

        # Cores do tema baseadas no CSS da web (theme-dark-blue)
        # Senac Blue Dark: #003366 -> Senac Blue Light: #4F7CAC
        # Vamos criar um gradiente vibrante de azul
        self.gradient_colors = ["#003366", "#004A8D", "#4F7CAC", "#8ec5fc"]
        
        self.bolhas = []
        self.background_drawn = False
        
        # Canvas ocupa toda a tela
        self.canvas = ctk.CTkCanvas(self, highlightthickness=0)
        self.canvas.place(relwidth=1, relheight=1)
        
        # Inicializa UI
        self.criar_bolhas()
        self.criar_card_login()
        self.criar_music_toggle()
        
        # Eventos
        self.bind("<Configure>", self.desenhar_gradiente)
        self.animar_bolhas()

    # ================= FUNDO GRADIENTE =================
    def desenhar_gradiente(self, event=None):
        if self.background_drawn: 
            return
            
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1: 
            return

        # Desenhar gradiente vertical
        # Interpolando entre as cores definidas
        limit = height
        # Simplificação para performance: faixas de 2 pixels
        step = 2
        
        # Cor inicial e final principal
        c1 = (0, 51, 102)   # #003366
        c2 = (79, 124, 172) # #4F7CAC
        
        for y in range(0, limit, step):
            ratio = y / limit
            r = int(c1[0] + (c2[0] - c1[0]) * ratio)
            g = int(c1[1] + (c2[1] - c1[1]) * ratio)
            b = int(c1[2] + (c2[2] - c1[2]) * ratio)
            color = f"#{r:02x}{g:02x}{b:02x}"
            self.canvas.create_line(0, y, width, y, fill=color, width=step)
            
        self.background_drawn = True
        
        # Trazer bolhas para frente do gradiente (se já existirem)
        for b in self.bolhas:
            self.canvas.tag_raise(b["id"])
            if "text_id" in b:
                self.canvas.tag_raise(b["text_id"])

    # ================= BOLHAS FLUTUANTES (BUBBLES) =================
    def criar_bolhas(self):
        # Baseado nas bolhas do CSS (x1 a x25)
        # Algumas com texto, outras vazias (ou com caracteres abstratos do HTML original)
        chars = ['a', 'b', 'c'] + [''] * 22
        
        for i in range(25):
            x = random.randint(0, 1200)
            y = random.randint(100, 800)
            size = random.randint(40, 130) # Tamanhos variados como no CSS (60px a 130px)
            
            # Efeito de bolha de sabão: contorno branco semitransparente, fill muito leve
            bolha_id = self.canvas.create_oval(
                x, y, x + size, y + size,
                outline="#ffffff",
                width=1,
                tags="bubble"
            )
            # CustomTkinter Canvas não suporta alpha no fill diretamente de forma simples,
            # mas podemos simular com stipple se necessário, ou apenas deixar outline para "glass"
            # O Canvas padrão do Tkinter suporta transparência apenas via imagens ou hacks.
            # Vamos manter apenas o outline e desenhar o texto.

            char = chars[i] if i < len(chars) else ""
            text_id = None
            if char:
                text_id = self.canvas.create_text(
                    x + size/2, y + size/2,
                    text=char,
                    fill="white",
                    font=("Segoe UI", int(size/3), "bold")
                )
            
            self.bolhas.append({
                "id": bolha_id,
                "text_id": text_id,
                "x": x,
                "y": y,
                "size": size,
                "speed": random.uniform(0.5, 2.0), # Velocidade de subida
                "wobble": random.uniform(0, 2 * math.pi) # Para movimento lateral
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

        self.after(20, self.animar_bolhas)

    # ================= CARD CENTRAL DE LOGIN =================
    def criar_card_login(self):
        # Card branco central
        self.card = ctk.CTkFrame(
            self,
            width=380,
            height=500,
            corner_radius=20,
            fg_color="white",
            bg_color="transparent" # Importante para cantos arredondados sobre o canvas
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        # 1. Ícone Coração (Gradient Circle)
        # Simulando o gradiente com uma cor sólida azul vibrante por limitação do CTK
        icon_bg = ctk.CTkFrame(
            self.card,
            width=80,
            height=80,
            corner_radius=40,
            fg_color="#3b82f6" # blue-500
        )
        icon_bg.pack(pady=(40, 15))
        icon_bg.pack_propagate(False)
        
        # Coração (Usando emoji ou texto, já que não temos o SVG 'heart' do lucide facilmente renderizável aqui)
        heart_label = ctk.CTkLabel(
            icon_bg,
            text="🤍", # Coração branco
            font=("Arial", 40),
            text_color="white"
        )
        heart_label.place(relx=0.5, rely=0.5, anchor="center")

        # 2. Título "Ser Pleno"
        title_label = ctk.CTkLabel(
            self.card,
            text="Ser Pleno",
            font=("Segoe UI", 28, "bold"),
            text_color="#1e40af" # blue-800
        )
        title_label.pack(pady=(0, 5))

        # 3. Subtítulo
        subtitle_label = ctk.CTkLabel(
            self.card,
            text="Sua jornada de bem-estar começa aqui",
            font=("Segoe UI", 12),
            text_color="#64748b" # gray-500
        )
        subtitle_label.pack(pady=(0, 25))

        # 4. Formulário
        # Usuario
        self.user_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.user_frame.pack(fill="x", padx=40, pady=8)
        
        self.entry_user = ctk.CTkEntry(
            self.user_frame,
            placeholder_text="Seu nome",
            height=45,
            corner_radius=12,
            border_width=1,
            border_color="#e2e8f0",
            fg_color="#f8fafc",
            text_color="#334155"
        )
        self.entry_user.pack(fill="x")
        # Nota: Ícones dentro do entry são complexos em CTK puro. 
        # Poderíamos colocar um Label com imagem sobre o entry, mas pode quebrar layout.
        
        # Senha
        self.pass_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        self.pass_frame.pack(fill="x", padx=40, pady=8)

        self.entry_pass = ctk.CTkEntry(
            self.pass_frame,
            placeholder_text="Sua senha",
            show="•",
            height=45,
            corner_radius=12,
            border_width=1,
            border_color="#e2e8f0",
            fg_color="#f8fafc",
            text_color="#334155"
        )
        self.entry_pass.pack(fill="x")

        # Mensagem de erro
        self.lbl_erro = ctk.CTkLabel(
            self.card,
            text="",
            text_color="#ef4444",
            font=("Segoe UI", 11)
        )
        self.lbl_erro.pack(pady=2)

        # Botão Entrar
        self.btn_entrar = ctk.CTkButton(
            self.card,
            text="Entrar",
            height=45,
            corner_radius=12,
            fg_color="#2563eb", # blue-600
            hover_color="#1d4ed8", # blue-700
            font=("Segoe UI", 14, "bold"),
            command=self.fazer_login
        )
        self.btn_entrar.pack(fill="x", padx=40, pady=(10, 15))

        # Link Política
        self.btn_politica = ctk.CTkButton(
            self.card,
            text="🛡️ Política de Privacidade",
            fg_color="transparent",
            text_color="#3b82f6",
            hover_color="#eff6ff",
            font=("Segoe UI", 12),
            height=30,
            command=self.abrir_politica
        )
        self.btn_politica.pack(pady=10)

    # ================= TOGGLE DE MÚSICA =================
    def criar_music_toggle(self):
        # Container no canto inferior direito
        self.music_frame = ctk.CTkFrame(
            self, 
            fg_color="transparent",
            bg_color="transparent" # Sobre o canvas
        )
        self.music_frame.place(relx=0.98, rely=0.98, anchor="se")

        # Vamos usar um Switch para simular o toggle
        self.music_var = ctk.StringVar(value="off")
        
        self.music_switch = ctk.CTkSwitch(
            self.music_frame,
            text="Música",
            command=self.toggle_music,
            variable=self.music_var,
            onvalue="on",
            offvalue="off",
            progress_color="#4ade80", # green-400 (cor do check no css visual)
            button_color="white",
            button_hover_color="#f1f5f9",
            text_color="white" # Texto sobre o fundo azul escuro
        )
        self.music_switch.pack(padx=20, pady=20)

    # ================= AÇÕES =================
    def fazer_login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
        if username and password:
            # Login bem sucedido
            self.controller.iniciar_sistema()
        else:
            self.lbl_erro.configure(text="Preencha usuário e senha")

    def abrir_politica(self):
        # Aqui seria aberta a modal. Como é desktop, podemos abrir uma nova janela ou Toplevel
        top = ctk.CTkToplevel(self)
        top.title("Política de Privacidade")
        top.geometry("400x300")
        lb = ctk.CTkLabel(top, text="Política de Privacidade\n\n(Texto Simulado)", font=("Segoe UI", 14))
        lb.pack(expand=True)

    def toggle_music(self):
        # Lógica de tocar música (Placeholder)
        status = self.music_var.get()
        if status == "on":
            print("Music Playing...")
            # Implementação real necessitaria de pygame ou similar
        else:
            print("Music Paused...")


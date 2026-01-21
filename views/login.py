import customtkinter as ctk
import random


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="white")

        self.controller = controller

        # Cores do tema (Sintonizadas com a imagem de referência)
        self.cor_primaria = "#4f75ff"   # Azul vibrante (botão e destaque)
        self.cor_texto_sec = "#64748b"  # Cinza médio para subtítulos
        
        self.background_drawn = False
        self.criar_fundo_gradiente()
        self.criar_bolhas_com_texto()
        self.criar_card_login()
        self.animar_bolhas()

    # ================= FUNDO GRADIENTE =================
    def criar_fundo_gradiente(self):
        # Canvas para desenhar o gradiente e as bolhas flutuantes
        self.canvas = ctk.CTkCanvas(
            self,
            bg="white",
            highlightthickness=0
        )
        self.canvas.place(relwidth=1, relheight=1)

        # Redesenha o gradiente quando a janela é redimensionada
        self.bind("<Configure>", self.desenhar_gradiente)

    def desenhar_gradiente(self, event=None):
        if self.background_drawn:
            return
            
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1: # Prevenção para quando a janela inicia minimizada
            return

        # Gradiente linear: Azul suave -> Lilás -> Rosa pálido
        for i in range(width):
            r = int(191 + (233 - 191) * (i / width))
            g = int(219 + (213 - 219) * (i / width))
            b = int(254 + (255 - 254) * (i / width))
            cor = f"#{r:02x}{g:02x}{b:02x}"
            self.canvas.create_line(i, 0, i, height, fill=cor)
        
        self.background_drawn = True

    # ================= BOLHAS FLUTUANTES COM TEXTO =================
    def criar_bolhas_com_texto(self):
        palavras = [
            "Sucesso", "Equilíbrio", "Propósito", "Conhecimento", 
            "Saúde Mental", "Comunidade", "Liderança", "Tecnologia", 
            "Ser", "Foco", "Aprendizado", "Pleno"
        ]
        
        self.bolhas = []

        for palavra in palavras:
            x = random.randint(50, 1200)
            y = random.randint(50, 700)
            r = random.randint(40, 65)

            bolha_id = self.canvas.create_oval(
                x - r, y - r,
                x + r, y + r,
                fill="#ffffff",
                outline="#cbd5e1",
                width=1
            )
            
            texto_id = self.canvas.create_text(
                x, y,
                text=palavra,
                font=("Segoe UI", 10, "bold"),
                fill="#475569",
                angle=random.randint(-20, 20)
            )

            self.bolhas.append({
                "id": bolha_id,
                "texto_id": texto_id,
                "dx": random.uniform(-0.4, 0.4),
                "dy": random.uniform(-0.6, -0.2),
                "r": r
            })

    def animar_bolhas(self):
        if not self.winfo_exists():
            return

        width = self.winfo_width()
        height = self.winfo_height()
        
        for b in self.bolhas:
            self.canvas.move(b["id"], b["dx"], b["dy"])
            self.canvas.move(b["texto_id"], b["dx"], b["dy"])
            
            pos = self.canvas.coords(b["id"])
            if not pos or len(pos) < 4: 
                continue
            
            if pos[3] < 0: # Canto inferior da bolha saiu do topo
                off_x = random.randint(-100, 100)
                self.canvas.move(b["id"], off_x, height + b["r"]*2)
                self.canvas.move(b["texto_id"], off_x, height + b["r"]*2)

        self.after(30, self.animar_bolhas)

    # ================= CARD DE LOGIN (GLASS-STYLE) =================
    def criar_card_login(self):
        # Container central (Card) com bg_color transparente para evitar o "vazado" nos cantos
        self.card = ctk.CTkFrame(
            self,
            width=380,
            height=530,
            corner_radius=30,
            fg_color="#f8fafc",            # Branco levemente azulado para efeito "glass"
            bg_color="transparent",        # ESSENCIAL: remove o fundo quadrado nos cantos arredondados
            border_width=2,
            border_color="white"           # Borda branca sólida ajuda no efeito de reflexo do vidro
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        # Ícone de Coração Blue-Circle
        icon_circle = ctk.CTkFrame(
            self.card, 
            width=64, 
            height=64, 
            corner_radius=32, 
            fg_color=self.cor_primaria
        )
        icon_circle.pack(pady=(40, 10))
        icon_circle.pack_propagate(False)

        ctk.CTkLabel(
            icon_circle, 
            text="💙", 
            font=("Arial", 28), 
            text_color="white"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Cabeçalho do App
        ctk.CTkLabel(
            self.card,
            text="Ser Pleno",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=self.cor_primaria
        ).pack()

        ctk.CTkLabel(
            self.card,
            text="Sua jornada de bem-estar começa aqui",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.cor_texto_sec
        ).pack(pady=(2, 35))

        # Inputs Customizados
        self.email = ctk.CTkEntry(
            self.card,
            placeholder_text="Seu nome",
            height=50,
            fg_color="#f1f5f9",
            border_width=0,
            corner_radius=12,
            placeholder_text_color="#94a3b8",
            text_color="#1e293b"
        )
        self.email.pack(fill="x", padx=45, pady=8)

        self.senha = ctk.CTkEntry(
            self.card,
            placeholder_text="Sua senha",
            show="•",
            height=50,
            fg_color="#f1f5f9",
            border_width=0,
            corner_radius=12,
            placeholder_text_color="#94a3b8",
            text_color="#1e293b"
        )
        self.senha.pack(fill="x", padx=45, pady=8)

        self.erro = ctk.CTkLabel(
            self.card,
            text="",
            text_color="#ef4444",
            font=ctk.CTkFont(size=12)
        )
        self.erro.pack(pady=2)

        # Botão Principal
        ctk.CTkButton(
            self.card,
            text="Entrar",
            height=50,
            fg_color=self.cor_primaria,
            hover_color="#3b60e6",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            corner_radius=12,
            command=self.login
        ).pack(fill="x", padx=45, pady=(15, 20))

        # Política de Privacidade (Maior e com Hover dinâmico)
        self.link_politica = ctk.CTkLabel(
            self.card,
            text="🛡️ Política de Privacidade",
            text_color=self.cor_primaria,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            cursor="hand2"
        )
        self.link_politica.pack(pady=5)
        
        # Eventos de Hover para o link
        self.link_politica.bind("<Enter>", lambda e: self.link_politica.configure(font=ctk.CTkFont(family="Segoe UI", size=13, underline=True)))
        self.link_politica.bind("<Leave>", lambda e: self.link_politica.configure(font=ctk.CTkFont(family="Segoe UI", size=13, underline=False)))

        # Botão Musical (Toggle) - Ajustado bg_color para evitar vazamento
        self.btn_music = ctk.CTkButton(
            self,
            text="🎵",
            width=42,
            height=42,
            corner_radius=21,
            fg_color="white",
            bg_color="transparent", 
            text_color=self.cor_primaria,
            border_width=1,
            border_color="#e2e8f0",
            hover_color="#f8fafc"
        )
        self.btn_music.place(relx=0.97, rely=0.96, anchor="center")

    # ================= FUNCIONALIDADE =================
    def login(self):
        if self.email.get() and self.senha.get():
            self.controller.iniciar_sistema()
        else:
            self.erro.configure(text="Por favor, preencha os campos de acesso.")

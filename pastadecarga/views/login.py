import customtkinter as ctk
import random


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="white")

        self.controller = controller

        self.criar_fundo()
        self.criar_card_login()
        self.animar_bolhas()

    # ================= FUNDO COM BOLHAS =================
    def criar_fundo(self):
        self.canvas = ctk.CTkCanvas(
            self,
            bg="white",
            highlightthickness=0
        )
        self.canvas.place(relwidth=1, relheight=1)

        self.bolhas = []

        for _ in range(14):
            x = random.randint(0, 1200)
            y = random.randint(0, 720)
            r = random.randint(20, 50)

            bolha = self.canvas.create_oval(
                x - r, y - r,
                x + r, y + r,
                fill="#e0f2fe",
                outline=""
            )

            self.bolhas.append({
                "id": bolha,
                "dx": random.uniform(-0.2, 0.2),
                "dy": random.uniform(-0.4, -0.1)
            })

    def animar_bolhas(self):
        for bolha in self.bolhas:
            self.canvas.move(bolha["id"], bolha["dx"], bolha["dy"])

        self.after(40, self.animar_bolhas)

    # ================= CARD LOGIN =================
    def criar_card_login(self):
        self.card = ctk.CTkFrame(
            self,
            width=380,
            height=420,
            corner_radius=20,
            fg_color="white",
            border_width=1,
            border_color="#e5e7eb"
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        ctk.CTkLabel(
            self.card,
            text="Bem-vinda",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#111827"
        ).pack(pady=(40, 5))

        ctk.CTkLabel(
            self.card,
            text="Acesse sua conta",
            text_color="#6b7280"
        ).pack(pady=(0, 30))

        self.email = ctk.CTkEntry(
            self.card,
            placeholder_text="E-mail"
        )
        self.email.pack(fill="x", padx=40, pady=10)

        self.senha = ctk.CTkEntry(
            self.card,
            placeholder_text="Senha",
            show="•"
        )
        self.senha.pack(fill="x", padx=40, pady=10)

        self.erro = ctk.CTkLabel(
            self.card,
            text="",
            text_color="red"
        )
        self.erro.pack()

        ctk.CTkButton(
            self.card,
            text="Entrar",
            height=42,
            command=self.login
        ).pack(fill="x", padx=40, pady=30)

    # ================= LOGIN =================
    def login(self):
        if self.email.get() and self.senha.get():
            self.controller.iniciar_sistema()
        else:
            self.erro.configure(text="Preencha todos os campos")
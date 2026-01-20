import customtkinter as ctk


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller

        # ================= TÍTULO =================
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 15))

        ctk.CTkLabel(
            header,
            text="Dashboard Central",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#111827"
        ).pack(side="left")

        # ================= CARDS TOPO =================
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=30)

        self.card(cards, "Atendimentos do Dia", "0", "👥")
        self.card(cards, "Vagas Disponíveis", "0", "📅")
        self.card(cards, "Alertas Ativos", "0", "🔔")
        self.card(cards, "Total de Estudantes", "6", "👨‍🎓")
        self.card(cards, "Humor Médio (Hoje)", "😊", "🙂")

        # ================= CONTEÚDO PRINCIPAL =================
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=30, pady=25)

        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(1, weight=1)

        # ---------- Próximos Atendimentos ----------
        agenda = ctk.CTkFrame(body, fg_color="white", corner_radius=12)
        agenda.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=(0, 15))

        self.titulo_card(
            agenda,
            "Próximos Atendimentos",
            "Ver agenda completa →"
        )

        ctk.CTkLabel(
            agenda,
            text="📅",
            font=ctk.CTkFont(size=40),
            text_color="#9ca3af"
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            agenda,
            text="Nenhum agendamento para hoje",
            text_color="#6b7280"
        ).pack()

        ctk.CTkButton(
            agenda,
            text="+ Criar agendamento",
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            corner_radius=8
        ).pack(pady=20)

        # ---------- Estudantes em Alerta ----------
        alertas = ctk.CTkFrame(body, fg_color="white", corner_radius=12)
        alertas.grid(row=0, column=1, sticky="nsew", pady=(0, 15))

        self.titulo_card(alertas, "Estudantes em Alerta", "2")

        self.alerta(
            alertas,
            "Bruno Henrique Souza",
            "Histórico de ansiedade - acompanhamento regular",
            "Desenvolvimento de Software Multiplataforma"
        )

        self.alerta(
            alertas,
            "Diego Martins Almeida",
            "TDAH diagnosticado - adaptações necessárias",
            "Gestão Empresarial"
        )

        # ---------- Gráfico (Mock) ----------
        grafico = ctk.CTkFrame(body, fg_color="white", corner_radius=12)
        grafico.grid(row=1, column=0, sticky="nsew", padx=(0, 15))

        self.titulo_card(grafico, "Humor dos Estudantes (30 dias)")

        ctk.CTkLabel(
            grafico,
            text="(Área de gráfico)",
            text_color="#9ca3af"
        ).pack(expand=True)

        # ---------- Bem-estar ----------
        bem_estar = ctk.CTkFrame(body, fg_color="white", corner_radius=12)
        bem_estar.grid(row=1, column=1, sticky="nsew")

        self.titulo_card(bem_estar, "Bem-Estar por Dimensão")

        for item in ["Acadêmico", "Emocional", "Social"]:
            linha = ctk.CTkFrame(bem_estar, fg_color="transparent")
            linha.pack(fill="x", padx=20, pady=10)

            ctk.CTkLabel(linha, text=item).pack(side="left")
            ctk.CTkLabel(linha, text="--", text_color="#6b7280").pack(side="right")

        ctk.CTkLabel(
            bem_estar,
            text="Baseado em autoavaliações dos últimos 7 dias",
            text_color="#9ca3af",
            font=ctk.CTkFont(size=11)
        ).pack(pady=15)

    # ================= COMPONENTES =================
    def card(self, parent, titulo, valor, icone):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        frame.pack(side="left", expand=True, fill="both", padx=8)

        ctk.CTkLabel(
            frame,
            text=titulo,
            text_color="#6b7280"
        ).pack(anchor="w", padx=15, pady=(12, 2))

        linha = ctk.CTkFrame(frame, fg_color="transparent")
        linha.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            linha,
            text=valor,
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            linha,
            text=icone,
            font=ctk.CTkFont(size=22)
        ).pack(side="right")

    def titulo_card(self, parent, titulo, extra=None):
        topo = ctk.CTkFrame(parent, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            topo,
            text=titulo,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left")

        if extra:
            ctk.CTkLabel(
                topo,
                text=extra,
                text_color="#6d28d9"
            ).pack(side="right")

    def alerta(self, parent, nome, motivo, curso):
        box = ctk.CTkFrame(parent, fg_color="#fee2e2", corner_radius=10)
        box.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            box,
            text=nome,
            font=ctk.CTkFont(weight="bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            box,
            text="⚠ " + motivo,
            text_color="#dc2626",
            wraplength=220,
            justify="left"
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            box,
            text=curso,
            text_color="#6b7280",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10, pady=(2, 8))

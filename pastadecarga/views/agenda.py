import customtkinter as ctk


class AgendaFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#f4f6fb")
        self.app = app

        self.horarios = ["18:00"]

        self.criar_layout()
        self.renderizar_horarios()

    # ================= LAYOUT =================
    def criar_layout(self):
        self.criar_header()
        self.criar_agenda_dia()
        self.criar_proxima_semana()

    # ================= HEADER =================
    def criar_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))

        ctk.CTkLabel(
            header,
            text="Agenda",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#111827"
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Gerir Horários",
            fg_color="#e5e7eb",
            text_color="#111827",
            hover_color="#6d28d9",
            width=140,
            command=self.abrir_modal_horarios
        ).pack(side="left", padx=20)

        ctk.CTkLabel(
            header,
            text="quinta-feira, 15 de janeiro de 2026",
            font=ctk.CTkFont(size=13),
            text_color="#374151"
        ).pack(side="right")

    # ================= AGENDA DO DIA =================
    def criar_agenda_dia(self):
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        container.pack(fill="x", padx=30, pady=(0, 20))

        ctk.CTkLabel(
            container,
            text="Agenda do Dia",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.lista_dia = ctk.CTkFrame(container, fg_color="transparent")
        self.lista_dia.pack(anchor="w", padx=20, pady=(0, 20))

    # ================= PRÓXIMA SEMANA =================
    def criar_proxima_semana(self):
        container = ctk.CTkFrame(self, fg_color="white", corner_radius=12)
        container.pack(fill="x", padx=30)

        ctk.CTkLabel(
            container,
            text="Próxima Semana",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.lista_semana = ctk.CTkFrame(container, fg_color="transparent")
        self.lista_semana.pack(anchor="w", padx=20, pady=(0, 20))

    # ================= HORÁRIOS =================
    def renderizar_horarios(self):
        for frame in (self.lista_dia, self.lista_semana):
            for widget in frame.winfo_children():
                widget.destroy()

            for horario in self.horarios:
                card = ctk.CTkFrame(
                    frame,
                    fg_color="#d1fae5",
                    corner_radius=10,
                    width=140,
                    height=60
                )
                card.pack(side="left", padx=10)
                card.pack_propagate(False)

                ctk.CTkLabel(
                    card,
                    text=horario,
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color="#065f46"
                ).pack(pady=(8, 0))

                ctk.CTkLabel(
                    card,
                    text="Disponível",
                    font=ctk.CTkFont(size=12),
                    text_color="#047857"
                ).pack()

    # ================= MODAL =================
    def abrir_modal_horarios(self):
        self.modal_bg = ctk.CTkFrame(self, fg_color="#1f2937")
        self.modal_bg.place(relwidth=1, relheight=1)

        modal = ctk.CTkFrame(
            self.modal_bg,
            fg_color="white",
            corner_radius=14,
            width=420,
            height=300
        )
        modal.place(relx=0.5, rely=0.5, anchor="center")
        modal.pack_propagate(False)

        ctk.CTkLabel(
            modal,
            text="Gerir Horários de Atendimento",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 15))

        for h in self.horarios:
            linha = ctk.CTkFrame(modal, fg_color="#f3f4f6", corner_radius=8)
            linha.pack(fill="x", padx=30, pady=5)

            ctk.CTkLabel(linha, text=h).pack(side="left", padx=12)

            ctk.CTkButton(
                linha,
                text="Remover",
                fg_color="transparent",
                text_color="#dc2626",
                width=80,
                command=lambda x=h: self.remover_horario(x)
            ).pack(side="right", padx=10)

        self.input_horario = ctk.CTkEntry(modal, placeholder_text="Ex: 18:00")
        self.input_horario.pack(pady=15)

        ctk.CTkButton(
            modal,
            text="Adicionar",
            fg_color="#6d28d9",
            command=self.adicionar_horario
        ).pack()

        ctk.CTkButton(
            modal,
            text="Fechar",
            fg_color="#111827",
            command=self.fechar_modal
        ).pack(pady=15)

    # ================= AÇÕES =================
    def fechar_modal(self):
        self.modal_bg.destroy()
        self.renderizar_horarios()

    def adicionar_horario(self):
        valor = self.input_horario.get()
        if valor and valor not in self.horarios:
            self.horarios.append(valor)
        self.fechar_modal()

    def remover_horario(self, horario):
        if horario in self.horarios:
            self.horarios.remove(horario)
        self.fechar_modal()
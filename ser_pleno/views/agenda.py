import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox
from services.agendamentos import ServicoAgendamento
from config.db_config import get_db_connection
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    PrimaryButton,
    GhostButton,
    Divider,
    EmptyState,
    blend_color,
)


class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME.get("bg", "#F1F5F9"))
        self.controller = controller
        self.servico_agendamento = ServicoAgendamento()

        self.data_selecionada = datetime.now()
        self.horarios_base = []
        self.mapa_estudantes = {}

        self.columnconfigure(0, weight=1)

        self.criar_cabecalho()
        self.criar_container_agenda_dia()
        self.criar_container_proxima_semana()

        self.refresh_all()

    def fetch_estudantes(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id_aluno, nome FROM aluno ORDER BY nome ASC")
            rows = cursor.fetchall()
            self.mapa_estudantes = {str(r["nome"]): int(r["id_aluno"]) for r in rows}
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao buscar estudantes: {e}")

    def fetch_horarios_base(self):
        try:
            from config.db_config import get_db_connection

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT Horario FROM disponibilidade WHERE is_active = 1 ORDER BY Horario"
            )
            results = cursor.fetchall()

            self.horarios_base = []
            for row in results:
                horario = row[0]
                if hasattr(horario, "strftime"):
                    self.horarios_base.append(horario.strftime("%H:%M"))
                else:
                    horario_str = str(horario)
                    if len(horario_str) > 5:
                        horario_str = horario_str[:5]
                    self.horarios_base.append(horario_str)

            cursor.close()
            conn.close()

            if not self.horarios_base:
                self.horarios_base = []
        except Exception as e:
            print(f"Erro ao buscar horários base: {e}")
            self.horarios_base = []

    def refresh_all(self):
        self.fetch_horarios_base()
        self.fetch_estudantes()
        self.atualizar_label_data()
        self.load_grid_data()

    def load_grid_data(self):
        data_str = self.data_selecionada.strftime("%Y-%m-%d")
        agendamentos_dia = self.servico_agendamento.listar_agendamentos(data=data_str)
        mapa_dia = {agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_dia}
        self.renderizar_grid(self.container_grid, mapa_dia)

        proxima_semana_str = (self.data_selecionada + timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )
        agendamentos_prox = self.servico_agendamento.listar_agendamentos(
            data=proxima_semana_str
        )
        mapa_prox = {
            agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_prox
        }
        self.renderizar_grid(self.container_semana, mapa_prox)
        self.atualizar_subtitulo_proxima_semana()

    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["page_x"], pady=(20, 10))
        ctk.CTkLabel(header, text="Agenda", font=font(22, "bold")).pack(side="left")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right")

        ctk.CTkButton(
            right,
            text="<",
            width=30,
            height=30,
            fg_color="transparent",
            text_color="black",
            hover_color="#F1F5F9",
            command=lambda: self.alterar_data(-1),
        ).pack(side="left")

        self.lbl_data_display = ctk.CTkLabel(
            right, text="", font=font(13, "bold"), width=180
        )
        self.lbl_data_display.pack(side="left", padx=5)
        self.atualizar_label_data()

        ctk.CTkButton(
            right,
            text=">",
            width=30,
            height=30,
            fg_color="transparent",
            text_color="black",
            hover_color="#F1F5F9",
            command=lambda: self.alterar_data(1),
        ).pack(side="left")

        ctk.CTkButton(
            right,
            text="Gerenciar Horários",
            width=140,
            height=42,
            fg_color="#9333EA",
            command=self.abrir_modal_gestao,
            corner_radius=10,
        ).pack(side="left", padx=(15, 0))

    def atualizar_label_data(self):
        dias_semana = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo",
        ]
        dia_nome = dias_semana[self.data_selecionada.weekday()]
        data_formatada = self.data_selecionada.strftime(f"{dia_nome}, %d de %B")
        self.lbl_data_display.configure(text=data_formatada)

    def atualizar_subtitulo_proxima_semana(self):
        proxima_semana = self.data_selecionada + timedelta(days=7)
        dias_semana = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo",
        ]
        dia_nome = dias_semana[proxima_semana.weekday()]
        data_formatada = proxima_semana.strftime(f"{dia_nome}, %d de %B")
        self.lbl_subtitulo_semana.configure(text=data_formatada)

    def alterar_data(self, dias):
        self.data_selecionada += timedelta(days=dias)
        self.refresh_all()

    def renderizar_grid(self, container, mapa_dados):
        for child in container.winfo_children():
            child.destroy()

        for idx, hora in enumerate(self.horarios_base):
            info = mapa_dados.get(hora)
            ocupado = info is not None
            cor_destaque = "#7E22CE" if ocupado else "#16A34A"

            cell = ctk.CTkFrame(
                container,
                height=120,
                corner_radius=RADIUS["md"],
                border_width=1,
                fg_color=blend_color("#7E22CE", 0.06)
                if ocupado
                else blend_color("#16A34A", 0.06),
                border_color=blend_color("#7E22CE", 0.22)
                if ocupado
                else blend_color("#16A34A", 0.22),
            )
            cell.grid(row=idx // 4, column=idx % 4, padx=6, pady=6, sticky="nsew")
            cell.grid_propagate(False)

            cell.bind(
                "<Button-1>",
                lambda e, h=hora, i=info: self.abrir_modal_agendamento(h, i),
            )
            cell.configure(cursor="hand2")

            ctk.CTkLabel(
                cell,
                text=hora,
                font=themed_font("body", "bold"),
                text_color=cor_destaque,
            ).pack(pady=(10, 0))
            nome_display = info["nome"] if ocupado else "Disponível"
            lbl_nome = ctk.CTkLabel(
                cell,
                text=nome_display,
                font=themed_font("overline", "bold" if ocupado else "normal"),
                text_color=cor_destaque,
                wraplength=110,
            )
            lbl_nome.pack()
            lbl_nome.bind(
                "<Button-1>",
                lambda e, h=hora, i=info: self.abrir_modal_agendamento(h, i),
            )

    def abrir_modal_agendamento(self, hora, info=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Agendamento" if info else "Novo Agendamento")
        modal.geometry("480x720")
        modal.configure(fg_color=THEME["card"])
        modal.grab_set()

        container = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=32, pady=(20, 10))

        ctk.CTkLabel(
            container,
            text="Editar Agendamento" if info else "Novo Agendamento",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 16))

        ctk.CTkLabel(
            container,
            text="Horário",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, 5))
        combo_hora = ctk.CTkComboBox(
            container,
            values=self.horarios_base,
            width=380,
            height=44,
            fg_color="white",
            border_color=THEME["border"],
            button_color=THEME["bg_alt"],
            button_hover_color=THEME["border"],
            dropdown_fg_color="white",
        )
        combo_hora.set(hora)
        combo_hora.pack(pady=(0, 12))

        ctk.CTkLabel(
            container,
            text="Estudante",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, 5))
        combo_estudante = ctk.CTkComboBox(
            container,
            values=list(self.mapa_estudantes.keys()),
            width=380,
            height=44,
            fg_color="white",
            border_color=THEME["border"],
            button_color=THEME["bg_alt"],
            button_hover_color=THEME["border"],
            dropdown_fg_color="white",
        )
        if info:
            combo_estudante.set(info["nome"])
        else:
            combo_estudante.set("Selecione um estudante")
        combo_estudante.pack(pady=(0, 12))

        ctk.CTkLabel(
            container,
            text="Status",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, 5))
        combo_status = ctk.CTkComboBox(
            container,
            values=["Agendado", "Realizado", "Cancelado", "Faltou"],
            width=380,
            height=44,
            fg_color="white",
            border_color=THEME["border"],
            button_color=THEME["bg_alt"],
            button_hover_color=THEME["border"],
            dropdown_fg_color="white",
        )
        if info:
            combo_status.set(info.get("status", "Agendado"))
        else:
            combo_status.set("Agendado")
        combo_status.pack(pady=(0, 12))

        ctk.CTkLabel(
            container,
            text="Observações",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, 5))
        txt_obs = ctk.CTkTextbox(
            container,
            height=100,
            fg_color="white",
            border_width=1,
            border_color=THEME["border"],
            corner_radius=RADIUS["input"],
        )
        if info:
            txt_obs.insert("1.0", info.get("motivo", ""))
        txt_obs.pack(fill="x", pady=(0, 12))

        footer = ctk.CTkFrame(modal, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=32, pady=20)

        if info:
            GhostButton(
                footer,
                text="Remover",
                command=lambda: self.remover_agendamento(info["id_agendamento"], modal),
                width=110,
            ).pack(side="left")

        PrimaryButton(
            footer,
            text="Salvar",
            command=lambda: self.salvar_agendamento(
                modal,
                combo_hora.get(),
                combo_estudante.get(),
                combo_status.get(),
                txt_obs.get("1.0", "end-1c"),
                info,
            ),
            width=120,
        ).pack(side="right")
        GhostButton(footer, text="Cancelar", command=modal.destroy, width=110).pack(
            side="right", padx=10
        )

    def salvar_agendamento(
        self, modal, hora, nome_estudante, status, motivo, info_antiga=None
    ):
        id_aluno = self.mapa_estudantes.get(nome_estudante)
        if not id_aluno:
            messagebox.showerror("Erro", "Selecione um estudante válido.")
            return

        data_hora_str = f"{self.data_selecionada.strftime('%Y-%m-%d')} {hora}"

        dados = {
            "nome_aluno": nome_estudante,
            "id_aluno": id_aluno,
            "data_hora": data_hora_str,
            "motivo": motivo,
            "status": status,
        }

        try:
            if info_antiga:
                res = self.servico_agendamento.atualizar_agendamento(
                    info_antiga["id_agendamento"], dados
                )
            else:
                res = self.servico_agendamento.criar_agendamento(dados)

            if res.get("success"):
                modal.destroy()
                self.refresh_all()
            else:
                messagebox.showerror(
                    "Erro", str(res.get("message", "Erro ao salvar agendamento"))
                )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def remover_agendamento(self, id_agendamento, modal):
        if messagebox.askyesno(
            "Confirmar", "Deseja realmente remover este agendamento?"
        ):
            try:
                res = self.servico_agendamento.deletar_agendamento(id_agendamento)
                if res.get("success"):
                    modal.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror(
                        "Erro", str(res.get("message", "Erro ao remover agendamento"))
                    )
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def criar_container_agenda_dia(self):
        card = Card(self)
        card.pack(fill="x", padx=SPACING["page_x"], pady=10)
        ctk.CTkLabel(
            card.body,
            text="Horários do Dia",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 8))
        Divider(card.body).pack(fill="x", pady=(0, 12))
        self.container_grid = ctk.CTkFrame(card.body, fg_color="transparent")
        self.container_grid.pack(fill="x", pady=(0, 12))
        for i in range(4):
            self.container_grid.columnconfigure(i, weight=1, uniform="grid")

    def criar_container_proxima_semana(self):
        card = Card(self)
        card.pack(fill="x", padx=SPACING["page_x"], pady=10)

        header = ctk.CTkFrame(card.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            header,
            text="Próxima Semana",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")
        self.lbl_subtitulo_semana = ctk.CTkLabel(
            header, text="", font=themed_font("body"), text_color=THEME["text_muted"]
        )
        self.lbl_subtitulo_semana.pack(side="left", padx=(10, 0))

        self.container_semana = ctk.CTkFrame(card.body, fg_color="transparent")
        self.container_semana.pack(fill="x", pady=(0, 12))
        for i in range(4):
            self.container_semana.columnconfigure(i, weight=1, uniform="grid")

    def abrir_modal_gestao(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Gestão de Grade")
        modal.geometry("380x520")
        modal.configure(fg_color=THEME["card"])
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container,
            text="Horários Ativos",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(pady=(0, 12))

        frame_lista = ctk.CTkScrollableFrame(
            container,
            width=340,
            height=280,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["md"],
        )
        frame_lista.pack(pady=6)

        def atualizar_lista_modal():
            for child in frame_lista.winfo_children():
                child.destroy()
            self.fetch_horarios_base()
            for h in self.horarios_base:
                row = ctk.CTkFrame(
                    frame_lista,
                    fg_color="white",
                    corner_radius=RADIUS["sm"],
                    border_width=1,
                    border_color=THEME["border"],
                )
                row.pack(fill="x", pady=4, padx=4)
                ctk.CTkLabel(row, text=h, font=themed_font("body", "bold")).pack(
                    side="left", padx=12, pady=8
                )
                GhostButton(
                    row,
                    text="Remover",
                    command=lambda x=h: self.remover_horario_disponibilidade(
                        x, atualizar_lista_modal
                    ),
                    width=90,
                ).pack(side="right", padx=8, pady=6)

        atualizar_lista_modal()

        ctk.CTkLabel(
            container,
            text="Novo Horário (HH:MM)",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(14, 5))
        new_h = ctk.CTkEntry(
            container,
            width=140,
            height=36,
            corner_radius=RADIUS["sm"],
            border_width=1,
            border_color=THEME["border"],
        )
        new_h.pack(pady=(0, 8))

        def formatar_horario(event):
            texto = new_h.get().replace(":", "")
            if len(texto) >= 2:
                new_h.delete(0, "end")
                new_h.insert(0, f"{texto[:2]}:{texto[2:4]}")

        new_h.bind("<KeyRelease>", formatar_horario)
        PrimaryButton(
            container,
            text="Adicionar à Grade",
            command=lambda: self.adicionar_horario_disponibilidade(
                new_h.get(), atualizar_lista_modal
            ),
        ).pack()

    def adicionar_horario_disponibilidade(self, horario, atualizar_lista):
        if len(horario) < 5 or horario[2] != ":":
            messagebox.showerror("Erro", "Formato de horário inválido. Use HH:MM.")
            return

        try:
            res = self.servico_agendamento.adicionar_horario_disponibilidade(horario)
            if res.get("success"):
                atualizar_lista()
            else:
                messagebox.showerror(
                    "Erro", str(res.get("message", "Erro ao adicionar horário"))
                )
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def remover_horario_disponibilidade(self, horario, atualizar_lista):
        if messagebox.askyesno(
            "Confirmar", f"Deseja realmente remover o horário {horario}?"
        ):
            try:
                res = self.servico_agendamento.remover_horario_disponibilidade(horario)
                if res.get("success"):
                    atualizar_lista()
                else:
                    messagebox.showerror(
                        "Erro", str(res.get("message", "Erro ao remover horário"))
                    )
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {e}")

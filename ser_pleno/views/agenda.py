import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox
from services.agendamentos import ServicoAgendamento
from config.db_config import get_db_connection
from ui_theme import THEME, SPACING, RADIUS, font, themed_font, blend_color, darken, lighten
from components.ui_components import (
    PageHeader, Card, PrimaryButton, GhostButton, Divider, EmptyState,
    InputField, SearchField, Badge, Avatar, Pill, Toast, SectionHeader
)


class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
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
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Horario FROM disponibilidade WHERE is_active = 1 ORDER BY Horario")
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

        proxima_semana_str = (self.data_selecionada + timedelta(days=7)).strftime("%Y-%m-%d")
        agendamentos_prox = self.servico_agendamento.listar_agendamentos(data=proxima_semana_str)
        mapa_prox = {agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_prox}
        self.renderizar_grid(self.container_semana, mapa_prox)
        self.atualizar_subtitulo_proxima_semana()

    def criar_cabecalho(self):
        self.lbl_data_display = ctk.CTkLabel(self, text="", font=themed_font("h2", "bold"), text_color=THEME["text"])
        self.lbl_data_display.pack(padx=SPACING["page_x"], pady=(SPACING["page_y"], 0), anchor="w")

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=SPACING["page_x"], pady=(6, 16))

        nav = ctk.CTkFrame(toolbar, fg_color=THEME["bg_alt"], corner_radius=RADIUS["button"])
        nav.pack(side="left")

        prev = ctk.CTkButton(nav, text="◀", width=34, height=34,
                             fg_color="transparent", hover_color=THEME["bg"],
                             text_color=THEME["text_secondary"], corner_radius=RADIUS["sm"],
                             font=themed_font("body", "bold"),
                             command=lambda: self.alterar_data(-1))
        prev.pack(side="left", padx=2, pady=2)

        self.lbl_data_display_sub = ctk.CTkLabel(nav, text="", font=themed_font("body"), text_color=THEME["text_secondary"], width=200)
        self.lbl_data_display_sub.pack(side="left", padx=8)
        self.atualizar_label_data()

        nxt = ctk.CTkButton(nav, text="▶", width=34, height=34,
                             fg_color="transparent", hover_color=THEME["bg"],
                             text_color=THEME["text_secondary"], corner_radius=RADIUS["sm"],
                             font=themed_font("body", "bold"),
                             command=lambda: self.alterar_data(1))
        nxt.pack(side="left", padx=2, pady=2)

        right = ctk.CTkFrame(toolbar, fg_color="transparent")
        right.pack(side="right")
        PrimaryButton(right, text="Gerenciar Horários", command=self.abrir_modal_gestao, width=170, icon="⚙").pack()

    def atualizar_label_data(self):
        dias_semana = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        dia_nome = dias_semana[self.data_selecionada.weekday()]
        data_formatada = self.data_selecionada.strftime(f"{dia_nome}, %d/%m/%Y")
        self.lbl_data_display.configure(text=data_formatada)
        self.lbl_data_display_sub.configure(text=data_formatada)

    def atualizar_subtitulo_proxima_semana(self):
        proxima_semana = self.data_selecionada + timedelta(days=7)
        dias_semana = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        dia_nome = dias_semana[proxima_semana.weekday()]
        data_formatada = proxima_semana.strftime(f"{dia_nome}, %d/%m/%Y")
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
            cor = THEME["accent"] if ocupado else THEME["success"]
            cell = ctk.CTkFrame(
                container, height=120, corner_radius=RADIUS["md"], border_width=1,
                fg_color=blend_color(cor, 0.07),
                border_color=blend_color(cor, 0.22),
            )
            cell.grid(row=idx // 4, column=idx % 4, padx=6, pady=6, sticky="nsew")
            cell.grid_propagate(False)

            cell.bind("<Button-1>", lambda e, h=hora, i=info: self.abrir_modal_agendamento(h, i))
            cell.configure(cursor="hand2")

            header = ctk.CTkFrame(cell, fg_color="transparent")
            header.pack(fill="x", padx=14, pady=(12, 0))
            ctk.CTkLabel(header, text=hora, font=themed_font("body", "bold"), text_color=cor).pack(side="left")
            status_lbl = ctk.CTkLabel(header, text="Agendado" if ocupado else "Disponível",
                                      font=themed_font("overline"), text_color=cor)
            status_lbl.pack(side="right")

            if ocupado:
                nome = info.get("nome", "")
                ctk.CTkLabel(cell, text=nome, font=themed_font("body", "bold"),
                             text_color=THEME["text"]).pack(pady=(6, 0), padx=14, anchor="w")
                curso = info.get("curso", "")
                ctk.CTkLabel(cell, text=f"🎓 {curso}", font=themed_font("overline"),
                             text_color=THEME["text_muted"]).pack(padx=14, anchor="w")
            else:
                ctk.CTkLabel(cell, text="Livre para atendimento",
                             font=themed_font("body_sm"), text_color=THEME["text_muted"]).pack(pady=(8, 0), padx=14, anchor="w")

            ctk.CTkButton(cell, text="→", width=28, height=28,
                          fg_color="transparent", hover_color=blend_color(cor, 0.18),
                          text_color=cor, corner_radius=RADIUS["pill"],
                          font=themed_font("body", "bold"),
                          command=lambda h=hora, i=info: self.abrir_modal_agendamento(h, i)).pack(anchor="se", padx=10, pady=10)

    def abrir_modal_agendamento(self, hora, info=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Agendamento" if info else "Novo Agendamento")
        modal.geometry("520x760")
        modal.configure(fg_color=THEME["surface"])
        modal.grab_set()
        modal.transient(self.winfo_toplevel())
        w, h = 520, 760
        modal.geometry(f"{w}x{h}+{(modal.winfo_screenwidth()//2)-(w//2)}+{(modal.winfo_screenheight()//2)-(h//2)}")

        container = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=32, pady=(24, 12))

        ctk.CTkLabel(container, text="Editar Agendamento" if info else "Novo Agendamento",
                     font=themed_font("h2", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(container, text="Gerencie horários e estudantes",
                     font=themed_font("body_sm"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(0, 22))
        Divider(container).pack(fill="x", pady=(0, 22))

        def campo(label, placeholder, values=None, initial=None):
            ctk.CTkLabel(container, text=label, font=themed_font("caption", "bold"),
                         text_color=THEME["text_secondary"]).pack(anchor="w", pady=(0, 5))
            widget = ctk.CTkComboBox if values else ctk.CTkEntry
            kw = {"values": values, "width": 440, "height": 44,
                  "fg_color": THEME["bg_alt"], "border_color": THEME["border"],
                  "button_color": THEME["border"], "button_hover_color": THEME["border_strong"],
                  "dropdown_fg_color": THEME["surface"], "corner_radius": RADIUS["input"],
                  "font": themed_font("body")}
            wgt = widget(container, **kw)
            if initial is not None:
                wgt.set(initial)
            elif values:
                wgt.set(values[0])
            else:
                wgt.insert("0", placeholder)
            wgt.pack(pady=(0, 14))
            return wgt

        combo_hora = campo("Horário", "", values=self.horarios_base, initial=hora)
        combo_estudante = campo("Estudante", "", values=list(self.mapa_estudantes.keys()), initial=info["nome"] if info else None)
        combo_status = campo("Status", "", values=["Agendado", "Realizado", "Cancelado", "Faltou"], initial=info.get("status", "Agendado") if info else "Agendado")
        ctk.CTkLabel(container, text="Observações", font=themed_font("caption", "bold"),
                     text_color=THEME["text_secondary"]).pack(anchor="w", pady=(0, 5))
        txt_obs = ctk.CTkTextbox(container, height=100, fg_color=THEME["bg_alt"],
                                 border_color=THEME["border"], border_width=1, corner_radius=RADIUS["input"],
                                 font=themed_font("body"))
        if info:
            txt_obs.insert("1.0", info.get("motivo", ""))
        txt_obs.pack(fill="x", pady=(0, 14))

        footer = ctk.CTkFrame(modal, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=32, pady=20)
        if info:
            GhostButton(footer, text="Remover", command=lambda: self.remover_agendamento(info["id_agendamento"], modal),
                        width=120).pack(side="left")
        GhostButton(footer, text="Cancelar", command=modal.destroy, width=120).pack(side="right", padx=8)
        PrimaryButton(footer, text="Salvar",
                      command=lambda: self.salvar_agendamento(modal, combo_hora.get(), combo_estudante.get(), combo_status.get(), txt_obs.get("1.0", "end-1c"), info),
                      width=120, icon="✔").pack(side="right")

    def salvar_agendamento(self, modal, hora, nome_estudante, status, motivo, info_antiga=None):
        id_aluno = self.mapa_estudantes.get(nome_estudante)
        if not id_aluno:
            messagebox.showerror("Erro", "Selecione um estudante válido.")
            return
        dados = {"nome_aluno": nome_estudante, "id_aluno": id_aluno,
                 "data_hora": f"{self.data_selecionada.strftime('%Y-%m-%d')} {hora}",
                 "motivo": motivo, "status": status}
        try:
            res = self.servico_agendamento.atualizar_agendamento(info_antiga["id_agendamento"], dados) if info_antiga else self.servico_agendamento.criar_agendamento(dados)
            if res.get("success"):
                modal.destroy()
                self.refresh_all()
                Toast(self, "Agendamento salvo com sucesso", status="success", duration=2500)
            else:
                messagebox.showerror("Erro", str(res.get("message", "Erro ao salvar agendamento")))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def remover_agendamento(self, id_agendamento, modal):
        if messagebox.askyesno("Confirmar", "Deseja realmente remover este agendamento?"):
            try:
                res = self.servico_agendamento.deletar_agendamento(id_agendamento)
                if res.get("success"):
                    modal.destroy()
                    self.refresh_all()
                    Toast(self, "Agendamento removido", status="success", duration=2500)
                else:
                    messagebox.showerror("Erro", str(res.get("message", "Erro ao remover agendamento")))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def criar_container_agenda_dia(self):
        card = Card(self, title="📅 Agenda do Dia", status="Em andamento")
        card.pack(fill="x", padx=SPACING["page_x"], pady=10)
        self.container_grid = ctk.CTkFrame(card.body, fg_color="transparent")
        self.container_grid.pack(fill="x", pady=(0, 12))
        for i in range(4):
            self.container_grid.columnconfigure(i, weight=1, uniform="grid")

    def criar_container_proxima_semana(self):
        card = Card(self)
        card.pack(fill="x", padx=SPACING["page_x"], pady=10)
        header = ctk.CTkFrame(card.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Próxima Semana", font=themed_font("h4", "bold"), text_color=THEME["text"]).pack(side="left")
        self.lbl_subtitulo_semana = ctk.CTkLabel(header, text="", font=themed_font("body_sm"), text_color=THEME["text_muted"])
        self.lbl_subtitulo_semana.pack(side="left", padx=(10, 0))
        self.container_semana = ctk.CTkFrame(card.body, fg_color="transparent")
        self.container_semana.pack(fill="x", pady=(0, 12))
        for i in range(4):
            self.container_semana.columnconfigure(i, weight=1, uniform="grid")

    def abrir_modal_gestao(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Gestão de Grade")
        modal.geometry("420x580")
        modal.configure(fg_color=THEME["surface"])
        modal.grab_set()
        modal.transient(self.winfo_toplevel())
        w, h = 420, 580
        modal.geometry(f"{w}x{h}+{(modal.winfo_screenwidth()//2)-(w//2)}+{(modal.winfo_screenheight()//2)-(h//2)}")

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(container, text="Horários Ativos", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(0, 12))
        frame_lista = ctk.CTkScrollableFrame(container, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"], height=260)
        frame_lista.pack(fill="x", pady=(0, 16))

        def atualizar_lista_modal():
            for child in frame_lista.winfo_children():
                child.destroy()
            self.fetch_horarios_base()
            for h in self.horarios_base:
                row = ctk.CTkFrame(frame_lista, fg_color=THEME["surface"], corner_radius=RADIUS["sm"],
                                  border_width=1, border_color=THEME["border"])
                row.pack(fill="x", pady=4, padx=4)
                ctk.CTkLabel(row, text=h, font=themed_font("body", "bold"), text_color=THEME["text"]).pack(side="left", padx=14, pady=10)
                GhostButton(row, text="Remover", command=lambda x=h: self.remover_horario_disponibilidade(x, atualizar_lista_modal), width=110).pack(side="right", padx=10, pady=8)

        atualizar_lista_modal()

        ctk.CTkLabel(container, text="Novo Horário (HH:MM)", font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(10, 5))
        new_h = ctk.CTkEntry(container, width=160, height=36, corner_radius=RADIUS["sm"],
                             border_width=1, border_color=THEME["border"], font=themed_font("body"))
        new_h.pack(anchor="w", pady=(0, 8))

        def formatar_horario(event):
            texto = new_h.get().replace(":", "")
            if len(texto) >= 3:
                new_h.delete(0, "end")
                new_h.insert(0, f"{texto[:2]}:{texto[2:4]}")

        new_h.bind("<KeyRelease>", formatar_horario)
        PrimaryButton(container, text="Adicionar à Grade", command=lambda: self.adicionar_horario_disponibilidade(new_h.get(), atualizar_lista_modal), icon="＋").pack(anchor="w")

    def adicionar_horario_disponibilidade(self, horario, atualizar_lista):
        if len(horario) < 5 or horario[2] != ":":
            messagebox.showerror("Erro", "Formato de horário inválido. Use HH:MM.")
            return
        try:
            res = self.servico_agendamento.adicionar_horario_disponibilidade(horario)
            if res.get("success"):
                atualizar_lista()
            else:
                messagebox.showerror("Erro", str(res.get("message", "Erro ao adicionar horário")))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def remover_horario_disponibilidade(self, horario, atualizar_lista):
        if messagebox.askyesno("Confirmar", f"Deseja realmente remover o horário {horario}?"):
            try:
                res = self.servico_agendamento.remover_horario_disponibilidade(horario)
                if res.get("success"):
                    atualizar_lista()
                else:
                    messagebox.showerror("Erro", str(res.get("message", "Erro ao remover horário")))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {e}")

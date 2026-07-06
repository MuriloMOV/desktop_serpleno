import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox
from ser_pleno.application.services.agendamentos import ServicoAgendamento
from ser_pleno.infrastructure.database import get_db_connection
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font, blend_color, darken, lighten
from ser_pleno.presentation.components.ui_components import (
    PageHeader, Card, PrimaryButton, GhostButton, Divider, EmptyState,
    InputField, SearchField, Badge, Avatar, Pill, Toast, SectionHeader
)


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Paleta dedicada Ó  tela de Agenda
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
AGENDA_COLORS = {
    "cell_ocupado_bg":   blend_color(THEME["primary"], 0.07),
    "cell_ocupado_border": blend_color(THEME["primary"], 0.22),
    "cell_livre_bg":    blend_color(THEME["success"], 0.07),
    "cell_livre_border": blend_color(THEME["success"], 0.22),
    "cell_hover":       blend_color(THEME["primary"], 0.18),
    "nav_bg":           THEME["bg_alt"],
}


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Utilitários puros
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

def _formatar_horario_entry(widget: ctk.CTkEntry):
    """Formata entrada HH:MM automaticamente após digitação."""
    texto = widget.get().replace(":", "")
    if len(texto) >= 3:
        widget.delete(0, "end")
        widget.insert(0, f"{texto[:2]}:{texto[2:4]}")


def _centralizar_janela(janela: ctk.CTkToplevel, w: int = 520, h: int = 760):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() // 2) - (w // 2)
    y = (janela.winfo_screenheight() // 2) - (h // 2)
    janela.geometry(f"{w}x{h}+{x}+{y}")


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Componentes reutilizáveis extraídos para classes próprias
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

class ScheduleCell(ctk.CTkFrame):
    """Célula individual do grid de horários (ocupada ou livre)."""
    def __init__(self, parent, hora: str, info: dict | None, on_open):
        self.hora = hora
        self.info = info
        self.on_open = on_open
        ocupado = info is not None
        cor = THEME["primary"] if ocupado else THEME["success"]

        super().__init__(
            parent, height=120, corner_radius=RADIUS["md"], border_width=1,
            fg_color=blend_color(cor, 0.07) if not ocupado else AGENDA_COLORS["cell_ocupado_bg"],
            border_color=blend_color(cor, 0.22) if not ocupado else AGENDA_COLORS["cell_ocupado_border"],
        )
        self.grid_propagate(False)
        self._cor = cor
        self._build()

    def _build(self):
        self.bind("<Button-1>", lambda e: self._open())
        if hasattr(self, "configure"):
            self.configure(cursor="hand2")

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 0))

        ctk.CTkLabel(header, text=self.hora,
                     font=themed_font("body", "bold"), text_color=self._cor).pack(side="left")
        status_text = "Agendado" if self.info else "Disponível"
        ctk.CTkLabel(header, text=status_text,
                     font=themed_font("overline"), text_color=self._cor).pack(side="right")

        if self.info:
            nome = self.info.get("nome", "")
            ctk.CTkLabel(self, text=nome, font=themed_font("body", "bold"),
                         text_color=THEME["text"]).pack(pady=(6, 0), padx=14, anchor="w")
            curso = self.info.get("curso", "")
            ctk.CTkLabel(self, text=f"ðŸŽ“ {curso}", font=themed_font("overline"),
                         text_color=THEME["text_muted"]).pack(padx=14, anchor="w")
        else:
            ctk.CTkLabel(self, text="Livre para atendimento",
                         font=themed_font("body_sm"), text_color=THEME["text_muted"]).pack(
                pady=(8, 0), padx=14, anchor="w"
            )

        arrow_btn = ctk.CTkButton(
            self, text="â†’", width=28, height=28,
            fg_color="transparent", hover_color=AGENDA_COLORS["cell_hover"],
            text_color=self._cor, corner_radius=RADIUS["pill"],
            font=themed_font("body", "bold"),
            command=lambda: self._open()
        )
        arrow_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def _open(self):
        if self.on_open:
            self.on_open(self.hora, self.info)


class AppointmentModal(ctk.CTkToplevel):
    """Modal de criação/edição de agendamento."""
    def __init__(self, parent, hora: str, info: dict | None,
                 horarios_base: list[str], mapa_estudantes: dict[str, int],
                 on_save, on_delete=None):
        super().__init__(parent)
        self._parent_window = parent.winfo_toplevel()
        self.hora = hora
        self.info = info
        self.horarios_base = horarios_base
        self.mapa_estudantes = mapa_estudantes
        self.on_save = on_save
        self.on_delete = on_delete
        self._setup_window()
        self._build()

    def _setup_window(self):
        self.title("Editar Agendamento" if self.info else "Novo Agendamento")
        self.geometry("520x760")
        self.configure(fg_color=THEME["surface"])
        self.grab_set()
        self.transient(self._parent_window)
        w, h = 520, 760
        self.geometry(f"{w}x{h}+{(self.winfo_screenwidth()//2)-(w//2)}+{(self.winfo_screenheight()//2)-(h//2)}")

    def _build(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=32, pady=(24, 12))

        ctk.CTkLabel(
            container,
            text="Editar Agendamento" if self.info else "Novo Agendamento",
            font=themed_font("h2", "bold"), text_color=THEME["text"]
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            container, text="Gerencie horários e estudantes",
            font=themed_font("body_sm"), text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(0, 22))

        Divider(container).pack(fill="x", pady=(0, 22))

        self.combo_hora = self._campo_combo(container, "Horário", "", self.horarios_base, initial=self.hora)
        estudantes = list(self.mapa_estudantes.keys())
        self.combo_estudante = self._campo_combo(
            container, "Estudante", "", estudantes,
            initial=self.info["nome"] if self.info else None
        )
        self.combo_status = self._campo_combo(
            container, "Status", "", ["Agendado", "Realizado", "Cancelado", "Faltou"],
            initial=self.info.get("status", "Agendado") if self.info else "Agendado"
        )

        ctk.CTkLabel(
            container, text="ObservaçÓµes",
            font=themed_font("caption", "bold"), text_color=THEME["text_secondary"]
        ).pack(anchor="w", pady=(0, 5))

        self.txt_obs = ctk.CTkTextbox(
            container, height=100, fg_color=THEME["bg_alt"],
            border_color=THEME["border"], border_width=1, corner_radius=RADIUS["input"],
            font=themed_font("body")
        )
        if self.info:
            self.txt_obs.insert("1.0", self.info.get("motivo", ""))
        self.txt_obs.pack(fill="x", pady=(0, 14))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=32, pady=20)

        if self.info:
            GhostButton(
                footer, text="Remover",
                command=self._delete, width=120
            ).pack(side="left")

        GhostButton(footer, text="Cancelar", command=self.destroy, width=120).pack(side="right", padx=8)
        PrimaryButton(
            footer, text="Salvar",
            command=self._save, width=120, icon="âœ”"
        ).pack(side="right")

    def _campo_combo(self, parent, label, placeholder, values=None, initial=None):
        ctk.CTkLabel(
            parent, text=label,
            font=themed_font("caption", "bold"), text_color=THEME["text_secondary"]
        ).pack(anchor="w", pady=(0, 5))

        kw = {
            "width": 440, "height": 44,
            "fg_color": THEME["bg_alt"], "border_color": THEME["border"],
            "corner_radius": RADIUS["input"],
            "font": themed_font("body")
        }
        if values:
            kw.update({
                "values": values,
                "button_color": THEME["border"],
                "button_hover_color": THEME["border_strong"],
                "dropdown_fg_color": THEME["surface"],
            })
            wgt = ctk.CTkComboBox(parent, **kw)
            if initial is not None and initial in values:
                wgt.set(initial)
            else:
                wgt.set(values[0] if values else "")
        else:
            wgt = ctk.CTkEntry(parent, **kw)
            if initial is not None:
                wgt.delete(0, "end")
                wgt.insert(0, initial)
            else:
                wgt.insert("0", placeholder)

        wgt.pack(pady=(0, 14))
        return wgt

    def _save(self):
        if self.on_save is None:
            self.destroy()
            return
        hora = self.combo_hora.get()
        nome = self.combo_estudante.get()
        status = self.combo_status.get()
        motivo = self.txt_obs.get("1.0", "end-1c")

        id_aluno = self.mapa_estudantes.get(nome)
        if not id_aluno:
            messagebox.showerror("Erro", "Selecione um estudante válido.")
            return

        dados = {
            "nome_aluno": nome,
            "id_aluno": id_aluno,
            "data_hora": f"{self._get_data_selecionada()} {hora}",
            "motivo": motivo,
            "status": status,
        }
        try:
            id_antigo = self.info.get("id_agendamento") if self.info else None
            res = self.on_save(id_antigo, dados)
            if res.get("success"):
                self.destroy()
                Toast(self, "Agendamento salvo com sucesso", status="success", duration=2500)
            else:
                messagebox.showerror("Erro", str(res.get("message", "Erro ao salvar")))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def _delete(self):
        if not self.info:
            return
        if messagebox.askyesno("Confirmar", "Deseja realmente remover este agendamento?"):
            try:
                res = self.on_delete(self.info["id_agendamento"])
                if res.get("success"):
                    self.destroy()
                    Toast(self, "Agendamento removido", status="success", duration=2500)
                else:
                    messagebox.showerror("Erro", str(res.get("message", "Erro ao remover")))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {e}")

    @staticmethod
    def _get_data_selecionada():
        # Será sobrescrito pelo AgendaFrame via closure se necessário
        return datetime.now().strftime("%Y-%m-%d")


class GradeManagementModal(ctk.CTkToplevel):
    """Modal de gestão de grade de horários."""
    def __init__(self, parent, horarios_base: list[str], servico: ServicoAgendamento,
                 on_refresh):
        super().__init__(parent)
        self._parent_window = parent.winfo_toplevel()
        self.horarios_base = horarios_base
        self.servico = servico
        self.on_refresh = on_refresh
        self._setup_window()
        self._build()

    def _setup_window(self):
        self.title("Gestão de Grade")
        self.geometry("420x580")
        self.configure(fg_color=THEME["surface"])
        self.grab_set()
        self.transient(self._parent_window)
        _centralizar_janela(self, w=420, h=580)

    def _build(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            container, text="Horários Ativos",
            font=themed_font("h3", "bold"), text_color=THEME["text"]
        ).pack(anchor="w", pady=(0, 12))

        self.lista_frame = ctk.CTkScrollableFrame(
            container, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"], height=260
        )
        self.lista_frame.pack(fill="x", pady=(0, 16))

        self._render_lista()

        ctk.CTkLabel(
            container, text="Novo Horário (HH:MM)",
            font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack(anchor="w", pady=(10, 5))

        self.entry_novo = ctk.CTkEntry(
            container, width=160, height=36, corner_radius=RADIUS["sm"],
            border_width=1, border_color=THEME["border"], font=themed_font("body")
        )
        self.entry_novo.pack(anchor="w", pady=(0, 8))
        self.entry_novo.bind("<KeyRelease>", lambda e: _formatar_horario_entry(self.entry_novo))

        PrimaryButton(
            container, text="Adicionar Ó  Grade",
            command=self._adicionar, icon="ï¼‹"
        ).pack(anchor="w")

    def _render_lista(self):
        for child in self.lista_frame.winfo_children():
            child.destroy()

        self.on_refresh()
        for h in self.horarios_base:
            row = ctk.CTkFrame(
                self.lista_frame, fg_color=THEME["surface"],
                corner_radius=RADIUS["sm"], border_width=1, border_color=THEME["border"]
            )
            row.pack(fill="x", pady=4, padx=4)

            ctk.CTkLabel(
                row, text=h, font=themed_font("body", "bold"), text_color=THEME["text"]
            ).pack(side="left", padx=14, pady=10)

            GhostButton(
                row, text="Remover",
                command=lambda x=h: self._remover(x),
                width=110
            ).pack(side="right", padx=10, pady=8)

    def _adicionar(self):
        horario = self.entry_novo.get().strip()
        if len(horario) < 5 or horario[2] != ":":
            messagebox.showerror("Erro", "Formato de horário inválido. Use HH:MM.")
            return
        try:
            res = self.servico.adicionar_horario_disponibilidade(horario)
            if res.get("success"):
                self.entry_novo.delete(0, "end")
                self._render_lista()
            else:
                messagebox.showerror("Erro", str(res.get("message", "Erro ao adicionar horário")))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def _remover(self, horario):
        if messagebox.askyesno("Confirmar", f"Deseja realmente remover o horário {horario}?"):
            try:
                res = self.servico.remover_horario_disponibilidade(horario)
                if res.get("success"):
                    self._render_lista()
                else:
                    messagebox.showerror("Erro", str(res.get("message", "Erro ao remover horário")))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {e}")


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Frame Principal – Agenda
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_agendamento = ServicoAgendamento()

        self.data_selecionada = datetime.now()
        self.horarios_base: list[str] = []
        self.mapa_estudantes: dict[str, int] = {}

        self.grid_columnconfigure(0, weight=1)

        self._criar_cabecalho()
        self._criar_container_agenda_dia()
        self._criar_container_proxima_semana()
        self.refresh_all()

    # ──────────────────────────────────────────────────────────────────────
    #  Ciclo de vida e dados
    # ──────────────────────────────────────────────────────────────────────

    def refresh_all(self):
        self.fetch_horarios_base()
        self.fetch_estudantes()
        self._atualizar_label_data()
        self.load_grid_data()

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
                    self.horarios_base.append(horario_str[:5] if len(horario_str) > 5 else horario_str)
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao buscar horários base: {e}")
            self.horarios_base = []

    def load_grid_data(self):
        data_str = self.data_selecionada.strftime("%Y-%m-%d")
        agendamentos_dia = self.servico_agendamento.listar_agendamentos(data=data_str)
        mapa_dia = {agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_dia}
        self._renderizar_grid(self.container_grid, mapa_dia)

        proxima_semana_str = (self.data_selecionada + timedelta(days=7)).strftime("%Y-%m-%d")
        agendamentos_prox = self.servico_agendamento.listar_agendamentos(data=proxima_semana_str)
        mapa_prox = {agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_prox}
        self._renderizar_grid(self.container_semana, mapa_prox)
        self._atualizar_subtitulo_proxima_semana()

    # ──────────────────────────────────────────────────────────────────────
    #  Grid de agendamentos
    # ──────────────────────────────────────────────────────────────────────

    def _renderizar_grid(self, container, mapa_dados):
        for child in container.winfo_children():
            child.destroy()

        for idx, hora in enumerate(self.horarios_base):
            info = mapa_dados.get(hora)
            cell = ScheduleCell(container, hora, info, on_open=self._abrir_modal_agendamento)
            cell.grid(row=idx // 4, column=idx % 4, padx=6, pady=6, sticky="nsew")

    # ──────────────────────────────────────────────────────────────────────
    #  Cabeçalho
    # ──────────────────────────────────────────────────────────────────────

    def _criar_cabecalho(self):
        self.lbl_data_display = ctk.CTkLabel(
            self, text="", font=themed_font("h2", "bold"), text_color=THEME["text"]
        )
        self.lbl_data_display.pack(padx=SPACING["page_x"], pady=(SPACING["page_y"], 0), anchor="w")

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=SPACING["page_x"], pady=(6, 16))

        nav = ctk.CTkFrame(toolbar, fg_color=AGENDA_COLORS["nav_bg"], corner_radius=RADIUS["button"])
        nav.pack(side="left")

        self._botao_navegacao(nav, "—€", -1)
        self._label_data_nav(nav)
        self._botao_navegacao(nav, "–¶", 1)

        right = ctk.CTkFrame(toolbar, fg_color="transparent")
        right.pack(side="right")
        PrimaryButton(right, text="Gerenciar Horários", command=self._abrir_modal_gestao, width=170, icon="âš™").pack()

    def _botao_navegacao(self, parent, texto, delta):
        btn = ctk.CTkButton(
            parent, text=texto, width=34, height=34,
            fg_color="transparent", hover_color=THEME["bg"],
            text_color=THEME["text_secondary"], corner_radius=RADIUS["sm"],
            font=themed_font("body", "bold"),
            command=lambda: self.alterar_data(delta)
        )
        btn.pack(side="left", padx=2, pady=2)

    def _label_data_nav(self, parent):
        self.lbl_data_display_sub = ctk.CTkLabel(
            parent, text="", font=themed_font("body"),
            text_color=THEME["text_secondary"], width=200
        )
        self.lbl_data_display_sub.pack(side="left", padx=8)
        self._atualizar_label_data()

    # ──────────────────────────────────────────────────────────────────────
    #  Data e navegação
    # ──────────────────────────────────────────────────────────────────────

    def _atualizar_label_data(self):
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        dia_nome = dias_semana[self.data_selecionada.weekday()]
        formato = f"{dia_nome}, %d/%m/%Y"
        texto = self.data_selecionada.strftime(formato)
        self.lbl_data_display.configure(text=texto)
        self.lbl_data_display_sub.configure(text=texto)

    def _atualizar_subtitulo_proxima_semana(self):
        proxima = self.data_selecionada + timedelta(days=7)
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        dia_nome = dias_semana[proxima.weekday()]
        self.lbl_subtitulo_semana.configure(
            text=proxima.strftime(f"{dia_nome}, %d/%m/%Y")
        )

    def alterar_data(self, dias: int):
        self.data_selecionada += timedelta(days=dias)
        self.refresh_all()

    # ──────────────────────────────────────────────────────────────────────
    #  Containers principais
    # ──────────────────────────────────────────────────────────────────────

    def _criar_container_agenda_dia(self):
        card = Card(self, title="ðŸ“… Agenda do Dia", status="Em andamento")
        card.pack(fill="x", padx=SPACING["page_x"], pady=10)
        self.container_grid = ctk.CTkFrame(card.body, fg_color="transparent")
        self.container_grid.pack(fill="x", pady=(0, 12))
        for i in range(4):
            self.container_grid.columnconfigure(i, weight=1, uniform="grid")

    def _criar_container_proxima_semana(self):
        card = Card(self)
        card.pack(fill="x", padx=SPACING["page_x"], pady=10)

        header = ctk.CTkFrame(card.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header, text="Próxima Semana",
            font=themed_font("h4", "bold"), text_color=THEME["text"]
        ).pack(side="left")

        self.lbl_subtitulo_semana = ctk.CTkLabel(
            header, text="", font=themed_font("body_sm"), text_color=THEME["text_muted"]
        )
        self.lbl_subtitulo_semana.pack(side="left", padx=(10, 0))

        self.container_semana = ctk.CTkFrame(card.body, fg_color="transparent")
        self.container_semana.pack(fill="x", pady=(0, 12))
        for i in range(4):
            self.container_semana.columnconfigure(i, weight=1, uniform="grid")

    # ──────────────────────────────────────────────────────────────────────
    #  Modais
    # ──────────────────────────────────────────────────────────────────────

    def _abrir_modal_agendamento(self, hora: str, info: dict | None = None):
        modal = AppointmentModal(
            self, hora, info,
            horarios_base=self.horarios_base,
            mapa_estudantes=self.mapa_estudantes,
            on_save=self._salvar_agendamento,
            on_delete=self.remover_agendamento
        )
        # Injeta data selecionada no modal estático
        modal._get_data_selecionada = lambda: self.data_selecionada.strftime("%Y-%m-%d")

    def _abrir_modal_gestao(self):
        GradeManagementModal(
            self, self.horarios_base, self.servico_agendamento,
            on_refresh=self.fetch_horarios_base
        )

    # ──────────────────────────────────────────────────────────────────────
    #  CRUD de agendamentos
    # ──────────────────────────────────────────────────────────────────────

    def _salvar_agendamento(self, id_antigo: int | None, dados: dict):
        return (
            self.servico_agendamento.atualizar_agendamento(id_antigo, dados)
            if id_antigo
            else self.servico_agendamento.criar_agendamento(dados)
        )

    def remover_agendamento(self, id_agendamento: int):
        return self.servico_agendamento.deletar_agendamento(id_agendamento)

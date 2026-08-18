import logging
from datetime import datetime, timedelta

import customtkinter as ctk

from ser_pleno.features.agenda.service import ServicoAgendamento
from ser_pleno.ui.components.icons import ICONS, IconButton
from ser_pleno.ui.components.ui_components import (
    BaseModal,
    Card,
    Divider,
    EmptyState,
    GhostButton,
    PrimaryButton,
    SkeletonLoader,
    Toast,
    bind_clickable,
)
from ser_pleno.ui.theme import (
    RADIUS,
    SPACING,
    THEME,
    blend_color,
    themed_font,
)
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.views.base import _ErrorModal
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger(__name__)

AGENDA_COLORS = {
    "cell_ocupado_bg": blend_color(THEME["primary"], 0.07),
    "cell_ocupado_border": blend_color(THEME["primary"], 0.22),
    "cell_livre_bg": blend_color(THEME["success"], 0.07),
    "cell_livre_border": blend_color(THEME["success"], 0.22),
    "cell_hover": blend_color(THEME["primary"], 0.18),
    "nav_bg": THEME["bg_alt"],
}


def _formatar_horario_entry(widget: ctk.CTkEntry):
    texto = widget.get().replace(":", "")
    if len(texto) >= 3:
        widget.delete(0, "end")
        widget.insert(0, f"{texto[:2]}:{texto[2:4]}")


def _centralizar_janela(janela: ctk.CTkToplevel, w: int = 520, h: int = 760):
    janela.update_idletasks()
    x = (janela.winfo_screenwidth() // 2) - (w // 2)
    y = (janela.winfo_screenheight() // 2) - (h // 2)
    janela.geometry(f"{w}x{h}+{x}+{y}")


class ScheduleCell(ctk.CTkFrame):
    def __init__(self, parent, hora: str, info: dict | None, on_open):
        self.hora = hora
        self.info = info
        self.on_open = on_open
        ocupado = info is not None
        cor = THEME["primary"] if ocupado else THEME["success"]

        super().__init__(
            parent,
            height=120,
            corner_radius=RADIUS["md"],
            border_width=1,
            fg_color=blend_color(cor, 0.07) if not ocupado else AGENDA_COLORS["cell_ocupado_bg"],
            border_color=blend_color(cor, 0.22)
            if not ocupado
            else AGENDA_COLORS["cell_ocupado_border"],
        )
        self.grid_propagate(False)
        self._cor = cor
        self._build()

    def _build(self):
        bind_clickable(self, self._open)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=spacing("md"), pady=(spacing("md"), 0))

        ctk.CTkLabel(
            header, text=self.hora, font=themed_font("body", "bold"), text_color=self._cor
        ).pack(side="left")
        status_text = "Agendado" if self.info else "Disponível"
        ctk.CTkLabel(
            header, text=status_text, font=themed_font("overline"), text_color=self._cor
        ).pack(side="right")

        if self.info:
            nome = self.info.get("nome", "")
            ctk.CTkLabel(
                self, text=nome, font=themed_font("body", "bold"), text_color=THEME["text"]
            ).pack(pady=(spacing("sm"), 0), padx=spacing("md"), anchor="w")
            curso = self.info.get("curso", "")
            ctk.CTkLabel(
                self,
                text=f"{ICONS['users']} {curso}",
                font=themed_font("overline"),
                text_color=THEME["text_muted"],
            ).pack(padx=spacing("md"), anchor="w")
        else:
            ctk.CTkLabel(
                self,
                text="Livre para atendimento",
                font=themed_font("body_sm"),
                text_color=THEME["text_muted"],
            ).pack(pady=(spacing("md"), 0), padx=spacing("md"), anchor="w")

        arrow_btn = IconButton(
            self,
            icon=ICONS["arrow_forward"],
            size=28,
            fg_color="transparent",
            hover_color=AGENDA_COLORS["cell_hover"],
            text_color=self._cor,
            corner_radius=RADIUS["pill"],
            command=self._open,
        )
        arrow_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def _open(self):
        if self.on_open:
            self.on_open(self.hora, self.info)


class AppointmentModal(BaseModal):
    def __init__(
        self,
        parent,
        hora: str,
        info: dict | None,
        horarios_base: list[str],
        mapa_estudantes: dict[str, int],
        on_save,
        on_delete=None,
        on_success=None,
    ):
        self._parent_window = parent.winfo_toplevel()
        self.hora = hora
        self.info = info
        self.horarios_base = horarios_base
        self.mapa_estudantes = mapa_estudantes
        self.on_save = on_save
        self.on_delete = on_delete
        self.on_success = on_success
        super().__init__(
            parent,
            title="Editar Agendamento" if info else "Novo Agendamento",
            width=520,
            height=760,
        )
        self._build()

    def _build(self):
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=32, pady=(24, 12))

        ctk.CTkLabel(
            container,
            text="Editar Agendamento" if self.info else "Novo Agendamento",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            container,
            text="Gerencie horários e estudantes",
            font=themed_font("body_sm"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w", pady=(0, 22))

        Divider(container).pack(fill="x", pady=(0, 22))

        self.combo_hora = self._campo_combo(
            container, "Horário", "", self.horarios_base, initial=self.hora
        )
        estudantes = list(self.mapa_estudantes.keys())
        self.combo_estudante = self._campo_combo(
            container, "Estudante", "", estudantes, initial=self.info["nome"] if self.info else None
        )
        self.combo_status = self._campo_combo(
            container,
            "Status",
            "",
            ["Agendado", "Realizado", "Cancelado", "Faltou"],
            initial=self.info.get("status", "Agendado") if self.info else "Agendado",
        )

        ctk.CTkLabel(
            container,
            text="Observações",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 5))

        self.txt_obs = ctk.CTkTextbox(
            container,
            height=100,
            fg_color=THEME["bg_alt"],
            border_color=THEME["border"],
            border_width=1,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        if self.info:
            self.txt_obs.insert("1.0", self.info.get("motivo", ""))
        self.txt_obs.pack(fill="x", pady=(0, 14))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=32, pady=20)

        if self.info:
            GhostButton(footer, text="Remover", command=self._delete, width=120).pack(side="left")

        GhostButton(footer, text="Cancelar", command=self.destroy, width=120).pack(
            side="right", padx=8
        )
        PrimaryButton(
            footer, text="Salvar", command=self._save, width=120, icon=ICONS["save"]
        ).pack(side="right")

    def _campo_combo(self, parent, label, placeholder, values=None, initial=None):
        ctk.CTkLabel(
            parent,
            text=label,
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 5))

        kw = {
            "width": 440,
            "height": 44,
            "fg_color": THEME["bg_alt"],
            "border_color": THEME["border"],
            "corner_radius": RADIUS["input"],
            "font": themed_font("body"),
        }
        if values:
            kw.update(
                {
                    "values": values,
                    "button_color": THEME["border"],
                    "button_hover_color": THEME["border_strong"],
                    "dropdown_fg_color": THEME["surface"],
                }
            )
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
            self._show_error("Selecione um estudante válido.")
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
                if callable(getattr(self, "on_success", None)):
                    try:
                        self.on_success()
                    except Exception:
                        pass
                Toast(
                    self._parent_window,
                    "Agendamento salvo com sucesso",
                    status="success",
                    duration=2500,
                )
                self.destroy()
            else:
                self._show_error(str(res.get("message", "Erro ao salvar")))
        except Exception as e:
            self._show_error(f"Erro inesperado: {e}")

    def _delete(self):
        if not self.info:
            return
        if self._confirmar("Deseja realmente remover este agendamento?"):
            try:
                res = self.on_delete(self.info["id_agendamento"])
                if res.get("success"):
                    if callable(getattr(self, "on_success", None)):
                        try:
                            self.on_success()
                        except Exception:
                            pass
                    Toast(
                        self._parent_window, "Agendamento removido", status="success", duration=2500
                    )
                    self.destroy()
                else:
                    self._show_error(str(res.get("message", "Erro ao remover")))
            except Exception as e:
                self._show_error(f"Erro inesperado: {e}")

    @staticmethod
    def _get_data_selecionada():
        return datetime.now().strftime("%Y-%m-%d")


class CalendarDayModal(BaseModal):
    def __init__(
        self,
        parent,
        data_str: str,
        agendamentos: list[dict],
        horarios_base: list[str],
        mapa_estudantes: dict[str, int],
        on_save,
        on_delete=None,
        on_success=None,
    ):
        self._parent_window = parent.winfo_toplevel()
        self.data_str = data_str
        self.agendamentos = agendamentos
        self.horarios_base = horarios_base
        self.mapa_estudantes = mapa_estudantes
        self.on_save = on_save
        self.on_delete = on_delete
        self.on_success = on_success
        try:
            dt = datetime.strptime(data_str, "%Y-%m-%d")
            titulo = dt.strftime("%d/%m/%Y")
        except Exception:
            titulo = data_str
        super().__init__(parent, title=f"Agendamentos do dia {titulo}", width=480, height=520)
        self._build()

    def _build(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            container,
            text="Agendamentos do dia",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        self.lista_frame = ctk.CTkScrollableFrame(
            container, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"], height=260
        )
        self.lista_frame.pack(fill="x", pady=(0, 16))
        self._render_lista()

        PrimaryButton(
            container,
            text="Novo Agendamento",
            command=self._novo_agendamento,
            icon=ICONS["add"],
            width=200,
        ).pack(anchor="w")

    def _render_lista(self):
        for child in self.lista_frame.winfo_children():
            child.destroy()

        if not self.agendamentos:
            EmptyState(
                self.lista_frame,
                icon=ICONS["calendar"],
                title="Nenhum agendamento",
                subtitle="Clique em Novo Agendamento para criar",
            ).pack(pady=20)
            return

        batch = WidgetBatchBuilder(parent=self.lista_frame, batch_size=20)
        for agt in self.agendamentos:
            batch.add(lambda a=agt: self._criar_item_lista(a))
        batch.execute()

    def _criar_item_lista(self, agt):
        row = ctk.CTkFrame(
            self.lista_frame,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["sm"],
            border_width=1,
            border_color=THEME["border"],
        )
        row.pack(fill="x", pady=4, padx=4)

        nome = agt.get("nome", "")
        hora = agt.get("data_hora")
        hora_str = hora.strftime("%H:%M") if hasattr(hora, "strftime") else str(hora)
        status = agt.get("status", "")

        ctk.CTkLabel(
            row,
            text=f"{hora_str} — {nome}",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left", padx=14, pady=10)

        ctk.CTkLabel(
            row, text=status, font=themed_font("overline"), text_color=THEME["text_muted"]
        ).pack(side="right", padx=14, pady=10)

        bind_clickable(row, lambda: self._abrir_edicao(agt))

    def _abrir_edicao(self, agt):
        if agt.get("data_hora") and hasattr(agt["data_hora"], "strftime"):
            hora = agt["data_hora"].strftime("%H:%M")
        else:
            hora = ""
        modal = AppointmentModal(
            self,
            hora,
            agt,
            horarios_base=self.horarios_base,
            mapa_estudantes=self.mapa_estudantes,
            on_save=self.on_save,
            on_delete=self.on_delete,
            on_success=self._refresh_and_close,
        )
        modal._get_data_selecionada = lambda: self.data_str

    def _novo_agendamento(self):
        if not self.horarios_base:
            self._show_error(
                "Nenhum horário configurado. Adicione horários na gestão de grade.", title="Info"
            )
            return
        modal = AppointmentModal(
            self,
            self.horarios_base[0],
            None,
            horarios_base=self.horarios_base,
            mapa_estudantes=self.mapa_estudantes,
            on_save=self.on_save,
            on_delete=self.on_delete,
            on_success=self._refresh_and_close,
        )
        modal._get_data_selecionada = lambda: self.data_str

    def _refresh_and_close(self):
        if callable(getattr(self, "on_success", None)):
            try:
                self.on_success()
            except Exception:
                pass
        self.destroy()


class GradeManagementModal(BaseModal):
    def __init__(
        self, parent, horarios_base: list[str], servico_agenda: ServicoAgendamento, on_refresh
    ):
        self._parent_window = parent.winfo_toplevel()
        self.horarios_base = horarios_base
        self.servico_agenda = servico_agenda
        self.on_refresh = on_refresh
        self._loading = False
        super().__init__(parent, title="Gestão de Grade", width=420, height=580)
        self._build()

    def _build(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=24)

        self._sync_label = ctk.CTkLabel(
            container,
            text="",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        )
        self._sync_label.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            container,
            text="Horários Ativos",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        self.lista_frame = ctk.CTkScrollableFrame(
            container, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"], height=260
        )
        self.lista_frame.pack(fill="x", pady=(0, 16))

        self._render_lista_skeletons()
        self.after_idle(self._load_horarios_async)

        ctk.CTkLabel(
            container,
            text="Novo Horário (HH:MM)",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(10, 5))

        self.entry_novo = ctk.CTkEntry(
            container,
            width=160,
            height=36,
            corner_radius=RADIUS["sm"],
            border_width=1,
            border_color=THEME["border"],
            font=themed_font("body"),
        )
        self.entry_novo.pack(anchor="w", pady=(0, 8))
        self.entry_novo.bind("<KeyRelease>", lambda e: _formatar_horario_entry(self.entry_novo))

        PrimaryButton(
            container,
            text="Adicionar à Grade",
            command=self._adicionar,
            icon=ICONS["add"],
            width=160,
        ).pack(anchor="w")

    def _render_lista_skeletons(self):
        for child in self.lista_frame.winfo_children():
            child.destroy()
        batch = WidgetBatchBuilder(parent=self.lista_frame, batch_size=20)
        for idx in range(4):
            batch.add(
                lambda i=idx: SkeletonLoader(
                    self.lista_frame, width=280, height=40, variant="card"
                ).pack(fill="x", pady=4, padx=4)
            )
        batch.execute()

    def _set_sync_status(self, text):
        if self._sync_label is not None:
            self._sync_label.configure(text=text)

    def _load_horarios_async(self):
        if getattr(self, "_loading", False):
            return
        self._loading = True

        def fetch():
            return self.servico_agenda.listar_horarios_base()

        def on_success(horarios):
            self._loading = False
            if not self.winfo_exists():
                return
            self.horarios_base = horarios
            self._render_lista()
            self._set_sync_status("")

        def on_error(exc):
            self._loading = False
            logger.error("GradeManagementModal._load_horarios_async: ERRO = %s", exc)
            self._set_sync_status("")

        self._set_sync_status("Sincronizando...")
        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _render_lista(self):
        for child in self.lista_frame.winfo_children():
            child.destroy()

        if not self.horarios_base:
            EmptyState(
                self.lista_frame,
                icon=ICONS["calendar"],
                title="Nenhum horário configurado",
                subtitle="Adicione horários para compor a grade",
            ).pack(pady=20)
            return

        batch = WidgetBatchBuilder(parent=self.lista_frame, batch_size=20)
        for h in self.horarios_base:
            batch.add(lambda h=h: self._criar_item_horario(h))
        batch.execute()

    def _criar_item_horario(self, h):
        row = ctk.CTkFrame(
            self.lista_frame,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["sm"],
            border_width=1,
            border_color=THEME["border"],
        )
        row.pack(fill="x", pady=4, padx=4)

        ctk.CTkLabel(
            row, text=h, font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack(side="left", padx=14, pady=10)

        GhostButton(row, text="Remover", command=lambda x=h: self._remover(x), width=110).pack(
            side="right", padx=10, pady=8
        )

    def _adicionar(self):
        horario = self.entry_novo.get().strip()
        if len(horario) < 5 or horario[2] != ":":
            self._show_error("Formato de horário inválido. Use HH:MM.")
            return

        def fetch():
            return self.servico_agenda.adicionar_horario_disponibilidade(horario)

        def on_success(res):
            if not self.winfo_exists():
                return
            if res.get("success"):
                self.entry_novo.delete(0, "end")
                self._load_horarios_async()
                if callable(getattr(self, "on_refresh", None)):
                    try:
                        self.on_refresh()
                    except Exception:
                        pass
            else:
                self._show_error(str(res.get("message", "Erro ao adicionar horário")))

        def on_error(exc):
            logger.error("GradeManagementModal._adicionar: ERRO = %s", exc)
            self._show_error(f"Erro inesperado: {exc}")

        self._set_sync_status("Adicionando...")
        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _remover(self, horario):
        if not self._confirmar(f"Deseja realmente remover o horário {horario}?"):
            return

        def fetch():
            return self.servico_agenda.remover_horario_disponibilidade(horario)

        def on_success(res):
            if not self.winfo_exists():
                return
            if res.get("success"):
                self._load_horarios_async()
                if callable(getattr(self, "on_refresh", None)):
                    try:
                        self.on_refresh()
                    except Exception:
                        pass
            else:
                self._show_error(str(res.get("message", "Erro ao remover horário")))

        def on_error(exc):
            logger.error("GradeManagementModal._remover: ERRO = %s", exc)
            self._show_error(f"Erro inesperado: {exc}")

        self._set_sync_status("Removendo...")
        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)


class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        import time as _time

        self._t0 = _time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_agenda = ServicoAgendamento(
            auth_service=getattr(controller, "auth_service", None)
        )

        self.data_selecionada = datetime.now()
        self.ano_calendario = self.data_selecionada.year
        self.mes_calendario = self.data_selecionada.month
        self.horarios_base: list[str] = []
        self.mapa_estudantes: dict[str, int] = {}
        self.mapa_agendamentos_mes: dict[str, list[dict]] = {}

        self.grid_columnconfigure(0, weight=1)

        self._criar_cabecalho()
        self._criar_container_agenda_dia()
        self._criar_container_proxima_semana()
        self._criar_calendario_mensal()

        self._mostrar_skeletons_grid(self.container_grid)
        self._mostrar_skeletons_grid(self.container_semana)
        self._mostrar_skeleton_calendario()

        self.after_idle(self.refresh_all_async)
        log_view_init_ms("agenda", self._t0, widget_ref=self)

    def refresh_all_async(self):
        def fetch():
            self._carregar_horarios_base()
            self._carregar_estudantes()
            data_str = self.data_selecionada.strftime("%Y-%m-%d")
            agendamentos_dia = self.servico_agenda.listar_agendamentos(data=data_str)
            proxima_semana_str = (self.data_selecionada + timedelta(days=7)).strftime("%Y-%m-%d")
            agendamentos_prox = self.servico_agenda.listar_agendamentos(data=proxima_semana_str)
            ano_mes = self.servico_agenda.listar_agendamentos_mes(
                self.ano_calendario, self.mes_calendario
            )
            return data_str, agendamentos_dia, proxima_semana_str, agendamentos_prox, ano_mes

        def on_success(result):
            if not self.winfo_exists():
                return
            data_str, agendamentos_dia, proxima_semana_str, agendamentos_prox, ano_mes = result
            mapa_dia = {agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_dia}
            mapa_prox = {agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_prox}
            self._renderizar_grid(self.container_grid, mapa_dia)
            self._renderizar_grid(self.container_semana, mapa_prox)
            self._atualizar_subtitulo_proxima_semana()
            self._processar_agendamentos_mes(ano_mes)
            self._renderizar_calendario(self.ano_calendario, self.mes_calendario)

        def on_error(exc):
            logger.error("AgendaFrame.refresh_all_async: ERRO = %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _mostrar_skeletons_grid(self, container):
        for w in container.winfo_children():
            w.destroy()
        batch = WidgetBatchBuilder(parent=container, batch_size=20)
        for idx in range(8):
            batch.add(
                lambda i=idx: SkeletonLoader(
                    container, width=220, height=100, variant="card"
                ).grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="nsew")
            )
        batch.execute()

    def _mostrar_skeleton_calendario(self):
        for w in self.container_calendario.winfo_children():
            w.destroy()
        batch = WidgetBatchBuilder(parent=self.container_calendario, batch_size=20)
        for idx in range(6):
            batch.add(
                lambda i=idx: SkeletonLoader(
                    self.container_calendario, width=120, height=80, variant="card"
                ).grid(row=i // 7 + 1, column=i % 7, padx=4, pady=4, sticky="nsew")
            )
        batch.execute()

    def refresh_all(self):
        self.refresh_all_async()

    def _carregar_estudantes(self):
        try:
            rows = self.servico_agenda.listar_estudantes()
            self.mapa_estudantes = {
                str(r.get("nome") or r.get("student_name") or ""): int(
                    r.get("id_aluno") or r.get("student_id") or 0
                )
                for r in rows
                if (r.get("nome") or r.get("student_name"))
                and (r.get("id_aluno") or r.get("student_id"))
            }
        except Exception as e:
            logger.error("Erro ao buscar estudantes: %s", e)
            self.mapa_estudantes = {}

    def _carregar_horarios_base(self):
        try:
            self.horarios_base = self.servico_agenda.listar_horarios_base()
        except Exception as e:
            logger.error("Erro ao buscar horários base: %s", e)
            self.horarios_base = []

    def load_grid_data(self):
        try:
            data_str = self.data_selecionada.strftime("%Y-%m-%d")
            agendamentos_dia = self.servico_agenda.listar_agendamentos(data=data_str)
            mapa_dia = {agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_dia}
            self._renderizar_grid(self.container_grid, mapa_dia)

            proxima_semana_str = (self.data_selecionada + timedelta(days=7)).strftime("%Y-%m-%d")
            agendamentos_prox = self.servico_agenda.listar_agendamentos(data=proxima_semana_str)
            mapa_prox = {agt["data_hora"].strftime("%H:%M"): agt for agt in agendamentos_prox}
            self._renderizar_grid(self.container_semana, mapa_prox)
            self._atualizar_subtitulo_proxima_semana()
        except Exception as e:
            logger.error("AgendaFrame.load_grid_data: ERRO = %s", e, exc_info=True)

    def _criar_calendario_mensal(self):
        card = Card(self)
        card.pack(fill="x", padx=SPACING["page_x"], pady=10)

        header = ctk.CTkFrame(card.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header,
            text="Calendário do Mês",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        self.lbl_mes_calendario = ctk.CTkLabel(
            header, text="", font=themed_font("body_sm"), text_color=THEME["text_muted"]
        )
        self.lbl_mes_calendario.pack(side="left", padx=(10, 0))

        nav = ctk.CTkFrame(header, fg_color=THEME["bg_alt"], corner_radius=RADIUS["button"])
        nav.pack(side="right")

        btn_prev = ctk.CTkButton(
            nav,
            text=ICONS["arrow_left"],
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=THEME["bg"],
            text_color=THEME["text_secondary"],
            corner_radius=RADIUS["sm"],
            font=themed_font("body", "bold"),
            command=lambda: self._alterar_mes_calendario(-1),
        )
        btn_prev.pack(side="left", padx=2, pady=2)

        btn_next = ctk.CTkButton(
            nav,
            text=ICONS["arrow_right"],
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=THEME["bg"],
            text_color=THEME["text_secondary"],
            corner_radius=RADIUS["sm"],
            font=themed_font("body", "bold"),
            command=lambda: self._alterar_mes_calendario(1),
        )
        btn_next.pack(side="left", padx=2, pady=2)

        self.container_calendario = ctk.CTkFrame(card.body, fg_color="transparent")
        self.container_calendario.pack(fill="x", pady=(0, 12))
        for i in range(7):
            self.container_calendario.columnconfigure(i, weight=1, uniform="cal")

    def _renderizar_calendario(self, ano: int, mes: int):
        for w in self.container_calendario.winfo_children():
            w.destroy()

        nomes_meses = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        self.lbl_mes_calendario.configure(text=f"{nomes_meses[mes - 1]} {ano}")

        dias_semana = ["D", "S", "T", "Q", "Q", "S", "S"]
        for i, nome in enumerate(dias_semana):
            ctk.CTkLabel(
                self.container_calendario,
                text=nome,
                font=themed_font("overline", "bold"),
                text_color=THEME["text_muted"],
            ).grid(row=0, column=i, padx=4, pady=(0, 4), sticky="nsew")

        primeiro_dia = datetime(ano, mes, 1)
        dias_no_mes = (
            (datetime(ano, mes % 12 + 1, 1) - timedelta(days=1)).day
            if mes < 12
            else (datetime(ano + 1, 1, 1) - timedelta(days=1)).day
        )
        inicio_semana = primeiro_dia.weekday()
        hoje_str = datetime.now().strftime("%Y-%m-%d")

        batch = WidgetBatchBuilder(parent=self.container_calendario, batch_size=20)
        idx = 0

        for i in range(inicio_semana):
            dia_ant = primeiro_dia - timedelta(days=inicio_semana - i)
            batch.add(
                lambda d=dia_ant, pos=idx: ctk.CTkLabel(
                    self.container_calendario,
                    text=str(d.day),
                    font=themed_font("body"),
                    text_color=THEME["text_disabled"],
                ).grid(row=pos // 7 + 1, column=pos % 7, padx=4, pady=4, sticky="nsew")
            )
            idx += 1

        for dia in range(1, dias_no_mes + 1):
            data_str = f"{ano}-{mes:02d}-{dia:02d}"
            agendamentos = self.mapa_agendamentos_mes.get(data_str, [])
            e_hoje = data_str == hoje_str
            batch.add(
                lambda d=dia, ds=data_str, apts=agendamentos, h_flag=e_hoje: self._criar_celula_calendario(
                    d, ds, apts, h_flag
                )
            )
            idx += 1

        restantes = (7 - (idx % 7)) % 7
        for i in range(restantes):
            dia_prox = datetime(ano, mes, dias_no_mes) + timedelta(days=i + 1)
            batch.add(
                lambda d=dia_prox, pos=idx: ctk.CTkLabel(
                    self.container_calendario,
                    text=str(d.day),
                    font=themed_font("body"),
                    text_color=THEME["text_disabled"],
                ).grid(row=pos // 7 + 1, column=pos % 7, padx=4, pady=4, sticky="nsew")
            )
            idx += 1

        batch.execute()

    def _criar_celula_calendario(
        self, dia: int, data_str: str, agendamentos: list[dict], hoje_flag: bool
    ):
        cor = THEME["primary"] if agendamentos else THEME["success"]
        frame = ctk.CTkFrame(
            self.container_calendario,
            corner_radius=RADIUS["sm"],
            border_width=1 if hoje_flag else 0,
            border_color=THEME["primary"] if hoje_flag else "transparent",
            fg_color=blend_color(cor, 0.10) if agendamentos else THEME["surface"],
        )
        frame.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")

        lbl = ctk.CTkLabel(
            frame,
            text=str(dia),
            font=themed_font("body", "bold"),
            text_color=THEME["primary"] if hoje_flag else THEME["text"],
        )
        lbl.pack(anchor="nw", padx=6, pady=(6, 0))

        if agendamentos:
            qtd = len(agendamentos)
            txt = f"{qtd} atend." if qtd > 1 else "1 atend."
            ctk.CTkLabel(frame, text=txt, font=themed_font("overline"), text_color=cor).pack(
                anchor="sw", padx=6, pady=(0, 6)
            )

        bind_clickable(frame, lambda ds=data_str: self._abrir_modal_dia(ds))

    def _processar_agendamentos_mes(self, result):
        self.mapa_agendamentos_mes = {}
        if isinstance(result, dict) and result.get("success"):
            for agt in result.get("data", []):
                data_hora = agt.get("data_hora")
                if data_hora and hasattr(data_hora, "strftime"):
                    data_str = data_hora.strftime("%Y-%m-%d")
                elif data_hora:
                    data_str = str(data_hora)[:10]
                else:
                    continue
                self.mapa_agendamentos_mes.setdefault(data_str, []).append(agt)

    def _carregar_calendario_async(self, ano: int, mes: int):
        def fetch():
            return self.servico_agenda.listar_agendamentos_mes(ano, mes)

        def on_success(result):
            if not self.winfo_exists():
                return
            self._processar_agendamentos_mes(result)
            self._renderizar_calendario(ano, mes)

        def on_error(exc):
            logger.error("AgendaFrame._carregar_calendario_async: ERRO = %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _abrir_modal_dia(self, data_str: str):
        agendamentos = self.mapa_agendamentos_mes.get(data_str, [])
        CalendarDayModal(
            self,
            data_str,
            agendamentos,
            horarios_base=self.horarios_base,
            mapa_estudantes=self.mapa_estudantes,
            on_save=self._salvar_agendamento,
            on_delete=self.remover_agendamento,
            on_success=self.refresh_all,
        )

    def _alterar_mes_calendario(self, delta: int):
        mes = self.mes_calendario + delta
        ano = self.ano_calendario
        if mes > 12:
            mes = 1
            ano += 1
        elif mes < 1:
            mes = 12
            ano -= 1
        self.ano_calendario = ano
        self.mes_calendario = mes
        self._carregar_calendario_async(ano, mes)

    def _renderizar_grid(self, container, mapa_dados):
        for child in container.winfo_children():
            child.destroy()

        horarios = self.horarios_base or []
        if not horarios:
            EmptyState(
                container,
                icon=ICONS["calendar"],
                title="Nenhum horário configurado",
                subtitle="Adicione horários na gestão de grade",
            ).pack(pady=20)
            return

        batch = WidgetBatchBuilder(parent=container, batch_size=20)
        for idx, hora in enumerate(horarios):
            info = mapa_dados.get(hora)
            batch.add(
                lambda c=container, h=hora, i=info, pos=idx: ScheduleCell(
                    c, h, i, on_open=self._abrir_modal_agendamento
                ).grid(row=pos // 4, column=pos % 4, padx=6, pady=6, sticky="nsew")
            )
        batch.execute()

    def _criar_cabecalho(self):
        self.lbl_data_display = ctk.CTkLabel(
            self, text="", font=themed_font("h2", "bold"), text_color=THEME["text"]
        )
        self.lbl_data_display.pack(padx=SPACING["page_x"], pady=(SPACING["page_y"], 0), anchor="w")

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=SPACING["page_x"], pady=(6, 16))

        nav = ctk.CTkFrame(
            toolbar, fg_color=AGENDA_COLORS["nav_bg"], corner_radius=RADIUS["button"]
        )
        nav.pack(side="left")

        self._botao_navegacao(nav, ICONS["arrow_left"], -1)
        self._label_data_nav(nav)
        self._botao_navegacao(nav, ICONS["arrow_right"], 1)

        right = ctk.CTkFrame(toolbar, fg_color="transparent")
        right.pack(side="right")
        PrimaryButton(
            right,
            text="Gerenciar Horários",
            command=self._abrir_modal_gestao,
            width=170,
            icon=ICONS["settings"],
        ).pack()

    def _botao_navegacao(self, parent, texto, delta):
        ctk.CTkButton(
            parent,
            text=texto,
            width=34,
            height=34,
            fg_color="transparent",
            hover_color=THEME["bg"],
            text_color=THEME["text_secondary"],
            corner_radius=RADIUS["sm"],
            font=themed_font("body", "bold"),
            command=lambda: self.alterar_data(delta),
        ).pack(side="left", padx=2, pady=2)

    def _label_data_nav(self, parent):
        self.lbl_data_display_sub = ctk.CTkLabel(
            parent, text="", font=themed_font("body"), text_color=THEME["text_secondary"], width=200
        )
        self.lbl_data_display_sub.pack(side="left", padx=8)
        self._atualizar_label_data()

    def _atualizar_label_data(self):
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        dia_nome = dias_semana[self.data_selecionada.weekday()]
        texto = self.data_selecionada.strftime(f"{dia_nome}, %d/%m/%Y")
        self.lbl_data_display.configure(text=texto)
        self.lbl_data_display_sub.configure(text=texto)

    def _atualizar_subtitulo_proxima_semana(self):
        proxima = self.data_selecionada + timedelta(days=7)
        dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        dia_nome = dias_semana[proxima.weekday()]
        self.lbl_subtitulo_semana.configure(text=proxima.strftime(f"{dia_nome}, %d/%m/%Y"))

    def alterar_data(self, dias: int):
        self.data_selecionada += timedelta(days=dias)
        self.refresh_all()

    def _criar_container_agenda_dia(self):
        card = Card(self, title=f"{ICONS['calendar']} Agenda do Dia", status="Em andamento")
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
            header, text="Próxima Semana", font=themed_font("h4", "bold"), text_color=THEME["text"]
        ).pack(side="left")

        self.lbl_subtitulo_semana = ctk.CTkLabel(
            header, text="", font=themed_font("body_sm"), text_color=THEME["text_muted"]
        )
        self.lbl_subtitulo_semana.pack(side="left", padx=(10, 0))

        self.container_semana = ctk.CTkFrame(card.body, fg_color="transparent")
        self.container_semana.pack(fill="x", pady=(0, 12))
        for i in range(4):
            self.container_semana.columnconfigure(i, weight=1, uniform="grid")

    def _abrir_modal_agendamento(self, hora: str, info: dict | None = None):
        modal = AppointmentModal(
            self,
            hora,
            info,
            horarios_base=self.horarios_base,
            mapa_estudantes=self.mapa_estudantes,
            on_save=self._salvar_agendamento,
            on_delete=self.remover_agendamento,
            on_success=self.refresh_all,
        )
        modal._get_data_selecionada = lambda: self.data_selecionada.strftime("%Y-%m-%d")

    def _abrir_modal_gestao(self):
        GradeManagementModal(
            self, self.horarios_base, self.servico_agenda, on_refresh=self.refresh_all
        )

    def _salvar_agendamento(self, id_antigo: int | None, dados: dict):
        return (
            self.servico_agenda.atualizar_agendamento(id_antigo, dados)
            if id_antigo
            else self.servico_agenda.criar_agendamento(dados)
        )

    def remover_agendamento(self, id_agendamento: int):
        return self.servico_agenda.deletar_agendamento(id_agendamento)

    def _show_error(self, message: str, title: str = "Não foi possível concluir") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _show_success(self, message: str, duration: int = 3000) -> None:
        try:
            if hasattr(self, "_toast") and self._toast and self._toast.winfo_exists():
                self._toast.destroy()
            self._toast = Toast(
                self.winfo_toplevel(), message=message, status="success", duration=duration
            )
        except Exception:
            pass

    def _confirmar(self, mensagem: str) -> bool:
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)
        _centralizar_janela(modal, 420, 200)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        resultado = {"ok": False}
        ctk.CTkLabel(
            modal,
            text=mensagem,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
            wraplength=360,
            justify="center",
        ).pack(pady=(24, 16))

        botoes = ctk.CTkFrame(modal, fg_color="transparent")
        botoes.pack(pady=(0, 20))
        ctk.CTkButton(
            botoes,
            text="Cancelar",
            width=110,
            height=36,
            fg_color=THEME["bg_alt"],
            hover_color=THEME["border"],
            text_color=THEME["text"],
            command=modal.destroy,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            botoes,
            text="Confirmar",
            width=110,
            height=36,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_on_primary"],
            command=lambda: self._confirmar_callback(modal, resultado),
        ).pack(side="right")

        modal.wait_window(modal)
        return resultado.get("ok", False)

    def _confirmar_callback(self, modal: ctk.CTkToplevel, resultado: dict):
        resultado["ok"] = True
        modal.destroy()
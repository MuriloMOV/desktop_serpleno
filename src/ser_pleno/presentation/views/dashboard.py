import logging
import customtkinter as ctk
from ser_pleno.presentation.components.ui_components import (
    Card, EmptyState, PrimaryButton, Divider, KPICard, bind_clickable, BaseModal
)
from ser_pleno.presentation.components.icons import IconLabel, ICONS
from ser_pleno.utils.async_runner import AsyncRunner

from ser_pleno.application.controllers.dashboard import DashboardController
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, themed_font, FONT_FAMILY
from ser_pleno.ui.theme_extensions import spacing

logger = logging.getLogger(__name__)


class _AgendaRow(ctk.CTkFrame):
    """Linha de item de agenda com estilo refinado."""
    def __init__(self, parent, appt: dict):
        super().__init__(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        self._build(appt)

    def _build(self, appt):
        # Barra colorida lateral
        ctk.CTkFrame(
            self, width=spacing("xs"), corner_radius=2, fg_color=THEME["primary"],
        ).pack(side="left", fill="y", padx=(spacing("sm"), spacing("md")), pady=spacing("md"))

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", pady=spacing("md"), fill="x", expand=True)

        ctk.CTkLabel(
            info, text=appt.get("student_name", "?"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=appt.get("curso", ""),
            font=themed_font("caption"),
            text_color=THEME["text_secondary"], anchor="w",
        ).pack(anchor="w", pady=(spacing("xs"), 0))

        # Hora
        time_frame = ctk.CTkFrame(
            self, fg_color=THEME["primary_soft"],
            corner_radius=RADIUS["button"],
        )
        time_frame.pack(side="right", padx=spacing("md"), pady=spacing("md"))
        ctk.CTkLabel(
            time_frame,
            text=f"{ICONS['chart']}  {appt.get('time', '')}",
            font=themed_font("body", "bold"),
            text_color=THEME["primary"],
        ).pack(padx=spacing("md"), pady=spacing("sm"))


class _AlertaRow(ctk.CTkFrame):
    """Linha de estudante em alerta."""
    _PRIORITY_COLOR = {0: THEME["warning"], 1: "#F97316", 2: THEME["danger"], 3: THEME["danger"]}
    _PRIORITY_LABEL = {0: "Moderado", 1: "Alto", 2: "Crítico", 3: "Crítico"}
    _PRIORITY_ICON  = {0: ICONS["bolt"], 1: ICONS["bolt"], 2: ICONS["priority_high"], 3: ICONS["priority_high"]}

    def __init__(self, parent, student: dict):
        super().__init__(
            parent,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        self._build(student)

    def _build(self, student):
        priority = student.get("priority_level", 0)
        bar_color = self._PRIORITY_COLOR.get(priority, THEME["warning"])

        ctk.CTkFrame(
            self, width=spacing("xs"), corner_radius=2, fg_color=bar_color,
        ).pack(side="left", fill="y", padx=(spacing("sm"), spacing("md")), pady=spacing("md"))

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", pady=spacing("md"), fill="x", expand=True)

        ctk.CTkLabel(
            info, text=student.get("name", "?"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=student.get("attention_reason", ""),
            font=themed_font("caption"),
            text_color=THEME["danger"], anchor="w",
        ).pack(anchor="w", pady=(spacing("xs"), 0))

        # Chip de prioridade
        chip = ctk.CTkFrame(
            self, fg_color=THEME["danger_soft"], corner_radius=RADIUS["button"],
        )
        chip.pack(side="right", padx=spacing("md"), pady=spacing("md"))
        ctk.CTkLabel(
            chip,
            text=f"{self._PRIORITY_ICON[priority]}  {self._PRIORITY_LABEL.get(priority, '')}",
            font=themed_font("caption", "bold"),
            text_color=THEME["danger"],
        ).pack(padx=spacing("sm"), pady=spacing("xs"))


class _BemEstarBar(ctk.CTkFrame):
    """Barra de progresso de dimensão de bem-estar."""
    def __init__(self, parent, nome: str, valor: float, color: str, soft: str):
        super().__init__(parent, fg_color="transparent")
        self._build(nome, max(0.0, min(1.0, valor)), color, soft)

    def _build(self, nome, valor, color, soft):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkLabel(
            row, text=nome,
            font=themed_font("body"),
            text_color=THEME["text"], anchor="w",
        ).pack(side="left")

        pct_frame = ctk.CTkFrame(row, fg_color=soft, corner_radius=RADIUS["pill"])
        pct_frame.pack(side="right")
        ctk.CTkLabel(
            pct_frame,
            text=f"{int(valor * 100)}%",
            font=themed_font("body", "bold"),
            text_color=color,
        ).pack(padx=spacing("sm"), pady=spacing("xs"))

        bar_bg = ctk.CTkFrame(self, fg_color=THEME["chart_grid"], corner_radius=RADIUS["pill"], height=7)
        bar_bg.pack(fill="x", pady=(6, 0))
        bar_bg.pack_propagate(False)

        fill_w = max(1, int(valor * 1000))  # proporcional em 1000 unidades
        fill_frame = ctk.CTkFrame(
            bar_bg, fg_color=color, corner_radius=RADIUS["pill"], height=7,
            width=fill_w,
        )
        fill_frame.pack(side="left", fill="y")


class NotificationPanel(BaseModal):
    """Modal de notificações."""
    def __init__(self, parent, titulo: str, notificacoes: list, tipo: str,
                 on_mark_read=None, on_mark_all_read=None):
        super().__init__(parent, title=titulo, width=520, height=480)
        self._parent_window = parent.winfo_toplevel()
        self.titulo = titulo
        self.notificacoes = notificacoes
        self.tipo = tipo
        self.on_mark_read = on_mark_read
        self.on_mark_all_read = on_mark_all_read
        self._build()

    def _build(self):
        is_ajuda = self.tipo == "ajuda"
        accent   = THEME["primary"] if is_ajuda else THEME["danger"]
        soft     = THEME["primary_soft"] if is_ajuda else THEME["danger_soft"]
        icon_txt = ICONS["user"] if is_ajuda else ICONS["notification"]

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color=soft, corner_radius=0)
        header.pack(fill="x")

        hinner = ctk.CTkFrame(header, fg_color="transparent")
        hinner.pack(fill="x", padx=SPACING["page_x"], pady=14)

        ctk.CTkLabel(
            hinner, text=f"{icon_txt}  {self.title()}",
            font=themed_font("h4", "bold"),
            text_color=accent,
        ).pack(side="left")

        PrimaryButton(
            hinner, text="Marcar todas como lidas",
            command=self._mark_all_read,
            height=30, width=180,
            text_color="white",
        ).pack(side="right")

        # Lista
        lst = ctk.CTkScrollableFrame(self, fg_color="transparent")
        lst.pack(fill="both", expand=True, padx=spacing("xxl"), pady=spacing("lg"))

        if not self.notificacoes:
            EmptyState(
                lst, icon=ICONS["empty"], title="Sem notificações",
                subtitle=f"Nenhuma notificação de {self.tipo} no momento",
            ).pack(pady=spacing("xl"))
        else:
            for notif in self.notificacoes:
                self._create_item(lst, notif, accent, soft, icon_txt)

    def _create_item(self, parent, notif, accent, soft, icon_txt):
        row = ctk.CTkFrame(
            parent, fg_color=soft,
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"))
        row.pack_propagate(True)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("md"), pady=spacing("sm"))
        inner.grid_columnconfigure(1, weight=1)

        # Ícone
        icon_bg = ctk.CTkFrame(
            inner, width=34, height=34, corner_radius=RADIUS["button"], fg_color=accent,
        )
        icon_bg.grid(row=0, column=0, rowspan=2, padx=(0, spacing("md")), sticky="n", pady=(spacing("xs"), 0))
        icon_bg.grid_propagate(False)
        ctk.CTkLabel(
            icon_bg, text=icon_txt,
            font=themed_font("body"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text=notif.get("titulo", ""),
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner, text=notif.get("descricao", ""),
            font=themed_font("caption"),
            text_color=THEME["text_secondary"], anchor="w",
        ).grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(
            inner, text=notif.get("data", ""),
            font=themed_font("caption"),
            text_color=THEME["text_muted"], anchor="e",
        ).grid(row=0, column=2, sticky="ne", padx=(spacing("sm"), 0))

        bind_clickable(
            row,
            lambda nid=notif["id"], t=self.tipo: self._on_click(nid, t),
        )

    def _on_click(self, notif_id, tipo):
        if self.on_mark_read:
            self.on_mark_read(notif_id, tipo)
        self.destroy()

    def _mark_all_read(self):
        if self.on_mark_all_read:
            self.on_mark_all_read(self.tipo)
        self.destroy()


class ProfileModal(BaseModal):
    """Modal de perfil do usuário."""
    def __init__(self, parent, user_data: dict, on_edit=None):
        super().__init__(parent, title="Meu Perfil", width=440, height=380)
        self._parent_window = parent.winfo_toplevel()
        self.user_data = user_data or {}
        self.on_edit = on_edit
        self._build()

    def _build(self):
        # Banner de topo
        banner = ctk.CTkFrame(self, fg_color=THEME["primary_soft"], corner_radius=0, height=80)

        initials = (
            (self.user_data.get("first_name", "") or "")[0:1] +
            (self.user_data.get("last_name",  "") or "")[0:1]
        ).upper() or self.user_data.get("username", "?")[:2].upper()

        av = ctk.CTkFrame(
            self, width=64, height=64,
            corner_radius=32, fg_color=THEME["primary"],
        )
        av.place(x=28, y=48)
        av.pack_propagate(False)
        ctk.CTkLabel(
            av, text=initials,
            font=themed_font("h3", "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(spacing("xl"), spacing("md")))

        nome = (
            f"{self.user_data.get('first_name', '')} "
            f"{self.user_data.get('last_name', '')}"
        ).strip() or self.user_data.get("username", "Usuário")

        ctk.CTkLabel(
            body, text=nome,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            body, text=self.user_data.get("email", ""),
            font=themed_font("body"),
            text_color=THEME["text_secondary"], anchor="w",
        ).pack(anchor="w", pady=(spacing("xs"), spacing("sm")))

        # Chip de função
        chip = ctk.CTkFrame(body, fg_color=THEME["primary_soft"], corner_radius=RADIUS["button"])
        chip.pack(anchor="w")
        ctk.CTkLabel(
            chip, text="Analista Escolar",
            font=themed_font("body", "bold"),
            text_color=THEME["primary"],
        ).pack(padx=spacing("sm"), pady=spacing("xs"))

        Divider(body).pack(fill="x", pady=spacing("md"))

        # Rows de info
        for label, value in [
            ("Usuário",  self.user_data.get("username", "")),
            ("Função",   "Analista Escolar"),
            ("Módulos",  "Dashboard, Estudantes, Agenda, Bem-Estar"),
        ]:
            self._row(body, label, value)

        PrimaryButton(
            self, text="Editar Perfil",
            command=lambda: self.on_edit() if self.on_edit else None,
            height=38, corner_radius=RADIUS["button"], width=160,
        ).pack(pady=(spacing("xs"), spacing("xl")))

    def _row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=spacing("xs"))

        ctk.CTkLabel(
            row, text=label, width=90,
            font=themed_font("body"),
            text_color=THEME["text_secondary"], anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            row, text=value,
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(side="left")


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Frame principal —“ DashboardFrame
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(
            parent,
            fg_color=THEME["bg"],
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.controller = controller
        self.controller_dashboard = DashboardController()

        self._criar_toolbar_acoes()
        self._criar_kpi_container()
        self._criar_grid_principal()
        self._carregar_dados()

    # ——————————————————————————————————————————————————————————————————————
    #  Dados
    # ——————————————————————————————————————————————————————————————————————
    def _carregar_dados(self):
        self._mostrar_skeletons()

        def fetch():
            data = self.controller_dashboard.carregar_kpis()
            return data

        def on_success(data):
            self._atualizar_dashboard(data)

        def on_error(exc):
            import tkinter.messagebox as mb
            mb.showerror("Erro", f"Não foi possível carregar o dashboard.\n{exc}")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _atualizar_dashboard(self, data):
        self._render_kpis(data)
        self._atualizar_secao_agenda(data)
        self._atualizar_secao_alertas(data)
        self._atualizar_secao_bem_estar(data)
        self._atualizar_secao_humor(data)
        # Atualiza badges de forma não-bloqueante
        self.after(0, self._atualizar_badge_notificacoes)

    # ——————————————————————————————————————————————————————————————————————
    #  Toolbar de ações
    # ——————————————————————————————————————————————————————————————————————
    def _criar_toolbar_acoes(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 4))

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        # Ícone ajuda
        help_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=RADIUS["button"],
                               fg_color=THEME["primary_soft"])
        help_f.pack(side="left", padx=spacing("xs"))
        help_f.pack_propagate(False)
        bind_clickable(help_f, self._abrir_notificacoes_ajuda)
        IconLabel(
            help_f, icon=ICONS["help"], size=20,
            fg_color="transparent", text_color=THEME["primary"],
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.help_badge = self._criar_badge(right)
        self.help_badge_anchor = help_f

        # Ícone alertas
        alert_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=RADIUS["button"],
                                fg_color=THEME["danger_soft"])
        alert_f.pack(side="left", padx=spacing("xs"))
        alert_f.pack_propagate(False)
        bind_clickable(alert_f, self._abrir_notificacoes_alertas)
        IconLabel(
            alert_f, icon=ICONS["notification"], size=20,
            fg_color="transparent", text_color=THEME["danger"],
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.alert_badge = self._criar_badge(right)
        self.alert_badge_anchor = alert_f

        # Avatar
        name = ""
        if self.controller.usuario_logado:
            name = self.controller.usuario_logado.get("username", "?")[:2].upper()
        av_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=RADIUS["button"],
                             fg_color=THEME["primary"])
        av_f.pack(side="left", padx=(spacing("md"), 0))
        av_f.pack_propagate(False)
        bind_clickable(av_f, self._abrir_perfil)
        ctk.CTkLabel(
            av_f, text=name,
            font=themed_font("body", "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _criar_badge(self, parent) -> ctk.CTkFrame:
        badge = ctk.CTkFrame(
            parent, corner_radius=9, fg_color=THEME["danger"],
        )
        ctk.CTkLabel(
            badge, text="0",
            font=themed_font("caption", "bold"),
            text_color="white",
        ).pack(padx=5, pady=1)
        return badge

    # ——————————————————————————————————————————————————————————————————————
    #  KPI row
    # ——————————————————————————————————————————————————————————————————————
    def _criar_kpi_container(self):
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))
        self._kpi_cards = []

    def _mostrar_skeletons(self):
        self._limpar(self.kpi_frame)
        self._kpi_cards = []
        for i in range(5):
            self.kpi_frame.grid_columnconfigure(i, weight=1)
            EmptyState(
                self.kpi_frame, icon="", title="",
            ).grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2)

    def _render_kpis(self, data):
        media_humor = data.get("media_humor")
        humor_emoji = self._humor_emoji(media_humor)

        kpis = [
            ("Atendimentos Hoje", str(data.get("appointments_today", 0)),
             ICONS["users"], THEME["kpi_blue"],   THEME["kpi_blue_soft"],  "Atendimentos marcados"),
            ("Vagas Disponíveis", str(data.get("available_slots", 0)),
             ICONS["calendar"], THEME["kpi_green"],  THEME["kpi_green_soft"], "Horários livres"),
            ("Alertas Ativos",    str(data.get("alerts", 0)),
             ICONS["bell"], THEME["kpi_red"],    THEME["kpi_red_soft"],   "Requerem atenção"),
            ("Total de Estudantes", str(data.get("total_students", 0)),
             ICONS["group"], THEME["kpi_violet"], THEME["kpi_violet_soft"],"Alunos cadastrados"),
            ("Humor Médio",
             f"{media_humor:.1f}/5" if media_humor else "—",
             humor_emoji, THEME["kpi_amber"], THEME["kpi_amber_soft"], "Média dos últimos 30 dias"),
        ]

        if not getattr(self, "_kpi_cards", None):
            self._kpi_cards = []
            for i, (title, value, icon, accent, soft, sub) in enumerate(kpis):
                self.kpi_frame.grid_columnconfigure(i, weight=1)
                card = KPICard(
                    self.kpi_frame, title=title, value=value, icon=icon,
                     accent=accent, trend="", unit="", size="wide",
                )
                card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2)
                self._kpi_cards.append(card)
        else:
            for card, (title, value, icon, accent, soft, sub) in zip(self._kpi_cards, kpis):
                card.set_value(value)

    # ——————————————————————————————————————————————————————————————————————
    #  Grid principal
    # ——————————————————————————————————————————————————————————————————————
    def _criar_grid_principal(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["section_gap"])

        self.left_col = ctk.CTkFrame(grid, fg_color="transparent")
        self.left_col.pack(side="left", fill="both", expand=True, padx=(0, SPACING["grid_gap"] // 2))

        self.right_col = ctk.CTkFrame(grid, fg_color="transparent")
        self.right_col.pack(side="right", fill="both", padx=(SPACING["grid_gap"] // 2, 0))

        # Card do gráfico (na esquerda)
        self._criar_card_chart()

    def _criar_card_chart(self):
        self.chart_card = Card(self.left_col, title=f"{ICONS['chart']}  Humor dos Estudantes — últimos 30 dias")
        self.chart_card.pack(fill="x", pady=(0, spacing("md")))

        self.canvas = ctk.CTkCanvas(
            self.chart_card.body,
            bg=THEME["surface"],
            height=230,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=spacing("xs"), pady=(spacing("xs"), spacing("md")))
        self._chart_after_id = None
        self._pending_humor_history = None
        self.chart_card.body.bind("<Configure>", self._schedule_draw_chart)

    def _schedule_draw_chart(self, event=None):
        if self._chart_after_id:
            self.after_cancel(self._chart_after_id)
        self._chart_after_id = self.after(80, lambda: self._draw_chart(self._pending_humor_history))

    # ——————————————————————————————————————————————————————————————————————
    #  Seções
    # ——————————————————————————————————————————————————————————————————————
    def _atualizar_secao_agenda(self, data):
        card = getattr(self, "_agenda_card", None)
        if card is None or not card.winfo_exists():
            card = Card(
                self.left_col, title=f"{ICONS['calendar']}  Próximos Atendimentos",
            )
            card.pack(fill="x", pady=(0, 14))
            self._agenda_card = card
        else:
            self._limpar(card.body)

        appointments = data.get("upcoming_appointments", [])
        if appointments:
            for appt in appointments:
                _AgendaRow(card.body, appt).pack(fill="x", pady=3)
        else:
            EmptyState(
                card.body, icon=ICONS["calendar"],
                title="Nenhum atendimento próximo",
                subtitle="Não há agendamentos futuros",
            ).pack(pady=10)

    def _atualizar_secao_alertas(self, data):
        card = getattr(self, "_alert_card", None)
        if card is None or not card.winfo_exists():
            card = Card(
                self.right_col, title=f"{ICONS['danger']}  Estudantes em Alerta",
            )
            card.pack(fill="x", pady=(0, 14))
            self._alert_card = card
        else:
            self._limpar(card.body)

        students = data.get("attention_students", [])
        if students:
            for s in students:
                _AlertaRow(card.body, s).pack(fill="x", pady=3)
        else:
            EmptyState(
                card.body, icon=ICONS["cross"],
                title="Tudo sob controle",
                subtitle="Nenhum estudante em alerta",
            ).pack(pady=10)

    def _atualizar_secao_bem_estar(self, data):
        card = getattr(self, "_bem_estar_card", None)
        if card is None or not card.winfo_exists():
            card = Card(self.left_col, title=f"{ICONS['heart']}  Bem-Estar por Dimensão")
            card.pack(fill="x", pady=(0, 14))
            self._bem_estar_card = card
        else:
            self._limpar(card.body)

        be = data.get("bem_estar_dimensions", {})
        dims = [
            (f"{ICONS['chart']} Acadêmico", be.get("academico", 0) / 5, THEME["primary"], THEME["primary_soft"]),
            (f"{ICONS['chat']}  Emocional",  be.get("emocional", 0) / 5, "#EC4899", "#FCE7F3"),
            (f"{ICONS['group']}  Social",    be.get("social",    0) / 5, THEME["success"], THEME["success_soft"]),
        ]
        for nome, val, color, soft in dims:
            _BemEstarBar(card.body, nome, val, color, soft).pack(
                fill="x", padx=spacing("xs"), pady=spacing("md")
            )

    def _atualizar_secao_humor(self, data):
        humor_history = data.get("humor_history", [])
        self._pending_humor_history = humor_history if humor_history else None
        self._schedule_draw_chart()

    # ——————————————————————————————————————————————————————————————————————
    #  Gráfico canvas
    # ——————————————————————————————————————————————————————————————————————
    def _draw_chart(self, humor_history=None):
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 80 or ch < 80:
            return

        if not humor_history:
            pts = []
            dates = []
        else:
            pts = [item.get("media_humor", 0) or 0 for item in humor_history]
            dates = [item.get("data") or item.get("date") or "" for item in humor_history]

        if len(pts) < 2:
            if len(pts) == 1:
                pts = [pts[0], pts[0]]
                dates = [dates[0], dates[0]] if dates else dates
            else:
                pts = []
                dates = []

        if not pts:
            for child in self.chart_card.body.winfo_children():
                if child.winfo_exists():
                    child.destroy()
            EmptyState(
                self.chart_card.body,
                icon=ICONS["chart"],
                title="Sem dados de humor",
                subtitle="Os registros aparecerão aqui quando houver entradas",
            ).pack(expand=True, fill="both", padx=24, pady=24)
            return

        mx, my = 44, 24
        cw2 = cw - 2 * mx
        ch2 = ch - 2 * my

        # Fundo
        self.canvas.create_rectangle(
            mx, my, cw - mx, ch - my,
            fill=THEME["surface"], outline=THEME["chart_grid"], width=1,
        )

        # Grades horizontais e labels Y
        for i in range(6):
            val = 1 + i
            gy  = (ch - my) - (i * ch2 / 5)
            self.canvas.create_line(
                mx, gy, cw - mx, gy,
                fill=THEME["chart_grid"], dash=(3, 5),
            )
            self.canvas.create_text(
                mx - 6, gy, text=str(val),
                font=(FONT_FAMILY, 8), fill=THEME["text_muted"], anchor="e",
            )

        # Coordenadas dos pontos
        n = len(pts)
        coords = [
            (mx + i * cw2 / (n - 1), (ch - my) - ((v - 1) * ch2 / 4))
            for i, v in enumerate(pts)
        ]

        # Área preenchida (gradiente simulado com polygon)
        poly_pts = []
        for x, y in coords:
            poly_pts += [x, y]
        poly_pts += [coords[-1][0], ch - my, coords[0][0], ch - my]
        self.canvas.create_polygon(poly_pts, fill=THEME["chart_fill"], outline="")

        # Linha principal
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=THEME["chart_line"], width=2,
                capstyle="round", joinstyle="round",
            )

        # Pontos
        for i, (x, y) in enumerate(coords):
            v = pts[i]
            dot = (THEME["dot_bad"] if v < 2.5 else
                   THEME["dot_mid"] if v < 3.5 else THEME["dot_good"])
            self.canvas.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill=dot, outline="#FFFFFF", width=2,
            )

        # Labels X (datas)
        step = max(1, n // 7)
        for i, (x, _) in enumerate(coords):
            if i % step == 0:
                self.canvas.create_text(
                    x, ch - 8, text=dates[i],
                    font=(FONT_FAMILY, 8), fill=THEME["text_muted"],
                )

        # Legenda no canto
        legend = [("● Bom", THEME["dot_good"]), ("● Atenção", THEME["dot_mid"]), ("● Baixo", THEME["dot_bad"])]
        lx = cw - mx - 4
        for j, (lbl, lcolor) in enumerate(reversed(legend)):
            self.canvas.create_text(
                lx, my + 12 + j * 14, text=lbl,
                font=(FONT_FAMILY, 8), fill=lcolor, anchor="e",
            )

    # ——————————————————————————————————————————————————————————————————————
    #  Notificações e badges
    # ——————————————————————————————————————————————————————————————————————
    def _abrir_notificacoes_ajuda(self):
        notifs = self.controller_dashboard.obter_notificacoes_ajuda()
        NotificationPanel(
            self, "Notificações de Ajuda", notifs, "ajuda",
            on_mark_read=self._marcar_lida,
            on_mark_all_read=self._marcar_todas_lidas,
        )

    def _abrir_notificacoes_alertas(self):
        notifs = self.controller_dashboard.obter_notificacoes_alertas()
        NotificationPanel(
            self, "Notificações de Alerta", notifs, "alerta",
            on_mark_read=self._marcar_lida,
            on_mark_all_read=self._marcar_todas_lidas,
        )

    def _abrir_perfil(self):
        ProfileModal(self, self.controller.usuario_logado, on_edit=self._editar_perfil)

    def _editar_perfil(self):
        user = getattr(self.controller, "usuario_logado", {}) or {}
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Perfil")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)
        w, h = 480, 420
        sx = modal.winfo_screenwidth()  // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"])
        card.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(card, text="Editar Perfil",
                     font=themed_font("h2", "bold"),
                     text_color=THEME["text"]).pack(anchor="w", pady=(0, 16))

        entry_nome = ctk.CTkEntry(card, placeholder_text="Nome completo")
        entry_nome.insert(0, user.get("first_name", ""))
        entry_nome.pack(fill="x", pady=(0, 10))

        entry_email = ctk.CTkEntry(card, placeholder_text="Email")
        entry_email.insert(0, user.get("email", ""))
        entry_email.pack(fill="x", pady=(0, 10))

        entry_senha = ctk.CTkEntry(card, placeholder_text="Nova senha (opcional)", show="*")
        entry_senha.pack(fill="x", pady=(0, 10))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 0))

        def _salvar():
            nome = entry_nome.get().strip()
            email = entry_email.get().strip()
            senha = entry_senha.get().strip()
            if not nome or not email:
                messagebox.showerror("Erro", "Nome e email são obrigatórios.", parent=modal)
                return
            try:
                user["first_name"] = nome
                user["email"] = email
                if senha:
                    from ser_pleno.application.controllers.autenticacao import AutenticacaoController
                    auth_controller = AutenticacaoController()
                    res = auth_controller.alterar_senha(user.get("password", ""), senha)
                    if not res.get("success"):
                        messagebox.showerror("Erro", res.get("message", "Falha ao alterar senha."), parent=modal)
                        return
                messagebox.showinfo("Sucesso", "Perfil atualizado.", parent=modal)
                modal.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao atualizar perfil.\n{e}", parent=modal)

        ctk.CTkButton(footer, text="Cancelar", command=modal.destroy,
                      width=110, height=36, corner_radius=10,
                      fg_color=THEME["divider"], hover_color=THEME["border"],
                      text_color=THEME["text_muted"]).pack(side="left", padx=(0, 8))
        ctk.CTkButton(footer, text="Salvar",
                      command=_salvar, width=140, height=36, corner_radius=10,
                      fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                      text_color="white", font=themed_font("button", "bold")).pack(side="right")

    def _atualizar_badge_notificacoes(self):
        if not hasattr(self, "help_badge") or not hasattr(self, "alert_badge"):
            return
        ajuda   = self.controller_dashboard.obter_notificacoes_ajuda()
        alertas = self.controller_dashboard.obter_notificacoes_alertas()
        n_ajuda   = sum(1 for n in ajuda   if not n.get("lida", True))
        n_alertas = sum(1 for n in alertas if not n.get("lida", True))
        self._set_badge(self.help_badge,  n_ajuda,  getattr(self, "help_badge_anchor", None))
        self._set_badge(self.alert_badge, n_alertas, getattr(self, "alert_badge_anchor", None))

    def _set_badge(self, badge: ctk.CTkFrame, count: int, anchor=None):
        lbl = next((c for c in badge.winfo_children()
                    if isinstance(c, ctk.CTkLabel)), None)
        if lbl:
            lbl.configure(text=str(count) if count else "")
        if count > 0 and anchor and anchor.winfo_exists():
            self.update_idletasks()
            anchor_x = anchor.winfo_x()
            anchor_y = anchor.winfo_y()
            badge.place(x=anchor_x + anchor.winfo_width() + 3, y=anchor_y - 3)
            badge.lift()
        else:
            badge.place_forget()

    def _marcar_lida(self, notif_id, tipo):
        self.controller_dashboard.marcar_notificacao_como_lida(notif_id, tipo)
        self._atualizar_badge_notificacoes()

    def _marcar_todas_lidas(self, tipo):
        try:
            notifs = (self.controller_dashboard.obter_notificacoes_ajuda()
                      if tipo == "ajuda"
                      else self.controller_dashboard.obter_notificacoes_alertas())
            for n in notifs:
                self.controller_dashboard.marcar_notificacao_como_lida(n["id"], tipo)
            self._atualizar_badge_notificacoes()
        except Exception as e:
            logger.error("Erro ao marcar todas como lidas: %s", e)
            messagebox.showerror("Erro", f"Erro ao marcar notificações como lidas:\n{e}", parent=self.winfo_toplevel())

    # ——————————————————————————————————————————————————————————————————————
    #  Utilitários
    # ——————————————————————————————————————————————————————————————————————
    @staticmethod
    def _limpar(widget):
        for child in widget.winfo_children():
            child.destroy()

    @staticmethod
    def _humor_emoji(media) -> str:
        if media is None: return ICONS["mood_bad"]
        if media < 2.0:   return ICONS["mood_bad"]
        if media < 3.0:   return ICONS["mood_bad"]
        if media < 4.0:   return ICONS["mood_good"]
        return ICONS["mood_good"]

    # Alias legado
    @staticmethod
    def get_humor_emoji(media):
        return DashboardFrame._humor_emoji(media)


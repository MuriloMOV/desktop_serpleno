from components.ui_components import (
    Card, EmptyState, PrimaryButton, Divider, KPICard, bind_clickable
)
from utils.async_runner import AsyncRunner

import customtkinter as ctk
from ui_theme import THEME, SPACING, RADIUS, themed_font, FONT_FAMILY
from ui_theme_extensions import extend_theme
from services.dashboard import ServicoDashboard

DASH_TOKENS = extend_theme(THEME, {
    "kpi_size": "wide",
})


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
            self, width=3, corner_radius=2, fg_color=THEME["primary"],
        ).pack(side="left", fill="y", padx=(10, 12), pady=10)

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", pady=12, fill="x", expand=True)

        ctk.CTkLabel(
            info, text=appt.get("student_name", "?"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=appt.get("curso", ""),
            font=themed_font("caption"),
            text_color=THEME["text_secondary"], anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Hora
        time_frame = ctk.CTkFrame(
            self, fg_color=THEME["primary_soft"],
            corner_radius=RADIUS["button"],
        )
        time_frame.pack(side="right", padx=14, pady=12)
        ctk.CTkLabel(
            time_frame,
            text=f"🕒  {appt.get('time', '')}",
            font=themed_font("body", "bold"),
            text_color=THEME["primary"],
        ).pack(padx=10, pady=5)


class _AlertaRow(ctk.CTkFrame):
    """Linha de estudante em alerta."""
    _PRIORITY_COLOR = {0: THEME["warning"], 1: "#F97316", 2: THEME["danger"], 3: THEME["danger"]}
    _PRIORITY_LABEL = {0: "Moderado", 1: "Alto", 2: "Crítico", 3: "Crítico"}
    _PRIORITY_ICON  = {0: "🟡", 1: "🟠", 2: "🔴", 3: "🔴"}

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
            self, width=3, corner_radius=2, fg_color=bar_color,
        ).pack(side="left", fill="y", padx=(10, 12), pady=10)

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", pady=12, fill="x", expand=True)

        ctk.CTkLabel(
            info, text=student.get("name", "?"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=student.get("attention_reason", ""),
            font=themed_font("caption"),
            text_color=THEME["danger"], anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Chip de prioridade
        chip = ctk.CTkFrame(
            self, fg_color=THEME["danger_soft"], corner_radius=RADIUS["button"],
        )
        chip.pack(side="right", padx=14, pady=12)
        ctk.CTkLabel(
            chip,
            text=f"{self._PRIORITY_ICON[priority]}  {self._PRIORITY_LABEL.get(priority, '')}",
            font=themed_font("caption", "bold"),
            text_color=THEME["danger"],
        ).pack(padx=8, pady=4)


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
        ).pack(padx=8, pady=2)

        bar_bg = ctk.CTkFrame(self, fg_color=THEME["chart_grid"], corner_radius=RADIUS["pill"], height=7)
        bar_bg.pack(fill="x", pady=(6, 0))
        bar_bg.pack_propagate(False)

        fill_w = max(1, int(valor * 1000))  # proporcional em 1000 unidades
        fill_frame = ctk.CTkFrame(
            bar_bg, fg_color=color, corner_radius=RADIUS["pill"], height=7,
            width=fill_w,
        )
        fill_frame.pack(side="left", fill="y")


class NotificationPanel(ctk.CTkToplevel):
    """Modal de notificações."""
    def __init__(self, parent, titulo: str, notificacoes: list, tipo: str,
                 on_mark_read=None, on_mark_all_read=None):
        super().__init__(parent)
        self._parent_window = parent.winfo_toplevel()
        self.titulo = titulo
        self.notificacoes = notificacoes
        self.tipo = tipo
        self.on_mark_read = on_mark_read
        self.on_mark_all_read = on_mark_all_read
        self._setup()
        self._build()

    def _setup(self):
        self.title(self.titulo)
        self.geometry("520x480")
        self.resizable(False, False)
        self.configure(fg_color=THEME["surface"])
        self.attributes("-topmost", True)
        self.transient(self._parent_window)
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - 260
        y = self.winfo_screenheight() // 2 - 240
        self.geometry(f"520x480+{x}+{y}")

    def _build(self):
        is_ajuda = self.tipo == "ajuda"
        accent   = THEME["primary"] if is_ajuda else THEME["danger"]
        soft     = THEME["primary_soft"] if is_ajuda else THEME["danger_soft"]
        icon_txt = "🤝" if is_ajuda else "🔔"

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color=soft, corner_radius=0)
        header.pack(fill="x")

        hinner = ctk.CTkFrame(header, fg_color="transparent")
        hinner.pack(fill="x", padx=SPACING["page_x"], pady=14)

        ctk.CTkLabel(
            hinner, text=f"{icon_txt}  {self.titulo}",
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
        lst.pack(fill="both", expand=True, padx=20, pady=12)

        if not self.notificacoes:
            EmptyState(
                lst, icon="📭", title="Sem notificações",
                subtitle=f"Nenhuma notificação de {self.tipo} no momento",
            ).pack(pady=40)
        else:
            for notif in self.notificacoes:
                self._create_item(lst, notif, accent, soft, icon_txt)

    def _create_item(self, parent, notif, accent, soft, icon_txt):
        row = ctk.CTkFrame(
            parent, fg_color=soft,
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=4)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)
        inner.grid_columnconfigure(1, weight=1)

        # Ícone
        icon_bg = ctk.CTkFrame(
            inner, width=34, height=34, corner_radius=RADIUS["button"], fg_color=accent,
        )
        icon_bg.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="n", pady=(2, 0))
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
        ).grid(row=0, column=2, sticky="ne", padx=(8, 0))

        row.bind("<Button-1>",
                 lambda e, nid=notif["id"], t=self.tipo: self._on_click(nid, t))

    def _on_click(self, notif_id, tipo):
        if self.on_mark_read:
            self.on_mark_read(notif_id, tipo)
        self.destroy()

    def _mark_all_read(self):
        if self.on_mark_all_read:
            self.on_mark_all_read(self.tipo)
        self.destroy()


class ProfileModal(ctk.CTkToplevel):
    """Modal de perfil do usuário."""
    def __init__(self, parent, user_data: dict, on_edit=None):
        super().__init__(parent)
        self._parent_window = parent.winfo_toplevel()
        self.user_data = user_data or {}
        self.on_edit = on_edit
        self._setup()
        self._build()

    def _setup(self):
        self.title("Meu Perfil")
        self.geometry("440x380")
        self.resizable(False, False)
        self.configure(fg_color=THEME["surface"])
        self.attributes("-topmost", True)
        self.transient(self._parent_window)
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - 220
        y = self.winfo_screenheight() // 2 - 190
        self.geometry(f"440x380+{x}+{y}")

    def _build(self):
        # Banner de topo
        banner = ctk.CTkFrame(self, fg_color=THEME["primary_soft"], corner_radius=0, height=80)
        banner.pack(fill="x")

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
        body.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=(40, 20))

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
        ).pack(anchor="w", pady=(2, 6))

        # Chip de função
        chip = ctk.CTkFrame(body, fg_color=THEME["primary_soft"], corner_radius=RADIUS["button"])
        chip.pack(anchor="w")
        ctk.CTkLabel(
            chip, text="Analista Escolar",
            font=themed_font("body", "bold"),
            text_color=THEME["primary"],
        ).pack(padx=10, pady=4)

        Divider(body).pack(fill="x", pady=12)

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
        ).pack(pady=(4, 20))

    def _row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

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


# ══════════════════════════════════════════════════════════════════════════════
#  Frame principal – DashboardFrame
# ══════════════════════════════════════════════════════════════════════════════

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(
            parent,
            fg_color=THEME["bg"],
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.controller = controller
        self.servico_dashboard = ServicoDashboard()

        self._criar_toolbar_acoes()
        self._criar_kpi_container()
        self._criar_grid_principal()
        self._carregar_dados()

    # ──────────────────────────────────────────────────────────────────────
    #  Dados
    # ──────────────────────────────────────────────────────────────────────
    def _carregar_dados(self):
        self._mostrar_skeletons()

        def fetch():
            data = self.servico_dashboard.obter_kpis()
            return data

        def on_success(data):
            self._atualizar_dashboard(data)
            self._atualizar_badge_notificacoes()

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

    # ──────────────────────────────────────────────────────────────────────
    #  Toolbar de ações
    # ──────────────────────────────────────────────────────────────────────
    def _criar_toolbar_acoes(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 4))

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        # Ícone ajuda
        help_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=RADIUS["button"],
                               fg_color=THEME["primary_soft"])
        help_f.pack(side="left", padx=4)
        help_f.pack_propagate(False)
        bind_clickable(help_f, self._abrir_notificacoes_ajuda)
        ctk.CTkLabel(
            help_f, text="🤝",
            font=themed_font("body"),
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.help_badge = self._criar_badge(help_f)

        # Ícone alertas
        alert_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=RADIUS["button"],
                                fg_color=THEME["danger_soft"])
        alert_f.pack(side="left", padx=4)
        alert_f.pack_propagate(False)
        bind_clickable(alert_f, self._abrir_notificacoes_alertas)
        ctk.CTkLabel(
            alert_f, text="🔔",
            font=themed_font("body"),
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.alert_badge = self._criar_badge(alert_f)

        # Avatar
        name = ""
        if self.controller.usuario_logado:
            name = self.controller.usuario_logado.get("username", "?")[:2].upper()
        av_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=RADIUS["button"],
                             fg_color=THEME["primary"])
        av_f.pack(side="left", padx=(8, 0))
        av_f.pack_propagate(False)
        bind_clickable(av_f, self._abrir_perfil)
        ctk.CTkLabel(
            av_f, text=name,
            font=themed_font("body", "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _criar_badge(self, parent) -> ctk.CTkFrame:
        badge = ctk.CTkFrame(
            parent, width=18, height=18,
            corner_radius=9, fg_color=THEME["danger"],
        )
        ctk.CTkLabel(
            badge, text="0",
            font=themed_font("caption", "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")
        return badge

    # ──────────────────────────────────────────────────────────────────────
    #  KPI row
    # ──────────────────────────────────────────────────────────────────────
    def _criar_kpi_container(self):
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

    def _mostrar_skeletons(self):
        self._limpar(self.kpi_frame)
        for i in range(5):
            self.kpi_frame.grid_columnconfigure(i, weight=1)
            EmptyState(
                self.kpi_frame, icon="", title="",
            ).grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2)

    def _render_kpis(self, data):
        self._limpar(self.kpi_frame)
        media_humor = data.get("media_humor")
        humor_emoji = self._humor_emoji(media_humor)

        kpis = [
            ("Atendimentos Hoje", str(data.get("appointments_today", 0)),
             "👥", THEME["kpi_blue"],   THEME["kpi_blue_soft"],  "Atendimentos marcados"),
            ("Vagas Disponíveis", str(data.get("available_slots", 0)),
             "📅", THEME["kpi_green"],  THEME["kpi_green_soft"], "Horários livres"),
            ("Alertas Ativos",    str(data.get("alerts", 0)),
             "🔔", THEME["kpi_red"],    THEME["kpi_red_soft"],   "Requerem atenção"),
            ("Total de Estudantes", str(data.get("total_students", 0)),
             "🎓", THEME["kpi_violet"], THEME["kpi_violet_soft"],"Alunos cadastrados"),
            ("Humor Médio",
             f"{media_humor:.1f}/5" if media_humor else "—",
             humor_emoji, THEME["kpi_amber"], THEME["kpi_amber_soft"], "Média dos últimos 30 dias"),
        ]

        for i, (title, value, icon, accent, soft, sub) in enumerate(kpis):
            self.kpi_frame.grid_columnconfigure(i, weight=1)
            KPICard(
                self.kpi_frame, title=title, value=value, icon=icon,
                accent=accent, trend="", unit="", size=DASH_TOKENS.get("kpi_size", "wide"),
            ).grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2)

    # ──────────────────────────────────────────────────────────────────────
    #  Grid principal
    # ──────────────────────────────────────────────────────────────────────
    def _criar_grid_principal(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["section_gap"])
        grid.grid_columnconfigure(0, weight=3)
        grid.grid_columnconfigure(1, weight=2)

        self.left_col = ctk.CTkFrame(grid, fg_color="transparent")
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["grid_gap"]))

        self.right_col = ctk.CTkFrame(grid, fg_color="transparent")
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(SPACING["grid_gap"], 0))

        # Card do gráfico (na esquerda)
        self._criar_card_chart()

    def _criar_card_chart(self):
        self.chart_card = Card(self.left_col, title="📈  Humor dos Estudantes — últimos 30 dias")
        self.chart_card.pack(fill="x", pady=(0, 14))

        self.canvas = ctk.CTkCanvas(
            self.chart_card.body,
            bg=THEME["surface"],
            height=230,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=(4, 8))
        self._chart_after_id = None
        self.chart_card.body.bind("<Configure>", self._schedule_draw_chart)

    def _schedule_draw_chart(self, event=None):
        if self._chart_after_id:
            self.after_cancel(self._chart_after_id)
        self._chart_after_id = self.after(80, lambda: self._draw_chart())

    # ──────────────────────────────────────────────────────────────────────
    #  Seções
    # ──────────────────────────────────────────────────────────────────────
    def _atualizar_secao_agenda(self, data):
        self._limpar(self.left_col)
        # Recria o card do gráfico (que foi limpo)
        self._criar_card_chart()

        card = Card(
            self.left_col, title="📅  Próximos Atendimentos",
        )
        card.pack(fill="x", pady=(0, 14))

        appointments = data.get("upcoming_appointments", [])
        if appointments:
            for appt in appointments:
                _AgendaRow(card.body, appt).pack(fill="x", pady=3)
        else:
            EmptyState(
                card.body, icon="📅",
                title="Nenhum atendimento próximo",
                subtitle="Não há agendamentos futuros",
            ).pack(pady=10)

    def _atualizar_secao_alertas(self, data):
        n_alerts = len(data.get("attention_students", []))
        card = Card(
            self.right_col, title=f"🔴  Estudantes em Alerta",
        )
        card.pack(fill="x", pady=(0, 14))

        students = data.get("attention_students", [])
        if students:
            for s in students:
                _AlertaRow(card.body, s).pack(fill="x", pady=3)
        else:
            EmptyState(
                card.body, icon="✔",
                title="Tudo sob controle",
                subtitle="Nenhum estudante em alerta",
            ).pack(pady=10)

    def _atualizar_secao_bem_estar(self, data):
        card = Card(self.right_col, title="💚  Bem-Estar por Dimensão")
        card.pack(fill="x", pady=(0, 14))

        be = data.get("bem_estar_dimensions", {})
        dims = [
            ("📁  Acadêmico", be.get("academico", 0) / 5, THEME["primary"], THEME["primary_soft"]),
            ("💗  Emocional",  be.get("emocional", 0) / 5, "#EC4899", "#FCE7F3"),
            ("👥  Social",    be.get("social",    0) / 5, THEME["success"], THEME["success_soft"]),
        ]
        for nome, val, color, soft in dims:
            _BemEstarBar(card.body, nome, val, color, soft).pack(
                fill="x", padx=4, pady=8
            )

    def _atualizar_secao_humor(self, data):
        humor_history = data.get("humor_history", [])
        self._draw_chart(humor_history if humor_history else None)

    # ──────────────────────────────────────────────────────────────────────
    #  Gráfico canvas
    # ──────────────────────────────────────────────────────────────────────
    def _draw_chart(self, humor_history=None):
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 80 or ch < 80:
            return

        if not humor_history:
            pts   = [2.8, 3.1, 2.9, 3.2, 2.7, 3.5, 3.2, 2.9, 3.0, 3.8, 3.4, 3.6, 3.2, 3.1, 3.9]
            dates = ["05/01", "07/01", "09/01", "11/01", "13/01", "15/01",
                     "17/01", "19/01", "21/01", "23/01", "25/01", "27/01",
                     "28/01", "29/01", "30/01"]
        else:
            pts   = [item["media_humor"] for item in humor_history]
            dates = [item.get("data", "") for item in humor_history]
            if len(pts) < 2:
                pts   = [pts[0], pts[0]]
                dates = [dates[0], dates[0]]

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

    # ──────────────────────────────────────────────────────────────────────
    #  Notificações e badges
    # ──────────────────────────────────────────────────────────────────────
    def _abrir_notificacoes_ajuda(self):
        notifs = self.servico_dashboard.obter_notificacoes_ajuda()
        NotificationPanel(
            self, "Notificações de Ajuda", notifs, "ajuda",
            on_mark_read=self._marcar_lida,
            on_mark_all_read=self._marcar_todas_lidas,
        )

    def _abrir_notificacoes_alertas(self):
        notifs = self.servico_dashboard.obter_notificacoes_alertas()
        NotificationPanel(
            self, "Notificações de Alerta", notifs, "alerta",
            on_mark_read=self._marcar_lida,
            on_mark_all_read=self._marcar_todas_lidas,
        )

    def _abrir_perfil(self):
        ProfileModal(self, self.controller.usuario_logado, on_edit=self._editar_perfil)

    def _editar_perfil(self):
        print("Editar perfil")

    def _atualizar_badge_notificacoes(self):
        ajuda   = self.servico_dashboard.obter_notificacoes_ajuda()
        alertas = self.servico_dashboard.obter_notificacoes_alertas()
        n_ajuda   = sum(1 for n in ajuda   if not n.get("lida", True))
        n_alertas = sum(1 for n in alertas if not n.get("lida", True))
        self._set_badge(self.help_badge,  n_ajuda)
        self._set_badge(self.alert_badge, n_alertas)

    def _set_badge(self, badge: ctk.CTkFrame, count: int):
        lbl = next((c for c in badge.winfo_children()
                    if isinstance(c, ctk.CTkLabel)), None)
        if lbl:
            lbl.configure(text=str(count) if count else "")
        if count > 0:
            badge.place(relx=0.72, rely=0.05)
        else:
            badge.place_forget()

    def _marcar_lida(self, notif_id, tipo):
        self.servico_dashboard.marcar_notificacao_como_lida(notif_id, tipo)
        self._atualizar_badge_notificacoes()

    def _marcar_todas_lidas(self, tipo):
        notifs = (self.servico_dashboard.obter_notificacoes_ajuda()
                  if tipo == "ajuda"
                  else self.servico_dashboard.obter_notificacoes_alertas())
        for n in notifs:
            self.servico_dashboard.marcar_notificacao_como_lida(n["id"], tipo)
        self._atualizar_badge_notificacoes()

    # ──────────────────────────────────────────────────────────────────────
    #  Utilitários
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _limpar(widget):
        for child in widget.winfo_children():
            child.destroy()

    @staticmethod
    def _humor_emoji(media) -> str:
        if media is None: return "😐"
        if media < 2.0:   return "😢"
        if media < 3.0:   return "😕"
        if media < 4.0:   return "😊"
        return "😄"

    # Alias legado
    @staticmethod
    def get_humor_emoji(media):
        return DashboardFrame._humor_emoji(media)

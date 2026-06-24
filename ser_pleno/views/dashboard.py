import customtkinter as ctk
import threading
from services.dashboard import ServicoDashboard
from ui_theme import THEME, SPACING, RADIUS, font, themed_font, blend_color, lighten
from components.ui_components import (
    PageHeader, SectionHeader, Card, KPICard, EmptyState,
    PrimaryButton, GhostButton, Badge, Pill, Divider,
    Avatar, MetricCard, ListCard, SkeletonLoader, Toast
)


# ══════════════════════════════════════════════════════════════════════════════
#  Paleta dedicada à tela de Dashboard
# ══════════════════════════════════════════════════════════════════════════════
DASH_COLORS = {
    "kpi_card_bg":     THEME["surface"],
    "section_bg":      THEME["bg_alt"],
    "agenda_row":      THEME["bg_alt"],
    "alerta_row":      THEME["danger_soft"],
    "alerta_text":     THEME["danger_strong"],
    "chart_line":      THEME["primary"],
    "chart_fill":      blend_color(THEME["primary"], 0.08),
    "chart_bg":        THEME["surface"],
    "dot_good":        THEME["success"],
    "dot_warn":        THEME["warning"],
    "dot_bad":         THEME["danger"],
}


# ══════════════════════════════════════════════════════════════════════════════
#  Componentes reutilizáveis extraídos para classes próprias
# ══════════════════════════════════════════════════════════════════════════════

class AgendaItemRow(ctk.CTkFrame):
    """Linha individual de item na seção de agenda."""
    def __init__(self, parent, appt: dict):
        super().__init__(parent, fg_color=DASH_COLORS["agenda_row"], corner_radius=RADIUS["md"])
        self.appt = appt
        self._build()

    def _build(self):
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", padx=18, pady=14)

        ctk.CTkLabel(
            info, text=self.appt.get("student_name", "?"),
            font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            info,
            text=f"🎓  {self.appt.get('curso', '')}",
            font=themed_font("overline"), text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            self, text=f"🕒  {self.appt.get('time', '')}",
            font=themed_font("body", "bold"), text_color=THEME["primary"]
        ).pack(side="right", padx=18)


class AlertaItemRow(ctk.CTkFrame):
    """Linha individual de item na seção de alertas."""
    def __init__(self, parent, student: dict):
        super().__init__(parent, fg_color=DASH_COLORS["alerta_row"], corner_radius=RADIUS["md"])
        self.student = student
        self._build()

    def _build(self):
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", padx=18, pady=14)

        ctk.CTkLabel(
            info, text=self.student.get("name", "?"),
            font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            info,
            text=self.student.get("attention_reason", ""),
            font=themed_font("body_sm"), text_color=DASH_COLORS["alerta_text"]
        ).pack(anchor="w", pady=(2, 0))

        priority = self.student.get("priority_level", 0)
        icon_pri = {0: "🟡", 1: "🟠", 2: "🔴"}.get(priority, "🟡")

        ctk.CTkLabel(self, text=icon_pri, font=themed_font("h3")).pack(side="right", padx=18)


class BemEstarDimensionBar(ctk.CTkFrame):
    """Barra de progresso para uma dimensão de bem-estar."""
    def __init__(self, parent, nome: str, valor: float, color: str):
        super().__init__(parent, fg_color="transparent")
        self.valor = max(0.0, min(1.0, valor))  # clamp 0..1
        self.color = color
        self.nome = nome
        self._build()

    def _build(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", pady=10)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            header, text=self.nome,
            font=themed_font("body_sm"), text_color=THEME["text"]
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=f"{int(self.valor * 100)}%",
            font=themed_font("body_sm", "bold"), text_color=self.color
        ).pack(side="right")

        prog = ctk.CTkProgressBar(
            container, height=6, progress_color=self.color,
            fg_color=THEME["bg_alt"], corner_radius=RADIUS["pill"]
        )
        prog.pack(fill="x", pady=(4, 0))
        prog.set(self.valor)


class IndicatorFooter(ctk.CTkFrame):
    """Indicador compacto com ícone, label e valor para o chart."""
    def __init__(self, parent, icon: str, label: str, val: str):
        super().__init__(parent, fg_color="transparent")
        self._build(icon, label, val)

    def _build(self, icon, label, val):
        ctk.CTkLabel(self, text=icon, font=themed_font("h3")).pack()
        ctk.CTkLabel(
            self, text=label,
            font=themed_font("overline"), text_color=THEME["text_muted"]
        ).pack()
        ctk.CTkLabel(
            self, text=val,
            font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack()


class NotificationPanel(ctk.CTkToplevel):
    """Modal de notificações (ajuda ou alertas)."""
    def __init__(self, parent, titulo: str, notificacoes: list, tipo: str,
                 on_mark_read=None, on_mark_all_read=None):
        super().__init__(parent)
        self.titulo = titulo
        self.notificacoes = notificacoes
        self.tipo = tipo
        self.on_mark_read = on_mark_read
        self.on_mark_all_read = on_mark_all_read
        self._setup_window()
        self._build()

    def _setup_window(self):
        self.title(self.titulo)
        self.geometry("540x460")
        self.resizable(False, False)
        self.configure(fg_color=THEME["surface"])
        self.attributes("-topmost", True)
        self.transient(self.winfo_toplevel())

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 270
        y = (self.winfo_screenheight() // 2) - 230
        self.geometry(f"540x460+{x}+{y}")

    def _build(self):
        icon_color = THEME["info"] if self.tipo == "ajuda" else THEME["danger"]

        header = ctk.CTkFrame(self, fg_color=THEME["bg"])
        header.pack(fill="x", padx=24, pady=(18, 0))

        ctk.CTkLabel(
            header, text=self.titulo,
            font=themed_font("h3", "bold"), text_color=THEME["text"]
        ).pack(side="left")

        GhostButton(
            header, text="Marcar todas como lidas",
            command=self._mark_all_read, width=160
        ).pack(side="right")

        list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=24, pady=16)

        if not self.notificacoes:
            EmptyState(
                list_frame, icon="📭", title="Sem alertas",
                subtitle=f"Nenhuma notificação de {self.tipo} no momento"
            ).pack(pady=36)
        else:
            for notif in self.notificacoes:
                self._create_item(list_frame, notif)

    def _create_item(self, parent, notif: dict):
        item_frame = Card(parent)
        item_frame.pack(fill="x", pady=6, padx=4)

        icon_text = "🤝" if self.tipo == "ajuda" else "🔔"
        icon_color = THEME["info"] if self.tipo == "ajuda" else THEME["danger"]

        icon_bg = ctk.CTkFrame(
            item_frame.body, fg_color=blend_color(icon_color, 0.12),
            width=34, height=34, corner_radius=RADIUS["sm"]
        )
        icon_bg.pack(side="left", padx=(0, 12))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(
            icon_bg, text=icon_text, font=themed_font("body")
        ).place(relx=0.5, rely=0.5, anchor="center")

        text_frame = ctk.CTkFrame(item_frame.body, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            text_frame, text=notif.get("titulo", ""),
            font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_frame, text=notif.get("descricao", ""),
            font=themed_font("body_sm"), text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            text_frame, text=notif.get("data", ""),
            font=themed_font("overline"), text_color=THEME["text_disabled"]
        ).pack(anchor="w", pady=(3, 0))

        item_frame.bind(
            "<Button-1>",
            lambda e, nid=notif["id"], t=self.tipo: self._on_click_item(nid, t)
        )

    def _on_click_item(self, notif_id, tipo):
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
        self.user_data = user_data
        self.on_edit = on_edit
        self._setup_window()
        self._build()

    def _setup_window(self):
        self.title("Perfil do Usuário")
        self.geometry("440x360")
        self.resizable(False, False)
        self.configure(fg_color=THEME["surface"])
        self.attributes("-topmost", True)
        self.transient(self.winfo_toplevel())

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 220
        y = (self.winfo_screenheight() // 2) - 180
        self.geometry(f"440x360+{x}+{y}")

    def _build(self):
        if not self.user_data:
            return

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(24, 12))

        initials = (
            (self.user_data.get("first_name", "") or "")[0:1] +
            (self.user_data.get("last_name", "") or "")[0:1]
        ).upper() or self.user_data.get("username", "?")[:2].upper()

        Avatar(top, initials=initials, size=56, color=THEME["primary"]).pack(
            side="left", padx=(0, 14)
        )

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)

        nome = (
            f"{self.user_data.get('first_name', '')} "
            f"{self.user_data.get('last_name', '')}"
        ).strip() or self.user_data.get("username", "Usuário")

        ctk.CTkLabel(
            info, text=nome,
            font=themed_font("h3", "bold"), text_color=THEME["text"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=self.user_data.get("email", ""),
            font=themed_font("body"), text_color=THEME["text_muted"]
        ).pack(anchor="w", pady=(2, 0))

        Pill(
            info, text="Analista Escolar",
            color=THEME["primary_soft"], text_color=THEME["primary"]
        ).pack(anchor="w", pady=(6, 0))

        self._profile_section()
        PrimaryButton(
            self, text="Editar Perfil", command=self._edit, width=160
        ).pack(pady=(22, 14))

    def _profile_section(self):
        if not self.user_data:
            return
        frame = ctk.CTkFrame(self, fg_color=THEME["bg"], corner_radius=RADIUS["lg"])
        frame.pack(fill="x", padx=24, pady=8)

        self._profile_row(frame, "Nome de usuário", self.user_data.get("username", ""))
        self._profile_row(frame, "Função", "Analista Escolar")
        self._profile_row(frame, "Módulos", "Dashboard, Estudantes, Agenda, Bem-Estar")

    def _profile_row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(10, 0))

        ctk.CTkLabel(
            row, text=label,
            font=themed_font("overline"), text_color=THEME["text_muted"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            row, text=value,
            font=themed_font("body", "bold"), text_color=THEME["text"]
        ).pack(anchor="w", pady=(1, 0))

    def _edit(self):
        if self.on_edit:
            self.on_edit()


# ══════════════════════════════════════════════════════════════════════════════
#  Frame Principal – Dashboard
# ══════════════════════════════════════════════════════════════════════════════

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_dashboard = ServicoDashboard()
        self.grid_columnconfigure(0, weight=1)

        self._criar_cabecalho()
        self._criar_container_kpi()
        self._criar_grid_principal()
        self._carregar_dados()

    # ──────────────────────────────────────────────────────────────────────
    #  Ciclo de vida e dados
    # ──────────────────────────────────────────────────────────────────────

    def _carregar_dados(self):
        self._mostrar_skeletons()

        def fetch():
            data = self.servico_dashboard.obter_kpis()
            self.after(0, lambda: self._atualizar_dashboard(data))
            self.after(0, lambda: self._atualizar_badge_notificacoes())

        threading.Thread(target=fetch, daemon=True).start()

    def _atualizar_dashboard(self, data):
        """Atualiza toda a interface do dashboard com os dados recebidos."""
        self._render_kpis(data)
        self._atualizar_secao_agenda(data)
        self._atualizar_secao_alertas(data)
        self._atualizar_secao_bem_estar(data)
        self._atualizar_secao_humor(data)

    # ──────────────────────────────────────────────────────────────────────
    #  KPIs
    # ──────────────────────────────────────────────────────────────────────

    def _criar_container_kpi(self):
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(
            fill="x", padx=SPACING["page_x"],
            pady=(16, SPACING["section_gap"])
        )

    def _mostrar_skeletons(self):
        kpis = [
            {"titulo": "Atendimentos do Dia"},
            {"titulo": "Vagas Disponíveis"},
            {"titulo": "Alertas Ativos"},
            {"titulo": "Total de Estudantes"},
            {"titulo": "Humor Médio"},
        ]

        self._limpar_container(self.kpi_container)
        for i, kpi in enumerate(kpis):
            self.kpi_container.grid_columnconfigure(i, weight=1)
            SkeletonLoader(
                self.kpi_container, width=180, height=110, variant="card"
            ).grid(row=0, column=i, sticky="ew", padx=6)

        self._mostrar_skeletons_secao_agenda()
        self._mostrar_skeletons_secao_alertas()
        self._mostrar_skeletons_secao_bem_estar()

    def _mostrar_skeletons_secao_agenda(self):
        card = self._criar_container_card(
            self.left_col, "📅  Próximos Atendimentos", "Ver agenda completa →"
        )
        self._limpar_container(card.body)
        for _ in range(3):
            SkeletonLoader(card.body, width=400, height=64, variant="card").pack(
                fill="x", pady=4
            )

    def _mostrar_skeletons_secao_alertas(self):
        card = self._criar_container_card(
            self.right_col, "🔔  Estudantes em Alerta", status="Alerta"
        )
        self._limpar_container(card.body)
        for _ in range(2):
            SkeletonLoader(card.body, width=260, height=64, variant="card").pack(
                fill="x", pady=4
            )

    def _mostrar_skeletons_secao_bem_estar(self):
        card = self._criar_container_card(
            self.right_col, "❤  Bem-Estar por Dimensão"
        )
        self._limpar_container(card.body)
        for _ in range(3):
            SkeletonLoader(card.body, width=260, height=48, variant="text").pack(
                fill="x", pady=6
            )

    def _render_kpis(self, data):
        self._limpar_container(self.kpi_container)

        media_humor = data.get("media_humor")
        humor_emoji = self.get_humor_emoji(media_humor)

        kpis = [
            {"titulo": "Atendimentos do Dia", "valor": str(data.get("appointments_today", 0)),
             "icone": "👥", "cor": THEME["primary"], "trend": "Hoje", "unit": ""},
            {"titulo": "Vagas Disponíveis",   "valor": str(data.get("available_slots", 0)),
             "icone": "📅", "cor": THEME["success"], "trend": "Slots livres", "unit": ""},
            {"titulo": "Alertas Ativos",       "valor": str(data.get("alerts", 0)),
             "icone": "🔔", "cor": THEME["danger"], "trend": "Requer ação", "unit": ""},
            {"titulo": "Total de Estudantes",  "valor": str(data.get("total_students", 0)),
             "icone": "👥", "cor": THEME["accent"], "trend": "Cadastrados", "unit": ""},
            {"titulo": "Humor Médio",          "valor": f"{media_humor:.1f}" if media_humor else "—",
             "icone": humor_emoji, "cor": THEME["warning"], "trend": "Média", "unit": "/ 5"},
        ]

        for i, kpi in enumerate(kpis):
            self.kpi_container.grid_columnconfigure(i, weight=1)
            card = KPICard(
                self.kpi_container, title=kpi["titulo"], value=kpi["valor"],
                icon=kpi["icone"], accent=kpi["cor"], trend=kpi.get("trend", ""),
                unit=kpi.get("unit", ""), size="default" if i < 3 else "compact"
            )
            card.grid(row=0, column=i, sticky="ew", padx=6)
            card.bind("<Enter>",   lambda e, c=card: c.configure(cursor="hand2"))
            card.bind("<Leave>",   lambda e, c=card: c.configure(cursor=""))

    # ──────────────────────────────────────────────────────────────────────
    #  Seções
    # ──────────────────────────────────────────────────────────────────────

    def _atualizar_secao_agenda(self, data):
        card = self._criar_container_card(
            self.left_col, "📅  Próximos Atendimentos", "Ver agenda completa →"
        )
        self._limpar_container(card.body)

        appointments = data.get("upcoming_appointments", [])
        if appointments:
            for appt in appointments:
                AgendaItemRow(card.body, appt).pack(fill="x", pady=5)
        else:
            self._render_empty_agenda(card.body)

    def _atualizar_secao_alertas(self, data):
        card = self._criar_container_card(
            self.right_col, "🔔  Estudantes em Alerta", status="Alerta"
        )
        self._limpar_container(card.body)

        attention_students = data.get("attention_students", [])
        if attention_students:
            for student in attention_students:
                AlertaItemRow(card.body, student).pack(fill="x", pady=5)
        else:
            self._render_empty_alerts(card.body)

    def _atualizar_secao_bem_estar(self, data):
        card = self._criar_container_card(
            self.right_col, "❤  Bem-Estar por Dimensão"
        )
        self._limpar_container(card.body)

        bem_estar = data.get("bem_estar_dimensions", {})
        rows = [
            ("📁  Acadêmico", bem_estar.get("academico", 0) / 5, THEME["primary"]),
            ("❤  Emocional",  bem_estar.get("emocional", 0) / 5, THEME["danger"]),
            ("👥  Social",    bem_estar.get("social", 0) / 5,    THEME["success"]),
        ]
        for nome, val, color in rows:
            BemEstarDimensionBar(card.body, nome, val, color).pack(fill="x", pady=10)

    def _atualizar_secao_humor(self, data):
        humor_history = data.get("humor_history", [])
        if humor_history:
            self._draw_chart(humor_history)
            self._limpar_container(self.stats_side)

            total = sum(item["media_humor"] for item in humor_history)
            media_geral = round(total / len(humor_history), 2) if humor_history else 0
            IndicatorFooter(
                self.stats_side,
                self.get_humor_emoji(media_geral), "Média Geral", f"{media_geral}/5"
            ).pack()
        else:
            self._draw_chart()

    # ──────────────────────────────────────────────────────────────────────
    #  Chart (canvas 2D)
    # ──────────────────────────────────────────────────────────────────────

    def _draw_chart(self, humor_history=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 80 or h < 80:
            return

        if humor_history is None or not humor_history:
            pts = [2.8, 3.1, 2.9, 3.2, 2.7, 3.5, 3.2, 2.9, 3.0, 3.8, 3.4, 3.6, 3.2, 3.1, 3.9]
            dates = [
                "05/01", "07/01", "09/01", "11/01", "13/01", "15/01",
                "17/01", "19/01", "21/01", "23/01", "25/01", "27/01",
                "28/01", "29/01", "30/01"
            ]
        else:
            pts = [item["media_humor"] for item in humor_history]
            dates = [item.get("data", "") for item in humor_history]
            if len(pts) < 2:
                pts = [pts[0], pts[0]]
                dates = [dates[0], dates[0]]

        margin_x, margin_y = 42, 30
        chart_w, chart_h = w - 2 * margin_x, h - 2 * margin_y

        coords = []
        for i, v in enumerate(pts):
            x = margin_x + (i * chart_w / (len(pts) - 1))
            y = (h - margin_y) - ((v - 1) * chart_h / 4)
            coords.append((x, y))

        # Área do gráfico
        self.canvas.create_rectangle(
            margin_x, margin_y, w - margin_x, h - margin_y,
            fill=DASH_COLORS["chart_bg"], outline=THEME["border"]
        )

        # Linhas de grade horizontais
        for i in range(5):
            gy = margin_y + (i * chart_h / 4)
            self.canvas.create_line(
                margin_x, gy, w - margin_x, gy,
                fill=THEME["border"], dash=(3, 4)
            )

        # Linha e área preenchida
        for i, (x, y) in enumerate(coords[:-1]):
            nx, ny = coords[i + 1]
            self.canvas.create_line(
                x, y, nx, ny, fill=DASH_COLORS["chart_line"],
                width=2, capstyle="round", joinstyle="round"
            )
            self.canvas.create_polygon(
                x, y, nx, ny, nx, h - margin_y, x, h - margin_y,
                fill=DASH_COLORS["chart_fill"], outline=""
            )

        # Pontos
        for i, (x, y) in enumerate(coords):
            val = pts[i]
            dot_color = (
                DASH_COLORS["dot_bad"] if val < 2.5 else
                DASH_COLORS["dot_warn"] if val < 3.5 else
                DASH_COLORS["dot_good"]
            )
            self.canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                fill=dot_color, outline=THEME["surface"], width=2
            )

        # Labels de data
        for i, (x, y) in enumerate(coords):
            if i % max(1, len(coords) // 7) == 0:
                self.canvas.create_text(
                    x, h - 8, text=dates[i],
                    font=("Inter", 8), fill=THEME["text_muted"]
                )

    # ──────────────────────────────────────────────────────────────────────
    #  Cabeçalho e grid principal
    # ──────────────────────────────────────────────────────────────────────

    def _criar_cabecalho(self):
        header = PageHeader(
            self, title="Dashboard Central",
            subtitle="Visão geral do acompanhamento discente",
            show_breadcrumb=True, breadcrumb_parts=["Início", "Dashboard"],
        )
        header.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["section_gap"]))

        icons_frame = ctk.CTkFrame(header, fg_color="transparent")
        icons_frame.pack(side="right", padx=(0, 14))

        # Ícone ajuda
        help_f = ctk.CTkFrame(icons_frame, fg_color="transparent", width=40, height=40, cursor="hand2")
        help_f.pack(side="left", padx=6)
        help_f.bind("<Button-1>", lambda e: self._abrir_notificacoes_ajuda())
        ctk.CTkLabel(help_f, text="🤝", font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")
        self.help_badge = Badge(help_f, text="0")
        self.help_badge.place(x=24, y=2)

        # Ícone alertas
        alert_f = ctk.CTkFrame(icons_frame, fg_color="transparent", width=40, height=40, cursor="hand2")
        alert_f.pack(side="left", padx=6)
        alert_f.bind("<Button-1>", lambda e: self._abrir_notificacoes_alertas())
        ctk.CTkLabel(
            alert_f, text="🔔", font=themed_font("h3"),
            text_color=THEME["text_secondary"]
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.alert_badge = Badge(alert_f, text="0")
        self.alert_badge.place(x=24, y=2)

        # Avatar do usuário
        profile_f = ctk.CTkFrame(icons_frame, fg_color="transparent", width=40, height=40, cursor="hand2")
        profile_f.pack(side="left", padx=6)
        profile_f.bind("<Button-1>", lambda e: self._abrir_perfil())
        name = ""
        if self.controller.usuario_logado:
            name = self.controller.usuario_logado.get("username", "?")[:2].upper()
        Avatar(profile_f, initials=name, size=36)

        # Logout
        logout_f = ctk.CTkFrame(icons_frame, fg_color="transparent", width=40, height=40, cursor="hand2")
        logout_f.pack(side="left", padx=6)
        logout_f.bind("<Button-1>", lambda e: self._fazer_logout())
        ctk.CTkLabel(
            logout_f, text="🚪", font=themed_font("h3"),
            text_color=THEME["text_secondary"]
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _criar_grid_principal(self):
        main_grid = ctk.CTkFrame(self, fg_color="transparent")
        main_grid.pack(fill="x", padx=SPACING["page_x"], pady=10)
        main_grid.grid_columnconfigure(0, weight=3)
        main_grid.grid_columnconfigure(1, weight=2)

        self.left_col = ctk.CTkFrame(main_grid, fg_color="transparent")
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        self._criar_secao_chart(self.left_col)

        self.right_col = ctk.CTkFrame(main_grid, fg_color="transparent")
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

    def _criar_secao_chart(self, parent):
        card = self._criar_container_card(parent, "📈  Humor dos Estudantes (30 dias)")
        chart_layout = ctk.CTkFrame(card.body, fg_color="transparent")
        chart_layout.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = ctk.CTkCanvas(
            chart_layout, bg=THEME["surface"], height=260, highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        self.stats_side = ctk.CTkFrame(chart_layout, fg_color="transparent")
        self.stats_side.pack_forget()

        card.body.bind("<Configure>", lambda e: self._draw_chart())

    # ──────────────────────────────────────────────────────────────────────
    #  Helpers de construção de cards
    # ──────────────────────────────────────────────────────────────────────

    def _criar_container_card(self, parent, titulo, link_txt=None, status=None) -> Card:
        card = Card(parent, title=titulo, status=status)
        card.pack(fill="x", pady=(0, SPACING["section_gap"]))
        if link_txt:
            first = card.body.winfo_children()[0] if card.body.winfo_children() else None
            if first:
                h = first.master if hasattr(first, "master") and isinstance(first.master, ctk.CTkFrame) else card.body
                link_lbl = ctk.CTkLabel(
                    h, text=link_txt, font=themed_font("caption"),
                    text_color=THEME["primary"], cursor="hand2"
                )
                link_lbl.pack(side="right")
        return card

    @staticmethod
    def _limpar_container(widget):
        for child in widget.winfo_children():
            child.destroy()

    @staticmethod
    def _render_empty_agenda(parent):
        EmptyState(
            parent, icon="📅", title="Nenhum atendimento próximo",
            subtitle="Não há agendamentos futuros"
        ).pack(pady=10)

    @staticmethod
    def _render_empty_alerts(parent):
        EmptyState(
            parent, icon="✔", title="Tudo sob controle",
            subtitle="Nenhum estudante em alerta no momento"
        ).pack(pady=10)

    # ──────────────────────────────────────────────────────────────────────
    #  ações do cabeçalho
    # ──────────────────────────────────────────────────────────────────────

    def _abrir_notificacoes_ajuda(self):
        notificacoes = self.servico_dashboard.obter_notificacoes_ajuda()
        self._abrir_painel_notificacoes("Notificações de Ajuda", notificacoes, "ajuda", THEME["info"])

    def _abrir_notificacoes_alertas(self):
        notificacoes = self.servico_dashboard.obter_notificacoes_alertas()
        self._abrir_painel_notificacoes("Notificações de Alertas", notificacoes, "alerta", THEME["danger"])

    def _abrir_painel_notificacoes(self, titulo, notificacoes, tipo, color):
        NotificationPanel(
            self, titulo, notificacoes, tipo,
            on_mark_read=self._marcar_notificacao_como_lida,
            on_mark_all_read=self._marcar_todas_como_lidas
        )

    def _abrir_perfil(self):
        user_data = self.controller.usuario_logado
        ProfileModal(self, user_data, on_edit=self.editar_perfil)

    def editar_perfil(self):
        print("Editar perfil")

    def _fazer_logout(self):
        from tkinter import messagebox
        if messagebox.askyesno("Logout", "Deseja realmente sair do SerPleno?"):
            self.controller.mostrar_login()

    # ──────────────────────────────────────────────────────────────────────
    #  Badges de notificação
    # ──────────────────────────────────────────────────────────────────────

    def _atualizar_badge_notificacoes(self):
        ajuda = self.servico_dashboard.obter_notificacoes_ajuda()
        alertas = self.servico_dashboard.obter_notificacoes_alertas()
        nao_lidas_ajuda = sum(1 for n in ajuda if not n.get("lida", True))
        nao_lidas_alertas = sum(1 for n in alertas if not n.get("lida", True))

        self._update_badge(self.help_badge, nao_lidas_ajuda)
        self._update_badge(self.alert_badge, nao_lidas_alertas)

    def _update_badge(self, badge, count):
        label = next((c for c in badge.winfo_children() if isinstance(c, ctk.CTkLabel)), None)
        if label is None:
            return
        label.configure(text=str(count) if count > 0 else "")
        badge.configure(width=max(22, len(str(count)) * 10 + 12))
        badge.place_forget()
        if count > 0:
            badge.place(x=24, y=0)

    def _marcar_notificacao_como_lida(self, notif_id, tipo):
        self.servico_dashboard.marcar_notificacao_como_lida(notif_id, tipo)
        self._atualizar_badge_notificacoes()

    def _marcar_todas_como_lidas(self, tipo):
        notificacoes = (
            self.servico_dashboard.obter_notificacoes_ajuda()
            if tipo == "ajuda"
            else self.servico_dashboard.obter_notificacoes_alertas()
        )
        for notif in notificacoes:
            self.servico_dashboard.marcar_notificacao_como_lida(notif["id"], tipo)
        self._atualizar_badge_notificacoes()

    # ──────────────────────────────────────────────────────────────────────
    #  Helpers utilitários
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_humor_emoji(media_humor):
        """Retorna emoji correspondente à faixa de humor médio."""
        if media_humor is None:
            return "😐"
        if media_humor < 2.0:
            return "😢"
        if media_humor < 3.0:
            return "😕"
        if media_humor < 4.0:
            return "😊"
        return "😄"

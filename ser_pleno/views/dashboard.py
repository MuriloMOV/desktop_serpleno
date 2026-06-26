import customtkinter as ctk
import threading
from services.dashboard import ServicoDashboard
from ui_theme import THEME, SPACING, RADIUS, font, themed_font, blend_color
from components.ui_components import (
    PageHeader, Card, KPICard, EmptyState,
    PrimaryButton, GhostButton, Badge, Pill, Divider,
    Avatar, SkeletonLoader,
)


# ══════════════════════════════════════════════════════════════════════════════
#  Design tokens – família índigo (consistente com login e app)
# ══════════════════════════════════════════════════════════════════════════════
D = {
    # Fundo geral
    "page_bg":          "#F8F7FF",   # branco com toque lavanda
    "card_bg":          "#FFFFFF",
    "card_border":      "#E5E7EB",
    "card_radius":      16,

    # KPI cores de acento
    "kpi_blue":         "#4F46E5",   # índigo
    "kpi_green":        "#059669",   # esmeralda
    "kpi_red":          "#DC2626",   # vermelho
    "kpi_violet":       "#7C3AED",   # violeta
    "kpi_amber":        "#D97706",   # âmbar

    # KPI pastel (bg do ícone)
    "kpi_blue_soft":    "#EEF2FF",
    "kpi_green_soft":   "#D1FAE5",
    "kpi_red_soft":     "#FEE2E2",
    "kpi_violet_soft":  "#EDE9FE",
    "kpi_amber_soft":   "#FEF3C7",

    # Texto
    "text":             "#111827",
    "text_muted":       "#6B7280",
    "text_light":       "#9CA3AF",

    # Gráfico
    "chart_line":       "#4F46E5",
    "chart_fill":       "#EEF2FF",
    "chart_grid":       "#E5E7EB",
    "dot_good":         "#059669",
    "dot_warn":         "#D97706",
    "dot_bad":          "#DC2626",

    # Seções
    "agenda_row_bg":    "#F8F7FF",
    "agenda_row_hover": "#EEF2FF",
    "alerta_row_bg":    "#FEF2F2",
    "alerta_text":      "#DC2626",

    # Bem-estar
    "be_academic":      "#4F46E5",
    "be_emotional":     "#EC4899",
    "be_social":        "#059669",

    # Divider
    "divider":          "#F3F4F6",

    # Badge notificação
    "badge_bg":         "#DC2626",
    "badge_text":       "#FFFFFF",
}


# ══════════════════════════════════════════════════════════════════════════════
#  Componentes auxiliares
# ══════════════════════════════════════════════════════════════════════════════

class _SectionCard(ctk.CTkFrame):
    """Card padrão de seção com título e corpo."""
    def __init__(self, parent, title: str, action_text: str = "",
                 action_cmd=None, badge_text: str = ""):
        super().__init__(
            parent,
            fg_color=D["card_bg"],
            corner_radius=D["card_radius"],
            border_width=1,
            border_color=D["card_border"],
        )

        # ── Cabeçalho do card ────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 0))

        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(side="left", fill="x")

        ctk.CTkLabel(
            title_row, text=title,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=D["text"],
        ).pack(side="left")

        if badge_text:
            badge = ctk.CTkFrame(
                title_row, width=22, height=22,
                corner_radius=11, fg_color=D["badge_bg"],
            )
            badge.pack(side="left", padx=(6, 0))
            badge.pack_propagate(False)
            ctk.CTkLabel(
                badge, text=badge_text,
                font=ctk.CTkFont("Segoe UI", 10, "bold"),
                text_color=D["badge_text"],
            ).place(relx=0.5, rely=0.5, anchor="center")

        if action_text and action_cmd:
            ctk.CTkButton(
                header, text=action_text,
                command=action_cmd,
                font=ctk.CTkFont("Segoe UI", 11),
                fg_color="transparent",
                hover_color=D["kpi_blue_soft"],
                text_color=D["kpi_blue"],
                height=28, corner_radius=8,
            ).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color=D["divider"]).pack(
            fill="x", padx=20, pady=(12, 0)
        )

        # ── Corpo ────────────────────────────────────────────────────────
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=16, pady=(8, 16))


class _KPICard(ctk.CTkFrame):
    """Card de KPI redesenhado: ícone num círculo colorido, valor grande, label."""
    def __init__(self, parent, title: str, value: str, icon: str,
                 accent: str, soft: str, sub: str = ""):
        super().__init__(
            parent,
            fg_color=D["card_bg"],
            corner_radius=D["card_radius"],
            border_width=1,
            border_color=D["card_border"],
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        # Linha superior: ícone + valor
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")

        # Círculo ícone
        icon_bg = ctk.CTkFrame(
            top, width=42, height=42,
            corner_radius=12, fg_color=soft,
        )
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(
            icon_bg, text=icon,
            font=ctk.CTkFont("Segoe UI", 18),
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Valor numérico grande
        ctk.CTkLabel(
            top, text=value,
            font=ctk.CTkFont("Segoe UI", 28, "bold"),
            text_color=D["text"],
        ).pack(side="right", anchor="e")

        # Linha inferior: título + sub
        ctk.CTkLabel(
            inner, text=title,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=D["text"],
            anchor="w",
        ).pack(fill="x", pady=(10, 2))

        if sub:
            ctk.CTkLabel(
                inner, text=sub,
                font=ctk.CTkFont("Segoe UI", 11),
                text_color=D["text_muted"],
                anchor="w",
            ).pack(fill="x")

        # Barra de acento na base
        ctk.CTkFrame(
            self, height=3,
            corner_radius=0, fg_color=accent,
        ).pack(side="bottom", fill="x")


class _AgendaRow(ctk.CTkFrame):
    """Linha de item de agenda com estilo refinado."""
    def __init__(self, parent, appt: dict):
        super().__init__(
            parent,
            fg_color=D["agenda_row_bg"],
            corner_radius=10,
        )
        self._build(appt)

    def _build(self, appt):
        # Barra colorida lateral
        ctk.CTkFrame(
            self, width=3, corner_radius=2, fg_color=D["kpi_blue"],
        ).pack(side="left", fill="y", padx=(10, 12), pady=10)

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", pady=12, fill="x", expand=True)

        ctk.CTkLabel(
            info, text=appt.get("student_name", "?"),
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=D["text"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=appt.get("curso", ""),
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=D["text_muted"], anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Hora
        time_frame = ctk.CTkFrame(
            self, fg_color=D["kpi_blue_soft"],
            corner_radius=8,
        )
        time_frame.pack(side="right", padx=14, pady=12)
        ctk.CTkLabel(
            time_frame,
            text=f"🕒  {appt.get('time', '')}",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=D["kpi_blue"],
        ).pack(padx=10, pady=5)


class _AlertaRow(ctk.CTkFrame):
    """Linha de estudante em alerta."""
    _PRIORITY_COLOR = {0: D["kpi_amber"], 1: "#F97316", 2: D["kpi_red"], 3: D["kpi_red"]}
    _PRIORITY_LABEL = {0: "Moderado", 1: "Alto", 2: "Crítico", 3: "Crítico"}
    _PRIORITY_ICON  = {0: "🟡", 1: "🟠", 2: "🔴", 3: "🔴"}

    def __init__(self, parent, student: dict):
        super().__init__(
            parent,
            fg_color=D["alerta_row_bg"],
            corner_radius=10,
        )
        self._build(student)

    def _build(self, student):
        priority = student.get("priority_level", 0)
        bar_color = self._PRIORITY_COLOR.get(priority, D["kpi_amber"])

        ctk.CTkFrame(
            self, width=3, corner_radius=2, fg_color=bar_color,
        ).pack(side="left", fill="y", padx=(10, 12), pady=10)

        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(side="left", pady=12, fill="x", expand=True)

        ctk.CTkLabel(
            info, text=student.get("name", "?"),
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=D["text"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            info, text=student.get("attention_reason", ""),
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=D["alerta_text"], anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Chip de prioridade
        chip = ctk.CTkFrame(
            self, fg_color=D["kpi_red_soft"], corner_radius=8,
        )
        chip.pack(side="right", padx=14, pady=12)
        ctk.CTkLabel(
            chip,
            text=f"{self._PRIORITY_ICON[priority]}  {self._PRIORITY_LABEL.get(priority, '')}",
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            text_color=D["kpi_red"],
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
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=D["text"], anchor="w",
        ).pack(side="left")

        pct_frame = ctk.CTkFrame(row, fg_color=soft, corner_radius=6)
        pct_frame.pack(side="right")
        ctk.CTkLabel(
            pct_frame,
            text=f"{int(valor * 100)}%",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=color,
        ).pack(padx=8, pady=2)

        bar_bg = ctk.CTkFrame(self, fg_color="#F3F4F6", corner_radius=4, height=7)
        bar_bg.pack(fill="x", pady=(6, 0))
        bar_bg.pack_propagate(False)

        fill_w = max(1, int(valor * 1000))  # proporcional em 1000 unidades
        fill_frame = ctk.CTkFrame(
            bar_bg, fg_color=color, corner_radius=4, height=7,
            width=fill_w,
        )
        fill_frame.pack(side="left", fill="y")


class NotificationPanel(ctk.CTkToplevel):
    """Modal de notificações."""
    def __init__(self, parent, titulo: str, notificacoes: list, tipo: str,
                 on_mark_read=None, on_mark_all_read=None):
        super().__init__(parent)
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
        self.configure(fg_color="#FFFFFF")
        self.attributes("-topmost", True)
        self.transient(self.winfo_toplevel())
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - 260
        y = self.winfo_screenheight() // 2 - 240
        self.geometry(f"520x480+{x}+{y}")

    def _build(self):
        is_ajuda = self.tipo == "ajuda"
        accent   = D["kpi_blue"] if is_ajuda else D["kpi_red"]
        soft     = D["kpi_blue_soft"] if is_ajuda else D["kpi_red_soft"]
        icon_txt = "🤝" if is_ajuda else "🔔"

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color=soft, corner_radius=0)
        header.pack(fill="x")

        hinner = ctk.CTkFrame(header, fg_color="transparent")
        hinner.pack(fill="x", padx=24, pady=14)

        ctk.CTkLabel(
            hinner, text=f"{icon_txt}  {self.titulo}",
            font=ctk.CTkFont("Segoe UI", 15, "bold"),
            text_color=accent,
        ).pack(side="left")

        ctk.CTkButton(
            hinner, text="Marcar todas como lidas",
            command=self._mark_all_read,
            height=30, corner_radius=8,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color=accent, hover_color=blend_color(accent, 0.8),
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
            corner_radius=10,
        )
        row.pack(fill="x", pady=4)
        row.pack_propagate(False)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=10)
        inner.grid_columnconfigure(1, weight=1)

        # Ícone
        icon_bg = ctk.CTkFrame(
            inner, width=34, height=34, corner_radius=8, fg_color=accent,
        )
        icon_bg.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="n", pady=(2, 0))
        icon_bg.grid_propagate(False)
        ctk.CTkLabel(
            icon_bg, text=icon_txt,
            font=ctk.CTkFont("Segoe UI", 14),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text=notif.get("titulo", ""),
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            text_color=D["text"], anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner, text=notif.get("descricao", ""),
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=D["text_muted"], anchor="w",
        ).grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(
            inner, text=notif.get("data", ""),
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=D["text_light"], anchor="e",
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
        self.user_data = user_data or {}
        self.on_edit = on_edit
        self._setup()
        self._build()

    def _setup(self):
        self.title("Meu Perfil")
        self.geometry("440x380")
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")
        self.attributes("-topmost", True)
        self.transient(self.winfo_toplevel())
        self.update_idletasks()
        x = self.winfo_screenwidth() // 2 - 220
        y = self.winfo_screenheight() // 2 - 190
        self.geometry(f"440x380+{x}+{y}")

    def _build(self):
        # Banner de topo
        banner = ctk.CTkFrame(self, fg_color=D["kpi_blue_soft"], corner_radius=0, height=80)
        banner.pack(fill="x")

        initials = (
            (self.user_data.get("first_name", "") or "")[0:1] +
            (self.user_data.get("last_name",  "") or "")[0:1]
        ).upper() or self.user_data.get("username", "?")[:2].upper()

        av = ctk.CTkFrame(
            self, width=64, height=64,
            corner_radius=32, fg_color=D["kpi_blue"],
        )
        av.place(x=28, y=48)
        av.pack_propagate(False)
        ctk.CTkLabel(
            av, text=initials,
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(40, 20))

        nome = (
            f"{self.user_data.get('first_name', '')} "
            f"{self.user_data.get('last_name', '')}"
        ).strip() or self.user_data.get("username", "Usuário")

        ctk.CTkLabel(
            body, text=nome,
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            text_color=D["text"], anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            body, text=self.user_data.get("email", ""),
            font=ctk.CTkFont("Segoe UI", 12),
            text_color=D["text_muted"], anchor="w",
        ).pack(anchor="w", pady=(2, 6))

        # Chip de função
        chip = ctk.CTkFrame(body, fg_color=D["kpi_blue_soft"], corner_radius=8)
        chip.pack(anchor="w")
        ctk.CTkLabel(
            chip, text="Analista Escolar",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=D["kpi_blue"],
        ).pack(padx=10, pady=4)

        ctk.CTkFrame(body, height=1, fg_color=D["card_border"]).pack(
            fill="x", pady=12
        )

        # Rows de info
        for label, value in [
            ("Usuário",  self.user_data.get("username", "")),
            ("Função",   "Analista Escolar"),
            ("Módulos",  "Dashboard, Estudantes, Agenda, Bem-Estar"),
        ]:
            self._row(body, label, value)

        ctk.CTkButton(
            self, text="Editar Perfil",
            command=lambda: self.on_edit() if self.on_edit else None,
            height=38, corner_radius=10, width=160,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=D["kpi_blue"], hover_color="#4338CA",
            text_color="white",
        ).pack(pady=(4, 20))

    def _row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row, text=label, width=90,
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=D["text_muted"], anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            row, text=value,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=D["text"], anchor="w",
        ).pack(side="left")


# ══════════════════════════════════════════════════════════════════════════════
#  Frame principal – DashboardFrame
# ══════════════════════════════════════════════════════════════════════════════

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(
            parent,
            fg_color=D["page_bg"],
            scrollbar_button_color="#C7D2FE",
            scrollbar_button_hover_color="#A5B4FC",
        )
        self.controller = controller
        self.servico_dashboard = ServicoDashboard()

        self._criar_cabecalho()
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
            self.after(0, lambda: self._atualizar_dashboard(data))
            self.after(0, self._atualizar_badge_notificacoes)
        threading.Thread(target=fetch, daemon=True).start()

    def _atualizar_dashboard(self, data):
        self._render_kpis(data)
        self._atualizar_secao_agenda(data)
        self._atualizar_secao_alertas(data)
        self._atualizar_secao_bem_estar(data)
        self._atualizar_secao_humor(data)

    # ──────────────────────────────────────────────────────────────────────
    #  Cabeçalho
    # ──────────────────────────────────────────────────────────────────────
    def _criar_cabecalho(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=28, pady=(20, 4))

        # Saudação
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left")

        ctk.CTkLabel(
            left, text="Dashboard Central",
            font=ctk.CTkFont("Segoe UI", 22, "bold"),
            text_color=D["text"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="Visão geral do acompanhamento discente",
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=D["text_muted"],
        ).pack(anchor="w", pady=(2, 0))

        # Botões do lado direito
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        # Ícone ajuda
        help_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=10,
                               fg_color=D["kpi_blue_soft"], cursor="hand2")
        help_f.pack(side="left", padx=4)
        help_f.pack_propagate(False)
        help_f.bind("<Button-1>", lambda e: self._abrir_notificacoes_ajuda())
        ctk.CTkLabel(
            help_f, text="🤝",
            font=ctk.CTkFont("Segoe UI", 16),
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.help_badge = self._criar_badge(help_f)

        # Ícone alertas
        alert_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=10,
                                fg_color=D["kpi_red_soft"], cursor="hand2")
        alert_f.pack(side="left", padx=4)
        alert_f.pack_propagate(False)
        alert_f.bind("<Button-1>", lambda e: self._abrir_notificacoes_alertas())
        ctk.CTkLabel(
            alert_f, text="🔔",
            font=ctk.CTkFont("Segoe UI", 16),
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.alert_badge = self._criar_badge(alert_f)

        # Avatar
        name = ""
        if self.controller.usuario_logado:
            name = self.controller.usuario_logado.get("username", "?")[:2].upper()
        av_f = ctk.CTkFrame(right, width=38, height=38, corner_radius=10,
                             fg_color=D["kpi_blue"], cursor="hand2")
        av_f.pack(side="left", padx=(8, 0))
        av_f.pack_propagate(False)
        av_f.bind("<Button-1>", lambda e: self._abrir_perfil())
        ctk.CTkLabel(
            av_f, text=name,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Divider
        ctk.CTkFrame(self, height=1, fg_color=D["card_border"]).pack(
            fill="x", padx=28, pady=(12, 0)
        )

    def _criar_badge(self, parent) -> ctk.CTkFrame:
        badge = ctk.CTkFrame(
            parent, width=18, height=18,
            corner_radius=9, fg_color=D["badge_bg"],
        )
        ctk.CTkLabel(
            badge, text="0",
            font=ctk.CTkFont("Segoe UI", 9, "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")
        return badge

    # ──────────────────────────────────────────────────────────────────────
    #  KPI row
    # ──────────────────────────────────────────────────────────────────────
    def _criar_kpi_container(self):
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.pack(fill="x", padx=28, pady=(18, 0))

    def _mostrar_skeletons(self):
        self._limpar(self.kpi_frame)
        for i in range(5):
            self.kpi_frame.grid_columnconfigure(i, weight=1)
            SkeletonLoader(
                self.kpi_frame, width=180, height=110, variant="card"
            ).grid(row=0, column=i, sticky="ew", padx=5)

    def _render_kpis(self, data):
        self._limpar(self.kpi_frame)
        media_humor = data.get("media_humor")
        humor_emoji = self._humor_emoji(media_humor)

        kpis = [
            ("Atendimentos Hoje", str(data.get("appointments_today", 0)),
             "👥", D["kpi_blue"],   D["kpi_blue_soft"],  "Atendimentos marcados"),
            ("Vagas Disponíveis", str(data.get("available_slots", 0)),
             "📅", D["kpi_green"],  D["kpi_green_soft"], "Horários livres"),
            ("Alertas Ativos",    str(data.get("alerts", 0)),
             "🔔", D["kpi_red"],    D["kpi_red_soft"],   "Requerem atenção"),
            ("Total de Estudantes", str(data.get("total_students", 0)),
             "🎓", D["kpi_violet"], D["kpi_violet_soft"],"Alunos cadastrados"),
            ("Humor Médio",
             f"{media_humor:.1f}/5" if media_humor else "—",
             humor_emoji, D["kpi_amber"], D["kpi_amber_soft"], "Média dos últimos 30 dias"),
        ]

        for i, (title, value, icon, accent, soft, sub) in enumerate(kpis):
            self.kpi_frame.grid_columnconfigure(i, weight=1)
            _KPICard(
                self.kpi_frame, title, value, icon, accent, soft, sub,
            ).grid(row=0, column=i, sticky="ew", padx=5)

    # ──────────────────────────────────────────────────────────────────────
    #  Grid principal
    # ──────────────────────────────────────────────────────────────────────
    def _criar_grid_principal(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=28, pady=18)
        grid.grid_columnconfigure(0, weight=3)
        grid.grid_columnconfigure(1, weight=2)

        self.left_col = ctk.CTkFrame(grid, fg_color="transparent")
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.right_col = ctk.CTkFrame(grid, fg_color="transparent")
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        # Card do gráfico (na esquerda)
        self._criar_card_chart()

    def _criar_card_chart(self):
        self.chart_card = _SectionCard(self.left_col, "📈  Humor dos Estudantes — últimos 30 dias")
        self.chart_card.pack(fill="x", pady=(0, 14))

        self.canvas = ctk.CTkCanvas(
            self.chart_card.body,
            bg=D["card_bg"],
            height=230,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=4, pady=(4, 8))
        self.chart_card.body.bind("<Configure>", lambda e: self._draw_chart())

    # ──────────────────────────────────────────────────────────────────────
    #  Seções
    # ──────────────────────────────────────────────────────────────────────
    def _atualizar_secao_agenda(self, data):
        self._limpar(self.left_col)
        # Recria o card do gráfico (que foi limpo)
        self._criar_card_chart()

        card = _SectionCard(
            self.left_col, "📅  Próximos Atendimentos",
            action_text="Ver agenda →",
            action_cmd=self.controller.mostrar_agenda,
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
        card = _SectionCard(
            self.right_col, "🔴  Estudantes em Alerta",
            badge_text=str(n_alerts) if n_alerts else "",
            action_text="Ver todos →",
            action_cmd=self.controller.mostrar_estudantes,
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
        card = _SectionCard(self.right_col, "💚  Bem-Estar por Dimensão")
        card.pack(fill="x", pady=(0, 14))

        be = data.get("bem_estar_dimensions", {})
        dims = [
            ("📁  Acadêmico", be.get("academico", 0) / 5, D["be_academic"], D["kpi_blue_soft"]),
            ("💗  Emocional",  be.get("emocional", 0) / 5, D["be_emotional"], "#FCE7F3"),
            ("👥  Social",    be.get("social",    0) / 5, D["be_social"],   D["kpi_green_soft"]),
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
            fill=D["card_bg"], outline=D["chart_grid"], width=1,
        )

        # Grades horizontais e labels Y
        for i in range(6):
            val = 1 + i
            gy  = (ch - my) - (i * ch2 / 5)
            self.canvas.create_line(
                mx, gy, cw - mx, gy,
                fill=D["chart_grid"], dash=(3, 5),
            )
            self.canvas.create_text(
                mx - 6, gy, text=str(val),
                font=("Segoe UI", 8), fill=D["text_muted"], anchor="e",
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
        self.canvas.create_polygon(poly_pts, fill=D["chart_fill"], outline="")

        # Linha principal
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=D["chart_line"], width=2,
                capstyle="round", joinstyle="round",
            )

        # Pontos
        for i, (x, y) in enumerate(coords):
            v = pts[i]
            dot = (D["dot_bad"] if v < 2.5 else
                   D["dot_warn"] if v < 3.5 else D["dot_good"])
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
                    font=("Segoe UI", 8), fill=D["text_muted"],
                )

        # Legenda no canto
        legend = [("● Bom", D["dot_good"]), ("● Atenção", D["dot_warn"]), ("● Baixo", D["dot_bad"])]
        lx = cw - mx - 4
        for j, (lbl, lcolor) in enumerate(reversed(legend)):
            self.canvas.create_text(
                lx, my + 12 + j * 14, text=lbl,
                font=("Segoe UI", 8), fill=lcolor, anchor="e",
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
        return DashboardFrame._humor_emoji.__func__(None, media)
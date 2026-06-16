import customtkinter as ctk
import threading
from services.dashboard import ServicoDashboard
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    SectionHeader,
    Card,
    KPICard,
    PrimaryButton,
    GhostButton,
    Badge,
    EmptyState,
    Divider,
    blend_color,
)


class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_dashboard = ServicoDashboard()
        self.grid_columnconfigure(0, weight=1)

        self.criar_cabecalho()

        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=SPACING["page_x"], pady=(10, SPACING["section_gap"]))

        self.criar_grid_principal()
        self.load_data()

    def load_data(self):
        def fetch():
            data = self.servico_dashboard.obter_kpis()
            self.after(0, lambda: self.update_dashboard(data))
            self.after(0, lambda: self.atualizar_badge_notificacoes())

        threading.Thread(target=fetch, daemon=True).start()

    def update_dashboard(self, data):
        for widget in self.kpi_container.winfo_children():
            widget.destroy()

        media_humor = data.get("media_humor")
        humor_emoji = self.get_humor_emoji(media_humor)

        kpis = [
            {"titulo": "Atendimentos do Dia", "valor": str(data.get("appointments_today", 0)), "icone": "👥", "cor": "#6366F1", "trend": "Hoje"},
            {"titulo": "Vagas Disponíveis", "valor": str(data.get("available_slots", 0)), "icone": "📅", "cor": "#10B981", "trend": "Slots livres"},
            {"titulo": "Alertas Ativos", "valor": str(data.get("alerts", 0)), "icone": "🔔", "cor": "#EF4444", "trend": "Requer ação"},
            {"titulo": "Total de Estudantes", "valor": str(data.get("total_students", 0)), "icone": "👥", "cor": "#8B5CF6", "trend": "Cadastrados"},
            {"titulo": "Humor Médio (Hoje)", "valor": humor_emoji, "icone": humor_emoji, "cor": "#F59E0B", "trend": "Média"},
        ]

        for i, kpi in enumerate(kpis):
            self.kpi_container.grid_columnconfigure(i, weight=1)
            KPICard(
                self.kpi_container,
                title=kpi["titulo"],
                value=kpi["valor"],
                icon=kpi["icone"],
                accent=kpi["cor"],
                trend=kpi.get("trend", ""),
            ).grid(row=0, column=i, sticky="ew", padx=8)

        # Atualizar próximos atendimentos
        agenda_card = self.criar_container_card(self.left_col, "Próximos Atendimentos", "Ver agenda completa →")
        for widget in agenda_card.body.winfo_children():
            widget.destroy()

        appointments = data.get("upcoming_appointments", [])
        if appointments:
            for appt in appointments:
                self.render_agenda_item(agenda_card.body, appt)
        else:
            self.render_empty_agenda(agenda_card.body)

        # Atualizar estudantes em alerta
        alerts_card = self.criar_container_card(self.right_col, "Estudantes em Alerta")
        for widget in alerts_card.body.winfo_children():
            widget.destroy()

        attention_students = data.get("attention_students", [])
        if attention_students:
            for student in attention_students:
                self.render_alerta_item(alerts_card.body, student)
        else:
            self.render_empty_alerts(alerts_card.body)

        # Atualizar bem-estar por dimensão
        bem_estar_card = self.criar_container_card(self.right_col, "❤ Bem-Estar por Dimensão")
        for widget in bem_estar_card.body.winfo_children():
            widget.destroy()

        bem_estar = data.get("bem_estar_dimensions", {})
        self.criar_dimensao_progresso(bem_estar_card.body, "📁 Acadêmico", bem_estar.get("academico", 0) / 5)
        self.criar_dimensao_progresso(bem_estar_card.body, "❤ Emocional", bem_estar.get("emocional", 0) / 5)
        self.criar_dimensao_progresso(bem_estar_card.body, "👥 Social", bem_estar.get("social", 0) / 5)

        # Atualizar gráfico de humor
        humor_history = data.get("humor_history", [])
        if humor_history:
            self.draw_chart(humor_history)
            for widget in self.stats_side.winfo_children():
                widget.destroy()

            total = sum(item["media_humor"] for item in humor_history)
            media_geral = round(total / len(humor_history), 2) if humor_history else 0
            self.criar_indicator_footer(self.stats_side, self.get_humor_emoji(media_geral), "Média Geral", f"{media_geral}/5")
            ctk.CTkFrame(self.stats_side, fg_color=THEME["border"], height=1).pack(pady=12, fill="x")
            self.criar_indicator_footer(self.stats_side, "📋", "Registros", str(len(humor_history)))
        else:
            self.draw_chart()

    def get_humor_emoji(self, media_humor):
        if media_humor is None:
            return "😐"
        if media_humor < 2.0:
            return "😢"
        elif media_humor < 3.0:
            return "😕"
        elif media_humor < 4.0:
            return "😊"
        else:
            return "😄"

    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], SPACING["section_gap"]))
        ctk.CTkLabel(header, text="Dashboard Central", font=themed_font("h1", "bold"), text_color=THEME["text"]).pack(side="left")

        r_tools = ctk.CTkFrame(header, fg_color="transparent")
        r_tools.pack(side="right")

        help_f = ctk.CTkFrame(r_tools, fg_color="transparent", width=44, height=44, cursor="hand2")
        help_f.pack(side="left", padx=8)
        help_f.bind("<Button-1>", lambda e: self.abrir_notificacoes_ajuda())
        ctk.CTkLabel(help_f, text="🤝", font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")
        self.help_badge = Badge(help_f, text="0")
        self.help_badge.place(x=24, y=4)

        alert_f = ctk.CTkFrame(r_tools, fg_color="transparent", width=44, height=44, cursor="hand2")
        alert_f.pack(side="left", padx=8)
        alert_f.bind("<Button-1>", lambda e: self.abrir_notificacoes_alertas())
        ctk.CTkLabel(alert_f, text="🔔", font=themed_font("h3"), text_color=THEME["text_secondary"]).place(relx=0.5, rely=0.5, anchor="center")
        self.alert_badge = Badge(alert_f, text="0")
        self.alert_badge.place(x=24, y=4)

        profile_f = ctk.CTkFrame(r_tools, fg_color="transparent", width=44, height=44, cursor="hand2")
        profile_f.pack(side="left", padx=8)
        profile_f.bind("<Button-1>", lambda e: self.abrir_perfil())
        ctk.CTkLabel(profile_f, text="👤", font=themed_font("h3"), text_color=THEME["text_secondary"]).place(relx=0.5, rely=0.5, anchor="center")

        logout_f = ctk.CTkFrame(r_tools, fg_color="transparent", width=44, height=44, cursor="hand2")
        logout_f.pack(side="left", padx=8)
        logout_f.bind("<Button-1>", lambda e: self.fazer_logout())
        ctk.CTkLabel(logout_f, text="🚪", font=themed_font("h3"), text_color=THEME["text_secondary"]).place(relx=0.5, rely=0.5, anchor="center")

    def criar_grid_principal(self):
        main_grid = ctk.CTkFrame(self, fg_color="transparent")
        main_grid.pack(fill="x", padx=SPACING["page_x"], pady=10)
        main_grid.grid_columnconfigure(0, weight=2)
        main_grid.grid_columnconfigure(1, weight=1)

        self.left_col = ctk.CTkFrame(main_grid, fg_color="transparent")
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        chart_card = self.criar_container_card(self.left_col, "📈 Humor dos Estudantes (30 dias)")
        chart_layout = ctk.CTkFrame(chart_card.body, fg_color="transparent")
        chart_layout.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        chart_layout.grid_columnconfigure(0, weight=1)
        chart_layout.grid_columnconfigure(1, weight=0)

        self.canvas = ctk.CTkCanvas(chart_layout.body if hasattr(chart_layout, "body") else chart_layout, bg="white", height=260, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.stats_side = ctk.CTkFrame(chart_layout, fg_color="transparent")
        self.stats_side.grid(row=0, column=1, sticky="ns", padx=(20, 0))

        chart_card.body.bind("<Configure>", lambda e: self.draw_chart())

        self.right_col = ctk.CTkFrame(main_grid, fg_color="transparent")
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

    def criar_container_card(self, parent, titulo, link_txt=None) -> Card:
        card = Card(parent, title=titulo)
        card.pack(fill="x", pady=(0, SPACING["section_gap"]))
        if link_txt:
            header = card.body.winfo_children()[0].master if card.body.winfo_children() else None
            if header:
                link_lbl = ctk.CTkLabel(header, text=link_txt, font=themed_font("caption"), text_color=THEME["primary"], cursor="hand2")
                link_lbl.pack(side="right")
        return card

    def criar_indicator_footer(self, parent, icon, label, val):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(pady=10)
        ctk.CTkLabel(f, text=icon, font=themed_font("h3")).pack()
        ctk.CTkLabel(f, text=label, font=themed_font("overline"), text_color=THEME["text_muted"]).pack()
        ctk.CTkLabel(f, text=val, font=themed_font("body", "bold"), text_color=THEME["text"]).pack()

    def criar_dimensao_progresso(self, parent, nome, valor):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=8)
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text=nome, font=themed_font("body"), text_color=THEME["text"]).pack(side="left")
        ctk.CTkLabel(header, text=f"{int(valor * 100)}%", font=themed_font("body", "bold"), text_color=THEME["text_muted"]).pack(side="right")

        prog = ctk.CTkProgressBar(container, height=6, progress_color=THEME["primary"], fg_color=THEME["bg_alt"])
        prog.pack(fill="x", pady=(8, 0))
        prog.set(valor)

    def render_agenda_item(self, parent, appt):
        row = ctk.CTkFrame(parent, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"])
        row.pack(fill="x", pady=5)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=18, pady=14)
        ctk.CTkLabel(info, text=appt["student_name"], font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(info, text=f"🎓 {appt['curso']}", font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(row, text=f"🕒 {appt['time']}", font=themed_font("body", "bold"), text_color=THEME["primary"]).pack(side="right", padx=18)

    def render_empty_agenda(self, parent):
        EmptyState(parent, icon="📅", title="Nenhum atendimento próximo", subtitle="Não há agendamentos futuros").pack(pady=10)

    def render_alerta_item(self, parent, student):
        row = ctk.CTkFrame(parent, fg_color=THEME["danger_soft"], corner_radius=RADIUS["md"])
        row.pack(fill="x", pady=5)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=18, pady=14)
        ctk.CTkLabel(info, text=student["name"], font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(info, text=student["attention_reason"], font=themed_font("overline"), text_color=THEME["danger_strong"]).pack(anchor="w", pady=(2, 0))
        priority = student.get("priority_level", 0)
        priority_icon = "🔴" if priority >= 2 else "🟠" if priority == 1 else "🟡"
        ctk.CTkLabel(row, text=priority_icon, font=themed_font("body", "bold")).pack(side="right", padx=18)

    def render_empty_alerts(self, parent):
        EmptyState(parent, icon="✔", title="Nenhum alerta no momento", subtitle="Todos os estudantes estão bem acompanhados").pack(pady=10)

    def draw_chart(self, humor_history=None):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50:
            return

        if humor_history is None or not humor_history:
            pts = [2.8, 3.1, 2.9, 3.2, 2.7, 3.5, 3.2, 2.9, 3.0, 3.8, 3.4, 3.6, 3.2, 3.1, 3.9]
            dates = ["05/01", "07/01", "09/01", "11/01", "13/01", "15/01", "17/01", "19/01", "21/01", "23/01", "25/01", "27/01", "28/01", "29/01", "30/01"]
        else:
            pts = [item["media_humor"] for item in humor_history]
            dates = [item["data"] for item in humor_history]

            if len(pts) < 2:
                pts = [pts[0], pts[0]]
                dates = [dates[0], dates[0]]

        margin_x, margin_y = 36, 36
        chart_w, chart_h = w - 2 * margin_x, h - 2 * margin_y

        coords = []
        for i, v in enumerate(pts):
            x = margin_x + (i * chart_w / (len(pts) - 1))
            y = (h - margin_y) - ((v - 1) * chart_h / 4)
            coords.append((x, y))

        # Grid horizontal
        for i in range(5):
            gy = margin_y + (i * chart_h / 4)
            self.canvas.create_line(margin_x, gy, w - margin_x, gy, fill=THEME["border"])

        # Linha principal
        for i in range(len(coords) - 1):
            self.canvas.create_line(coords[i], coords[i + 1], fill=THEME["primary"], width=2, smooth=True)

        # Pontos
        for i, (x, y) in enumerate(coords):
            val = pts[i]
            dot_color = THEME["danger"] if val < 2.5 else THEME["warning"] if val < 3.5 else THEME["success"]
            self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=dot_color, outline="white", width=1)
            if i % 2 == 0:
                self.canvas.create_text(x, h - 12, text=dates[i], font=("Inter", 8), fill=THEME["text_muted"])

    def abrir_notificacoes_ajuda(self):
        notificacoes = self.servico_dashboard.obter_notificacoes_ajuda()

        modal = ctk.CTkToplevel(self)
        modal.title("Notificações de Ajuda")
        modal.geometry("520x420")
        modal.resizable(False, False)
        modal.configure(fg_color=THEME["card"])
        modal.attributes("-topmost", True)

        modal.update_idletasks()
        width = modal.winfo_width()
        height = modal.winfo_height()
        x = (modal.winfo_screenwidth() // 2) - (width // 2)
        y = (modal.winfo_screenheight() // 2) - (height // 2)
        modal.geometry(f"{width}x{height}+{x}+{y}")

        header = ctk.CTkFrame(modal, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(header, text="Notificações de Ajuda", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")
        ctk.CTkButton(header, text="Marcar todas como lidas", font=themed_font("overline"), width=150, height=32, command=lambda: self.marcar_todas_como_lidas(modal, "ajuda")).pack(side="right")

        list_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=24, pady=10)

        if not notificacoes:
            EmptyState(list_frame, icon="📭", title="Sem notificações de ajuda", subtitle="Tudo certo por aqui").pack(pady=30)
        else:
            for notif in notificacoes:
                self.criar_item_notificacao(list_frame, notif, "ajuda")

        self.atualizar_badge_notificacoes()

    def abrir_notificacoes_alertas(self):
        notificacoes = self.servico_dashboard.obter_notificacoes_alertas()

        modal = ctk.CTkToplevel(self)
        modal.title("Notificações de Alertas")
        modal.geometry("520x420")
        modal.resizable(False, False)
        modal.configure(fg_color=THEME["card"])
        modal.attributes("-topmost", True)

        modal.update_idletasks()
        width = modal.winfo_width()
        height = modal.winfo_height()
        x = (modal.winfo_screenwidth() // 2) - (width // 2)
        y = (modal.winfo_screenheight() // 2) - (height // 2)
        modal.geometry(f"{width}x{height}+{x}+{y}")

        header = ctk.CTkFrame(modal, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(header, text="Notificações de Alertas", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")
        ctk.CTkButton(header, text="Marcar todas como lidas", font=themed_font("overline"), width=150, height=32, command=lambda: self.marcar_todas_como_lidas(modal, "alerta")).pack(side="right")

        list_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=24, pady=10)

        if not notificacoes:
            EmptyState(list_frame, icon="🔔", title="Sem alertas no momento", subtitle="Tudo sob controle").pack(pady=30)
        else:
            for notif in notificacoes:
                self.criar_item_notificacao(list_frame, notif, "alerta")

        self.atualizar_badge_notificacoes()

    def abrir_perfil(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Perfil do Usuário")
        modal.geometry("420x340")
        modal.resizable(False, False)
        modal.configure(fg_color=THEME["card"])
        modal.attributes("-topmost", True)

        modal.update_idletasks()
        width = modal.winfo_width()
        height = modal.winfo_height()
        x = (modal.winfo_screenwidth() // 2) - (width // 2)
        y = (modal.winfo_screenheight() // 2) - (height // 2)
        modal.geometry(f"{width}x{height}+{x}+{y}")

        user_data = self.controller.usuario_logado
        if user_data:
            ctk.CTkLabel(modal, text="👤", font=themed_font("h1")).pack(pady=(24, 10))
            ctk.CTkLabel(modal, text=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or user_data.get('username', 'Usuário'), font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(pady=4)
            ctk.CTkLabel(modal, text=user_data.get("email", ""), font=themed_font("body"), text_color=THEME["text_muted"]).pack(pady=(0, 12))

            Divider(modal).pack(fill="x", padx=24, pady=8)
            info_frame = ctk.CTkFrame(modal, fg_color="transparent")
            info_frame.pack(fill="x", padx=24)
            ctk.CTkLabel(info_frame, text="Nome de usuário:", font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=user_data.get("username", ""), font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(2, 10))
            ctk.CTkLabel(info_frame, text="Tipo de usuário:", font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(0, 0))
            ctk.CTkLabel(info_frame, text="Analista Escolar", font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(2, 0))

        PrimaryButton(modal, text="Editar Perfil", command=lambda: self.editar_perfil(), width=180).pack(pady=(20, 12))

    def fazer_logout(self):
        from tkinter import messagebox
        if messagebox.askyesno("Logout", "Deseja realmente sair do sistema?"):
            self.controller.mostrar_login()

    def editar_perfil(self):
        print("Editar perfil")

    def criar_item_notificacao(self, parent, notif, tipo):
        item_frame = Card(parent)
        item_frame.pack(fill="x", pady=6, padx=4)

        icon_text = "🤝" if tipo == "ajuda" else "🔔"
        icon_color = THEME["primary"] if tipo == "ajuda" else THEME["danger"]

        icon_bg = ctk.CTkFrame(item_frame.body, fg_color=icon_color, width=32, height=32, corner_radius=RADIUS["sm"])
        icon_bg.pack(side="left", padx=(0, 12))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon_text, font=themed_font("body")).place(relx=0.5, rely=0.5, anchor="center")

        text_frame = ctk.CTkFrame(item_frame.body, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(text_frame, text=notif["titulo"], font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=notif["descricao"], font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(text_frame, text=notif["data"], font=themed_font("overline"), text_color=THEME["text_disabled"]).pack(anchor="w", pady=(2, 0))

        item_frame.bind("<Button-1>", lambda e: self.marcar_notificacao_como_lida(notif["id"], tipo))

    def marcar_notificacao_como_lida(self, notif_id, tipo):
        self.servico_dashboard.marcar_notificacao_como_lida(notif_id, tipo)
        self.atualizar_badge_notificacoes()

    def marcar_todas_como_lidas(self, modal, tipo):
        notificacoes = self.servico_dashboard.obter_notificacoes_ajuda() if tipo == "ajuda" else self.servico_dashboard.obter_notificacoes_alertas()
        for notif in notificacoes:
            self.servico_dashboard.marcar_notificacao_como_lida(notif["id"], tipo)

        modal.destroy()
        self.atualizar_badge_notificacoes()

    def atualizar_badge_notificacoes(self):
        ajuda_notificacoes = self.servico_dashboard.obter_notificacoes_ajuda()
        alertas_notificacoes = self.servico_dashboard.obter_notificacoes_alertas()

        ajuda_count = sum(1 for notif in ajuda_notificacoes if not notif["lida"])
        alertas_count = sum(1 for notif in alertas_notificacoes if not notif["lida"])

        self.help_badge.configure(text=str(ajuda_count) if ajuda_count > 0 else "0")
        self.alert_badge.configure(text=str(alertas_count) if alertas_count > 0 else "0")

        self.help_badge.place_forget()
        self.alert_badge.place_forget()

        if ajuda_count > 0:
            self.help_badge.place(x=24, y=4)
        if alertas_count > 0:
            self.alert_badge.place(x=24, y=4)

import customtkinter as ctk
import threading
from services.dashboard import ServicoDashboard
from ui_theme import THEME, SPACING, RADIUS, font, themed_font, blend_color, lighten
from components.ui_components import (
    PageHeader, SectionHeader, Card, KPICard, EmptyState,
    PrimaryButton, GhostButton, Badge, Pill, Divider
)
from components.ui_components import Avatar, MetricCard, ListCard, SkeletonLoader, Toast


class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_dashboard = ServicoDashboard()
        self.grid_columnconfigure(0, weight=1)

        self.criar_cabecalho()
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=SPACING["page_x"], pady=(16, SPACING["section_gap"]))

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
            {"titulo": "Atendimentos do Dia", "valor": str(data.get("appointments_today", 0)),
             "icone": "👥", "cor": THEME["primary"], "trend": "Hoje", "unit": ""},
            {"titulo": "Vagas Disponíveis", "valor": str(data.get("available_slots", 0)),
             "icone": "📅", "cor": THEME["success"], "trend": "Slots livres", "unit": ""},
            {"titulo": "Alertas Ativos", "valor": str(data.get("alerts", 0)),
             "icone": "🔔", "cor": THEME["danger"], "trend": "Requer ação", "unit": ""},
            {"titulo": "Total de Estudantes", "valor": str(data.get("total_students", 0)),
             "icone": "👥", "cor": THEME["accent"], "trend": "Cadastrados", "unit": ""},
            {"titulo": "Humor Médio", "valor": f"{media_humor:.1f}" if media_humor else "—",
             "icone": humor_emoji, "cor": THEME["warning"], "trend": "Média", "unit": "/ 5"},
        ]

        for i, kpi in enumerate(kpis):
            self.kpi_container.grid_columnconfigure(i, weight=1)
            KPICard(self.kpi_container, title=kpi["titulo"], value=kpi["valor"],
                    icon=kpi["icone"], accent=kpi["cor"], trend=kpi.get("trend", ""),
                    unit=kpi.get("unit", ""), size="default" if i < 3 else "compact").grid(
                row=0, column=i, sticky="ew", padx=6
            )

        agenda_card = self.criar_container_card(self.left_col, "📅  Próximos Atendimentos", "Ver agenda completa →")
        for widget in agenda_card.body.winfo_children():
            widget.destroy()

        appointments = data.get("upcoming_appointments", [])
        if appointments:
            for appt in appointments:
                self.render_agenda_item(agenda_card.body, appt)
        else:
            self.render_empty_agenda(agenda_card.body)

        alerts_card = self.criar_container_card(self.right_col, "🔔  Estudantes em Alerta", status="Alerta")
        for widget in alerts_card.body.winfo_children():
            widget.destroy()

        attention_students = data.get("attention_students", [])
        if attention_students:
            for student in attention_students:
                self.render_alerta_item(alerts_card.body, student)
        else:
            self.render_empty_alerts(alerts_card.body)

        bem_estar_card = self.criar_container_card(self.right_col, "❤  Bem-Estar por Dimensão")
        for widget in bem_estar_card.body.winfo_children():
            widget.destroy()

        bem_estar = data.get("bem_estar_dimensions", {})
        rows = [
            ("📁  Acadêmico", bem_estar.get("academico", 0) / 5, THEME["primary"]),
            ("❤  Emocional", bem_estar.get("emocional", 0) / 5, THEME["danger"]),
            ("👥  Social", bem_estar.get("social", 0) / 5, THEME["success"]),
        ]
        for nome, val, color in rows:
            self.criar_dimensao_progresso(bem_estar_card.body, nome, val, color)

        humor_history = data.get("humor_history", [])
        if humor_history:
            self.draw_chart(humor_history)
            for widget in self.stats_side.winfo_children():
                widget.destroy()

            total = sum(item["media_humor"] for item in humor_history)
            media_geral = round(total / len(humor_history), 2) if humor_history else 0
            self.criar_indicator_footer(self.stats_side,
                                        self.get_humor_emoji(media_geral), "Média Geral", f"{media_geral}/5")
        else:
            self.draw_chart()

    def criar_cabecalho(self):
        header = PageHeader(
            self, title="Dashboard Central",
            subtitle="Visão geral do acompanhamento discente",
            show_breadcrumb=True, breadcrumb_parts=["Início", "Dashboard"],
        )
        header.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["section_gap"]))

        icons_frame = ctk.CTkFrame(header, fg_color="transparent")
        icons_frame.pack(side="right", padx=(0, 14))

        help_f = ctk.CTkFrame(icons_frame, fg_color="transparent", width=40, height=40, cursor="hand2")
        help_f.pack(side="left", padx=6)
        help_f.bind("<Button-1>", lambda e: self.abrir_notificacoes_ajuda())
        ctk.CTkLabel(help_f, text="🤝", font=themed_font("h3")).place(relx=0.5, rely=0.5, anchor="center")
        self.help_badge = Badge(help_f, text="0")
        self.help_badge.place(x=24, y=2)

        alert_f = ctk.CTkFrame(icons_frame, fg_color="transparent", width=40, height=40, cursor="hand2")
        alert_f.pack(side="left", padx=6)
        alert_f.bind("<Button-1>", lambda e: self.abrir_notificacoes_alertas())
        ctk.CTkLabel(alert_f, text="🔔", font=themed_font("h3"), text_color=THEME["text_secondary"]).place(relx=0.5, rely=0.5, anchor="center")
        self.alert_badge = Badge(alert_f, text="0")
        self.alert_badge.place(x=24, y=2)

        profile_f = ctk.CTkFrame(icons_frame, fg_color="transparent", width=40, height=40, cursor="hand2")
        profile_f.pack(side="left", padx=6)
        profile_f.bind("<Button-1>", lambda e: self.abrir_perfil())

        name = ""
        if self.controller.usuario_logado:
            name = self.controller.usuario_logado.get("username", "?")[:2].upper()
        Avatar(profile_f, initials=name, size=36)

        logout_f = ctk.CTkFrame(icons_frame, fg_color="transparent", width=40, height=40, cursor="hand2")
        logout_f.pack(side="left", padx=6)
        logout_f.bind("<Button-1>", lambda e: self.fazer_logout())
        ctk.CTkLabel(logout_f, text="🚪", font=themed_font("h3"), text_color=THEME["text_secondary"]).place(relx=0.5, rely=0.5, anchor="center")

    def criar_grid_principal(self):
        main_grid = ctk.CTkFrame(self, fg_color="transparent")
        main_grid.pack(fill="x", padx=SPACING["page_x"], pady=10)
        main_grid.grid_columnconfigure(0, weight=3)
        main_grid.grid_columnconfigure(1, weight=2)

        self.left_col = ctk.CTkFrame(main_grid, fg_color="transparent")
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 16))

        chart_card = self.criar_container_card(self.left_col, "📈  Humor dos Estudantes (30 dias)")
        chart_layout = ctk.CTkFrame(chart_card.body, fg_color="transparent")
        chart_layout.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = ctk.CTkCanvas(chart_layout, bg=THEME["surface"], height=260, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.stats_side = ctk.CTkFrame(chart_layout, fg_color="transparent")
        self.stats_side.pack_forget()

        chart_card.body.bind("<Configure>", lambda e: self.draw_chart())

        self.right_col = ctk.CTkFrame(main_grid, fg_color="transparent")
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

    def criar_container_card(self, parent, titulo, link_txt=None, status=None) -> Card:
        card = Card(parent, title=titulo, status=status)
        card.pack(fill="x", pady=(0, SPACING["section_gap"]))
        if link_txt:
            first = card.body.winfo_children()[0] if card.body.winfo_children() else None
            if first:
                h = first.master if hasattr(first, "master") and isinstance(first.master, ctk.CTkFrame) else card.body
                link_lbl = ctk.CTkLabel(h, text=link_txt, font=themed_font("caption"), text_color=THEME["primary"], cursor="hand2")
                link_lbl.pack(side="right")
        return card

    def criar_indicator_footer(self, parent, icon, label, val):
        ctk.CTkLabel(parent, text=icon, font=themed_font("h3")).pack()
        ctk.CTkLabel(parent, text=label, font=themed_font("overline"), text_color=THEME["text_muted"]).pack()
        ctk.CTkLabel(parent, text=val, font=themed_font("body", "bold"), text_color=THEME["text"]).pack()

    def criar_dimensao_progresso(self, parent, nome, valor, color):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=10)
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(header, text=nome, font=themed_font("body_sm"), text_color=THEME["text"]).pack(side="left")
        ctk.CTkLabel(header, text=f"{int(valor * 100)}%", font=themed_font("body_sm", "bold"), text_color=color).pack(side="right")

        prog = ctk.CTkProgressBar(container, height=6, progress_color=color, fg_color=THEME["bg_alt"], corner_radius=RADIUS["pill"])
        prog.pack(fill="x", pady=(4, 0))
        prog.set(valor)

    def render_agenda_item(self, parent, appt):
        row = ctk.CTkFrame(parent, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"])
        row.pack(fill="x", pady=5)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=18, pady=14)
        ctk.CTkLabel(info, text=appt["student_name"], font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(info, text=f"🎓  {appt.get('curso', '')}", font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(row, text=f"🕒  {appt.get('time', '')}", font=themed_font("body", "bold"), text_color=THEME["primary"]).pack(side="right", padx=18)

    def render_empty_agenda(self, parent):
        EmptyState(parent, icon="📅", title="Nenhum atendimento próximo",
                   subtitle="Não há agendamentos futuros").pack(pady=10)

    def render_alerta_item(self, parent, student):
        row = ctk.CTkFrame(parent, fg_color=THEME["danger_soft"], corner_radius=RADIUS["md"])
        row.pack(fill="x", pady=5)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=18, pady=14)
        ctk.CTkLabel(info, text=student.get("name", "?"), font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(info, text=student.get("attention_reason", ""), font=themed_font("body_sm"), text_color=THEME["danger_strong"]).pack(anchor="w", pady=(2, 0))
        priority = student.get("priority_level", 0)
        icon_pri = {0: "🟡", 1: "🟠", 2: "🔴"}.get(priority, "🟡")
        ctk.CTkLabel(row, text=icon_pri, font=themed_font("h3")).pack(side="right", padx=18)

    def render_empty_alerts(self, parent):
        EmptyState(parent, icon="✔", title="Tudo sob controle",
                   subtitle="Nenhum estudante em alerta no momento").pack(pady=10)

    def draw_chart(self, humor_history=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 80 or h < 80:
            return

        if humor_history is None or not humor_history:
            pts = [2.8, 3.1, 2.9, 3.2, 2.7, 3.5, 3.2, 2.9, 3.0, 3.8, 3.4, 3.6, 3.2, 3.1, 3.9]
            dates = ["05/01", "07/01", "09/01", "11/01", "13/01", "15/01", "17/01", "19/01",
                     "21/01", "23/01", "25/01", "27/01", "28/01", "29/01", "30/01"]
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

        self.canvas.create_rectangle(margin_x, margin_y, w - margin_x, h - margin_y,
                                     fill=THEME["surface"], outline=THEME["border"])

        for i in range(5):
            gy = margin_y + (i * chart_h / 4)
            self.canvas.create_line(margin_x, gy, w - margin_x, gy, fill=THEME["border"], dash=(3, 4))

        for i, (x, y) in enumerate(coords[:-1]):
            nx, ny = coords[i + 1]
            color = THEME["primary"]
            self.canvas.create_line(x, y, nx, ny, fill=color, width=2, capstyle="round", joinstyle="round")

            self.canvas.create_polygon(x, y, nx, ny, nx, h - margin_y, x, h - margin_y,
                                       fill=blend_color(THEME["primary"], 0.08), outline="")

        for i, (x, y) in enumerate(coords):
            val = pts[i]
            dot_color = THEME["danger"] if val < 2.5 else THEME["warning"] if val < 3.5 else THEME["success"]
            self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill=dot_color, outline=THEME["surface"], width=2)

        for i, (x, y) in enumerate(coords):
            if i % max(1, len(coords) // 7) == 0:
                self.canvas.create_text(x, h - 8, text=dates[i], font=("Inter", 8), fill=THEME["text_muted"])

    def abrir_notificacoes_ajuda(self):
        notificacoes = self.servico_dashboard.obter_notificacoes_ajuda()
        self._mostrar_notificacoes("Notificações de Ajuda", notificacoes, "ajuda", THEME["info"])

    def abrir_notificacoes_alertas(self):
        notificacoes = self.servico_dashboard.obter_notificacoes_alertas()
        self._mostrar_notificacoes("Notificações de Alertas", notificacoes, "alerta", THEME["danger"])

    def _mostrar_notificacoes(self, titulo, notificacoes, tipo, color=THEME["primary"]):
        modal = ctk.CTkToplevel(self)
        modal.title(titulo)
        modal.geometry("540x460")
        modal.resizable(False, False)
        modal.configure(fg_color=THEME["surface"])
        modal.attributes("-topmost", True)
        modal.transient(self.winfo_toplevel())

        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - 270
        y = (modal.winfo_screenheight() // 2) - 230
        modal.geometry(f"540x460+{x}+{y}")

        header = ctk.CTkFrame(modal, fg_color=THEME["bg"])
        header.pack(fill="x", padx=24, pady=(18, 0))
        ctk.CTkLabel(header, text=titulo, font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")
        GhostButton(header, text="Marcar todas como lidas",
                    command=lambda: self.marcar_todas_como_lidas(modal, tipo), width=160).pack(side="right")

        list_frame = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=24, pady=16)

        if not notificacoes:
            EmptyState(list_frame, icon="📭", title="Sem alertas",
                       subtitle=f"Nenhuma notificação de {tipo} no momento").pack(pady=36)
        else:
            for notif in notificacoes:
                self.criar_item_notificacao(list_frame, notif, tipo)

        self.atualizar_badge_notificacoes()

    def criar_item_notificacao(self, parent, notif, tipo):
        item_frame = Card(parent)
        item_frame.pack(fill="x", pady=6, padx=4)

        icon_text = "🤝" if tipo == "ajuda" else "🔔"
        icon_color = THEME["info"] if tipo == "ajuda" else THEME["danger"]

        icon_bg = ctk.CTkFrame(item_frame.body, fg_color=blend_color(icon_color, 0.12),
                               width=34, height=34, corner_radius=RADIUS["sm"])
        icon_bg.pack(side="left", padx=(0, 12))
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text=icon_text, font=themed_font("body")).place(relx=0.5, rely=0.5, anchor="center")

        text_frame = ctk.CTkFrame(item_frame.body, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(text_frame, text=notif.get("titulo", ""), font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(text_frame, text=notif.get("descricao", ""), font=themed_font("body_sm"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(text_frame, text=notif.get("data", ""), font=themed_font("overline"), text_color=THEME["text_disabled"]).pack(anchor="w", pady=(3, 0))

        item_frame.bind("<Button-1>", lambda e, nid=notif["id"], t=tipo: self.marcar_notificacao_como_lida(nid, t))

    def abrir_perfil(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Perfil do Usuário")
        modal.geometry("440x360")
        modal.resizable(False, False)
        modal.configure(fg_color=THEME["surface"])
        modal.attributes("-topmost", True)
        modal.transient(self.winfo_toplevel())

        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - 220
        y = (modal.winfo_screenheight() // 2) - 180
        modal.geometry(f"440x360+{x}+{y}")

        user_data = self.controller.usuario_logado
        if user_data:
            top = ctk.CTkFrame(modal, fg_color="transparent")
            top.pack(fill="x", padx=24, pady=(24, 12))
            initials = ((user_data.get("first_name", "") or "")[0:1] + (user_data.get("last_name", "") or "")[0:1]).upper() or user_data.get("username", "?")[:2].upper()
            Avatar(top, initials=initials, size=56, color=THEME["primary"]).pack(side="left", padx=(0, 14))

            info = ctk.CTkFrame(top, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True)
            nome = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or user_data.get("username", "Usuário")
            ctk.CTkLabel(info, text=nome, font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(anchor="w")
            email = user_data.get("email", "")
            ctk.CTkLabel(info, text=email, font=themed_font("body"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))
            Pill(info, text="Analista Escolar", color=THEME["primary_soft"], text_color=THEME["primary"]).pack(anchor="w", pady=(6, 0))

        self._profile_info_section(modal, user_data)
        PrimaryButton(modal, text="Editar Perfil", command=self.editar_perfil, width=160).pack(pady=(22, 14))

    def _profile_info_section(self, modal, user_data):
        if not user_data:
            return
        frame = ctk.CTkFrame(modal, fg_color=THEME["bg"], corner_radius=RADIUS["lg"])
        frame.pack(fill="x", padx=24, pady=8)

        self._profile_row(frame, "Nome de usuário", user_data.get("username", ""))
        self._profile_row(frame, "Função", "Analista Escolar")
        self._profile_row(frame, "Módulos", "Dashboard, Estudantes, Agenda, Bem-Estar")

    def _profile_row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(row, text=label, font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(row, text=value, font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(1, 0))

    def editar_perfil(self):
        print("Editar perfil")

    def fazer_logout(self):
        from tkinter import messagebox
        if messagebox.askyesno("Logout", "Deseja realmente sair do SerPleno?"):
            self.controller.mostrar_login()

    def atualizar_badge_notificacoes(self):
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

    def marcar_notificacao_como_lida(self, notif_id, tipo):
        self.servico_dashboard.marcar_notificacao_como_lida(notif_id, tipo)
        self.atualizar_badge_notificacoes()

    def marcar_todas_como_lidas(self, modal, tipo):
        notificacoes = self.servico_dashboard.obter_notificacoes_ajuda() if tipo == "ajuda" else self.servico_dashboard.obter_notificacoes_alertas()
        for notif in notificacoes:
            self.servico_dashboard.marcar_notificacao_como_lida(notif["id"], tipo)
        modal.destroy()
        self.atualizar_badge_notificacoes()

    @staticmethod
    def get_humor_emoji(media_humor):
        if media_humor is None:
            return "😐"
        if media_humor < 2.0:
            return "😢"
        if media_humor < 3.0:
            return "😕"
        if media_humor < 4.0:
            return "😊"
        return "😄"

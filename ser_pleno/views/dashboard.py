import customtkinter as ctk
from datetime import datetime
import threading
from services.dashboard import ServicoDashboard
# Compat alias para testes
DashboardService = ServicoDashboard

from ui_theme import THEME, SPACING, RADIUS, font

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_dashboard = ServicoDashboard()
        
        # Dados de estado
        self.dados_kpis = []

        # Configuração de Layout
        self.grid_columnconfigure(0, weight=1)

        # Cabeçalho
        self.criar_cabecalho()

        # 1. Indicadores (KPIs)
        self.criar_kpis()

        # 2. Conteúdo Principal (Agenda & Alertas)
        self.criar_conteudo_principal()

        # 3. Análise (Gráficos)
        self.criar_analise_bem_estar()

        # Carregar dados
        self.load_data()

    def load_data(self):
        def fetch():
            data = self.servico_dashboard.obter_kpis()
            self.after(0, lambda: self.update_kpis(data))
        
        threading.Thread(target=fetch, daemon=True).start()

    def update_kpis(self, data):
        # Limpar kpis antigos
        for widget in self.kpi_container.winfo_children():
            widget.destroy()
            
        # Grid para distribuir cards uniformente
        count = 5
        for i in range(count):
            self.kpi_container.grid_columnconfigure(i, weight=1)

        # Dados Reais mapeados
        kpis = [
            {"titulo": "Atendimentos do Dia", "valor": str(data.get("appointments_today", 0)), "icone": "👥", "cor_icone": THEME["info"]},
            {"titulo": "Triagens Pendentes", "valor": str(data.get("screenings_pending", 0)), "icone": "📋", "cor_icone": THEME["success"]},
            {"titulo": "Alertas Ativos", "valor": str(data.get("alerts", 0)), "icone": "🔔", "cor_icone": THEME["danger"]},
            {"titulo": "Total de Estudantes", "valor": str(data.get("total_students", "N/A")), "icone": "🎓", "cor_icone": "#8B5CF6"},
            {"titulo": "Taxa Presença", "valor": f"{data.get('attendance_rate', 0)}%", "icone": "📊", "cor_icone": THEME["warning"]}
        ]

        for i, kpi in enumerate(kpis):
            self.criar_card_kpi(self.kpi_container, i, kpi)
            
        # 2. Update Agenda
        if hasattr(self, 'agenda_content'):
             self.update_agenda(data.get("upcoming_appointments", []))

        # 3. Update Alerts
        if hasattr(self, 'alert_content'):
             self.update_alerts(data.get("attention_students", []))

    def update_agenda(self, items):
        for w in self.agenda_content.winfo_children():
            w.destroy()
        
        if not items:
            self.render_empty_agenda()
            return
            
        for appt in items:
            container = ctk.CTkFrame(self.agenda_content, fg_color=THEME["bg_alt"], corner_radius=RADIUS["button"])
            container.pack(fill="x", pady=4, padx=5)
            
            # Faixa lateral
            strip = ctk.CTkFrame(container, width=4, fg_color=THEME["primary"], height=40)
            strip.pack(side="left", padx=(0, 10))
            
            info = ctk.CTkFrame(container, fg_color="transparent")
            info.pack(side="left", pady=8)
            
            nm = appt.get('student_name', 'Estudante')
            tm = appt.get('time', '--:--')
            
            ctk.CTkLabel(info, text=nm, font=font(13, "bold"), text_color=THEME["text"]).pack(anchor="w")
            ctk.CTkLabel(info, text=f"Hoje, {tm}", text_color=THEME["text_muted"], font=font(11)).pack(anchor="w")

    def update_alerts(self, items):
        for w in self.alert_content.winfo_children():
            w.destroy()
        
        if not items:
            self.render_empty_alerts()
            return

        for student in items:
            container = ctk.CTkFrame(self.alert_content, fg_color=THEME["danger_light"], corner_radius=RADIUS["button"]) 
            container.pack(fill="x", pady=4, padx=5)
            
            ctk.CTkLabel(container, text="⚠", text_color=THEME["danger"], font=font(14)).pack(side="left", padx=12)
            
            info = ctk.CTkFrame(container, fg_color="transparent")
            info.pack(side="left", pady=8)
            
            name = student.get('name', 'Estudante')
            reason = student.get('attention_reason') or 'Requer atenção'
            
            ctk.CTkLabel(info, text=name, font=font(13, "bold"), text_color=THEME["text"]).pack(anchor="w")
            ctk.CTkLabel(info, text=reason, text_color=THEME["danger"], font=font(11)).pack(anchor="w")
            
    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 18))
        
        # Título
        titulo = ctk.CTkLabel(
            header, 
            text="Dashboard Central", 
            font=font(24, "bold"),
            text_color=THEME["text"]
        )
        titulo.pack(side="left")

        # Ícones do lado direito
        icons_frame = ctk.CTkFrame(header, fg_color="transparent")
        icons_frame.pack(side="right")

        # 1. Ícone de Apoio (Aperto de mão) com Badge Vermelho "1"
        helper_frame = ctk.CTkFrame(icons_frame, fg_color="transparent", width=45, height=45)
        helper_frame.pack(side="left", padx=2)
        helper_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            helper_frame, 
            text="🤝", 
            font=font(22), 
            text_color=THEME["text_muted"]
        ).place(relx=0.4, rely=0.6, anchor="center")

        badge_1 = ctk.CTkLabel(helper_frame, text="9+", font=font(9, "bold"), text_color="white", fg_color=THEME["danger"], width=16, height=16, corner_radius=8)
        badge_1.place(x=24, y=4)

        # 2. Sino de Notificação
        bell_icon = ctk.CTkLabel(
            icons_frame, 
            text="🔔", 
            font=font(20), 
            text_color=THEME["text_muted"], 
            width=40
        )
        bell_icon.pack(side="left", padx=5)

        # 3. Avatar do Usuário "M"
        avatar_frame = ctk.CTkFrame(icons_frame, fg_color=THEME["bg_alt"], width=42, height=42, corner_radius=21)
        avatar_frame.pack(side="left", padx=8)
        avatar_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            avatar_frame, 
            text="M", 
            font=font(15, "bold"), 
            text_color="#475569"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # 4. Ícone de Logout (Porta/Sair)
        logout_icon = ctk.CTkLabel(
            icons_frame, 
            text="⎗", 
            font=font(22, "bold"), 
            text_color=THEME["text_muted"], 
            width=40
        )
        logout_icon.pack(side="left", padx=2)



    def criar_kpis(self):
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=SPACING["page_x"], pady=10)

        # 5 Colunas
        for i in range(5):
            self.kpi_container.grid_columnconfigure(i, weight=1)

        # Dados iniciais
        kpis = [
            {"titulo": "Atendimentos do Dia", "valor": "5", "icone": "👥", "cor_icone": THEME["info"]},
            {"titulo": "Vagas Disponíveis", "valor": "0", "icone": "📅", "cor_icone": THEME["success"]},
            {"titulo": "Alertas Ativos", "valor": "0", "icone": "🔔", "cor_icone": THEME["danger"]},
            {"titulo": "Total de Estudantes", "valor": "13", "icone": "🎓", "cor_icone": "#8B5CF6"},
            {"titulo": "Humor Médio (Hoje)", "valor": "😊", "icone": "🙂", "cor_icone": THEME["warning"]}
        ]

        for i, kpi in enumerate(kpis):
            self.criar_card_kpi(self.kpi_container, i, kpi)

    def criar_card_kpi(self, parent, col_idx, dados):
        # Card with white bg and rounded corners
        card = ctk.CTkFrame(parent, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        card.grid(row=0, column=col_idx, sticky="ew", padx=6, pady=5)
        
        # Use grid inside card for layout
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)

        # Content (Left)
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        ctk.CTkLabel(
            content_frame,
            text=dados["titulo"],
            font=font(13),
            text_color=THEME["text_muted"],
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            content_frame,
            text=dados["valor"],
            font=font(28, "bold"),
            text_color=THEME["text"],
            anchor="w"
        ).pack(anchor="w", pady=(5, 0))

        # Stylized Icon (Right) - Boxed icon
        # Create a light background for the icon
        icon_bg_color = self.hex_to_rgba(dados["cor_icone"], 0.1) # Fallback to transparent if not possible
        
        icon_container = ctk.CTkFrame(
            card, 
            width=48, height=48, 
            corner_radius=RADIUS["button"], 
            fg_color=THEME["bg_alt"]
        )
        icon_container.grid(row=0, column=1, padx=20, sticky="e")
        icon_container.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_container, 
            text=dados["icone"], 
            font=font(22),
            text_color=dados["cor_icone"]
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

    def hex_to_rgba(self, hex_color, alpha):
        # Helper to create light versions of colors for backgrounds
        hex_color = hex_color.lstrip('#')
        if hex_color == "white": return "white"
        try:
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            # Since CTK doesn't support RGBA in all places easily, 
            # we can return a very light hex color by blending with white
            r = int(r * alpha + 255 * (1 - alpha))
            g = int(g * alpha + 255 * (1 - alpha))
            b = int(b * alpha + 255 * (1 - alpha))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return "#f3f4f6"


    def criar_conteudo_principal(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["page_x"], pady=20)
        
        container.grid_columnconfigure(0, weight=3) # Agenda 
        container.grid_columnconfigure(1, weight=2) # Alertas

        # --- Próximos Atendimentos ---
        agenda_card = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        agenda_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header Agenda
        agenda_header = ctk.CTkFrame(agenda_card, fg_color="transparent")
        agenda_header.pack(fill="x", padx=25, pady=20)
        
        ctk.CTkLabel(
            agenda_header, 
            text="Próximos Atendimentos",
            font=font(16, "bold"),
            text_color=THEME["text"]
        ).pack(side="left")

        ctk.CTkLabel(
            agenda_header,
            text="Ver agenda completa →",
            font=font(13),
            text_color=THEME["primary"],
            cursor="hand2"
        ).pack(side="right")

        # Agenda Content Container (Salvo em self para updates)
        self.agenda_content = ctk.CTkFrame(agenda_card, fg_color="transparent")
        self.agenda_content.pack(fill="both", expand=True, padx=25, pady=(0, 30))

        # --- Estudantes em Alerta ---
        alert_card = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        alert_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        check_header = ctk.CTkFrame(alert_card, fg_color="transparent")
        check_header.pack(fill="x", padx=25, pady=20)

        ctk.CTkLabel(
            check_header,
            text="Estudantes em Alerta",
            font=font(16, "bold"),
            text_color=THEME["text"]
        ).pack(side="left")

        # Alert Content Container (Salvo em self para updates)
        self.alert_content = ctk.CTkFrame(alert_card, fg_color="transparent")
        self.alert_content.pack(fill="both", expand=True, padx=25, pady=(0, 30))

        # Renderizar estados iniciais vazios
        self.render_empty_agenda()
        self.render_empty_alerts()

    def render_empty_agenda(self):
        for w in self.agenda_content.winfo_children(): w.destroy()
        
        icon_circle = ctk.CTkFrame(self.agenda_content, width=80, height=80, corner_radius=40, fg_color=THEME["bg_alt"])
        icon_circle.pack(pady=(20, 15))
        icon_circle.pack_propagate(False)
        
        ctk.CTkLabel(
            icon_circle, text="📅", font=font(32), text_color=THEME["text_highlight"]
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.agenda_content, text="Nenhum agendamento para hoje",
            font=font(14), text_color=THEME["text_muted"]
        ).pack(pady=(0, 15))

        ctk.CTkButton(
            self.agenda_content, text="+ Criar agendamento",
            font=font(14, "bold"),
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"], corner_radius=RADIUS["button"], height=36
        ).pack()

    def render_empty_alerts(self):
        for w in self.alert_content.winfo_children(): w.destroy()
        
        ctk.CTkLabel(
            self.alert_content, text="✔", font=font(32),
            text_color=THEME["text_highlight"], height=60, width=60, corner_radius=30, fg_color=THEME["bg_alt"]
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            self.alert_content, text="Nenhum alerta no momento",
            font=font(14, "bold"), text_color=THEME["text"]
        ).pack()

        ctk.CTkLabel(
            self.alert_content, text="Todos os estudantes estão bem acompanhados",
            font=font(13), text_color=THEME["text_highlight"]
        ).pack()

    def criar_analise_bem_estar(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["page_x"], pady=10)
        
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)

        # --- Chart ---
        chart_card = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header
        chart_header = ctk.CTkFrame(chart_card, fg_color="transparent")
        chart_header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            chart_header, 
            text="📉 Humor dos Estudantes (7 dias)", # Adding icon as text for simplicity
            font=font(16, "bold"),
            text_color=THEME["text"]
        ).pack(side="left")

        # Legend (simplified)
        legend_frame = ctk.CTkFrame(chart_header, fg_color="transparent")
        legend_frame.pack(side="right")
        self.criar_legenda_item(legend_frame, "Bom", THEME["success"])
        self.criar_legenda_item(legend_frame, "Neutro", THEME["warning"])
        self.criar_legenda_item(legend_frame, "Ruim", THEME["danger"])

        # Chart Canvas
        self.chart_frame = ctk.CTkFrame(chart_card, fg_color=THEME["bg_alt"], height=180, corner_radius=0)
        self.chart_frame.pack(fill="x", padx=20, pady=10)
        
        self.canvas = ctk.CTkCanvas(self.chart_frame, bg=THEME["bg_alt"], height=180, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Bind resize event
        self.chart_frame.bind("<Configure>", self.draw_chart)

        # Stats at bottom
        stats_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=40, pady=20)
        
        self.criar_stat_chart(stats_frame, "Média Geral", "3.14/5", "😐")
        self.criar_stat_chart(stats_frame, "Registros", "222", "📋")


        # --- Bem-Estar List ---
        list_card = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        list_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            list_card,
            text="❤ Bem-Estar por Dimensão",
            font=font(16, "bold"),
            text_color=THEME["text"],
            anchor="w"
        ).pack(fill="x", padx=20, pady=20)

        metrics = [
            ("📁 Acadêmico", "--"),
            ("❤ Emocional", "--"),
            ("👥 Social", "--")
        ]
        
        for name, value in metrics:
            row = ctk.CTkFrame(list_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=8)
            
            ctk.CTkLabel(
                row, 
                text=name, 
                text_color=THEME["text_muted"], 
                font=font(13, "bold")
            ).pack(side="left")
            
            # Separator dots (simulated)
            ctk.CTkLabel(
                row, 
                text="." * 40, 
                text_color=THEME["border"],
                font=font(10)
            ).pack(side="left", padx=10, expand=True)

            ctk.CTkLabel(
                row, 
                text=value, 
                text_color=THEME["text_highlight"],
                font=font(13)
            ).pack(side="right")
        
        info_lbl = ctk.CTkLabel(
            list_card, 
            text="Baseado em autoavaliações dos últimos 7 dias", 
            text_color=THEME["text_highlight"], 
            font=font(11)
        )
        info_lbl.pack(side="bottom", pady=25)

    def draw_chart(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w < 100: return 

        # Margins
        pad_x = 50
        pad_y = 30
        
        # Mock Data (7 points)
        data = [3.2, 3.3, 3.6, 3.4, 3.5, 3.8, 4.2] 
        dates = ["12/01", "13/01", "14/01", "15/01", "16/01", "17/01", "18/01"]
        
        # Horizontal Grid Lines
        for i in range(1, 6):
            y = h - pad_y - (i * (h - 2*pad_y) / 5)
            self.canvas.create_line(pad_x, y, w - pad_x, y, fill=THEME["border"], width=1)

        # Calculate Points
        points = []
        for i, val in enumerate(data):
            x = pad_x + (i * (w - 2*pad_x) / (len(data) - 1))
            y = h - pad_y - (val * (h - 2*pad_y) / 5)
            points.append((x, y))
            
            # Draw Date Labels
            self.canvas.create_text(x, h - 15, text=dates[i], fill=THEME["text_highlight"], font=("Segoe UI", 8))

        # 1. Draw "Filled" area (Polygon) - Semi-transparent look
        poly_points = [pad_x, h - pad_y]
        for x, y in points:
            poly_points.extend([x, y])
        poly_points.extend([w - pad_x, h - pad_y])
        
        # Simulating transparency with a very light indigo
        self.canvas.create_polygon(poly_points, fill=THEME["primary_light"], outline="")

        # 2. Draw Smooth Line
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i+1]
            # Custom Line
            self.canvas.create_line(x1, y1, x2, y2, fill=THEME["primary"], width=3, capstyle="round", joinstyle="round")

        # 3. Draw Points with Halo
        for i, (x, y) in enumerate(points):
            # Only draw points for some or all
            color = THEME["primary"]
            if i == len(points) - 1: # Last point highlight
                self.canvas.create_oval(x-5, y-5, x+5, y+5, fill=THEME["primary"], outline="white", width=2)
            else:
                # Color based on value alert
                dot_color = THEME["danger"] if data[i] < 3.0 else THEME["primary"]
                self.canvas.create_oval(x-3, y-3, x+3, y+3, fill=dot_color, outline="white", width=1)


    def criar_legenda_item(self, parent, text, color):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", padx=5)
        ctk.CTkLabel(f, text="●", text_color=color, font=font(10)).pack(side="left")
        ctk.CTkLabel(f, text=text, text_color=THEME["text_muted"], font=font(11)).pack(side="left", padx=2)

    def criar_stat_chart(self, parent, label, value, icon):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", expand=True)

        icon_box = ctk.CTkFrame(f, width=40, height=40, corner_radius=20, fg_color=THEME["bg_alt"])
        icon_box.pack(pady=(0, 5))
        icon_box.pack_propagate(False)

        ctk.CTkLabel(icon_box, text=icon, font=font(18)).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text=label, font=font(12, "bold"), text_color=THEME["text_muted"]).pack()
        ctk.CTkLabel(f, text=value, font=font(18, "bold"), text_color=THEME["text"]).pack()



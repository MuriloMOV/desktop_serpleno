import customtkinter as ctk
from datetime import datetime

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb") # Background light gray/blue
        self.controller = controller

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        # self.grid_rowconfigure(...): rows will stack naturally with pack or grid

        # Header
        self.criar_cabecalho()

        # 1. KPIs
        self.criar_kpis()

        # 2. Main Content (Agenda & Alerts)
        self.criar_conteudo_principal()

        # 3. Analysis (Charts)
        self.criar_analise_bem_estar()

        # 4. Risk View
        self.criar_visao_risco()

    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        # Title
        titulo = ctk.CTkLabel(
            header, 
            text="Dashboard Central", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#1f2937"
        )
        titulo.pack(side="left")

        # Right side icons setup - Identical to ideal.png
        icons_frame = ctk.CTkFrame(header, fg_color="transparent")
        icons_frame.pack(side="right")

        # 1. Helper Icon (Handshake) with Red Badge "1"
        helper_frame = ctk.CTkFrame(icons_frame, fg_color="transparent", width=45, height=45)
        helper_frame.pack(side="left", padx=2)
        helper_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            helper_frame, 
            text="🤝", # Handshake icon
            font=ctk.CTkFont(size=22), 
            text_color="#64748b"
        ).place(relx=0.4, rely=0.6, anchor="center")

        badge_1 = ctk.CTkLabel(
            helper_frame, 
            text="1", 
            font=ctk.CTkFont(size=9, weight="bold"), 
            text_color="white", 
            fg_color="#ef4444", 
            width=16, height=16, 
            corner_radius=8
        )
        badge_1.place(x=24, y=4)

        # 2. Notification Bell (Solid)
        bell_icon = ctk.CTkLabel(
            icons_frame, 
            text="🔔", 
            font=ctk.CTkFont(size=20), 
            text_color="#64748b", 
            width=40
        )
        bell_icon.pack(side="left", padx=5)

        # 3. User Avatar "M"
        avatar_frame = ctk.CTkFrame(icons_frame, fg_color="#e5e9f0", width=42, height=42, corner_radius=21)
        avatar_frame.pack(side="left", padx=8)
        avatar_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            avatar_frame, 
            text="M", 
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), 
            text_color="#475569"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # 4. Logout Icon (Door/Exit)
        logout_icon = ctk.CTkLabel(
            icons_frame, 
            text="⎗", # Better Logout symbol representation
            font=ctk.CTkFont(size=22, weight="bold"), 
            text_color="#64748b", 
            width=40
        )
        logout_icon.pack(side="left", padx=2)



    def criar_kpis(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=30, pady=10)

        # 5 Columns
        for i in range(5):
            container.grid_columnconfigure(i, weight=1)

        # Data from image
        kpis = [
            {"titulo": "Atendimentos do Dia", "valor": "5", "icone": "👥", "cor_icone": "#3b82f6"}, # Blue
            {"titulo": "Vagas Disponíveis", "valor": "0", "icone": "📅", "cor_icone": "#22c55e"}, # Green
            {"titulo": "Alertas Ativos", "valor": "0", "icone": "🔔", "cor_icone": "#ef4444"},   # Red
            {"titulo": "Total de Estudantes", "valor": "13", "icone": "🎓", "cor_icone": "#a855f7"}, # Purple
            {"titulo": "Humor Médio (Hoje)", "valor": "😊", "icone": "🙂", "cor_icone": "#eab308"} # Yellow
        ]

        for i, kpi in enumerate(kpis):
            self.criar_card_kpi(container, i, kpi)

    def criar_card_kpi(self, parent, col_idx, dados):
        # Card with white bg and rounded corners
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
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
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#6b7280",
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            content_frame,
            text=dados["valor"],
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color="#111827",
            anchor="w"
        ).pack(anchor="w", pady=(5, 0))

        # Stylized Icon (Right) - Boxed icon
        # Create a light background for the icon
        icon_bg_color = self.hex_to_rgba(dados["cor_icone"], 0.1) # Fallback to transparent if not possible
        
        icon_container = ctk.CTkFrame(
            card, 
            width=48, height=48, 
            corner_radius=10, 
            fg_color="#f8fafc" # Light gray bg for icons
        )
        icon_container.grid(row=0, column=1, padx=20, sticky="e")
        icon_container.grid_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_container, 
            text=dados["icone"], 
            font=ctk.CTkFont(size=22),
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
        container.pack(fill="x", padx=30, pady=20)
        
        container.grid_columnconfigure(0, weight=3) # Agenda 
        container.grid_columnconfigure(1, weight=2) # Alertas

        # --- Próximos Atendimentos ---
        agenda_card = ctk.CTkFrame(container, fg_color="white", corner_radius=12)
        agenda_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header Agenda
        agenda_header = ctk.CTkFrame(agenda_card, fg_color="transparent")
        agenda_header.pack(fill="x", padx=25, pady=20)
        
        ctk.CTkLabel(
            agenda_header, 
            text="Próximos Atendimentos",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#1f2937"
        ).pack(side="left")

        ctk.CTkLabel(
            agenda_header,
            text="Ver agenda completa →",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#4f46e5", # Link color
            cursor="hand2"
        ).pack(side="right")

        # Empty State Content
        agenda_content = ctk.CTkFrame(agenda_card, fg_color="transparent")
        agenda_content.pack(fill="both", expand=True, padx=25, pady=(0, 30))

        icon_circle = ctk.CTkFrame(agenda_content, width=80, height=80, corner_radius=40, fg_color="#f3f4f6")
        icon_circle.pack(pady=(20, 15))
        icon_circle.pack_propagate(False)
        
        ctk.CTkLabel(
            icon_circle,
            text="📅", 
            font=ctk.CTkFont(size=32),
            text_color="#9ca3af"
        ).place(relx=0.5, rely=0.5, anchor="center")


        ctk.CTkLabel(
            agenda_content,
            text="Nenhum agendamento para hoje",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#6b7280"
        ).pack(pady=(0, 15))

        ctk.CTkButton(
            agenda_content,
            text="+ Criar agendamento",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#6366f1", # Indigo-500
            hover_color="#4f46e5",
            corner_radius=8,
            height=36
        ).pack()


        # --- Estudantes em Alerta ---
        alert_card = ctk.CTkFrame(container, fg_color="white", corner_radius=12)
        alert_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        check_header = ctk.CTkFrame(alert_card, fg_color="transparent")
        check_header.pack(fill="x", padx=25, pady=20)

        ctk.CTkLabel(
            check_header,
            text="Estudantes em Alerta",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#1f2937"
        ).pack(side="left")

        alert_content = ctk.CTkFrame(alert_card, fg_color="transparent")
        alert_content.pack(fill="both", expand=True, padx=25, pady=(0, 30))

        # Check Icon (Circle with check)
        ctk.CTkLabel(
            alert_content,
            text="✔", 
            font=ctk.CTkFont(size=32),
            text_color="#d1d5db", # Gray check
            height=60, width=60, corner_radius=30, fg_color="#f3f4f6" # Gray circle bg
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            alert_content,
            text="Nenhum alerta no momento",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#374151"
        ).pack()

        ctk.CTkLabel(
            alert_content,
            text="Todos os estudantes estão bem acompanhados",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#9ca3af"
        ).pack()

    def criar_analise_bem_estar(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=30, pady=10)
        
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=1)

        # --- Chart ---
        chart_card = ctk.CTkFrame(container, fg_color="white", corner_radius=12)
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header
        chart_header = ctk.CTkFrame(chart_card, fg_color="transparent")
        chart_header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            chart_header, 
            text="📉 Humor dos Estudantes (30 dias)", # Adding icon as text for simplicity
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#1f2937"
        ).pack(side="left")

        # Legend (simplified)
        legend_frame = ctk.CTkFrame(chart_header, fg_color="transparent")
        legend_frame.pack(side="right")
        self.criar_legenda_item(legend_frame, "Bom", "#22c55e")
        self.criar_legenda_item(legend_frame, "Neutro", "#eab308")
        self.criar_legenda_item(legend_frame, "Ruim", "#ef4444")

        # Chart Canvas
        self.chart_frame = ctk.CTkFrame(chart_card, fg_color="#f8fafc", height=180, corner_radius=0)
        self.chart_frame.pack(fill="x", padx=20, pady=10)
        
        self.canvas = ctk.CTkCanvas(self.chart_frame, bg="#f8fafc", height=180, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Bind resize event
        self.chart_frame.bind("<Configure>", self.draw_chart)

        # Stats at bottom
        stats_frame = ctk.CTkFrame(chart_card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=40, pady=20)
        
        self.criar_stat_chart(stats_frame, "Média Geral", "3.14/5", "😐")
        self.criar_stat_chart(stats_frame, "Registros", "222", "📋")


        # --- Bem-Estar List ---
        list_card = ctk.CTkFrame(container, fg_color="white", corner_radius=12)
        list_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            list_card,
            text="❤ Bem-Estar por Dimensão",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#1f2937",
            anchor="w"
        ).pack(fill="x", padx=20, pady=20)

        metrics = ["Acadêmico", "Emocional", "Social"]
        for m in metrics:
            row = ctk.CTkFrame(list_card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(row, text=f"📓 {m}" if m=="Acadêmico" else (f"❤ {m}" if m=="Emocional" else f"👥 {m}"), text_color="#374151", font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text="--", text_color="#9ca3af").pack(side="right")
        
        ctk.CTkLabel(list_card, text="Baseado em autoavaliações dos últimos 7 dias", text_color="#9ca3af", font=ctk.CTkFont(size=10)).pack(side="bottom", pady=20)

    def draw_chart(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # Margins
        pad_x = 40
        pad_y = 30
        
        # Mock Data (10 points)
        data = [3.0, 3.1, 3.2, 3.4, 3.2, 3.3, 3.5, 3.4, 3.4, 4.0] 
        dates = ["09/01", "10/01", "11/01", "12/01", "13/01", "14/01", "15/01", "16/01", "17/01", "18/01"]
        
        if w < 100: return # Too small

        # Horizontal Grid Lines (1 to 5)
        for i in range(1, 6):
            y = h - pad_y - (i * (h - 2*pad_y) / 5)
            self.canvas.create_line(pad_x, y, w - pad_x, y, fill="#e5e7eb", width=1)
            # Icons/Text for Y axis? Image shows icons on left (angry to happy)
            # We skip icons for simplicity or draw simple circles

        # Draw Line
        points = []
        for i, val in enumerate(data):
            x = pad_x + (i * (w - 2*pad_x) / (len(data) - 1))
            y = h - pad_y - (val * (h - 2*pad_y) / 5)
            points.append((x, y))
            
            # Draw Date Labels
            self.canvas.create_text(x, h - 10, text=dates[i], fill="#9ca3af", font=("Segoe UI", 8))

        # Bezier or Straight lines
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i+1]
            self.canvas.create_line(x1, y1, x2, y2, fill="#6366f1", width=2, capstyle="round", smooth=True)

        # Draw Points
        for x, y in points:
            self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="#fbbf24", outline="white", width=2)


    def criar_legenda_item(self, parent, text, color):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", padx=5)
        ctk.CTkLabel(f, text="●", text_color=color, font=ctk.CTkFont(size=10)).pack(side="left")
        ctk.CTkLabel(f, text=text, text_color="#6b7280", font=ctk.CTkFont(size=11)).pack(side="left", padx=2)

    def criar_stat_chart(self, parent, label, value, icon):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(side="left", expand=True)

        icon_box = ctk.CTkFrame(f, width=40, height=40, corner_radius=20, fg_color="#f3f4f6")
        icon_box.pack(pady=(0, 5))
        icon_box.pack_propagate(False)

        ctk.CTkLabel(icon_box, text=icon, font=ctk.CTkFont(size=18)).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="#64748b").pack()
        ctk.CTkLabel(f, text=value, font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="#1e293b").pack()




    def criar_visao_risco(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="x", padx=30, pady=10)

        # Header Risk
        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.pack(fill="x", pady=(10, 15))
        
        ctk.CTkLabel(
            header,
            text="🛡 Visão de Risco dos Estudantes",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#1f2937"
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Atualizar", 
            fg_color="#e5e7eb", text_color="#374151", hover_color="#d1d5db", 
            width=80, height=30
        ).pack(side="right")

        # Columns Container
        cols_container = ctk.CTkFrame(wrapper, fg_color="transparent")
        cols_container.pack(fill="x")
        
        for i in range(4):
            cols_container.grid_columnconfigure(i, weight=1)

        # Columns Data
        columns_data = [
            {"title": "Crítico", "count": 5, "color": "#ef4444", "students": [
                {"name": "Ana Beatriz Costa", "course": "Software Multiplataforma", "msg": "Pedido de ajuda urgente"},
                {"name": "Alice Lima", "course": "Sistemas de Informação", "msg": "Pedido de ajuda urgente"}
            ]},
            {"title": "Alto", "count": 0, "color": "#f97316", "students": []},
            {"title": "Médio", "count": 0, "color": "#eab308", "students": []},
            {"title": "Normal", "count": 8, "color": "#22c55e", "students": [
                {"name": "Bruno Henrique Souza", "course": "Logística", "msg": "Sem registros de humor recentes", "safe": True},
                {"name": "Camila Ferreira Santos", "course": "Gestão de TI", "msg": "Sem registros de humor recentes", "safe": True}
            ]}
        ]

        for i, col in enumerate(columns_data):
            self.criar_coluna_risco(cols_container, i, col)

    def criar_coluna_risco(self, parent, idx, dados):
        frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
        frame.grid(row=0, column=idx, sticky="nsew", padx=6)
        
        # Color bar header
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=15)
        
        # Dot
        ctk.CTkLabel(header, text="●", text_color=dados["color"], font=ctk.CTkFont(size=14)).pack(side="left")
        
        # Title
        ctk.CTkLabel(
            header, 
            text=dados["title"], 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#374151"
        ).pack(side="left", padx=5)

        # Count
        ctk.CTkLabel(
            header, 
            text=str(dados["count"]), 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#1f2937"
        ).pack(side="right")

        # Content
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        if not dados["students"]:
            ctk.CTkLabel(content, text="Nenhum estudante", text_color="#9ca3af", font=ctk.CTkFont(size=12)).pack(pady=20)
        else:
            for s in dados["students"]:
                self.criar_card_estudante_risco(content, s, dados["color"])

    def criar_card_estudante_risco(self, parent, student, color):
        card = ctk.CTkFrame(parent, fg_color="#ffffff", corner_radius=6, border_width=1, border_color="#f1f5f9")
        card.pack(fill="x", pady=4)

        # Left border indicator
        indicator = ctk.CTkFrame(card, width=4, fg_color=color, corner_radius=0)
        indicator.pack(side="left", fill="y")
        
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        ctk.CTkLabel(
            info, text=student["name"], 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), 
            text_color="#1f2937", anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            info, text=student["course"], 
            font=ctk.CTkFont(family="Segoe UI", size=11), 
            text_color="#64748b", anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            info, text=student["msg"], 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
            text_color="#ef4444", anchor="w"
        ).pack(fill="x", pady=(6,0))



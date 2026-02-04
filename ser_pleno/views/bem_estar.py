import customtkinter as ctk
from services.bem_estar import ServicoBemEstar
import threading
from ui_theme import THEME, SPACING, RADIUS, font

class BemEstarFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_bem_estar = ServicoBemEstar()

        self.grid_columnconfigure(0, weight=1)

        self.criar_cabecalho()
        self.criar_cards_humor()
        
        # Seção de Análise (30 Dias)
        self.criar_analise_mensal()

        # Visão de Risco (Migrada do Dashboard)
        self.criar_visao_risco()

        # Check-ins Recentes
        self.criar_lista_checkins()
        
        self.load_data()

    def load_data(self):
        def fetch():
            dash = self.servico_bem_estar.obter_dashboard()
            checkins = self.servico_bem_estar.listar_checkins()
            risks = self.servico_bem_estar.listar_estudantes_risco()
            self.after(0, lambda: self.update_ui(dash, checkins, risks))
        threading.Thread(target=fetch, daemon=True).start()

    def update_ui(self, dash_res, checkins_res, risks_res):
        if dash_res.get('success'):
            self.update_metrics(dash_res.get('data', {}))
        
        if checkins_res.get('success'):
            # The API returns {'data': {'checkins': [...]}}
            data = checkins_res.get('data', {})
            checkins = data.get('checkins') if isinstance(data, dict) else []
            if checkins is None: checkins = [] # fallback if data is just the list
            self.populate_checkins(checkins)
            
        if risks_res.get('success'):
            # The API returns {'data': {'groups': {...}}}
            data = risks_res.get('data', {})
            groups = data.get('groups', {})
            
            # Flatten groups for the existing populate_risks logic
            flat_risks = []
            mapping = {
                'critical': 'critico',
                'high': 'alto',
                'medium': 'medio',
                'low': 'normal'
            }
            for backend_level, ui_level in mapping.items():
                for student in groups.get(backend_level, []):
                    student['level'] = ui_level
                    student['msg'] = ", ".join(student.get('reasons', [])) or "Requer atenção"
                    flat_risks.append(student)
            
            self.populate_risks(flat_risks)

    def update_metrics(self, data):
        # Update metrics from wellness dashboard
        summary = data.get('summary', {})
        # We could update the cards here if needed
        pass

    def criar_cabecalho(self):
        header = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 12))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)

        icon_box = ctk.CTkFrame(inner, width=48, height=48, corner_radius=12, fg_color=THEME["primary_light"])
        icon_box.pack(side="left", padx=(0, 16))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="🧡", font=font(20), text_color=THEME["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(inner, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="Bem-Estar e Humor", font=font(20, "bold"), text_color=THEME["text"]).pack(anchor="w")
        ctk.CTkLabel(text_box, text="Monitoramento emocional e social", font=font(12), text_color=THEME["text_muted"]).pack(anchor="w")

    def criar_cards_humor(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="ew", padx=SPACING["page_x"], pady=10)
        for i in range(3): container.grid_columnconfigure(i, weight=1)

        metricas = [
            {"label": "Humor Médio", "value": "Bom (4.2)", "icon": "😊", "bg": THEME["success_light"], "fg": THEME["success"]},
            {"label": "Participação", "value": "85%", "icon": "📈", "bg": THEME["info_light"], "fg": THEME["info"]},
            {"label": "Alertas Críticos", "value": "2", "icon": "🚨", "bg": THEME["danger_light"], "fg": THEME["danger"]}
        ]

        for i, m in enumerate(metricas):
            card = ctk.CTkFrame(container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
            card.grid(row=0, column=i, sticky="ew", padx=5)
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(padx=20, pady=20)
            
            ctk.CTkLabel(content, text=m["icon"], font=font(24)).pack(side="left", padx=(0, 15))
            txts = ctk.CTkFrame(content, fg_color="transparent")
            txts.pack(side="left")
            ctk.CTkLabel(txts, text=m["value"], font=font(22, "bold"), text_color=THEME["text"]).pack(anchor="w")
            ctk.CTkLabel(txts, text=m["label"], font=font(12, "bold"), text_color=THEME["text_muted"]).pack(anchor="w")

    def criar_analise_mensal(self):
        box = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        box.grid(row=2, column=0, sticky="ew", padx=SPACING["page_x"], pady=10)
        
        ctk.CTkLabel(box, text="📈 Tendência de Bem-Estar (30 dias)", font=font(16, "bold"), text_color=THEME["text"]).pack(anchor="w", padx=25, pady=(20, 10))
        
        # Chart Canvas
        self.canvas_frame = ctk.CTkFrame(box, fg_color=THEME["bg_alt"], height=200)
        self.canvas_frame.pack(fill="x", padx=25, pady=10)
        self.canvas_30d = ctk.CTkCanvas(self.canvas_frame, bg=THEME["bg_alt"], height=200, highlightthickness=0)
        self.canvas_30d.pack(fill="both", expand=True)
        self.canvas_frame.bind("<Configure>", self.draw_30day_chart)

        # Percentages below
        perc_container = ctk.CTkFrame(box, fg_color="transparent")
        perc_container.pack(fill="x", padx=25, pady=(10, 25))
        
        percs = [
            {"label": "Felicidade/Bom", "value": "65%", "color": THEME["success"]},
            {"label": "Neutralidade", "value": "25%", "color": THEME["warning"]},
            {"label": "Tristeza/Ruim", "value": "10%", "color": THEME["danger"]}
        ]
        
        for p in percs:
            item = ctk.CTkFrame(perc_container, fg_color="transparent")
            item.pack(side="left", expand=True)
            ctk.CTkLabel(item, text=p["label"], font=font(12, "bold"), text_color=THEME["text_muted"]).pack()
            # Bar
            bar_bg = ctk.CTkFrame(item, width=120, height=8, fg_color=THEME["border"], corner_radius=4)
            bar_bg.pack(pady=5)
            bar_bg.pack_propagate(False)
            ctk.CTkFrame(bar_bg, width=int(120 * (int(p["value"][:-1])/100)), height=8, fg_color=p["color"], corner_radius=4).pack(side="left")
            ctk.CTkLabel(item, text=p["value"], font=font(13, "bold"), text_color=THEME["text"]).pack()

    def draw_30day_chart(self, event=None):
        self.canvas_30d.delete("all")
        w = self.canvas_30d.winfo_width()
        h = self.canvas_30d.winfo_height()
        if w < 50: return
        
        pad_x, pad_y = 40, 30
        # Simulated 15 points for 30 days
        data = [3.5, 3.2, 3.8, 3.4, 3.1, 3.0, 3.6, 3.9, 4.2, 4.0, 3.8, 4.1, 4.3, 4.2, 4.5]
        
        points = []
        for i, val in enumerate(data):
            x = pad_x + (i * (w - 2*pad_x) / (len(data) - 1))
            y = h - pad_y - (val * (h - 2*pad_y) / 5)
            points.append((x, y))

        # Area
        poly = [pad_x, h - pad_y]
        for x, y in points: poly.extend([x, y])
        poly.extend([w - pad_x, h - pad_y])
        self.canvas_30d.create_polygon(poly, fill=THEME["primary_light"], outline="")
        
        # Line
        for i in range(len(points) - 1):
            self.canvas_30d.create_line(points[i], points[i+1], fill=THEME["primary"], width=2)
            
        # Dots
        for x, y in points:
            self.canvas_30d.create_oval(x-2, y-2, x+2, y+2, fill="white", outline=THEME["primary"])

    def criar_visao_risco(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=3, column=0, sticky="ew", padx=SPACING["page_x"], pady=10)

        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.pack(fill="x", pady=(10, 15))
        ctk.CTkLabel(header, text="🛡 Visão de Risco dos Estudantes", font=font(18, "bold"), text_color=THEME["text"]).pack(side="left")

        cols = ctk.CTkFrame(wrapper, fg_color="transparent")
        cols.pack(fill="x")
        for i in range(4): cols.grid_columnconfigure(i, weight=1)

        self.colunas_risco = {}
        config_cols = [
            {"title": "Crítico", "color": "#ef4444", "key": "critico"},
            {"title": "Alto", "color": "#f97316", "key": "alto"},
            {"title": "Médio", "color": "#eab308", "key": "medio"},
            {"title": "Normal", "color": "#22c55e", "key": "normal"}
        ]

        for i, config in enumerate(config_cols):
            frame = ctk.CTkFrame(cols, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
            frame.grid(row=0, column=i, sticky="nsew", padx=6)
            
            h = ctk.CTkFrame(frame, fg_color="transparent")
            h.pack(fill="x", padx=15, pady=15)
            ctk.CTkLabel(h, text="●", text_color=config["color"], font=font(14)).pack(side="left")
            ctk.CTkLabel(h, text=config["title"], font=font(14, "bold"), text_color=THEME["text_muted"]).pack(side="left", padx=5)
            
            count_lbl = ctk.CTkLabel(h, text="0", font=font(14, "bold"), text_color=THEME["text"])
            count_lbl.pack(side="right")

            content = ctk.CTkFrame(frame, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=10, pady=(0, 15))
            
            self.colunas_risco[config["key"]] = {
                "content": content,
                "count_lbl": count_lbl,
                "color": config["color"]
            }

    def populate_risks(self, risks):
        for col in self.colunas_risco.values():
            for child in col["content"].winfo_children(): child.destroy()
            col["count_lbl"].configure(text="0")

        if not risks:
            for key in ["critico", "alto", "medio", "normal"]:
                ctk.CTkLabel(self.colunas_risco[key]["content"], text="Nenhum estudante", text_color=THEME["text_highlight"], font=font(11)).pack(pady=10)
            return

        counts = {"critico": 0, "alto": 0, "medio": 0, "normal": 0}
        for s in risks:
            nivel = s.get('level', 'normal').lower()
            if nivel not in self.colunas_risco: nivel = 'normal'
            counts[nivel] += 1
            self.criar_card_estudante_risco(self.colunas_risco[nivel]["content"], s, self.colunas_risco[nivel]["color"])

        for key, count in counts.items():
            self.colunas_risco[key]["count_lbl"].configure(text=str(count))
            if count == 0:
                ctk.CTkLabel(self.colunas_risco[key]["content"], text="Nenhum estudante", text_color=THEME["text_highlight"], font=font(11)).pack(pady=10)

    def criar_card_estudante_risco(self, parent, student, color):
        card = ctk.CTkFrame(parent, fg_color=THEME["card"], corner_radius=RADIUS["button"], border_width=1, border_color=THEME["border"])
        card.pack(fill="x", pady=4)
        indicator = ctk.CTkFrame(card, width=4, fg_color=color, corner_radius=0)
        indicator.pack(side="left", fill="y")
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        ctk.CTkLabel(info, text=student.get("name", "Nome"), font=font(13, "bold"), text_color=THEME["text"], anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=student.get("course", "Geral"), font=font(11), text_color=THEME["text_muted"], anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=student.get("msg", ""), font=font(11, "bold"), text_color=THEME["danger"], anchor="w").pack(fill="x", pady=(6,0))

    def criar_lista_checkins(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=4, column=0, sticky="ew", padx=SPACING["page_x"], pady=20)
        ctk.CTkLabel(container, text="📝 Check-ins Recentes", font=font(16, "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(0,10))
        
        self.checkins_container = ctk.CTkFrame(container, fg_color="transparent")
        self.checkins_container.pack(fill="both", expand=True)

    def populate_checkins(self, checkins):
        for w in self.checkins_container.winfo_children(): w.destroy()
        
        # Ensure checkins is a list
        if not isinstance(checkins, list):
            checkins = []
            
        if not checkins:
            ctk.CTkLabel(self.checkins_container, text="Nenhum check-in registrado.", font=font(14), text_color=THEME["text_muted"]).pack(pady=40)
            return
        
        for c in checkins:
            if not isinstance(c, dict): continue # Skip if not a dictionary
            
            item = ctk.CTkFrame(self.checkins_container, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
            item.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(item, fg_color="transparent")
            inner.pack(fill="x", padx=15, pady=10)
            
            ctk.CTkLabel(inner, text="📝", font=font(16)).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(inner, text=c.get('student_name', 'Estudante'), font=font(13, "bold")).pack(side="left")
            ctk.CTkLabel(inner, text=c.get('mood_text', 'Neutro'), font=font(12), text_color=THEME["text_muted"]).pack(side="left", padx=20)
            ctk.CTkLabel(inner, text=c.get('date', 'Hoje'), font=font(11), text_color=THEME["text_muted"]).pack(side="right")

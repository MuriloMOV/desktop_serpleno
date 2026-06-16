import customtkinter as ctk
from services.bem_estar import ServicoBemEstar
import threading
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    Divider,
    EmptyState,
    Pill,
    blend_color,
)


class BemEstarFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_bem_estar = ServicoBemEstar()

        self.grid_columnconfigure(0, weight=1)

        self.criar_cabecalho()
        self.criar_cards_humor()
        self.criar_analise_mensal()
        self.criar_visao_risco()
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
            data = checkins_res.get('data', {})
            checkins = data.get('checkins') if isinstance(data, dict) else []
            if checkins is None:
                checkins = []
            self.populate_checkins(checkins)

        if risks_res.get('success'):
            data = risks_res.get('data', {})
            groups = data.get('groups', {})

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
        summary = data.get('summary', {})
        pass

    def criar_cabecalho(self):
        header = PageHeader(self, title="Bem-Estar e Humor", subtitle="Monitoramento emocional e social dos estudantes")
        header.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 16))

    def criar_cards_humor(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["page_x"], pady=10)
        for i in range(3):
            container.grid_columnconfigure(i, weight=1)

        metricas = [
            {"label": "Humor Médio", "value": "Bom (4.2)", "icon": "😊", "accent": THEME["success"], "trend": "Últimos 7 dias"},
            {"label": "Participação", "value": "85%", "icon": "📈", "accent": THEME["info"], "trend": "Check-ins"},
            {"label": "Alertas Críticos", "value": "2", "icon": "🚨", "accent": THEME["danger"], "trend": "Requer ação"},
        ]

        for i, m in enumerate(metricas):
            card = Card(container)
            card.grid(row=0, column=i, sticky="ew", padx=6)

            content = ctk.CTkFrame(card.body, fg_color="transparent")
            content.pack(fill="both", expand=True, pady=4)

            ctk.CTkLabel(content, text=m["icon"], font=themed_font("h2")).pack(side="left", padx=(0, 12))
            txts = ctk.CTkFrame(content, fg_color="transparent")
            txts.pack(side="left")
            ctk.CTkLabel(txts, text=m["value"], font=themed_font("h2", "bold"), text_color=THEME["text"]).pack(anchor="w")
            ctk.CTkLabel(txts, text=m["label"], font=themed_font("body"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 0))
            ctk.CTkLabel(txts, text=m["trend"], font=themed_font("overline"), text_color=THEME["text_disabled"]).pack(anchor="w", pady=(2, 0))

    def criar_analise_mensal(self):
        card = Card(self, title="📈 Tendência de Bem-Estar (30 dias)")
        card.pack(fill="x", padx=SPACING["page_x"], pady=10)

        chart_area = ctk.CTkFrame(card.body, fg_color=THEME["bg_alt"], height=220, corner_radius=RADIUS["md"])
        chart_area.pack(fill="x", pady=(0, 12))
        self.canvas_30d = ctk.CTkCanvas(chart_area, bg=THEME["bg_alt"], height=220, highlightthickness=0)
        self.canvas_30d.pack(fill="both", expand=True)
        chart_area.bind("<Configure>", self.draw_30day_chart)

        perc_container = ctk.CTkFrame(card.body, fg_color="transparent")
        perc_container.pack(fill="x", pady=(0, 4))

        percs = [
            {"label": "Felicidade/Bom", "value": "65%", "color": THEME["success"]},
            {"label": "Neutralidade", "value": "25%", "color": THEME["warning"]},
            {"label": "Tristeza/Ruim", "value": "10%", "color": THEME["danger"]},
        ]

        for p in percs:
            item = ctk.CTkFrame(perc_container, fg_color="transparent")
            item.pack(side="left", expand=True)
            ctk.CTkLabel(item, text=p["label"], font=themed_font("body", "bold"), text_color=THEME["text_muted"]).pack()
            bar_bg = ctk.CTkFrame(item, width=110, height=8, fg_color=THEME["border"], corner_radius=RADIUS["pill"])
            bar_bg.pack(pady=5)
            bar_bg.pack_propagate(False)
            ctk.CTkFrame(bar_bg, width=int(110 * (int(p["value"][:-1]) / 100)), height=8, fg_color=p["color"], corner_radius=RADIUS["pill"]).pack(side="left")
            ctk.CTkLabel(item, text=p["value"], font=themed_font("body", "bold"), text_color=THEME["text"]).pack()

    def draw_30day_chart(self, event=None):
        self.canvas_30d.delete("all")
        w = self.canvas_30d.winfo_width()
        h = self.canvas_30d.winfo_height()
        if w < 50:
            return

        data = [3.5, 3.2, 3.8, 3.4, 3.1, 3.0, 3.6, 3.9, 4.2, 4.0, 3.8, 4.1, 4.3, 4.2, 4.5]
        pad_x, pad_y = 36, 28
        chart_w, chart_h = w - 2 * pad_x, h - 2 * pad_y

        points = []
        for i, val in enumerate(data):
            x = pad_x + (i * chart_w / (len(data) - 1))
            y = h - pad_y - (val * chart_h / 5)
            points.append((x, y))

        poly = [pad_x, h - pad_y]
        for x, y in points:
            poly.extend([x, y])
        poly.extend([w - pad_x, h - pad_y])
        self.canvas_30d.create_polygon(poly, fill=THEME["primary_light"], outline="")

        for i in range(len(points) - 1):
            self.canvas_30d.create_line(points[i], points[i + 1], fill=THEME["primary"], width=2)

        for x, y in points:
            self.canvas_30d.create_oval(x - 3, y - 3, x + 3, y + 3, fill="white", outline=THEME["primary"], width=1)

    def criar_visao_risco(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="x", padx=SPACING["page_x"], pady=10)

        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.pack(fill="x", pady=(10, 12))
        ctk.CTkLabel(header, text="🛡 Visão de Risco dos Estudantes", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")

        cols = ctk.CTkFrame(wrapper, fg_color="transparent")
        cols.pack(fill="x")
        for i in range(4):
            cols.grid_columnconfigure(i, weight=1)

        self.colunas_risco = {}
        config_cols = [
            {"title": "Crítico", "color": THEME["danger"], "key": "critico"},
            {"title": "Alto", "color": "#f97316", "key": "alto"},
            {"title": "Médio", "color": THEME["warning"], "key": "medio"},
            {"title": "Normal", "color": THEME["success"], "key": "normal"},
        ]

        for i, config in enumerate(config_cols):
            frame = Card(cols)
            frame.grid(row=0, column=i, sticky="nsew", padx=6)

            h = ctk.CTkFrame(frame.body, fg_color="transparent")
            h.pack(fill="x", padx=14, pady=14)
            ctk.CTkLabel(h, text="●", text_color=config["color"], font=themed_font("h3")).pack(side="left")
            ctk.CTkLabel(h, text=config["title"], font=themed_font("body", "bold"), text_color=THEME["text_muted"]).pack(side="left", padx=6)
            count_lbl = ctk.CTkLabel(h, text="0", font=themed_font("body", "bold"), text_color=THEME["text"])
            count_lbl.pack(side="right")

            content = ctk.CTkFrame(frame.body, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=10, pady=(0, 14))

            self.colunas_risco[config["key"]] = {
                "content": content,
                "count_lbl": count_lbl,
                "color": config["color"],
            }

    def populate_risks(self, risks):
        for col in self.colunas_risco.values():
            for child in col["content"].winfo_children():
                child.destroy()
            col["count_lbl"].configure(text="0")

        if not risks:
            for key in ["critico", "alto", "medio", "normal"]:
                ctk.CTkLabel(self.colunas_risco[key]["content"], text="Nenhum estudante", text_color=THEME["text_disabled"], font=themed_font("overline")).pack(pady=10)
            return

        counts = {"critico": 0, "alto": 0, "medio": 0, "normal": 0}
        for s in risks:
            nivel = s.get('level', 'normal').lower()
            if nivel not in self.colunas_risco:
                nivel = 'normal'
            counts[nivel] += 1
            self.criar_card_estudante_risco(self.colunas_risco[nivel]["content"], s, self.colunas_risco[nivel]["color"])

        for key, count in counts.items():
            self.colunas_risco[key]["count_lbl"].configure(text=str(count))
            if count == 0:
                ctk.CTkLabel(self.colunas_risco[key]["content"], text="Nenhum estudante", text_color=THEME["text_disabled"], font=themed_font("overline")).pack(pady=10)

    def criar_card_estudante_risco(self, parent, student, color):
        card = Card(parent)
        card.pack(fill="x", pady=4)

        indicator = ctk.CTkFrame(card.body, width=4, fg_color=color, corner_radius=0)
        indicator.pack(side="left", fill="y")
        info = ctk.CTkFrame(card.body, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        ctk.CTkLabel(info, text=student.get("name", "Nome"), font=themed_font("body", "bold"), text_color=THEME["text"], anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=student.get("course", "Geral"), font=themed_font("overline"), text_color=THEME["text_muted"], anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=student.get("msg", ""), font=themed_font("overline", "bold"), text_color=THEME["danger_strong"], anchor="w").pack(fill="x", pady=(6, 0))

    def criar_lista_checkins(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=SPACING["page_x"], pady=20)
        ctk.CTkLabel(container, text="📝 Check-ins Recentes", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(0, 10))

        self.checkins_container = ctk.CTkFrame(container, fg_color="transparent")
        self.checkins_container.pack(fill="both", expand=True)

    def populate_checkins(self, checkins):
        for w in self.checkins_container.winfo_children():
            w.destroy()

        if not isinstance(checkins, list):
            checkins = []

        if not checkins:
            EmptyState(self.checkins_container, icon="📝", title="Nenhum check-in registrado", subtitle="Os registros de humor aparecerão aqui").pack(pady=10)
            return

        for c in checkins:
            if not isinstance(c, dict):
                continue

            card = Card(self.checkins_container)
            card.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(card.body, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=10)

            ctk.CTkLabel(inner, text="📝", font=themed_font("h3")).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(inner, text=c.get('student_name', 'Estudante'), font=themed_font("body", "bold"), text_color=THEME["text"]).pack(side="left")
            ctk.CTkLabel(inner, text=c.get('mood_text', 'Neutro'), font=themed_font("body"), text_color=THEME["text_muted"]).pack(side="left", padx=14)
            ctk.CTkLabel(inner, text=c.get('date', 'Hoje'), font=themed_font("overline"), text_color=THEME["text_muted"]).pack(side="right")

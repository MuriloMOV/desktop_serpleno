import customtkinter as ctk
import threading
from services.dashboard import ServicoDashboard
from ui_theme import THEME, SPACING, RADIUS, font

class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_dashboard = ServicoDashboard()
        self.grid_columnconfigure(0, weight=1)

        self.criar_cabecalho()
        
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=SPACING["page_x"], pady=(10, 20))
        
        self.criar_grid_principal()
        self.load_data()

    def load_data(self):
        def fetch():
            data = self.servico_dashboard.obter_kpis()
            self.after(0, lambda: self.update_dashboard(data))
        threading.Thread(target=fetch, daemon=True).start()

    def update_dashboard(self, data):
        # Atualizar KPIs
        for widget in self.kpi_container.winfo_children():
            widget.destroy()
            
        # Obter humor médio com emoji
        media_humor = data.get("media_humor")
        humor_emoji = self.get_humor_emoji(media_humor)
        
        kpis = [
            {"titulo": "Atendimentos do Dia", "valor": str(data.get("appointments_today", 0)), "icone": "👥", "cor": "#6366F1"},
            {"titulo": "Vagas Disponíveis", "valor": str(data.get("available_slots", 0)), "icone": "📅", "cor": "#10B981"},
            {"titulo": "Alertas Ativos", "valor": str(data.get("alerts", 0)), "icone": "🔔", "cor": "#EF4444"},
            {"titulo": "Total de Estudantes", "valor": str(data.get("total_students", 0)), "icone": "👥", "cor": "#8B5CF6"},
            {"titulo": "Humor Médio (Hoje)", "valor": humor_emoji, "icone": humor_emoji, "cor": "#F59E0B"}
        ]

        for i, kpi in enumerate(kpis):
            self.kpi_container.grid_columnconfigure(i, weight=1)
            self.criar_card_kpi(self.kpi_container, i, kpi)

        # Atualizar próximos atendimentos
        agenda_card = self.criar_container_card(self.left_col, "Próximos Atendimentos", "Ver agenda completa →")
        # Limpar conteúdo do card
        for widget in agenda_card.winfo_children():
            if widget not in [agenda_card.winfo_children()[0]]:  # Manter cabeçalho
                widget.destroy()
        
        appointments = data.get("upcoming_appointments", [])
        if appointments:
            for appt in appointments:
                self.render_agenda_item(agenda_card, appt)
        else:
            self.render_empty_agenda(agenda_card)

        # Atualizar estudantes em alerta
        alerts_card = self.criar_container_card(self.right_col, "Estudantes em Alerta")
        # Limpar conteúdo do card
        for widget in alerts_card.winfo_children():
            if widget not in [alerts_card.winfo_children()[0]]:  # Manter cabeçalho
                widget.destroy()
        
        attention_students = data.get("attention_students", [])
        if attention_students:
            for student in attention_students:
                self.render_alerta_item(alerts_card, student)
        else:
            self.render_empty_alerts(alerts_card)

        # Atualizar bem-estar por dimensão
        bem_estar_card = self.criar_container_card(self.right_col, "❤ Bem-Estar por Dimensão")
        # Limpar conteúdo do card
        for widget in bem_estar_card.winfo_children():
            if widget not in [bem_estar_card.winfo_children()[0]]:  # Manter cabeçalho
                widget.destroy()
        
        bem_estar = data.get("bem_estar_dimensions", {})
        self.criar_dimensao_progresso(bem_estar_card, "📁 Acadêmico", bem_estar.get("academico", 0) / 5)
        self.criar_dimensao_progresso(bem_estar_card, "❤ Emocional", bem_estar.get("emocional", 0) / 5)
        self.criar_dimensao_progresso(bem_estar_card, "👥 Social", bem_estar.get("social", 0) / 5)

        # Atualizar gráfico de humor
        humor_history = data.get("humor_history", [])
        if humor_history:
            self.draw_chart(humor_history)
            
            # Atualizar stats do gráfico
            for widget in self.stats_side.winfo_children():
                widget.destroy()
                
            # Calcular média geral
            total = sum(item["media_humor"] for item in humor_history)
            media_geral = round(total / len(humor_history), 2) if humor_history else 0
            self.criar_indicator_footer(self.stats_side, self.get_humor_emoji(media_geral), "Média Geral", f"{media_geral}/5")
            ctk.CTkFrame(self.stats_side, fg_color="#F1F5F9", height=2, width=80).pack(pady=15)
            self.criar_indicator_footer(self.stats_side, "📋", "Registros", str(len(humor_history)))
        else:
            # Gráfico padrão se não houver dados
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
        header.pack(fill="x", padx=SPACING["page_x"], pady=(30, 20))
        ctk.CTkLabel(header, text="Dashboard Central", font=font(24, "bold"), text_color="#1E293B").pack(side="left")

        r_tools = ctk.CTkFrame(header, fg_color="transparent")
        r_tools.pack(side="right")

        msg_f = ctk.CTkFrame(r_tools, fg_color="transparent", width=45, height=45)
        msg_f.pack(side="left", padx=10)
        ctk.CTkLabel(msg_f, text="💬", font=font(20)).place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(msg_f, text="1", font=font(10, "bold"), text_color="white", fg_color="#EF4444", width=16, height=16, corner_radius=8).place(x=25, y=5)

        ctk.CTkLabel(r_tools, text="🔔", font=font(20), text_color="#64748B").pack(side="left", padx=15)
        ctk.CTkLabel(r_tools, text="U", font=font(15, "bold"), text_color="#1E293B", fg_color="#E2E8F0", width=40, height=40, corner_radius=20).pack(side="left", padx=10)
        ctk.CTkLabel(r_tools, text="⎗", font=font(20), text_color="#64748B", cursor="hand2").pack(side="left", padx=15)

    def criar_card_kpi(self, parent, col, d):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=15, border_width=1, border_color="#F1F5F9")
        card.grid(row=0, column=col, sticky="ew", padx=10)
        
        txt_f = ctk.CTkFrame(card, fg_color="transparent")
        txt_f.pack(side="left", padx=25, pady=25)
        ctk.CTkLabel(txt_f, text=d["titulo"], font=font(13), text_color="#64748B").pack(anchor="w")
        ctk.CTkLabel(txt_f, text=d["valor"], font=font(28, "bold"), text_color="#1E293B").pack(anchor="w", pady=(5, 0))

        bg_hex = self.blend_color(d["cor"], 0.1)
        ctk.CTkLabel(card, text=d["icone"], font=font(22), text_color=d["cor"], fg_color=bg_hex, width=50, height=50, corner_radius=10).pack(side="right", padx=25)

    def criar_grid_principal(self):
        main_grid = ctk.CTkFrame(self, fg_color="transparent")
        main_grid.pack(fill="x", padx=SPACING["page_x"], pady=10)
        main_grid.grid_columnconfigure(0, weight=2)
        main_grid.grid_columnconfigure(1, weight=1)

        self.left_col = ctk.CTkFrame(main_grid, fg_color="transparent")
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))

        # Gráfico (Ajustado para ocupar mais espaço vertical)
        chart_card = self.criar_container_card(self.left_col, "📈 Humor dos Estudantes (30 dias)")
        
        # Container interno para Gráfico + Stats Lateral
        chart_layout = ctk.CTkFrame(chart_card, fg_color="transparent")
        chart_layout.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        chart_layout.grid_columnconfigure(0, weight=1) # Espaço do Gráfico
        chart_layout.grid_columnconfigure(1, weight=0) # Espaço dos Stats

        self.canvas = ctk.CTkCanvas(chart_layout, bg="white", height=280, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        # Stats na lateral direita
        self.stats_side = ctk.CTkFrame(chart_layout, fg_color="transparent")
        self.stats_side.grid(row=0, column=1, sticky="ns", padx=(20, 0))
        
        chart_card.bind("<Configure>", lambda e: self.draw_chart())

        self.right_col = ctk.CTkFrame(main_grid, fg_color="transparent")
        self.right_col.grid(row=0, column=1, sticky="nsew", padx=(15, 0))

    def criar_container_card(self, parent, titulo, link_txt=None):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=15, border_width=1, border_color="#F1F5F9")
        card.pack(fill="x", pady=(0, 25))
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=25, pady=20)
        ctk.CTkLabel(h, text=titulo, font=font(16, "bold"), text_color="#1E293B").pack(side="left")
        if link_txt:
            ctk.CTkLabel(h, text=link_txt, font=font(12), text_color="#6366F1", cursor="hand2").pack(side="right")
        return card

    def criar_indicator_footer(self, parent, icon, label, val):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(pady=10)
        ctk.CTkLabel(f, text=icon, font=font(20)).pack()
        ctk.CTkLabel(f, text=label, font=font(11), text_color="#64748B").pack()
        ctk.CTkLabel(f, text=val, font=font(14, "bold"), text_color="#1E293B").pack()

    def criar_dimensao_progresso(self, parent, nome, valor):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=25, pady=12)
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text=nome, font=font(13), text_color="#1E293B").pack(side="left")
        ctk.CTkLabel(header, text=f"{int(valor*100)}%", font=font(13, "bold"), text_color="#64748B").pack(side="right")
        prog = ctk.CTkProgressBar(container, height=8, progress_color="#6366F1", fg_color="#F1F5F9")
        prog.pack(fill="x", pady=(8, 0))
        prog.set(valor)

    def render_agenda_item(self, parent, appt):
        row = ctk.CTkFrame(parent, fg_color="#F8FAFC", corner_radius=10)
        row.pack(fill="x", padx=25, pady=5)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(info, text=appt["student_name"], font=font(14, "bold")).pack(anchor="w")
        ctk.CTkLabel(info, text=f"🎓 {appt['curso']}", font=font(12), text_color="#94A3B8").pack(anchor="w")
        ctk.CTkLabel(row, text=f"🕒 {appt['time']}", font=font(13, "bold"), text_color="#6366F1").pack(side="right", padx=20)

    def render_empty_agenda(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(pady=40)
        ctk.CTkLabel(f, text="📅", font=font(32), text_color="#CBD5E1", fg_color="#F8FAFC", width=70, height=70, corner_radius=35).pack()
        ctk.CTkLabel(f, text="Nenhum atendimento próximo", font=font(14, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(f, text="Não há agendamentos futuros", font=font(12), text_color="#94A3B8").pack()

    def render_alerta_item(self, parent, student):
        row = ctk.CTkFrame(parent, fg_color="#FEE2E2", corner_radius=10)
        row.pack(fill="x", padx=25, pady=5)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(info, text=student["name"], font=font(14, "bold")).pack(anchor="w")
        ctk.CTkLabel(info, text=student["attention_reason"], font=font(12), text_color="#DC2626").pack(anchor="w")
        priority = student.get("priority_level", 0)
        priority_icon = "🔴" if priority >= 2 else "🟠" if priority == 1 else "🟡"
        ctk.CTkLabel(row, text=priority_icon, font=font(13, "bold")).pack(side="right", padx=20)

    def render_empty_alerts(self, parent):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(pady=40)
        ctk.CTkLabel(f, text="✔", font=font(32), text_color="#CBD5E1", fg_color="#F8FAFC", width=70, height=70, corner_radius=35).pack()
        ctk.CTkLabel(f, text="Nenhum alerta no momento", font=font(14, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(f, text="Todos os estudantes estão bem acompanhados", font=font(12), text_color="#94A3B8").pack()

    def draw_chart(self, humor_history=None):
        self.canvas.delete("all")
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 50: return
        
        if humor_history is None or not humor_history:
            # Dados padrão caso não haja registros
            pts = [2.8, 3.1, 2.9, 3.2, 2.7, 3.5, 3.2, 2.9, 3.0, 3.8, 3.4, 3.6, 3.2, 3.1, 3.9]
            dates = ["05/01", "07/01", "09/01", "11/01", "13/01", "15/01", "17/01", "19/01", "21/01", "23/01", "25/01", "27/01", "28/01", "29/01", "30/01"]
        else:
            pts = [item["media_humor"] for item in humor_history]
            dates = [item["data"] for item in humor_history]
            
            # Garantir que haja pelo menos 2 pontos para evitar divisão por zero
            if len(pts) < 2:
                # Se houver apenas 1 ponto, duplicar para criar um gráfico válido
                pts = [pts[0], pts[0]]
                dates = [dates[0], dates[0]]
        
        margin_x, margin_y = 40, 40
        chart_w, chart_h = w - 2*margin_x, h - 2*margin_y
        
        coords = []
        for i, v in enumerate(pts):
            x = margin_x + (i * chart_w / (len(pts)-1))
            y = (h - margin_y) - ((v-1) * chart_h / 4)
            coords.append((x, y))

        # Linha e Grid Horizontal
        for i in range(5):
            gy = margin_y + (i * chart_h / 4)
            self.canvas.create_line(margin_x, gy, w-margin_x, gy, fill="#F1F5F9")

        for i in range(len(coords)-1):
            self.canvas.create_line(coords[i], coords[i+1], fill="#6366F1", width=2, smooth=True)

        for i, (x, y) in enumerate(coords):
            val = pts[i]
            dot_color = "#EF4444" if val < 2.5 else "#F59E0B" if val < 3.5 else "#10B981"
            self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=dot_color, outline="white", width=1)
            if i % 2 == 0:
                self.canvas.create_text(x, h-15, text=dates[i], font=("Arial", 8), fill="#94A3B8")

    def blend_color(self, hex_c, alpha):
        r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
        return f"#{int(r*alpha + 255*(1-alpha)):02x}{int(g*alpha + 255*(1-alpha)):02x}{int(b*alpha + 255*(1-alpha)):02x}"
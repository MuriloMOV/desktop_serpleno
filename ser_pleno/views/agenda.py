import customtkinter as ctk
from datetime import datetime, timedelta
import threading
from tkinter import messagebox
from services.agendamentos import ServicoAgendamento
from ui_theme import THEME, SPACING, RADIUS, font

class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_agendamento = ServicoAgendamento()
        self.data_atual = datetime.now()
        self.appointments = {}
        self.horarios_base = []
        
        self.columnconfigure(0, weight=1)

        self.criar_barra_topo()
        self.criar_header_agenda()
        self.criar_secao_dia()
        self.criar_secao_proxima_semana()
        
        self.load_data()

    def criar_barra_topo(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=SPACING["page_x"], pady=(10, 5))
        
        ctk.CTkLabel(topo, text="Agenda", font=font(18, "bold"), text_color=THEME["text"]).pack(side="left")
        
        actions = ctk.CTkFrame(topo, fg_color="transparent")
        actions.pack(side="right")
        
        icones = [("🤝", None), ("🔔", None), ("👤", None), ("➔", None)]
        for icone, cmd in icones:
            btn = ctk.CTkLabel(actions, text=icone, font=font(16), cursor="hand2", text_color=THEME["text_muted"])
            btn.pack(side="left", padx=10)

    def criar_header_agenda(self):
        header = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        header.pack(fill="x", padx=SPACING["page_x"], pady=10)
        
        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        icon_box = ctk.CTkFrame(inner, width=40, height=40, corner_radius=8, fg_color=THEME["primary_light"])
        icon_box.pack(side="left", padx=(0, 15))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="📅", font=font(18)).place(relx=0.5, rely=0.5, anchor="center")

        txt_frame = ctk.CTkFrame(inner, fg_color="transparent")
        txt_frame.pack(side="left")
        ctk.CTkLabel(txt_frame, text="Agenda de Atendimentos", font=font(16, "bold")).pack(anchor="w")
        ctk.CTkLabel(txt_frame, text="Gerencie seus horários e atendimentos", font=font(12), text_color=THEME["text_muted"]).pack(anchor="w")

        right_side = ctk.CTkFrame(inner, fg_color="transparent")
        right_side.pack(side="right")

        nav = ctk.CTkFrame(right_side, fg_color=THEME["bg_alt"], corner_radius=20)
        nav.pack(side="left", padx=15)
        
        ctk.CTkButton(nav, text="❮", width=25, fg_color="transparent", text_color=THEME["text"], command=lambda: self.mudar_dia(-1)).pack(side="left", padx=5)
        self.lbl_data_display = ctk.CTkLabel(nav, text="", font=font(12, "bold"))
        self.lbl_data_display.pack(side="left", padx=10)
        ctk.CTkButton(nav, text="❯", width=25, fg_color="transparent", text_color=THEME["text"], command=lambda: self.mudar_dia(1)).pack(side="left", padx=5)

        ctk.CTkButton(right_side, text="🕒 Gerir Horários", font=font(12, "bold"), fg_color=THEME["primary"], height=35, command=self.abrir_modal_gerir).pack(side="left")

    def criar_secao_dia(self):
        self.container_dia = self.criar_container_secao("Agenda do Dia", "Visualização Detalhada")
        self.grid_dia = ctk.CTkFrame(self.container_dia, fg_color="transparent")
        self.grid_dia.pack(fill="x", padx=20, pady=(0, 20))
        self.grid_dia.columnconfigure((0, 1), weight=1)

    def criar_secao_proxima_semana(self):
        self.container_semana = self.criar_container_secao("Próxima Semana", self.data_atual.strftime("%d de %B"))
        self.grid_semana = ctk.CTkFrame(self.container_semana, fg_color="transparent")
        self.grid_semana.pack(fill="x", padx=20, pady=(0, 20))
        self.grid_semana.columnconfigure((0, 1), weight=1)

    def criar_container_secao(self, titulo, subtitulo):
        container = ctk.CTkFrame(self, fg_color=THEME["card"], corner_radius=RADIUS["card"])
        container.pack(fill="x", padx=SPACING["page_x"], pady=10)
        
        head = ctk.CTkFrame(container, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(head, text="📅", font=font(16)).pack(side="left", padx=(0, 10))
        v_box = ctk.CTkFrame(head, fg_color="transparent")
        v_box.pack(side="left")
        ctk.CTkLabel(v_box, text=titulo, font=font(14, "bold")).pack(anchor="w")
        ctk.CTkLabel(v_box, text=subtitulo, font=font(11), text_color=THEME["text_muted"]).pack(anchor="w")
        
        return container

    def load_data(self):
        data_str = self.data_atual.strftime('%Y-%m-%d')
        self.lbl_data_display.configure(text=self.data_atual.strftime("%A, %d de Fevereiro"))
        
        def fetch():
            res_appts = self.servico_agendamento.listar_agendamentos(data=data_str)
            res_times = self.servico_agendamento.listar_horarios_disponiveis(data=data_str)
            self.after(0, lambda: self.process_data(res_appts, res_times))
            
        threading.Thread(target=fetch, daemon=True).start()

    def process_data(self, res_appts, res_times):
        self.appointments = {}
        if res_appts.get('success'):
            data = res_appts.get('data', [])
            for a in (data if isinstance(data, list) else data.get('appointments', [])):
                self.appointments[a.get('time')[:5]] = a
        
        self.horarios_base = res_times.get('data', ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"])
        self.render_grids()

    def render_grids(self):
        for g in [self.grid_dia, self.grid_semana]:
            for w in g.winfo_children(): w.destroy()

        for i, hora in enumerate(self.horarios_base):
            row, col = i // 2, i % 2
            apt = self.appointments.get(hora)
            
            card_dia = self.criar_card_slot(self.grid_dia, hora, apt)
            card_dia.grid(row=row, column=col, sticky="ew", padx=10, pady=8)
            
            card_sem = self.criar_card_slot(self.grid_semana, hora, None)
            card_sem.grid(row=row, column=col, sticky="ew", padx=10, pady=8)

    def criar_card_slot(self, parent, hora, apt):
        is_booked = apt is not None
        bg = THEME["slot_purple_bg"] if is_booked else THEME["slot_green_bg"]
        text_color = THEME["slot_purple_text"] if is_booked else THEME["slot_green_text"]
        
        slot = ctk.CTkFrame(parent, fg_color=bg, height=80, corner_radius=10, cursor="hand2")
        slot.pack_propagate(False)
        
        content = ctk.CTkFrame(slot, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(content, text=hora, font=font(14, "bold"), text_color=text_color).pack()
        nome = apt.get('student', {}).get('name') if is_booked else "Disponível"
        ctk.CTkLabel(content, text=nome, font=font(11), text_color=text_color).pack()

        if is_booked:
            ctk.CTkLabel(slot, text="✎", font=font(10), text_color=text_color).place(relx=0.5, rely=0.85, anchor="center")
            slot.bind("<Button-1>", lambda e: self.abrir_modal_agendamento(hora, apt))
        else:
            slot.bind("<Button-1>", lambda e: self.abrir_modal_agendamento(hora))

        return slot

    def abrir_modal_agendamento(self, hora, apt=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Agendar Atendimento")
        modal.geometry("450x450")
        modal.grab_set()

        ctk.CTkLabel(modal, text="Agendar Atendimento", font=font(18, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(modal, text=f"Às {hora} - {self.data_atual.strftime('%d/%m/%Y')}", font=font(14), text_color=THEME["primary"]).pack(pady=(0, 20))

        ctk.CTkLabel(modal, text="Selecione o Estudante:", font=font(12)).pack(padx=30, anchor="w")
        student_var = ctk.StringVar()
        combo = ctk.CTkOptionMenu(modal, variable=student_var, values=["Carregando..."], fg_color=THEME["bg"], button_color=THEME["primary"])
        combo.pack(fill="x", padx=30, pady=(5, 15))

        ctk.CTkLabel(modal, text="Observações:", font=font(12)).pack(padx=30, anchor="w")
        obs = ctk.CTkTextbox(modal, height=100, border_width=1)
        obs.pack(fill="x", padx=30, pady=(5, 20))

        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30)
        
        ctk.CTkButton(btn_frame, text="Cancelar", fg_color="#E5E7EB", text_color="black", command=modal.destroy).pack(side="left", expand=True, padx=(0, 5))
        
        def confirmar():
            sid = getattr(modal, "_smap", {}).get(student_var.get())
            payload = {"date": self.data_atual.strftime('%Y-%m-%d'), "time": hora, "student_id": sid, "notes": obs.get("1.0", "end")}
            res = self.servico_agendamento.criar_agendamento(payload)
            if res.get('success'):
                self.load_data()
                modal.destroy()

        ctk.CTkButton(btn_frame, text="Confirmar Agendamento", fg_color=THEME["primary"], command=confirmar).pack(side="left", expand=True, padx=(5, 0))

        def load():
            from services.estudantes import ServicoEstudante
            s_data = ServicoEstudante().listar_estudantes().get('data', [])
            s_map = {s['name']: s['id'] for s in s_data}
            modal._smap = s_map
            self.after(0, lambda: combo.configure(values=list(s_map.keys())))
            if s_data: student_var.set(s_data[0]['name'])
            
        threading.Thread(target=load, daemon=True).start()

    def abrir_modal_gerir(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Gerir Horários")
        modal.geometry("400x500")
        modal.grab_set()

        ctk.CTkLabel(modal, text="Gerir Horários de Atendimento", font=font(16, "bold")).pack(pady=20)
        ctk.CTkLabel(modal, text="Horários Atuais", font=font(12, "bold")).pack(anchor="w", padx=40)

        scroll = ctk.CTkScrollableFrame(modal, height=250, fg_color="transparent", border_width=1)
        scroll.pack(fill="x", padx=40, pady=10)

        def refresh_list():
            for w in scroll.winfo_children(): w.destroy()
            for h in self.horarios_base:
                f = ctk.CTkFrame(scroll, fg_color="white", height=40)
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=h, font=font(12)).pack(side="left", padx=10)
                ctk.CTkButton(f, text="🗑 Remover", width=70, height=25, fg_color="transparent", text_color="#ef4444", 
                             command=lambda x=h: remover(x)).pack(side="right", padx=5)

        def remover(h):
            if self.servico_agendamento.gerenciar_horario({"action": "remove", "time": h}):
                self.load_data()
                self.after(500, refresh_list)

        refresh_list()

        add_frame = ctk.CTkFrame(modal, fg_color="transparent")
        add_frame.pack(fill="x", padx=40, pady=20)
        
        entry = ctk.CTkEntry(add_frame, placeholder_text="--:--")
        entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        def adicionar():
            if self.servico_agendamento.gerenciar_horario({"action": "add", "time": entry.get()}):
                self.load_data()
                self.after(500, refresh_list)

        ctk.CTkButton(add_frame, text="+ Adicionar", width=100, fg_color=THEME["primary"], command=adicionar).pack(side="right")
        ctk.CTkButton(modal, text="Fechar", fg_color="#1f2937", command=modal.destroy).pack(pady=10)

    def mudar_dia(self, dias):
        self.data_atual += timedelta(days=dias)
        self.load_data()
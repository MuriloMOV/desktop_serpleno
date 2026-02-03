import customtkinter as ctk
from datetime import datetime, timedelta
from services.agendamentos import ServicoAgendamento
import threading

from ui_theme import THEME, SPACING, RADIUS, font

class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_agendamento = ServicoAgendamento()
        
        # Estado
        self.data_atual = datetime.now()
        self.agendamentos = {}

        self.colors = THEME

        # Configuração do Layout
        self.columnconfigure(0, weight=1)

        # 1. Cabeçalho Superior (Título e Perfil)
        self.criar_cabecalho_superior()

        # 2. Card de Resumo da Agenda
        self.criar_card_resumo()

        # 3. Agenda do Dia
        self.criar_secao_agenda_dia()

        # 4. Próxima Semana
        self.criar_secao_proxima_semana()
        
        # Carregar Dados
        self.load_data()

    def load_data(self):
        date_str = self.data_atual.strftime('%Y-%m-%d')
        
        # Atualizar label de data se existir
        if hasattr(self, 'lbl_data_atual'):
            self.lbl_data_atual.configure(text=self.data_atual.strftime("%A, %d de %B de %Y"))

        def fetch():
            # Busca em paralelo
            appts = self.servico_agendamento.listar_agendamentos(data=date_str)
            self.after(0, lambda: self.update_view(appts))
            
        threading.Thread(target=fetch, daemon=True).start()

    def update_view(self, appts_data):
        self.appointments = {}
        if appts_data.get('success'):
            raw_appts = appts_data.get('data', [])
            
            # Robust extraction of list from potential dict/pagination structure
            if isinstance(raw_appts, dict):
                raw_appts = raw_appts.get('appointments', []) or raw_appts.get('results', [])
                
            if isinstance(raw_appts, list):
                for apt in raw_appts:
                    if not isinstance(apt, dict): continue
                    
                    time = apt.get('time') # "HH:MM"
                    if time:
                        # Normaliza para HH:MM se vier com segundos
                        self.appointments[time[:5]] = apt
        
        self.refresh_agenda_dia()

    def criar_cabecalho_superior(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        header.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], 18))

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)
        
        # Título da Página
        icon_box = ctk.CTkFrame(inner, width=48, height=48, corner_radius=12, fg_color=self.colors["primary_light"])
        icon_box.pack(side="left", padx=(0, 16))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="📅", font=font(20), text_color=self.colors["primary"]).place(relx=0.5, rely=0.5, anchor="center")

        text_box = ctk.CTkFrame(inner, fg_color="transparent")
        text_box.pack(side="left")
        ctk.CTkLabel(text_box, text="Agenda de Atendimentos", font=font(20, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(text_box, text="Gerencie seus horários e atendimentos", font=font(12), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Container de Ícones (Igual ao Dashboard)
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

    def criar_card_resumo(self):
        card = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        card.pack(fill="x", padx=SPACING["page_x"], pady=(0, 20))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        # Infos Lado Esquerdo
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left")

        icon_box = ctk.CTkFrame(info_frame, width=54, height=54, fg_color=self.colors["primary_light"], corner_radius=12)
        icon_box.pack(side="left", padx=(0, 20))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="🗓️", font=font(24)).place(relx=0.5, rely=0.5, anchor="center")

        titles = ctk.CTkFrame(info_frame, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(titles, text="Agenda de Atendimentos", font=font(20, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        ctk.CTkLabel(titles, text="Gerencie seus horários e atendimentos", font=font(14), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Lado Direito: Seletor de Data e Botão
        actions_frame = ctk.CTkFrame(inner, fg_color="transparent")
        actions_frame.pack(side="right")

        # Date Navigator (Estilizado)
        date_nav = ctk.CTkFrame(actions_frame, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["pill"], border_width=1, border_color=self.colors["border"])
        date_nav.pack(side="left", padx=(0, 15))
        
        # Seta Esquerda
        btn_prev = ctk.CTkButton(
            date_nav, text="❮", 
            font=font(10), 
            text_color=self.colors["text_muted"], 
            fg_color="transparent",
            hover_color=self.colors["border"],
            width=30,
            command=lambda: self.mudar_dia(-1)
        )
        btn_prev.pack(side="left", padx=2, pady=5)

        # Data Atual
        self.lbl_data_atual = ctk.CTkLabel(
            date_nav, 
            text=self.data_atual.strftime("%A, %d de %B de %Y"), 
            font=font(13, "bold"), 
            text_color=self.colors["text"]
        )
        self.lbl_data_atual.pack(side="left", padx=10)

        # Seta Direita
        btn_next = ctk.CTkButton(
            date_nav, text="❯", 
            font=font(10), 
            text_color=self.colors["text_muted"], 
            fg_color="transparent",
            hover_color=self.colors["border"],
            width=30,
            command=lambda: self.mudar_dia(1)
        )
        btn_next.pack(side="left", padx=2, pady=5)

        # Botão Gerir
        ctk.CTkButton(
            actions_frame, text="Gerir Horários", 
            fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"],
            text_color="white", font=font(13, "bold"),
            height=42, corner_radius=RADIUS["button"],
            image=None
        ).pack(side="left")

    def criar_secao_agenda_dia(self):
        container = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        container.pack(fill="x", padx=SPACING["page_x"], pady=(0, 20))

        # Cabeçalho da Seção
        sec_header = ctk.CTkFrame(container, fg_color="transparent")
        sec_header.pack(fill="x", padx=25, pady=(20, 15))

        ctk.CTkLabel(sec_header, text="📅", font=font(18)).pack(side="left", padx=(0, 10))
        text_v = ctk.CTkFrame(sec_header, fg_color="transparent")
        text_v.pack(side="left")
        ctk.CTkLabel(text_v, text="Agenda do Dia", font=font(16, "bold"), text_color=self.colors["text_main"]).pack(anchor="w")
        self.grid_frame_dia = ctk.CTkFrame(container, fg_color="transparent")
        self.grid_frame_dia.pack(fill="x", padx=25, pady=(0, 20))
        self.grid_frame_dia.columnconfigure((0, 1), weight=1, pad=15)

        # Render inicial vazio
        # Sera preenchido por refresh_agenda_dia

    def refresh_agenda_dia(self):
        # Limpar
        for w in self.grid_frame_dia.winfo_children(): w.destroy()
        
        # Gerar slots de 08:00 a 18:00
        hours = [f"{h:02d}:00" for h in range(8, 19)]
        
        for i, hora in enumerate(hours):
            # Verificar se tem agendamento
            appt = self.appointments.get(hora)
            
            if appt:
                student_name = appt.get('student', {}).get('name', 'Ocupado')
                status_text = appt.get('status', 'Agendado')
                tipo = "booked"
            else:
                student_name = "Disponível"
                status_text = "Livre" 
                tipo = "free"

            row = i // 2
            col = i % 2
            # Usando grid_frame_dia que é o container correto para o dia
            self.criar_card_agenda(self.grid_frame_dia, hora, student_name, tipo).grid(row=row, column=col, sticky="ew", pady=10, padx=5)

    def criar_secao_proxima_semana(self):
        container = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=15)
        container.pack(fill="x", padx=30, pady=(0, 40))

        # Cabeçalho da Seção
        sec_header = ctk.CTkFrame(container, fg_color="transparent")
        sec_header.pack(fill="x", padx=25, pady=(20, 15))

        ctk.CTkLabel(sec_header, text="📅", font=font(18)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(sec_header, text="Próxima Semana", font=font(16, "bold"), text_color=self.colors["text_main"]).pack(side="left")

        # Grade de Slots
        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(fill="x", padx=25, pady=(0, 20))
        grid_frame.columnconfigure((0, 1), weight=1, pad=15)

        # Mock Slots para Próxima Semana
        slots = [
            ("08:00", "Mariana Costa", "booked"),
            ("09:00", "Zeca Martins", "booked"),
            ("10:00", "Disponível", "free"),
            ("11:00", "Disponível", "free")
        ]

        for hora, nome, status in slots:
             self.criar_card_agenda(grid_frame, hora, nome, status).pack(side="left", fill="both", expand=True, padx=5)

    def criar_card_agenda(self, parent, hora, titulo, tipo):
        subtitulo = "Sessão Individual" if tipo == "booked" else "Livre"
        bg = self.colors["slot_purple_bg"] if tipo == "booked" else self.colors["slot_green_bg"]
        text_color = self.colors["slot_purple_text"] if tipo == "booked" else self.colors["slot_green_text"]
        hover_color = "#e0e7ff" if tipo == "booked" else "#dcfce7"
        
        slot = ctk.CTkFrame(parent, fg_color=bg, height=100, corner_radius=12)
        # Removed internal pack to allow external layout management (grid/pack) defined by parent container
        slot.pack_propagate(False)
        
        # Conteúdo do Slot centralizado
        content = ctk.CTkFrame(slot, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(content, text=hora, font=font(16, "bold"), text_color=text_color).pack()
        ctk.CTkLabel(content, text=titulo, font=font(13, "bold" if tipo == "booked" else "normal"), text_color=text_color).pack(pady=(2, 0))

        if subtitulo and subtitulo != "Livre":
             ctk.CTkLabel(
                content, 
                text=subtitulo, 
                font=ctk.CTkFont(family="Segoe UI", size=11), 
                text_color=text_color
            ).pack()
        
        if tipo == "booked":
            # Ícone de edição pequeno e discreto
            edit_lbl = ctk.CTkLabel(slot, text="✎", font=font(14), text_color=text_color, cursor="hand2")
            edit_lbl.place(relx=0.5, rely=0.82, anchor="center")

        # Efeito de Hover simples
        def on_enter(e):
            slot.configure(fg_color=hover_color)
        def on_leave(e):
            slot.configure(fg_color=bg)
            
        slot.bind("<Enter>", on_enter)
        slot.bind("<Leave>", on_leave)

        return slot

import customtkinter as ctk
from datetime import datetime, timedelta

class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f4f6fb")
        self.controller = controller

        # Mock Data
        self.current_date = datetime.now()
        self.horarios = ["18:00", "19:00", "20:00", "21:00"] # Mock available slots
        self.appointments = {
            "18:00": {"student": "Ana Beatriz", "status": "confirmed"},
            # "19:00": free
            "20:00": {"student": "Diego Martins", "status": "pending"},
        }
        
        self.grid_columnconfigure(0, weight=1)

        self.criar_header()
        self.criar_agenda_dia()
        self.criar_proxima_semana()

    def criar_header(self):
        # Container Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        
        # Título e Botão Gerir
        left_header = ctk.CTkFrame(header, fg_color="transparent")
        left_header.pack(side="left")

        ctk.CTkLabel(
            left_header, 
            text="Agenda", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#1f2937"
        ).pack(side="left", padx=(0, 20))

        ctk.CTkButton(
            left_header,
            text="⚙️ Gerir Horários",
            fg_color="#e5e7eb",
            text_color="#374151",
            hover_color="#d1d5db",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.abrir_gerir_horarios
        ).pack(side="left")

        # Navegação de Data
        right_header = ctk.CTkFrame(header, fg_color="transparent")
        right_header.pack(side="right")

        ctk.CTkButton(
            right_header, text="◄", width=30, fg_color="#e5e7eb", text_color="#374151", hover_color="#d1d5db",
            command=lambda: self.mudar_dia(-1)
        ).pack(side="left", padx=5)

        self.lbl_data = ctk.CTkLabel(
            right_header,
            text=self.current_date.strftime("%A, %d de %B"), # Format simplified
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#1f2937"
        )
        self.lbl_data.pack(side="left", padx=10)

        ctk.CTkButton(
            right_header, text="►", width=30, fg_color="#e5e7eb", text_color="#374151", hover_color="#d1d5db",
            command=lambda: self.mudar_dia(1)
        ).pack(side="left", padx=5)


    def criar_agenda_dia(self):
        # Container Card
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Titulo
        ctk.CTkLabel(
            card,
            text="Agenda do Dia",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#374151"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Grid de Slots (Container)
        self.slots_container = ctk.CTkFrame(card, fg_color="transparent")
        self.slots_container.pack(fill="x", padx=20, pady=20)
        
        # Render Slots
        self.renderizar_slots(self.slots_container)

    def criar_proxima_semana(self):
         # Container Card
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        card.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        # Titulo com Data (+7 dias)
        next_week = self.current_date + timedelta(days=7)
        ctk.CTkLabel(
            card,
            text=f"Próxima Semana ({next_week.strftime('%d/%m/%Y')})",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#374151"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Grid de Slots (Container)
        self.slots_next_week = ctk.CTkFrame(card, fg_color="transparent")
        self.slots_next_week.pack(fill="x", padx=20, pady=20)

        # Mock Render (Same slots for ease)
        self.renderizar_slots(self.slots_next_week, is_next_week=True)

    def renderizar_slots(self, parent, is_next_week=False):
        # Limpar
        for w in parent.winfo_children(): w.destroy()

        # Grid layout manager logic manually or using .grid
        # Vamos usar .grid com 2 colunas para simular o "grid-cols-2"
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)

        row = 0
        col = 0
        
        data_source = self.appointments if not is_next_week else {} # Mock: Next week empty

        for i, time in enumerate(self.horarios):
            appt = data_source.get(time)
            
            # Frame do Slot
            slot = ctk.CTkFrame(parent, corner_radius=8, border_width=1)
            slot.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            
            # Info Time
            ctk.CTkLabel(
                slot, 
                text=time, 
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#1f2937" if appt else "#059669" # Gray if occupied, Green if free
            ).pack(anchor="w", padx=15, pady=(10, 0))

            if appt:
                # Ocupado (Red/Orange style depending on status in real app, here Gray/Blue)
                slot.configure(fg_color="#f3f4f6", border_color="#e5e7eb") # Occupied Style
                
                ctk.CTkLabel(
                    slot,
                    text=appt["student"],
                    font=ctk.CTkFont(size=14),
                    text_color="#4b5563"
                ).pack(anchor="w", padx=15, pady=(2, 10))
                
                # Edit Icon (Button)
                edit_btn = ctk.CTkButton(
                    slot, text="✏️", width=30, height=30, fg_color="transparent", hover_color="#e5e7eb", text_color="#374151",
                    command=lambda t=time: self.editar_agendamento(t)
                )
                edit_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-5, y=5)

            else:
                # Livre (Green Style)
                slot.configure(fg_color="#d1fae5", border_color="#a7f3d0") # bg-emerald-100 border-emerald-200
                
                ctk.CTkLabel(
                    slot,
                    text="Disponível",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    text_color="#059669" # text-emerald-600
                ).pack(anchor="w", padx=15, pady=(2, 10))

                # Click to schedule
                slot.bind("<Button-1>", lambda e, t=time: self.agendar_horario(t))
                for child in slot.winfo_children():
                    child.bind("<Button-1>", lambda e, t=time: self.agendar_horario(t))

            # Grid Calc
            col += 1
            if col > 1:
                col = 0
                row += 1


    def mudar_dia(self, delta):
        self.current_date += timedelta(days=delta)
        self.lbl_data.configure(text=self.current_date.strftime("%A, %d de %B"))
        # Reload slots (Mock refresh)
        self.renderizar_slots(self.slots_container)

    def abrir_gerir_horarios(self):
        print("Abrir Modal de Gerência de Horários")

    def agendar_horario(self, time):
        print(f"Agendar para {time}")
    
    def editar_agendamento(self, time):
        print(f"Editar agendamento de {time}")

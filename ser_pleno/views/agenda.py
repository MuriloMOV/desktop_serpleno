import customtkinter as ctk
from datetime import datetime

class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#f8fafc")
        self.controller = controller

        # Cores (Paleta Moderna e Vibrante)
        self.colors = {
            "bg": "#f8fafc",          # slate-50
            "card": "white",
            "primary": "#4f46e5",    # indigo-600
            "primary_hover": "#4338ca", # indigo-700
            "text_main": "#1e293b",   # slate-800
            "text_muted": "#64748b",  # slate-500
            "slot_green_bg": "#f0fdf4", # green-50
            "slot_green_text": "#16a34a", # green-600
            "slot_purple_bg": "#eef2ff", # indigo-50
            "slot_purple_text": "#4f46e5", # indigo-600
            "border": "#e2e8f0"       # slate-200
        }

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

    def criar_cabecalho_superior(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        # Título da Página
        ctk.CTkLabel(
            header, 
            text="Agenda", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.colors["text_main"]
        ).pack(side="left")

        # Container de Ícones (Igual ao Dashboard)
        icons_frame = ctk.CTkFrame(header, fg_color="transparent")
        icons_frame.pack(side="right")

        # Helper/Support com Badge
        helper_frame = ctk.CTkFrame(icons_frame, fg_color="transparent", width=45, height=45)
        helper_frame.pack(side="left", padx=2)
        helper_frame.pack_propagate(False)
        
        ctk.CTkLabel(helper_frame, text="🤝", font=ctk.CTkFont(size=22)).place(relx=0.4, rely=0.6, anchor="center")
        
        # Badge Vermelha "9+"
        badge = ctk.CTkLabel(
            helper_frame, text="9+", font=ctk.CTkFont(size=9, weight="bold"), 
            text_color="white", fg_color="#ef4444", 
            width=16, height=16, corner_radius=8
        )
        badge.place(x=24, y=4)

        # Notificações
        ctk.CTkLabel(icons_frame, text="🔔", font=ctk.CTkFont(size=20), text_color="#64748b", width=40).pack(side="left", padx=5)

        # Avatar do Usuário
        avatar_frame = ctk.CTkFrame(icons_frame, fg_color="#e5e9f0", width=42, height=42, corner_radius=21)
        avatar_frame.pack(side="left", padx=8)
        avatar_frame.pack_propagate(False)
        ctk.CTkLabel(avatar_frame, text="U", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color="#475569").place(relx=0.5, rely=0.5, anchor="center")

        # Logout
        ctk.CTkLabel(icons_frame, text="⎗", font=ctk.CTkFont(size=22, weight="bold"), text_color="#64748b", width=40).pack(side="left", padx=2)

    def criar_card_resumo(self):
        card = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=15)
        card.pack(fill="x", padx=30, pady=(0, 25))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)

        # Infos Lado Esquerdo
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left")

        icon_box = ctk.CTkFrame(info_frame, width=54, height=54, fg_color="#f5f3ff", corner_radius=12)
        icon_box.pack(side="left", padx=(0, 20))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="🗓️", font=("Segoe UI", 24)).place(relx=0.5, rely=0.5, anchor="center")

        titles = ctk.CTkFrame(info_frame, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(titles, text="Agenda de Atendimentos", font=("Segoe UI", 20, "bold"), text_color=self.colors["text_main"]).pack(anchor="w")
        ctk.CTkLabel(titles, text="Gerencie seus horários e atendimentos", font=("Segoe UI", 14), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Lado Direito: Seletor de Data e Botão
        actions_frame = ctk.CTkFrame(inner, fg_color="transparent")
        actions_frame.pack(side="right")

        # Date Navigator (Estilizado)
        date_nav = ctk.CTkFrame(actions_frame, fg_color="#f8fafc", corner_radius=20, border_width=1, border_color="#e2e8f0")
        date_nav.pack(side="left", padx=(0, 15))
        
        # Seta Esquerda
        ctk.CTkLabel(
            date_nav, text="❮", 
            font=("Segoe UI", 10), 
            text_color=self.colors["text_muted"], 
            cursor="hand2",
            width=30
        ).pack(side="left", padx=2, pady=5)

        # Data Atual
        ctk.CTkLabel(
            date_nav, 
            text="sexta-feira, 30 de janeiro de 2026", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), 
            text_color=self.colors["text_main"]
        ).pack(side="left", padx=10)

        # Seta Direita
        ctk.CTkLabel(
            date_nav, text="❯", 
            font=("Segoe UI", 10), 
            text_color=self.colors["text_muted"], 
            cursor="hand2",
            width=30
        ).pack(side="left", padx=2, pady=5)

        # Botão Gerir
        ctk.CTkButton(
            actions_frame, text="Gerir Horários", 
            fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"],
            text_color="white", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=42, corner_radius=10,
            image=None # Se tiver ícone de relógio pode adicionar aqui
        ).pack(side="left")

    def criar_secao_agenda_dia(self):
        container = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=15)
        container.pack(fill="x", padx=30, pady=(0, 25))

        # Cabeçalho da Seção
        sec_header = ctk.CTkFrame(container, fg_color="transparent")
        sec_header.pack(fill="x", padx=25, pady=(20, 15))

        ctk.CTkLabel(sec_header, text="📅", font=("Segoe UI", 18)).pack(side="left", padx=(0, 10))
        text_v = ctk.CTkFrame(sec_header, fg_color="transparent")
        text_v.pack(side="left")
        ctk.CTkLabel(text_v, text="Agenda do Dia", font=("Segoe UI", 16, "bold"), text_color=self.colors["text_main"]).pack(anchor="w")
        ctk.CTkLabel(text_v, text="Visualização Detalhada", font=("Segoe UI", 12), text_color=self.colors["text_muted"]).pack(anchor="w")

        # Grade de Slots
        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(fill="x", padx=25, pady=(0, 20))
        grid_frame.columnconfigure((0, 1), weight=1, pad=15)

        # Mock Slots para Agenda do Dia (Exatamente como a imagem)
        slots = [
            ("08:00", "Daniel Silva", "booked"),
            ("09:00", "Disponível", "free"),
            ("10:00", "Disponível", "free"),
            ("11:00", "Disponível", "free"),
            ("14:00", "Bruno Silva", "booked"),
            ("15:00", "Disponível", "free"),
            ("16:00", "Disponível", "free"),
            ("17:00", "Disponível", "free"),
        ]

        for i, (hora, status, tipo) in enumerate(slots):
            row = i // 2
            col = i % 2
            self.criar_slot_agenda(grid_frame, hora, status, tipo).grid(row=row, column=col, sticky="ew", pady=10, padx=5)

    def criar_secao_proxima_semana(self):
        container = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=15)
        container.pack(fill="x", padx=30, pady=(0, 40))

        # Cabeçalho da Seção
        sec_header = ctk.CTkFrame(container, fg_color="transparent")
        sec_header.pack(fill="x", padx=25, pady=(20, 15))

        ctk.CTkLabel(sec_header, text="📅", font=("Segoe UI", 18)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(sec_header, text="Próxima Semana", font=("Segoe UI", 16, "bold"), text_color=self.colors["text_main"]).pack(side="left")

        # Grade de Slots
        grid_frame = ctk.CTkFrame(container, fg_color="transparent")
        grid_frame.pack(fill="x", padx=25, pady=(0, 20))
        grid_frame.columnconfigure((0, 1), weight=1, pad=15)

        # Mock Slots para Próxima Semana
        slots = [
            ("08:00", "Mariana Costa", "booked"),
            ("09:00", "Zeca Martins", "booked"),
            ("10:00", "Disponível", "free"),
            ("11:00", "Disponível", "free"),
            ("14:00", "Disponível", "free"),
            ("15:00", "Disponível", "free"),
            ("16:00", "Disponível", "free"),
            ("17:00", "Disponível", "free"),
        ]

        for i, (hora, status, tipo) in enumerate(slots):
            row = i // 2
            col = i % 2
            self.criar_slot_agenda(grid_frame, hora, status, tipo).grid(row=row, column=col, sticky="ew", pady=10, padx=5)


    def criar_slot_agenda(self, parent, hora, status, tipo):
        bg = self.colors["slot_purple_bg"] if tipo == "booked" else self.colors["slot_green_bg"]
        text_color = self.colors["slot_purple_text"] if tipo == "booked" else self.colors["slot_green_text"]
        hover_color = "#e0e7ff" if tipo == "booked" else "#dcfce7"
        
        slot = ctk.CTkFrame(parent, fg_color=bg, height=100, corner_radius=12)
        slot.pack_propagate(False)
        
        # Conteúdo do Slot centralizado
        content = ctk.CTkFrame(slot, fg_color="transparent")
        content.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(
            content, 
            text=hora, 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), 
            text_color=text_color
        ).pack()
        
        ctk.CTkLabel(
            content, 
            text=status, 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold" if tipo == "booked" else "normal"), 
            text_color=text_color
        ).pack(pady=(2, 0))
        
        if tipo == "booked":
            # Ícone de edição pequeno e discreto
            edit_lbl = ctk.CTkLabel(
                slot, 
                text="✎", 
                font=("Segoe UI", 14), 
                text_color=text_color, 
                cursor="hand2"
            )
            edit_lbl.place(relx=0.5, rely=0.82, anchor="center")

        # Efeito de Hover simples
        def on_enter(e):
            slot.configure(fg_color=hover_color)
        def on_leave(e):
            slot.configure(fg_color=bg)
            
        slot.bind("<Enter>", on_enter)
        slot.bind("<Leave>", on_leave)

        return slot

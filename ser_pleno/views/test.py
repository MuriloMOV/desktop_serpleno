import customtkinter as ctk
from datetime import datetime, timedelta
from tkinter import messagebox
from services.agendamentos import ServicoAgendamento
from config.db_config import get_db_connection
from ui_theme import THEME, SPACING, RADIUS, font

class AgendaFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME.get("bg", "#F1F5F9"))
        self.controller = controller
        self.servico_agendamento = ServicoAgendamento()
        
        # Estado da Data Selecionada
        self.data_selecionada = datetime.now()
        
        self.horarios_base = []
        self.mapa_estudantes = {} # Para vincular Nome -> ID no Modal
        
        self.columnconfigure(0, weight=1)

        self.criar_barra_global()
        self.criar_header_secao()
        self.criar_container_agenda_dia()
        self.criar_container_proxima_semana()
        
        self.refresh_all()

    def fetch_estudantes(self):
        """Busca estudantes do banco para o Dropdown."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id_aluno, nome FROM aluno ORDER BY nome ASC")
            rows = cursor.fetchall()
            # Criamos um dicionário para facilitar a busca do ID pelo Nome selecionado no ComboBox
            self.mapa_estudantes = {r['nome']: r['id_aluno'] for r in rows}
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Erro ao buscar estudantes: {e}")

    def fetch_horarios_base(self):
        """Busca a grade de horários configurada no banco."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT Horario FROM disponibilidade WHERE is_active = 1 ORDER BY Horario ASC")
            self.horarios_base = [str(h[0])[:5] for h in cursor.fetchall()]
            cursor.close()
            conn.close()
        except:
            self.horarios_base = ["08:00", "09:00", "10:00"] # Fallback

    def refresh_all(self):
        """Recarrega dados e atualiza a UI."""
        self.fetch_horarios_base()
        self.fetch_estudantes()
        self.atualizar_label_data()
        self.load_grid_data()

    def load_grid_data(self):
        # Carrega dia atual selecionado
        data_str = self.data_selecionada.strftime('%Y-%m-%d')
        agendamentos_dia = self.servico_agendamento.listar_agendamentos(data=data_str)
        mapa_dia = {agt['data_hora'].strftime('%H:%M'): agt for agt in agendamentos_dia}
        self.renderizar_grid(self.container_grid, mapa_dia)

        # Carrega "Próxima Semana" (Exemplo: Próximo dia útil ou amanhã)
        amanha_str = (self.data_selecionada + timedelta(days=1)).strftime('%Y-%m-%d')
        agendamentos_prox = self.servico_agendamento.listar_agendamentos(data=amanha_str)
        mapa_prox = {agt['data_hora'].strftime('%H:%M'): agt for agt in agendamentos_prox}
        self.renderizar_grid(self.container_semana, mapa_prox)

    def criar_barra_global(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=SPACING["page_x"], pady=(20, 10))
        ctk.CTkLabel(barra, text="Agenda", font=font(22, "bold")).pack(side="left")
        
        f_icons = ctk.CTkFrame(barra, fg_color="transparent")
        f_icons.pack(side="right")
        for icon in [("🤝", "Ajuda"), ("🔔", "Notif"), ("👤", "Perfil"), ("🚪", "Sair")]:
            ctk.CTkButton(f_icons, text=icon[0], width=40, height=40, fg_color="white", 
                         text_color="black", hover_color="#E2E8F0", corner_radius=10).pack(side="left", padx=5)

    def criar_header_secao(self):
        header = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        header.pack(fill="x", padx=SPACING["page_x"], pady=10)
        
        # Esquerda: Info
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(left, text="📅", font=font(28, "normal")).pack(side="left", padx=(0, 15))
        
        titles = ctk.CTkFrame(left, fg_color="transparent")
        titles.pack(side="left")
        ctk.CTkLabel(titles, text="Agenda de atendimentos", font=font(18, "bold")).pack(anchor="w")
        ctk.CTkLabel(titles, text="Gerencie seus horários e atendimentos", font=font(13, "normal"), text_color="#64748B").pack(anchor="w")
        
        # Direita: Navegação de Data e Gestão
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=20)

        # Seletor de Data com Setas
        ctk.CTkButton(right, text="<", width=30, height=30, fg_color="transparent", 
                     text_color="black", hover_color="#F1F5F9", 
                     command=lambda: self.alterar_data(-1)).pack(side="left")
        
        self.lbl_data_display = ctk.CTkLabel(right, text="", font=font(13, "bold"), width=180)
        self.lbl_data_display.pack(side="left", padx=5)

        ctk.CTkButton(right, text=">", width=30, height=30, fg_color="transparent", 
                     text_color="black", hover_color="#F1F5F9", 
                     command=lambda: self.alterar_data(1)).pack(side="left")
        
        # Botão Relógio
        ctk.CTkButton(right, text="🕒", width=42, height=42, fg_color="#9333EA", 
                     command=self.abrir_modal_gestao, corner_radius=10).pack(side="left", padx=(15, 0))

    def atualizar_label_data(self):
        dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        dia_nome = dias_semana[self.data_selecionada.weekday()]
        data_formatada = self.data_selecionada.strftime(f"{dia_nome}, %d de %B")
        self.lbl_data_display.configure(text=data_formatada)

    def alterar_data(self, dias):
        self.data_selecionada += timedelta(days=dias)
        self.refresh_all()

    def renderizar_grid(self, container, mapa_dados):
        for child in container.winfo_children(): child.destroy()

        for idx, hora in enumerate(self.horarios_base):
            info = mapa_dados.get(hora)
            ocupado = info is not None
            cor_destaque = "#7E22CE" if ocupado else "#16A34A"
            
            cell = ctk.CTkFrame(container, height=115, corner_radius=10, border_width=1,
                               fg_color="#F3E8FF" if ocupado else "#F0FDF4",
                               border_color="#D8B4FE" if ocupado else "#BBF7D0")
            cell.grid(row=idx // 4, column=idx % 4, padx=6, pady=6, sticky="nsew")
            cell.grid_propagate(False)

            ctk.CTkLabel(cell, text=hora, font=font(14, "bold"), text_color=cor_destaque).pack(pady=(10, 0))
            
            # Nome do Aluno (do banco)
            nome_display = info['nome'] if ocupado else "Disponível"
            ctk.CTkLabel(cell, text=nome_display, font=font(11, "bold" if ocupado else "normal"), 
                        text_color=cor_destaque, wraplength=100).pack()

            btn_color = "#9333EA" if ocupado else "#22C55E"
            ctk.CTkButton(cell, text="Detalhes" if ocupado else "Agendar", height=24, width=85, 
                         fg_color=btn_color, font=font(10, "bold"),
                         command=lambda h=hora, i=info: self.abrir_modal_agendamento(h, i)).pack(side="bottom", pady=10)

    def abrir_modal_agendamento(self, hora, info=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Agendamento")
        modal.geometry("400x500")
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"Horário: {hora}", font=font(18, "bold")).pack(pady=20)
        
        # Dropdown Estudantes
        ctk.CTkLabel(modal, text="Estudante:", anchor="w").pack(fill="x", padx=40)
        combo = ctk.CTkComboBox(modal, values=list(self.mapa_estudantes.keys()), width=300)
        if info: combo.set(info['nome'])
        combo.pack(padx=40, pady=(0, 20))

        ctk.CTkLabel(modal, text="Motivo:", anchor="w").pack(fill="x", padx=40)
        txt_motivo = ctk.CTkTextbox(modal, height=100)
        if info: txt_motivo.insert("1.0", info.get('motivo', ''))
        txt_motivo.pack(fill="x", padx=40, pady=(0, 20))

        def salvar():
            nome_sel = combo.get()
            id_aluno = self.mapa_estudantes.get(nome_sel)
            # Lógica para chamar self.servico_agendamento.criar_agendamento ou atualizar
            modal.destroy()
            self.refresh_all()

        ctk.CTkButton(modal, text="Salvar Agendamento", fg_color="#22C55E", command=salvar).pack(pady=10)

    # Containers de Base
    def criar_container_agenda_dia(self):
        self.card_dia = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        self.card_dia.pack(fill="x", padx=SPACING["page_x"], pady=10)
        ctk.CTkLabel(self.card_dia, text="Horários do Dia", font=font(15, "bold")).pack(anchor="w", padx=20, pady=15)
        ctk.CTkFrame(self.card_dia, fg_color="#E2E8F0", height=1).pack(fill="x", padx=20)
        self.container_grid = ctk.CTkFrame(self.card_dia, fg_color="transparent")
        self.container_grid.pack(fill="x", padx=20, pady=20)
        for i in range(4): self.container_grid.columnconfigure(i, weight=1, uniform="grid")

    def criar_container_proxima_semana(self):
        self.card_semana = ctk.CTkFrame(self, fg_color="white", corner_radius=12, border_width=1, border_color="#E2E8F0")
        self.card_semana.pack(fill="x", padx=SPACING["page_x"], pady=10)
        ctk.CTkLabel(self.card_semana, text="Próxima Sessão (Amanhã)", font=font(15, "bold")).pack(anchor="w", padx=20, pady=15)
        self.container_semana = ctk.CTkFrame(self.card_semana, fg_color="transparent")
        self.container_semana.pack(fill="x", padx=20, pady=20)
        for i in range(4): self.container_semana.columnconfigure(i, weight=1, uniform="grid")

    def abrir_modal_gestao(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Gestão de Grade")
        modal.geometry("350x500")
        modal.grab_set()
        ctk.CTkLabel(modal, text="Horários Ativos", font=font(16, "bold")).pack(pady=10)
        
                # Lista de horários com scroll
        frame_lista = ctk.CTkScrollableFrame(modal, width=320, height=300)
        frame_lista.pack(padx=20, pady=10)

        def atualizar_lista_modal():
            for child in frame_lista.winfo_children(): child.destroy()
            for h in self.horarios_base:
                row = ctk.CTkFrame(frame_lista, fg_color="#F8FAFC")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=h, font=font(13, "bold")).pack(side="left", padx=10)
                ctk.CTkButton(row, text="Remover", width=70, height=22, fg_color="#EF4444", 
                             command=lambda x=h: print(f"Remover {x}")).pack(side="right", padx=5)

        atualizar_lista_modal()

        # Adicionar novo
        ctk.CTkLabel(modal, text="Novo Horário (HH:MM):").pack()
        new_h = ctk.CTkEntry(modal, width=120)
        new_h.pack(pady=5)
        ctk.CTkButton(modal, text="Adicionar à Grade", command=lambda: modal.destroy()).pack(pady=10)
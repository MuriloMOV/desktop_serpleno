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
            self.mapa_estudantes = {str(r['nome']): int(r['id_aluno']) for r in rows} # type: ignore
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
            self.horarios_base = [str(h[0])[:5] for h in cursor.fetchall()] # type: ignore
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
        mapa_dia = {agt['data_hora'].strftime('%H:%M'): agt for agt in agendamentos_dia} # type: ignore
        self.renderizar_grid(self.container_grid, mapa_dia)

        # Carrega "Próxima Semana"
        proxima_semana_str = (self.data_selecionada + timedelta(days=7)).strftime('%Y-%m-%d')
        agendamentos_prox = self.servico_agendamento.listar_agendamentos(data=proxima_semana_str)
        mapa_prox = {agt['data_hora'].strftime('%H:%M'): agt for agt in agendamentos_prox} # type: ignore
        self.renderizar_grid(self.container_semana, mapa_prox)
        self.atualizar_subtitulo_proxima_semana()

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
        ctk.CTkButton(right, text="Gerenciar Horários", width=140, height=42, fg_color="#9333EA", 
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
            
            # Tornar a célula clicável
            cell.bind("<Button-1>", lambda e, h=hora, i=info: self.abrir_modal_agendamento(h, i))
            cell.configure(cursor="hand2")

            ctk.CTkLabel(cell, text=hora, font=font(14, "bold"), text_color=cor_destaque).pack(pady=(10, 0))
            
            # Nome do Aluno (do banco)
            nome_display = info['nome'] if ocupado else "Disponível"
            lbl_nome = ctk.CTkLabel(cell, text=nome_display, font=font(11, "bold" if ocupado else "normal"), 
                        text_color=cor_destaque, wraplength=100)
            lbl_nome.pack()
            lbl_nome.bind("<Button-1>", lambda e, h=hora, i=info: self.abrir_modal_agendamento(h, i))

    def abrir_modal_agendamento(self, hora, info=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Agendamento" if info else "Novo Agendamento")
        modal.geometry("450x650")
        modal.configure(fg_color="white")
        modal.grab_set()

        # Header com Título e Botão Fechar
        header = ctk.CTkFrame(modal, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(header, text="Editar Agendamento" if info else "Novo Agendamento", 
                    font=font(20, "bold"), text_color="#1E293B").pack(side="left", expand=True)
        


        # Container principal com scroll se necessário
        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40)

        # Campo Horário
        ctk.CTkLabel(container, text="Horário:", font=font(13, "bold"), text_color="#1E293B", anchor="w").pack(fill="x", pady=(10, 5))
        combo_hora = ctk.CTkComboBox(container, values=self.horarios_base, width=370, height=45,
                                    fg_color="white", border_color="#E2E8F0", button_color="#F8FAFC",
                                    button_hover_color="#F1F5F9", dropdown_fg_color="white")
        combo_hora.set(hora)
        combo_hora.pack(pady=(0, 15))

        # Campo Estudante
        ctk.CTkLabel(container, text="Estudante:", font=font(13, "bold"), text_color="#1E293B", anchor="w").pack(fill="x", pady=(5, 5))
        combo_estudante = ctk.CTkComboBox(container, values=list(self.mapa_estudantes.keys()), width=370, height=45,
                                         fg_color="white", border_color="#E2E8F0", button_color="#F8FAFC",
                                         button_hover_color="#F1F5F9", dropdown_fg_color="white")
        if info: combo_estudante.set(info['nome'])
        else: combo_estudante.set("Selecione um estudante")
        combo_estudante.pack(pady=(0, 15))

        # Campo Status
        ctk.CTkLabel(container, text="Status:", font=font(13, "bold"), text_color="#1E293B", anchor="w").pack(fill="x", pady=(5, 5))
        combo_status = ctk.CTkComboBox(container, values=["Agendado", "Realizado", "Cancelado", "Faltou"], width=370, height=45,
                                      fg_color="white", border_color="#E2E8F0", button_color="#F8FAFC",
                                      button_hover_color="#F1F5F9", dropdown_fg_color="white")
        if info: combo_status.set(info.get('status', 'Agendado'))
        else: combo_status.set("Agendado")
        combo_status.pack(pady=(0, 15))

        # Campo Observações
        ctk.CTkLabel(container, text="Observações:", font=font(13, "bold"), text_color="#1E293B", anchor="w").pack(fill="x", pady=(5, 5))
        txt_obs = ctk.CTkTextbox(container, height=100, fg_color="white", border_width=1, border_color="#E2E8F0")
        if info: txt_obs.insert("1.0", info.get('motivo', ''))
        txt_obs.pack(fill="x", pady=(0, 15))

        # Campo Trocar Horário
        ctk.CTkLabel(container, text="Trocar Horário com:", font=font(13, "bold"), text_color="#1E293B", anchor="w").pack(fill="x", pady=(5, 5))
        combo_trocar = ctk.CTkComboBox(container, values=["Não trocar"] + list(self.mapa_estudantes.keys()), width=370, height=45,
                                      fg_color="white", border_color="#6366F1", button_color="#F8FAFC",
                                      button_hover_color="#F1F5F9", dropdown_fg_color="white")
        combo_trocar.set("Não trocar")
        combo_trocar.pack(pady=(0, 20))

        # Footer com Botões
        footer = ctk.CTkFrame(modal, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=30, pady=30)

        if info:
            btn_remover = ctk.CTkButton(footer, text="Remover", fg_color="#FEE2E2", text_color="#EF4444",
                                       hover_color="#FECACA", width=100, height=40, font=font(13, "bold"),
                                       command=lambda: self.remover_agendamento(info['id_agendamento'], modal))
            btn_remover.pack(side="left")

        btn_salvar = ctk.CTkButton(footer, text="Salvar", fg_color="#4F46E5", text_color="white",
                                  hover_color="#4338CA", width=100, height=40, font=font(13, "bold"),
                                  command=lambda: self.salvar_agendamento(modal, combo_hora.get(), combo_estudante.get(), combo_status.get(), txt_obs.get("1.0", "end-1c"), info))
        btn_salvar.pack(side="right")

        btn_cancelar = ctk.CTkButton(footer, text="Cancelar", fg_color="#E2E8F0", text_color="#475569",
                                    hover_color="#CBD5E1", width=100, height=40, font=font(13, "bold"),
                                    command=modal.destroy)
        btn_cancelar.pack(side="right", padx=10)

    def salvar_agendamento(self, modal, hora, nome_estudante, status, motivo, info_antiga=None):
        id_aluno = self.mapa_estudantes.get(nome_estudante)
        if not id_aluno:
            messagebox.showerror("Erro", "Selecione um estudante válido.")
            return

        data_hora_str = f"{self.data_selecionada.strftime('%Y-%m-%d')} {hora}:00"
        
        dados = {
            "nome_aluno": nome_estudante,
            "id_aluno": id_aluno,
            "data_hora": data_hora_str,
            "motivo": motivo,
            "status": status
        }

        try:
            if info_antiga:
                # Lógica de Update (precisaria estar no ServicoAgendamento)
                # Por enquanto vamos simular ou usar o que temos
                res = self.servico_agendamento.atualizar_agendamento(info_antiga['id_agendamento'], dados)
            else:
                res = self.servico_agendamento.criar_agendamento(dados)

            if res.get("success"):
                modal.destroy()
                self.refresh_all()
            else:
                messagebox.showerror("Erro", str(res.get("message", "Erro ao salvar agendamento")))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def remover_agendamento(self, id_agendamento, modal):
        if messagebox.askyesno("Confirmar", "Deseja realmente remover este agendamento?"):
            try:
                # Precisaria do método deletar no ServicoAgendamento
                res = self.servico_agendamento.deletar_agendamento(id_agendamento)
                if res.get("success"):
                    modal.destroy()
                    self.refresh_all()
                else:
                    messagebox.showerror("Erro", str(res.get("message", "Erro ao remover agendamento")))
            except Exception as e:
                messagebox.showerror("Erro", f"Erro inesperado: {e}")

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
        
        # Título e subtítulo
        title_frame = ctk.CTkFrame(self.card_semana, fg_color="transparent")
        title_frame.pack(anchor="w", padx=20, pady=15)
        ctk.CTkLabel(title_frame, text="Próxima Semana", font=font(15, "bold")).pack(anchor="w")
        
        self.lbl_subtitulo_semana = ctk.CTkLabel(title_frame, text="", font=font(12, "normal"), text_color="#64748B")
        self.lbl_subtitulo_semana.pack(anchor="w")
        
        self.container_semana = ctk.CTkFrame(self.card_semana, fg_color="transparent")
        self.container_semana.pack(fill="x", padx=20, pady=20)
        for i in range(4): self.container_semana.columnconfigure(i, weight=1, uniform="grid")
        
    def atualizar_subtitulo_proxima_semana(self):
        """Atualiza o subtítulo com a data da próxima semana"""
        proxima_semana = self.data_selecionada + timedelta(days=7)
        dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        dia_nome = dias_semana[proxima_semana.weekday()]
        data_formatada = proxima_semana.strftime(f"{dia_nome}, %d de %B")
        self.lbl_subtitulo_semana.configure(text=data_formatada)

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
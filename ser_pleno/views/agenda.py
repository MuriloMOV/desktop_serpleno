import customtkinter as ctk
from datetime import datetime, timedelta
from services.agendamentos import ServicoAgendamento
# Compat alias para tests
AppointmentService = ServicoAgendamento
import threading
from tkinter import messagebox

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
            edit_lbl.bind("<Button-1>", lambda e, h=hora: self.abrir_gerenciar_agendamento(h))

        # Efeito de Hover simples
        def on_enter(e):
            slot.configure(fg_color=hover_color)
        def on_leave(e):
            slot.configure(fg_color=bg)
            
        slot.bind("<Enter>", on_enter)
        slot.bind("<Leave>", on_leave)

        return slot

    def abrir_novo_agendamento(self, hora=None):
        """Abre modal para criar um novo agendamento (ou editar se hora existir)."""
        modal = ctk.CTkToplevel(self)
        modal.title("Agendar Atendimento")
        modal.geometry("520x380")
        modal.transient(self)

        content = ctk.CTkFrame(modal, fg_color=self.colors["card"], corner_radius=12)
        content.pack(fill="both", expand=True, padx=12, pady=12)

        # Date
        ctk.CTkLabel(content, text="Data (YYYY-MM-DD)", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        date_entry = ctk.CTkEntry(content, fg_color=self.colors["bg_alt"], placeholder_text=self.data_atual.strftime('%Y-%m-%d'))
        date_entry.pack(fill="x", pady=(4, 8))

        # Time selection
        ctk.CTkLabel(content, text="Horário", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        time_var = ctk.StringVar()
        time_menu = ctk.CTkOptionMenu(content, values=["Carregando..."], variable=time_var, fg_color=self.colors["bg_alt"], button_color=self.colors["bg_alt"], corner_radius=RADIUS["input"]) 
        time_menu.pack(fill="x", pady=(4, 8))

        # Student selection
        ctk.CTkLabel(content, text="Estudante", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        student_var = ctk.StringVar()
        student_menu = ctk.CTkOptionMenu(content, values=["Carregando..."], variable=student_var, fg_color=self.colors["bg_alt"], button_color=self.colors["bg_alt"], corner_radius=RADIUS["input"]) 
        student_menu.pack(fill="x", pady=(4, 8))

        # Notes
        ctk.CTkLabel(content, text="Observações", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        notes = ctk.CTkTextbox(content, height=80, fg_color=self.colors["bg_alt"], corner_radius=8)
        notes.pack(fill="both", pady=(6, 8))

        # Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(fill="x")
        ctk.CTkButton(actions, text="Cancelar", fg_color=self.colors["bg_alt"], command=modal.destroy).pack(side="right", padx=8)

        def submit():
            payload = {
                'date': date_entry.get().strip() or self.data_atual.strftime('%Y-%m-%d'),
                'time': time_var.get(),
                'student_id': getattr(modal, '_students_map', {}).get(student_var.get()),
                'notes': notes.get('1.0', 'end').strip()
            }
            self.criar_agendamento(payload)
            modal.destroy()

        ctk.CTkButton(actions, text="Agendar", fg_color=self.colors["primary"], text_color="white", command=submit).pack(side="right")

        # Load lookups async
        def load_lookups():
            times_resp = self.servico_agendamento.listar_horarios_disponiveis(data=self.data_atual.strftime('%Y-%m-%d'))
            t_list = []
            if isinstance(times_resp, dict):
                t_list = times_resp.get('data', [])
            # Students
            from services.estudantes import ServicoEstudante
            ss = ServicoEstudante()
            students_resp = ss.listar_estudantes()
            s_list = []
            s_map = {}
            if students_resp:
                for s in students_resp.get('data', []):
                    label = f"{s.get('name')} ({s.get('id')})"
                    s_list.append(label)
                    s_map[label] = s.get('id')

            def apply():
                if t_list:
                    time_menu.configure(values=[t for t in t_list])
                    time_var.set(t_list[0])
                else:
                    time_menu.configure(values=["08:00", "09:00", "10:00"])
                    time_var.set("08:00")

                if s_list:
                    student_menu.configure(values=s_list)
                    student_var.set(s_list[0])
                else:
                    student_menu.configure(values=["Nenhum estudante disponível"])
                    student_var.set("Nenhum estudante disponível")

                modal._students_map = s_map

            self.after(0, apply)

        threading.Thread(target=load_lookups, daemon=True).start()

    def abrir_gerenciar_agendamento(self, hora):
        """Abre modal para gerenciar um agendamento existente (editar / cancelar)."""
        appt = self.appointments.get(hora)
        if not appt:
            print("Agendamento não encontrado para", hora)
            return

        modal = ctk.CTkToplevel(self)
        modal.title("Gerenciar Agendamento")
        modal.geometry("520x380")
        modal.transient(self)

        content = ctk.CTkFrame(modal, fg_color=self.colors["card"], corner_radius=12)
        content.pack(fill="both", expand=True, padx=12, pady=12)

        # Data (read-only)
        ctk.CTkLabel(content, text="Data (YYYY-MM-DD)", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        date_entry = ctk.CTkEntry(content, fg_color=self.colors["bg_alt"], placeholder_text=appt.get('date', self.data_atual.strftime('%Y-%m-%d')))
        date_entry.insert(0, appt.get('date', self.data_atual.strftime('%Y-%m-%d')))
        date_entry.pack(fill="x", pady=(4, 8))

        # Time (read-only)
        ctk.CTkLabel(content, text="Horário", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        time_var = ctk.StringVar(value=hora)
        time_menu = ctk.CTkOptionMenu(content, values=[hora], variable=time_var, fg_color=self.colors["bg_alt"], button_color=self.colors["bg_alt"], corner_radius=RADIUS["input"]) 
        time_menu.pack(fill="x", pady=(4, 8))

        # Student (selectable)
        ctk.CTkLabel(content, text="Estudante", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        student_var = ctk.StringVar()
        student_menu = ctk.CTkOptionMenu(content, values=["Carregando..."], variable=student_var, fg_color=self.colors["bg_alt"], button_color=self.colors["bg_alt"], corner_radius=RADIUS["input"]) 
        student_menu.pack(fill="x", pady=(4, 8))

        # Notes
        ctk.CTkLabel(content, text="Observações", font=font(11, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        notes = ctk.CTkTextbox(content, height=80, fg_color=self.colors["bg_alt"], corner_radius=8)
        notes.pack(fill="both", pady=(6, 8))
        notes.insert("1.0", appt.get('notes', ""))

        # Actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(fill="x")
        ctk.CTkButton(actions, text="Cancelar", fg_color=self.colors["bg_alt"], command=modal.destroy).pack(side="right", padx=8)

        def do_update():
            payload = {
                'date': date_entry.get().strip() or appt.get('date'),
                'time': time_var.get(),
                'student_id': getattr(modal, '_students_map', {}).get(student_var.get()),
                'notes': notes.get('1.0', 'end').strip()
            }
            self.atualizar_agendamento(appt.get('id'), payload)
            modal.destroy()

        def do_delete():
            if messagebox.askyesno("Confirmar", "Deseja realmente cancelar este agendamento?"):
                self.deletar_agendamento(appt.get('id'))
                modal.destroy()

        ctk.CTkButton(actions, text="Excluir", fg_color="#ef4444", text_color="white", command=do_delete).pack(side="right", padx=8)
        ctk.CTkButton(actions, text="Salvar", fg_color=self.colors["primary"], text_color="white", command=do_update).pack(side="right")

        # Load students async and preselect the current one
        def load_students():
            from services.estudantes import ServicoEstudante
            ss = ServicoEstudante()
            students_resp = ss.listar_estudantes()
            s_list = []
            s_map = {}
            current_label = None
            if students_resp:
                for s in students_resp.get('data', []):
                    label = f"{s.get('name')} ({s.get('id')})"
                    s_list.append(label)
                    s_map[label] = s.get('id')
                    if s.get('name') == appt.get('student', {}).get('name'):
                        current_label = label

            def apply():
                if s_list:
                    student_menu.configure(values=s_list)
                    student_var.set(current_label or s_list[0])
                else:
                    student_menu.configure(values=["Nenhum estudante disponível"])
                    student_var.set("Nenhum estudante disponível")
                modal._students_map = s_map

            self.after(0, apply)

        threading.Thread(target=load_students, daemon=True).start()

    def atualizar_agendamento(self, id_agendamento, dados):
        """Wrapper to update appointment via service and reload data."""
        res = self.servico_agendamento.atualizar_agendamento(id_agendamento, dados)
        ok = False
        if isinstance(res, dict):
            ok = res.get('success', False)
        else:
            ok = getattr(res, 'status_code', 200) in (200, 201)

        if ok:
            try:
                self.load_data()
            except Exception:
                pass
        else:
            print('Erro ao atualizar agendamento:', res)

    def deletar_agendamento(self, id_agendamento):
        """Wrapper to delete appointment via service and reload data."""
        res = self.servico_agendamento.deletar_agendamento(id_agendamento)
        ok = False
        if isinstance(res, dict):
            ok = res.get('success', False)
        else:
            ok = getattr(res, 'status_code', 200) in (200, 204)

        if ok:
            try:
                self.load_data()
            except Exception:
                pass
        else:
            print('Erro ao deletar agendamento:', res)

    def criar_agendamento(self, dados):
        """Cria um agendamento via serviço e recarrega os dados da agenda."""
        if not dados.get('time') or not dados.get('student_id'):
            print("Dados incompletos para agendamento")
            return
        res = self.servico_agendamento.criar_agendamento(dados)
        ok = False
        if isinstance(res, dict):
            ok = res.get('success', False)
        else:
            ok = getattr(res, 'status_code', 200) in (200, 201)

        if ok:
            try:
                self.load_data()
            except Exception:
                pass
        else:
            print('Erro ao criar agendamento:', res)

    def gerar_ics(self, dados):
        """Gera um conteúdo ICS simples para o agendamento (retorna string)."""
        dt = f"{dados.get('date')}T{dados.get('time').replace(':', '')}00"
        ics = (
            "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//SerPleno//EN\nBEGIN:VEVENT\n"
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n"
            f"DTSTART:{dt}\n"
            f"SUMMARY:Atendimento - {dados.get('student_name', 'Estudante')}\n"
            f"DESCRIPTION:{dados.get('notes', '')}\n"
            "END:VEVENT\nEND:VCALENDAR"
        )
        return ics

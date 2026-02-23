import customtkinter as ctk
from PIL import Image
import os
import json
import threading
from datetime import datetime
from tkinter import messagebox
from ui_theme import THEME, SPACING, RADIUS, font
from views.backup_dialog import BackupDialog
from services.configuracoes import servico_configuracoes


class ConfiguracoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.colors = THEME
        self._images = {}
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.render_layout()

    def load_image(self, name, size):
        try:
            cache_key = f"{name}:{size}"
            if cache_key in self._images:
                return self._images[cache_key]
            path = os.path.join(self.base_path, "assets", "avatars", name)
            if os.path.exists(path):
                img = ctk.CTkImage(light_image=Image.open(path), size=size)
                self._images[cache_key] = img
                return img
        except Exception as e:
            print(f"Erro ao carregar imagem {name}: {e}")
            return None

    def render_layout(self):
        header = self.criar_secao_header("Preferências do Sistema", "Personalize sua experiência no SerPleno", show_actions=True)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=SPACING["page_x"], pady=(20, 10))

        col_left = ctk.CTkFrame(self, fg_color="transparent")
        col_left.grid(row=1, column=0, sticky="nsew", padx=(SPACING["page_x"], 10))
        
        self.render_cartao_pessoal(col_left)

        col_right = ctk.CTkFrame(self, fg_color="transparent")
        col_right.grid(row=1, column=1, sticky="nsew", padx=(10, SPACING["page_x"]))
        
        self.render_central_avisos(col_right)
        self.render_aparencia(col_right)
        self.render_seguranca(col_right)
        self.render_backup_section(col_right)
        self.render_sync_section(col_right)

    def criar_secao_header(self, title, subtitle, show_actions=False):
        frame = ctk.CTkFrame(self, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        icon_box = ctk.CTkFrame(inner, width=40, height=40, corner_radius=8, fg_color="#EEF2FF")
        icon_box.pack(side="left", padx=(0, 15))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="⚙️", font=font(18)).place(relx=0.5, rely=0.5, anchor="center")

        txt_box = ctk.CTkFrame(inner, fg_color="transparent")
        txt_box.pack(side="left")
        ctk.CTkLabel(txt_box, text=title, font=font(14, "bold")).pack(anchor="w")
        ctk.CTkLabel(txt_box, text=subtitle, font=font(11), text_color=self.colors["text_muted"]).pack(anchor="w")

        if show_actions:
            actions = ctk.CTkFrame(inner, fg_color="transparent")
            actions.pack(side="right")
            ctk.CTkButton(actions, text="Descartar", fg_color="transparent", text_color=self.colors["text_muted"], width=80).pack(side="left", padx=5)
            ctk.CTkButton(actions, text="✓", fg_color="#4F46E5", width=35, height=35).pack(side="left")
        return frame

    def render_cartao_pessoal(self, container):
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="both", expand=True)
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="👤 Informações Pessoais", font=font(14, "bold")).pack(side="left")

        # Carregar avatar salvo no perfil
        try:
            with open(os.path.join(self.base_path, "user_profile.json"), "r") as f:
                profile = json.load(f)
            avatar_name = profile.get("avatar", "avatar-1.jpg")
        except Exception as e:
            print(f"Erro ao carregar perfil: {e}")
            avatar_name = "avatar-1.jpg"
        
        self.avatar_display = ctk.CTkLabel(card, text="", image=self.load_image(avatar_name, (160, 160)))
        self.avatar_display.pack(pady=10)

        change_btn = ctk.CTkButton(card, text="Toque para alterar imagem", fg_color="transparent", text_color="#4F46E5", font=font(11, "bold"), command=self.toggle_gallery)
        change_btn.pack()

        self.gallery_frame = ctk.CTkFrame(card, fg_color=self.colors["bg_alt"], corner_radius=12)
        self.grid_galeria = ctk.CTkFrame(self.gallery_frame, fg_color="transparent")
        self.grid_galeria.pack(padx=10, pady=10)
        
        # Carregar todos os avatares disponíveis na pasta assets/avatars
        avatars_dir = os.path.join(self.base_path, "assets", "avatars")
        try:
            avatar_files = [f for f in os.listdir(avatars_dir) if f.startswith("avatar-") and f.endswith(".jpg")]
            avatar_files.sort()
            print(f"Avatars carregados: {avatar_files}")
        except Exception as e:
            print(f"Erro ao listar avatares: {e}")
            avatar_files = []
        
        for i, filename in enumerate(avatar_files):
            btn = ctk.CTkButton(
                self.grid_galeria, 
                text="", 
                image=self.load_image(filename, (50, 50)), 
                width=50, 
                height=50, 
                fg_color="white", 
                command=lambda x=filename: self.update_avatar(x)
            )
            btn.grid(row=i//3, column=i%3, padx=2, pady=2)

        # Usar dados do usuário logado
        if self.controller.usuario_logado:
            nome_usuario = f"{self.controller.usuario_logado.get('first_name', '')} {self.controller.usuario_logado.get('last_name', '')}".strip()
            nome_usuario = nome_usuario if nome_usuario else self.controller.usuario_logado.get('username', 'Usuário')
            email_usuario = self.controller.usuario_logado.get('email', 'email@exemplo.com')
        else:
            nome_usuario = 'Usuário'
            email_usuario = 'email@exemplo.com'

        self.criar_input_field(card, "Nome de exibição", nome_usuario, "👤")
        self.criar_input_field(card, "Endereço de E-mail", email_usuario, "📧")

    def toggle_gallery(self):
        if self.gallery_frame.winfo_ismapped():
            self.gallery_frame.pack_forget()
        else:
            self.gallery_frame.pack(fill="x", padx=20, pady=10, before=self.avatar_display)

    def update_avatar(self, filename):
        img = self.load_image(filename, (160, 160))
        if img: 
            self.avatar_display.configure(image=img)
            # Salvar a escolha do avatar no perfil
            try:
                with open(os.path.join(self.base_path, "user_profile.json"), "w") as f:
                    json.dump({"avatar": filename}, f)
            except Exception as e:
                print(f"Erro ao salvar avatar: {e}")
        self.gallery_frame.pack_forget()

    def render_central_avisos(self, container):
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="x", pady=(0, 15))
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="🔔 Central de Avisos", font=font(14, "bold")).pack(side="left")
        ctk.CTkLabel(h, text="Tempo Real", font=font(9, "bold"), fg_color="#FEF3C7", text_color="#92400E", corner_radius=4, padx=8).pack(side="right")

        items = [
            ("Mensagens Diretas", "Alertar novos chats privados e mural"),
            ("Pedidos de Ajuda", "Notificações críticas de suporte ao aluno"),
            ("Feedback de Alunos", "Novas avaliações e comentários"),
            ("Efeitos Sonoros", "Feedback auditivo para alertas")
        ]
        self.notification_switches = {}
        for t, s in items:
            switch = self.criar_toggle_row(card, t, s)
            self.notification_switches[t] = switch
            # Adicionar funcionalidade ao switch
            switch.configure(command=lambda switch=switch, t=t: self.toggle_notification(t, switch))

    def toggle_notification(self, notification_type, switch):
        """Função para tratar a alternância de notificações"""
        estado = switch.get()
        print(f"Notificação '{notification_type}' {'ativada' if estado else 'desativada'}")
        # Aqui você poderia salvar a preferência no banco de dados ou arquivo de configuração

    def render_aparencia(self, container):
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="x", pady=(0, 15))
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="🌎 Aparência & Acessibilidade", font=font(14, "bold")).pack(side="left")

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=10)
        self.theme_select = self.criar_select(row, "Esquema de Cores", ["Modo Sereno (Claro)", "Modo Foco (Escuro)"])
        self.theme_select.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.font_select = self.criar_select(row, "Escala de Texto", ["Padrão (16px)", "Grande (18px)"])
        self.font_select.pack(side="left", expand=True, fill="x")

        tip = ctk.CTkFrame(card, fg_color="#F8FAFC", corner_radius=8, border_width=1, border_color="#E2E8F0")
        tip.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkLabel(tip, text="📝 Dica de Produtividade", font=font(11, "bold")).pack(anchor="w", padx=15, pady=(8, 0))
        ctk.CTkLabel(tip, text="O Modo Foco reduz a emissão de luz azul, ideal para sessões noturnas.", font=font(10), text_color="#64748B", wraplength=400).pack(anchor="w", padx=15, pady=(0, 8))

    def render_seguranca(self, container):
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="x")
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="🛡️ Sessão & Segurança", font=font(14, "bold")).pack(side="left")

        self.criar_item_lista(card, "👥", "Perfil Público", "Permitir que outros visualizem suas conquistas", toggle=True)
        self.criar_item_lista(card, "🔑", "Credenciais", "Última alteração há 3 meses", btn_text="Alterar Senha")
        self.criar_item_lista(card, "💻", "Este Dispositivo", "Sessão ativa agora • Windows Desktop", btn_text="Encerrar Acesso", danger=True)

    def alterar_configuracao(self, valor):
        """Função para tratar alterações nas opções de aparência"""
        print(f"Configuração alterada para: {valor}")
        # Aqui você poderia implementar a lógica para alterar o tema ou a escala de texto
        if valor == "Modo Sereno (Claro)":
            ctk.set_appearance_mode("light")
        elif valor == "Modo Foco (Escuro)":
            ctk.set_appearance_mode("dark")

    def toggle_seguranca_opcao(self, opcao, switch):
        """Função para tratar alternância de opções de segurança"""
        estado = switch.get()
        print(f"Opção '{opcao}' {'ativada' if estado else 'desativada'}")

    def clicar_botao_seguranca(self, btn_text):
        """Função para tratar cliques em botões de segurança"""
        if btn_text == "Alterar Senha":
            self.abrir_tela_alterar_senha()
        elif btn_text == "Encerrar Acesso":
            self.encerrar_sessao()

    def abrir_tela_alterar_senha(self):
        """Abre uma tela para alterar a senha do usuário"""
        top = ctk.CTkToplevel(self)
        top.title("Alterar Senha")
        top.geometry("400x300")
        top.resizable(False, False)
        
        # Centralizar a janela
        top.update_idletasks()
        x = (top.winfo_screenwidth() // 2) - (400 // 2)
        y = (top.winfo_screenheight() // 2) - (300 // 2)
        top.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(top, fg_color=THEME["card"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Alterar Senha", font=font(16, "bold")).pack(pady=(0, 20))
        
        # Campo para senha atual
        self.senha_atual_entry = self.criar_input_field(frame, "Senha Atual", "", "🔒")
        
        # Campo para nova senha
        self.nova_senha_entry = self.criar_input_field(frame, "Nova Senha", "", "🔑")
        
        # Campo para confirmar nova senha
        self.confirmar_senha_entry = self.criar_input_field(frame, "Confirmar Senha", "", "🔑")
        
        # Botão para salvar
        btn_salvar = ctk.CTkButton(frame, text="Salvar Alterações", fg_color="#4F46E5", hover_color="#4338CA", font=font(12, "bold"), command=self.salvar_alteracao_senha)
        btn_salvar.pack(fill="x", pady=(20, 0))

    def salvar_alteracao_senha(self):
        """Salva a alteração de senha"""
        senha_atual = self.senha_atual_entry.get()
        nova_senha = self.nova_senha_entry.get()
        confirmar_senha = self.confirmar_senha_entry.get()
        
        if nova_senha != confirmar_senha:
            print("As senhas não coincidem")
            return
        
        if len(nova_senha) < 6:
            print("Senha deve ter pelo menos 6 caracteres")
            return
        
        print("Senha alterada com sucesso")

    def encerrar_sessao(self):
        """Encerra a sessão do usuário"""
        self.controller.mostrar_login()

    def criar_toggle_row(self, parent, title, sub):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=10)
        txt = ctk.CTkFrame(f, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(txt, text=title, font=font(12, "bold")).pack(anchor="w")
        ctk.CTkLabel(txt, text=sub, font=font(10), text_color="#64748B").pack(anchor="w")
        switch = ctk.CTkSwitch(f, text="", progress_color="#4F46E5")
        switch.pack(side="right")
        return switch

    def criar_input_field(self, parent, label, val, icon):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(f, text=label, font=font(10, "bold"), text_color="#64748B").pack(anchor="w")
        entry_f = ctk.CTkFrame(f, fg_color="#F8FAFC", height=35, corner_radius=6, border_width=1, border_color="#E2E8F0")
        entry_f.pack(fill="x", pady=4)
        entry_f.pack_propagate(False)
        ctk.CTkLabel(entry_f, text=icon, padx=10).pack(side="left")
        e = ctk.CTkEntry(entry_f, fg_color="transparent", border_width=0, font=font(11))
        e.pack(side="left", fill="both", expand=True)
        e.insert(0, val)
        return e

    def criar_select(self, parent, label, opts):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(f, text=label, font=font(10, "bold"), text_color="#64748B").pack(anchor="w")
        option_menu = ctk.CTkOptionMenu(f, values=opts, fg_color="#F8FAFC", text_color="black", button_color="#F8FAFC", button_hover_color="#E2E8F0", height=35, command=self.alterar_configuracao)
        option_menu.pack(fill="x", pady=4)
        return f

    def criar_item_lista(self, parent, icon, title, sub, toggle=False, btn_text=None, danger=False):
        f = ctk.CTkFrame(parent, fg_color="transparent", border_width=1, border_color="#F1F5F9", corner_radius=8)
        f.pack(fill="x", padx=20, pady=5)
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        
        ctk.CTkLabel(inner, text=icon, font=font(16), fg_color="#F1F5F9", width=35, height=35, corner_radius=6).pack(side="left", padx=(0, 12))
        
        txt = ctk.CTkFrame(inner, fg_color="transparent")
        txt.pack(side="left")
        ctk.CTkLabel(txt, text=title, font=font(12, "bold")).pack(anchor="w")
        ctk.CTkLabel(txt, text=sub, font=font(10), text_color="#64748B").pack(anchor="w")

        if toggle:
            switch = ctk.CTkSwitch(inner, text="", progress_color="#4F46E5")
            switch.pack(side="right")
            switch.configure(command=lambda switch=switch, title=title: self.toggle_seguranca_opcao(title, switch))
        elif btn_text:
            color = "#EF4444" if danger else "#4F46E5"
            btn = ctk.CTkButton(inner, text=btn_text, font=font(10, "bold"), fg_color="transparent", text_color=color, hover_color="#FEF2F2" if danger else "#EEF2FF", width=100, command=lambda btn_text=btn_text: self.clicar_botao_seguranca(btn_text))
            btn.pack(side="right")

    def render_backup_section(self, container):
        """Renderiza seção de backup e restore"""
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="x", pady=(0, 15))
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="💾 Backup e Restore", font=font(14, "bold")).pack(side="left")
        
        # Status do backup
        status_frame = ctk.CTkFrame(card, fg_color="transparent")
        status_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            status_frame, 
            text="Último backup: Não realizado", 
            font=font(10),
            text_color=self.colors["text_muted"]
        ).pack(anchor="w")
        
        # Botões de ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        backup_btn = ctk.CTkButton(
            btn_frame,
            text="💾 Fazer Backup",
            font=font(11, "bold"),
            fg_color="#4F46E5",
            hover_color="#4338CA",
            height=36,
            command=self.abrir_dialog_backup
        )
        backup_btn.pack(side="left", padx=(0, 10))
        
        restore_btn = ctk.CTkButton(
            btn_frame,
            text="📂 Restaurar",
            font=font(11),
            fg_color="#F8FAFC",
            text_color="#4F46E5",
            hover_color="#EEF2FF",
            height=36,
            command=self.abrir_dialog_backup
        )
        restore_btn.pack(side="left")
        
        # Opções de backup automático
        self.criar_item_lista(
            card, "⏰", "Backup Automático", 
            "Realizar backup diário às 02:00", 
            toggle=True
        )
        
        self.criar_item_lista(
            card, "🗂️", "Local de Backup",
            "Pasta padrão: /backups",
            btn_text="Alterar"
        )

    def render_sync_section(self, container):
        """Renderiza seção de sincronização"""
        card = ctk.CTkFrame(container, fg_color=self.colors["card"], corner_radius=RADIUS["card"])
        card.pack(fill="x", pady=(0, 15))
        
        h = ctk.CTkFrame(card, fg_color="transparent")
        h.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(h, text="🔄 Sincronização", font=font(14, "bold")).pack(side="left")
        
        # Status de sincronização (será atualizado dinamicamente)
        self.sync_status_frame = ctk.CTkFrame(card, fg_color="#F0FDF4", corner_radius=8)
        self.sync_status_frame.pack(fill="x", padx=20, pady=5)
        
        self.sync_status_inner = ctk.CTkFrame(self.sync_status_frame, fg_color="transparent")
        self.sync_status_inner.pack(fill="x", padx=12, pady=8)
        
        self.sync_status_indicator = ctk.CTkLabel(
            self.sync_status_inner,
            text="●",
            font=font(12),
            text_color="#22C55E"
        )
        self.sync_status_indicator.pack(side="left", padx=(0, 8))
        
        self.sync_status_text = ctk.CTkLabel(
            self.sync_status_inner,
            text="Verificando conexão...",
            font=font(11),
            text_color="#166534"
        )
        self.sync_status_text.pack(side="left")
        
        self.sync_last_time = ctk.CTkLabel(
            self.sync_status_inner,
            text="",
            font=font(10),
            text_color="#64748B"
        )
        self.sync_last_time.pack(side="right")
        
        # Botão de teste de conexão
        test_frame = ctk.CTkFrame(card, fg_color="transparent")
        test_frame.pack(fill="x", padx=20, pady=5)
        
        test_btn = ctk.CTkButton(
            test_frame,
            text="🔍 Testar Conexão",
            font=font(10),
            fg_color="#EEF2FF",
            text_color="#4F46E5",
            hover_color="#E0E7FF",
            height=28,
            command=self.testar_conexao
        )
        test_btn.pack(side="left")
        
        # Opções de sincronização
        self.criar_item_lista(
            card, "📡", "Sincronização Automática",
            "Sincronizar dados a cada 5 minutos",
            toggle=True
        )
        
        self.criar_item_lista(
            card, "📱", "Modo Offline",
            "Trabalhar sem conexão e sincronizar depois",
            toggle=True
        )
        
        # Botão de sincronização manual
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        self.sync_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Sincronizar Agora",
            font=font(11),
            fg_color="#F8FAFC",
            text_color="#4F46E5",
            hover_color="#EEF2FF",
            height=36,
            command=self.sincronizar_agora
        )
        self.sync_btn.pack(side="left")
        
        # Indicador de progresso
        self.sync_progress = ctk.CTkProgressBar(btn_frame, width=150, mode="indeterminate")
        
        # Indicador de conflitos (será atualizado dinamicamente)
        self.conflitos_frame = ctk.CTkFrame(card, fg_color="#FEF3C7", corner_radius=8)
        
        self.conflitos_inner = ctk.CTkFrame(self.conflitos_frame, fg_color="transparent")
        self.conflitos_inner.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(
            self.conflitos_inner,
            text="⚠️",
            font=font(12)
        ).pack(side="left", padx=(0, 8))
        
        self.conflitos_text = ctk.CTkLabel(
            self.conflitos_inner,
            text="0 conflitos pendentes",
            font=font(11),
            text_color="#92400E"
        )
        self.conflitos_text.pack(side="left")
        
        resolver_btn = ctk.CTkButton(
            self.conflitos_inner,
            text="Resolver",
            font=font(10),
            fg_color="#F59E0B",
            hover_color="#D97706",
            height=28,
            width=80,
            command=self.abrir_dialog_conflitos
        )
        resolver_btn.pack(side="right")
        
        # Carregar status inicial
        self.atualizar_status_sync()
    
    def testar_conexao(self):
        """Testa a conexão com a API e banco de dados"""
        def _testar():
            # Testar API
            resultado_api = servico_configuracoes.testar_conexao_api()
            resultado_banco = servico_configuracoes.testar_conexao_banco()
            
            # Atualizar UI na thread principal
            self.after(0, lambda: self._mostrar_resultado_teste(resultado_api, resultado_banco))
        
        threading.Thread(target=_testar, daemon=True).start()
    
    def _mostrar_resultado_teste(self, resultado_api, resultado_banco):
        """Mostra o resultado do teste de conexão"""
        api_ok = resultado_api.get("success", False)
        banco_ok = resultado_banco.get("success", False)
        
        mensagem = "Resultado do Teste de Conexão:\n\n"
        mensagem += f"📡 API: {'✅ Online' if api_ok else '❌ Offline'}\n"
        if api_ok:
            mensagem += f"   Latência: {resultado_api.get('latency_ms', 0):.0f}ms\n"
        else:
            mensagem += f"   Erro: {resultado_api.get('message', 'Desconhecido')}\n"
        
        mensagem += f"\n💾 Banco de Dados: {'✅ Online' if banco_ok else '❌ Offline'}\n"
        if banco_ok:
            mensagem += f"   Latência: {resultado_banco.get('latency_ms', 0):.0f}ms\n"
        else:
            mensagem += f"   Erro: {resultado_banco.get('message', 'Desconhecido')}\n"
        
        # Atualizar status visual
        if api_ok:
            self.sync_status_frame.configure(fg_color="#F0FDF4")
            self.sync_status_indicator.configure(text_color="#22C55E")
            self.sync_status_text.configure(
                text="Conectado ao servidor",
                text_color="#166534"
            )
        else:
            self.sync_status_frame.configure(fg_color="#FEF2F2")
            self.sync_status_indicator.configure(text_color="#EF4444")
            self.sync_status_text.configure(
                text="Servidor indisponível",
                text_color="#991B1B"
            )
        
        messagebox.showinfo("Teste de Conexão", mensagem)
    
    def atualizar_status_sync(self):
        """Atualiza o status de sincronização"""
        def _carregar():
            status = servico_configuracoes.obter_status_sincronizacao()
            self.after(0, lambda: self._atualizar_ui_sync(status))
        
        threading.Thread(target=_carregar, daemon=True).start()
    
    def _atualizar_ui_sync(self, status):
        """Atualiza a UI com o status de sincronização"""
        data = status.get("data", {})
        
        # Atualizar última sincronização
        last_sync = data.get("last_sync")
        if last_sync:
            try:
                dt = datetime.fromisoformat(last_sync)
                diff = datetime.now() - dt
                if diff.total_seconds() < 60:
                    tempo = "há menos de 1 minuto"
                elif diff.total_seconds() < 3600:
                    tempo = f"há {int(diff.total_seconds() / 60)} minutos"
                else:
                    tempo = f"há {int(diff.total_seconds() / 3600)} horas"
                self.sync_last_time.configure(text=f"Última sync: {tempo}")
            except Exception:
                self.sync_last_time.configure(text=f"Última sync: {last_sync}")
        
        # Atualizar conflitos
        conflitos = data.get("conflicts", 0)
        if conflitos > 0:
            self.conflitos_frame.pack(fill="x", padx=20, pady=(0, 20))
            self.conflitos_text.configure(text=f"{conflitos} conflitos pendentes")
        else:
            self.conflitos_frame.pack_forget()
    
    def abrir_dialog_conflitos(self):
        """Abre diálogo para resolver conflitos"""
        messagebox.showinfo(
            "Resolver Conflitos",
            "Não há conflitos para resolver no momento.\n\n"
            "Todos os dados estão sincronizados."
        )

    def abrir_dialog_backup(self):
        """Abre o diálogo de backup"""
        BackupDialog(self.winfo_toplevel())

    def sincronizar_agora(self):
        """Executa sincronização manual"""
        # Mostrar progresso
        self.sync_progress.pack(side="left", padx=10)
        self.sync_progress.start()
        self.sync_btn.configure(state="disabled", text="Sincronizando...")
        
        def _on_complete(resultado):
            self.after(0, lambda: self._sync_complete(resultado))
        
        servico_configuracoes.sincronizar(on_complete=_on_complete)
    
    def _sync_complete(self, resultado):
        """Callback quando sincronização termina"""
        self.sync_progress.stop()
        self.sync_progress.pack_forget()
        self.sync_btn.configure(state="normal", text="🔄 Sincronizar Agora")
        
        if resultado.get("success"):
            itens = resultado.get("items_synced", 0)
            pendentes = resultado.get("items_pending", 0)
            messagebox.showinfo(
                "Sincronização Concluída",
                f"Sincronização realizada com sucesso!\n\n"
                f"✅ {itens} itens sincronizados\n"
                f"⏳ {pendentes} itens pendentes"
            )
            # Atualizar status
            self.atualizar_status_sync()
        else:
            erro = resultado.get("error", "Erro desconhecido")
            messagebox.showerror(
                "Erro na Sincronização",
                f"Não foi possível completar a sincronização.\n\n"
                f"Erro: {erro}"
            )

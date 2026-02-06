import customtkinter as ctk
from PIL import Image
import os
import datetime
import threading
import time

from ui_theme import THEME, SPACING, RADIUS, font
from services.comunicacao import ServicoComunicacao

class ComunicacaoInternaFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico = ServicoComunicacao()

        self.colors = THEME

        # Caminhos de imagens
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.img_path = os.path.join(self.base_path, "..", "imagens")

        # Dados da conversa
        self.contatos = []
        self.conversa_atual = None
        self.mensagens = []
        self.atualizando = False

        # Grid layout principal (Sidebar + Chat Area)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============= 1. Sidebar (Lista de Contatos) =============
        self.criar_sidebar()

        # ============= 2. Chat Area (Conversa Ativa) =============
        self.criar_chat_area()

        # Carregar dados inicial
        self.carregar_contatos()

    def load_image(self, name, size):
        try:
            if not hasattr(self, "_images"):
                self._images = {}
            cache_key = f"{name}:{size}"
            if cache_key in self._images:
                return self._images[cache_key]

            candidates = [
                os.path.join(self.img_path, name),
                os.path.join(self.base_path, "assets", "avatars", name),
                os.path.join(self.base_path, "..", "imagens", name),
            ]
            for path in candidates:
                if path and os.path.exists(path):
                    img = ctk.CTkImage(light_image=Image.open(path), size=size)
                    self._images[cache_key] = img
                    return img
        except Exception as e:
            print(f"Erro ao carregar imagem {name}: {e}")
        return None

    def carregar_contatos(self):
        """Carrega contatos da API em thread separada"""
        def task():
            try:
                data = self.servico.listar_contatos()
                if data and 'results' in data:
                    self.contatos = data['results']
                    self.atualizar_lista_contatos()
                    # Selecionar primeira conversa
                    if self.contatos:
                        self.selecionar_conversa(self.contatos[0])
            except Exception as e:
                print(f"Erro ao carregar contatos: {e}")
        
        threading.Thread(target=task, daemon=True).start()

    def atualizar_lista_contatos(self):
        """Atualiza a lista de contatos na sidebar"""
        # Limpar contatos existentes
        for widget in self.scroll_contacts.winfo_children():
            widget.destroy()
        
        for i, contato in enumerate(self.contatos):
            self.criar_contato_item(contato, is_first=(i==0))

    def criar_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=self.colors["card"], width=320, corner_radius=0, border_width=1, border_color=self.colors["border"])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # Header Sidebar
        header = ctk.CTkFrame(sidebar, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=25)
        
        header_text = ctk.CTkFrame(header, fg_color="transparent")
        header_text.pack(side="left")
        ctk.CTkLabel(
            header_text,
            text="Mensagens",
            font=font(20, "bold"),
            text_color=self.colors["text"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            header_text,
            text="Conversas internas e suporte",
            font=font(12),
            text_color=self.colors["text_muted"]
        ).pack(anchor="w")
        
        btn_new = ctk.CTkButton(
            header, text="+", width=35, height=35, corner_radius=18, 
            fg_color=self.colors["primary_light"], text_color=self.colors["primary"],
            hover_color="#E0E7FF", font=font(20, "bold")
        )
        btn_new.pack(side="right")

        # Busca
        search_frame = ctk.CTkFrame(sidebar, fg_color=self.colors["bg_alt"], height=45, corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        search_frame.pack(fill="x", padx=20, pady=(0, 20))
        search_frame.pack_propagate(False)
        
        ctk.CTkLabel(search_frame, text="🔍", font=font(14), text_color=self.colors["text_highlight"]).pack(side="left", padx=12)
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar conversas...", fg_color="transparent", border_width=0, font=font(13))
        self.search_entry.pack(side="left", fill="both", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda e: self.filtrar_contatos())

        # Lista de Conversas
        self.scroll_contacts = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", corner_radius=0)
        self.scroll_contacts.pack(fill="both", expand=True)

    def filtrar_contatos(self):
        """Filtra contatos com base no texto de busca"""
        termo = self.search_entry.get().lower()
        contatos_filtrados = [c for c in self.contatos if termo in c.get("name", "").lower() or termo in c.get("msg", "").lower()]
        # Limpar e atualizar lista
        for widget in self.scroll_contacts.winfo_children():
            widget.destroy()
        for i, contato in enumerate(contatos_filtrados):
            is_selected = self.conversa_atual and contato.get("id") == self.conversa_atual.get("id")
            self.criar_contato_item(contato, is_first=is_selected)

    def selecionar_conversa(self, contato):
        """Seleciona uma conversa e carrega suas mensagens"""
        self.conversa_atual = contato
        # Atualizar visualização da lista de contatos
        self.atualizar_lista_contatos()
        # Carregar mensagens da conversa
        self.carregar_mensagens(contato.get("id"))
        # Atualizar header da conversa
        self.atualizar_header_chat(contato)

    def atualizar_header_chat(self, contato):
        """Atualiza o header da chat area com os dados do contato"""
        # Atualizar nome
        self.label_nome.configure(text=contato.get("name", "Contato"))
        # Atualizar status
        status = "Online" if contato.get("active") else "Offline"
        self.label_status.configure(text=status)
        self.label_status.configure(text_color=self.colors["success"] if contato.get("active") else self.colors["text_muted"])
        # Atualizar avatar
        img = self.load_image(contato.get("img", "avatar-1.jpg"), (42, 42))
        self.label_avatar.configure(image=img)

    def criar_contato_item(self, data, is_first=False):
        bg_color = self.colors["primary_light"] if is_first else "transparent"
        item = ctk.CTkFrame(self.scroll_contacts, fg_color=bg_color, height=80, corner_radius=RADIUS["input"] if is_first else 0)
        item.pack(fill="x", padx=10, pady=2)
        item.bind("<Button-1>", lambda e: self.selecionar_conversa(data))
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=10)

        # Avatar com Indicador Online
        avatar_box = ctk.CTkFrame(inner, width=48, height=48, fg_color="transparent")
        avatar_box.pack(side="left", padx=(0, 12))
        avatar_box.pack_propagate(False)
        
        img = self.load_image(data.get("img", "avatar-1.jpg"), (48, 48))
        lbl_img = ctk.CTkLabel(avatar_box, text="" if img else "👤", image=img, width=48, height=48, corner_radius=24, fg_color=self.colors["border"])
        lbl_img.place(relx=0.5, rely=0.5, anchor="center")
        
        if data.get("active"):
            ctk.CTkFrame(avatar_box, width=12, height=12, fg_color=self.colors["success"], corner_radius=6, border_width=2, border_color="white").place(relx=0.85, rely=0.85, anchor="center")

        # Textos
        txt_frame = ctk.CTkFrame(inner, fg_color="transparent")
        txt_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(txt_frame, text=data.get("name", "Unknown"), font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        # Corrigindo o erro de cor condicional
        color_msg = self.colors["text_muted"] if not is_first else self.colors["primary"]
        ctk.CTkLabel(txt_frame, text=data.get("msg", "Sem mensagens"), font=font(12), text_color=color_msg).pack(anchor="w")

        # Unread / Time
        if data.get("unread", 0) > 0:
            badge = ctk.CTkLabel(inner, text=str(data["unread"]), width=20, height=20, corner_radius=10, fg_color=self.colors["danger"], text_color="white", font=font(10, "bold"))
            badge.pack(side="right")
        elif is_first and data.get("time"):
            ctk.CTkLabel(inner, text=data["time"], font=font(11), text_color=self.colors["primary"]).pack(side="right", anchor="n")

    def carregar_mensagens(self, id_usuario):
        """Carrega mensagens da conversa com um usuário"""
        def task():
            try:
                data = self.servico.obter_mensagens(id_usuario)
                if data and 'results' in data:
                    self.mensagens = data['results']
                    self.atualizar_area_mensagens()
                    # Marcar mensagens como lidas
                    self.marcar_mensagens_lidas()
            except Exception as e:
                print(f"Erro ao carregar mensagens: {e}")
        
        threading.Thread(target=task, daemon=True).start()

    def marcar_mensagens_lidas(self):
        """Marca mensagens não lidas como lidas"""
        for msg in self.mensagens:
            if not msg.get('read'):
                try:
                    self.servico.marcar_mensagem_lida(msg.get('id'))
                except Exception as e:
                    print(f"Erro ao marcar mensagem como lida: {e}")

    def atualizar_area_mensagens(self):
        """Atualiza a area de mensagens com as mensagens carregadas usando container approach"""
        try:
            # Verificar se o widget ainda existe
            if not hasattr(self, 'msg_area') or not self.msg_area.winfo_exists():
                return
                
            # Limpar todos os widgets existentes na área de mensagens
            for widget in self.msg_area.winfo_children():
                widget.destroy()
                
            # Crie um container para todas as mensagens
            container = ctk.CTkFrame(self.msg_area, fg_color="transparent")
            container.pack(fill="both", expand=True)

            if not self.mensagens:
                # Mensagem de conversa vazia
                frame_vazio = ctk.CTkFrame(container, fg_color="transparent")
                frame_vazio.pack(expand=True, fill="both", padx=20, pady=40)
                ctk.CTkLabel(frame_vazio, text="Sem mensagens", font=font(14), text_color=self.colors["text_muted"]).pack()
                return

            # Agrupar mensagens por data
            mensagens_por_data = {}
            for msg in self.mensagens:
                timestamp = msg.get('timestamp')
                if timestamp:
                    # Converter para data
                    try:
                        dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        data_str = dt.strftime('%d/%m/%Y')
                        if data_str not in mensagens_por_data:
                            mensagens_por_data[data_str] = []
                        mensagens_por_data[data_str].append(msg)
                    except:
                        continue

            # Adicionar mensagens agrupadas
            for data_str, msgs in mensagens_por_data.items():
                # Timeline (ex: HOJE, ontem, etc.)
                if data_str == datetime.datetime.now().strftime('%d/%m/%Y'):
                    timeline_text = "HOJE"
                elif data_str == (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%d/%m/%Y'):
                    timeline_text = "ONTEM"
                else:
                    timeline_text = data_str
                
                try:
                    label = ctk.CTkLabel(
                        container, 
                        text=timeline_text, 
                        font=font(11, "bold"), 
                        text_color=self.colors["text_highlight"], 
                        fg_color=self.colors["bg_alt"], 
                        corner_radius=RADIUS["pill"], 
                        width=80
                    )
                    label.pack(pady=20)
                except Exception as e:
                    print(f"Erro ao criar label de timeline: {e}")
                    continue

                for msg in msgs:
                    # Verificar se é mensagem do usuário atual
                    is_mine = msg.get('self', False)
                    # Formatar hora
                    hora = ""
                    try:
                        dt = datetime.datetime.fromisoformat(msg.get('timestamp', '').replace('Z', '+00:00'))
                        hora = dt.strftime('%H:%M')
                    except:
                        pass
                    
                    try:
                        self.criar_mensagem_container(container, msg.get('text', ''), is_mine, hora)
                    except Exception as e:
                        print(f"Erro ao criar mensagem: {e}")
                        continue

            # Scroll to bottom
            self.msg_area._parent_canvas.yview_moveto(1.0)
        except Exception as e:
            print(f"Erro ao atualizar area de mensagens: {e}")

    def criar_mensagem_container(self, container, text, is_mine, time):
        """Cria um widget de mensagem dentro de um container específico"""
        frame = ctk.CTkFrame(container, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        # Alinhamento
        align = "right" if is_mine else "left"
        bubble_color = self.colors["bubble_sent"] if is_mine else self.colors["bubble_recv"]
        text_color = "white" if is_mine else self.colors["text"]
        
        # Outer wrapper for alignment
        wrapper = ctk.CTkFrame(frame, fg_color="transparent")
        wrapper.pack(side=align, padx=10)

        # Bubble
        bubble = ctk.CTkFrame(
            wrapper,
            fg_color=bubble_color,
            corner_radius=18,
            border_width=1 if not is_mine else 0,
            border_color=self.colors["border"] if not is_mine else None
        )
        bubble.pack(side="top")
        
        lbl = ctk.CTkLabel(bubble, text=text, font=font(13), text_color=text_color, wraplength=400, justify="left")
        lbl.pack(padx=15, pady=10)
        
        # Time and Status
        info = ctk.CTkFrame(wrapper, fg_color="transparent")
        info.pack(side="top", fill="x", pady=2)
        
        ctk.CTkLabel(info, text=time, font=font(10), text_color=self.colors["text_highlight"]).pack(side=align)
        if is_mine:
            ctk.CTkLabel(info, text="✓✓", font=font(10), text_color=self.colors["primary"]).pack(side=align, padx=5)

    def criar_chat_area(self):
        container = ctk.CTkFrame(self, fg_color=self.colors["bg_chat"], corner_radius=0)
        container.grid(row=0, column=1, sticky="nsew")
        
        # Grid Interno Chat
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # --- 1. Header Chat ---
        header = ctk.CTkFrame(container, fg_color=self.colors["card"], height=80, corner_radius=0, border_width=1, border_color=self.colors["border"])
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        
        inner_h = ctk.CTkFrame(header, fg_color="transparent")
        inner_h.pack(fill="both", expand=True, padx=25)

        # Info User
        user_info = ctk.CTkFrame(inner_h, fg_color="transparent")
        user_info.pack(side="left")
        
        img_h = self.load_image("avatar-2.jpg", (42, 42))
        self.label_avatar = ctk.CTkLabel(user_info, text="", image=img_h, width=42, height=42, corner_radius=21, fg_color=self.colors["border"])
        self.label_avatar.pack(side="left", padx=(0, 15))
        
        title_v = ctk.CTkFrame(user_info, fg_color="transparent")
        title_v.pack(side="left")
        self.label_nome = ctk.CTkLabel(title_v, text="Dra. Beatriz Clara", font=font(16, "bold"), text_color=self.colors["text"])
        self.label_nome.pack(anchor="w")
        self.label_status = ctk.CTkLabel(title_v, text="Online agora", font=font(12), text_color=self.colors["success"])
        self.label_status.pack(anchor="w")

        # Actions
        actions = ctk.CTkFrame(inner_h, fg_color="transparent")
        actions.pack(side="right")
        
        btn_style = {"width": 40, "height": 40, "corner_radius": 20, "fg_color": "transparent", "hover_color": self.colors["bg_alt"], "text_color": self.colors["text_muted"]}
        ctk.CTkButton(actions, text="📷", **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="📞", **btn_style).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="⋮", **btn_style).pack(side="left", padx=2)

        # --- 2. Mensagens ---
        self.msg_area = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.msg_area.grid(row=1, column=0, sticky="nsew", padx=24, pady=12)

        # --- 3. Input Area ---
        input_container = ctk.CTkFrame(container, fg_color=self.colors["card"], height=100, corner_radius=0, border_width=1, border_color=self.colors["border"])
        input_container.grid(row=2, column=0, sticky="ew")
        input_container.grid_propagate(False)
        
        box = ctk.CTkFrame(input_container, fg_color=self.colors["bg_alt"], height=55, corner_radius=28, border_width=1, border_color=self.colors["border"])
        box.pack(fill="x", padx=25, pady=22)
        box.pack_propagate(False)
        
        ctk.CTkButton(box, text="📎", width=40, height=40, corner_radius=20, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["border"]).pack(side="left", padx=10)
        
        self.entry_msg = ctk.CTkEntry(box, placeholder_text="Digite sua mensagem...", fg_color="transparent", border_width=0, font=font(14))
        self.entry_msg.pack(side="left", fill="both", expand=True)
        
        actions_in = ctk.CTkFrame(box, fg_color="transparent")
        actions_in.pack(side="right", padx=10)
        
        ctk.CTkButton(actions_in, text="😊", width=40, height=40, corner_radius=20, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["border"]).pack(side="left")
        
        btn_send = ctk.CTkButton(
            actions_in, text="➤", width=42, height=42, corner_radius=21, 
            fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"], 
            text_color="white", font=font(16, "bold"),
            command=self.enviar_msg
        )
        btn_send.pack(side="left", padx=(5, 0))

    def criar_mensagem(self, text, is_mine, time):
        frame = ctk.CTkFrame(self.msg_area, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        
        # Alinhamento
        align = "right" if is_mine else "left"
        bubble_color = self.colors["bubble_sent"] if is_mine else self.colors["bubble_recv"]
        text_color = "white" if is_mine else self.colors["text"]
        
        # Outer wrapper for alignment
        wrapper = ctk.CTkFrame(frame, fg_color="transparent")
        wrapper.pack(side=align, padx=10)

        # Bubble
        bubble = ctk.CTkFrame(
            wrapper,
            fg_color=bubble_color,
            corner_radius=18,
            border_width=1 if not is_mine else 0,
            border_color=self.colors["border"] if not is_mine else None
        )
        bubble.pack(side="top")
        
        lbl = ctk.CTkLabel(bubble, text=text, font=font(13), text_color=text_color, wraplength=400, justify="left")
        lbl.pack(padx=15, pady=10)
        
        # Time and Status
        info = ctk.CTkFrame(wrapper, fg_color="transparent")
        info.pack(side="top", fill="x", pady=2)
        
        ctk.CTkLabel(info, text=time, font=font(10), text_color=self.colors["text_highlight"]).pack(side=align)
        if is_mine:
            ctk.CTkLabel(info, text="✓✓", font=font(10), text_color=self.colors["primary"]).pack(side=align, padx=5)

    def enviar_msg(self):
        """Envia mensagem para o servidor"""
        txt = self.entry_msg.get().strip()
        if txt and self.conversa_atual:
            # Limpar campo de entrada
            self.entry_msg.delete(0, 'end')
            
            # Adicionar mensagem temporária (pending)
            tempo_atual = datetime.datetime.now().strftime('%H:%M')
            msg_temp = self.criar_mensagem(txt, True, tempo_atual)
            
            # Enviar para servidor em thread separada
            def task():
                try:
                    # Chamar API para enviar mensagem
                    response = self.servico.enviar_mensagem(self.conversa_atual.get("id"), txt)
                    if response:
                        # Atualizar lista de mensagens
                        self.carregar_mensagens(self.conversa_atual.get("id"))
                except Exception as e:
                    print(f"Erro ao enviar mensagem: {e}")
                    # Marcar mensagem como falha
                    self.mostrar_erro_envio(msg_temp)
            
            threading.Thread(target=task, daemon=True).start()

            # Scroll to bottom
            self.msg_area._parent_canvas.yview_moveto(1.0)

    def mostrar_erro_envio(self, msg_widget):
        """Mostra indicação de erro no envio de mensagem"""
        # Criar ícone de erro
        erro_label = ctk.CTkLabel(msg_widget, text="!", width=16, height=16, corner_radius=8, fg_color=self.colors["danger"], text_color="white", font=font(10, "bold"))
        erro_label.pack(side="right", padx=5)

    def iniciar_atualizacao_realtime(self):
        """Inicia thread para atualizar mensagens em tempo real"""
        def task():
            while True:
                if self.conversa_atual and not self.atualizando:
                    self.atualizando = True
                    try:
                        self.carregar_mensagens(self.conversa_atual.get("id"))
                    except Exception as e:
                        print(f"Erro na atualização realtime: {e}")
                    finally:
                        self.atualizando = False
                # Esperar 5 segundos antes da próxima atualização
                time.sleep(5)
        
        threading.Thread(target=task, daemon=True).start()

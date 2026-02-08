import customtkinter as ctk
from PIL import Image
import os

from ui_theme import THEME, SPACING, RADIUS, font

class ComunicacaoInternaFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller

        # Inicializa o serviço de comunicação
        from services.comunicacao import ServicoComunicacao
        self.servico_comunicacao = ServicoComunicacao()

        self.colors = THEME

        # Dados da conversa
        self.contatos = []
        self.conversa_ativa = None
        self.mensagens = []
        # Obtém o ID do usuário logado do controller (não mais hardcoded)
        self.usuario_logado_id = controller.usuario_logado_id

        # Caminhos de imagens
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.img_path = os.path.join(self.base_path, "..", "imagens")

        # Grid layout principal (Sidebar + Chat Area)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============= 1. Sidebar (Lista de Contatos) =============
        self.criar_sidebar()

        # ============= 2. Chat Area (Conversa Ativa) =============
        self.criar_chat_area()

        # Carrega contatos do banco de dados
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
        self.entry_busca = ctk.CTkEntry(search_frame, placeholder_text="Buscar conversas...", fg_color="transparent", border_width=0, font=font(13))
        self.entry_busca.pack(side="left", fill="both", expand=True)
        self.entry_busca.bind("<KeyRelease>", self.filtrar_contatos)

        # Lista de Conversas
        self.scroll_contacts = ctk.CTkScrollableFrame(sidebar, fg_color="transparent", corner_radius=0)
        self.scroll_contacts.pack(fill="both", expand=True)

        # Mock Contacts
        contacts = [
            {"name": "Dra. Beatriz Clara", "msg": "Online agora", "active": True, "unread": 2, "img": "avatar-2.jpg"},
            {"name": "Coordenação", "msg": "Reunião Pedagógica", "active": False, "unread": 0, "img": "avatar-3.jpg"},
            {"name": "Suporte Técnico", "msg": "Chamado #442 aberto", "active": True, "unread": 0, "img": "avatar-4.jpg"},
            {"name": "Carlos Eduardo", "msg": "Vi seu relatório ontem", "active": False, "unread": 0, "img": "avatar-5.jpg"},
            {"name": "Ana Luiza", "msg": "Pode revisar a triagem?", "active": True, "unread": 1, "img": "avatar-6.jpg"}
        ]

        for i, c in enumerate(contacts):
            self.criar_contato_item(c, is_first=(i==0))

    def criar_contato_item(self, data, is_first=False):
        bg_color = self.colors["primary_light"] if is_first else "transparent"
        item = ctk.CTkFrame(self.scroll_contacts, fg_color=bg_color, height=80, corner_radius=RADIUS["input"] if is_first else 0)
        item.pack(fill="x", padx=10, pady=2)
        item.bind("<Button-1>", lambda e: self.selecionar_conversa(data, item))
        item.configure(cursor="hand2")
        item.contato_data = data  # Armazena os dados do contato no widget
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=10)
        # Garante que o inner frame também responda ao clique
        inner.bind("<Button-1>", lambda e: self.selecionar_conversa(data, item))
        inner.configure(cursor="hand2")

        # Avatar com Indicador Online
        avatar_box = ctk.CTkFrame(inner, width=48, height=48, fg_color="transparent")
        avatar_box.pack(side="left", padx=(0, 12))
        avatar_box.pack_propagate(False)
        avatar_box.bind("<Button-1>", lambda e: self.selecionar_conversa(data, item))
        avatar_box.configure(cursor="hand2")
        
        img = self.load_image(data["img"], (48, 48))
        lbl_img = ctk.CTkLabel(avatar_box, text="" if img else "👤", image=img, width=48, height=48, corner_radius=24, fg_color=self.colors["border"])
        lbl_img.place(relx=0.5, rely=0.5, anchor="center")
        
        if data["active"]:
            ctk.CTkFrame(avatar_box, width=12, height=12, fg_color=self.colors["success"], corner_radius=6, border_width=2, border_color="white").place(relx=0.85, rely=0.85, anchor="center")

        # Textos
        txt_frame = ctk.CTkFrame(inner, fg_color="transparent")
        txt_frame.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(txt_frame, text=data["name"], font=font(14, "bold"), text_color=self.colors["text"]).pack(anchor="w")
        
        # Corrigindo o erro de cor condicional
        color_msg = self.colors["text_muted"] if not is_first else self.colors["primary"]
        ctk.CTkLabel(txt_frame, text=data["msg"], font=font(12), text_color=color_msg).pack(anchor="w")

        # Unread / Time
        if data["unread"] > 0:
            badge = ctk.CTkLabel(inner, text=str(data["unread"]), width=20, height=20, corner_radius=10, fg_color=self.colors["danger"], text_color="white", font=font(10, "bold"))
            badge.pack(side="right")
        elif is_first:
            ctk.CTkLabel(inner, text="2 min", font=font(11), text_color=self.colors["primary"]).pack(side="right", anchor="n")

    def get_avatar_por_papel(self, papel):
        avatares = {
            "admin": "avatar-1.jpg",
            "analista": "avatar-2.jpg",
            "coordenador": "avatar-3.jpg",
            "suporte": "avatar-4.jpg",
            "group": "avatar-6.jpg"
        }
        return avatares.get(papel, "avatar-6.jpg")

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
        ctk.CTkLabel(user_info, text="", image=img_h, width=42, height=42, corner_radius=21, fg_color=self.colors["border"]).pack(side="left", padx=(0, 15))
        
        title_v = ctk.CTkFrame(user_info, fg_color="transparent")
        title_v.pack(side="left")
        self.lbl_chat_nome = ctk.CTkLabel(title_v, text="Dra. Beatriz Clara", font=font(16, "bold"), text_color=self.colors["text"])
        self.lbl_chat_nome.pack(anchor="w")
        self.lbl_chat_status = ctk.CTkLabel(title_v, text="Online agora", font=font(12), text_color=self.colors["success"])
        self.lbl_chat_status.pack(anchor="w")

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
        
        self.btn_clip = ctk.CTkButton(box, text="📎", width=40, height=40, corner_radius=20, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["border"], command=self.toggle_modal_arquivos)
        self.btn_clip.pack(side="left", padx=10)
        
        self.entry_mensagem = ctk.CTkEntry(box, placeholder_text="Digite sua mensagem...", fg_color="transparent", border_width=0, font=font(14))
        self.entry_mensagem.pack(side="left", fill="both", expand=True)
        
        actions_in = ctk.CTkFrame(box, fg_color="transparent")
        actions_in.pack(side="right", padx=10)
        
        ctk.CTkButton(actions_in, text="😊", width=40, height=40, corner_radius=20, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["border"]).pack(side="left")
        
        self.btn_enviar = ctk.CTkButton(
            actions_in, text="➤", width=42, height=42, corner_radius=21, 
            fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"], 
            text_color="white", font=font(16, "bold"),
            command=self.enviar_mensagem
        )
        self.btn_enviar.pack(side="left", padx=(5, 0))
        
        # --- 4. Modal de Arquivos ---
        self.criar_modal_arquivos(container)
    
    def toggle_modal_arquivos(self):
        """Alterna a exibição do modal de arquivos"""
        if self.modal_arquivos.winfo_manager():
            self.modal_arquivos.grid_remove()
        else:
            # Posiciona o modal sobre o ícone de clip (garantindo padding positivo)
            btn_x = self.btn_clip.winfo_x()
            btn_y = max(10, self.btn_clip.winfo_y() - 200)  # Garante que não fique negativo
            self.modal_arquivos.grid(row=2, column=0, sticky="w", padx=(btn_x + 25, 0), pady=(btn_y, 0))
    
    def criar_modal_arquivos(self, parent):
        """Cria o modal de seleção de arquivos por categoria"""
        self.modal_arquivos = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        self.modal_arquivos.grid(row=2, column=0, sticky="w", padx=25, pady=0)
        self.modal_arquivos.grid_remove()  # Inicialmente oculta
        
        # Categorias de arquivos
        categorias = [
            {"nome": "Documentos", "icone": "📄", "extensao": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx"]},
            {"nome": "Imagens", "icone": "🖼️", "extensao": [".jpg", ".jpeg", ".png", ".gif", ".bmp"]},
            {"nome": "Videos", "icone": "🎥", "extensao": [".mp4", ".avi", ".mov", ".wmv"]},
            {"nome": "Audio", "icone": "🎵", "extensao": [".mp3", ".wav", ".ogg"]},
            {"nome": "Todos", "icone": "📁", "extensao": []}
        ]
        
        for i, cat in enumerate(categorias):
            card = ctk.CTkFrame(self.modal_arquivos, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
            card.grid(row=0, column=i, sticky="nsew", padx=10, pady=10)
            card.pack_propagate(False)
            card.configure(cursor="hand2")
            card.bind("<Button-1>", lambda e, c=cat: self.selecionar_categoria(c))
            
            # Icone da categoria
            ctk.CTkLabel(card, text=cat["icone"], font=font(24)).pack(pady=(15, 5))
            # Nome da categoria
            ctk.CTkLabel(card, text=cat["nome"], font=font(12, "bold"), text_color=self.colors["text"]).pack(pady=(0, 15))
            
            self.modal_arquivos.grid_columnconfigure(i, weight=1)

    def atualizar_area_mensagens(self):
        """Atualiza a área de mensagens com as mensagens carregadas"""
        # Limpa todas as mensagens existentes
        for widget in self.msg_area.winfo_children():
            widget.destroy()
        
        # Adiciona a linha "HOJE"
        ctk.CTkLabel(self.msg_area, text="HOJE", font=font(11, "bold"), text_color=self.colors["text_highlight"], fg_color=self.colors["bg_alt"], corner_radius=RADIUS["pill"], width=80).pack(pady=20)
        
        # Cria cada mensagem
        for msg in self.mensagens:
            self.criar_mensagem(msg)

    def criar_mensagem(self, msg):
        """Cria uma mensagem na interface"""
        is_mine = msg["sender_id"] == self.usuario_logado_id
        
        # Obter nome do remetente
        remetente_nome = "Eu" if is_mine else self.obter_nome_remetente(msg["sender_id"])
        
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
            border_color=self.colors["border"]
        )
        bubble.pack(side="top")
        
        # Nome do remetente (apenas para mensagens de grupo)
        if self.conversa_ativa and self.conversa_ativa["role"] == "group" and not is_mine:
            ctk.CTkLabel(bubble, text=remetente_nome, font=font(11, "bold"), text_color=text_color, wraplength=400, justify="left").pack(padx=15, pady=(10, 0))
        
        # Verifica se é uma mensagem de arquivo
        if "caminho_arquivo" in msg:
            self.criar_mensagem_arquivo(bubble, msg, text_color)
        else:
            lbl = ctk.CTkLabel(bubble, text=msg["text"], font=font(13), text_color=text_color, wraplength=400, justify="left")
            lbl.pack(padx=15, pady=(0 if (self.conversa_ativa and self.conversa_ativa["role"] == "group" and not is_mine) else 10, 10))
        
        # Time and Status
        info = ctk.CTkFrame(wrapper, fg_color="transparent")
        info.pack(side="top", fill="x", pady=2)
        
        # Formata o timestamp
        from datetime import datetime
        timestamp = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M")
        
        ctk.CTkLabel(info, text=time_str, font=font(10), text_color=self.colors["text_highlight"]).pack(side=align)
        if is_mine:
            ctk.CTkLabel(info, text="✓✓", font=font(10), text_color=self.colors["primary"]).pack(side=align, padx=5)
    
    def criar_mensagem_arquivo(self, bubble, msg, text_color):
        """Cria uma mensagem de arquivo com visualização e download"""
        nome_arquivo = os.path.basename(msg["caminho_arquivo"])
        tamanho_arquivo = os.path.getsize(msg["caminho_arquivo"])
        tamanho_str = self.formatar_tamanho_arquivo(tamanho_arquivo)
        
        # Card do arquivo
        card_arquivo = ctk.CTkFrame(bubble, fg_color=self.colors["bg_alt"], corner_radius=RADIUS["input"], border_width=1, border_color=self.colors["border"])
        card_arquivo.pack(padx=15, pady=10, fill="x")
        
        # Icone do arquivo
        icone_arquivo = "📄"
        if msg["tipo_arquivo"] == "Imagens":
            icone_arquivo = "🖼️"
        elif msg["tipo_arquivo"] == "Videos":
            icone_arquivo = "🎥"
        elif msg["tipo_arquivo"] == "Audio":
            icone_arquivo = "🎵"
        
        ctk.CTkLabel(card_arquivo, text=icone_arquivo, font=font(20)).pack(side="left", padx=10, pady=10)
        
        # Info do arquivo
        info_arquivo = ctk.CTkFrame(card_arquivo, fg_color="transparent")
        info_arquivo.pack(side="left", fill="both", expand=True, padx=5, pady=10)
        
        ctk.CTkLabel(info_arquivo, text=nome_arquivo, font=font(12, "bold"), text_color=text_color, wraplength=250, justify="left").pack(anchor="w")
        ctk.CTkLabel(info_arquivo, text=tamanho_str, font=font(10), text_color=self.colors["text_muted"]).pack(anchor="w")
        
        # Botões de visualização e download
        botoes = ctk.CTkFrame(card_arquivo, fg_color="transparent")
        botoes.pack(side="right", padx=10, pady=10)
        
        ctk.CTkButton(botoes, text="👁️", width=30, height=30, corner_radius=15, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["border"], command=lambda: self.visualizar_arquivo(msg["caminho_arquivo"])).pack(side="top", pady=2)
        ctk.CTkButton(botoes, text="📥", width=30, height=30, corner_radius=15, fg_color="transparent", text_color=self.colors["text_muted"], hover_color=self.colors["border"], command=lambda: self.download_arquivo(msg["caminho_arquivo"], nome_arquivo)).pack(side="top", pady=2)
    
    def visualizar_arquivo(self, caminho_arquivo):
        """Visualiza o arquivo dependendo do tipo"""
        import webbrowser
        try:
            webbrowser.open(caminho_arquivo)
        except Exception as e:
            print(f"Erro ao visualizar arquivo: {e}")
    
    def download_arquivo(self, caminho_arquivo, nome_arquivo):
        """Faz o download do arquivo (salva em local escolhido pelo usuário)"""
        import tkinter.filedialog as fd
        try:
            destino = fd.asksaveasfilename(title="Salvar arquivo", initialfile=nome_arquivo, filetypes=[("Todos os arquivos", "*.*")])
            if destino:
                import shutil
                shutil.copy2(caminho_arquivo, destino)
        except Exception as e:
            print(f"Erro ao download arquivo: {e}")

    def obter_nome_remetente(self, id_remetente):
        for contato in self.contatos:
            if contato["id"] == id_remetente:
                return contato["name"]

        return f"Usuário {id_remetente}"

    def enviar_msg(self):
        """Método de fallback para a função mock"""
        txt = self.entry_mensagem.get()
        if txt:
            self.criar_mensagem({
                "sender_id": self.usuario_logado_id,
                "text": txt,
                "timestamp": "2024-05-20T10:45:00Z",
                "read": False,
                "recipient_id": None
            })
            self.entry_mensagem.delete(0, 'end')
            # Scroll to bottom
            self.msg_area._parent_canvas.yview_moveto(1.0)

    def enviar_mensagem(self):
        """Envia uma mensagem para a conversa ativa"""
        txt = self.entry_mensagem.get()
        if txt:
            self.criar_mensagem({
                "sender_id": self.usuario_logado_id,
                "text": txt,
                "timestamp": "2024-05-20T10:45:00Z",
                "read": False,
                "recipient_id": None
            })
            self.entry_mensagem.delete(0, 'end')
            # Scroll to bottom
            self.msg_area._parent_canvas.yview_moveto(1.0)

    def carregar_contatos(self):
        """Carrega contatos do serviço de comunicação (apenas admin, analista, coordenador, suporte) + chat em grupo"""
        try:
            resultado = self.servico_comunicacao.listar_contatos(self.usuario_logado_id)
            if resultado["success"]:
                self.contatos = [c for c in resultado["data"] if c["role"] in ["admin", "analista", "coordenador", "suporte"]]
                self.contatos.insert(0, {
                    "id": None,
                    "name": "Todos",
                    "email": "",
                    "student_name": "",
                    "role": "group",
                    "is_staff": True
                })
                
                for widget in self.scroll_contacts.winfo_children():
                    widget.destroy()
                
                for i, c in enumerate(self.contatos):
                    avatar = self.get_avatar_por_papel(c["role"])
                    self.criar_contato_item({
                        "id": c["id"],
                        "name": c["name"],
                        "msg": "Grupo de todos" if c["role"] == "group" else f"Online ({c['role']})",
                        "active": c["is_staff"],
                        "unread": 0,
                        "img": avatar,
                        "role": c["role"]
                    }, is_first=(i==0))
        except Exception as e:
            print(f"Erro ao carregar contatos: {e}")

    def selecionar_categoria(self, categoria):
        """Abre o diálogo de seleção de arquivo com a categoria especificada"""
        import tkinter.filedialog as fd
        
        # Filtro de arquivos baseado na categoria
        if categoria["extensao"]:
            tipos_arquivo = []
            for ext in categoria["extensao"]:
                tipos_arquivo.append((f"{categoria['nome']} (*{ext})", f"*{ext}"))
            # Adiciona opção de todos os tipos da categoria
            tipos_arquivo.append((f"Todos {categoria['nome']}", f"{' '.join([f'*{ext}' for ext in categoria['extensao']])}"))
        else:
            tipos_arquivo = [("Todos os arquivos", "*.*")]
        
        arquivo = fd.askopenfilename(title=f"Selecione um arquivo {categoria['nome'].lower()}", filetypes=tipos_arquivo)
        
        if arquivo:
            self.enviar_arquivo(arquivo, categoria["nome"])
    
    def enviar_arquivo(self, caminho_arquivo, categoria):
        """Envia um arquivo para a conversa ativa"""
        if not self.conversa_ativa:
            return
            
        try:
            # Aqui você pode implementar a lógica para enviar o arquivo
            # Por enquanto, vamos exibir um mock da mensagem de arquivo
            nome_arquivo = os.path.basename(caminho_arquivo)
            tamanho_arquivo = os.path.getsize(caminho_arquivo)
            tamanho_str = self.formatar_tamanho_arquivo(tamanho_arquivo)
            
            # Cria mensagem de arquivo
            mensagem_arquivo = {
                "sender_id": self.usuario_logado_id,
                "text": "",
                "timestamp": "2024-05-20T10:45:00Z",
                "read": False,
                "recipient_id": None,
                "tipo_arquivo": categoria,
                "caminho_arquivo": caminho_arquivo
            }
            
            self.criar_mensagem(mensagem_arquivo)
            self.modal_arquivos.grid_remove()  # Oculta o modal após seleção
        except Exception as e:
            print(f"Erro ao enviar arquivo: {e}")
    
    def formatar_tamanho_arquivo(self, bytes):
        """Formata o tamanho do arquivo em KB, MB ou GB"""
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024 * 1024:
            return f"{round(bytes / 1024, 1)} KB"
        elif bytes < 1024 * 1024 * 1024:
            return f"{round(bytes / (1024 * 1024), 1)} MB"
        else:
            return f"{round(bytes / (1024 * 1024 * 1024), 1)} GB"

    def filtrar_contatos(self, event):
        termo_busca = self.entry_busca.get().lower()
        for widget in self.scroll_contacts.winfo_children():
            widget.destroy()
            
        for i, c in enumerate(self.contatos):
            if termo_busca in c["name"].lower() or termo_busca in c["role"].lower():
                avatar = self.get_avatar_por_papel(c["role"])
                self.criar_contato_item({
                    "id": c["id"],
                    "name": c["name"],
                    "msg": "Grupo de todos" if c["role"] == "group" else f"Online ({c['role']})",
                    "active": c["is_staff"],
                    "unread": 0,
                    "img": avatar,
                    "role": c["role"]
                }, is_first=(i==0))

    def selecionar_conversa(self, contato, item_widget=None):
        # Atualiza a cor de todos os contatos para transparente
        for widget in self.scroll_contacts.winfo_children():
            if hasattr(widget, "contato_data"):
                widget.configure(fg_color="transparent")
        
        # Atualiza a cor do contato selecionado
        if item_widget:
            item_widget.configure(fg_color=self.colors["primary_light"])
        
        self.conversa_ativa = contato
        self.lbl_chat_nome.configure(text=contato["name"])
        self.lbl_chat_status.configure(text="Grupo de comunicação" if contato["role"] == "group" else contato["role"].capitalize())
        
        # Atualiza o avatar do chat header
        avatar = self.get_avatar_por_papel(contato["role"])
        img_h = self.load_image(avatar, (42, 42))
        # Encontra o label do avatar no header
        for widget in self.lbl_chat_nome.master.master.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget.cget("image"):
                widget.configure(image=img_h)
                break
        
        self.carregar_mensagens()

    def carregar_mensagens(self):
        """Carrega mensagens da conversa ativa"""
        if not self.conversa_ativa:
            return
        
        try:
            if self.conversa_ativa["role"] == "group":
                resultado = self.servico_comunicacao.obter_mensagens_grupo()
            else:
                resultado = self.servico_comunicacao.obter_mensagens(self.usuario_logado_id, self.conversa_ativa["id"])
                
            if resultado["success"]:
                self.mensagens = resultado["data"]
                self.atualizar_area_mensagens()
        except Exception as e:
            print(f"Erro ao carregar mensagens: {e}")

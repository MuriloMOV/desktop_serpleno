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
        # Inicializa o serviço de comunicação
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

        # Dados da conversa
        self.contatos = []
        self.conversa_atual = None
        self.mensagens = []
        self.atualizando = False
        self.contador_nao_lidas = {}
        self.atualizacao_periodica = True

        # Grid layout principal (Sidebar + Chat Area)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============= 1. Sidebar (Lista de Contatos) =============
        self.criar_sidebar()

        # ============= 2. Chat Area (Conversa Ativa) =============
        self.criar_chat_area()

        # Carrega contatos do banco de dados
        self.carregar_contatos()
        # Inicia loop de atualização periódica
        self.iniciar_atualizacao_periodica()
        
        # Vincula o evento de destruição do frame para parar a thread
        self.bind("<Destroy>", self.on_destroy)
    
    def on_destroy(self, event):
        """Parar a thread de atualização quando o frame é destruído"""
        self.atualizacao_periodica = False

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
                
                if hasattr(self, "scroll_contacts") and self.scroll_contacts.winfo_exists():
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
    
    def carregar_contador_nao_lidas(self):
        """Carrega o contador de mensagens não lidas por contato"""
        try:
            data = self.servico_comunicacao.contar_mensagens_nao_lidas(self.usuario_logado_id)
            if data and 'success' in data and data['success']:
                self.contador_nao_lidas = data['data']
        except Exception as e:
            print(f"Erro ao carregar contador de não lidas: {e}")
    
    def iniciar_atualizacao_periodica(self):
        """Inicia o loop de atualização periódica das mensagens"""
        def task():
            while self.atualizacao_periodica:
                time.sleep(5)  # Atualiza a cada 5 segundos
                if not self.atualizando:
                    self.atualizar_dados_conversa()
        
        threading.Thread(target=task, daemon=True).start()
    
    def atualizar_dados_conversa(self):
        """Atualiza os dados da conversa atual e o contador de não lidas"""
        # Verifica se o frame ainda existe antes de tentar atualizar
        if not hasattr(self, "winfo_exists") or not self.winfo_exists():
            self.atualizacao_periodica = False
            return
            
        self.atualizando = True
        try:
            # Atualiza contador de mensagens não lidas
            self.carregar_contador_nao_lidas()
            # Atualiza a lista de contatos para exibir o badge
            self.atualizar_lista_contatos()
            # Se houver conversa ativa, atualiza as mensagens
            if self.conversa_atual:
                self.carregar_mensagens()
        except Exception as e:
            # Ignora erros de widgets destruídos
            if "invalid command name" not in str(e) and "TCL error" not in str(e):
                print(f"Erro na atualização periódica: {e}")
        finally:
            self.atualizando = False
    
    def atualizar_lista_contatos(self):
        """Atualiza a lista de contatos na sidebar - apenas atualiza contadores de não lidas"""
        # Verificar se o widget scroll_contacts ainda existe antes de acessar seus filhos
        if not hasattr(self, "scroll_contacts") or not self.scroll_contacts.winfo_exists():
            return
            
        # Itera sobre os widgets de contato existentes
        for widget in self.scroll_contacts.winfo_children():
            if hasattr(widget, "contato_data") and widget.winfo_exists():
                contato = widget.contato_data
                # Obtém o contador de mensagens não lidas para este contato
                unread = self.contador_nao_lidas.get(contato["id"], 0)
                
                # Verifica se já existe um badge de não lidas
                badge = None
                for child in widget.winfo_children():
                    # O badge é um CTkFrame com fg_color danger
                    if isinstance(child, ctk.CTkFrame) and hasattr(child, "winfo_children") and child.winfo_exists():
                        # Verifica se esse frame contém um label com número
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkLabel) and grandchild.cget("text").isdigit():
                                badge = child
                                break
                        if badge:
                            break
                
                if unread > 0:
                    if not badge:
                        # Cria o badge se não existe
                        info_frame = None
                        for child in widget.winfo_children():
                            # O info_frame é o segundo filho (posição 1) do widget de contato
                            if isinstance(child, ctk.CTkFrame) and child.cget("fg_color") == "transparent":
                                info_frame = child
                                break
                        
                        if info_frame and info_frame.winfo_exists():
                            badge = ctk.CTkFrame(info_frame, fg_color=self.colors["danger"], corner_radius=10)
                            badge.pack(side="right", padx=10)
                            ctk.CTkLabel(badge, text=str(unread), font=font(11, "bold"), text_color="white", width=20, height=20).pack()
                    else:
                        # Atualiza o texto do badge existente
                        for child in badge.winfo_children():
                            if isinstance(child, ctk.CTkLabel) and child.winfo_exists():
                                child.configure(text=str(unread))
                else:
                    # Remove o badge se não houver mensagens não lidas
                    if badge and badge.winfo_exists():
                        badge.destroy()

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
        self.conversa_atual = contato  # Atualiza a segunda variável para manter consistência
        self.lbl_chat_nome.configure(text=contato["name"])
        self.lbl_chat_status.configure(text="Grupo de comunicação" if contato["role"] == "group" else contato["role"].capitalize())
        
        # Atualiza o avatar do chat header
        avatar = self.get_avatar_por_papel(contato["role"])
        img_h = self.load_image(avatar, (42, 42))
        # Encontra o label do avatar no header
        try:
            for widget in self.lbl_chat_nome.master.master.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("image"):
                    widget.configure(image=img_h)
                    break
        except Exception as e:
            print(f"Erro ao atualizar avatar: {e}")
        
        self.carregar_mensagens()

    def carregar_mensagens(self):
        """Carrega mensagens da conversa ativa - otimizado para não recriar toda a área se não houver mudanças"""
        if not self.conversa_ativa or not hasattr(self, "winfo_exists") or not self.winfo_exists():
            return
        
        try:
            if self.conversa_ativa["role"] == "group":
                resultado = self.servico_comunicacao.obter_mensagens_grupo()
            else:
                resultado = self.servico_comunicacao.obter_mensagens(self.usuario_logado_id, self.conversa_ativa["id"])
                
            if resultado["success"]:
                novas_mensagens = resultado["data"]
                
                # Verifica se houve mudanças nas mensagens
                if self.mensagens != novas_mensagens:
                    self.mensagens = novas_mensagens
                    self.atualizar_area_mensagens()
        except Exception as e:
            # Ignora erros de widgets destruídos
            if "invalid command name" not in str(e) and "TCL error" not in str(e):
                print(f"Erro ao carregar mensagens: {e}")

    def marcar_mensagens_lidas(self):
        """Marca mensagens não lidas como lidas"""
        for msg in self.mensagens:
            if not msg.get('read'):

                try:
                    self.servico_comunicacao.marcar_mensagem_lida(msg.get('id'))
                except Exception as e:
                    print(f"Erro ao marcar mensagem como lida: {e}")

    def atualizar_area_mensagens(self):
        """Atualiza a área de mensagens com as mensagens carregadas - limpa todas as mensagens antigas antes de adicionar as novas"""
        # Verifica se a área de mensagens ainda existe
        if not hasattr(self, "msg_area") or not self.msg_area.winfo_exists():
            return
            
        # Limpa todas as mensagens existentes na área de mensagens
        for widget in self.msg_area.winfo_children():
            if widget.winfo_exists():
                widget.destroy()
        
        # Adiciona a linha "HOJE"
        ctk.CTkLabel(self.msg_area, text="HOJE", font=font(11, "bold"), text_color=self.colors["text_highlight"], fg_color=self.colors["bg_alt"], corner_radius=RADIUS["pill"], width=80).pack(pady=20)
        
        # Cria todas as mensagens da conversa ativa
        for msg in self.mensagens:
            self.criar_mensagem(msg)

    def criar_mensagem(self, msg):
        """Cria uma mensagem na interface"""
        is_mine = msg["sender_id"] == self.usuario_logado_id
        
        # Obter nome do remetente
        remetente_nome = "Eu" if is_mine else self.obter_nome_remetente(msg["sender_id"])
        
        frame = ctk.CTkFrame(self.msg_area, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        # Adiciona dados da mensagem ao widget para identificação
        frame.msg_data = msg
        
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
        
        # Nome do remetente (apenas para mensajes de grupo)
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
        timestamp = datetime.datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
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
        elif msg["tipo_arquivo"] == "Planilhas":
            icone_arquivo = "📊"
        elif msg["tipo_arquivo"] == "Presentações":
            icone_arquivo = "📽️"
        elif msg["tipo_arquivo"] == "Arquivos Zip":
            icone_arquivo = "🗜️"
        elif msg["tipo_arquivo"] == "Code":
            icone_arquivo = "💻"
        
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
        if txt and self.conversa_ativa:
            try:
                # Envia a mensagem para o serviço de comunicação
                if self.conversa_ativa["role"] == "group":
                    resultado = self.servico_comunicacao.enviar_mensagem_grupo(
                        self.usuario_logado_id, 
                        txt
                    )
                else:
                    resultado = self.servico_comunicacao.enviar_mensagem(
                        self.usuario_logado_id, 
                        self.conversa_ativa["id"], 
                        txt
                    )
                
                if resultado["success"]:
                    # Recarrega as mensagens para exibir a nova mensagem
                    self.carregar_mensagens()
                    self.entry_mensagem.delete(0, 'end')
                    # Atualiza o contador de mensagens não lidas
                    self.carregar_contador_nao_lidas()
                    self.atualizar_lista_contatos()
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")

    def criar_contato_item(self, contato, is_first=False):
        """Cria um widget de contato na sidebar"""
        # Container principal do item de contato
        item = ctk.CTkFrame(self.scroll_contacts, fg_color="transparent", height=70)
        item.pack(fill="x", padx=15, pady=(0, 10))
        item.pack_propagate(False)
        item.contato_data = contato
        
        # Avatar
        img = self.load_image(contato["img"], (45, 45))
        lbl_avatar = ctk.CTkLabel(item, text="", image=img, width=45, height=45, corner_radius=22, fg_color=self.colors["border"])
        lbl_avatar.pack(side="left", padx=(0, 15))
        
        # Informações do contato
        info = ctk.CTkFrame(item, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        
        lbl_nome = ctk.CTkLabel(info, text=contato["name"], font=font(14, "bold"), text_color=self.colors["text"])
        lbl_nome.pack(anchor="w", pady=(8, 0))
        
        lbl_msg = ctk.CTkLabel(info, text=contato["msg"], font=font(12), text_color=self.colors["text_muted"])
        lbl_msg.pack(anchor="w", pady=(2, 8))
        
        # Contador de mensagens não lidas
        if contato.get("unread", 0) > 0:
            badge = ctk.CTkFrame(info, fg_color=self.colors["danger"], corner_radius=10)
            badge.pack(side="right", padx=10)
            ctk.CTkLabel(badge, text=str(contato["unread"]), font=font(11, "bold"), text_color="white", width=20, height=20).pack()
        
        # Evento de clique
        item.bind("<Button-1>", lambda e: self.selecionar_conversa(contato, item))
        
        # Se for o primeiro item, seleciona automaticamente
        if is_first:
            self.selecionar_conversa(contato, item)

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
        self.label_avatar = ctk.CTkLabel(user_info, text="", image=img_h, width=42, height=42, corner_radius=21, fg_color=self.colors["border"])
        self.label_avatar.pack(side="left", padx=(0, 15))
        
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
            # Posiciona o modal diretamente sobre o ícone de clip, garantindo padding positivo
            btn_x = self.btn_clip.winfo_x()
            btn_y = max(10, self.btn_clip.winfo_y() - 280)  # Garante que não fique negativo
            self.modal_arquivos.grid(row=2, column=0, sticky="w", padx=(btn_x + 25, 0), pady=(btn_y, 0))
    
    def criar_modal_arquivos(self, parent):
        """Cria o modal de seleção de arquivos por categoria em grid 3x3 muito compacto"""
        self.modal_arquivos = ctk.CTkFrame(parent, fg_color=self.colors["card"], corner_radius=RADIUS["card"], border_width=1, border_color=self.colors["border"])
        self.modal_arquivos.grid(row=2, column=0, sticky="w", padx=25, pady=0)
        self.modal_arquivos.grid_remove()  # Inicialmente oculta
        
        # Categorias de arquivos - grid 3x3 (9 categorias)
        categorias = [
            {"nome": "Documentos", "icone": "📄", "extensao": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx"]},
            {"nome": "Imagens", "icone": "🖼️", "extensao": [".jpg", ".jpeg", ".png", ".gif", ".bmp"]},
            {"nome": "Videos", "icone": "🎥", "extensao": [".mp4", ".avi", ".mov", ".wmv"]},
            {"nome": "Audio", "icone": "🎵", "extensao": [".mp3", ".wav", ".ogg"]},
            {"nome": "Planilhas", "icone": "📊", "extensao": [".xls", ".xlsx", ".csv"]},
            {"nome": "Presentações", "icone": "📽️", "extensao": [".ppt", ".pptx"]},
            {"nome": "Arquivos Zip", "icone": "🗜️", "extensao": [".zip", ".rar", ".7z"]},
            {"nome": "Code", "icone": "💻", "extensao": [".py", ".js", ".html", ".css"]},
            {"nome": "Todos", "icone": "📁", "extensao": []}
        ]
        
        # Configura grid 3x3 muito compacto
        for row in range(3):
            self.modal_arquivos.grid_rowconfigure(row, minsize=60)
        for col in range(3):
            self.modal_arquivos.grid_columnconfigure(col, minsize=80)
            
        for i, cat in enumerate(categorias):
            row = i // 3
            col = i % 3
            
            btn = ctk.CTkButton(
                self.modal_arquivos,
                text=f"{cat['icone']}\n{cat['nome']}",
                font=font(10),
                height=60,
                corner_radius=8,
                fg_color=self.colors["bg_alt"],
                hover_color=self.colors["border"],
                text_color=self.colors["text"],
                command=lambda c=cat: self.selecionar_categoria(c)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
    
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
            nome_arquivo = os.path.basename(caminho_arquivo)
            
            # Salva a mensagem de arquivo no banco de dados
            if self.conversa_ativa["role"] == "group":
                resultado = self.servico_comunicacao.enviar_mensagem_grupo(
                    self.usuario_logado_id, 
                    nome_arquivo,  # Usamos o nome do arquivo como texto da mensagem
                    caminho_arquivo, 
                    categoria
                )
            else:
                resultado = self.servico_comunicacao.enviar_mensagem(
                    self.usuario_logado_id, 
                    self.conversa_ativa["id"], 
                    nome_arquivo,  # Usamos o nome do arquivo como texto da mensagem
                    caminho_arquivo, 
                    categoria
                )
                
            if resultado["success"]:
                # Recarrega as mensagens para exibir a nova mensagem de arquivo
                self.carregar_mensagens()
                
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

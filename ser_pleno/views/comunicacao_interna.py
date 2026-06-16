import customtkinter as ctk
from PIL import Image
import os
import datetime
import threading
import time

from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    PrimaryButton,
    GhostButton,
    Badge,
    EmptyState,
    Divider,
)
from services.comunicacao import ServicoComunicacao


class ComunicacaoInternaFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_comunicacao = ServicoComunicacao()

        self.contatos = []
        self.conversa_ativa = None
        self.conversa_atual = None
        self.mensagens = []
        self.atualizando = False
        self.contador_nao_lidas = {}
        self.atualizacao_periodica = True

        self.usuario_logado_id = controller.usuario_logado_id
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.img_path = os.path.join(self.base_path, "..", "imagens")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.criar_sidebar()
        self.criar_chat_area()

        self.carregar_contatos()
        self.iniciar_atualizacao_periodica()
        self.bind("<Destroy>", self.on_destroy)

    def on_destroy(self, event):
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

    def criar_sidebar(self):
        sidebar_card = Card(self)
        sidebar_card.grid(row=0, column=0, sticky="nsew", padx=(SPACING["page_x"], 12))
        sidebar_card.grid_propagate(False)

        header = ctk.CTkFrame(sidebar_card.body, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 10))
        ctk.CTkLabel(header, text="Mensagens", font=themed_font("h3", "bold"), text_color=THEME["text"]).pack(side="left")
        ctk.CTkLabel(header, text="Conversas internas e suporte", font=themed_font("overline"), text_color=THEME["text_muted"]).pack(side="left", anchor="w")

        GhostButton(header, text="＋", width=36, height=36, command=lambda: None).pack(side="right")

        search = SearchField(sidebar_card.body, placeholder="Buscar conversas...", command=self.filtrar_contatos)
        search.pack(fill="x", padx=16, pady=(0, 12))

        self.scroll_contacts = ctk.CTkScrollableFrame(sidebar_card.body, fg_color="transparent", corner_radius=0)
        self.scroll_contacts.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def carregar_contatos(self):
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
                    "is_staff": True,
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
                            "role": c["role"],
                        }, is_first=(i == 0))
        except Exception as e:
            print(f"Erro ao carregar contatos: {e}")

    def carregar_contador_nao_lidas(self):
        try:
            data = self.servico_comunicacao.contar_mensagens_nao_lidas(self.usuario_logado_id)
            if data and "success" in data and data["success"]:
                self.contador_nao_lidas = data["data"]
        except Exception as e:
            print(f"Erro ao carregar contador de não lidas: {e}")

    def iniciar_atualizacao_periodica(self):
        def task():
            while self.atualizacao_periodica:
                time.sleep(5)
                if not self.atualizando:
                    self.atualizar_dados_conversa()

        threading.Thread(target=task, daemon=True).start()

    def atualizar_dados_conversa(self):
        if not hasattr(self, "winfo_exists") or not self.winfo_exists():
            self.atualizacao_periodica = False
            return

        self.atualizando = True
        try:
            self.carregar_contador_nao_lidas()
            self.atualizar_lista_contatos()
            if self.conversa_atual:
                self.carregar_mensagens()
        except Exception as e:
            if "invalid command name" not in str(e) and "TCL error" not in str(e):
                print(f"Erro na atualização periódica: {e}")
        finally:
            self.atualizando = False

    def atualizar_lista_contatos(self):
        if not hasattr(self, "scroll_contacts") or not self.scroll_contacts.winfo_exists():
            return

        for widget in self.scroll_contacts.winfo_children():
            if hasattr(widget, "contato_data") and widget.winfo_exists():
                contato = widget.contato_data
                unread = self.contador_nao_lidas.get(contato["id"], 0)

                badge = None
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkFrame) and child.winfo_exists():
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ctk.CTkLabel) and grandchild.cget("text").isdigit():
                                badge = child
                                break
                        if badge:
                            break

                if unread > 0:
                    if not badge:
                        info_frame = None
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame) and child.cget("fg_color") == "transparent":
                                info_frame = child
                                break

                        if info_frame and info_frame.winfo_exists():
                            badge = ctk.CTkFrame(info_frame, fg_color=THEME["danger"], corner_radius=RADIUS["pill"])
                            badge.pack(side="right", padx=10)
                            Badge(badge, text=str(unread)).pack()
                    else:
                        for child in badge.winfo_children():
                            if isinstance(child, ctk.CTkLabel) and child.winfo_exists():
                                child.configure(text=str(unread))
                else:
                    if badge and badge.winfo_exists():
                        badge.destroy()

    def filtrar_contatos(self, event):
        termo_busca = self.entry_busca.get().lower() if hasattr(self, "entry_busca") else ""
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
                    "role": c["role"],
                }, is_first=(i == 0))

    def selecionar_conversa(self, contato, item_widget=None):
        for widget in self.scroll_contacts.winfo_children():
            if hasattr(widget, "contato_data"):
                widget.configure(fg_color="transparent")

        if item_widget:
            item_widget.configure(fg_color=THEME["primary_light"])

        self.conversa_ativa = contato
        self.conversa_atual = contato
        self.lbl_chat_nome.configure(text=contato["name"])
        self.lbl_chat_status.configure(
            text="Grupo de comunicação" if contato["role"] == "group" else contato["role"].capitalize()
        )

        avatar = self.get_avatar_por_papel(contato["role"])
        img_h = self.load_image(avatar, (42, 42))
        try:
            for widget in self.lbl_chat_nome.master.master.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("image"):
                    widget.configure(image=img_h)
                    break
        except Exception as e:
            print(f"Erro ao atualizar avatar: {e}")

        self.carregar_mensagens()

    def carregar_mensagens(self):
        if not self.conversa_ativa or not hasattr(self, "winfo_exists") or not self.winfo_exists():
            return

        try:
            if self.conversa_ativa["role"] == "group":
                resultado = self.servico_comunicacao.obter_mensagens_grupo()
            else:
                resultado = self.servico_comunicacao.obter_mensagens(self.usuario_logado_id, self.conversa_ativa["id"])

            if resultado["success"]:
                novas_mensagens = resultado["data"]
                if self.mensagens != novas_mensagens:
                    self.mensagens = novas_mensagens
                    self.atualizar_area_mensagens()
        except Exception as e:
            if "invalid command name" not in str(e) and "TCL error" not in str(e):
                print(f"Erro ao carregar mensagens: {e}")

    def marcar_mensagens_lidas(self):
        for msg in self.mensagens:
            if not msg.get("read"):
                try:
                    self.servico_comunicacao.marcar_mensagem_lida(msg.get("id"))
                except Exception as e:
                    print(f"Erro ao marcar mensagem como lida: {e}")

    def atualizar_area_mensagens(self):
        if not hasattr(self, "msg_area") or not self.msg_area.winfo_exists():
            return

        for widget in self.msg_area.winfo_children():
            if widget.winfo_exists():
                widget.destroy()

        ctk.CTkLabel(
            self.msg_area,
            text="HOJE",
            font=themed_font("overline", "bold"),
            text_color=THEME["text_muted"],
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["pill"],
            width=72,
        ).pack(pady=16)

        for msg in self.mensagens:
            self.criar_mensagem(msg)

    def criar_mensagem(self, msg):
        is_mine = msg["sender_id"] == self.usuario_logado_id
        remetente_nome = "Eu" if is_mine else self.obter_nome_remetente(msg["sender_id"])

        frame = ctk.CTkFrame(self.msg_area, fg_color="transparent")
        frame.pack(fill="x", pady=8)
        frame.msg_data = msg

        align = "right" if is_mine else "left"
        bubble_color = THEME["bubble_sent"] if is_mine else THEME["bubble_recv"]
        text_color = "white" if is_mine else THEME["text"]

        wrapper = ctk.CTkFrame(frame, fg_color="transparent")
        wrapper.pack(side=align, padx=12)

        bubble = ctk.CTkFrame(
            wrapper,
            fg_color=bubble_color,
            corner_radius=RADIUS["xl"],
            border_width=1 if not is_mine else 0,
            border_color=THEME["border"],
        )
        bubble.pack(side="top")

        if self.conversa_ativa and self.conversa_ativa["role"] == "group" and not is_mine:
            ctk.CTkLabel(
                bubble,
                text=remetente_nome,
                font=themed_font("body", "bold"),
                text_color=text_color,
                wraplength=400,
                justify="left",
            ).pack(padx=14, pady=(10, 0))

        if "caminho_arquivo" in msg:
            self.criar_mensagem_arquivo(bubble, msg, text_color)
        else:
            lbl = ctk.CTkLabel(
                bubble,
                text=msg["text"],
                font=themed_font("body"),
                text_color=text_color,
                wraplength=400,
                justify="left",
            )
            lbl.pack(
                padx=14,
                pady=(0 if (self.conversa_ativa and self.conversa_ativa["role"] == "group" and not is_mine) else 10, 10),
            )

        info = ctk.CTkFrame(wrapper, fg_color="transparent")
        info.pack(side="top", fill="x", pady=2)

        timestamp = datetime.datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
        time_str = timestamp.strftime("%H:%M")

        ctk.CTkLabel(info, text=time_str, font=themed_font("overline"), text_color=THEME["text_disabled"]).pack(side=align)
        if is_mine:
            ctk.CTkLabel(info, text="✓✓", font=themed_font("overline"), text_color=THEME["primary"]).pack(side=align, padx=6)

    def criar_mensagem_arquivo(self, bubble, msg, text_color):
        nome_arquivo = os.path.basename(msg["caminho_arquivo"])
        tamanho_arquivo = os.path.getsize(msg["caminho_arquivo"])
        tamanho_str = self.formatar_tamanho_arquivo(tamanho_arquivo)

        card_arquivo = ctk.CTkFrame(bubble, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"], border_width=1, border_color=THEME["border"])
        card_arquivo.pack(padx=14, pady=10, fill="x")

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

        ctk.CTkLabel(card_arquivo, text=icone_arquivo, font=themed_font("h2")).pack(side="left", padx=12, pady=10)

        info_arquivo = ctk.CTkFrame(card_arquivo, fg_color="transparent")
        info_arquivo.pack(side="left", fill="both", expand=True, padx=8, pady=10)

        ctk.CTkLabel(info_arquivo, text=nome_arquivo, font=themed_font("body", "bold"), text_color=text_color, wraplength=260, justify="left").pack(anchor="w")
        ctk.CTkLabel(info_arquivo, text=tamanho_str, font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w")

        botoes = ctk.CTkFrame(card_arquivo, fg_color="transparent")
        botoes.pack(side="right", padx=10, pady=10)

        GhostButton(botoes, text="👁️", width=32, height=32, corner_radius=RADIUS["pill"], command=lambda: self.visualizar_arquivo(msg["caminho_arquivo"])).pack(side="top", pady=2)
        GhostButton(botoes, text="📥", width=32, height=32, corner_radius=RADIUS["pill"], command=lambda: self.download_arquivo(msg["caminho_arquivo"], nome_arquivo)).pack(side="top", pady=2)

    def visualizar_arquivo(self, caminho_arquivo):
        import webbrowser

        try:
            webbrowser.open(caminho_arquivo)
        except Exception as e:
            print(f"Erro ao visualizar arquivo: {e}")

    def download_arquivo(self, caminho_arquivo, nome_arquivo):
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
        txt = self.entry_mensagem.get()
        if txt:
            self.criar_mensagem({
                "sender_id": self.usuario_logado_id,
                "text": txt,
                "timestamp": "2024-05-20T10:45:00Z",
                "read": False,
                "recipient_id": None,
            })
            self.entry_mensagem.delete(0, "end")
            self.msg_area._parent_canvas.yview_moveto(1.0)

    def enviar_mensagem(self):
        txt = self.entry_mensagem.get()
        if txt and self.conversa_ativa:
            try:
                if self.conversa_ativa["role"] == "group":
                    resultado = self.servico_comunicacao.enviar_mensagem_grupo(self.usuario_logado_id, txt)
                else:
                    resultado = self.servico_comunicacao.enviar_mensagem(self.usuario_logado_id, self.conversa_ativa["id"], txt)

                if resultado["success"]:
                    self.carregar_mensagens()
                    self.entry_mensagem.delete(0, "end")
                    self.carregar_contador_nao_lidas()
                    self.atualizar_lista_contatos()
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")

    def criar_contato_item(self, contato, is_first=False):
        item = ctk.CTkFrame(self.scroll_contacts, fg_color="transparent", height=68)
        item.pack(fill="x", padx=8, pady=(0, 6))
        item.pack_propagate(False)
        item.contato_data = contato

        img = self.load_image(contato["img"], (44, 44))
        lbl_avatar = ctk.CTkLabel(item, text="", image=img, width=44, height=44, corner_radius=RADIUS["pill"], fg_color=THEME["border"])
        lbl_avatar.pack(side="left", padx=(4, 10))

        info = ctk.CTkFrame(item, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(info, text=contato["name"], font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(info, text=contato["msg"], font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(2, 8))

        if contato.get("unread", 0) > 0:
            Badge(info, text=str(contato["unread"])).pack(side="right", padx=10)

        item.bind("<Button-1>", lambda e: self.selecionar_conversa(contato, item))
        if is_first:
            self.selecionar_conversa(contato, item)

    def get_avatar_por_papel(self, papel):
        avatares = {
            "admin": "avatar-1.jpg",
            "analista": "avatar-2.jpg",
            "coordenador": "avatar-3.jpg",
            "suporte": "avatar-4.jpg",
            "group": "avatar-6.jpg",
        }
        return avatares.get(papel, "avatar-6.jpg")

    def criar_chat_area(self):
        container = ctk.CTkFrame(self, fg_color=THEME["bg_chat"], corner_radius=0)
        container.grid(row=0, column=1, sticky="nsew")

        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(container, fg_color=THEME["card"], height=80, corner_radius=0, border_width=1, border_color=THEME["border"])
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        inner_h = ctk.CTkFrame(header, fg_color="transparent")
        inner_h.pack(fill="both", expand=True, padx=20, pady=8)

        user_info = ctk.CTkFrame(inner_h, fg_color="transparent")
        user_info.pack(side="left")

        img_h = self.load_image("avatar-2.jpg", (42, 42))
        self.label_avatar = ctk.CTkLabel(user_info, text="", image=img_h, width=42, height=42, corner_radius=21, fg_color=THEME["border"])
        self.label_avatar.pack(side="left", padx=(0, 12))

        title_v = ctk.CTkFrame(user_info, fg_color="transparent")
        title_v.pack(side="left")
        self.lbl_chat_nome = ctk.CTkLabel(title_v, text="Dra. Beatriz Clara", font=themed_font("h3", "bold"), text_color=THEME["text"])
        self.lbl_chat_nome.pack(anchor="w")
        self.lbl_chat_status = ctk.CTkLabel(title_v, text="Online agora", font=themed_font("body"), text_color=THEME["success"])
        self.lbl_chat_status.pack(anchor="w")

        actions = ctk.CTkFrame(inner_h, fg_color="transparent")
        actions.pack(side="right")

        btn_style = {
            "width": 40,
            "height": 40,
            "corner_radius": RADIUS["pill"],
            "fg_color": "transparent",
            "hover_color": THEME["bg_alt"],
            "text_color": THEME["text_muted"],
        }
        GhostButton(actions, text="📷", **btn_style).pack(side="left", padx=4)
        GhostButton(actions, text="📞", **btn_style).pack(side="left", padx=4)
        GhostButton(actions, text="⋮", **btn_style).pack(side="left", padx=4)

        self.msg_area = ctk.CTkScrollableFrame(container, fg_color="transparent")
        self.msg_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)

        input_container = ctk.CTkFrame(container, fg_color=THEME["card"], height=100, corner_radius=0, border_width=1, border_color=THEME["border"])
        input_container.grid(row=2, column=0, sticky="ew")
        input_container.grid_propagate(False)

        box = ctk.CTkFrame(input_container, fg_color=THEME["bg_alt"], height=56, corner_radius=RADIUS["pill"], border_width=1, border_color=THEME["border"])
        box.pack(fill="x", padx=20, pady=16)
        box.pack_propagate(False)

        self.btn_clip = GhostButton(box, text="📎", width=40, height=40, corner_radius=RADIUS["pill"], command=self.toggle_modal_arquivos)
        self.btn_clip.pack(side="left", padx=10)

        self.entry_mensagem = ctk.CTkEntry(box, placeholder_text="Digite sua mensagem...", fg_color="transparent", border_width=0, font=themed_font("body"))
        self.entry_mensagem.pack(side="left", fill="both", expand=True)

        actions_in = ctk.CTkFrame(box, fg_color="transparent")
        actions_in.pack(side="right", padx=10)

        GhostButton(actions_in, text="😊", width=40, height=40, corner_radius=RADIUS["pill"]).pack(side="left", padx=4)

        self.btn_enviar = PrimaryButton(
            actions_in,
            text="➤",
            width=44,
            height=44,
            corner_radius=RADIUS["pill"],
            command=self.enviar_mensagem,
        )
        self.btn_enviar.pack(side="left", padx=(6, 0))

        self.criar_modal_arquivos(container)

    def toggle_modal_arquivos(self):
        if self.modal_arquivos.winfo_manager():
            self.modal_arquivos.grid_remove()
        else:
            btn_x = self.btn_clip.winfo_x()
            btn_y = max(10, self.btn_clip.winfo_y() - 280)
            self.modal_arquivos.grid(row=2, column=0, sticky="w", padx=(btn_x + 25, 0), pady=(btn_y, 0))

    def criar_modal_arquivos(self, parent):
        self.modal_arquivos = ctk.CTkFrame(parent, fg_color=THEME["card"], corner_radius=RADIUS["card"], border_width=1, border_color=THEME["border"])
        self.modal_arquivos.grid(row=2, column=0, sticky="w", padx=20, pady=0)
        self.modal_arquivos.grid_remove()

        categorias = [
            {"nome": "Documentos", "icone": "📄", "extensao": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx"]},
            {"nome": "Imagens", "icone": "🖼️", "extensao": [".jpg", ".jpeg", ".png", ".gif", ".bmp"]},
            {"nome": "Videos", "icone": "🎥", "extensao": [".mp4", ".avi", ".mov", ".wmv"]},
            {"nome": "Audio", "icone": "🎵", "extensao": [".mp3", ".wav", ".ogg"]},
            {"nome": "Planilhas", "icone": "📊", "extensao": [".xls", ".xlsx", ".csv"]},
            {"nome": "Presentações", "icone": "📽️", "extensao": [".ppt", ".pptx"]},
            {"nome": "Arquivos Zip", "icone": "🗜️", "extensao": [".zip", ".rar", ".7z"]},
            {"nome": "Code", "icone": "💻", "extensao": [".py", ".js", ".html", ".css"]},
            {"nome": "Todos", "icone": "📁", "extensao": []},
        ]

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
                font=themed_font("overline"),
                height=60,
                corner_radius=RADIUS["md"],
                fg_color=THEME["bg_alt"],
                hover_color=THEME["border"],
                text_color=THEME["text"],
                command=lambda c=cat: self.selecionar_categoria(c),
            )
            btn.grid(row=row, column=col, padx=5, pady=5)

    def selecionar_categoria(self, categoria):
        import tkinter.filedialog as fd

        if categoria["extensao"]:
            tipos_arquivo = []
            for ext in categoria["extensao"]:
                tipos_arquivo.append((f"{categoria['nome']} (*{ext})", f"*{ext}"))
            tipos_arquivo.append((f"Todos {categoria['nome']}", f"{' '.join([f'*{ext}' for ext in categoria['extensao']])}"))
        else:
            tipos_arquivo = [("Todos os arquivos", "*.*")]

        arquivo = fd.askopenfilename(title=f"Selecione um arquivo {categoria['nome'].lower()}", filetypes=tipos_arquivo)
        if arquivo:
            self.enviar_arquivo(arquivo, categoria["nome"])

    def enviar_arquivo(self, caminho_arquivo, categoria):
        if not self.conversa_ativa:
            return

        try:
            nome_arquivo = os.path.basename(caminho_arquivo)

            if self.conversa_ativa["role"] == "group":
                resultado = self.servico_comunicacao.enviar_mensagem_grupo(self.usuario_logado_id, nome_arquivo, caminho_arquivo, categoria)
            else:
                resultado = self.servico_comunicacao.enviar_mensagem(self.usuario_logado_id, self.conversa_ativa["id"], nome_arquivo, caminho_arquivo, categoria)

            if resultado["success"]:
                self.carregar_mensagens()

            self.modal_arquivos.grid_remove()
        except Exception as e:
            print(f"Erro ao enviar arquivo: {e}")

    def formatar_tamanho_arquivo(self, bytes):
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024 * 1024:
            return f"{round(bytes / 1024, 1)} KB"
        elif bytes < 1024 * 1024 * 1024:
            return f"{round(bytes / (1024 * 1024), 1)} MB"
        else:
            return f"{round(bytes / (1024 * 1024 * 1024), 1)} GB"

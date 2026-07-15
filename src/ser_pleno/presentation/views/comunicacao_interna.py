import customtkinter as ctk
from PIL import Image
import os
import datetime
import logging
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, themed_font, font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.application.controllers.comunicacao import ComunicacaoController
from ser_pleno.utils.async_runner import AsyncRunner
from ser_pleno.presentation.components.icons import IconLabel, IconButton, ICONS
from ser_pleno.presentation.components.ui_components import bind_clickable

logger = logging.getLogger(__name__)


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Design tokens —“ família índigo (consistente com login/app/dashboard)
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••

# Cor de avatar por papel
_CHAT_AVATAR_COLORS = {
    "admin":       THEME["kpi_violet"],
    "analista":    THEME["primary"],
    "coordenador": THEME["success"],
    "suporte":     THEME["warning"],
    "group":       "#EC4899",
}

# Iniciais padrão por papel
_AVATAR_INITIALS = {
    "admin": "AD", "analista": "AN",
    "coordenador": "CO", "suporte": "SP", "group": ICONS["group"],
}

# Ícones de tipo de arquivo
_FILE_ICONS = {
    "Imagens": ICONS["folder"], "Videos": ICONS["video"], "Audio": ICONS["audio"],
    "Planilhas": ICONS["spreadsheet"], "Presentações": ICONS["presentation"],
    "Arquivos Zip": ICONS["zip"], "Code": ICONS["code"],
}


# ——————————————————————————————————————————————————————————————————————————————
#  Helper: avatar colorido com inicial
# ——————————————————————————————————————————————————————————————————————————————
def _make_avatar(parent, initials: str, color: str,
                 size: int = 40) -> ctk.CTkFrame:
    av = ctk.CTkFrame(parent, width=size, height=size,
                      corner_radius=size // 2, fg_color=color)
    av.pack_propagate(False)
    ctk.CTkLabel(
        av, text=initials[:2],
        font=font(size=size // 3, weight="bold"),
        text_color="#FFFFFF",
    ).place(relx=0.5, rely=0.5, anchor="center")
    return av


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Frame principal
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class ComunicacaoInternaFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller          = controller
        self.controller_comunicacao = ComunicacaoController()
        self.contatos:     list  = []
        self.conversa_ativa      = None
        self.conversa_atual      = None
        self.mensagens:    list  = []
        self.atualizando         = False
        self.contador_nao_lidas: dict = {}
        self.atualizacao_periodica    = True
        self.usuario_logado_id        = controller.usuario_logado_id
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.img_path  = os.path.join(self.base_path, "..", "imagens")
        self._images: dict = {}
        self._contact_widgets: dict = {}   # id → frame widget

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._criar_sidebar()
        self._criar_chat_area()
        self.carregar_contatos()
        self._iniciar_atualizacao_periodica()
        self.bind("<Destroy>", self._on_destroy)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Ciclo de vida
    # ••••••••••••••••••••••••••••••••••••••••••
    def _on_destroy(self, _=None):
        self.atualizacao_periodica = False

    def on_destroy(self, event):          # alias legado
        self._on_destroy(event)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Imagens
    # ••••••••••••••••••••••••••••••••••••••••••
    def load_image(self, name: str, size: tuple):
        key = f"{name}:{size}"
        if key in self._images:
            return self._images[key]
        candidates = [
            os.path.join(self.img_path, name),
            os.path.join(self.base_path, "assets", "avatars", name),
            os.path.join(self.base_path, "..", "imagens", name),
        ]
        for path in candidates:
            if path and os.path.exists(path):
                try:
                    img = ctk.CTkImage(light_image=Image.open(path), size=size)
                    self._images[key] = img
                    return img
                except Exception as e:
                    logger.error("Erro ao carregar imagem %s: %s", name, e)
        return None

    def get_avatar_por_papel(self, papel: str) -> str:
        return {
            "admin": "avatar-1.jpg", "analista": "avatar-2.jpg",
            "coordenador": "avatar-3.jpg", "suporte": "avatar-4.jpg",
        }.get(papel, "avatar-6.jpg")

    # ••••••••••••••••••••••••••••••••••••••••••
    #  SIDEBAR —“ lista de contatos
    # ••••••••••••••••••••••••••••••••••••••••••
    def _criar_sidebar(self):
        sidebar = ctk.CTkFrame(
            self,
            width=300,
            fg_color=THEME["surface"],
            corner_radius=0,
            border_width=0,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(2, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        # —— Cabeçalho da sidebar ————————————————————————————————————
        hdr = ctk.CTkFrame(sidebar, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=spacing("lg"), pady=(spacing("lg"), spacing("item_gap")))

        ctk.CTkLabel(
            hdr, text="Mensagens",
            font=font(size=17, weight="bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        # Botão nova conversa
        IconButton(
            hdr, icon=ICONS["add"], size=34,
            fg_color=THEME["primary_soft"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            command=self._nova_conversa,
        ).pack(side="right")

        # —— Campo de busca ——————————————————————————————————————————
        search_wrap = ctk.CTkFrame(
            sidebar, fg_color="#F3F4F6",
            corner_radius=10,
        )
        search_wrap.grid(row=1, column=0, sticky="ew", padx=spacing("md"), pady=(0, spacing("item_gap")))

        IconLabel(
            search_wrap, icon=ICONS["search"], size=20,
            fg_color="transparent", text_color=THEME["text_muted"],
        ).pack(side="left", padx=(10, 0))

        self.entry_busca = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Buscar conversas...",
            fg_color="#F3F4F6",
            border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=font(size=13),
            height=36,
        )
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.entry_busca.bind("<KeyRelease>", self.filtrar_contatos)

        # —— Lista de contatos ———————————————————————————————————————
        ctk.CTkFrame(sidebar, height=1,
                     fg_color=THEME["border"]).grid(
            row=2, column=0, sticky="ew", padx=0, pady=0
        )
        self.scroll_contacts = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            scrollbar_button_color="#D1D5DB",
            scrollbar_button_hover_color="#9CA3AF",
        )
        self.scroll_contacts.grid(row=2, column=0, sticky="nsew")

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Carregar / filtrar contatos
    # ••••••••••••••••••••••••••••••••••••••••••
    def carregar_contatos(self):
        try:
            res = self.controller_comunicacao.listar_contatos(self.usuario_logado_id)
            if res["success"]:
                self.contatos = [
                    c for c in res["data"]
                    if c["role"] in ["admin", "analista", "coordenador", "suporte"]
                ]
                self.contatos.insert(0, {
                    "id": None, "name": "Todos", "email": "",
                    "student_name": "", "role": "group", "is_staff": True,
                })
                self._renderizar_lista_contatos(self.contatos, select_first=True)
        except Exception as e:
            logger.error("Erro ao carregar contatos: %s", e)

    def _renderizar_lista_contatos(self, lista: list, select_first: bool = False):
        if not hasattr(self, "scroll_contacts") or not self.scroll_contacts.winfo_exists():
            return
        for w in self.scroll_contacts.winfo_children():
            w.destroy()
        self._contact_widgets = {}
        for i, c in enumerate(lista):
            self._criar_contato_item(c)
            if select_first and i == 0:
                w = self._contact_widgets.get(c["id"])
                if w:
                    self.selecionar_conversa(c, w)

    def _criar_contato_item(self, contato: dict):
        cid   = contato["id"]
        papel = contato["role"]
        nome  = contato["name"]

        row = ctk.CTkFrame(
            self.scroll_contacts,
            fg_color="transparent",
            corner_radius=10,
            cursor="hand2",
        )
        row.pack(fill="x", padx=spacing("md"), pady=spacing("xs"))
        row.contato_data = contato

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)

        # Avatar colorido com inicial
        av_color = _CHAT_AVATAR_COLORS.get(papel, THEME["primary"])
        av_init  = nome[:2].upper() if papel != "group" else ICONS["group"]
        av = _make_avatar(inner, av_init, av_color, size=44)
        av.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="nsew")

        # Nome
        ctk.CTkLabel(
            inner, text=nome,
            font=font(size=13, weight="bold"),
            text_color=THEME["text"], anchor="w",
        ).grid(row=0, column=1, sticky="w")

        # Sub-label (papel)
        sub = "Grupo de comunicação" if papel == "group" else papel.capitalize()
        ctk.CTkLabel(
            inner, text=sub,
            font=font(size=11),
            text_color=THEME["text_secondary"], anchor="w",
        ).grid(row=1, column=1, sticky="w")

        # Badge de não-lidas (oculto por padrão)
        unread = self.contador_nao_lidas.get(cid, 0)
        badge_frame = ctk.CTkFrame(
            inner, width=22, height=22,
            corner_radius=11, fg_color=THEME["danger"],
        )
        if unread > 0:
            badge_frame.grid(row=0, column=2, rowspan=2, padx=(6, 0))
            badge_frame.grid_propagate(False)
            ctk.CTkLabel(
                badge_frame, text=str(unread),
                font=font(size=9, weight="bold"),
                text_color=THEME["text_on_primary"],
            ).place(relx=0.5, rely=0.5, anchor="center")
        row._badge_frame = badge_frame

        # Hover
        row.bind("<Enter>",   lambda e, r=row: r.configure(fg_color=THEME["primary_soft"]))
        row.bind("<Leave>",   lambda e, r=row, cid2=cid: r.configure(
            fg_color=THEME["primary_soft"]
            if self.conversa_ativa and self.conversa_ativa.get("id") == cid2
            else "transparent"
        ))
        bind_clickable(row, lambda c=contato, r=row: self.selecionar_conversa(c, r))

        self._contact_widgets[cid] = row

    def criar_contato_item(self, contato: dict, is_first: bool = False):
        """Alias legado."""
        self._criar_contato_item(contato)
        if is_first:
            w = self._contact_widgets.get(contato["id"])
            if w:
                self.selecionar_conversa(contato, w)

    def filtrar_contatos(self, _=None):
        termo = self.entry_busca.get().lower() if hasattr(self, "entry_busca") else ""
        filtrados = [
            c for c in self.contatos
            if termo in c["name"].lower() or termo in c["role"].lower()
        ]
        self._renderizar_lista_contatos(filtrados)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Selecionar conversa
    # ••••••••••••••••••••••••••••••••••••••••••
    def _nova_conversa(self):
        """Reseta o estado da conversa atual para iniciar uma nova."""
        self.conversa_ativa = None
        self.conversa_atual = None
        self.mensagens = []

        self.lbl_chat_nome.configure(text="Selecione uma conversa")
        self.lbl_chat_status.configure(text="Online")

        for w in self._header_av_slot.winfo_children():
            w.destroy()
        _make_avatar(self._header_av_slot, "AN", THEME["primary"], 42).pack()

        for w in self.msg_area.winfo_children():
            w.destroy()

    def selecionar_conversa(self, contato: dict, item_widget=None):
        # Limpa seleção anterior
        for w in self.scroll_contacts.winfo_children():
            if hasattr(w, "contato_data"):
                w.configure(fg_color="transparent")
        if item_widget:
            item_widget.configure(fg_color=THEME["primary_soft"])

        self.conversa_ativa = contato
        self.conversa_atual = contato

        # Atualiza header do chat
        nome  = contato["name"]
        papel = contato["role"]
        sub   = "Grupo de comunicação" if papel == "group" else papel.capitalize()

        self.lbl_chat_nome.configure(text=nome)
        self.lbl_chat_status.configure(text=sub)

        # Atualiza avatar no header
        av_color = _CHAT_AVATAR_COLORS.get(papel, THEME["primary"])
        av_init  = nome[:2].upper() if papel != "group" else ICONS["group"]
        for w in self._header_av_slot.winfo_children():
            w.destroy()
        av = _make_avatar(self._header_av_slot, av_init, av_color, size=42)
        av.pack(expand=True)

        self.carregar_mensagens()

    # ••••••••••••••••••••••••••••••••••••••••••
    #  CHAT AREA
    # ••••••••••••••••••••••••••••••••••••••••••
    def _criar_chat_area(self):
        chat = ctk.CTkFrame(self, fg_color=THEME["bg"], corner_radius=0)
        chat.grid(row=0, column=1, sticky="nsew")
        chat.grid_rowconfigure(1, weight=1)
        chat.grid_columnconfigure(0, weight=1)

        self._criar_chat_header(chat)
        self._criar_mensagens_area(chat)
        self._criar_input_area(chat)

    # —— Header —————————————————————————————————————————————————————————————
    def _criar_chat_header(self, parent):
        header = ctk.CTkFrame(
            parent,
            fg_color=THEME["surface"],
            corner_radius=0,
            height=66,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        # Linha de separação base
        ctk.CTkFrame(header, height=1,
                     fg_color=THEME["border"]).pack(side="bottom", fill="x")

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("xl"), pady=0)

        # Slot de avatar (substituível ao trocar conversa)
        self._header_av_slot = ctk.CTkFrame(
            inner, width=44, height=44,
            fg_color="transparent",
        )
        self._header_av_slot.pack(side="left", padx=(0, 14))
        self._header_av_slot.pack_propagate(False)
        # Avatar inicial
        _make_avatar(self._header_av_slot, "AN", THEME["primary"], 42).pack()

        # Nome + status
        title_stack = ctk.CTkFrame(inner, fg_color="transparent")
        title_stack.pack(side="left")

        self.lbl_chat_nome = ctk.CTkLabel(
            title_stack, text="Selecione uma conversa",
            font=font(size=14, weight="bold"),
            text_color=THEME["text"],
        )
        self.lbl_chat_nome.pack(anchor="w")

        status_row = ctk.CTkFrame(title_stack, fg_color="transparent")
        status_row.pack(anchor="w")

        # Ponto verde de status
        ctk.CTkFrame(
            status_row, width=8, height=8,
            corner_radius=4, fg_color=THEME["success"],
        ).pack(side="left", padx=(0, 5))

        self.lbl_chat_status = ctk.CTkLabel(
            status_row, text="Online",
            font=font(size=11),
            text_color=THEME["success"],
        )
        self.lbl_chat_status.pack(side="left")

        # Botões de ação (direita)
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

        for icon_key in ("attach", "document", "send"):
            IconButton(
                actions, icon=ICONS[icon_key], size=36,
                fg_color="transparent",
                hover_color=THEME["primary_soft"],
                text_color=THEME["text_secondary"],
            ).pack(side="left", padx=spacing("xs"))

    # —— Área de mensagens ———————————————————————————————————————————————————
    def _criar_mensagens_area(self, parent):
        self.msg_area = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color="#D1D5DB",
            scrollbar_button_hover_color="#9CA3AF",
        )
        self.msg_area.grid(row=1, column=0, sticky="nsew", padx=spacing("lg"), pady=spacing("md"))

    # —— Input ———————————————————————————————————————————————————————————————
    def _criar_input_area(self, parent):
        input_bar = ctk.CTkFrame(
            parent,
            fg_color=THEME["input_bg"],
            corner_radius=0,
            height=74,
        )
        input_bar.grid(row=2, column=0, sticky="ew")
        input_bar.grid_propagate(False)
        ctk.CTkFrame(input_bar, height=1,
                     fg_color=THEME["border"]).pack(side="top", fill="x")

        inner = ctk.CTkFrame(input_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("lg"), pady=spacing("md"))

        # Caixa de input
        box = ctk.CTkFrame(
            inner,
            fg_color="#F9FAFB",
            corner_radius=14,
            border_width=1,
            border_color=THEME["input_border"],
        )
        box.pack(fill="x", expand=True)

        # Botão clipe
        self.btn_clip = IconButton(
            box, icon=ICONS["attach"], size=36,
            fg_color="transparent",
            hover_color=THEME["primary_soft"],
            text_color=THEME["text_secondary"],
            command=self.toggle_modal_arquivos,
        )
        self.btn_clip.pack(side="left", padx=(8, 0))

        # Entry
        self.entry_mensagem = ctk.CTkEntry(
            box,
            placeholder_text="Digite sua mensagem...",
            fg_color="#F9FAFB",
            border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=font(size=13),
            height=42,
        )
        self.entry_mensagem.pack(side="left", fill="x", expand=True, padx=spacing("xs"))
        self.entry_mensagem.bind("<Return>", lambda e: self.enviar_mensagem())
        self.entry_mensagem.bind("<FocusIn>",  lambda e: box.configure(border_color=THEME["input_border_focus"]))
        self.entry_mensagem.bind("<FocusOut>", lambda e: box.configure(border_color=THEME["input_border"]))

        # Emoji
        IconButton(
            box, icon=ICONS["emoji"], size=36,
            fg_color="transparent",
            hover_color=THEME["primary_soft"],
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=spacing("xs"))

        # Enviar
        self.btn_enviar = IconButton(
            box, icon=ICONS["send_plane"], size=40,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color="#FFFFFF",
            command=self.enviar_mensagem,
        )
        self.btn_enviar.pack(side="right", padx=(4, 8))

        # Modal de arquivos (oculto)
        self._criar_modal_arquivos(parent)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Modal de arquivos (popover)
    # ••••••••••••••••••••••••••••••••••••••••••
    def _criar_modal_arquivos(self, parent):
        self.modal_arquivos = ctk.CTkFrame(
            parent,
            fg_color=THEME["surface"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["border"],
            width=280,
        )
        self.modal_arquivos.grid(row=2, column=0, sticky="sw",
                                  padx=spacing("lg"), pady=spacing("xl"))
        self.modal_arquivos.grid_remove()

        categorias = [
            (ICONS["file"], "Documentos",   [".pdf", ".doc", ".docx", ".txt"]),
            (ICONS["folder"], "Imagens",      [".jpg", ".jpeg", ".png", ".gif"]),
            (ICONS["video"], "Vídeos",       [".mp4", ".avi", ".mov"]),
            (ICONS["audio"], "Áudio",        [".mp3", ".wav", ".ogg"]),
            (ICONS["spreadsheet"], "Planilhas",    [".xls", ".xlsx", ".csv"]),
            (ICONS["presentation"], "Apresentações",[".ppt", ".pptx"]),
            (ICONS["zip"], "Compactados",  [".zip", ".rar", ".7z"]),
            (ICONS["code"], "Código",       [".py", ".js", ".html", ".css"]),
            (ICONS["chart"], "Todos",        []),
        ]

        # Título do popover
        ctk.CTkLabel(
            self.modal_arquivos,
            text="Enviar arquivo",
            font=font(size=13, weight="bold"),
            text_color=THEME["text"],
        ).grid(row=0, column=0, columnspan=3, padx=spacing("md"), pady=(spacing("md"), spacing("item_gap")), sticky="w")

        for i, (icon, nome, exts) in enumerate(categorias):
            btn = ctk.CTkButton(
                self.modal_arquivos,
                text=f"{icon}\n{nome}",
                font=font(size=11),
                height=58, width=78,
                corner_radius=10,
                fg_color=THEME["bg_alt"],
                hover_color=THEME["primary_soft"],
                text_color=THEME["text"],
                command=lambda c={"nome": nome, "extensao": exts}: self.selecionar_categoria(c),
            )
            row_i, col_i = divmod(i, 3)
            btn.grid(row=row_i + 1, column=col_i, padx=spacing("xs"), pady=spacing("xs"))

    def toggle_modal_arquivos(self):
        if self.modal_arquivos.winfo_manager():
            self.modal_arquivos.grid_remove()
        else:
            self.modal_arquivos.grid()

    # Alias legado
    def criar_modal_arquivos(self, parent):
        self._criar_modal_arquivos(parent)

    def criar_chat_area(self):
        self._criar_chat_area()

    def criar_sidebar(self):
        self._criar_sidebar()

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Mensagens
    # ••••••••••••••••••••••••••••••••••••••••••
    def carregar_mensagens(self):
        if not self.conversa_ativa:
            return
        if not hasattr(self, "winfo_exists") or not self.winfo_exists():
            return
        try:
            if self.conversa_ativa["role"] == "group":
                res = self.controller_comunicacao.obter_mensagens_grupo()
            else:
                res = self.controller_comunicacao.obter_mensagens(
                    self.usuario_logado_id, self.conversa_ativa["id"]
                )
            if res["success"]:
                novas = res["data"]
                if self.mensagens != novas:
                    self.mensagens = novas
                    self.atualizar_area_mensagens()
        except Exception as e:
            if "invalid command name" not in str(e):
                logger.error("Erro ao carregar mensagens: %s", e)

    def marcar_mensagens_lidas(self):
        for msg in self.mensagens:
            if not msg.get("read"):
                try:
                    self.controller_comunicacao.marcar_mensagem_lida(msg.get("id"))
                except Exception as e:
                    logger.error("Erro ao marcar como lida: %s", e)

    def atualizar_area_mensagens(self):
        if not hasattr(self, "msg_area") or not self.msg_area.winfo_exists():
            return
        for w in self.msg_area.winfo_children():
            if w.winfo_exists():
                w.destroy()

        # Label de data
        date_lbl = ctk.CTkFrame(
            self.msg_area,
            fg_color=THEME["bg_alt"],
            corner_radius=10,
        )
        date_lbl.pack(pady=(12, 8))
        ctk.CTkLabel(
            date_lbl, text="HOJE",
            font=font(size=10, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(padx=spacing("md"), pady=spacing("xs"))

        for msg in self.mensagens:
            self.criar_mensagem(msg)

        # Scroll para o final
        self.after(50, lambda: self.msg_area._parent_canvas.yview_moveto(1.0))

    def criar_mensagem(self, msg: dict):
        is_mine = msg["sender_id"] == self.usuario_logado_id
        remetente = "Eu" if is_mine else self.obter_nome_remetente(msg["sender_id"])

        outer = ctk.CTkFrame(self.msg_area, fg_color="transparent")
        outer.pack(fill="x", pady=spacing("xs"), padx=spacing("md"))
        outer.msg_data = msg

        side = "right" if is_mine else "left"

        wrapper = ctk.CTkFrame(outer, fg_color="transparent")
        wrapper.pack(side=side, padx=spacing("xs"))

        # Avatar do remetente (mensagens recebidas em grupo)
        if (not is_mine
                and self.conversa_ativa
                and self.conversa_ativa["role"] == "group"):
            av_row = ctk.CTkFrame(wrapper, fg_color="transparent")
            av_row.pack(anchor="w", pady=(0, 2))
            av_color = THEME["primary"]
            for c in self.contatos:
                if c["id"] == msg["sender_id"]:
                    av_color = _CHAT_AVATAR_COLORS.get(c.get("role", ""), THEME["primary"])
                    break
            _make_avatar(av_row, remetente[:2].upper(), av_color, 22).pack(
                side="left", padx=(0, 6)
            )
            ctk.CTkLabel(
                av_row, text=remetente,
                font=font(size=11, weight="bold"),
                text_color=THEME["text_secondary"],
            ).pack(side="left")

        # Bolha
        bubble = ctk.CTkFrame(
            wrapper,
            fg_color=THEME["primary"] if is_mine else THEME["surface"],
            corner_radius=14,
            border_width=0 if is_mine else 1,
            border_color=THEME["border"],
        )
        bubble.pack(anchor="e" if is_mine else "w")

        txt_color = THEME["text_on_primary"] if is_mine else THEME["text"]

        if "caminho_arquivo" in msg:
            self._criar_mensagem_arquivo(bubble, msg, txt_color)
        else:
            ctk.CTkLabel(
                bubble,
                text=msg["text"],
                font=font(size=13),
                text_color=txt_color,
                wraplength=380,
                justify="left",
            ).pack(padx=spacing("md"), pady=(spacing("md"), spacing("item_gap")))

        # Timestamp + ticks
        meta = ctk.CTkFrame(wrapper, fg_color="transparent")
        meta.pack(anchor="e" if is_mine else "w", pady=(2, 0))

        try:
            ts  = datetime.datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
            time_str = ts.strftime("%H:%M")
        except Exception:
            time_str = ""

        ctk.CTkLabel(
            meta, text=time_str,
            font=font(size=10),
            text_color=THEME["text_muted"],
        ).pack(side="left")

        if is_mine:
            ctk.CTkLabel(
                meta, text=f" {ICONS['check']}{ICONS['check']}",
                font=font(size=10),
                text_color=THEME["primary"] if msg.get("read") else THEME["text_muted"],
            ).pack(side="left")

    def _criar_mensagem_arquivo(self, bubble, msg: dict, txt_color: str):
        nome   = os.path.basename(msg["caminho_arquivo"])
        tam    = self._formatar_tamanho(
            os.path.getsize(msg["caminho_arquivo"]) if os.path.exists(msg["caminho_arquivo"]) else 0
        )
        icon   = _FILE_ICONS.get(msg.get("tipo_arquivo", ""), ICONS["file"])

        card = ctk.CTkFrame(
            bubble,
            fg_color=THEME["input_bg"],
            corner_radius=10,
            border_width=1,
            border_color=THEME["border"],
        )
        card.pack(padx=spacing("lg"), pady=spacing("md"), fill="x")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text=icon,
            font=font(size=26),
        ).grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=10)

        ctk.CTkLabel(
            card, text=nome,
            font=font(size=12, weight="bold"),
            text_color=THEME["text"], anchor="w", wraplength=220,
        ).grid(row=0, column=1, sticky="w", pady=(10, 2))

        ctk.CTkLabel(
            card, text=tam,
            font=font(size=11),
            text_color=THEME["text_secondary"], anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(0, 10))

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.grid(row=0, column=2, rowspan=2, padx=(4, 10))

        for icon_btn, cmd in [
            (ICONS["view"], lambda p=msg["caminho_arquivo"]: self.visualizar_arquivo(p)),
            (ICONS["download"], lambda p=msg["caminho_arquivo"], n=nome: self.download_arquivo(p, n)),
        ]:
            ctk.CTkButton(
                btns, text=icon_btn,
                width=30, height=30, corner_radius=8,
                fg_color=THEME["primary_soft"],
                hover_color=THEME["primary_hover"],
                text_color=THEME["primary"],
                font=font(size=14),
                command=cmd,
            ).pack(pady=3)

    def criar_mensagem_arquivo(self, bubble, msg, txt_color):
        self._criar_mensagem_arquivo(bubble, msg, txt_color)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Enviar mensagem / arquivo
    # ••••••••••••••••••••••••••••••••••••••••••
    def enviar_mensagem(self):
        txt = self.entry_mensagem.get().strip()
        if not txt or not self.conversa_ativa:
            return
        try:
            if self.conversa_ativa["role"] == "group":
                res = self.controller_comunicacao.enviar_mensagem_grupo_texto(
                    self.usuario_logado_id, txt
                )
            else:
                res = self.controller_comunicacao.enviar_mensagem(
                    self.usuario_logado_id, self.conversa_ativa["id"], txt
                )
            if res["success"]:
                self.carregar_mensagens()
                self.entry_mensagem.delete(0, "end")
                self.carregar_contador_nao_lidas()
                self.atualizar_lista_contatos()
        except Exception as e:
            logger.error("Erro ao enviar mensagem: %s", e)

    def enviar_msg(self):
        self.enviar_mensagem()

    def selecionar_categoria(self, categoria: dict):
        import tkinter.filedialog as fd
        exts = categoria.get("extensao", [])
        if exts:
            tipos = [(f"{categoria['nome']} (*{e})", f"*{e}") for e in exts]
            tipos.append((f"Todos {categoria['nome']}", " ".join(f"*{e}" for e in exts)))
        else:
            tipos = [("Todos os arquivos", "*.*")]
        arq = fd.askopenfilename(
            title=f"Selecionar {categoria['nome'].lower()}", filetypes=tipos
        )
        if arq:
            self.enviar_arquivo(arq, categoria["nome"])

    def enviar_arquivo(self, caminho: str, categoria: str):
        if not self.conversa_ativa:
            return
        try:
            nome = os.path.basename(caminho)
            if self.conversa_ativa["role"] == "group":
                res = self.controller_comunicacao.enviar_mensagem_grupo_arquivo(
                    self.usuario_logado_id, nome, caminho, categoria
                )
            else:
                res = self.controller_comunicacao.enviar_mensagem(
                    self.usuario_logado_id, self.conversa_ativa["id"],
                    nome, caminho, categoria
                )
            if res["success"]:
                self.carregar_mensagens()
            self.modal_arquivos.grid_remove()
        except Exception as e:
            logger.error("Erro ao enviar arquivo: %s", e)

    def visualizar_arquivo(self, caminho: str):
        import webbrowser
        try:
            webbrowser.open(caminho)
        except Exception as e:
            logger.error("Erro ao visualizar: %s", e)

    def download_arquivo(self, caminho: str, nome: str):
        import tkinter.filedialog as fd
        try:
            destino = fd.asksaveasfilename(
                title="Salvar arquivo", initialfile=nome,
                filetypes=[("Todos os arquivos", "*.*")],
            )
            if destino:
                import shutil
                shutil.copy2(caminho, destino)
        except Exception as e:
            logger.error("Erro ao salvar: %s", e)

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Atualização periódica
    # ••••••••••••••••••••••••••••••••••••••••••
    def _iniciar_atualizacao_periodica(self):
        def ciclo():
            AsyncRunner.run(
                task=self._atualizar_dados,
                on_error=lambda exc: logger.warning("Falha na atualização periódica: %s", exc),
                widget_ref=self,
            )
            if self.atualizacao_periodica and self.winfo_exists():
                self.after(5000, ciclo)

        self.after(5000, ciclo)

    def iniciar_atualizacao_periodica(self):
        self._iniciar_atualizacao_periodica()

    def _atualizar_dados(self):
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
            if "invalid command name" not in str(e):
                logger.error("Erro na atualização: %s", e)
        finally:
            self.atualizando = False

    def atualizar_dados_conversa(self):
        self._atualizar_dados()

    def carregar_contador_nao_lidas(self):
        try:
            data = self.controller_comunicacao.contar_mensagens_nao_lidas(
                self.usuario_logado_id
            )
            if data and data.get("success"):
                self.contador_nao_lidas = data["data"]
        except Exception as e:
            logger.error("Erro ao carregar contador: %s", e)

    def atualizar_lista_contatos(self):
        """Atualiza badges de não-lidas sem redesenhar a lista inteira."""
        if not hasattr(self, "scroll_contacts") or not self.scroll_contacts.winfo_exists():
            return
        for cid, widget in self._contact_widgets.items():
            if not widget.winfo_exists():
                continue
            unread = self.contador_nao_lidas.get(cid, 0)
            badge  = getattr(widget, "_badge_frame", None)
            if badge is None:
                continue
            if unread > 0:
                lbl = next(
                    (c for c in badge.winfo_children() if isinstance(c, ctk.CTkLabel)),
                    None,
                )
                if lbl:
                    lbl.configure(text=str(unread))
                badge.grid()
            else:
                badge.grid_remove()

    # ••••••••••••••••••••••••••••••••••••••••••
    #  Utilitários
    # ••••••••••••••••••••••••••••••••••••••••••
    def obter_nome_remetente(self, id_remetente) -> str:
        for c in self.contatos:
            if c["id"] == id_remetente:
                return c["name"]
        return f"Usuário {id_remetente}"

    @staticmethod
    def _formatar_tamanho(b: int) -> str:
        if b < 1024:
            return f"{b} B"
        if b < 1024 ** 2:
            return f"{b / 1024:.1f} KB"
        if b < 1024 ** 3:
            return f"{b / 1024**2:.1f} MB"
        return f"{b / 1024**3:.1f} GB"

    def formatar_tamanho_arquivo(self, b: int) -> str:
        return self._formatar_tamanho(b)


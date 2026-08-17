import datetime
import logging
import os
import shutil
import time
import tkinter.filedialog as fd
import webbrowser
import customtkinter as ctk
from PIL import Image

from ser_pleno.features.comunicacao.service import ServicoComunicacao
from ser_pleno.config.paths import get_project_root
from ser_pleno.infrastructure.api.api import ClienteAPI
from ser_pleno.infrastructure.api.websocket_client import WebSocketChatClient
from ser_pleno.ui.components.ui_components import bind_clickable
from ser_pleno.ui.components.icons import ICONS, IconButton, IconLabel
from ser_pleno.ui.theme import RADIUS, SPACING, THEME, font, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger(__name__)

_CHAT_AVATAR_COLORS = {
    "admin": THEME["kpi_violet"],
    "analista": THEME["primary"],
    "coordenador": THEME["success"],
    "suporte": THEME["warning"],
    "group": "#EC4899",
}

_AVATAR_INITIALS = {
    "admin": "AD",
    "analista": "AN",
    "coordenador": "CO",
    "suporte": "SP",
    "group": ICONS["group"],
}

_FILE_ICONS = {
    "Imagens": ICONS["folder"],
    "Videos": ICONS["video"],
    "Audio": ICONS["audio"],
    "Planilhas": ICONS["spreadsheet"],
    "Presentações": ICONS["presentation"],
    "Arquivos Zip": ICONS["zip"],
    "Code": ICONS["code"],
}


def _make_avatar(parent, initials: str, color: str, size: int = 40) -> ctk.CTkFrame:
    av = ctk.CTkFrame(parent, width=size, height=size, corner_radius=size // 2, fg_color=color)
    av.pack_propagate(False)
    ctk.CTkLabel(
        av,
        text=initials[:2],
        font=font(size=size // 3, weight="bold"),
        text_color=THEME["text_on_primary"],
    ).place(relx=0.5, rely=0.5, anchor="center")
    return av


class ComunicacaoFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        self._t0 = time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_comunicacao = ServicoComunicacao()
        self.contatos: list = []
        self.conversa_ativa = None
        self.conversa_atual = None
        self.mensagens: list = []
        self.atualizando = False
        self.contador_nao_lidas: dict = {}
        self.atualizacao_periodica = True
        self.usuario_logado_id = controller.usuario_logado_id

        self.base_path = get_project_root()
        self.img_path = os.path.join(self.base_path, "..", "imagens")
        self._images: dict = {}
        self._contact_widgets: dict = {}
        self._ws_client: WebSocketChatClient | None = None
        self._ws_connected = False

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._criar_sidebar()
        self._criar_chat_area()
        self.carregar_contatos()
        self._iniciar_atualizacao_periodica()
        self.bind("<Destroy>", self._on_destroy)
        log_view_init_ms("comunicacao", self._t0, widget_ref=self)

    def _on_destroy(self, event=None):
        self.atualizacao_periodica = False
        self._disconnect_ws()

    def on_destroy(self, event):
        self._on_destroy(event)

    def _get_ws_base_url(self) -> str:
        try:
            api = ClienteAPI()
            return api.base_url
        except Exception as exc:
            logger.debug("Falha ao obter base_url da API: %s", exc)
            return "http://localhost:8000"

    def _connect_ws(self):
        if self._ws_client and self._ws_client.is_connected():
            return
        base_url = self._get_ws_base_url()
        self._ws_client = WebSocketChatClient(base_url=base_url)
        self._ws_client.on("message", self._on_ws_message)
        self._ws_client.on("open", self._on_ws_open)
        self._ws_client.on("close", self._on_ws_close)
        self._ws_client.on("error", self._on_ws_error)
        if self.conversa_ativa and self.conversa_ativa.get("role") != "group":
            target_id = self.conversa_ativa.get("id")
            if target_id is not None:
                self._ws_client.connect(self.usuario_logado_id, target_id)

    def _connect_ws_group(self):
        if self._ws_client and self._ws_client.is_connected():
            self._disconnect_ws()
        base_url = self._get_ws_base_url()
        self._ws_client = WebSocketChatClient(base_url=base_url)
        self._ws_client.on("message", self._on_ws_message)
        self._ws_client.on("open", self._on_ws_open)
        self._ws_client.on("close", self._on_ws_close)
        self._ws_client.on("error", self._on_ws_error)
        self._ws_client.connect_group(self.usuario_logado_id)

    def _disconnect_ws(self) -> None:
        if self._ws_client:
            try:
                self._ws_client.disconnect()
            except Exception as exc:
                logger.debug("Falha ao desconectar WebSocket: %s", exc)
            self._ws_client = None
            self._ws_connected = False

    def _on_ws_open(self):
        self._ws_connected = True
        if hasattr(self, "lbl_chat_status"):
            self.lbl_chat_status.configure(text="Online (WebSocket)")

    def _on_ws_close(self):
        self._ws_connected = False
        if hasattr(self, "lbl_chat_status"):
            self.lbl_chat_status.configure(text="Reconectando...")

    def _on_ws_error(self, exc):
        self._ws_connected = False
        if hasattr(self, "lbl_chat_status"):
            self.lbl_chat_status.configure(text="Erro na conexão")

    def _on_ws_message(self, msg: dict) -> None:
        try:
            if not self.winfo_exists():
                return
            self.after(0, lambda: self._processar_mensagem_ws(msg))
        except Exception as exc:
            logger.debug("Falha em _on_ws_message: %s", exc)

    def _processar_mensagem_ws(self, msg: dict):
        if not self.winfo_exists():
            return
        try:
            self.mensagens.append(msg)
            self.atualizar_area_mensagens()
            self.carregar_contador_nao_lidas()
            self.atualizar_lista_contatos()
        except Exception as e:
            logger.error("Erro ao processar mensagem WebSocket: %s", e)

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
                def _load(p=path, s=size):
                    return ctk.CTkImage(light_image=Image.open(p), size=s)

                def _on_ready(img, k=key):
                    self._images[k] = img

                AsyncRunner.run(task=_load, on_success=_on_ready, widget_ref=self)
                return None
        return None

    def get_avatar_por_papel(self, papel: str) -> str:
        return {
            "admin": "avatar-1.jpg",
            "analista": "avatar-2.jpg",
            "coordenador": "avatar-3.jpg",
            "suporte": "avatar-4.jpg",
        }.get(papel, "avatar-6.jpg")

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

        hdr = ctk.CTkFrame(sidebar, fg_color="transparent")
        hdr.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=spacing("lg"),
            pady=(spacing("lg"), spacing("item_gap")),
        )

        ctk.CTkLabel(
            hdr,
            text="Mensagens",
            font=font(size=17, weight="bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        IconButton(
            hdr,
            icon=ICONS["add"],
            size=34,
            fg_color=THEME["primary_soft"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            command=self._nova_conversa,
        ).pack(side="right")

        IconButton(
            hdr,
            icon=ICONS["check"],
            size=34,
            fg_color=THEME["primary_soft"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            command=self.marcar_todas_mensagens_lidas,
        ).pack(side="right", padx=(0, spacing("xs")))

        search_wrap = ctk.CTkFrame(
            sidebar,
            fg_color=THEME["bg_alt"],
            corner_radius=10,
        )
        search_wrap.grid(
            row=1, column=0, sticky="ew", padx=spacing("md"), pady=(0, spacing("item_gap"))
        )

        IconLabel(
            search_wrap,
            icon=ICONS["search"],
            size=20,
            fg_color="transparent",
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(10, 0))

        self.entry_busca = ctk.CTkEntry(
            search_wrap,
            placeholder_text="Buscar conversas...",
            fg_color=THEME["bg_alt"],
            border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=font(size=13),
            height=36,
        )
        self.entry_busca.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.entry_busca.bind("<KeyRelease>", self.filtrar_contatos)

        ctk.CTkFrame(sidebar, height=1, fg_color=THEME["border"]).grid(
            row=2, column=0, sticky="ew", padx=0, pady=0
        )
        self.scroll_contacts = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.scroll_contacts.grid(row=2, column=0, sticky="nsew")

    def carregar_contatos(self):
        try:
            res = self.servico_comunicacao.listar_contatos(self.usuario_logado_id)
            if res["success"]:
                self.contatos = [
                    c
                    for c in res["data"]
                    if c["role"] in ["admin", "analista", "coordenador", "suporte"]
                ]
                self.contatos.insert(
                    0,
                    {
                        "id": None,
                        "name": "Todos",
                        "email": "",
                        "student_name": "",
                        "role": "group",
                        "is_staff": True,
                    },
                )
                self._renderizar_lista_contatos(self.contatos, select_first=True)
        except Exception as e:
            logger.error("Erro ao carregar contatos: %s", e)

    def _renderizar_lista_contatos(self, lista: list, select_first: bool = False):
        if not hasattr(self, "scroll_contacts") or not self.scroll_contacts.winfo_exists():
            return
        for w in self.scroll_contacts.winfo_children():
            w.destroy()
        self._contact_widgets = {}

        batch = WidgetBatchBuilder(parent=self, batch_size=20)
        for c in lista:
            batch.add(lambda c=c: self._criar_contato_item(c))
        batch.execute()

        if select_first and lista:
            first = lista[0]
            w = self._contact_widgets.get(first.get("id"))
            if w:
                self.selecionar_conversa(first, w)

    def _criar_contato_item(self, contato: dict, is_first: bool = False):
        cid = contato["id"]
        papel = contato["role"]
        nome = contato["name"]

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

        av_color = _CHAT_AVATAR_COLORS.get(papel, THEME["primary"])
        av_init = nome[:2].upper() if papel != "group" else ICONS["group"]
        av = _make_avatar(inner, av_init, av_color, size=44)
        av.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="nsew")

        ctk.CTkLabel(
            inner,
            text=nome,
            font=font(size=13, weight="bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        sub = "Grupo de comunicação" if papel == "group" else papel.capitalize()
        ctk.CTkLabel(
            inner,
            text=sub,
            font=font(size=11),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w")

        unread = self.contador_nao_lidas.get(cid, 0)
        badge_frame = ctk.CTkFrame(
            inner,
            width=22,
            height=22,
            corner_radius=11,
            fg_color=THEME["danger"],
        )
        if unread > 0:
            badge_frame.grid(row=0, column=2, rowspan=2, padx=(6, 0))
            badge_frame.grid_propagate(False)
            ctk.CTkLabel(
                badge_frame,
                text=str(unread),
                font=font(size=9, weight="bold"),
                text_color=THEME["text_on_primary"],
            ).place(relx=0.5, rely=0.5, anchor="center")
        row._badge_frame = badge_frame

        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=THEME["primary_soft"]))
        row.bind(
            "<Leave>",
            lambda e, r=row, cid2=cid: r.configure(
                fg_color=THEME["primary_soft"]
                if self.conversa_ativa and self.conversa_ativa.get("id") == cid2
                else "transparent"
            ),
        )
        bind_clickable(row, lambda c=contato, r=row: self.selecionar_conversa(c, r))

        self._contact_widgets[cid] = row

        if is_first:
            w = self._contact_widgets.get(contato["id"])
            if w:
                self.selecionar_conversa(contato, w)

    def filtrar_contatos(self, _=None):
        termo = self.entry_busca.get().lower() if hasattr(self, "entry_busca") else ""
        filtrados = [
            c for c in self.contatos if termo in c["name"].lower() or termo in c["role"].lower()
        ]
        self._renderizar_lista_contatos(filtrados)

    def _nova_conversa(self):
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
        for w in self.scroll_contacts.winfo_children():
            if hasattr(w, "contato_data"):
                w.configure(fg_color="transparent")
        if item_widget:
            item_widget.configure(fg_color=THEME["primary_soft"])

        self.conversa_ativa = contato
        self.conversa_atual = contato

        nome = contato["name"]
        papel = contato["role"]

        self.lbl_chat_nome.configure(text=nome)
        self.lbl_chat_status.configure(
            text="Conectando..." if not self._ws_connected else "Online (WebSocket)"
        )

        av_color = _CHAT_AVATAR_COLORS.get(papel, THEME["primary"])
        av_init = nome[:2].upper() if papel != "group" else ICONS["group"]
        for w in self._header_av_slot.winfo_children():
            w.destroy()
        av = _make_avatar(self._header_av_slot, av_init, av_color, size=42)
        av.pack(expand=True)

        if papel == "group":
            self._connect_ws_group()
        else:
            self._connect_ws()

        self.carregar_mensagens()

    def _criar_chat_area(self):
        chat = ctk.CTkFrame(self, fg_color=THEME["bg"], corner_radius=0)
        chat.grid(row=0, column=1, sticky="nsew")
        chat.grid_rowconfigure(1, weight=1)
        chat.grid_columnconfigure(0, weight=1)

        self._criar_chat_header(chat)
        self._criar_mensagens_area(chat)
        self._criar_input_area(chat)

    def _criar_chat_header(self, parent):
        header = ctk.CTkFrame(
            parent,
            fg_color=THEME["surface"],
            corner_radius=0,
            height=66,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        ctk.CTkFrame(header, height=1, fg_color=THEME["border"]).pack(side="bottom", fill="x")

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("xl"), pady=0)

        self._header_av_slot = ctk.CTkFrame(
            inner,
            width=44,
            height=44,
            fg_color="transparent",
        )
        self._header_av_slot.pack(side="left", padx=(0, 14))
        self._header_av_slot.pack_propagate(False)
        _make_avatar(self._header_av_slot, "AN", THEME["primary"], 42).pack()

        title_stack = ctk.CTkFrame(inner, fg_color="transparent")
        title_stack.pack(side="left")

        self.lbl_chat_nome = ctk.CTkLabel(
            title_stack,
            text="Selecione uma conversa",
            font=font(size=14, weight="bold"),
            text_color=THEME["text"],
        )
        self.lbl_chat_nome.pack(anchor="w")

        status_row = ctk.CTkFrame(title_stack, fg_color="transparent")
        status_row.pack(anchor="w")

        ctk.CTkFrame(
            status_row,
            width=8,
            height=8,
            corner_radius=4,
            fg_color=THEME["success"],
        ).pack(side="left", padx=(0, 5))

        self.lbl_chat_status = ctk.CTkLabel(
            status_row,
            text="Online",
            font=font(size=11),
            text_color=THEME["success"],
        )
        self.lbl_chat_status.pack(side="left")

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(side="right")

        for icon_key in ("attach", "document", "send"):
            IconButton(
                actions,
                icon=ICONS[icon_key],
                size=36,
                fg_color="transparent",
                hover_color=THEME["primary_soft"],
                text_color=THEME["text_secondary"],
            ).pack(side="left", padx=spacing("xs"))

    def _criar_mensagens_area(self, parent):
        self.msg_area = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.msg_area.grid(row=1, column=0, sticky="nsew", padx=spacing("lg"), pady=spacing("md"))

    def _criar_input_area(self, parent):
        input_bar = ctk.CTkFrame(
            parent,
            fg_color=THEME["input_bg"],
            corner_radius=0,
            height=74,
        )
        input_bar.grid(row=2, column=0, sticky="ew")
        input_bar.grid_propagate(False)
        ctk.CTkFrame(input_bar, height=1, fg_color=THEME["border"]).pack(side="top", fill="x")

        inner = ctk.CTkFrame(input_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=spacing("lg"), pady=spacing("md"))

        box = ctk.CTkFrame(
            inner,
            fg_color=THEME["input_bg"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["input_border"],
        )
        box.pack(fill="x", expand=True)

        self.btn_clip = IconButton(
            box,
            icon=ICONS["attach"],
            size=36,
            fg_color="transparent",
            hover_color=THEME["primary_soft"],
            text_color=THEME["text_secondary"],
            command=self.toggle_modal_arquivos,
        )
        self.btn_clip.pack(side="left", padx=(8, 0))

        self.entry_mensagem = ctk.CTkEntry(
            box,
            placeholder_text="Digite sua mensagem...",
            fg_color=THEME["input_bg"],
            border_width=0,
            text_color=THEME["text"],
            placeholder_text_color=THEME["text_muted"],
            font=font(size=13),
            height=42,
        )
        self.entry_mensagem.pack(side="left", fill="x", expand=True, padx=spacing("xs"))
        self.entry_mensagem.bind("<Return>", lambda e: self.enviar_mensagem())
        self.entry_mensagem.bind(
            "<FocusIn>", lambda e: box.configure(border_color=THEME["input_border_focus"])
        )
        self.entry_mensagem.bind(
            "<FocusOut>", lambda e: box.configure(border_color=THEME["input_border"])
        )

        IconButton(
            box,
            icon=ICONS["emoji"],
            size=36,
            fg_color="transparent",
            hover_color=THEME["primary_soft"],
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=spacing("xs"))

        self.btn_enviar = IconButton(
            box,
            icon=ICONS["send_plane"],
            size=40,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_on_primary"],
            command=self.enviar_mensagem,
        )
        self.btn_enviar.pack(side="right", padx=(4, 8))

        self._criar_modal_arquivos(parent)

    def _criar_modal_arquivos(self, parent):
        self.modal_arquivos = ctk.CTkFrame(
            parent,
            fg_color=THEME["surface"],
            corner_radius=14,
            border_width=1,
            border_color=THEME["border"],
            width=280,
        )
        self.modal_arquivos.grid(
            row=2, column=0, sticky="sw", padx=spacing("lg"), pady=spacing("xl")
        )
        self.modal_arquivos.grid_remove()

        categorias = [
            (ICONS["file"], "Documentos", [".pdf", ".doc", ".docx", ".txt"]),
            (ICONS["folder"], "Imagens", [".jpg", ".jpeg", ".png", ".gif"]),
            (ICONS["video"], "Vídeos", [".mp4", ".avi", ".mov"]),
            (ICONS["audio"], "Áudio", [".mp3", ".wav", ".ogg"]),
            (ICONS["spreadsheet"], "Planilhas", [".xls", ".xlsx", ".csv"]),
            (ICONS["presentation"], "Apresentações", [".ppt", ".pptx"]),
            (ICONS["zip"], "Compactados", [".zip", ".rar", ".7z"]),
            (ICONS["code"], "Código", [".py", ".js", ".html", ".css"]),
            (ICONS["chart"], "Todos", []),
        ]

        ctk.CTkLabel(
            self.modal_arquivos,
            text="Enviar arquivo",
            font=font(size=13, weight="bold"),
            text_color=THEME["text"],
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            padx=spacing("md"),
            pady=(spacing("md"), spacing("item_gap")),
            sticky="w",
        )

        for i, (icon, nome, exts) in enumerate(categorias):
            btn = ctk.CTkButton(
                self.modal_arquivos,
                text=f"{icon}\n{nome}",
                font=font(size=11),
                height=58,
                width=78,
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

    def carregar_mensagens(self):
        if not self.conversa_ativa or not hasattr(self, "winfo_exists") or not self.winfo_exists():
            return
        try:
            if self.conversa_ativa["role"] == "group":
                res = self.servico_comunicacao.obter_mensagens_grupo()
            else:
                res = self.servico_comunicacao.obter_mensagens(
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
                    self.servico_comunicacao.marcar_mensagem_lida(msg.get("id"))
                except Exception as e:
                    logger.error("Erro ao marcar como lida: %s", e)

    def atualizar_area_mensagens(self):
        if not hasattr(self, "msg_area") or not self.msg_area.winfo_exists():
            return
        for w in self.msg_area.winfo_children():
            if w.winfo_exists():
                w.destroy()

        date_lbl = ctk.CTkFrame(
            self.msg_area,
            fg_color=THEME["bg_alt"],
            corner_radius=10,
        )
        date_lbl.pack(pady=(12, 8))
        ctk.CTkLabel(
            date_lbl,
            text="HOJE",
            font=font(size=10, weight="bold"),
            text_color=THEME["text_secondary"],
        ).pack(padx=spacing("md"), pady=spacing("xs"))

        batch = WidgetBatchBuilder(parent=self, batch_size=20)
        for msg in self.mensagens:
            batch.add(lambda msg=msg: self.criar_mensagem(msg))
        batch.execute()

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

        if not is_mine and self.conversa_ativa and self.conversa_ativa["role"] == "group":
            av_row = ctk.CTkFrame(wrapper, fg_color="transparent")
            av_row.pack(anchor="w", pady=(0, 2))
            av_color = THEME["primary"]
            for c in self.contatos:
                if c["id"] == msg["sender_id"]:
                    av_color = _CHAT_AVATAR_COLORS.get(c.get("role", ""), THEME["primary"])
                    break
            _make_avatar(av_row, remetente[:2].upper(), av_color, 22).pack(side="left", padx=(0, 6))
            ctk.CTkLabel(
                av_row,
                text=remetente,
                font=font(size=11, weight="bold"),
                text_color=THEME["text_secondary"],
            ).pack(side="left")

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

        meta = ctk.CTkFrame(wrapper, fg_color="transparent")
        meta.pack(anchor="e" if is_mine else "w", pady=(2, 0))

        try:
            ts = datetime.datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
            time_str = ts.strftime("%H:%M")
        except Exception as exc:
            logger.debug("Falha ao formatar timestamp da mensagem: %s", exc)
            time_str = ""

        ctk.CTkLabel(
            meta,
            text=time_str,
            font=font(size=10),
            text_color=THEME["text_muted"],
        ).pack(side="left")

        if is_mine:
            ctk.CTkLabel(
                meta,
                text=f" {ICONS['check']}{ICONS['check']}",
                font=font(size=10),
                text_color=THEME["primary"] if msg.get("read") else THEME["text_muted"],
            ).pack(side="left")

        def _abrir_menu(event):
            self._abrir_menu_contexto_mensagem(event, msg, bubble)

        bubble.bind("<Button-3>", _abrir_menu)
        wrapper.bind("<Button-3>", _abrir_menu)

    def _criar_mensagem_arquivo(self, bubble, msg: dict, txt_color: str):
        nome = os.path.basename(msg["caminho_arquivo"])
        tam = self._formatar_tamanho(
            os.path.getsize(msg["caminho_arquivo"]) if os.path.exists(msg["caminho_arquivo"]) else 0
        )
        icon = _FILE_ICONS.get(msg.get("tipo_arquivo", ""), ICONS["file"])

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
            card,
            text=icon,
            font=font(size=26),
        ).grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=10)

        ctk.CTkLabel(
            card,
            text=nome,
            font=font(size=12, weight="bold"),
            text_color=THEME["text"],
            anchor="w",
            wraplength=220,
        ).grid(row=0, column=1, sticky="w", pady=(10, 2))

        ctk.CTkLabel(
            card,
            text=tam,
            font=font(size=11),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(0, 10))

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.grid(row=0, column=2, rowspan=2, padx=(4, 10))

        for icon_btn, cmd in [
            (ICONS["view"], lambda p=msg["caminho_arquivo"]: self.visualizar_arquivo(p)),
            (
                ICONS["download"],
                lambda p=msg["caminho_arquivo"], n=nome: self.download_arquivo(p, n),
            ),
        ]:
            ctk.CTkButton(
                btns,
                text=icon_btn,
                width=30,
                height=30,
                corner_radius=8,
                fg_color=THEME["primary_soft"],
                hover_color=THEME["primary_hover"],
                text_color=THEME["primary"],
                font=font(size=14),
                command=cmd,
            ).pack(pady=3)

    def enviar_mensagem(self):
        txt = self.entry_mensagem.get().strip()
        if not txt or not self.conversa_ativa:
            return
        try:
            if self.conversa_ativa["role"] == "group":
                if self._ws_client and self._ws_client.is_connected():
                    self._ws_client.send(
                        {"type": "group_message", "text": txt, "sender_id": self.usuario_logado_id}
                    )
                res = self.servico_comunicacao.enviar_mensagem_grupo(self.usuario_logado_id, txt)
            else:
                if self._ws_client and self._ws_client.is_connected():
                    self._ws_client.send(
                        {
                            "type": "private_message",
                            "text": txt,
                            "sender_id": self.usuario_logado_id,
                            "recipient_id": self.conversa_ativa["id"],
                        }
                    )
                res = self.servico_comunicacao.enviar_mensagem(
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
        exts = categoria.get("extensao", [])
        if exts:
            tipos = [(f"{categoria['nome']} (*{e})", f"*{e}") for e in exts]
            tipos.append((f"Todos {categoria['nome']}", " ".join(f"*{e}" for e in exts)))
        else:
            tipos = [("Todos os arquivos", "*.*")]
        arq = fd.askopenfilename(title=f"Selecionar {categoria['nome'].lower()}", filetypes=tipos)
        if arq:
            self.enviar_arquivo(arq, categoria["nome"])

    def enviar_arquivo(self, caminho: str, categoria: str):
        if not self.conversa_ativa:
            return
        try:
            nome = os.path.basename(caminho)
            if self.conversa_ativa["role"] == "group":
                res = self.servico_comunicacao.enviar_mensagem_grupo(
                    self.usuario_logado_id, nome, caminho, categoria
                )
            else:
                res = self.servico_comunicacao.enviar_mensagem(
                    self.usuario_logado_id, self.conversa_ativa["id"], nome
                )
            if res["success"]:
                self.carregar_mensagens()
            self.modal_arquivos.grid_remove()
        except Exception as e:
            logger.error("Erro ao enviar arquivo: %s", e)

    def visualizar_arquivo(self, caminho: str):
        try:
            webbrowser.open(caminho)
        except Exception as e:
            logger.error("Erro ao visualizar: %s", e)

    def download_arquivo(self, caminho: str, nome: str):
        try:
            destino = fd.asksaveasfilename(
                title="Salvar arquivo",
                initialfile=nome,
                filetypes=[("Todos os arquivos", "*.*")],
            )
            if destino:
                shutil.copy2(caminho, destino)
        except Exception as e:
            logger.error("Erro ao salvar: %s", e)

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

    def carregar_contador_nao_lidas(self):
        try:
            data = self.servico_comunicacao.contar_mensagens_nao_lidas(self.usuario_logado_id)
            if data and data.get("success"):
                self.contador_nao_lidas = data["data"]
        except Exception as e:
            logger.error("Erro ao carregar contador: %s", e)

    def marcar_todas_mensagens_lidas(self):
        try:
            res = self.servico_comunicacao.marcar_todas_mensagens_lidas(self.usuario_logado_id)
            if res["success"]:
                self.carregar_contador_nao_lidas()
                self.atualizar_lista_contatos()
                if self.conversa_atual:
                    self.carregar_mensagens()
        except Exception as e:
            logger.error("Erro ao marcar todas como lidas: %s", e)

    def excluir_mensagem(self, mensagem_id: int):
        try:
            res = self.servico_comunicacao.excluir_mensagem(mensagem_id)
            if res["success"]:
                self.carregar_mensagens()
                self.carregar_contador_nao_lidas()
                self.atualizar_lista_contatos()
        except Exception as e:
            logger.error("Erro ao excluir mensagem: %s", e)

    def _abrir_menu_contexto_mensagem(self, event, msg: dict, bubble_widget):
        menu = ctk.CTkFrame(
            self,
            fg_color=THEME["surface"],
            corner_radius=8,
            border_width=1,
            border_color=THEME["border"],
        )
        x = event.x_root - self.winfo_rootx()
        y = event.y_root - self.winfo_rooty()
        menu.place(x=x, y=y)
        menu.lift()
        menu.grab_set()

        def fechar_menu():
            menu.grab_release()
            menu.destroy()

        opcoes = []
        if not msg.get("read"):
            opcoes.append(
                (
                    "Marcar como lida",
                    lambda: self._marcar_mensagem_lida_individual(msg, fechar_menu),
                )
            )
        opcoes.append(("Excluir", lambda: self._confirmar_exclusao_mensagem(msg, fechar_menu)))

        for texto, cmd in opcoes:
            btn = ctk.CTkButton(
                menu,
                text=texto,
                font=font(size=12),
                fg_color="transparent",
                hover_color=THEME["primary_soft"],
                text_color=THEME["text"],
                anchor="w",
                command=cmd,
            )
            btn.pack(fill="x", padx=spacing("sm"), pady=spacing("xs"))

        menu.bind("<FocusOut>", lambda e: fechar_menu())
        menu.focus_set()

    def _marcar_mensagem_lida_individual(self, msg: dict, fechar_menu):
        try:
            self.servico_comunicacao.marcar_mensagem_lida(msg["id"])
            self.carregar_mensagens()
            self.carregar_contador_nao_lidas()
            self.atualizar_lista_contatos()
        except Exception as e:
            logger.error("Erro ao marcar mensagem como lida: %s", e)
        finally:
            fechar_menu()

    def _confirmar_exclusao_mensagem(self, msg: dict, fechar_menu):
        fechar_menu()
        confirmacao = ctk.CTkFrame(
            self,
            fg_color=THEME["surface"],
            corner_radius=12,
            border_width=1,
            border_color=THEME["border"],
        )
        confirmacao.place(relx=0.5, rely=0.5, anchor="center")
        confirmacao.lift()

        ctk.CTkLabel(
            confirmacao,
            text="Excluir mensagem?",
            font=font(size=14, weight="bold"),
            text_color=THEME["text"],
        ).pack(padx=spacing("lg"), pady=(spacing("lg"), spacing("item_gap")))

        ctk.CTkLabel(
            confirmacao,
            text="Esta ação não pode ser desfeita.",
            font=font(size=12),
            text_color=THEME["text_secondary"],
        ).pack(padx=spacing("lg"), pady=(0, spacing("md")))

        botoes = ctk.CTkFrame(confirmacao, fg_color="transparent")
        botoes.pack(padx=spacing("lg"), pady=(0, spacing("lg")), fill="x")

        def confirmar():
            confirmacao.destroy()
            self.excluir_mensagem(msg["id"])

        def cancelar():
            confirmacao.destroy()

        ctk.CTkButton(
            botoes,
            text="Cancelar",
            font=font(size=12),
            fg_color=THEME["bg_alt"],
            hover_color=THEME["primary_soft"],
            text_color=THEME["text"],
            command=cancelar,
        ).pack(side="left", fill="x", expand=True, padx=(0, spacing("xs")))

        ctk.CTkButton(
            botoes,
            text="Excluir",
            font=font(size=12, weight="bold"),
            fg_color=THEME["danger"],
            hover_color="#DC2626",
            text_color=THEME["text_on_primary"],
            command=confirmar,
        ).pack(side="left", fill="x", expand=True, padx=(spacing("xs"), 0))

        confirmacao.bind("<FocusOut>", lambda e: confirmacao.destroy())
        confirmacao.focus_set()

    def atualizar_lista_contatos(self):
        if not hasattr(self, "scroll_contacts") or not self.scroll_contacts.winfo_exists():
            return
        for cid, widget in self._contact_widgets.items():
            if not widget.winfo_exists():
                continue
            unread = (
                (self.contador_nao_lidas or {}).get(cid, 0)
                if isinstance(self.contador_nao_lidas, dict)
                else 0
            )
            badge = getattr(widget, "_badge_frame", None)
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

    def obter_nome_remetente(self, id_remetente) -> str:
        for c in self.contatos:
            if c["id"] == id_remetente:
                return c["name"]
        return f"Usuário {id_remetente}"

    @staticmethod
    def _formatar_tamanho(b: int) -> str:
        if b < 1024:
            return f"{b} B"
        if b < 1024**2:
            return f"{b / 1024:.1f} KB"
        if b < 1024**3:
            return f"{b / 1024**2:.1f} MB"
        return f"{b / 1024**3:.1f} GB"
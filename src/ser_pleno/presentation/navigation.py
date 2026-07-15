"""Gerenciador de navegação da aplicação SerPleno."""

from __future__ import annotations

import logging
import time

import customtkinter as ctk

from ser_pleno.ui.theme import THEME, SPACING, font
from ser_pleno.presentation.components.icons import ICONS
from ser_pleno.presentation.components.ui_components import GhostButton, Avatar, Divider
from ser_pleno.presentation.views.dashboard import DashboardFrame
from ser_pleno.presentation.views.estudantes import EstudantesFrame
from ser_pleno.presentation.views.agenda import AgendaFrame
from ser_pleno.presentation.views.bem_estar import BemEstarFrame
from ser_pleno.presentation.views.analise_triagem import AnaliseTriagemFrame
from ser_pleno.presentation.views.relatorio import RelatorioFrame
from ser_pleno.presentation.views.comunicacao_interna import ComunicacaoInternaFrame
from ser_pleno.presentation.views.orientacoes import OrientacoesFrame
from ser_pleno.presentation.views.quadro_avisos import QuadroAvisosFrame
from ser_pleno.presentation.views.configuracoes import ConfiguracoesFrame

logger = logging.getLogger(__name__)

MENU_ITEMS = [
    {"key": "dashboard",     "label": "Dashboard",         "icon": ICONS["chart"], "frame": DashboardFrame,
     "header": ("Dashboard", "Resumo geral do ambiente")},
    {"key": "estudantes",    "label": "Estudantes",        "icon": ICONS["users"], "frame": EstudantesFrame,
     "header": ("Estudantes", "Acompanhamento e gestao academica")},
    {"key": "agenda",        "label": "Agenda",            "icon": ICONS["calendar"], "frame": AgendaFrame,
     "header": ("Agenda", "Planejamento e compromissos")},
    {"key": "bem_estar",     "label": "Bem-estar",         "icon": ICONS["heart_blue"], "frame": BemEstarFrame,
     "header": ("Bem-estar", "Monitoramento e apoio emocional")},
    {"key": "analise",       "label": "Analise",           "icon": ICONS["search"], "frame": AnaliseTriagemFrame,
     "header": ("Analise", "Triagem e classificacao")},
    {"key": "relatorios",    "label": "Relatorios",        "icon": ICONS["empty"], "frame": RelatorioFrame,
     "header": ("Relatorios", "Indicadores e exportacoes")},
    {"key": "comunicacao",   "label": "Comunicacao",       "icon": ICONS["chat"], "frame": ComunicacaoInternaFrame,
     "header": ("Comunicacao", "Mensagens internas e suporte")},
    {"key": "orientacoes",   "label": "Orientacoes",       "icon": ICONS["compass"], "frame": OrientacoesFrame,
     "header": ("Orientacoes", "Fluxo de apoio e encaminhamentos")},
    {"key": "avisos",        "label": "Quadro de avisos",  "icon": ICONS["megaphone"], "frame": QuadroAvisosFrame,
     "header": ("Avisos", "Quadro de comunicacao institucional")},
    {"key": "configuracoes", "label": "Configuracoes",     "icon": ICONS["settings"], "frame": ConfiguracoesFrame,
     "header": ("Configuracoes", "Preferencias da aplicacao")},
]
_MENU_BY_KEY = {item["key"]: item for item in MENU_ITEMS}

SIDEBAR_WIDTH = 272
PAGE_HEADER_HEIGHT = 86


class NavigationManager:
    """Gerencia a navegação entre telas da aplicação."""

    def __init__(self, app):
        self.app = app
        self._menu_ativo = None
        self.menu_buttons = {}

    # ================= SIDEBAR =================
    def criar_sidebar(self):
        self.app.sidebar = ctk.CTkFrame(
            self.app.container,
            width=SIDEBAR_WIDTH,
            fg_color=THEME["nav_bg"],
            corner_radius=0,
            border_width=0,
        )
        self.app.sidebar.grid(row=0, column=0, sticky="nsew")
        self.app.sidebar.pack_propagate(False)

        self._criar_marca()
        Divider(self.app.sidebar).pack(fill="x", padx=18, pady=(6, 16))

        menu_label = ctk.CTkLabel(
            self.app.sidebar,
            text="NAVEGACAO",
            font=font(11, "bold"),
            text_color=THEME["text_muted"],
        )
        menu_label.pack(anchor="w", padx=22, pady=(4, 10))

        self.app.menu_container = ctk.CTkScrollableFrame(
            self.app.sidebar, fg_color="transparent",
            scrollbar_button_color=THEME["nav_bg"],
            scrollbar_button_hover_color=THEME["border_strong"],
        )
        self.app.menu_container.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        self._criar_menu()
        self._criar_rodape_sidebar()

    def _criar_marca(self):
        brand_frame = ctk.CTkFrame(self.app.sidebar, fg_color="transparent")
        brand_frame.pack(pady=(24, 16), padx=20, fill="x")

        icon_lbl = ctk.CTkLabel(
            brand_frame,
            text=f"{ICONS['group']} ",
            font=font(22, "bold"),
            text_color=THEME["brand_accent"],
        )
        icon_lbl.pack(side="left", padx=(0, 10))

        title_frame = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_frame,
            text="SerPleno",
            font=font(20, "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="Gestao escolar e bem-estar",
            font=font(11),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

    def _criar_rodape_sidebar(self):
        footer = ctk.CTkFrame(self.app.sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(12, 18), side="bottom")

        nome = self.app.usuario_logado.get("first_name") or self.app.usuario_logado.get("username", "usuario")
        iniciais = "".join(p[0] for p in nome.split()[:2]).upper() or "U"

        self.app.user_chip = ctk.CTkFrame(footer, fg_color=THEME["primary_soft"], corner_radius=14)
        self.app.user_chip.pack(fill="x", pady=(0, 10))

        chip_inner = ctk.CTkFrame(self.app.user_chip, fg_color="transparent")
        chip_inner.pack(fill="x", padx=12, pady=10)

        Avatar(chip_inner, initials=iniciais, size=36, color=THEME["primary"]).pack(side="left", padx=(0, 10))

        texto_frame = ctk.CTkFrame(chip_inner, fg_color="transparent")
        texto_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            texto_frame,
            text=f"Ola, {nome}",
            font=font(12, "bold"),
            text_color=THEME["primary"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            texto_frame,
            text="Psicologa(o) escolar",
            font=font(10),
            text_color=THEME["text_muted"],
            anchor="w",
        ).pack(fill="x")

        modo_atual = get_mode()
        rotulo = f"{ICONS['moon']}  Modo escuro" if modo_atual == "light" else f"{ICONS['sun']}  Modo claro"
        self.app.theme_toggle_btn = ctk.CTkButton(
            footer,
            text=rotulo,
            command=self.app.theme_manager.toggle,
            height=40,
            corner_radius=10,
            fg_color=THEME["surface"],
            hover_color=THEME["nav_hover"],
            text_color=THEME["text"],
            border_width=1,
            border_color=THEME["border"],
            cursor="hand2",
        )
        self.app.theme_toggle_btn.pack(fill="x")

    def _criar_menu(self):
        self.menu_buttons = {}
        for item in MENU_ITEMS:
            self._criar_botao_menu(item)

    def _criar_botao_menu(self, item: dict) -> None:
        key = item["key"]
        item_frame = ctk.CTkFrame(self.app.menu_container, fg_color="transparent")
        item_frame.pack(fill="x", padx=6, pady=3)

        indicator = ctk.CTkFrame(item_frame, width=4, height=36, corner_radius=999, fg_color="transparent")
        indicator.pack(side="left", fill="y", padx=(2, 8))

        btn = GhostButton(
            item_frame,
            text=item["label"],
            icon=item["icon"],
            command=lambda k=key: self.show(k),
            width=210,
            height=40,
            corner_radius=10,
            anchor="w",
        )
        btn.pack(side="left", fill="x", expand=True)

        self.menu_buttons[key] = {"frame": item_frame, "indicator": indicator, "btn": btn}
        self._aplicar_estilo_botao_menu(key, active=(key == self._menu_ativo))

    def _aplicar_estilo_botao_menu(self, key: str, active: bool = False) -> None:
        data = self.menu_buttons.get(key)
        if not data:
            return

        btn = data["btn"]
        indicator = data["indicator"]

        if active:
            indicator.configure(fg_color=THEME["brand_accent"])
            btn.configure(
                fg_color=THEME["nav_active_bg"],
                hover_color=THEME["nav_active_bg"],
                text_color=THEME["nav_active_text"],
                border_color=THEME["nav_active_text"],
                border_width=1,
            )
        else:
            indicator.configure(fg_color="transparent")
            btn.configure(
                fg_color="transparent",
                hover_color=THEME["nav_hover"],
                text_color=THEME["nav_text"],
                border_width=0,
            )

    # ================= AREA DE CONTEUDO =================
    def criar_area_conteudo(self):
        self.app.content = ctk.CTkFrame(self.app.container, fg_color=THEME["bg"])
        self.app.content.grid(row=0, column=1, sticky="nsew")
        self.app.content.grid_columnconfigure(0, weight=1)
        self.app.content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.app.content, fg_color="transparent", height=PAGE_HEADER_HEIGHT)
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 8))
        header.grid_columnconfigure(0, weight=1)

        self.app.header_title = ctk.CTkLabel(
            header,
            text="Dashboard",
            font=font(24, "bold"),
            text_color=THEME["text"],
            anchor="w",
        )
        self.app.header_title.grid(row=0, column=0, sticky="w")

        self.app.header_subtitle = ctk.CTkLabel(
            header,
            text="Resumo geral do ambiente",
            font=font(12),
            text_color=THEME["text_secondary"],
            anchor="w",
        )
        self.app.header_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.app.content_body = ctk.CTkFrame(self.app.content, fg_color="transparent")
        self.app.content_body.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))

    # ================= NAVEGACAO =================
    def atualizar_menu(self, active_key: str) -> None:
        self._menu_ativo = active_key
        for key in self.menu_buttons:
            self._aplicar_estilo_botao_menu(key, key == active_key)

    def atualizar_header(self, title: str, subtitle: str) -> None:
        if hasattr(self.app, "header_title") and self.app.header_title.winfo_exists():
            self.app.header_title.configure(text=title)
        if hasattr(self.app, "header_subtitle") and self.app.header_subtitle.winfo_exists():
            self.app.header_subtitle.configure(text=subtitle)

    def show(self, key: str) -> None:
        item = _MENU_BY_KEY.get(key)
        if not item:
            return
        t0 = time.perf_counter()
        self.atualizar_menu(key)
        titulo, subtitulo = item["header"]
        self.atualizar_header(titulo, subtitulo)
        self.trocar_frame(item["frame"])
        try:
            logger.info("PERF nav_switch_%s_ms=%.1f", key, (time.perf_counter() - t0) * 1000)
        except Exception:
            pass

    def trocar_frame(self, frame_cls, controller=None):
        if not hasattr(self.app, "content_body") or not self.app.content_body.winfo_exists():
            self.criar_area_conteudo()

        for widget in self.app.content_body.winfo_children():
            widget.destroy()

        if frame_cls is QuadroAvisosFrame:
            frame = frame_cls(self.app.content_body, app=self.app)
        elif controller is not None:
            frame = frame_cls(self.app.content_body, controller)
        else:
            frame = frame_cls(self.app.content_body, self.app)
        frame.pack(fill="both", expand=True)

    def limpar_tela(self):
        for widget in self.app.container.winfo_children():
            widget.destroy()

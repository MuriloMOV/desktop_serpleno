import os
import sys
import time

# Carrega .env da raiz do projeto antes de qualquer import que use os.getenv()
_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_path = os.path.join(_base_dir, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# Logging centralizado (antes de importar módulos que usam logger)
from ser_pleno.utils.logging_config import setup_logging

setup_logging()

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

from ser_pleno.infrastructure.api.connectivity import atualizar_disponibilidade_api_async

from ser_pleno.ui.theme import (
    THEME, SPACING, RADIUS, ELEVATION, font, themed_font,
    get_mode, apply_global_style, toggle_mode, on_theme_change,
)
from ser_pleno.presentation.components.icons import ICONS
from ser_pleno.presentation.components.ui_components import (
    PageHeader,
    SectionHeader,
    Card,
    KPICard,
    PrimaryButton,
    SecondaryButton,
    GhostButton,
    Badge,
    EmptyState,
    Divider,
    blend_color,
    SkeletonLoader,
    Tooltip,
    Avatar,
)

from ser_pleno.presentation.views.login import LoginFrame
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


def _global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger = logging.getLogger("apps.desktop")
    logger.error("Excecao nao tratada", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = _global_exception_handler

try:
    ctk.CTk.report_callback_exception = lambda *args: None
except Exception:
    pass


# Navegação orientada por dados: cada entrada descreve uma tela.
# `key` é usado para destacar o item ativo e para reconstruir a tela certa
# depois de um rebuild (ex.: ao alternar o tema).
MENU_ITEMS = [
    {"key": "dashboard",     "label": "Dashboard",         "icon": ICONS["chart"], "frame": DashboardFrame,
     "header": ("Dashboard", "Resumo geral do ambiente")},
    {"key": "estudantes",    "label": "Estudantes",        "icon": ICONS["users"], "frame": EstudantesFrame,
     "header": ("Estudantes", "Acompanhamento e gestão acadêmica")},
    {"key": "agenda",        "label": "Agenda",            "icon": ICONS["calendar"], "frame": AgendaFrame,
     "header": ("Agenda", "Planejamento e compromissos")},
    {"key": "bem_estar",     "label": "Bem-estar",         "icon": ICONS["heart_blue"], "frame": BemEstarFrame,
     "header": ("Bem-estar", "Monitoramento e apoio emocional")},
    {"key": "analise",       "label": "Análise",           "icon": ICONS["search"], "frame": AnaliseTriagemFrame,
     "header": ("Análise", "Triagem e classificação")},
    {"key": "relatorios",    "label": "Relatórios",        "icon": ICONS["empty"], "frame": RelatorioFrame,
     "header": ("Relatórios", "Indicadores e exportações")},
    {"key": "comunicacao",   "label": "Comunicação",       "icon": ICONS["chat"], "frame": ComunicacaoInternaFrame,
     "header": ("Comunicação", "Mensagens internas e suporte")},
    {"key": "orientacoes",   "label": "Orientações",       "icon": ICONS["compass"], "frame": OrientacoesFrame,
     "header": ("Orientações", "Fluxo de apoio e encaminhamentos")},
    {"key": "avisos",        "label": "Quadro de avisos",  "icon": ICONS["megaphone"], "frame": QuadroAvisosFrame,
     "header": ("Avisos", "Quadro de comunicação institucional")},
    {"key": "configuracoes", "label": "Configurações",     "icon": ICONS["settings"], "frame": ConfiguracoesFrame,
     "header": ("Configurações", "Preferências da aplicação")},
]
_MENU_BY_KEY = {item["key"]: item for item in MENU_ITEMS}

SIDEBAR_WIDTH = 272
PAGE_HEADER_HEIGHT = 86


class App(ctk.CTk):
    def __init__(self):
        self._t_boot = time.perf_counter()
        super().__init__()

        apply_global_style("light")

        self.title("SerPleno")
        self.geometry("1280x720")
        self.minsize(1000, 600)
        self.configure(fg_color=THEME["bg"])

        self.usuario_logado = None
        self.usuario_logado_id = None
        self.menu_buttons = {}
        self._menu_ativo = None
        self._tela_login_ativa_cache = False
        self._tela_login_ativa_cache = False

        self.container = ctk.CTkFrame(self, fg_color=THEME["bg"])
        self.container.pack(fill="both", expand=True)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Permite reconstrução real da UI ao alternar claro/escuro:
        # CustomTkinter não propaga mudanças de cor para widgets já criados,
        # então a forma confiável de "retemar" a tela é reconstruí-la.
        on_theme_change(self._on_theme_changed)

        try:
            atualizar_disponibilidade_api_async()
        except Exception:
            pass

        self.mostrar_login()
        self._t_boot_fim = time.perf_counter()
        try:
            logger.info(
                "PERF boot cold_start_ms=%.1f",
                (self._t_boot_fim - self._t_boot) * 1000,
            )
        except Exception:
            pass

    # ================= LOGIN =================
    def mostrar_login(self):
        self.limpar_tela()
        frame = LoginFrame(self.container, self)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    # ================= SISTEMA =================
    def iniciar_sistema(self, user_data):
        self._t_login_fim = time.perf_counter()
        self.usuario_logado = user_data
        self.usuario_logado_id = user_data["id"]
        self.limpar_tela()

        self._controllers = {}
        self._t_controllers_start = time.perf_counter()
        # Nenhum controller instanciado ainda — lazy-load na primeira navegação.
        self._t_controllers_end = time.perf_counter()

        self._t_ui_start = time.perf_counter()
        self.criar_sidebar()
        self.criar_area_conteudo()
        self.mostrar_dashboard()
        self._t_ui_end = time.perf_counter()
        try:
            logger.info(
                "PERF login_flow_ms=%.1f controllers_ms=%.1f ui_build_ms=%.1f",
                (self._t_login_fim - self._t_boot_fim) * 1000,
                (self._t_controllers_end - self._t_controllers_start) * 1000,
                (self._t_ui_end - self._t_ui_start) * 1000,
            )
        except Exception:
            pass

    # ================= TEMA =================
    def _on_theme_changed(self, mode: str) -> None:
        """Reconstrói a interface autenticada com as cores do novo tema.
        Chamado automaticamente por ui_theme.set_mode()/toggle_mode()."""
        if not self.winfo_exists():
            return
        self.configure(fg_color=THEME["bg"])
        if hasattr(self, "container") and self.container.winfo_exists():
            self.container.configure(fg_color=THEME["bg"])

        if not self.usuario_logado:
            # Ainda na tela de login: apenas recria para herdar as cores novas.
            if self._tela_login_ativa():
                self.mostrar_login()
            return

        tela_anterior = self._menu_ativo or "dashboard"
        self.limpar_tela()
        self.criar_sidebar()
        self.criar_area_conteudo()
        self._mostrar_por_key(tela_anterior)

    def _tela_login_ativa(self) -> bool:
        return not hasattr(self, "sidebar") or not self.sidebar.winfo_exists()

    def alternar_tema(self):
        # _on_theme_changed cuida da reconstrução automaticamente.
        toggle_mode()

    # ================= SIDEBAR =================
    def criar_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.container,
            width=SIDEBAR_WIDTH,
            fg_color=THEME["nav_bg"],
            corner_radius=0,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)

        self._criar_marca()
        Divider(self.sidebar).pack(fill="x", padx=18, pady=(6, 16))

        menu_label = ctk.CTkLabel(
            self.sidebar,
            text="NAVEGAÇAO",
            font=font(11, "bold"),
            text_color=THEME["text_muted"],
        )
        menu_label.pack(anchor="w", padx=22, pady=(4, 10))

        self.menu_container = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=THEME["nav_bg"],
            scrollbar_button_hover_color=THEME["border_strong"],
        )
        self.menu_container.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        self._criar_menu()
        self._criar_rodape_sidebar()

    def _criar_marca(self):
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
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
            text="Gestão escolar e bem-estar",
            font=font(11),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

    def _criar_rodape_sidebar(self):
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(12, 18), side="bottom")

        nome = self.usuario_logado.get("first_name") or self.usuario_logado.get("username", "usuário")
        iniciais = "".join(p[0] for p in nome.split()[:2]).upper() or "U"

        self.user_chip = ctk.CTkFrame(footer, fg_color=THEME["primary_soft"], corner_radius=14)
        self.user_chip.pack(fill="x", pady=(0, 10))

        chip_inner = ctk.CTkFrame(self.user_chip, fg_color="transparent")
        chip_inner.pack(fill="x", padx=12, pady=10)

        Avatar(chip_inner, initials=iniciais, size=36, color=THEME["primary"]).pack(side="left", padx=(0, 10))

        texto_frame = ctk.CTkFrame(chip_inner, fg_color="transparent")
        texto_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            texto_frame,
            text=f"Olá, {nome}",
            font=font(12, "bold"),
            text_color=THEME["primary"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            texto_frame,
            text="Psicóloga(o) escolar",
            font=font(10),
            text_color=THEME["text_muted"],
            anchor="w",
        ).pack(fill="x")

        modo_atual = get_mode()
        rotulo = f"{ICONS['moon']}  Modo escuro" if modo_atual == "light" else f"{ICONS['sun']}  Modo claro"
        self.theme_toggle_btn = ctk.CTkButton(
            footer,
            text=rotulo,
            command=self.alternar_tema,
            height=40,
            corner_radius=10,
            fg_color=THEME["surface"],
            hover_color=THEME["nav_hover"],
            text_color=THEME["text"],
            border_width=1,
            border_color=THEME["border"],
            cursor="hand2",
        )
        self.theme_toggle_btn.pack(fill="x")

    def _criar_menu(self):
        self.menu_buttons = {}
        for item in MENU_ITEMS:
            self._criar_botao_menu(item)

    def _criar_botao_menu(self, item: dict) -> None:
        key = item["key"]
        item_frame = ctk.CTkFrame(self.menu_container, fg_color="transparent")
        item_frame.pack(fill="x", padx=6, pady=3)

        indicator = ctk.CTkFrame(item_frame, width=4, height=36, corner_radius=999, fg_color="transparent")
        indicator.pack(side="left", fill="y", padx=(2, 8))

        btn = GhostButton(
            item_frame,
            text=item["label"],
            icon=item["icon"],
            command=lambda k=key: self._mostrar_por_key(k),
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

    # ================= ÁREA DE CONTEÚDO =================
    def criar_area_conteudo(self):
        self.content = ctk.CTkFrame(self.container, fg_color=THEME["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.content, fg_color="transparent", height=PAGE_HEADER_HEIGHT)
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 8))
        header.grid_columnconfigure(0, weight=1)

        self.header_title = ctk.CTkLabel(
            header,
            text="Dashboard",
            font=font(24, "bold"),
            text_color=THEME["text"],
            anchor="w",
        )
        self.header_title.grid(row=0, column=0, sticky="w")

        self.header_subtitle = ctk.CTkLabel(
            header,
            text="Resumo geral do ambiente",
            font=font(12),
            text_color=THEME["text_secondary"],
            anchor="w",
        )
        self.header_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.content_body = ctk.CTkFrame(self.content, fg_color="transparent")
        self.content_body.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))

    # ================= NAVEGAÇAO =================
    def atualizar_menu(self, active_key: str) -> None:
        self._menu_ativo = active_key
        for key in self.menu_buttons:
            self._aplicar_estilo_botao_menu(key, key == active_key)

    def atualizar_header(self, title: str, subtitle: str) -> None:
        if hasattr(self, "header_title") and self.header_title.winfo_exists():
            self.header_title.configure(text=title)
        if hasattr(self, "header_subtitle") and self.header_subtitle.winfo_exists():
            self.header_subtitle.configure(text=subtitle)

    def _mostrar_por_key(self, key: str) -> None:
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

    # Mantidos como métodos nomeados por compatibilidade com o restante do
    # sistema e por clareza de leitura (ex.: chamadas vindas de outras views).
    def mostrar_dashboard(self):
        self._mostrar_por_key("dashboard")

    def mostrar_estudantes(self):
        self._mostrar_por_key("estudantes")

    def mostrar_agenda(self):
        self._mostrar_por_key("agenda")

    def mostrar_bem_estar(self):
        self._mostrar_por_key("bem_estar")

    def mostrar_analise_triagem(self):
        self._mostrar_por_key("analise")

    def mostrar_relatorio(self):
        self._mostrar_por_key("relatorios")

    def mostrar_comunicacao_interna(self):
        self._mostrar_por_key("comunicacao")

    def mostrar_orientacoes(self):
        self._mostrar_por_key("orientacoes")

    def mostrar_quadro_avisos(self):
        self._mostrar_por_key("avisos")

    def mostrar_configuracoes(self):
        self._mostrar_por_key("configuracoes")

    def trocar_frame(self, frame_cls, controller=None):
        if not hasattr(self, "content_body") or not self.content_body.winfo_exists():
            self.criar_area_conteudo()

        for widget in self.content_body.winfo_children():
            widget.destroy()

        if frame_cls is QuadroAvisosFrame:
            frame = frame_cls(self.content_body, app=self)
        elif controller is not None:
            frame = frame_cls(self.content_body, controller)
        else:
            frame = frame_cls(self.content_body, self)
        frame.pack(fill="both", expand=True)

    def limpar_tela(self):
        for widget in self.container.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    App().mainloop()


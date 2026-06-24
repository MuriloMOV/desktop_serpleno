import customtkinter as ctk

from services.connectivity import atualizar_disponibilidade_api_async

from ui_theme import THEME, SPACING, RADIUS, ELEVATION, font, themed_font, get_mode, apply_global_style, toggle_mode
from components.ui_components import (
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
)

from controllers.dashboard import DashboardController
from controllers.estudantes import EstudantesController
from controllers.bem_estar import BemEstarController
from controllers.configuracoes import ConfiguracoesController
from controllers.analise_triagem import AnaliseTriagemController
from views.login import LoginFrame
from views.dashboard import DashboardFrame
from views.estudantes import EstudantesFrame
from views.agenda import AgendaFrame
from views.bem_estar import BemEstarFrame
from views.analise_triagem import AnaliseTriagemFrame
from views.relatorio import RelatorioFrame
from views.comunicacao_interna import ComunicacaoInternaFrame
from views.orientacoes import OrientacoesFrame
from views.quadro_avisos import QuadroAvisosFrame
from views.configuracoes import ConfiguracoesFrame


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        apply_global_style("light")

        self.title("SerPleno")
        self.geometry("1280x720")
        self.minsize(800, 480)
        self.configure(fg_color=THEME["bg"])

        self.usuario_logado = None
        self.usuario_logado_id = None
        self.menu_buttons = {}
        self._menu_ativo = None

        self.container = ctk.CTkFrame(self, fg_color=THEME["bg"])
        self.container.pack(fill="both", expand=True)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        try:
            atualizar_disponibilidade_api_async()
        except Exception:
            pass

        self.mostrar_login()

    # ================= LOGIN =================
    def mostrar_login(self):
        self.limpar_tela()
        frame = LoginFrame(self.container, self)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    # ================= SISTEMA =================
    def iniciar_sistema(self, user_data):
        self.usuario_logado = user_data
        self.usuario_logado_id = user_data["id"]
        self.limpar_tela()

        self.dashboard_controller = DashboardController()
        self.estudantes_controller = EstudantesController()
        self.bem_estar_controller = BemEstarController()
        self.configuracoes_controller = ConfiguracoesController()
        self.analise_triagem_controller = AnaliseTriagemController()

        self.criar_sidebar()
        self.criar_area_conteudo()
        self.mostrar_dashboard()

    def criar_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.container,
            width=272,
            fg_color=THEME["nav_bg"],
            corner_radius=0,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        self.sidebar.pack_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(pady=(24, 16), padx=20, fill="x")

        icon_lbl = ctk.CTkLabel(
            brand_frame,
            text="🧠",
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

        Divider(self.sidebar).pack(fill="x", padx=18, pady=(6, 16))

        menu_label = ctk.CTkLabel(
            self.sidebar,
            text="NAVEGAÇÃO",
            font=font(11, "bold"),
            text_color=THEME["text_muted"],
        )
        menu_label.pack(anchor="w", padx=22, pady=(4, 10))

        self.menu_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.menu_container.pack(fill="x", padx=10, pady=(0, 8))

        self._criar_menu()

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(12, 18), side="bottom")

        self.user_chip = ctk.CTkFrame(footer, fg_color=THEME["primary_soft"], corner_radius=14)
        self.user_chip.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            self.user_chip,
            text=f"Olá, {self.usuario_logado.get('first_name', self.usuario_logado.get('username', 'usuário'))}",
            font=font(12, "bold"),
            text_color=THEME["primary"],
        ).pack(padx=14, pady=10, anchor="w")

        self.theme_toggle_btn = ctk.CTkButton(
            footer,
            text="🌓  Tema claro",
            command=self.alternar_tema,
            height=40,
            corner_radius=10,
            fg_color=THEME["surface"],
            hover_color=THEME["nav_hover"],
            text_color=THEME["text"],
            border_width=1,
            border_color=THEME["border"],
        )
        self.theme_toggle_btn.pack(fill="x")

    def _criar_menu(self):
        self.menu_buttons = {}
        self._menu_ativo = None

        menu_items = [
            ("dashboard", "Dashboard", self.mostrar_dashboard, True),
            ("estudantes", "Estudantes", self.mostrar_estudantes, False),
            ("agenda", "Agenda", self.mostrar_agenda, False),
            ("bem_estar", "Bem-estar", self.mostrar_bem_estar, False),
            ("analise", "Análise", self.mostrar_analise_triagem, False),
            ("relatorios", "Relatórios", self.mostrar_relatorio, False),
            ("comunicacao", "Comunicação", self.mostrar_comunicacao_interna, False),
            ("orientacoes", "Orientações", self.mostrar_orientacoes, False),
            ("avisos", "Quadro de avisos", self.mostrar_quadro_avisos, False),
            ("configuracoes", "Configurações", self.mostrar_configuracoes, False),
        ]

        for key, label, target, active in menu_items:
            self._criar_botao_menu(key, label, target, active)

    def _criar_botao_menu(self, key: str, label: str, target, active: bool = False) -> None:
        item_frame = ctk.CTkFrame(self.menu_container, fg_color="transparent")
        item_frame.pack(fill="x", padx=8, pady=3)

        indicator = ctk.CTkFrame(item_frame, width=5, height=38, corner_radius=999, fg_color="transparent")
        indicator.pack(side="left", fill="y", padx=(4, 8))

        btn = GhostButton(
            item_frame,
            text=label,
            command=target,
            width=220,
            height=40,
            corner_radius=10,
        )
        btn.pack(side="left", fill="x", expand=True)

        if active:
            self._menu_ativo = key

        self.menu_buttons[key] = {"frame": item_frame, "indicator": indicator, "btn": btn}
        self._aplicar_estilo_botao_menu(key, active)

    def _aplicar_estilo_botao_menu(self, key: str, active: bool = False) -> None:
        data = self.menu_buttons.get(key)
        if not data:
            return

        btn = data["btn"]
        indicator = data["indicator"]
        is_active = key == getattr(self, "_menu_ativo", None) or active

        if is_active:
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

    def alternar_tema(self):
        novo_modo = toggle_mode()
        rotulo = "🌓  Tema claro" if novo_modo == "light" else "🌓  Tema escuro"
        if hasattr(self, "theme_toggle_btn") and self.theme_toggle_btn.winfo_exists():
            self.theme_toggle_btn.configure(text=rotulo)
        self.atualizar_tema_widgets()

    def atualizar_tema_widgets(self):
        if hasattr(self, "container") and self.container.winfo_exists():
            self.container.configure(fg_color=THEME["bg"])
        if hasattr(self, "sidebar") and self.sidebar.winfo_exists():
            self.sidebar.configure(fg_color=THEME["nav_bg"])
        if hasattr(self, "content") and self.content.winfo_exists():
            self.content.configure(fg_color=THEME["bg"])
        if hasattr(self, "content_body") and self.content_body.winfo_exists():
            self.content_body.configure(fg_color="transparent")
        for widget in self.winfo_children():
            if hasattr(widget, "configure") and callable(getattr(widget, "configure")):
                try:
                    widget.configure()
                except Exception:
                    pass

    def criar_area_conteudo(self):
        self.content = ctk.CTkFrame(self.container, fg_color=THEME["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.content, fg_color="transparent", height=86)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
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
        self.content_body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))

    # ================= NAVEGAÇÃO =================
    def atualizar_menu(self, active_key: str) -> None:
        self._menu_ativo = active_key
        for key, data in self.menu_buttons.items():
            self._aplicar_estilo_botao_menu(key, key == active_key)

    def atualizar_header(self, title: str, subtitle: str) -> None:
        if hasattr(self, "header_title") and self.header_title.winfo_exists():
            self.header_title.configure(text=title)
        if hasattr(self, "header_subtitle") and self.header_subtitle.winfo_exists():
            self.header_subtitle.configure(text=subtitle)

    def mostrar_dashboard(self):
        self.atualizar_menu("dashboard")
        self.atualizar_header("Dashboard", "Resumo geral do ambiente")
        self.trocar_frame(DashboardFrame)

    def mostrar_estudantes(self):
        self.atualizar_menu("estudantes")
        self.atualizar_header("Estudantes", "Acompanhamento e gestão acadêmica")
        self.trocar_frame(EstudantesFrame)

    def mostrar_agenda(self):
        self.atualizar_menu("agenda")
        self.atualizar_header("Agenda", "Planejamento e compromissos")
        self.trocar_frame(AgendaFrame)

    def mostrar_bem_estar(self):
        self.atualizar_menu("bem_estar")
        self.atualizar_header("Bem-estar", "Monitoramento e apoio emocional")
        self.trocar_frame(BemEstarFrame)

    def mostrar_analise_triagem(self):
        self.atualizar_menu("analise")
        self.atualizar_header("Análise", "Triagem e classificação")
        self.trocar_frame(AnaliseTriagemFrame)

    def mostrar_relatorio(self):
        self.atualizar_menu("relatorios")
        self.atualizar_header("Relatórios", "Indicadores e exportações")
        self.trocar_frame(RelatorioFrame)

    def mostrar_comunicacao_interna(self):
        self.atualizar_menu("comunicacao")
        self.atualizar_header("Comunicação", "Mensagens internas e suporte")
        self.trocar_frame(ComunicacaoInternaFrame)

    def mostrar_orientacoes(self):
        self.atualizar_menu("orientacoes")
        self.atualizar_header("Orientações", "Fluxo de apoio e encaminhamentos")
        self.trocar_frame(OrientacoesFrame)

    def mostrar_quadro_avisos(self):
        self.atualizar_menu("avisos")
        self.atualizar_header("Avisos", "Quadro de comunicação institucional")
        self.trocar_frame(QuadroAvisosFrame)

    def mostrar_configuracoes(self):
        self.atualizar_menu("configuracoes")
        self.atualizar_header("Configurações", "Preferências da aplicação")
        self.trocar_frame(ConfiguracoesFrame)

    def trocar_frame(self, frame_cls, controller=None):
        if not hasattr(self, "content_body") or not self.content_body.winfo_exists():
            self.criar_area_conteudo()

        for widget in self.content_body.winfo_children():
            widget.destroy()

        if frame_cls is QuadroAvisosFrame:
            frame = frame_cls(self.content_body, app=self)
        elif controller is not None:
            frame = frame_cls(self.content_body, self, controller=controller)
        else:
            frame = frame_cls(self.content_body, self)
        frame.pack(fill="both", expand=True)

    def limpar_tela(self):
        for widget in self.container.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    App().mainloop()

import customtkinter as ctk

from services.connectivity import atualizar_disponibilidade_api_async

from ui_theme import THEME, SPACING, RADIUS, ELEVATION, font, themed_font
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

        ctk.set_appearance_mode("light")

        self.title("SerPleno")
        self.geometry("1280x720")
        self.minsize(800, 480)
        self.configure(fg_color=THEME["bg"])

        self.usuario_logado = None  # Armazena os dados do usuário logados
        self.usuario_logado_id = None

        self.container = ctk.CTkFrame(self, fg_color=THEME["bg"])
        self.container.pack(fill="both", expand=True)

        # Verifica disponibilidade da API de forma não-bloqueante
        try:
            atualizar_disponibilidade_api_async()
        except Exception:
            pass

        self.mostrar_login()

    # ================= LOGIN =================
    def mostrar_login(self):
        self.limpar_tela()
        frame = LoginFrame(self.container, self)
        frame.pack(fill="both", expand=True)

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
            width=260,
            fg_color=THEME["nav_bg"],
            corner_radius=0,
            border_width=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(pady=(28, 24), padx=22, fill="x")

        icon_lbl = ctk.CTkLabel(
            brand_frame,
            text="🧠",
            font=font(22, "bold"),
            text_color=THEME["brand_accent"],
        )
        icon_lbl.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            brand_frame,
            text="SerPleno",
            font=font(20, "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        Divider(self.sidebar).pack(fill="x", padx=18, pady=(0, 14))

        # ===== MENU =====
        self.menu_buttons = {}

        def add_menu(key: str, label: str, target, active: bool = False) -> None:
            btn = GhostButton(
                self.sidebar,
                text=label,
                command=target,
                width=220,
                height=42,
            )
            btn.pack(fill="x", padx=14, pady=4)
            if active:
                btn.configure(
                    fg_color=THEME["nav_active_bg"],
                    hover_color=THEME["nav_active_bg"],
                    text_color=THEME["nav_active_text"],
                    border_color=THEME["nav_active_text"],
                    border_width=1,
                )
            self.menu_buttons[key] = btn

        add_menu("dashboard", "🏠  Início", self.mostrar_dashboard, active=True)
        add_menu("estudantes", "👥  Estudantes", self.mostrar_estudantes)
        add_menu("agenda", "📅  Agenda", self.mostrar_agenda)
        add_menu("bem_estar", "🧡  Bem-Estar", self.mostrar_bem_estar)
        add_menu("analise", "📈  Análise de Triagem", self.mostrar_analise_triagem)
        add_menu("relatorios", "📋  Relatórios", self.mostrar_relatorio)
        add_menu(
            "comunicacao", "💬  Comunicação Interna", self.mostrar_comunicacao_interna
        )
        add_menu("orientacoes", "🧭  Orientações", self.mostrar_orientacoes)
        add_menu("avisos", "📢  Quadro de Avisos", self.mostrar_quadro_avisos)
        add_menu("configuracoes", "⚙  Configurações", self.mostrar_configuracoes)

    def criar_area_conteudo(self):
        self.content = ctk.CTkFrame(self.container, fg_color=THEME["bg"])
        self.content.pack(side="left", fill="both", expand=True)

    # ================= NAVEGAÇÃO =================
    def atualizar_menu(self, active_key: str) -> None:
        for key, btn in self.menu_buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=THEME["nav_active_bg"],
                    hover_color=THEME["nav_active_bg"],
                    text_color=THEME["nav_active_text"],
                    border_color=THEME["nav_active_text"],
                    border_width=1,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=THEME["nav_hover"],
                    text_color=THEME["nav_text"],
                    border_width=0,
                )

    def mostrar_dashboard(self):
        self.atualizar_menu("dashboard")
        self.trocar_frame(DashboardFrame, self.dashboard_controller)

    def mostrar_estudantes(self):
        self.atualizar_menu("estudantes")
        self.trocar_frame(EstudantesFrame, self.estudantes_controller)

    def mostrar_agenda(self):
        self.atualizar_menu("agenda")
        self.trocar_frame(AgendaFrame)

    def mostrar_bem_estar(self):
        self.atualizar_menu("bem_estar")
        self.trocar_frame(BemEstarFrame, self.bem_estar_controller)

    def mostrar_analise_triagem(self):
        self.atualizar_menu("analise")
        self.trocar_frame(AnaliseTriagemFrame)

    def mostrar_relatorio(self):
        self.atualizar_menu("relatorios")
        self.trocar_frame(RelatorioFrame)

    def mostrar_comunicacao_interna(self):
        self.atualizar_menu("comunicacao")
        self.trocar_frame(ComunicacaoInternaFrame)

    def mostrar_orientacoes(self):
        self.atualizar_menu("orientacoes")
        self.trocar_frame(OrientacoesFrame)

    def mostrar_quadro_avisos(self):
        self.atualizar_menu("avisos")
        self.trocar_frame(QuadroAvisosFrame)

    def mostrar_configuracoes(self):
        self.atualizar_menu("configuracoes")
        self.trocar_frame(ConfiguracoesFrame, self.configuracoes_controller)

    def trocar_frame(self, frame_cls, controller=None):
        for widget in self.content.winfo_children():
            widget.destroy()

        frame = frame_cls(self.content, self, controller=controller)
        frame.pack(fill="both", expand=True)

    def limpar_tela(self):
        for widget in self.container.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    App().mainloop()

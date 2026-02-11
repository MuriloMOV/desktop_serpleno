import customtkinter as ctk

from ui_theme import THEME, SPACING, RADIUS, font

from views.dashboard import DashboardFrame
from views.estudantes import EstudantesFrame
from views.agenda import AgendaFrame
from views.login import LoginFrame
from views.analise_triagem import AnaliseTriagemFrame
from views.comunicacao_interna import ComunicacaoInternaFrame
from views.orientacoes import OrientacoesFrame
from views.quadro_avisos import QuadroAvisosFrame
from views.configuracoes import ConfiguracoesFrame
from views.relatorio import RelatorioFrame
from views.bem_estar import BemEstarFrame

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("light")

        self.title("SerPleno")
        self.geometry("1280x720")
        self.minsize(800, 480)
        self.configure(fg_color=THEME["bg"])

        self.usuario_logado = None  # Armazena os dados do usuário logado
        self.usuario_logado_id = None

        self.container = ctk.CTkFrame(self, fg_color=THEME["bg"])
        self.container.pack(fill="both", expand=True)

        self.mostrar_login()

    # ================= LOGIN =================
    def mostrar_login(self):
        self.limpar_tela()
        frame = LoginFrame(self.container, self)
        frame.pack(fill="both", expand=True)

    # ================= SISTEMA =================
    def iniciar_sistema(self, user_data):
        self.usuario_logado = user_data
        self.usuario_logado_id = user_data['id']
        self.limpar_tela()

        self.criar_sidebar()
        self.criar_area_conteudo()

        self.mostrar_dashboard()

    def criar_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.container,
            width=240,
            fg_color=THEME["nav_bg"],
            corner_radius=0,
            border_width=1,
            border_color=THEME["border"]
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(pady=(28, 18), padx=22, fill="x")

        ctk.CTkLabel(
            brand_frame,
            text="🧠",
            font=font(22, "bold"),
            text_color=THEME["brand_accent"]
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            brand_frame,
            text="SerPleno",
            font=font(20, "bold"),
            text_color=THEME["text"]
        ).pack(side="left")

        divider = ctk.CTkFrame(self.sidebar, height=1, fg_color=THEME["border"])
        divider.pack(fill="x", padx=18, pady=(0, 14))


        # ===== MENU =====
        self.menu_buttons = {}
        self.menu_buttons["dashboard"] = self.botao_sidebar("🏠  Início", self.mostrar_dashboard, active=True)
        self.menu_buttons["estudantes"] = self.botao_sidebar("👥  Estudantes", self.mostrar_estudantes)
        self.menu_buttons["agenda"] = self.botao_sidebar("📅  Agenda", self.mostrar_agenda)
        self.menu_buttons["bem_estar"] = self.botao_sidebar("🧡  Bem-Estar", self.mostrar_bem_estar)
        self.menu_buttons["analise"] = self.botao_sidebar("📈  Análise de Triagem", self.mostrar_analise_triagem)
        self.menu_buttons["relatorios"] = self.botao_sidebar("📋  Relatórios", self.mostrar_relatorio)
        self.menu_buttons["comunicacao"] = self.botao_sidebar("💬  Comunicação Interna", self.mostrar_comunicacao_interna)
        self.menu_buttons["orientacoes"] = self.botao_sidebar("🧡  Orientações", self.mostrar_orientacoes)
        self.menu_buttons["avisos"] = self.botao_sidebar("📢  Quadro de Avisos", self.mostrar_quadro_avisos)
        self.menu_buttons["configuracoes"] = self.botao_sidebar("⚙  Configurações", self.mostrar_configuracoes)

    def botao_sidebar(self, texto, comando=None, active=False):
        btn = ctk.CTkButton(
            self.sidebar,
            text=texto,
            height=42,
            fg_color=THEME["nav_active_bg"] if active else "transparent",
            text_color=THEME["nav_active_text"] if active else THEME["nav_text"],
            hover_color=THEME["nav_hover"],
            corner_radius=RADIUS["button"],
            font=font(14, "bold" if active else "normal"),
            anchor="w",
            command=comando
        )
        btn.pack(fill="x", padx=14, pady=4)
        return btn


    def criar_area_conteudo(self):
        self.content = ctk.CTkFrame(self.container, fg_color=THEME["bg"])
        self.content.pack(side="left", fill="both", expand=True)

    # ================= NAVEGAÇÃO =================
    def atualizar_menu(self, active_key):
        for key, btn in self.menu_buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=THEME["nav_active_bg"],
                    text_color=THEME["nav_active_text"],
                    font=font(14, "bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=THEME["nav_text"],
                    font=font(14, "normal")
                )

    def mostrar_dashboard(self):
        self.atualizar_menu("dashboard")
        self.trocar_frame(DashboardFrame)

    def mostrar_estudantes(self):
        self.atualizar_menu("estudantes")
        self.trocar_frame(EstudantesFrame)

    def mostrar_agenda(self):
        self.atualizar_menu("agenda")
        self.trocar_frame(AgendaFrame)

    def mostrar_bem_estar(self):
        self.atualizar_menu("bem_estar")
        self.trocar_frame(BemEstarFrame)

    def mostrar_analise_triagem(self):
        self.atualizar_menu("analise")
        self.trocar_frame(AnaliseTriagemFrame)

    def mostrar_relatorio(self):
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

    def mostrar_relatorio(self):
        self.atualizar_menu("relatorios")
        self.trocar_frame(RelatorioFrame)

    def mostrar_configuracoes(self):
        self.atualizar_menu("configuracoes")
        self.trocar_frame(ConfiguracoesFrame)


    def trocar_frame(self, FrameClasse):
        for widget in self.content.winfo_children():
            widget.destroy()

        frame = FrameClasse(self.content, self)
        frame.pack(fill="both", expand=True)

    def limpar_tela(self):
        for widget in self.container.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    App().mainloop()
import customtkinter as ctk

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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SerPleno")
        self.geometry("1300x750")
        self.configure(fg_color="#f4f6fb")

        self.usuario_logado = False

        self.container = ctk.CTkFrame(self, fg_color="#f4f6fb")
        self.container.pack(fill="both", expand=True)

        self.mostrar_login()

    # ================= LOGIN =================
    def mostrar_login(self):
        self.limpar_tela()
        frame = LoginFrame(self.container, self)
        frame.pack(fill="both", expand=True)

    # ================= SISTEMA =================
    def iniciar_sistema(self):
        self.usuario_logado = True
        self.limpar_tela()

        self.criar_sidebar()
        self.criar_area_conteudo()

        self.mostrar_dashboard()

    def criar_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.container, width=220, fg_color="white")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(pady=(30, 40), padx=20, fill="x")

        ctk.CTkLabel(
            brand_frame,
            text="🧬", # Brain/DNA-like icon
            font=ctk.CTkFont(size=24),
            text_color="#6366f1"
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            brand_frame,
            text="SerPleno",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#1e1b4b" # Dark Indigo
        ).pack(side="left")


        # ===== MENU =====
        self.menu_buttons = {}
        self.menu_buttons["dashboard"] = self.botao_sidebar("🏠  Início", self.mostrar_dashboard, active=True)
        self.menu_buttons["estudantes"] = self.botao_sidebar("👥  Estudantes", self.mostrar_estudantes)
        self.menu_buttons["agenda"] = self.botao_sidebar("📅  Agenda", self.mostrar_agenda)
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
            height=45,
            fg_color="#4f46e5" if active else "transparent",
            text_color="white" if active else "#4b5563",
            hover_color="#f3f4f6" if not active else "#4338ca",
            corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold" if active else "normal"),
            anchor="w",
            command=comando
        )
        btn.pack(fill="x", padx=15, pady=4)
        return btn


    def criar_area_conteudo(self):
        self.content = ctk.CTkFrame(self.container, fg_color="#f4f6fb")
        self.content.pack(side="left", fill="both", expand=True)

    # ================= NAVEGAÇÃO =================
    def atualizar_menu(self, active_key):
        for key, btn in self.menu_buttons.items():
            if key == active_key:
                btn.configure(fg_color="#4f46e5", text_color="white", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color="#4b5563", font=ctk.CTkFont(family="Segoe UI", size=14, weight="normal"))

    def mostrar_dashboard(self):
        self.atualizar_menu("dashboard")
        self.trocar_frame(DashboardFrame)

    def mostrar_estudantes(self):
        self.atualizar_menu("estudantes")
        self.trocar_frame(EstudantesFrame)

    def mostrar_agenda(self):
        self.atualizar_menu("agenda")
        self.trocar_frame(AgendaFrame)

    def mostrar_analise_triagem(self):
        self.atualizar_menu("analise")
        self.trocar_frame(AnaliseTriagemFrame)

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
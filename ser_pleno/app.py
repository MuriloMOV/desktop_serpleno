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

        ctk.CTkLabel(
            self.sidebar,
            text="SerPleno",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#111827"
        ).pack(pady=(30, 40))

        # ===== MENU =====
        self.botao_sidebar("Início", self.mostrar_dashboard)
        self.botao_sidebar("Estudantes", self.mostrar_estudantes)
        self.botao_sidebar("Agenda", self.mostrar_agenda)
        self.botao_sidebar("Análise de Triagem", self.mostrar_analise_triagem)

        self.botao_sidebar("Relatórios", self.mostrar_relatorio)
        self.botao_sidebar("Comunicação Interna", self.mostrar_comunicacao_interna)
        self.botao_sidebar("Orientações", self.mostrar_orientacoes)
        self.botao_sidebar("Quadro de Avisos", self.mostrar_quadro_avisos)
        self.botao_sidebar("Configurações", self.mostrar_configuracoes)
    def botao_sidebar(self, texto, comando=None):
        ctk.CTkButton(
            self.sidebar,
            text=texto,
            height=40,
            fg_color="#e5e7eb",
            text_color="#111827",
            hover_color="#6d28d9",
            corner_radius=8,
            command=comando
        ).pack(fill="x", padx=20, pady=6)

    def criar_area_conteudo(self):
        self.content = ctk.CTkFrame(self.container, fg_color="#f4f6fb")
        self.content.pack(side="left", fill="both", expand=True)

    # ================= NAVEGAÇÃO =================
    def mostrar_dashboard(self):
        self.trocar_frame(DashboardFrame)

    def mostrar_estudantes(self):
        self.trocar_frame(EstudantesFrame)

    def mostrar_agenda(self):
        self.trocar_frame(AgendaFrame)

    def mostrar_analise_triagem(self):
        self.trocar_frame(AnaliseTriagemFrame)

    def mostrar_relatorio(self):
        self.trocar_frame(RelatorioFrame)
    
    def mostrar_comunicacao_interna(self):
        self.trocar_frame(ComunicacaoInternaFrame)
    
    def mostrar_orientacoes(self):
        self.trocar_frame(OrientacoesFrame)
    
    def mostrar_quadro_avisos(self):
        self.trocar_frame(QuadroAvisosFrame)

    def mostrar_configuracoes(self):
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
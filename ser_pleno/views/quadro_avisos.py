import customtkinter as ctk
from services.mural import ServicoMural
# Compat alias para testes
BoardService = ServicoMural
import threading
from datetime import datetime
import webbrowser
import os
from datetime import datetime

from ui_theme import THEME, SPACING, RADIUS, font

class QuadroAvisosFrame(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="#f4f6fb")
        self.app = app

        self.publicacoes = [
            {
                "titulo": "Semana de acolhimento emocional",
                "descricao": "Durante esta semana estaremos oferecendo atendimentos especiais de escuta ativa para alunos que se sentirem sobrecarregados emocionalmente.",
                "autor": "Psicologia Escolar",
                "data": "29/01/2026",
                "status": "Rascunho"
            },
            {
                "titulo": "Mudança no horário de atendimento",
                "descricao": "A partir do próximo mês o atendimento psicológico ocorrerá das 09h às 17h.",
                "autor": "Coordenação",
                "data": "27/01/2026",
                "status": "Rascunho"
            }
        ]

        self._layout()
        self._header()
        self._lista_publicacoes()

    # ================= BASE =================
    def _layout(self):
        self.pack(fill="both", expand=True)

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=30, pady=30)

    # ================= HEADER =================
    def _header(self):
        header = ctk.CTkFrame(self.container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header,
            text="Quadro de Avisos",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#111827"
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Nova publicação",
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            text_color="white",
            height=42,
            corner_radius=8,
            command=self.abrir_modal
        ).pack(side="right")

    # ================= LISTA =================
    def _lista_publicacoes(self):
        self.lista = ctk.CTkFrame(self.container, fg_color="transparent")
        self.lista.pack(fill="both", expand=True)

        for pub in self.publicacoes:
            self._card_publicacao(pub)

    def _card_publicacao(self, pub):
        card = ctk.CTkFrame(self.lista, fg_color="white", corner_radius=14)
        card.pack(fill="x", pady=10)

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=(15, 5))

    def criar_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 8))
        
        ctk.CTkLabel(
            topo,
            text=pub["titulo"],
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#111827"
        ).pack(side="left")

        ctk.CTkLabel(
            card,
            text=pub["descricao"],
            wraplength=900,
            justify="left",
            text_color="#374151"
        ).pack(anchor="w", padx=20, pady=10)

        rodape = ctk.CTkFrame(card, fg_color="transparent")
        rodape.pack(fill="x", padx=20, pady=(0, 15))

        ctk.CTkLabel(
            rodape,
            text=f"{pub['autor']} • {pub['data']}",
            font=ctk.CTkFont(size=12),
            text_color="#6b7280"
        ).pack(side="left")

        ctk.CTkButton(
            rodape,
            text="Editar",
            width=80,
            fg_color="#e5e7eb",
            text_color="#111827",
            hover_color="#d1d5db"
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            rodape,
            text="Excluir",
            width=80,
            fg_color="#fee2e2",
            text_color="#991b1b",
            hover_color="#fecaca"
        ).pack(side="right")

    # ================= MODAL =================
    def abrir_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Nova publicação")
        modal.geometry("640x620")
        modal.resizable(False, False)
        modal.grab_set()

        modal.update_idletasks()
        x = (modal.winfo_screenwidth() // 2) - (640 // 2)
        y = (modal.winfo_screenheight() // 2) - (620 // 2)
        modal.geometry(f"+{x}+{y}")

        box = ctk.CTkFrame(modal, fg_color="white", corner_radius=18)
        box.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkFrame(box, fg_color="#6d28d9", height=64, corner_radius=16)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="📝  Nova publicação",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20)

        ctk.CTkButton(
            header,
            text="✕",
            width=36,
            height=36,
            fg_color="#5b21b6",
            hover_color="#4c1d95",
            corner_radius=18,
            command=modal.destroy
        ).pack(side="right", padx=16)

        content = ctk.CTkFrame(box, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=25)

        def label(text):
            return ctk.CTkLabel(
                content,
                text=text,
                text_color="#6b7280",
                font=ctk.CTkFont(size=12, weight="bold")
            )

        entry_style = {
            "height": 40,
            "fg_color": "#f9fafb",
            "border_color": "#e5e7eb",
            "border_width": 1
        }

        label("Título").pack(anchor="w")
        ctk.CTkEntry(content, placeholder_text="Digite o título do aviso", **entry_style)\
            .pack(fill="x", pady=(6, 16))

        label("Descrição").pack(anchor="w")
        ctk.CTkTextbox(
            content,
            height=160,
            fg_color="#f9fafb",
            border_color="#e5e7eb",
            border_width=1
        ).pack(fill="x", pady=(6, 16))

        label("Data do evento").pack(anchor="w")
        ctk.CTkEntry(content, placeholder_text="dd/mm/aaaa", **entry_style)\
            .pack(fill="x", pady=(6, 16))

        footer = ctk.CTkFrame(box, fg_color="#f9fafb", height=70, corner_radius=16)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        ctk.CTkButton(
            footer,
            text="Cancelar",
            fg_color="#e5e7eb",
            text_color="#111827",
            hover_color="#d1d5db",
            height=40,
            command=modal.destroy
        ).pack(side="left", expand=True, fill="x", padx=(30, 10), pady=15)

        ctk.CTkButton(
            footer,
            text="Salvar rascunho",
            fg_color="#6d28d9",
            hover_color="#5b21b6",
            text_color="white",
            height=40
        ).pack(side="right", expand=True, fill="x", padx=(10, 30), pady=15)

import customtkinter as ctk
from PIL import Image
import os
import threading
from datetime import datetime
from services.estudantes import ServicoEstudante
from ui_theme import THEME, SPACING, RADIUS, font, themed_font
from components.ui_components import (
    PageHeader,
    Card,
    PrimaryButton,
    SecondaryButton,
    SearchField,
    EmptyState,
    Divider,
    Badge,
)


class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_estudante = ServicoEstudante()
        self.colors = THEME

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.criar_cabecalho()
        self.criar_area_conteudo()
        self.load_data()

    def criar_cabecalho(self):
        header = PageHeader(
            self,
            title="Estudantes",
            subtitle="Acompanhamento e monitoramento discente",
            actions=[
                PrimaryButton(None, text="Novo Estudante", command=self.novo_estudante_click, icon="➕", width=160),
            ],
        )
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 16))

    def criar_area_conteudo(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)

        self.criar_sidebar(content)
        self.criar_detalhes(content)

    def criar_sidebar(self, parent):
        sidebar_card = Card(parent)
        sidebar_card.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        self.sidebar_card = sidebar_card

        SearchField(sidebar_card.body, placeholder="Buscar estudante...", command=self.filtrar_estudantes).pack(fill="x", pady=(0, 10))

        filter_box = ctk.CTkFrame(sidebar_card.body, fg_color="transparent")
        filter_box.pack(fill="x", pady=(0, 8))

        self.f_laudo = ctk.CTkOptionMenu(
            filter_box,
            values=["Laudos: Todos", "Com Laudo", "Sem Laudo"],
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            height=30,
        )
        self.f_laudo.pack(side="left", expand=True, padx=(0, 4))

        self.f_aten = ctk.CTkOptionMenu(
            filter_box,
            values=["Atenção: Todos", "Requer Atenção"],
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            height=30,
        )
        self.f_aten.pack(side="left", expand=True, padx=(4, 0))

        self.scroll_list = ctk.CTkScrollableFrame(sidebar_card.body, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, pady=8)

    def criar_detalhes(self, parent):
        detail_card = Card(parent)
        detail_card.grid(row=0, column=1, sticky="nsew")
        self.detail_card = detail_card

        header = ctk.CTkFrame(detail_card.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        self.lbl_avatar_big = ctk.CTkLabel(
            header, text="AS", width=56, height=56, corner_radius=28, fg_color=THEME["primary"], text_color="white", font=themed_font("h3", "bold")
        )
        self.lbl_avatar_big.pack(side="left", padx=(0, 14))

        info_v = ctk.CTkFrame(header, fg_color="transparent")
        info_v.pack(side="left")
        self.lbl_nome_det = ctk.CTkLabel(info_v, text="Ana Silva", font=themed_font("h3", "bold"), text_color=THEME["text"])
        self.lbl_nome_det.pack(anchor="w")
        self.lbl_curso_det = ctk.CTkLabel(info_v, text="Segurança da Informação", font=themed_font("body"), text_color=THEME["text_muted"])
        self.lbl_curso_det.pack(anchor="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", anchor="n")
        SecondaryButton(actions, text="Editar", command=lambda: None, width=90).pack(side="left", padx=6)
        SecondaryButton(actions, text="Excluir", command=lambda: None, width=90).pack(side="left", padx=6)

        self.tabs = ctk.CTkTabview(detail_card.body, fg_color="transparent", segmented_button_selected_color=THEME["primary"])
        self.tabs.pack(fill="both", expand=True, pady=(8, 0))

        self.tab_info = self.tabs.add("Informações Pessoais")
        self.tabs.add("Histórico de Intervenções")
        self.tabs.add("Agendamentos")

        info_grid = ctk.CTkFrame(self.tab_info, fg_color="transparent")
        info_grid.pack(fill="both", expand=True, pady=8)
        info_grid.grid_columnconfigure((0, 1), weight=1)

        self.card_email = self.criar_info_box(info_grid, "Contato", "--", "📧", 0, 0)
        self.card_idade = self.criar_info_box(info_grid, "Idade", "--", "🎂", 0, 1)
        self.card_curso = self.criar_info_box(info_grid, "Curso / Turma", "--", "🎓", 1, 0)
        self.card_laudo = self.criar_info_box(info_grid, "Laudo Médico", "--", "📄", 1, 1)

    def criar_info_box(self, parent, label, value, icon, r, c):
        box = Card(parent)
        box.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(box.body, text=label, font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(0, 6))
        row = ctk.CTkFrame(box.body, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text=icon, font=themed_font("body")).pack(side="left", padx=(0, 8))
        lbl = ctk.CTkLabel(row, text=value, font=themed_font("body", "bold"), text_color=THEME["text"])
        lbl.pack(side="left")
        return lbl

    def load_data(self):
        def fetch():
            res = self.servico_estudante.listar_estudantes()
            self.after(0, lambda: self.render_list(res))

        threading.Thread(target=fetch, daemon=True).start()

    def render_list(self, result):
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        students = []
        if result.get('success'):
            data = result.get('data', [])
            if isinstance(data, dict):
                students = data.get('students', []) or data.get('results', [])
            elif isinstance(data, list):
                students = data

        if not students:
            EmptyState(self.scroll_list, icon="👥", title="Nenhum estudante encontrado", subtitle="Tente ajustar os filtros de busca").pack(pady=10)
            return

        for st in students:
            if not isinstance(st, dict):
                continue

            item = ctk.CTkFrame(self.scroll_list, fg_color="transparent", height=64, cursor="hand2")
            item.pack(fill="x", pady=3)

            inicial = (st.get('name', '??')[:2] or "??").upper()
            avatar = ctk.CTkLabel(item, text=inicial, width=36, height=36, corner_radius=18, fg_color=THEME["primary_soft"], text_color=THEME["primary"], font=themed_font("body", "bold"))
            avatar.pack(side="left", padx=(4, 10))

            txt = ctk.CTkFrame(item, fg_color="transparent")
            txt.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(txt, text=st.get('name', 'N/A'), font=themed_font("body", "bold"), text_color=THEME["text"]).pack(anchor="w")
            ctk.CTkLabel(txt, text=st.get('course', 'Sem curso'), font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="w")

            if st.get('requires_attention'):
                Badge(txt, text="Atenção").pack(side="right")

            item.bind("<Button-1>", lambda e, s=st: self.selecionar_estudante(s))

    def filtrar_estudantes(self, termo: str) -> None:
        termo = termo.lower()
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        # Nota: este filtro é visual; se quiser filtrar no dataset, ajustar load_data.
        print(f"Filtrando por: {termo}")

    def selecionar_estudante(self, st):
        self.lbl_nome_det.configure(text=st.get('name', 'N/A'))
        self.lbl_curso_det.configure(text=st.get('course', 'N/A'))
        self.lbl_avatar_big.configure(text=(st.get('name', '??')[:2] or "??").upper())

        self.card_email.configure(text=st.get('contact', '--'))
        self.card_idade.configure(text=f"{st.get('age', '--')} anos")
        self.card_curso.configure(text=st.get('course', '--'))
        self.card_laudo.configure(text="Sim" if st.get('has_medical_report') else "Não")

    def novo_estudante_click(self):
        from tkinter import messagebox
        modal = ctk.CTkToplevel(self)
        modal.title("Adicionar Novo Estudante")
        modal.geometry("580x720")
        modal.configure(fg_color=THEME["card"])
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=28)

        def criar_input(parent, label, placeholder):
            ctk.CTkLabel(parent, text=label, font=themed_font("caption", "bold"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(10, 5))
            entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=40, fg_color=THEME["bg_alt"], border_width=0, corner_radius=RADIUS["input"])
            entry.pack(fill="x")
            return entry

        en_nome = criar_input(container, "Nome Completo", "Ex: Ana Silva")

        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=8)
        en_curso = criar_input(row1, "Curso / Turma", "Ex: Psicologia")
        en_idade = criar_input(row1, "Idade", "Ex: 22")

        en_email = criar_input(container, "Email de Contato", "email@exemplo.com")

        sw_laudo = ctk.CTkSwitch(container, text="Possui laudo médico", font=themed_font("body"))
        sw_laudo.pack(fill="x", pady=10)

        sw_aten = ctk.CTkSwitch(container, text="Requer atendimento prioritário", font=themed_font("body"))
        sw_aten.pack(fill="x", pady=6)

        def salvar():
            if not en_nome.get():
                return messagebox.showerror("Erro", "Nome é obrigatório")

            dados = {
                'nome': en_nome.get(),
                'email': en_email.get(),
                'has_medical_report': sw_laudo.get(),
                'requires_attention': sw_aten.get(),
                'course': en_curso.get(),
                'age': en_idade.get()
            }
            if self.servico_estudante.criar_estudante(dados).get('success'):
                modal.destroy()
                self.load_data()

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom", pady=16)
        GhostButton(btn_box, text="Cancelar", command=modal.destroy).pack(side="left")
        PrimaryButton(btn_box, text="Salvar Estudante", command=salvar).pack(side="right")

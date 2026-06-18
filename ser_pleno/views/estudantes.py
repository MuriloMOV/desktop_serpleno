import customtkinter as ctk
from PIL import Image
import os
import threading
from datetime import datetime
from services.estudantes import ServicoEstudante
from ui_theme import THEME, SPACING, RADIUS, font, themed_font, blend_color
from components.ui_components import (
    PageHeader, Card, PrimaryButton, SecondaryButton, SearchField, EmptyState, Divider,
    Badge, Pill, InputField, Avatar, DangerButton
)


class EstudantesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_estudante = ServicoEstudante()
        self.colors = THEME

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.criar_cabecalho()
        self.criar_area_conteudo()
        self.load_data()

    def criar_cabecalho(self):
        header = PageHeader(
            self,
            title="Estudantes",
            subtitle="Acompanhamento e monitoramento discente",
            actions=[PrimaryButton(None, text="Novo Estudante", command=self.novo_estudante_click, icon="➕", width=160)],
            show_breadcrumb=True, breadcrumb_parts=["Estudantes", "Turma"],
        )
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(0, 16))

    def criar_area_conteudo(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))
        content.grid_columnconfigure(1, weight=3)
        content.grid_rowconfigure(0, weight=1)

        self.criar_sidebar(content)
        self.criar_detalhes(content)

    def criar_sidebar(self, parent):
        card = Card(parent, title="")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.sidebar_card = card

        top = ctk.CTkFrame(card.body, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))
        SearchField(top, placeholder="Buscar estudante...", command=self.filtrar_estudantes).pack(side="left", fill="x", expand=True, padx=(0, 8))

        f_box = ctk.CTkFrame(self.sidebar_card.body, fg_color="transparent")
        f_box.pack(fill="x", pady=(0, 8))

        self.f_laudo = ctk.CTkOptionMenu(
            f_box, values=["Laudos: Todos", "Com Laudo", "Sem Laudo"],
            fg_color=THEME["bg_alt"], text_color=THEME["text"], height=32, corner_radius=RADIUS["input"],
        )
        self.f_laudo.pack(side="left", expand=True, padx=(0, 4))

        self.f_aten = ctk.CTkOptionMenu(
            f_box, values=["Atenção: Todos", "Requer Atenção"],
            fg_color=THEME["bg_alt"], text_color=THEME["text"], height=32, corner_radius=RADIUS["input"],
        )
        self.f_aten.pack(side="left", expand=True, padx=(4, 0))

        self.scroll_list = ctk.CTkScrollableFrame(self.sidebar_card.body, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, pady=8)

    def criar_detalhes(self, parent):
        card = Card(parent, title="")
        card.grid(row=0, column=1, sticky="nsew")
        self.detail_card = card

        header = ctk.CTkFrame(card.body, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))

        self.lbl_avatar_big = Avatar(header, initials="AS", size=56, color=THEME["primary"])
        self.lbl_avatar_big.pack(side="left", padx=(0, 14))

        info_v = ctk.CTkFrame(header, fg_color="transparent")
        info_v.pack(side="left", fill="both", expand=True)
        self.lbl_nome_det = ctk.CTkLabel(info_v, text="Selecione um estudante", font=themed_font("h3", "bold"), text_color=THEME["text"])
        self.lbl_nome_det.pack(anchor="w")
        self.lbl_curso_det = ctk.CTkLabel(info_v, text="—", font=themed_font("body_sm"), text_color=THEME["text_muted"])
        self.lbl_curso_det.pack(anchor="w")

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.pack(side="right", anchor="n")
        SecondaryButton(actions, text="Editar", command=lambda: None, width=96, icon="✏").pack(side="left", padx=6)
        DangerButton(actions, text="Excluir", command=lambda: None, width=96, icon="🗑").pack(side="left", padx=6)

        btn_row = ctk.CTkFrame(card.body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 12))
        PrimaryButton(btn_row, text="➕  Cadastrar novo",
                      command=self.novo_estudante_click, icon="➕", width=180).pack(side="left")

        self.tabs = ctk.CTkTabview(card.body, fg_color="transparent",
                                   segmented_button_fg_color=THEME["bg_alt"],
                                   segmented_button_selected_color=THEME["primary"],
                                   segmented_button_selected_hover_color=THEME["primary_hover"],
                                   text_color=THEME["text_secondary"],
                                   text_color_disabled=THEME["text_muted"],
                                   corner_radius=RADIUS["button"],
                                   height=320)
        self.tabs.pack(fill="both", expand=True, pady=(4, 0))

        self.tab_info = self.tabs.add("Perfil")
        self.tabs.add("Intervenções")
        self.tabs.add("Agenda")

        info_grid = ctk.CTkFrame(self.tab_info, fg_color="transparent")
        info_grid.pack(fill="both", expand=True, pady=10)
        info_grid.grid_columnconfigure((0, 1), weight=1)

        self.card_email = self.criar_info_box(info_grid, "Contato", "--", "📧", 0, 0)
        self.card_idade = self.criar_info_box(info_grid, "Idade", "--", "🎂", 0, 1)
        self.card_curso = self.criar_info_box(info_grid, "Curso / Turma", "--", "🎓", 1, 0)
        self.card_laudo = self.criar_info_box(info_grid, "Laudo Médico", "--", "📄", 1, 1)

        self.detail_status = ctk.CTkFrame(card.body, fg_color=THEME["bg_alt"], corner_radius=RADIUS["sm"])
        self.detail_status.pack(fill="x", side="bottom", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        ctk.CTkLabel(self.detail_status, text="Status", font=themed_font("overline"), text_color=THEME["text_muted"]).pack(anchor="nw", padx=12, pady=(10, 0))
        self.lbl_status_det = ctk.CTkLabel(self.detail_status, text="—", font=themed_font("body", "bold"), text_color=THEME["text"])
        self.lbl_status_det.pack(anchor="nw", padx=12, pady=(2, 10))

    def criar_info_box(self, parent, label, value, icon, r, c):
        box = Card(parent, title="")
        box.grid(row=r, column=c, padx=6, pady=6, sticky="nsew", ipadx=8, ipady=8)

        h = ctk.CTkFrame(box.body, fg_color="transparent")
        h.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(h, text=icon, font=themed_font("h3")).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(h, text=label, font=themed_font("caption", "bold"), text_color=THEME["text_secondary"]).pack(side="left")

        lbl = ctk.CTkLabel(box.body, text=value, font=themed_font("h4", "bold"), text_color=THEME["text"])
        lbl.pack(anchor="w")

        return lbl

    def load_data(self):
        def fetch():
            res = self.servico_estudante.listar_estudantes()
            self.after(0, lambda: self.render_list(res))

        threading.Thread(target=fetch, daemon=True).start()

    def render_list(self, result):
        if not self.winfo_exists():
            return
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        students = []
        if result.get("success"):
            data = result.get("data", [])
            if isinstance(data, dict):
                students = data.get("students", []) or data.get("results", [])
            elif isinstance(data, list):
                students = data

        if not students:
            EmptyState(self.scroll_list, icon="👥", title="Nenhum estudante encontrado",
                       subtitle="Tente ajustar os filtros de busca").pack(pady=10)
            return

        for st in students:
            if not isinstance(st, dict):
                continue

            item = ctk.CTkFrame(self.scroll_list, fg_color=THEME["surface"], corner_radius=RADIUS["md"],
                                border_width=1, border_color=THEME["border"], height=64, cursor="hand2")
            item.pack(fill="x", pady=3)

            inicial = (st.get("name", "??")[:2] or "??").upper()
            avatar = Avatar(item, initials=inicial, size=38,
                            color=THEME["primary_soft"], text_color=THEME["primary"])
            avatar.pack(side="left", padx=(10, 10))

            txt = ctk.CTkFrame(item, fg_color="transparent")
            txt.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(txt, text=st.get("name", "N/A"), font=themed_font("body", "bold"),
                         text_color=THEME["text"]).pack(anchor="w")
            ctk.CTkLabel(txt, text=st.get("course", "Sem curso"), font=themed_font("overline"),
                         text_color=THEME["text_muted"]).pack(anchor="w")

            if st.get("requires_attention"):
                Pill(txt, text="Atenção", color=THEME["danger_soft"], text_color=THEME["danger_strong"], variant="soft").pack(side="right", padx=(8, 8))

            item.bind("<Button-1>", lambda e, s=st: self.selecionar_estudante(s))

    def filtrar_estudantes(self, termo: str) -> None:
        termo = termo.lower()
        for widget in self.scroll_list.winfo_children():
            widgets = widget.winfo_children()
            lbls = [w for w in widgets if isinstance(w, ctk.CTkLabel)]
            nome = next((l.cget("text") for l in lbls if l.cget("font") != themed_font("overline")), "").lower()
            estado = "normal" if termo in nome else "hidden"
            widget.pack(fill="x", pady=3) if estado == "normal" else widget.pack_forget()

    def selecionar_estudante(self, st):
        nome = st.get("name", "N/A")
        inicial = nome[:2].upper()
        self.lbl_avatar_big.configure(text=inicial)
        self.lbl_nome_det.configure(text=nome)
        self.lbl_curso_det.configure(text=st.get("course", "Sem curso"))

        self.card_email.configure(text=st.get("contact", "--"))
        self.card_idade.configure(text=f"{st.get('age', '--')} anos")
        self.card_curso.configure(text=st.get("course", "--"))
        self.card_laudo.configure(text="Sim" if st.get("has_medical_report") else "Não")

        status = "Sem alertas"
        if st.get("requires_attention"):
            status = "Requere atenção prioritária"
        self.lbl_status_det.configure(text=status, text_color=THEME["danger_strong"] if st.get("requires_attention") else THEME["text"])

    def novo_estudante_click(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Adicionar Novo Estudante")
        modal.geometry("620x740")
        modal.configure(fg_color=THEME["surface"])
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        w, h = 620, 760
        modal.geometry(f"{w}x{h}+{(modal.winfo_screenwidth()//2)-(w//2)}+{(modal.winfo_screenheight()//2)-(h//2)}")

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=32, pady=32)

        ctk.CTkLabel(container, text="Novo Estudante", font=themed_font("h2", "bold"),
                     text_color=THEME["text"]).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(container, text="Preencha os dados para cadastrar um novo estudante",
                     font=themed_font("body_sm"), text_color=THEME["text_muted"]).pack(anchor="w", pady=(0, 20))

        Divider(container).pack(fill="x", pady=(0, 20))

        en_nome = InputField(container, "Nome Completo", placeholder="Ex: Ana Silva",
                             icon="👤", helper="Nome completo do estudante")
        en_nome.pack(fill="x", pady=SPACING["input_y"])

        en_email = InputField(container, "Email de Contato", placeholder="email@exemplo.com",
                              icon="📧", helper="Email institucional ou pessoal")
        en_email.pack(fill="x", pady=SPACING["input_y"])

        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=8)
        en_curso = InputField(row1, "Curso / Turma", placeholder="Ex: Psicologia", icon="🎓")
        en_curso.pack(side="left", fill="both", expand=True, padx=(0, 8))
        en_idade = InputField(row1, "Idade", placeholder="Ex: 22", icon="🎂")
        en_idade.pack(side="right", fill="both", expand=True, padx=(8, 0))

        sw_laudo = ctk.CTkSwitch(
            container, text="Possui laudo médico",
            fg_color=THEME["bg_alt"], progress_color=THEME["primary"],
            button_color=THEME["surface"], button_hover_color=THEME["bg_alt"],
            font=themed_font("body"), corner_radius=RADIUS["pill"]
        )
        sw_laudo.pack(fill="x", pady=6)

        sw_aten = ctk.CTkSwitch(
            container, text="Requer atendimento prioritário",
            fg_color=THEME["bg_alt"], progress_color=THEME["danger"],
            button_color=THEME["surface"], button_hover_color=THEME["bg_alt"],
            font=themed_font("body"), corner_radius=RADIUS["pill"]
        )
        sw_aten.pack(fill="x", pady=6)

        def salvar():
            if not en_nome.get().strip():
                en_nome.set_error("Nome é obrigatório")
                return
            dados = {
                "nome": en_nome.get().strip(),
                "email": en_email.get().strip(),
                "has_medical_report": sw_laudo.get(),
                "requires_attention": sw_aten.get(),
                "course": en_curso.get().strip(),
                "age": en_idade.get().strip(),
            }
            if self.servico_estudante.criar_estudante(dados).get("success"):
                modal.destroy()
                self.load_data()
                Toast(self, "Estudante cadastrado com sucesso!", status="success", duration=3000)

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x", side="bottom", pady=20)
        GhostButton(btn_box, text="Cancelar", command=modal.destroy, width=140).pack(side="left", padx=(0, 8))
        PrimaryButton(btn_box, text="Salvar Estudante", command=salvar, width=200, icon="✔").pack(side="right")

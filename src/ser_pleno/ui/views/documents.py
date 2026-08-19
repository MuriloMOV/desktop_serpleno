from __future__ import annotations

import logging
import os
from tkinter import filedialog

import customtkinter as ctk

from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.components.ui_components import (
    BaseModal,
    Card,
    DangerButton,
    EmptyState,
    GhostButton,
    PrimaryButton,
)
from ser_pleno.ui.theme import RADIUS, SPACING, THEME, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.views.base import BaseViewFrame
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger(__name__)


class DocumentsFrame(BaseViewFrame):
    def __init__(self, parent, controller):
        self._t0 = __import__("time").perf_counter()
        super().__init__(parent, controller, fg_color=THEME["bg"])
        self.servico_documents = getattr(controller, "servico_documents", None)
        self._search_var = ctk.StringVar()
        self._documents: list[dict] = []
        self._card_refs: list[ctk.CTkFrame] = []

        self._criar_toolbar()
        self._carregar_dados()

        log_view_init_ms("documents", self._t0, widget_ref=self)

    def _criar_toolbar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], spacing("sm")))

        ctk.CTkLabel(
            bar,
            text=f"{ICONS['document']}  Documentos",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).pack(side="left")

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        search_entry = ctk.CTkEntry(
            right,
            placeholder_text="Buscar documento...",
            textvariable=self._search_var,
            width=220,
            height=34,
            corner_radius=RADIUS["button"],
        )
        search_entry.pack(side="left", padx=(0, spacing("sm")))
        search_entry.bind("<KeyRelease>", self._on_search)

        PrimaryButton(
            right,
            text=f"{ICONS['add']}  Novo Documento",
            command=self._abrir_modal_criar,
            height=34,
            text_color="white",
        ).pack(side="left")

    def _on_search(self, event=None):
        self._carregar_dados()

    def _carregar_dados(self):
        self._limpar_cards()

        skeleton = Card(self, title="Carregando...", padding=(spacing("sm"), spacing("xs")))
        skeleton.pack(fill="x", padx=SPACING["page_x"], pady=(0, spacing("sm")))
        self._card_refs.append(skeleton)
        ctk.CTkLabel(skeleton.body, text="", font=themed_font("body")).pack(pady=spacing("md"))

        def fetch():
            search = self._search_var.get().strip() or None
            resp = self.servico_documents.listar_documentos(search=search)
            if resp and resp.get("success"):
                return resp.get("data", [])
            return []

        def on_success(documents):
            self._documents = documents
            self._render_documents(documents)

        def on_error(exc):
            logger.error("Erro ao carregar documentos: %s", exc)
            self._render_documents([])

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _limpar_cards(self):
        for ref in self._card_refs:
            if ref.winfo_exists():
                ref.destroy()
        self._card_refs.clear()

    def _render_documents(self, documents):
        self._limpar_cards()

        if not documents:
            EmptyState(
                self,
                icon=ICONS["document"],
                title="Nenhum documento encontrado",
                subtitle="Clique em Novo Documento para adicionar",
            ).pack(pady=spacing("xl"))
            return

        for doc in documents:
            self._criar_document_row(doc)

    def _criar_document_row(self, doc):
        nome = doc.get("name", "Sem nome")
        tipo = doc.get("document_type", "Geral")
        tamanho = doc.get("file_size", 0)
        tamanho_str = self._formatar_tamanho(tamanho)
        expira = doc.get("expires_at")
        expira_str = f"Expira: {expira}" if expira else "Sem vencimento"

        card = Card(self, title="", padding=(spacing("sm"), spacing("xs")))
        card.pack(fill="x", padx=SPACING["page_x"], pady=(0, spacing("sm")))
        self._card_refs.append(card)

        inner = ctk.CTkFrame(card.body, fg_color="transparent")
        inner.pack(fill="both", padx=spacing("md"), pady=spacing("sm"))
        inner.grid_columnconfigure(1, weight=1)

        icon_bg = ctk.CTkFrame(
            inner,
            width=40,
            height=40,
            corner_radius=RADIUS["button"],
            fg_color=THEME["kpi_blue"],
        )
        icon_bg.grid(row=0, column=0, rowspan=2, padx=(0, spacing("md")), sticky="n", pady=(spacing("xs"), 0))
        icon_bg.grid_propagate(False)
        ctk.CTkLabel(
            icon_bg,
            text=ICONS["document"],
            font=themed_font("h4"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text=nome,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner,
            text=f"{tipo}  •  {tamanho_str}  •  {expira_str}",
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(spacing("xs"), 0))

        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, padx=(spacing("sm"), 0), sticky="e")

        GhostButton(
            actions,
            text="Abrir",
            command=lambda d=doc: self._abrir_documento(d),
            width=80,
            height=30,
        ).pack(side="left", padx=(0, spacing("xs")))

        DangerButton(
            actions,
            text="Excluir",
            command=lambda d=doc: self._confirmar_exclusao(d),
            width=80,
            height=30,
        ).pack(side="left")

    def _formatar_tamanho(self, bytes_size):
        if not bytes_size:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(bytes_size) < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"

    def _abrir_modal_criar(self):
        modal = BaseModal(self, title="Novo Documento", width=520, height=420)
        scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        entry_nome = ctk.CTkEntry(scroll, placeholder_text="Nome do documento")
        entry_nome.pack(fill="x", padx=spacing("lg"), pady=(spacing("lg"), spacing("sm")))

        entry_tipo = ctk.CTkEntry(scroll, placeholder_text="Tipo (ex: Laudo, Relatório)")
        entry_tipo.pack(fill="x", padx=spacing("lg"), pady=(0, spacing("sm")))

        entry_caminho = ctk.CTkEntry(scroll, placeholder_text="Caminho do arquivo")
        entry_caminho.pack(fill="x", padx=spacing("lg"), pady=(0, spacing("sm")))

        def _selecionar_arquivo():
            caminho = filedialog.askopenfilename()
            if caminho:
                entry_caminho.delete(0, "end")
                entry_caminho.insert(0, caminho)

        GhostButton(
            scroll,
            text="Selecionar Arquivo",
            command=_selecionar_arquivo,
            height=32,
        ).pack(padx=spacing("lg"), pady=(0, spacing("sm")), anchor="w")

        entry_descricao = ctk.CTkTextbox(scroll, height=100)
        entry_descricao.insert("0.0", "Descrição...")
        entry_descricao.pack(fill="x", padx=spacing("lg"), pady=(0, spacing("sm")))

        entry_expiracao = ctk.CTkEntry(scroll, placeholder_text="Expira em (YYYY-MM-DD, opcional)")
        entry_expiracao.pack(fill="x", padx=spacing("lg"), pady=(0, spacing("md")))

        footer = ctk.CTkFrame(scroll, fg_color="transparent")
        footer.pack(fill="x", padx=spacing("lg"), pady=(0, spacing("lg")))

        def _salvar():
            nome = entry_nome.get().strip()
            if not nome:
                self._show_error("Nome é obrigatório.")
                return
            caminho = entry_caminho.get().strip()
            if not caminho or not os.path.exists(caminho):
                self._show_error("Selecione um arquivo válido.")
                return
            file_size = os.path.getsize(caminho)
            dados = {
                "name": nome,
                "document_type": entry_tipo.get().strip() or "Geral",
                "file_path": caminho,
                "file_size": file_size,
                "uploaded_by_id": getattr(self.controller, "usuario_logado_id", 1),
                "description": entry_descricao.get("0.0", "end").strip(),
                "expires_at": entry_expiracao.get().strip() or None,
            }
            res = self.servico_documents.criar_documento(dados)
            if res and res.get("success"):
                self._show_success("Documento criado com sucesso.")
                modal.destroy()
                self._carregar_dados()
            else:
                self._show_error(res.get("message", "Falha ao criar documento."))

        PrimaryButton(footer, text="Salvar", command=_salvar, height=36, text_color="white").pack(
            side="right"
        )
        GhostButton(footer, text="Cancelar", command=modal.destroy, height=36).pack(
            side="right", padx=(0, spacing("sm"))
        )

    def _abrir_documento(self, doc):
        caminho = doc.get("file_path")
        if caminho and os.path.exists(caminho):
            os.startfile(caminho)
        else:
            self._show_error("Arquivo não encontrado.")

    def _confirmar_exclusao(self, doc):
        modal = BaseModal(self, title="Confirmar exclusão", width=420, height=200)
        scroll = ctk.CTkScrollableFrame(modal, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text=f"Excluir documento '{doc.get('name')}'?",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(pady=spacing("lg"), padx=spacing("lg"))

        footer = ctk.CTkFrame(scroll, fg_color="transparent")
        footer.pack(fill="x", padx=spacing("lg"), pady=(0, spacing("lg")))

        def _excluir():
            res = self.servico_documents.deletar_documento(doc.get("id"))
            if res and res.get("success"):
                self._show_success("Documento excluído.")
                modal.destroy()
                self._carregar_dados()
            else:
                self._show_error(res.get("message", "Falha ao excluir."))

        DangerButton(footer, text="Excluir", command=_excluir, height=36, text_color="white").pack(
            side="right"
        )
        GhostButton(footer, text="Cancelar", command=modal.destroy, height=36).pack(
            side="right", padx=(0, spacing("sm"))
        )

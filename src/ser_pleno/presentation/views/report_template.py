# -*- coding: utf-8 -*-
"""View de Templates de Relatorio."""

from __future__ import annotations

import logging
import customtkinter as ctk
from typing import Optional

from ser_pleno.application.controllers.report_template import ReportTemplateController
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.presentation.components.ui_components import (
    Card, EmptyState, PrimaryButton, GhostButton, Divider, BaseModal, Toast,
)
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger("apps.desktop")


class TemplateFormModal(BaseModal):
    def __init__(self, parent, on_salvar, template: Optional[dict] = None):
        self.on_salvar = on_salvar
        self.template = template
        super().__init__(parent, title="Novo Template" if not template else "Editar Template", width=560, height=420)
        self.configure(fg_color=THEME["surface"])
        self._build()

    def _build(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=f"{ICONS['file']}  {'Novo Template' if not self.template else 'Editar Template'}",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        form = ctk.CTkFrame(wrapper, fg_color="transparent")
        form.pack(fill="both", expand=True)

        ctk.CTkLabel(form, text="Nome", font=font(size=12), text_color=THEME["text"]).pack(anchor="w")
        self.f_nome = ctk.CTkEntry(form, fg_color=THEME["input_bg"], border_width=1, border_color=THEME["input_border"], font=font(size=12))
        self.f_nome.pack(fill="x", pady=(0, spacing("md")))

        ctk.CTkLabel(form, text="Tipo", font=font(size=12), text_color=THEME["text"]).pack(anchor="w")
        self.f_tipo = ctk.CTkOptionMenu(
            form,
            values=["geral", "estudante", "agendamentos", "triagens", "estatisticas", "intervencoes"],
            font=font(size=12),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
        )
        self.f_tipo.pack(fill="x", pady=(0, spacing("md")))

        ctk.CTkLabel(form, text="Configuracao (JSON opcional)", font=font(size=12), text_color=THEME["text"]).pack(anchor="w")
        self.f_config = ctk.CTkTextbox(form, height=100, fg_color=THEME["input_bg"], border_width=1, border_color=THEME["input_border"], font=font(size=12))
        self.f_config.pack(fill="x", pady=(0, spacing("md")))

        btns = ctk.CTkFrame(wrapper, fg_color="transparent")
        btns.pack(fill="x", pady=(spacing("md"), 0))

        PrimaryButton(btns, text="Salvar", command=self._salvar, width=120).pack(side="right", padx=(spacing("sm"), 0))
        GhostButton(btns, text="Cancelar", command=self.destroy, width=120).pack(side="right")

        if self.template:
            self.f_nome.insert(0, self.template.get("name", ""))
            self.f_tipo.set(self.template.get("report_type", "geral"))
            config = self.template.get("template_config") or {}
            self.f_config.insert("1.0", str(config))

    def _salvar(self):
        nome = self.f_nome.get().strip()
        tipo = self.f_tipo.get()
        if not nome:
            self._show_error("Nome do template é obrigatório.")
            return
        try:
            config_text = self.f_config.get("1.0", "end").strip()
            import json
            config = json.loads(config_text) if config_text else {}
        except Exception:
            config = {}
        self.on_salvar({
            "name": nome,
            "report_type": tipo,
            "template_config": config,
            "is_active": True,
        })
        self.destroy()


class ReportTemplateFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        import time as _time
        self._t0 = _time.perf_counter()
        super().__init__(master, fg_color=THEME["bg"])
        self.controller = controller
        self.app = getattr(controller, "app", None)
        self._templates: list[dict] = []
        self._filtro_tipo = ""

        self._build_header()
        self._build_filtros()
        self._build_lista()
        self.carregar_templates_async()
        log_view_init_ms("report_template", self._t0, widget_ref=self)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=spacing("xl"), pady=(spacing("lg"), spacing("sm")))

        ctk.CTkLabel(
            header, text=f"{ICONS['file']}  Templates de Relatorio",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        PrimaryButton(
            header, text="Novo Template", command=self._abrir_novo,
            height=36, width=140,
        ).pack(side="right")

    def _build_filtros(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=spacing("xl"), pady=(0, spacing("sm")))

        ctk.CTkLabel(frame, text="Tipo:", font=font(size=12), text_color=THEME["text_muted"]).pack(side="left", padx=(0, spacing("xs")))
        self.f_tipo = ctk.CTkOptionMenu(
            frame,
            values=["Todos", "geral", "estudante", "agendamentos", "triagens", "estatisticas", "intervencoes"],
            font=font(size=12),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            width=160,
            height=34,
            corner_radius=RADIUS["input"],
            command=self._aplicar_filtro,
        )
        self.f_tipo.pack(side="left")

    def _build_lista(self):
        card = Card(self, padding=(SPACING["card_pad"], SPACING["label_gap"]))
        card.pack(fill="both", expand=True, padx=spacing("xl"), pady=(0, spacing("xl")))

        hdr = ctk.CTkFrame(card.body, fg_color="transparent")
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="Templates",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        Divider(card.body).pack(fill="x", pady=(SPACING["label_gap"], 0))

        self.lista = ctk.CTkScrollableFrame(
            card.body, fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.lista.pack(fill="both", expand=True, pady=(SPACING["label_gap"], 0))

    def _aplicar_filtro(self, valor):
        self._filtro_tipo = "" if valor == "Todos" else valor
        self.carregar_templates_async()

    def _limpar_lista(self):
        try:
            if self.lista.winfo_exists():
                for w in self.lista.winfo_children():
                    w.destroy()
        except Exception:
            pass

    def _mostrar_skeletons(self):
        for _ in range(3):
            SkeletonLoader(self.lista, width=760, height=64, variant="card").pack(
                fill="x", pady=(0, 12)
            )

    def carregar_templates_async(self):
        self._limpar_lista()
        self._mostrar_skeletons()

        def _fetch():
            return self.controller.listar_templates(tipo=self._filtro_tipo or None, apenas_ativos=True)

        def _on_success(res):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            templates = self._parse(res)
            self._templates = templates

            if not templates:
                EmptyState(
                    self.lista,
                    icon=ICONS["empty"],
                    title="Nenhum template encontrado",
                    subtitle="Crie um novo template para comecar",
                ).pack(pady=30)
                return

            batch = WidgetBatchBuilder(parent=self, batch_size=20)
            for t in templates:
                if not isinstance(t, dict):
                    continue
                batch.add(lambda t=t: self._criar_row(t))
            batch.execute()

        def _on_error(exc):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            EmptyState(
                self.lista,
                icon=ICONS["bolt"],
                title="Erro ao carregar templates",
                subtitle=str(exc),
            ).pack(pady=20)

        AsyncRunner.run(
            task=_fetch,
            on_success=_on_success,
            on_error=_on_error,
            widget_ref=self,
        )

    def _parse(self, res) -> list[dict]:
        if isinstance(res, dict):
            if res.get("success") is False:
                return []
            data = res.get("data")
            if isinstance(data, list):
                return data
            if res.get("id"):
                return [res]
        if isinstance(res, list):
            return res
        return []

    def _criar_row(self, template: dict):
        row = ctk.CTkFrame(
            self.lista,
            fg_color=THEME["row_bg"],
            corner_radius=RADIUS["button"],
        )
        row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)

        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=THEME["row_hover"]))
        row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=THEME["row_bg"]))

        nome = template.get("name", "Template")
        tipo = template.get("report_type", "geral")
        ativo = template.get("is_active", True)

        ctk.CTkLabel(
            row, text=nome,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).grid(row=0, column=0, sticky="w", padx=spacing("md"), pady=spacing("item_gap"))

        ctk.CTkLabel(
            row, text=tipo,
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=1, sticky="w", padx=spacing("md"), pady=spacing("item_gap"))

        badge_text = "Ativo" if ativo else "Inativo"
        badge_color = THEME["success"] if ativo else THEME["text_muted"]
        Badge(row, text=badge_text, fg_color=THEME["success_soft"] if ativo else THEME["row_bg"], text_color=badge_color).grid(row=0, column=2, sticky="w", padx=spacing("md"), pady=spacing("item_gap"))

        acts = ctk.CTkFrame(row, fg_color="transparent")
        acts.grid(row=0, column=3, sticky="e", padx=spacing("md"), pady=spacing("icon_gap"))

        for icon, cmd in [
            (ICONS["view"], lambda t=template: self._preview(t)),
            (ICONS["edit"], lambda t=template: self._abrir_editar(t)),
            (ICONS["delete"], lambda t=template: self._excluir(t)),
        ]:
            GhostButton(
                acts, text=icon,
                width=30, height=30, corner_radius=RADIUS["xs"],
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=cmd,
            ).pack(side="left", padx=spacing("label_gap") // 2)

    def _abrir_novo(self):
        def _salvar(dados):
            def _fetch():
                return self.controller.criar_template(dados)

            def _on_success(res):
                if isinstance(res, dict) and res.get("success") is False:
                    self._show_error(res.get("message", "Falha ao criar template."))
                    return
                self.carregar_templates_async()

            def _on_error(exc):
                self._show_error(f"Falha ao criar template: {exc}")

            AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

        TemplateFormModal(self, on_salvar=_salvar)

    def _abrir_editar(self, template):
        def _salvar(dados):
            def _fetch():
                return self.controller.atualizar_template(template.get("id"), dados)

            def _on_success(res):
                if isinstance(res, dict) and res.get("success") is False:
                    self._show_error(res.get("message", "Falha ao atualizar template."))
                    return
                self.carregar_templates_async()

            def _on_error(exc):
                self._show_error(f"Falha ao atualizar template: {exc}")

            AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

        TemplateFormModal(self, on_salvar=_salvar, template=template)

    def _preview(self, template):
        def _fetch():
            return self.controller.gerar_preview(template.get("id"))

        def _on_success(res):
            if isinstance(res, dict) and res.get("success") is False:
                self._show_error(res.get("message", "Falha ao gerar preview."))
                return
            data = res.get("data", {}) if isinstance(res, dict) else {}
            msg = "\n".join([f"{k}: {v}" for k, v in data.items()]) if data else "Preview vazio."
            self._show_success(msg, duration=5000)

        def _on_error(exc):
            self._show_error(f"Falha ao gerar preview: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _excluir(self, template):
        if not self._confirmar(f"Excluir template '{template.get('name')}'?"):
            return

        def _fetch():
            return self.controller.deletar_template(template.get("id"))

        def _on_success(res):
            if isinstance(res, dict) and res.get("success") is False:
                self._show_error(res.get("message", "Falha ao excluir template."))
                return
            self.carregar_templates_async()

        def _on_error(exc):
            self._show_error(f"Falha ao excluir template: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def load_data(self):
        self.carregar_templates_async()

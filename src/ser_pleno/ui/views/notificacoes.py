# -*- coding: utf-8 -*-
"""View de Notificacoes."""

from __future__ import annotations

import logging
import customtkinter as ctk

from ser_pleno.features.notificacoes.service import ServicoNotificacoes
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.components.ui_components import (
    Card, EmptyState, PrimaryButton, GhostButton, Divider, Badge, SkeletonLoader, Toast, BaseModal,
)
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder
from ser_pleno.ui.views.base import _ErrorModal

logger = logging.getLogger("apps.desktop")


class NotificacoesFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        import time as _time
        self._t0 = _time.perf_counter()
        super().__init__(master, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_notificacoes = ServicoNotificacoes(auth_service=getattr(controller, 'auth_service', None))
        self.app = getattr(controller, "app", None)
        self.notificacoes: list[dict] = []
        self._mostrar_nao_lidas = False

        self._build_filtros()
        self._build_header_actions()
        self._build_status_bar()

        self.lista = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.lista.pack(fill="both", expand=True, padx=spacing("xl"), pady=(0, spacing("xl")))

        self.carregar_notificacoes_async()
        log_view_init_ms("notificacoes", self._t0, widget_ref=self)

    def _build_filtros(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=spacing("xl"), pady=(spacing("lg"), spacing("sm")))

        self.f_filtro = ctk.CTkOptionMenu(
            frame,
            values=["Todas", "Nao lidas"],
            font=themed_font("body"),
            fg_color=THEME["primary_soft"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            text_color=THEME["primary"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            width=130,
            height=34,
            corner_radius=RADIUS["input"],
            command=self._aplicar_filtro,
        )
        self.f_filtro.pack(side="left")

    def _build_header_actions(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=spacing("xl"), pady=(0, spacing("sm")))

        PrimaryButton(
            bar, text=f"{ICONS['check']}  Marcar todas como lidas",
            command=self._marcar_todas_lidas,
            height=36, width=240,
        ).pack(side="left")

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.status_bar.pack(fill="x", padx=spacing("xl"), pady=(0, spacing("item_gap")))
        self.status_lbl = ctk.CTkLabel(
            self.status_bar, text="", font=font(size=12),
            text_color=THEME["text_muted"], anchor="w",
        )
        self.status_lbl.pack(side="left")

    def _aplicar_filtro(self, valor):
        self._mostrar_nao_lidas = valor == "Nao lidas"
        self.carregar_notificacoes_async()

    def _limpar_lista(self):
        try:
            if self.lista.winfo_exists():
                for w in self.lista.winfo_children():
                    w.destroy()
        except Exception:
            pass

    def _mostrar_skeletons(self):
        for _ in range(4):
            SkeletonLoader(self.lista, width=760, height=72, variant="card").pack(
                fill="x", pady=(0, 12)
            )

    def carregar_notificacoes_async(self):
        self._limpar_lista()
        self._mostrar_skeletons()
        self.status_lbl.configure(text="Carregando...")

        def _fetch():
            return self.servico_notificacoes.listar(unread_only=self._mostrar_nao_lidas)

        def _on_success(res):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            notificacoes = self._parse(res)
            self.notificacoes = notificacoes

            if not notificacoes:
                EmptyState(
                    self.lista,
                    icon=ICONS["empty"],
                    title="Nenhuma notificacao encontrada",
                    subtitle="Tente ajustar os filtros",
                ).pack(pady=30)
                self._atualizar_status(0)
                return

            batch = WidgetBatchBuilder(parent=self, batch_size=20)
            for n in notificacoes:
                if not isinstance(n, dict):
                    continue
                batch.add(lambda n=n: self._criar_card(n))
            batch.execute()
            self._atualizar_status(len(self.notificacoes))

        def _on_error(exc):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            EmptyState(
                self.lista,
                icon=ICONS["bolt"],
                title="Erro ao carregar notificacoes",
                subtitle=str(exc),
            ).pack(pady=20)
            self._atualizar_status(0)

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

    def _atualizar_status(self, total: int):
        self.status_lbl.configure(
            text=f"Mostrando {total} notificacoes"
        )

    def _criar_card(self, notificacao: dict):
        card = Card(self.lista)
        card.pack(fill="x", pady=(0, 12))

        body = card.body
        body.pack_configure(padx=(0, spacing("lg")), pady=spacing("md"))

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True)

        titulo = notificacao.get("titulo") or notificacao.get("title") or "(sem titulo)"
        mensagem = notificacao.get("mensagem") or notificacao.get("message") or ""

        ctk.CTkLabel(
            content, text=titulo,
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w", wraplength=600,
        ).pack(fill="x")

        if mensagem:
            ctk.CTkLabel(
                content, text=mensagem,
                font=themed_font("body_sm"),
                text_color=THEME["text_muted"], anchor="w", wraplength=600,
            ).pack(fill="x", pady=(spacing("xs"), 0))

        footer = ctk.CTkFrame(body, fg_color="transparent")
        footer.pack(fill="x", pady=(spacing("xs"), 0))

        data = notificacao.get("created_at") or ""
        if isinstance(data, str) and len(data) >= 10:
            data = data[:10]

        lida = notificacao.get("lida") or notificacao.get("is_read") or False
        badge_text = "Lida" if lida else "Nao lida"
        badge_color = THEME["text_muted"] if lida else THEME["info"]

        Badge(footer, text=badge_text, fg_color=badge_color, text_color=THEME["text_on_primary"]).pack(side="left")

        if data:
            ctk.CTkLabel(
                footer, text=f"{ICONS['clock']}  {data}",
                font=font(size=11),
                text_color=THEME["text_light"],
            ).pack(side="left", padx=(spacing("md"), 0))

        if not lida:
            GhostButton(
                footer, text=ICONS["check"],
                width=32, height=32, corner_radius=8,
                text_color=THEME["success"],
                command=lambda n=notificacao: self._marcar_lida(n),
            ).pack(side="right", padx=(spacing("sm"), 0))

    def _marcar_lida(self, notificacao):
        nid = notificacao.get("id") or notificacao.get("notification_id")
        if not nid:
            return

        def _fetch():
            return self.servico_notificacoes.marcar_lida(nid)

        def _on_success(res):
            if isinstance(res, dict) and res.get("success") is False:
                self._show_error(res.get("message", "Erro ao marcar como lida"))
                return
            self.carregar_notificacoes_async()

        def _on_error(exc):
            self._show_error(f"Erro ao marcar como lida: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _marcar_todas_lidas(self):
        def _fetch():
            return self.servico_notificacoes.marcar_todas_lidas()

        def _on_success(res):
            if isinstance(res, dict) and res.get("success") is False:
                self._show_error(res.get("message", "Erro ao marcar todas como lidas"))
                return
            self.carregar_notificacoes_async()

        def _on_error(exc):
            self._show_error(f"Erro ao marcar todas como lidas: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _show_error(self, message: str, title: str = "Nao foi possivel concluir") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _show_success(self, message: str, duration: int = 3000) -> None:
        try:
            if hasattr(self, "_toast") and self._toast and self._toast.winfo_exists():
                self._toast.destroy()
            self._toast = Toast(self.winfo_toplevel(), message=message, status="success", duration=duration)
        except Exception:
            pass

    def _confirmar(self, mensagem: str) -> bool:
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)
        w, h = 420, 200
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        resultado = {"ok": False}
        ctk.CTkLabel(modal, text=mensagem,
                     font=themed_font("h4", "bold"),
                     text_color=THEME["text"],
                     wraplength=360, justify="center").pack(pady=(24, 16))
        botoes = ctk.CTkFrame(modal, fg_color="transparent")
        botoes.pack(pady=(0, 20))
        ctk.CTkButton(botoes, text="Cancelar", width=110, height=36,
                      fg_color=THEME["bg_alt"], hover_color=THEME["border"],
                      text_color=THEME["text"],
                      command=lambda: modal.destroy()).pack(side="left", padx=(0, 8))
        ctk.CTkButton(botoes, text="Confirmar", width=110, height=36,
                      fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
                      text_color=THEME["text_on_primary"],
                      command=lambda: self._confirmar_callback(modal, resultado)).pack(side="right")
        modal.wait_window(modal)
        return resultado.get("ok", False)

    def _confirmar_callback(self, modal: ctk.CTkToplevel, resultado: dict):
        resultado["ok"] = True
        modal.destroy()

    def load_data(self):
        self.carregar_notificacoes_async()

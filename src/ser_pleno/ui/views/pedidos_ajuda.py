# -*- coding: utf-8 -*-
"""View de Pedidos de Ajuda."""

from __future__ import annotations

import logging
import time
from typing import Optional

import customtkinter as ctk

from ser_pleno.ui.theme import THEME, SPACING, RADIUS, themed_font
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.views.base import BaseViewFrame
from ser_pleno.ui.components.ui_components import (
    BaseModal,
    Card,
    EmptyState,
    SkeletonLoader,
    SecondaryButton,
    PrimaryButton,
    GhostButton,
    SegmentedButton,
    Toast,
)
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder
from ser_pleno.features.pedidos_ajuda.service import ServicoPedidosAjuda

logger = logging.getLogger("apps.desktop")


class ResponderModal(BaseModal):
    """Modal para responder a um pedido de ajuda."""

    def __init__(self, parent, pedido_id, on_enviar, on_cancel):
        self.pedido_id = pedido_id
        self.on_enviar = on_enviar
        self.on_cancel = on_cancel
        super().__init__(parent, title="Responder Pedido de Ajuda", width=520, height=420)
        self.configure(fg_color=THEME["surface"])
        self._build()

    def _build(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=f"{ICONS['message']}  Resposta",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        preset_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
        preset_frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            preset_frame,
            text="Respostas rápidas:",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))

        presets_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        presets_row.pack(fill="x", pady=(0, 12))

        for texto_preset in PedidosAjudaFrame.RESPOSTAS_PRESET:
            GhostButton(
                presets_row,
                text=texto_preset,
                command=lambda t=texto_preset: self._usar_preset(t),
                width=200,
                height=30,
            ).pack(side="left", padx=(0, 8))

        self.f_resposta = ctk.CTkTextbox(
            wrapper,
            height=100,
            fg_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
            text_color=THEME["text"],
        )
        self.f_resposta.pack(fill="x", pady=(0, 16))

        footer = ctk.CTkFrame(wrapper, fg_color="transparent")
        footer.pack(fill="x")

        SecondaryButton(
            footer,
            text="Cancelar",
            command=self._cancelar,
            width=120,
            height=38,
        ).pack(side="left")

        self._btn_enviar = PrimaryButton(
            footer,
            text=f"{ICONS['send']}  Enviar Resposta",
            command=self._enviar,
            width=180,
            height=38,
        )
        self._btn_enviar.pack(side="right")

        self.f_resposta.bind("<KeyRelease>", self._on_key)
        self._update_enviar_state()

    def _usar_preset(self, texto: str):
        self.f_resposta.delete("1.0", "end")
        self.f_resposta.insert("1.0", texto)
        self._update_enviar_state()

    def _on_key(self, _=None):
        self._update_enviar_state()

    def _update_enviar_state(self):
        texto = self.f_resposta.get("1.0", "end").strip()
        estado = "normal" if texto else "disabled"
        try:
            self._btn_enviar.configure(state=estado)
        except Exception:
            pass

    def _enviar(self):
        resposta = self.f_resposta.get("1.0", "end").strip()
        if not resposta:
            return
        self._btn_enviar.configure(state="disabled")
        if self.on_enviar:
            self.on_enviar(self.pedido_id, resposta)

    def _cancelar(self):
        try:
            self._btn_enviar.configure(state="normal")
        except Exception:
            pass
        if self.on_cancel:
            self.on_cancel()
        self.close()

    def close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


class PedidosAjudaFrame(BaseViewFrame):
    """Frame principal de Pedidos de Ajuda."""

    STATUS_OPCOES = ["Todos", "pending", "viewed", "in_progress", "resolved"]

    STATUS_LABELS = {
        "Todos": "Todos",
        "pending": "Pendentes",
        "viewed": "Vistos",
        "in_progress": "Em Atendimento",
        "resolved": "Resolvidos",
    }

    STATUS_COLORS_MAP = {
        "pending": THEME["warning"],
        "viewed": THEME["info"],
        "in_progress": THEME["primary"],
        "resolved": THEME["success"],
    }

    RESPOSTAS_PRESET = [
        "Estou livre, pode vir",
        "Aguarde, estou em atendimento",
        "Já estou a caminho",
        "Mantenha-se no local, por favor",
    ]

    def __init__(self, parent, controller):
        self._t0 = time.perf_counter()
        super().__init__(
            parent,
            controller,
            title="Pedidos de Ajuda",
            subtitle="Solicitacoes de suporte e acompanhamento",
            auto_header=True,
        )
        self.controller = controller
        self.servico_pedidos = ServicoPedidosAjuda(
            auth_service=getattr(controller, "auth_service", None),
        )
        self.app = getattr(controller, "app", None)

        self.pedidos: list[dict] = []
        self._filtro_status: str = "Todos"
        self._polling_job: Optional[str] = None
        self._ultimo_count_pendentes: int = 0

        self._build_filtros()
        self._build_status_bar()

        self._cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self._cards_container.pack(
            fill="both",
            expand=True,
            padx=SPACING["page_x"],
            pady=(0, SPACING["page_y"]),
        )

        self._modal_responder: Optional[ResponderModal] = None

        self.after(100, self._iniciar_polling)
        self.carregar_pedidos_async()
        log_view_init_ms("pedidos_ajuda", self._t0, widget_ref=self)

    def _build_filtros(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(
            fill="x",
            padx=SPACING["page_x"],
            pady=(SPACING["item_gap"], SPACING["label_gap"]),
        )

        self.seg_status = SegmentedButton(
            frame,
            options=[self.STATUS_LABELS.get(s, s) for s in self.STATUS_OPCOES],
            on_change=self._on_mudar_filtro,
            initial=0,
        )
        self.seg_status.pack(side="left")

        ctk.CTkFrame(frame, fg_color="transparent", width=16).pack(side="left")

        SecondaryButton(
            frame,
            text=f"{ICONS['search']}  Atualizar",
            command=self.carregar_pedidos_async,
            width=140,
            height=36,
        ).pack(side="right")

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.status_bar.pack(fill="x", padx=SPACING["page_x"], pady=(0, SPACING["label_gap"]))
        self.status_lbl = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=themed_font("body_sm"),
            text_color=THEME["text_muted"],
            anchor="w",
        )
        self.status_lbl.pack(side="left")

        self.notificacao_lbl = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=themed_font("caption", "bold"),
            text_color=THEME["danger"],
            anchor="e",
        )
        self.notificacao_lbl.pack(side="right")

    def _on_mudar_filtro(self, idx: int):
        self._filtro_status = self.STATUS_OPCOES[idx]
        self.carregar_pedidos_async()

    def _get_status_filtro(self) -> Optional[str]:
        return None if self._filtro_status == "Todos" else self._filtro_status

    def _iniciar_polling(self):
        if self._polling_job:
            try:
                self.after_cancel(self._polling_job)
            except Exception:
                pass
        self._verificar_novos_pedidos()

    def _parar_polling(self):
        if self._polling_job:
            try:
                self.after_cancel(self._polling_job)
            except Exception:
                pass
            self._polling_job = None

    def _verificar_novos_pedidos(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        try:
            count = self.servico_pedidos.contar_pendentes()
            if isinstance(count, dict):
                count = count.get("data", 0) if count.get("success") else 0
            if not isinstance(count, int):
                count = 0

            if count > 0 and count != self._ultimo_count_pendentes:
                self._ultimo_count_pendentes = count
                Toast(
                    self,
                    f"{count} novo(s) pedido(s) de ajuda aguardando atendimento",
                    status="warning",
                    duration=5000,
                )
                self.notificacao_lbl.configure(text=f"{count} pendentes")
            elif count == 0:
                self.notificacao_lbl.configure(text="")

        except Exception as e:
            logger.debug("Erro ao verificar novos pedidos: %s", e)

        try:
            self._polling_job = self.after(30000, self._verificar_novos_pedidos)
        except Exception:
            pass

    def destroy(self):
        self._parar_polling()
        try:
            super().destroy()
        except Exception:
            pass

    def carregar_pedidos_async(self):
        self._limpar_lista()
        self._mostrar_skeletons()
        self.status_lbl.configure(text="Carregando...")

        def _fetch():
            return self.servico_pedidos.listar_pedidos(status=self._get_status_filtro())

        def _on_success(res):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            pedidos = self._parse_pedidos(res)
            self.pedidos = pedidos

            if not pedidos:
                EmptyState(
                    self._cards_container,
                    icon=ICONS["empty"],
                    title="Nenhum pedido encontrado",
                    subtitle="Nenhum pedido corresponde aos filtros selecionados",
                ).pack(pady=30)
                self._atualizar_status(0, 0)
                return

            batch = WidgetBatchBuilder(parent=self, batch_size=20)
            for pedido in pedidos:
                if not isinstance(pedido, dict):
                    continue
                batch.add(lambda p=pedido: self._criar_card(p))
            batch.execute()
            self._atualizar_status(len(pedidos), len(pedidos))

            pendentes = sum(1 for p in pedidos if p.get("status") == "pending")
            if pendentes > 0:
                self.notificacao_lbl.configure(text=f"{pendentes} pendentes")
                self._ultimo_count_pendentes = pendentes

        def _on_error(exc):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            EmptyState(
                self._cards_container,
                icon=ICONS["bolt"],
                title="Erro ao carregar pedidos",
                subtitle=str(exc),
            ).pack(pady=20)
            self._atualizar_status(0, 0)

        AsyncRunner.run(
            task=_fetch,
            on_success=_on_success,
            on_error=_on_error,
            widget_ref=self,
        )

    def _mostrar_skeletons(self):
        for _ in range(4):
            SkeletonLoader(self._cards_container, width=760, height=80, variant="card").pack(
                fill="x", pady=(0, 12)
            )

    def _limpar_lista(self):
        try:
            if self._cards_container.winfo_exists():
                for w in self._cards_container.winfo_children():
                    w.destroy()
        except Exception:
            pass

    def _atualizar_status(self, total: int, filtrados: int):
        self.status_lbl.configure(
            text=f"Mostrando {filtrados} de {total} pedidos"
        )

    def _parse_pedidos(self, res) -> list[dict]:
        if isinstance(res, dict):
            if res.get("success") is False:
                return []
            if "data" in res and isinstance(res["data"], list):
                return res["data"]
            if res.get("id"):
                return [res]
        if isinstance(res, list):
            return res
        return []

    def _criar_card(self, pedido: dict):
        pedido_id = pedido.get("id")
        status = pedido.get("status", "pending")
        tipo = pedido.get("type", "suporte")
        mensagem = pedido.get("message", "")
        prioridade = pedido.get("priority", "media")
        localizacao = pedido.get("location", "")
        created_at = pedido.get("created_at", "")
        extra = pedido.get("extra_data") or {}
        resposta = extra.get("resposta") or ""
        aluno_nome = pedido.get("student_name", "")
        aluno_curso = pedido.get("student_course", "")
        aluno_sala = pedido.get("student_class", "")

        card = Card(self._cards_container, status=status)
        card.pack(fill="x", pady=(0, 12))

        body = card.body
        body.pack_configure(padx=(SPACING["md"], SPACING["lg"]), pady=SPACING["md"])

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(fill="both", expand=True)

        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x", pady=(0, SPACING["item_gap"]))

        ctk.CTkLabel(
            top,
            text=tipo.capitalize(),
            font=themed_font("overline", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(side="left")

        prioridade_color = THEME["danger"] if prioridade == "alta" else (
            THEME["warning"] if prioridade == "media" else THEME["success"]
        )
        ctk.CTkLabel(
            top,
            text=prioridade.upper(),
            font=themed_font("overline", "bold"),
            text_color=prioridade_color,
        ).pack(side="left", padx=(SPACING["sm"], 0))

        ctk.CTkLabel(
            top,
            text=self._formatar_data(created_at),
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        ).pack(side="right")

        if aluno_nome:
            ctk.CTkLabel(
                content,
                text=f"{ICONS['user']}  {aluno_nome}",
                font=themed_font("body_sm", "bold"),
                text_color=THEME["text"],
                anchor="w",
            ).pack(anchor="w", pady=(0, 2))

            aluno_info_parts = []
            if aluno_curso:
                aluno_info_parts.append(aluno_curso)
            if aluno_sala:
                aluno_info_parts.append(f"Sala: {aluno_sala}")
            if aluno_info_parts:
                ctk.CTkLabel(
                    content,
                    text="  ·  ".join(aluno_info_parts),
                    font=themed_font("caption"),
                    text_color=THEME["text_muted"],
                    anchor="w",
                ).pack(anchor="w", pady=(0, SPACING["xs"]))

        if mensagem:
            ctk.CTkLabel(
                content,
                text=mensagem,
                wraplength=720,
                justify="left",
                font=themed_font("body"),
                text_color=THEME["text"],
                anchor="w",
            ).pack(anchor="w", pady=(0, SPACING["xs"]))

        if localizacao:
            ctk.CTkLabel(
                content,
                text=f"{ICONS['location']} {localizacao}",
                font=themed_font("caption"),
                text_color=THEME["text_muted"],
                anchor="w",
            ).pack(anchor="w", pady=(0, SPACING["xs"]))

        if resposta:
            ctk.CTkLabel(
                content,
                text=f"{ICONS['message']} {resposta}",
                wraplength=720,
                justify="left",
                font=themed_font("body_sm"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).pack(anchor="w", pady=(0, SPACING["xs"]))

        ctk.CTkFrame(content, height=1, fg_color=THEME["divider"]).pack(
            fill="x", pady=(SPACING["xs"], 8),
        )

        acts = ctk.CTkFrame(content, fg_color="transparent")
        acts.pack(fill="x")

        if status == "pending":
            SecondaryButton(
                acts,
                text=f"{ICONS['view']}  Marcar Visto",
                command=lambda pid=pedido_id: self._acao_marcar_visto(pid),
                width=140,
                height=32,
            ).pack(side="left", padx=(0, 8))
            PrimaryButton(
                acts,
                text=f"{ICONS['check']}  Iniciar Atendimento",
                command=lambda pid=pedido_id: self._acao_iniciar(pid),
                width=180,
                height=32,
            ).pack(side="left")
        elif status == "viewed":
            PrimaryButton(
                acts,
                text=f"{ICONS['check']}  Iniciar Atendimento",
                command=lambda pid=pedido_id: self._acao_iniciar(pid),
                width=180,
                height=32,
            ).pack(side="left", padx=(0, 8))
            PrimaryButton(
                acts,
                text=f"{ICONS['check_circle']}  Resolver",
                command=lambda pid=pedido_id: self._acao_resolver(pid),
                width=140,
                height=32,
            ).pack(side="left")
        elif status == "in_progress":
            PrimaryButton(
                acts,
                text=f"{ICONS['check_circle']}  Resolver",
                command=lambda pid=pedido_id: self._acao_resolver(pid),
                width=140,
                height=32,
            ).pack(side="left", padx=(0, 8))
            SecondaryButton(
                acts,
                text=f"{ICONS['message']}  Responder",
                command=lambda pid=pedido_id: self._acao_responder(pid),
                width=140,
                height=32,
            ).pack(side="left")
        elif status == "resolved":
            SecondaryButton(
                acts,
                text=f"{ICONS['message']}  Responder",
                command=lambda pid=pedido_id: self._acao_responder(pid),
                width=140,
                height=32,
            ).pack(side="left")

    def _formatar_data(self, data_str: str) -> str:
        if not data_str:
            return ""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            return data_str

    def _acao_marcar_visto(self, pedido_id):
        def _fetch():
            return self.servico_pedidos.marcar_visto(pedido_id)

        def _on_success(res):
            if isinstance(res, dict) and res.get("success"):
                Toast(self, "Pedido marcado como visto", status="success", duration=2500)
                self.carregar_pedidos_async()
            else:
                self._show_error(str(res.get("message", "Erro ao marcar visto")))

        def _on_error(exc):
            self._show_error(f"Erro: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _acao_iniciar(self, pedido_id):
        def _fetch():
            return self.servico_pedidos.iniciar_atendimento(pedido_id)

        def _on_success(res):
            if isinstance(res, dict) and res.get("success"):
                Toast(self, "Atendimento iniciado", status="success", duration=2500)
                self.carregar_pedidos_async()
            else:
                self._show_error(str(res.get("message", "Erro ao iniciar atendimento")))

        def _on_error(exc):
            self._show_error(f"Erro: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _acao_resolver(self, pedido_id):
        def _fetch():
            return self.servico_pedidos.resolver_pedido(pedido_id)

        def _on_success(res):
            if isinstance(res, dict) and res.get("success"):
                Toast(self, "Pedido resolvido", status="success", duration=2500)
                self.carregar_pedidos_async()
            else:
                self._show_error(str(res.get("message", "Erro ao resolver pedido")))

        def _on_error(exc):
            self._show_error(f"Erro: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _acao_responder(self, pedido_id):
        if self._modal_responder is not None:
            try:
                self._modal_responder.destroy()
            except Exception:
                pass

        self._modal_responder = ResponderModal(
            self.winfo_toplevel(),
            pedido_id=pedido_id,
            on_enviar=self._on_responder_enviar,
            on_cancel=self._on_responder_cancelar,
        )
        self._modal_responder.show()

    def _on_responder_enviar(self, pedido_id, resposta):
        def _fetch():
            return self.servico_pedidos.responder_pedido(pedido_id, resposta)

        def _on_success(res):
            if isinstance(res, dict) and res.get("success"):
                Toast(self, "Resposta enviada com sucesso", status="success", duration=3000)
                self.carregar_pedidos_async()
            else:
                self._show_error(str(res.get("message", "Erro ao enviar resposta")))

        def _on_error(exc):
            self._show_error(f"Erro: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)
        try:
            self._modal_responder.destroy()
        except Exception:
            pass
        self._modal_responder = None

    def _on_responder_cancelar(self):
        self._modal_responder = None

    def load_data(self):
        self.carregar_pedidos_async()

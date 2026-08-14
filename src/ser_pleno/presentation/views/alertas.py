# -*- coding: utf-8 -*-
"""View de Alertas Avancados."""

from __future__ import annotations

import logging
import customtkinter as ctk
from ser_pleno.application.controllers.alertas import AlertasController
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.presentation.components.ui_components import (
    Card, EmptyState, PrimaryButton, SecondaryButton, GhostButton,
    Divider, Badge, SkeletonLoader, Dropdown, BaseModal,
)
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger("apps.desktop")

_TIPOS_ALERTA = [
    "screening_pending", "appointment_reminder", "followup_required",
    "high_risk", "missed_appointment", "system", "academic", "emotional", "social",
]
_SEVERIDADES = ["info", "warning", "error", "critical"]
_STATUS_LEITURA = ["Todos", "Lidos", "Nao lidos"]
_STATUS_RESOLUCAO = ["Todos", "Resolvidos", "Pendentes"]

_LABEL_TIPOS = {
    "screening_pending": "Triagem Pendente",
    "appointment_reminder": "Lembrete de Consulta",
    "followup_required": "Acompanhamento Necessario",
    "high_risk": "Alto Risco",
    "missed_appointment": "Falta em Consulta",
    "system": "Alerta do Sistema",
    "academic": "Academico",
    "emotional": "Emocional",
    "social": "Social",
}
_LABEL_SEVERIDADES = {
    "info": "Informativo",
    "warning": "Atencao",
    "error": "Erro",
    "critical": "Critico",
}
_COR_SEVERIDADE = {
    "info": THEME["info"],
    "warning": THEME["warning"],
    "error": THEME["danger"],
    "critical": THEME["danger"],
}
_SOFT_SEVERIDADE = {
    "info": THEME["info_soft"],
    "warning": THEME["warning_soft"],
    "error": THEME["danger_soft"],
    "critical": THEME["danger_soft"],
}


def _formatar_tipo(t: str) -> str:
    return _LABEL_TIPOS.get(t, t.replace("_", " ").title() if t else "Alerta")


def _formatar_severidade(s: str) -> str:
    return _LABEL_SEVERIDADES.get(s, s.title() if s else "Info")


class AlertasFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        import time as _time
        self._t0 = _time.perf_counter()
        super().__init__(master, fg_color=THEME["bg"])
        self.controller = controller
        self.app = getattr(controller, "app", None)
        self.alertas: list[dict] = []
        self._filtros = {
            "alert_type": None,
            "severity": None,
            "is_read": None,
            "is_resolved": None,
            "data_inicio": None,
            "data_fim": None,
        }
        self._total_alertas = 0

        self._build_filtros()
        self._build_status_bar()
        self._build_action_bar()

        self.lista = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.lista.pack(fill="both", expand=True, padx=spacing("xl"), pady=(0, spacing("xl")))

        self._inicializar_badge()
        self.carregar_alertas_async()
        log_view_init_ms("alertas", self._t0, widget_ref=self)

    def _build_filtros(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=spacing("xl"), pady=(spacing("lg"), spacing("sm")))

        tipos = ["Todos"] + [_formatar_tipo(t) for t in _TIPOS_ALERTA]
        self.f_tipo = Dropdown(frame, values=tipos, initial="Todos", width=150,
                                command=lambda _: self._aplicar_filtros_auto())
        self.f_tipo.pack(side="left", padx=(0, spacing("sm")))

        sevs = ["Todas"] + [_formatar_severidade(s) for s in _SEVERIDADES]
        self.f_severidade = Dropdown(frame, values=sevs, initial="Todas", width=130,
                                      command=lambda _: self._aplicar_filtros_auto())
        self.f_severidade.pack(side="left", padx=(0, spacing("sm")))

        self.f_leitura = Dropdown(frame, values=_STATUS_LEITURA, initial="Todos", width=110,
                                   command=lambda _: self._aplicar_filtros_auto())
        self.f_leitura.pack(side="left", padx=(0, spacing("sm")))

        self.f_resolucao = Dropdown(frame, values=_STATUS_RESOLUCAO, initial="Todos", width=120,
                                     command=lambda _: self._aplicar_filtros_auto())
        self.f_resolucao.pack(side="left", padx=(0, spacing("sm")))

        ctk.CTkLabel(frame, text="De", font=font(size=12),
                     text_color=THEME["text_muted"]).pack(side="left", padx=(spacing("md"), 4))
        self.f_data_inicio = ctk.CTkEntry(
            frame, placeholder_text="YYYY-MM-DD", width=100, height=36,
            fg_color=THEME["input_bg"], border_width=1, border_color=THEME["input_border"],
            font=font(size=12), text_color=THEME["text"],
        )
        self.f_data_inicio.pack(side="left", padx=(0, spacing("xs")))

        ctk.CTkLabel(frame, text="Ate", font=font(size=12),
                     text_color=THEME["text_muted"]).pack(side="left", padx=(spacing("sm"), 4))
        self.f_data_fim = ctk.CTkEntry(
            frame, placeholder_text="YYYY-MM-DD", width=100, height=36,
            fg_color=THEME["input_bg"], border_width=1, border_color=THEME["input_border"],
            font=font(size=12), text_color=THEME["text"],
        )
        self.f_data_fim.pack(side="left", padx=(0, spacing("sm")))

        SecondaryButton(
            frame, text="Limpar filtros", command=self._limpar_filtros,
            width=120, height=36,
        ).pack(side="left", padx=(spacing("md"), 0))

        for w in (self.f_data_inicio, self.f_data_fim):
            w.bind("<KeyRelease>", lambda _: self._aplicar_filtros_auto())

    def _build_action_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=spacing("xl"), pady=(0, spacing("sm")))

        PrimaryButton(
            bar, text=f"{ICONS['check']}  Marcar todos como lidos",
            command=self._marcar_todos_lidos,
            height=36, width=220,
        ).pack(side="left")

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.status_bar.pack(fill="x", padx=spacing("xl"), pady=(0, spacing("item_gap")))
        self.status_lbl = ctk.CTkLabel(
            self.status_bar, text="", font=font(size=12),
            text_color=THEME["text_muted"], anchor="w",
        )
        self.status_lbl.pack(side="left")

    def _limpar_filtros(self):
        self.f_tipo.set("Todos")
        self.f_severidade.set("Todas")
        self.f_leitura.set("Todos")
        self.f_resolucao.set("Todos")
        self.f_data_inicio.delete(0, "end")
        self.f_data_fim.delete(0, "end")
        self._filtros = {
            "alert_type": None, "severity": None,
            "is_read": None, "is_resolved": None,
            "data_inicio": None, "data_fim": None,
        }
        self.carregar_alertas_async()

    def _aplicar_filtros_auto(self):
        tipo_raw = self.f_tipo.get()
        sev_raw = self.f_severidade.get()
        leitura_raw = self.f_leitura.get()
        resolucao_raw = self.f_resolucao.get()

        tipo_map = {v: k for k, v in _LABEL_TIPOS.items()}
        sev_map = {v: k for k, v in _LABEL_SEVERIDADES.items()}

        is_read = None
        if leitura_raw == "Lidos":
            is_read = True
        elif leitura_raw == "Nao lidos":
            is_read = False

        is_resolved = None
        if resolucao_raw == "Resolvidos":
            is_resolved = True
        elif resolucao_raw == "Pendentes":
            is_resolved = False

        self._filtros = {
            "alert_type": tipo_map.get(tipo_raw) if tipo_raw != "Todos" else None,
            "severity": sev_map.get(sev_raw) if sev_raw != "Todas" else None,
            "is_read": is_read,
            "is_resolved": is_resolved,
            "data_inicio": self.f_data_inicio.get().strip() or None,
            "data_fim": self.f_data_fim.get().strip() or None,
        }
        self.carregar_alertas_async()

    def _atualizar_status(self, total: int, filtrados: int):
        if filtrados == total:
            self.status_lbl.configure(
                text=f"{total} alerta{'s' if total != 1 else ''}"
            )
        else:
            self.status_lbl.configure(
                text=f"Mostrando {filtrados} de {total} alertas"
            )

    def carregar_alertas_async(self):
        self._limpar_lista()
        self._mostrar_skeletons()
        self.status_lbl.configure(text="Carregando...")

        service = self.controller.get_service()

        def _fetch():
            return service.listar_alertas(filters=self._filtros)

        def _on_success(res):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            alertas = self._parse_alertas(res)
            self.alertas = alertas

            if not alertas:
                EmptyState(
                    self.lista,
                    icon=ICONS["empty"],
                    title="Nenhum alerta encontrado",
                    subtitle="Tente ajustar os filtros",
                ).pack(pady=30)
                self._atualizar_status(0, 0)
                self._atualizar_badge_navegacao(0)
                return

            batch = WidgetBatchBuilder(parent=self, batch_size=20)
            for alerta in alertas:
                if not isinstance(alerta, dict):
                    continue
                batch.add(lambda a=alerta: self._criar_card(a))
            batch.execute()
            self._atualizar_status(len(self.alertas), len(self.alertas))
            self._atualizar_badge_navegacao(
                sum(1 for a in self.alertas if not a.get("is_read"))
            )

        def _on_error(exc):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            EmptyState(
                self.lista,
                icon=ICONS["bolt"],
                title="Erro ao carregar alertas",
                subtitle=str(exc),
            ).pack(pady=20)
            self._atualizar_status(0, 0)

        AsyncRunner.run(
            task=_fetch,
            on_success=_on_success,
            on_error=_on_error,
            widget_ref=self,
        )

    def _parse_alertas(self, res) -> list[dict]:
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

    def _mostrar_skeletons(self):
        for _ in range(5):
            SkeletonLoader(self.lista, width=760, height=80, variant="card").pack(
                fill="x", pady=(0, 12)
            )

    def _limpar_lista(self):
        try:
            if self.lista.winfo_exists():
                for w in self.lista.winfo_children():
                    w.destroy()
        except Exception:
            pass

    def _criar_card(self, alerta: dict):
        card = Card(self.lista)
        card.pack(fill="x", pady=(0, 12))

        severity = (alerta.get("severity") or "info").lower()
        cor = _COR_SEVERIDADE.get(severity, THEME["info"])
        soft = _SOFT_SEVERIDADE.get(severity, THEME["info_soft"])
        is_critical = severity == "critical"
        body = card.body
        body.pack_configure(padx=(0, spacing("lg")), pady=spacing("md"))

        border_w = 6 if is_critical else 4
        ctk.CTkFrame(body, width=border_w, corner_radius=0, fg_color=cor).pack(
            side="left", fill="y"
        )

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=(4, 0))

        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x", pady=(0, spacing("item_gap")))

        tipo = alerta.get("alert_type") or "system"
        chip_frame = ctk.CTkFrame(top, fg_color=soft, corner_radius=6)
        chip_frame.pack(side="left", padx=(0, spacing("md")))
        ctk.CTkLabel(
            chip_frame, text=_formatar_tipo(tipo),
            font=font(size=10, weight="bold"), text_color=cor,
        ).pack(padx=spacing("sm"), pady=spacing("xs"))

        if is_critical:
            critico_frame = ctk.CTkFrame(top, fg_color=THEME["danger_soft"], corner_radius=6)
            critico_frame.pack(side="left", padx=(0, spacing("sm")))
            ctk.CTkLabel(
                critico_frame, text="CRITICO",
                font=font(size=9, weight="bold"), text_color=THEME["danger"],
            ).pack(padx=spacing("sm"), pady=spacing("xs"))

        msg_lbl = ctk.CTkLabel(
            top, text=alerta.get("message") or "(sem mensagem)",
            font=font(size=13, weight="bold"),
            text_color=THEME["text"], anchor="w", wraplength=600,
        )
        msg_lbl.pack(side="left", fill="x", expand=True)

        acts = ctk.CTkFrame(top, fg_color="transparent")
        acts.pack(side="right")

        if not alerta.get("is_read"):
            ctk.CTkButton(
                acts, text=ICONS["check"],
                command=lambda a=alerta: self._marcar_lido(a),
                width=32, height=32, corner_radius=8,
                fg_color=THEME["success_soft"], hover_color=THEME["success"],
                text_color=THEME["success"], font=font(size=13),
            ).pack(side="left", padx=(0, 4))

        if not alerta.get("is_resolved"):
            ctk.CTkButton(
                acts, text=ICONS["cross"],
                command=lambda a=alerta: self._dispensar(a),
                width=32, height=32, corner_radius=8,
                fg_color=THEME["danger_soft"], hover_color=THEME["danger"],
                text_color=THEME["danger"], font=font(size=13),
            ).pack(side="left")

        footer = ctk.CTkFrame(content, fg_color="transparent")
        footer.pack(fill="x")

        data = alerta.get("created_at") or ""
        if isinstance(data, str) and len(data) >= 10:
            data = data[:10]

        student_id = alerta.get("student_id")
        student_label = f"Estudante #{student_id}" if student_id else ""

        for icon, val in [
            (ICONS["clock"], data),
            (ICONS["user"], student_label),
            (ICONS["view"], f"ID {alerta.get('id', '')}"),
        ]:
            if val:
                lbl_row = ctk.CTkFrame(footer, fg_color="transparent")
                lbl_row.pack(side="left", padx=(0, 12))
                ctk.CTkLabel(
                    lbl_row, text=f"{icon}  {val}",
                    font=font(size=11),
                    text_color=THEME["text_light"],
                ).pack(side="left")

    def _marcar_lido(self, alerta):
        def _fetch():
            return self.controller.marcar_alerta_lido(alerta.get("id"))

        def _on_success(res):
            if isinstance(res, dict) and res.get("success") is False:
                self._show_error(res.get("message", "Erro ao marcar como lido"))
                return
            self.carregar_alertas_async()

        def _on_error(exc):
            self._show_error(f"Erro ao marcar como lido: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _dispensar(self, alerta):
        def _fetch():
            return self.controller.dispensar_alerta(alerta.get("id"))

        def _on_success(res):
            if isinstance(res, dict) and res.get("success") is False:
                self._show_error(res.get("message", "Erro ao dispensar alerta"))
                return
            self.carregar_alertas_async()

        def _on_error(exc):
            self._show_error(f"Erro ao dispensar alerta: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _marcar_todos_lidos(self):
        def _fetch():
            return self.controller.marcar_todos_lidos()

        def _on_success(res):
            if isinstance(res, dict) and res.get("success") is False:
                self._show_error(res.get("message", "Erro ao marcar todos como lidos"))
                return
            self.carregar_alertas_async()

        def _on_error(exc):
            self._show_error(f"Erro ao marcar todos como lidos: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _inicializar_badge(self):
        def fetch():
            service = self.controller.get_service()
            return service.contar_nao_lidos()

        def on_success(count):
            if not self.winfo_exists():
                return
            self._atualizar_badge_navegacao(count)

        def on_error(exc):
            logger.error("Erro ao inicializar badge de alertas: %s", exc)

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _atualizar_badge_navegacao(self, count: int):
        app = getattr(self.controller, "app", None)
        if app and hasattr(app, "navigation"):
            try:
                app.navigation.update_alert_badge(count)
            except Exception:
                pass

    def _show_error(self, message: str, title: str = "Nao foi possivel concluir") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

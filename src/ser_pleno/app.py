from __future__ import annotations

import logging
import os
import sys
import time

import customtkinter as ctk

from ser_pleno.config.paths import get_project_root

base_dir = get_project_root()

_env_path = os.path.join(base_dir, ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if not _line or _line.startswith("#") or "=" not in _line:
                continue
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from ser_pleno.utils.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

from ser_pleno.infrastructure.api.connectivity import atualizar_disponibilidade_api_async
from ser_pleno.infrastructure.api.sync_service import get_sync_service
from ser_pleno.ui.components.ui_components import (
    Avatar,
    Badge,
    Card,
    Divider,
    EmptyState,
    GhostButton,
    KPICard,
    PageHeader,
    PrimaryButton,
    SecondaryButton,
    SectionHeader,
    SkeletonLoader,
    Tooltip,
    blend_color,
)
from ser_pleno.ui.navigation import NavigationManager
from ser_pleno.ui.theme_manager import ThemeManager
from ser_pleno.ui.views.login import LoginFrame
from ser_pleno.ui.components.onboarding_tour import OnboardingTourController
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.theme import (
    ELEVATION,
    RADIUS,
    SPACING,
    THEME,
    apply_global_style,
    font,
    get_mode,
    on_theme_change,
    themed_font,
    toggle_mode,
)
from ser_pleno.infrastructure.desktop.native_notifier import get_desktop_notifier
from ser_pleno.application.services.bootstrap import BootstrapService
from ser_pleno.features.agenda.service import ServicoAgendamento
from ser_pleno.features.estudantes.service import ServicoEstudante
from ser_pleno.features.orientacoes.service import ServicoOrientacoes
from ser_pleno.features.triagem.service import ServicoTriagem
from ser_pleno.features.bem_estar.service import ServicoBemEstar
from ser_pleno.features.alertas.service import ServicoAlertas
from ser_pleno.features.dashboard.service import ServicoDashboard
from ser_pleno.features.analytics.service import ServicoAnalytics
from ser_pleno.features.interventions.service import ServicoIntervencoes
from ser_pleno.features.metas.service import ServicoMetas
from ser_pleno.features.wellness_challenges.service import ServicoWellnessChallenges
from ser_pleno.features.configuracoes.service import ServicoConfiguracoes
from ser_pleno.features.notificacoes.service import ServicoNotificacoes
from ser_pleno.features.relatorio.service import ServicoRelatorio
from ser_pleno.features.report_template.service import ServicoReportTemplate
from ser_pleno.application.services.mural import ServicoMural
from ser_pleno.features.pedidos_ajuda.service import ServicoPedidosAjuda
from ser_pleno.features.audit_logs.service import ServicoAuditLogs
from ser_pleno.features.compartilhamento.service import ServicoCompartilhamentoDadosClinicos
from ser_pleno.features.comunicacao.service import ServicoComunicacao
from ser_pleno.features.documents.service import ServicoDocuments
from ser_pleno.application.services.autenticacao import ServicoAutenticacao


def _global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger("apps.desktop").error(
        "Excecao nao tratada", exc_info=(exc_type, exc_value, exc_traceback)
    )


sys.excepthook = _global_exception_handler


def _report_callback_exception(self, exc, val, tb):
    logging.getLogger("apps.desktop").error(
        "Excecao em callback do CustomTkinter", exc_info=(exc, val, tb)
    )


try:
    ctk.CTk.report_callback_exception = _report_callback_exception
except Exception as exc:
    logger.exception("Falha ao registrar report_callback_exception: %s", exc)


class App(ctk.CTk):
    def __init__(self):
        self._t_boot = time.perf_counter()
        super().__init__()

        self.usuario_logado = None
        self.usuario_logado_id = None
        self.auth_service = None
        self.onboarding_tour = None

        self._desktop_notifier = get_desktop_notifier()
        self._desktop_notifier.set_window(self)

        self._setup_window()
        self._setup_container()
        self._init_managers()
        self._start_background_services()
        self._show_login()
        self._log_boot_perf()

    def _setup_window(self) -> None:
        apply_global_style("light")
        self.title("SerPleno")
        self.minsize(1280, 720)
        self.configure(fg_color=THEME["bg"])
        try:
            self.state("zoomed")
        except Exception as exc:
            logger.debug("Falha ao aplicar estado maximizado: %s", exc)

    def _setup_container(self) -> None:
        self.container = ctk.CTkFrame(self, fg_color=THEME["bg"])
        self.container.pack(fill="both", expand=True)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def _init_managers(self) -> None:
        self.navigation = NavigationManager(self, auth_service=self.auth_service)
        self.theme_manager = ThemeManager(self)
        self._bootstrap = BootstrapService()

    def _start_background_services(self) -> None:
        try:
            atualizar_disponibilidade_api_async()
        except Exception as exc:
            logger.exception("Falha em atualizar_disponibilidade_api_async: %s", exc)

        try:
            sync_service = get_sync_service()
            if sync_service:
                sync_service.start_background_sync()
        except Exception as exc:
            logger.exception("Falha em start_background_sync: %s", exc)

    def _show_login(self) -> None:
        self.navigation.clear_screen()
        frame = LoginFrame(self.container, self)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    def _init_services(self) -> None:
        self.servico_agenda = ServicoAgendamento(auth_service=self.auth_service)
        self.servico_estudantes = ServicoEstudante(auth_service=self.auth_service)
        self.servico_orientacoes = ServicoOrientacoes(auth_service=self.auth_service)
        self.servico_triagem = ServicoTriagem(auth_service=self.auth_service)
        self.servico_bem_estar = ServicoBemEstar(auth_service=self.auth_service)
        self.servico_alertas = ServicoAlertas(auth_service=self.auth_service)
        self.servico_dashboard = ServicoDashboard(auth_service=self.auth_service)
        self.servico_analytics = ServicoAnalytics(auth_service=self.auth_service)
        self.servico_intervencoes = ServicoIntervencoes(auth_service=self.auth_service)
        self.servico_metas = ServicoMetas(auth_service=self.auth_service)
        self.servico_wellness_challenges = ServicoWellnessChallenges(auth_service=self.auth_service)
        self.servico_configuracoes = ServicoConfiguracoes(auth_service=self.auth_service)
        self.servico_notificacoes = ServicoNotificacoes(auth_service=self.auth_service)
        self.servico_relatorio = ServicoRelatorio(auth_service=self.auth_service)
        self.servico_report_template = ServicoReportTemplate(auth_service=self.auth_service)
        self.servico_mural = ServicoMural(auth_service=self.auth_service)
        self.servico_pedidos_ajuda = ServicoPedidosAjuda(auth_service=self.auth_service)
        self.servico_audit = ServicoAuditLogs(auth_service=self.auth_service)
        self.servico_compartilhamento = ServicoCompartilhamentoDadosClinicos(auth_service=self.auth_service)
        self.servico_comunicacao = ServicoComunicacao(auth_service=self.auth_service)
        self.servico_documents = ServicoDocuments(auth_service=self.auth_service)
        self.servico_autenticacao = ServicoAutenticacao(auth_service=self.auth_service)

    def _log_boot_perf(self) -> None:
        self._t_boot_fim = time.perf_counter()
        try:
            logger.info(
                "PERF boot cold_start_ms=%.1f",
                (self._t_boot_fim - self._t_boot) * 1000,
            )
        except Exception as exc:
            logger.exception("Falha ao logar PERF boot cold_start: %s", exc)

    def mostrar_login(self) -> None:
        self._show_login()

    def iniciar_sistema(
        self,
        user_data: dict[str, Any],
        auth_service: Any | None = None,
        login_start: float | None = None,
    ) -> None:
        self.usuario_logado = user_data
        self.usuario_logado_id = user_data["id"]
        self.auth_service = auth_service
        self._init_services()

        self.navigation.clear_screen()

        self._t_controllers_start = time.perf_counter()
        self._t_controllers_end = time.perf_counter()

        self._t_ui_start = time.perf_counter()
        self.navigation.create_sidebar()
        self.after_idle(self._build_main_content)
        self._t_ui_end = time.perf_counter()

        self._t_login_fim = time.perf_counter()

        try:
            logger.info(
                "PERF login_flow_ms=%.1f auth_ms=%.1f controllers_ms=%.1f ui_build_ms=%.1f",
                (self._t_login_fim - self._t_boot_fim) * 1000,
                (self._t_login_fim - login_start) * 1000 if login_start else 0.0,
                (self._t_controllers_end - self._t_controllers_start) * 1000,
                (self._t_ui_end - self._t_ui_start) * 1000,
            )
        except Exception as exc:
            logger.exception("Falha ao logar PERF login_flow: %s", exc)

        self._bootstrap.run_post_login_seed()

        self._apply_saved_notification_settings()

        self.onboarding_tour = OnboardingTourController(self, self.navigation)
        if self.onboarding_tour.should_show():
            self.after_idle(self._maybe_start_onboarding)

    def _maybe_start_onboarding(self) -> None:
        if not self.winfo_exists():
            return
        content_body = getattr(self, "content_body", None)
        if content_body is None or not content_body.winfo_exists():
            self.after_idle(self._maybe_start_onboarding)
            return
        if self.onboarding_tour is not None and self.onboarding_tour.should_show():
            self.onboarding_tour.start()

    def _is_login_active(self) -> bool:
        return not hasattr(self.navigation, "sidebar") or not self.navigation.sidebar.winfo_exists()

    def _apply_saved_notification_settings(self) -> None:
        try:
            from ser_pleno.features.configuracoes.service import ServicoConfiguracoes
            servico = ServicoConfiguracoes(auth_service=self.auth_service)
            res = servico.obter_configuracoes()
            if not res.get("success") or not res.get("data"):
                return
            user_id = None
            auth = getattr(servico, "_auth_service", None)
            if auth and getattr(auth, "user", None):
                user_id = auth.user.get("id")
            for item in res["data"]:
                if item.get("user_id") == user_id and user_id is not None:
                    notifications = item.get("notifications")
                    if notifications:
                        import json
                        try:
                            notif = json.loads(notifications)
                            sound_enabled = notif.get("Efeitos Sonoros", True)
                            self._desktop_notifier.set_sound_enabled(bool(sound_enabled))
                        except Exception as exc:
                            logger.debug("Falha ao aplicar configuracoes de notificacao: %s", exc)
                    break
        except Exception as exc:
            logger.debug("Falha ao aplicar configurações de notificação: %s", exc)

    def _build_main_content(self) -> None:
        if not self.winfo_exists():
            return
        self.navigation.create_content_area()
        self.navigation.precreate("dashboard")
        self.navigation.show("dashboard")
        self._bind_global_search()

    def _bind_global_search(self) -> None:
        def _focus_search(_=None):
            search = getattr(self.navigation.app, "global_search", None)
            if search and hasattr(search, "focus"):
                search.focus()
        try:
            self.bind_all("<Control-k>", _focus_search)
            self.bind_all("<Control-K>", _focus_search)
        except Exception as exc:
            logger.debug("Falha ao registrar atalho de busca global: %s", exc)

    def reiniciar_onboarding(self) -> None:
        if self.onboarding_tour is not None:
            self.onboarding_tour.restart()


if __name__ == "__main__":
    App().mainloop()

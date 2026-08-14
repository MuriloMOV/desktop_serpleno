import os
import sys
import time
import threading

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

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

from ser_pleno.infrastructure.api.connectivity import atualizar_disponibilidade_api_async

from ser_pleno.ui.theme import (
    THEME,
    SPACING,
    RADIUS,
    ELEVATION,
    font,
    themed_font,
    get_mode,
    apply_global_style,
    toggle_mode,
    on_theme_change,
)
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.presentation.components.ui_components import (
    PageHeader,
    SectionHeader,
    Card,
    KPICard,
    PrimaryButton,
    SecondaryButton,
    GhostButton,
    Badge,
    EmptyState,
    Divider,
    blend_color,
    SkeletonLoader,
    Tooltip,
    Avatar,
)
from ser_pleno.presentation.views.login import LoginFrame
from ser_pleno.presentation.navigation import NavigationManager
from ser_pleno.presentation.theme_manager import ThemeManager
from ser_pleno.application.services.bootstrap import BootstrapService


def _global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger = logging.getLogger("apps.desktop")
    logger.error("Excecao nao tratada", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = _global_exception_handler


def _report_callback_exception(self, exc, val, tb):
    logger = logging.getLogger("apps.desktop")
    logger.error("Excecao em callback do CustomTkinter", exc_info=(exc, val, tb))


try:
    ctk.CTk.report_callback_exception = _report_callback_exception
except Exception as exc:
    logger.exception("Falha ao registrar report_callback_exception: %s", exc)


class App(ctk.CTk):
    def __init__(self):
        self._t_boot = time.perf_counter()
        super().__init__()

        self._setup_window()

        self.usuario_logado = None
        self.usuario_logado_id = None
        self.auth_service = None

        self.container = ctk.CTkFrame(self, fg_color=THEME["bg"])
        self.container.pack(fill="both", expand=True)
        self.container.grid_columnconfigure(1, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.navigation = NavigationManager(self, auth_service=self.auth_service)
        self.theme_manager = ThemeManager(self)
        self._bootstrap = BootstrapService()

        try:
            atualizar_disponibilidade_api_async()
        except Exception as exc:
            logger.exception("Falha em atualizar_disponibilidade_api_async: %s", exc)

        try:
            from ser_pleno.infrastructure.api.sync_service import get_sync_service

            sync_service = get_sync_service()
            if sync_service:
                sync_service.start_background_sync()
        except Exception as exc:
            logger.exception("Falha em start_background_sync: %s", exc)

        self.mostrar_login()
        self._t_boot_fim = time.perf_counter()
        try:
            logger.info(
                "PERF boot cold_start_ms=%.1f",
                (self._t_boot_fim - self._t_boot) * 1000,
            )
        except Exception as exc:
            logger.exception("Falha ao logar PERF boot cold_start: %s", exc)

    def _setup_window(self):
        apply_global_style("light")
        self.title("SerPleno")
        self.minsize(1000, 600)
        self.configure(fg_color=THEME["bg"])
        # Aplica estado maximizado sem esconder a janela.
        # Falhas aqui são ignoradas para não quebrar inicialização.
        try:
            self.state("zoomed")
        except Exception as exc:
            logger.debug("Falha ao aplicar estado maximizado: %s", exc)

    # ================= LOGIN =================
    def mostrar_login(self):
        self.navigation.clear_screen()
        frame = LoginFrame(self.container, self)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    # ================= SISTEMA =================
    def iniciar_sistema(self, user_data, auth_service=None, login_start=None):
        self._t_login_fim = time.perf_counter()
        self.usuario_logado = user_data
        self.usuario_logado_id = user_data["id"]
        self.auth_service = auth_service
        self.navigation.clear_screen()

        self._t_controllers_start = time.perf_counter()
        self._t_controllers_end = time.perf_counter()

        self._t_ui_start = time.perf_counter()
        self.navigation.create_sidebar()
        # Conteúdo e dashboard são adiados para after_idle para o sidebar
        # aparecer primeiro, reduzindo a latência percebida no login.
        self.after_idle(self._build_main_content)
        self._t_ui_end = time.perf_counter()
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

    def _is_login_active(self) -> bool:
        return not hasattr(self.navigation, "sidebar") or not self.navigation.sidebar.winfo_exists()

    def _build_main_content(self) -> None:
        """Constrói área de conteúdo e exibe dashboard após o sidebar."""
        if not self.winfo_exists():
            return
        self.navigation.create_content_area()
        self.navigation.precreate("dashboard")
        self.navigation.show("dashboard")


if __name__ == "__main__":
    App().mainloop()

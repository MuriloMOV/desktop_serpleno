import os
import sys
import time
import threading

_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_path = os.path.join(_base_dir, ".env")
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
    THEME, SPACING, RADIUS, ELEVATION, font, themed_font,
    get_mode, apply_global_style, toggle_mode, on_theme_change,
)
from ser_pleno.presentation.components.icons import ICONS
from ser_pleno.presentation.components.ui_components import (
    PageHeader, SectionHeader, Card, KPICard,
    PrimaryButton, SecondaryButton, GhostButton,
    Badge, EmptyState, Divider, blend_color,
    SkeletonLoader, Tooltip, Avatar,
)
from ser_pleno.presentation.views.login import LoginFrame
from ser_pleno.presentation.navigation import NavigationManager
from ser_pleno.presentation.theme_manager import ThemeManager


def _global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger = logging.getLogger("apps.desktop")
    logger.error("Excecao nao tratada", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = _global_exception_handler

try:
    ctk.CTk.report_callback_exception = lambda *args: None
except Exception:
    pass


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

        self.navigation = NavigationManager(self)
        self.theme_manager = ThemeManager(self)

        try:
            atualizar_disponibilidade_api_async()
        except Exception:
            pass

        try:
            from ser_pleno.infrastructure.api.sync_service import get_sync_service
            sync_service = get_sync_service()
            if sync_service:
                sync_service.start_background_sync()
        except Exception:
            pass

        self.mostrar_login()
        self._t_boot_fim = time.perf_counter()
        try:
            logger.info(
                "PERF boot cold_start_ms=%.1f",
                (self._t_boot_fim - self._t_boot) * 1000,
            )
        except Exception:
            pass

    def _setup_window(self):
        apply_global_style("light")
        self.title("SerPleno")
        self.geometry("1280x720")
        self.minsize(1000, 600)
        self.configure(fg_color=THEME["bg"])

    # ================= LOGIN =================
    def mostrar_login(self):
        self.navigation.limpar_tela()
        frame = LoginFrame(self.container, self)
        frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

    # ================= SISTEMA =================
    def iniciar_sistema(self, user_data, auth_service=None):
        self._t_login_fim = time.perf_counter()
        self.usuario_logado = user_data
        self.usuario_logado_id = user_data["id"]
        self.auth_service = auth_service
        self.navigation.limpar_tela()

        self._t_controllers_start = time.perf_counter()
        self._t_controllers_end = time.perf_counter()

        self._t_ui_start = time.perf_counter()
        self.navigation.criar_sidebar()
        self.navigation.criar_area_conteudo()
        self.navigation.show("dashboard")
        self._t_ui_end = time.perf_counter()
        try:
            logger.info(
                "PERF login_flow_ms=%.1f controllers_ms=%.1f ui_build_ms=%.1f",
                (self._t_login_fim - self._t_boot_fim) * 1000,
                (self._t_controllers_end - self._t_controllers_start) * 1000,
                (self._t_ui_end - self._t_ui_start) * 1000,
            )
        except Exception:
            pass

        self._run_post_login_seed()

    def _run_post_login_seed(self) -> None:
        def _seed_thread():
            try:
                from ser_pleno.infrastructure.local.seed_service import sync_critical_entities
                result = sync_critical_entities()
                if result.get("failed"):
                    logger.warning("Seed pos-login parcial: %s", result)
                else:
                    logger.info("Seed pos-login concluido: %s", result)
            except Exception as exc:
                logger.warning("Seed pos-login falhou (nao-bloqueante): %s", exc)

        threading.Thread(target=_seed_thread, daemon=True).start()

    def _tela_login_ativa(self) -> bool:
        return not hasattr(self.navigation, "sidebar") or not self.navigation.sidebar.winfo_exists()


if __name__ == "__main__":
    App().mainloop()

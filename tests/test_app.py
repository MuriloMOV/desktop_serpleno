import os
import sys
from unittest.mock import MagicMock, patch

import customtkinter as ctk

# Add project root and src to path for imports
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src = os.path.join(_root, "src")
for _p in [_src, _root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ser_pleno.app import App
from ser_pleno.ui.views.agenda import AgendaFrame
from ser_pleno.ui.navigation import NavigationManager
from ser_pleno.ui.theme_manager import ThemeManager


def test_app_initialization():
    with (
        patch("ser_pleno.app.atualizar_disponibilidade_api_async"),
        patch("ser_pleno.app.get_sync_service"),
        patch.object(ctk, "CTkFrame"),
        patch.object(ctk.CTk, "__init__", return_value=None),
        patch.object(App, "mostrar_login"),
        patch.object(App, "_show_login"),
        patch.object(App, "_setup_window"),
        patch.object(App, "_setup_container"),
        patch.object(App, "_init_managers"),
        patch.object(App, "_start_background_services"),
        patch.object(App, "_log_boot_perf"),
    ):
        app = App()
        assert app.usuario_logado is None
        assert app.usuario_logado_id is None


def test_navigation_flow():
    app = App.__new__(App)
    app.header_title = MagicMock()
    app.header_subtitle = MagicMock()
    app.header_title.winfo_exists.return_value = True
    app.header_subtitle.winfo_exists.return_value = True
    app.content_body = MagicMock()

    navigation = NavigationManager(app)
    navigation.update_menu = MagicMock()
    navigation.view_factory = MagicMock()
    app.navigation = navigation

    app.navigation.show("agenda")

    app.navigation.update_menu.assert_called_once_with("agenda")
    navigation.view_factory.create.assert_called_once_with("agenda", app.content_body)


def test_navigation_update_header():
    app = App.__new__(App)
    app.header_title = MagicMock()
    app.header_subtitle = MagicMock()
    app.header_title.winfo_exists.return_value = True
    app.header_subtitle.winfo_exists.return_value = True

    navigation = NavigationManager(app)
    navigation.update_header("Test Title", "Test Subtitle")

    app.header_title.configure.assert_called_once_with(text="Test Title")
    app.header_subtitle.configure.assert_called_once_with(text="Test Subtitle")


def test_navigation_get_active_screen():
    app = App.__new__(App)
    navigation = NavigationManager(app)

    assert navigation.get_active_screen() == "dashboard"

    navigation.update_menu("agenda")
    assert navigation.get_active_screen() == "agenda"


def test_navigation_clear_screen():
    app = App.__new__(App)
    app.container = MagicMock()
    app.container.winfo_children.return_value = [MagicMock(), MagicMock()]

    navigation = NavigationManager(app)
    navigation.clear_screen()

    assert app.container.winfo_children.called
    for child in app.container.winfo_children.return_value:
        child.destroy.assert_called_once()


def test_theme_manager_rebuilds_ui_on_theme_change():
    app = App.__new__(App)
    app.usuario_logado = {"id": 1}
    app.configure = MagicMock()
    app.container = MagicMock()
    app.container.winfo_exists.return_value = True

    navigation = NavigationManager(app)
    navigation.clear_screen = MagicMock()
    navigation.create_sidebar = MagicMock()
    navigation.create_content_area = MagicMock()
    navigation.show = MagicMock()
    app.navigation = navigation

    with patch.object(app, "winfo_exists", return_value=True):
        theme_manager = ThemeManager(app)
        # Manually trigger the theme changed callback
        theme_manager._on_theme_changed("dark")

    navigation.clear_screen.assert_called_once()
    navigation.create_sidebar.assert_called_once()
    navigation.create_content_area.assert_called_once()
    navigation.show.assert_called_once()

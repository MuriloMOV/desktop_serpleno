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
from ser_pleno.presentation.views.agenda import AgendaFrame
from ser_pleno.presentation.navigation import NavigationManager


@patch.object(App, "mostrar_login")
@patch.object(App, "configure")
@patch.object(App, "minsize")
@patch.object(App, "geometry")
@patch.object(App, "title")
@patch.object(ctk, "CTkFrame")
@patch.object(ctk.CTk, "__init__", return_value=None)
def test_app_initialization(
    mock_ctk_init,
    mock_frame,
    mock_title,
    mock_geometry,
    mock_minsize,
    mock_configure,
    mock_mostrar_login,
):
    container = MagicMock()
    mock_frame.return_value = container

    app = App()

    mock_ctk_init.assert_called_once_with()
    mock_title.assert_called_once_with("SerPleno")
    mock_geometry.assert_called_once_with("1280x720")
    mock_minsize.assert_called_once_with(1000, 600)
    container.pack.assert_called_once_with(fill="both", expand=True)
    mock_mostrar_login.assert_called_once_with()
    assert app.usuario_logado is None
    assert app.usuario_logado_id is None


def test_navigation_flow():
    app = App.__new__(App)
    app.header_title = MagicMock()
    app.header_subtitle = MagicMock()
    app.header_title.winfo_exists.return_value = True
    app.header_subtitle.winfo_exists.return_value = True

    navigation = NavigationManager(app)
    navigation.atualizar_menu = MagicMock()
    navigation.trocar_frame = MagicMock()
    app.navigation = navigation

    app.navigation.show("agenda")

    app.navigation.atualizar_menu.assert_called_once_with("agenda")
    app.navigation.trocar_frame.assert_called_once_with(AgendaFrame)

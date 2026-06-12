import os
import sys
from unittest.mock import MagicMock, patch

import customtkinter as ctk

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ser_pleno")),
)

from app import App
from views.agenda import AgendaFrame


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
    mock_minsize.assert_called_once_with(800, 480)
    container.pack.assert_called_once_with(fill="both", expand=True)
    mock_mostrar_login.assert_called_once_with()
    assert app.usuario_logado is None
    assert app.usuario_logado_id is None


def test_navigation_flow():
    app = App.__new__(App)
    app.atualizar_menu = MagicMock()
    app.trocar_frame = MagicMock()

    app.mostrar_agenda()

    app.atualizar_menu.assert_called_once_with("agenda")
    app.trocar_frame.assert_called_once_with(AgendaFrame)

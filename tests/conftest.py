import pytest
from unittest.mock import MagicMock
import customtkinter as ctk
from tkinter import TclError
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def app():
    """Create the app instance for the entire session"""
    ctk.set_appearance_mode("Dark")
    try:
        app = ctk.CTk()
    except TclError as error:
        pytest.skip(f"Tcl/Tk indisponível para testes visuais: {error}")
    app.geometry("800x600")
    yield app
    app.destroy()

@pytest.fixture
def controller(app):
    """Mock controller"""
    controller = MagicMock()
    controller.content = app
    return controller

@pytest.fixture
def mock_response():
    def _create_response(data, success=True):
        return {"success": success, "data": data}
    return _create_response

@pytest.fixture(autouse=True)
def mock_network(monkeypatch):
    """Disable actual network calls"""
    monkeypatch.setattr("requests.get", MagicMock())
    monkeypatch.setattr("requests.post", MagicMock())

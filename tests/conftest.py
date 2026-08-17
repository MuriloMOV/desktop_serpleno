import gc
import weakref
import pytest
from unittest.mock import MagicMock
import customtkinter as ctk
from tkinter import TclError
import sys
import os

# Add project root and src to path for imports
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src = os.path.join(_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
if _root not in sys.path:
    sys.path.insert(0, _root)


@pytest.fixture(scope="function")
def app():
    """Create a fresh CTk window per test to avoid Tcl/Tk interpreter memory leak."""
    ctk.set_appearance_mode("Dark")
    try:
        app = ctk.CTk()
    except TclError as error:
        pytest.skip(f"Tcl/Tk indisponível para testes visuais: {error}")
    app.geometry("800x600")
    yield app
    try:
        app.destroy()
    except Exception:
        pass
    _cleanup_tk()


@pytest.fixture(autouse=True)
def cleanup_theme_listeners():
    """Prevent theme listener accumulation across UI tests."""
    from ser_pleno.ui.theme import _LISTENERS

    before = list(_LISTENERS)
    yield
    after = set(_LISTENERS)
    for cb in after - set(before):
        try:
            _LISTENERS.remove(cb)
        except ValueError:
            pass


@pytest.fixture(autouse=True)
def cleanup_memory():
    """Force cleanup after each test to prevent memory accumulation."""
    yield
    _cleanup_tk()


def _cleanup_tk() -> None:
    """Destroy orphan Tkinter widgets and force garbage collection."""
    try:
        for widget in list(ctk.CTk._instance().winfo_children()):
            try:
                widget.destroy()
            except Exception:
                pass
        ctk.CTk._instance().destroy()
    except Exception:
        pass
    try:
        gc.collect()
        gc.garbage.clear()
    except Exception:
        pass


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

import gc
import pytest
import subprocess
import sys
import os
from unittest.mock import MagicMock, patch

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src = os.path.join(_root, "src")
for _p in [_src, _root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _run_ui_tests(path: str) -> None:
    cmd = [sys.executable, "-m", "pytest", path, "-v"]
    proc = subprocess.run(cmd, cwd=_root, capture_output=True, text=True)
    out = proc.stdout + "\n" + proc.stderr
    if proc.returncode != 0:
        pytest.fail(f"Testes de UI falharam em subprocesso:\n{out}")
    print(out)


@pytest.fixture(scope="function")
def app():
    import customtkinter as ctk
    from tkinter import TclError
    ctk.set_appearance_mode("Dark")
    try:
        app = ctk.CTk()
    except TclError as error:
        pytest.skip(f"Tcl/Tk indisponível para testes visuais: {error}")
    app.geometry("800x600")
    yield app
    try:
        for widget in list(app.winfo_children()):
            try:
                widget.destroy()
            except Exception:
                pass
        app.destroy()
    except Exception:
        pass
    for _ in range(5):
        gc.collect()
        gc.garbage.clear()
    try:
        ctk.CTk._instance().destroy()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def cleanup_theme_listeners():
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
    yield
    for _ in range(5):
        gc.collect()
        gc.garbage.clear()


@pytest.fixture
def controller(app):
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
    monkeypatch.setattr("requests.get", MagicMock())
    monkeypatch.setattr("requests.post", MagicMock())

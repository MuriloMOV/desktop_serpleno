import gc
import os
import subprocess
import sys
from unittest.mock import MagicMock

import pytest

from ser_pleno.application.services.autenticacao import ServicoAutenticacao

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


@pytest.fixture(scope="session")
def app():
    """Instância CTk reutilizada para TODOS os testes de UI (evita vazamento de memória do Tcl/Tk)."""
    from tkinter import TclError

    import customtkinter as ctk

    ctk.set_appearance_mode("Dark")
    try:
        app = ctk.CTk()
    except TclError as error:
        pytest.skip(f"Tcl/Tk indisponível para testes visuais: {error}")
    app.geometry("1200x800")
    app.withdraw()  # Oculta janela durante testes
    yield app
    # Cleanup final da sessão
    try:
        _teardown_ctk_app(app)
    except Exception:
        pass
    _cleanup_ctk_resources()


@pytest.fixture(autouse=True)
def clear_app_widgets(app):
    """Limpa todos os widgets do app entre cada teste para evitar acúmulo."""
    yield
    _clear_all_widgets(app)


def _clear_all_widgets(app):
    """Remove todos os widgets filhos do app e força garbage collection."""
    try:
        for widget in list(app.winfo_children()):
            try:
                widget.destroy()
            except Exception:
                pass
    except Exception:
        pass
    # Força GC para limpar referências circulares
    for _ in range(3):
        gc.collect()
        gc.garbage.clear()


def _teardown_ctk_app(app):
    """Destrói widgets e a instância CTk de forma segura."""
    try:
        app.quit()
    except Exception:
        pass
    try:
        for widget in list(app.winfo_children()):
            try:
                widget.destroy()
            except Exception:
                pass
        app.destroy()
    except Exception:
        pass
    try:
        import customtkinter as ctk
        instance = ctk.CTk._instance()
        if instance is not None:
            instance.destroy()
    except Exception:
        pass


def _cleanup_ctk_resources():
    """Força limpeza de memória e recursos nativos do Tcl/Tk."""
    import sys
    import ctypes

    for _ in range(6):
        gc.collect()
        gc.garbage.clear()
    if sys.platform == "win32":
        try:
            ctypes.windll.kernel32.SetProcessWorkingSetSize(
                ctypes.c_int(-1), ctypes.c_size_t(0), ctypes.c_size_t(0)
            )
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
def disable_service_background_threads():
    original = ServicoAutenticacao._try_establish_session_async
    ServicoAutenticacao._try_establish_session_async = lambda self, usuario, senha: None
    yield
    ServicoAutenticacao._try_establish_session_async = original


@pytest.fixture(autouse=True)
def cleanup_memory():
    yield
    for _ in range(5):
        gc.collect()
        gc.garbage.clear()


@pytest.fixture(autouse=True)
def mock_network(monkeypatch):
    monkeypatch.setattr("requests.get", MagicMock())
    monkeypatch.setattr("requests.post", MagicMock())


@pytest.fixture(autouse=True)
def mock_async_runner(monkeypatch):
    """Mocka AsyncRunner.run para evitar criação de threads reais durante testes."""
    from unittest.mock import MagicMock
    
    def mock_run(task, on_success=None, on_error=None, on_complete=None, widget_ref=None):
        try:
            result = task()
            if on_success:
                on_success(result)
        except Exception as exc:
            if on_error:
                on_error(exc)
        finally:
            if on_complete:
                on_complete()
    
    monkeypatch.setattr("ser_pleno.utils.async_runner.AsyncRunner.run", staticmethod(mock_run))


@pytest.fixture(autouse=True)
def mock_widget_batch_builder(monkeypatch):
    """Mocka WidgetBatchBuilder para evitar criação real de widgets em lote."""
    from unittest.mock import MagicMock
    
    class MockWidgetBatchBuilder:
        def __init__(self, parent=None, batch_size=50):
            self._parent = parent
            self._batch_size = batch_size
            self._ops = []
        
        def add(self, op):
            self._ops.append(op)
        
        def add_many(self, ops):
            self._ops.extend(ops)
        
        def execute(self):
            # NÃO executa as operações para evitar criação real de widgets
            self._ops.clear()
    
    monkeypatch.setattr("ser_pleno.utils.widget_batch.WidgetBatchBuilder", MockWidgetBatchBuilder)
    # Aplica para todos os módulos que importam
    import sys
    for module_name in list(sys.modules.keys()):
        if 'interventions' in module_name or 'metas' in module_name or 'relatorio' in module_name or 'report_template' in module_name:
            module = sys.modules[module_name]
            if hasattr(module, 'WidgetBatchBuilder'):
                module.WidgetBatchBuilder = MockWidgetBatchBuilder


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
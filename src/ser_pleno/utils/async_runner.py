"""
Execução assíncrona segura para CustomTkinter.
Encapsula threading.Thread com tratamento de exceções, logging e callback
garantido na thread principal via CTk after(), evitando UI freezes e falhas silenciosas.
"""

import logging
import threading
import time
import traceback
from functools import partial
from typing import Callable, Optional, Any

logger = logging.getLogger(__name__)


class AsyncRunner:
    """
    Wrapper para execução de tarefas em background com atualização segura da UI.
    """

    @staticmethod
    def run(
        task: Callable[[], Any],
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
        widget_ref: Any = None,
    ) -> None:
        """
        Executa `task` em thread daemon. Garante que callbacks são chamados
        via `widget_ref.after(0, ...)` se widget_ref for fornecido, senão chama direto.

        :param task: Função síncrona a ser executada em background.
        :param on_success: Callback chamado com o resultado de `task` se não houver exceção.
        :param on_error: Callback chamado com a exceção se `task` falhar.
        :param on_complete: Callback chamado sempre ao final (sucesso ou erro).
        :param widget_ref: Widget CTk (qualquer) para agendar callbacks na thread principal.
        """
        t0 = time.perf_counter()
        def _worker():
            try:
                result = task()
                logger.debug("AsyncRunner.task done in %.1fms", (time.perf_counter() - t0) * 1000)
                if on_success:
                    _safe_after(widget_ref, partial(on_success, result))
            except Exception as exc:
                logger.exception("Erro em tarefa assíncrona")
                if on_error:
                    _safe_after(widget_ref, partial(on_error, exc))
            finally:
                if on_complete:
                    _safe_after(widget_ref, on_complete)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()


def _safe_after(widget_ref: Any, callback: Callable[[], None]) -> None:
    """
    Agenda callback na thread principal do Tkinter/CTk se widget_ref existir e
    a janela ainda estiver de pé. Caso contrário, executa diretamente (fallback).
    """
    try:
        if widget_ref is not None and hasattr(widget_ref, "after") and hasattr(widget_ref, "winfo_exists") and widget_ref.winfo_exists():
            widget_ref.after(0, callback)
        else:
            callback()
    except Exception:
        try:
            callback()
        except Exception:
            pass


def log_view_init_ms(view_name: str, t0: float, widget_ref: Any = None) -> None:
    """Loga métrica de tempo de init de uma view."""
    dt = (time.perf_counter() - t0) * 1000
    msg = f"PERF view_init_{view_name}_ms={dt:.1f}"
    if widget_ref is not None and hasattr(widget_ref, "winfo_exists") and widget_ref.winfo_exists():
        widget_ref.after(0, lambda: logger.info(msg))
    else:
        logger.info(msg)


__all__ = ["AsyncRunner", "log_view_init_ms"]

"""
widget_batch.py —” helper para criação em lote de widgets CustomTkinter
com supressão controlada de update_idletasks, reduzindo flickering e
travamentos durante renderização de listas grandes.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class WidgetBatchBuilder:
    """Acumula operações de criação de widgets e aplica update_idletasks()
    apenas uma vez no final, evitando recálculos de layout intermediários.

    Uso:
        batch = WidgetBatchBuilder(parent=self.scroll_list)
        for item in items:
            batch.add(lambda i=item: self._criar_item(i))
        batch.execute()
    """

    def __init__(self, parent: Any = None, batch_size: int = 50) -> None:
        self._parent = parent
        self._batch_size = batch_size
        self._ops: list[Callable[[], None]] = []

    def add(self, op: Callable[[], None]) -> None:
        """Agrega uma operação de criação de widget."""
        self._ops.append(op)

    def add_many(self, ops: list[Callable[[], None]]) -> None:
        """Agrega múltiplas operações de uma vez."""
        self._ops.extend(ops)

    def execute(self) -> None:
        """Executa todas as operações acumuladas com update_idletasks() controlado."""
        if not self._ops:
            return

        parent = self._parent
        has_after = parent is not None and hasattr(parent, "after")

        # Reduz automaticamente o batch se o widget pai não estiver visível;
        # isso evita flickering em monitores com baixa taxa de atualização.
        effective_batch = self._batch_size
        if parent is not None and hasattr(parent, "winfo_ismapped") and not parent.winfo_ismapped():
            effective_batch = min(self._batch_size, 8)

        # Se o pai suportar after_idle, agenda a execução em lotes curtos
        # para não travar a UI com muitos widgets de uma vez.
        if has_after:
            self._ops = self._ops[::-1]
            parent.after_idle(self._execute_next_batch, parent, effective_batch, 0)
        else:
            self._execute_all(effective_batch)

    def _execute_all(self, effective_batch: int) -> None:
        total = len(self._ops)
        for i in range(0, total, effective_batch):
            lot = self._ops[i:i + effective_batch]
            for op in lot:
                try:
                    op()
                except Exception as exc:
                    logger.debug("WidgetBatchBuilder: erro ao criar widget: %s", exc)
        self._ops.clear()

    def _execute_next_batch(self, parent: Any, batch_size: int, index: int) -> None:
        total = len(self._ops)
        if index >= total or not parent.winfo_exists():
            self._ops.clear()
            return

        lot = self._ops[index:index + batch_size]
        for op in lot:
            try:
                op()
            except Exception as exc:
                logger.debug("WidgetBatchBuilder: erro ao criar widget: %s", exc)

        next_index = index + batch_size
        if next_index < total:
            try:
                parent.after(0, parent.update_idletasks)
                parent.after_idle(self._execute_next_batch, parent, batch_size, next_index)
            except Exception:
                self._ops.clear()
        else:
            self._ops.clear()
            try:
                parent.after(0, parent.update_idletasks)
            except Exception:
                pass


def batch_render(parent, widgets_data: list, builder_fn, batch_size: int = 50) -> None:
    """Helper de alto nível: renderiza uma lista de widgets usando builder_fn.

    :param parent: Widget pai onde os widgets serão criados.
    :param widgets_data: Lista de dados para criar widgets.
    :param builder_fn: Função que recebe (parent, data_item) e retorna um widget.
    :param batch_size: Tamanho do lote para update_idletasks intermediário.
    """
    if not widgets_data:
        return

    batch = WidgetBatchBuilder(parent=parent, batch_size=batch_size)
    for item in widgets_data:
        batch.add(lambda item=item, parent=parent, fn=builder_fn: fn(parent, item))
    batch.execute()


__all__ = ["WidgetBatchBuilder", "batch_render"]

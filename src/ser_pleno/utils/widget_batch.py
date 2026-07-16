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

    def __init__(self, parent=None, batch_size: int = 50):
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

        # Em telas grandes, divide em lotes menores para não travar a UI
        total = len(self._ops)
        for i in range(0, total, effective_batch):
            lot = self._ops[i:i + effective_batch]
            for op in lot:
                try:
                    op()
                except Exception as exc:
                    logger.debug("WidgetBatchBuilder: erro ao criar widget: %s", exc)

            # Apenas o último lote força o recálculo de layout
            if i + effective_batch >= total and has_after:
                try:
                    parent.after(0, parent.update_idletasks)
                except Exception:
                    pass

        self._ops.clear()


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

# -*- coding: utf-8 -*-
"""Re-export de retrocompatibilidade — use ``ser_pleno.application.controllers.triagem``.

Este módulo mantém os nomes antigos disponíveis para evitar quebras
em código externo que ainda importe ``AnaliseTriagemController``
ou use o caminho ``ser_pleno.application.controllers.analise_triagem``.
"""

from ser_pleno.application.controllers.triagem import TriagemController

# Alias de retrocompatibilidade
AnaliseTriagemController = TriagemController

__all__ = ["AnaliseTriagemController", "TriagemController"]

# -*- coding: utf-8 -*-
"""Re-export de retrocompatibilidade — use ``ser_pleno.application.controllers.avisos``.

Este módulo mantém os nomes antigos disponíveis para evitar quebras
em código externo que ainda importe ``QuadroAvisosController``
ou use o caminho ``ser_pleno.application.controllers.quadro_avisos``.
"""

from ser_pleno.application.controllers.avisos import AvisosController

# Alias de retrocompatibilidade
QuadroAvisosController = AvisosController

__all__ = ["QuadroAvisosController", "AvisosController"]

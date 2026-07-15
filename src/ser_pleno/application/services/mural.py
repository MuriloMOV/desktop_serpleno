# -*- coding: utf-8 -*-
"""Service de Mural — mediação entre Controllers e Infrastructure."""

from ser_pleno.infrastructure.api.mural import ServicoMural as _ServicoMural


class ServicoMural(_ServicoMural):
    """Wrapper do ServicoMural de infrastructure para a camada de application."""
    pass

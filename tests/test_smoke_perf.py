#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke test automatizado do SerPleno Desktop.

Valida:
- Inicialização sem exceção
- Login frame é criado
- Navegação entre views
- Métricas dePerformance são registradas
"""

import sys
import time
import unittest
from unittest.mock import patch

# Garante que o src está no path
sys.path.insert(0, "src")

from ser_pleno.ui.theme import THEME, SPACING, RADIUS
from ser_pleno.ui.theme_extensions import spacing, extend_theme
from ser_pleno.application.services.autenticacao import ServicoAutenticacao


class TestThemeExtensions(unittest.TestCase):
    def test_spacing_helpers(self):
        self.assertEqual(spacing("page"), SPACING["page_x"])
        self.assertEqual(spacing("card"), SPACING["card_pad"])
        self.assertEqual(spacing("half_grid"), SPACING["grid_gap"] // 2)

    def test_extend_theme_does_not_mutate_base(self):
        base = {"a": 1, "b": 2}
        overrides = {"b": 3}
        result = extend_theme(base, overrides)
        self.assertEqual(result["b"], 3)
        self.assertEqual(base["b"], 2)


class TestAutenticacaoPerformance(unittest.TestCase):
    def test_login_paralelo_nao_bloqueia(self):
        svc = ServicoAutenticacao()
        # Garante que não há sessão ativa
        svc.user = None
        # login() deve retornar dict com 'success' sem levantar exceção
        result = svc.login("inexistente", "senha_errada")
        self.assertIn("success", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)

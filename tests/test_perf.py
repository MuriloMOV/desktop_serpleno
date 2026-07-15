#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testes de performance e theme extensions do SerPleno Desktop.

Consolida:
- Testes de tema e espaçamento
- Benchmark de login (latência do serviço de autenticação)
"""

import sys
import time
import unittest

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


class TestLoginPerformance(unittest.TestCase):
    def setUp(self):
        self.svc = ServicoAutenticacao()

    def test_login_fallback_db_tempo(self):
        """Login com usuário inexistente deve retornar em < 2.5s."""
        t0 = time.perf_counter()
        result = self.svc.login("user_inexistente", "senha_qualquer")
        dt = (time.perf_counter() - t0) * 1000
        self.assertIn("success", result)
        self.assertLess(dt, 2500, f"Login demorou {dt:.1f}ms (teto: 2500ms)")


if __name__ == "__main__":
    unittest.main(verbosity=2)

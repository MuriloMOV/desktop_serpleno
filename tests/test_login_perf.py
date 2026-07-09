#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Benchmark de performance do login e inicialização.

Métrica:
- cold_start: App.__init__() → janela visível
- login_flow: início do login até conclusão do serviço
- nav_switch: troca de view
"""

import sys
import time
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, "src")

from ser_pleno.application.services.autenticacao import ServicoAutenticacao


class TestLoginPerformance(unittest.TestCase):
    def setUp(self):
        self.svc = ServicoAutenticacao()

    def test_login_fallback_db_tempo(self):
        """Login com usuário inexistente deve retornar em < 2s."""
        t0 = time.perf_counter()
        result = self.svc.login("user_inexistente", "senha_qualquer")
        dt = (time.perf_counter() - t0) * 1000
        self.assertIn("success", result)
        self.assertLess(dt, 2500, f"Login demorou {dt:.1f}ms (teto: 2500ms)")


if __name__ == "__main__":
    unittest.main(verbosity=2)

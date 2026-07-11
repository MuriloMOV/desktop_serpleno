#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Benchmark rápido de performance dos repositórios.

Mede:
- Latência de carregamento de KPIs do dashboard (MySQL + fallback local)
- Throughput de operações no LocalCache
- Eficácia do cache de dashboard (primeira vs segunda chamada)
"""

from __future__ import annotations

import time
import statistics
import sys
import os

_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_src = os.path.join(_root, "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
if _root not in sys.path:
    sys.path.insert(0, _root)

from ser_pleno.repositories.dashboard import DashboardRepository, invalidate_dashboard_cache
from ser_pleno.infrastructure.local.local_cache import LocalCache


def bench_dashboard_kpis(iterations: int = 20):
    repo = DashboardRepository()
    samples = []
    for i in range(iterations):
        t0 = time.perf_counter()
        repo.obter_kpis()
        dt = (time.perf_counter() - t0) * 1000
        samples.append(dt)
        if i == iterations // 2:
            invalidate_dashboard_cache()

    cold = statistics.mean(samples[: iterations // 2])
    warm = statistics.mean(samples[iterations // 2 :])
    print(f"Dashboard KPIs  -> cold={cold:.1f}ms  warm={warm:.1f}ms  "
          f"samples={len(samples)}")

    return cold, warm


def bench_local_cache_ops(iterations: int = 100):
    cache = LocalCache()
    student = {
        "id": 99999,
        "nome": "Benchmark",
        "email": "bench@teste",
        "has_medical_report": 0,
        "requires_attention": 0,
    }

    # upsert
    t0 = time.perf_counter()
    for _ in range(iterations):
        cache.upsert_student(student)
    upsert_ms = (time.perf_counter() - t0) * 1000 / iterations

    # list
    t0 = time.perf_counter()
    for _ in range(iterations):
        cache.list_students()
    list_ms = (time.perf_counter() - t0) * 1000 / iterations

    print(f"LocalCache ops  -> upsert={upsert_ms:.2f}ms/op  list={list_ms:.2f}ms/op  "
          f"iterations={iterations}")

    # cleanup
    cache.delete("students", "id", 99999)


def main():
    print("=" * 60)
    print("SerPleno Desktop - Performance Benchmark")
    print("=" * 60)

    print("\n[1/2] Dashboard KPIs (consulta consolidada + TTL cache)")
    bench_dashboard_kpis(iterations=20)

    print("\n[2/2] LocalCache throughput (connection reuse)")
    bench_local_cache_ops(iterations=100)

    print("\n" + "=" * 60)
    print("Benchmark concluído.")
    print("Alvo: dashboard KPIs < 200ms (warm), LocalCache ops < 5ms")
    print("=" * 60)


if __name__ == "__main__":
    main()

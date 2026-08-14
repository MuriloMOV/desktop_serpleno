# -*- coding: utf-8 -*-
"""Validação de política de senha forte e cálculo de força."""

from __future__ import annotations

import re


MIN_LENGTH = 8

STRENGTH_COLORS = {
    "fraca":    "#DC2626",
    "razoável": "#F97316",
    "boa":      "#D97706",
    "forte":    "#059669",
}


def calcular_forca(senha: str) -> tuple:
    score = 0
    if len(senha) >= MIN_LENGTH:
        score += 1
    if re.search(r'[A-Z]', senha):
        score += 1
    if re.search(r'[a-z]', senha):
        score += 1
    if re.search(r'\d', senha):
        score += 1
    if re.search(r'[!@#$%^&*()_\-+=\[\]{}|;:,.<>?/`~]', senha):
        score += 1
    bonus = len(senha) - MIN_LENGTH
    score += max(0, bonus // 4)

    if score <= 2:
        level = "fraca"
    elif score <= 4:
        level = "razoável"
    elif score <= 5:
        level = "boa"
    else:
        level = "forte"

    pct = min(1.0, score / 6.0)
    color = STRENGTH_COLORS[level]
    return score, level, pct, color


def validar_policy(senha: str) -> dict:
    return {
        "comprimento":  len(senha) >= MIN_LENGTH,
        "maiusculas":   bool(re.search(r'[A-Z]', senha)),
        "minusculas":   bool(re.search(r'[a-z]', senha)),
        "numeros":      bool(re.search(r'\d', senha)),
        "especiais":    bool(re.search(r'[!@#$%^&*()_\-+=\[\]{}|;:,.<>?/`~]', senha)),
    }


def atende_policy(senha: str) -> bool:
    return all(validar_policy(senha).values())

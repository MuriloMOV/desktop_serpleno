# -*- coding: utf-8 -*-
"""Utilitários centralizados para mapeamento de humor/emoji."""

from __future__ import annotations


def mood_emoji_from_score(score: int) -> str:
    """Retorna emoji para score de humor inteiro (1–5), usado em check-ins."""
    return {
        1: "😢",
        2: "😕",
        3: "😐",
        4: "😊",
        5: "😄",
    }.get(max(1, min(5, int(score))), "😐")


def mood_emoji_from_avg(avg) -> str:
    """Retorna emoji para média de humor contínua, usado no dashboard."""
    if avg is None:
        return "😐"
    if avg < 2.0:
        return "😢"
    if avg < 3.0:
        return "😕"
    if avg < 4.0:
        return "😊"
    return "😄"

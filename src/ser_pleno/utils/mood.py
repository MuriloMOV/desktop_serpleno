# -*- coding: utf-8 -*-
"""Utilitários centralizados para mapeamento de humor/emoji."""

from __future__ import annotations

from ser_pleno.ui.components.icons import MOOD_EMOJIS


def mood_emoji_from_score(score: int) -> str:
    """Retorna emoji para score de humor inteiro (1–5), usado em check-ins."""
    return MOOD_EMOJIS.get(max(1, min(5, int(score))), MOOD_EMOJIS[3])


def mood_emoji_from_avg(avg) -> str:
    """Retorna emoji para média de humor contínua, usado no dashboard."""
    if avg is None:
        return MOOD_EMOJIS[3]
    if avg < 2.0:
        return MOOD_EMOJIS[1]
    if avg < 3.0:
        return MOOD_EMOJIS[2]
    if avg < 4.0:
        return MOOD_EMOJIS[4]
    return MOOD_EMOJIS[5]

# -*- coding: utf-8 -*-
"""Utilitários centralizados para desenho de gráficos no canvas."""

from __future__ import annotations

from typing import Sequence

from ser_pleno.ui.theme import THEME, SPACING, FONT_FAMILY


def draw_mood_line_chart(
    canvas,
    points: Sequence[float],
    dates: Sequence[str],
    *,
    theme: dict = None,
    spacing: dict = None,
    margin_x: int = 44,
    margin_y: int = 24,
    dot_bad_key: str = "dot_bad",
    dot_mid_key: str = "dot_mid",
    dot_good_key: str = "dot_good",
    chart_grid_key: str = "chart_grid",
    chart_fill_key: str = "chart_fill",
    chart_line_key: str = "chart_line",
    text_muted_key: str = "text_muted",
    font_size: int = 8,
) -> None:
    """Desenha gráfico de linha de humor com área preenchida no canvas fornecido.

    Reutilizável por múltiplas views (dashboard, bem-estar, etc.).
    """
    theme = theme or THEME
    spacing = spacing or SPACING

    canvas.delete("all")
    cw = canvas.winfo_width()
    ch = canvas.winfo_height()
    if cw < 80 or ch < 80:
        return

    pts = list(points)
    n = len(pts)
    if n < 2:
        return

    # Garantir que dates tenha o mesmo tamanho de pts
    if len(dates) < n:
        dates = list(dates) + [""] * (n - len(dates))

    cw2 = cw - 2 * margin_x
    ch2 = ch - 2 * margin_y

    # Fundo e borda
    canvas.create_rectangle(
        margin_x, margin_y, cw - margin_x, ch - margin_y,
        fill=theme["surface"], outline=theme[chart_grid_key], width=1,
    )

    # Grades horizontais e labels Y
    for i in range(6):
        val = 1 + i
        gy = (ch - margin_y) - (i * ch2 / 5)
        canvas.create_line(
            margin_x, gy, cw - margin_x, gy,
            fill=theme[chart_grid_key], dash=(3, 5),
        )
        canvas.create_text(
            margin_x - spacing["item_gap"], gy, text=str(val),
            font=(FONT_FAMILY, font_size), fill=theme[text_muted_key], anchor="e",
        )

    # Coordenadas dos pontos
    coords = [
        (margin_x + i * cw2 / (n - 1), (ch - margin_y) - ((v - 1) * ch2 / 4))
        for i, v in enumerate(pts)
    ]

    # Órea preenchida (polygon)
    poly_pts = []
    for x, y in coords:
        poly_pts += [x, y]
    poly_pts += [coords[-1][0], ch - margin_y, coords[0][0], ch - margin_y]
    canvas.create_polygon(poly_pts, fill=theme[chart_fill_key], outline="")

    # Linha principal
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        canvas.create_line(
            x1, y1, x2, y2,
            fill=theme[chart_line_key], width=2,
            capstyle="round", joinstyle="round",
        )

    # Pontos coloridos por valor
    for i, (x, y) in enumerate(coords):
        v = pts[i]
        dot = (
            theme[dot_bad_key] if v < 2.5
            else theme[dot_mid_key] if v < 3.5
            else theme[dot_good_key]
        )
        canvas.create_oval(
            x - 4, y - 4, x + 4, y + 4,
            fill=dot, outline="#FFFFFF", width=2,
        )

    # Labels X (datas) — passo adaptativo
    step = max(1, n // 7)
    for i, (x, _) in enumerate(coords):
        if i % step == 0:
            lbl = dates[i] if i < len(dates) else ""
            canvas.create_text(
                x, ch - 8, text=lbl,
                font=(FONT_FAMILY, font_size), fill=theme[text_muted_key],
            )

    # Legenda
    legend = [
        ("— Bom", theme[dot_good_key]),
        ("— Atenção", theme[dot_mid_key]),
        ("— Baixo", theme[dot_bad_key]),
    ]
    lx = cw - spacing["item_gap"]
    for j, (lbl, lcolor) in enumerate(reversed(legend)):
        canvas.create_text(
            lx, margin_y + spacing["item_gap"] + j * (spacing["item_gap"] + 4),
            text=lbl, font=(FONT_FAMILY, font_size), fill=lcolor, anchor="e",
        )

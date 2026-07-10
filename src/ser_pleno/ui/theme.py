# -*- coding: utf-8 -*-
"""
ui_theme.py —” Design System do SerPleno
========================================

Fonte única da verdade para cores, espaçamento, raio, tipografia e animação.
Mantém 100% de compatibilidade de chaves com o restante da aplicação
(nenhuma chave de THEME/SPACING/RADIUS/TYPO foi removida ou renomeada).

Novidades desta revisão:
  —¢ Paleta índigo refinada com melhor contraste em ambos os modos (AA/AAA
    para texto em superfícies), pensada para transmitir confiança e acolhimento
    (contexto: sistema de psicologia escolar).
  —¢ Sistema de listeners de tema: qualquer parte da aplicação pode se
    inscrever com `on_theme_change(callback)` e ser notificada quando o modo
    muda, permitindo reconstrução real da UI (ver app.py).
  —¢ `current()` para obter o dicionário do tema ativo sem depender de uma
    referência antiga ao módulo (evita o problema clássico de
    `from ser_pleno.ui.theme import THEME` "congelar" uma cópia antiga do dicionário).
"""

from __future__ import annotations

import colorsys
import platform
from typing import Callable, Literal

import customtkinter as ctk

# ——————————————————————————————————————————————————————————————————————————
#  Tipografia
# ——————————————————————————————————————————————————————————————————————————
_PLATFORM = platform.system()
if _PLATFORM == "Windows":
    FONT_FAMILY = "Segoe UI"
elif _PLATFORM == "Darwin":
    FONT_FAMILY = "Helvetica Neue"
else:
    FONT_FAMILY = "Inter"

FONT_FAMILY_MONO = "JetBrains Mono"

# ——————————————————————————————————————————————————————————————————————————
#  Paleta —” Light
#  Índigo como cor de marca, com neutros levemente frios para transmitir
#  clareza e profissionalismo sem parecer "clínico" ou frio.
# ——————————————————————————————————————————————————————————————————————————
LIGHT_THEME = {
    # Neutros / superfície
    "bg":               "#F7F7FC",
    "page_bg":          "#F7F7FC",
    "bg_alt":           "#F0F1F7",
    "surface":          "#FFFFFF",
    "surface_elevated": "#FFFFFF",
    "border":           "#E6E7F0",
    "border_strong":    "#CBCEDD",
    "divider":          "#EEEFF6",

    # Tipografia
    "text":             "#14162B",
    "text_secondary":   "#5B5E76",
    "text_muted":       "#7C7F97",
    "text_disabled":    "#C6C8D8",
    "text_on_primary":  "#FFFFFF",

    # Marca / primária
    "primary":          "#4F46E5",
    "primary_hover":    "#4338CA",
    "primary_soft":     "#EEF0FF",
    "primary_medium":   "#C7CBFA",
    "primary_strong":   "#312E81",
    "primary_light":    "#EEF0FF",

    # Acento / secundária
    "accent":           "#6366F1",
    "accent_hover":     "#4F46E5",
    "accent_soft":      "#EEF0FF",
    "accent_medium":    "#A5ABF7",
    "accent_strong":    "#3730A3",

    # Semântico
    "success":          "#059669",
    "success_soft":     "#DCFAEF",
    "success_medium":   "#A7F3D0",
    "success_strong":   "#065F46",
    "warning":          "#D97706",
    "warning_soft":     "#FEF3C7",
    "warning_medium":   "#FDE68A",
    "warning_strong":   "#92400E",
    "danger":           "#DC2626",
    "danger_soft":      "#FEE7E7",
    "danger_medium":    "#FECACA",
    "danger_strong":    "#991B1B",
    "info":             "#3B82F6",
    "info_soft":        "#E0EBFE",
    "info_medium":      "#BFDBFE",
    "info_strong":      "#1D4ED8",

    # Navegação
    "nav_bg":           "#FFFFFF",
    "nav_text":         "#63667E",
    "nav_muted":        "#9497AC",
    "nav_active_bg":    "#EEF0FF",
    "nav_hover":        "#F7F7FC",
    "nav_active_text":  "#4F46E5",

    # Marca / gradiente
    "brand_accent":         "#4F46E5",
    "brand_gradient_start": "#4F46E5",
    "brand_gradient_mid":   "#6366F1",
    "brand_gradient_end":   "#7C3AED",

    # Chat
    "bg_chat":          "#F7F7FC",
    "bubble_sent":      "#4F46E5",
    "bubble_recv":      "#FFFFFF",

    # Tags / chips
    "tag_bg":           "#F0F1F7",
    "tag_text":         "#4B4E66",

    # Chips específicos (relatórios)
    "chip_geral_bg":        "#EEF0FF",
    "chip_geral_text":      "#4F46E5",
    "chip_estudante_bg":    "#DCFAEF",
    "chip_estudante_text":  "#059669",
    "chip_agenda_bg":       "#FEF3C7",
    "chip_agenda_text":     "#D97706",
    "export_item_bg":       "#EEF0FF",

    # Status
    "status_online":    "#059669",
    "status_offline":   "#D1D5DB",
    "status_busy":      "#D97706",

    # Inputs
    "input_bg":          "#FAFAFD",
    "input_border":      "#D5D7E4",
    "input_border_focus": "#4F46E5",
    "input_placeholder":  "#9C9FB4",
    "input_error":       "#DC2626",
    "input_error_soft":  "#FEE7E7",

    # Música
    "card_music":       "#4F46E5",
    "border_music":     "#4338CA",

    # Risco / bem-estar
    "critico":          "#DC2626",
    "critico_soft":     "#FEE7E7",
    "alto":             "#EA580C",
    "alto_soft":        "#FFEDD5",
    "medio":            "#D97706",
    "medio_soft":       "#FEF3C7",
    "normal":           "#059669",
    "normal_soft":      "#DCFAEF",

    # KPI
    "kpi_blue":         "#4F46E5",
    "kpi_blue_soft":    "#EEF0FF",
    "kpi_green":        "#059669",
    "kpi_green_soft":   "#DCFAEF",
    "kpi_red":          "#DC2626",
    "kpi_red_soft":     "#FEE7E7",
    "kpi_violet":       "#7C3AED",
    "kpi_violet_soft":  "#EFE9FE",
    "kpi_amber":        "#D97706",
    "kpi_amber_soft":   "#FEF3C7",
    "kpi_pink":         "#DB2777",
    "kpi_pink_soft":    "#FCE7F3",

    # Linhas de tabela
    "row_bg":           "#FAFAFD",
    "row_hover":        "#EEF0FF",

    # Gráfico
    "chart_grid":       "#E6E7F0",
    "chart_line":       "#4F46E5",
    "chart_fill":       "#EEF0FF",
    "chart_bar_1":      "#4F46E5",
    "chart_bar_2":      "#7C3AED",
    "chart_bar_3":      "#059669",
    "chart_bar_soft_1": "#EEF0FF",
    "chart_bar_soft_2": "#EFE9FE",
    "chart_bar_soft_3": "#DCFAEF",
    "dot_good":         "#059669",
    "dot_mid":          "#D97706",
    "dot_bad":          "#DC2626",

    # Overlay
    "overlay":          "#12142A",
    "overlay_light":    "#F8FAFC",

    # Shadows (referência semântica —” customtkinter não renderiza CSS,
    # usadas por widgets que simulam elevação com bordas/cores)
    "shadow_xs": "0 1px 2px 0 rgb(15 15 35 / 0.05)",
    "shadow_sm": "0 1px 3px 0 rgb(15 15 35 / 0.08), 0 1px 2px -1px rgb(15 15 35 / 0.08)",
    "shadow_md": "0 4px 6px -1px rgb(15 15 35 / 0.08), 0 2px 4px -2px rgb(15 15 35 / 0.08)",
    "shadow_lg": "0 10px 15px -3px rgb(15 15 35 / 0.10), 0 4px 6px -4px rgb(15 15 35 / 0.10)",
    "shadow_xl": "0 20px 25px -5px rgb(15 15 35 / 0.12), 0 8px 10px -6px rgb(15 15 35 / 0.12)",
}


# ——————————————————————————————————————————————————————————————————————————
#  Paleta —” Dark
#  Fundo azul-ardósia profundo (não preto puro) para reduzir fadiga visual;
#  a marca migra para tons mais claros de índigo para manter contraste AA.
# ——————————————————————————————————————————————————————————————————————————
DARK_THEME = {
    # Neutros / superfície
    "bg":               "#0E1120",
    "page_bg":          "#0E1120",
    "bg_alt":           "#181C30",
    "surface":          "#181C30",
    "surface_elevated": "#20253E",
    "border":           "#2B3050",
    "border_strong":    "#3C426B",
    "divider":          "#20253E",

    # Tipografia
    "text":             "#F4F5FB",
    "text_secondary":   "#C6C9DE",
    "text_muted":       "#8D91B0",
    "text_disabled":    "#565B80",
    "text_on_primary":  "#FFFFFF",

    # Marca / primária
    "primary":          "#818CF8",
    "primary_hover":    "#6C77F0",
    "primary_soft":     "#212555",
    "primary_medium":   "#383F7A",
    "primary_strong":   "#C7CBFA",
    "primary_light":    "#212555",

    # Acento / secundária
    "accent":           "#A78BFA",
    "accent_hover":     "#9270F8",
    "accent_soft":      "#2C2059",
    "accent_medium":    "#4C3F94",
    "accent_strong":    "#D8CCFC",

    # Semântico
    "success":          "#34D399",
    "success_soft":     "#0E3B31",
    "success_medium":   "#0F5A48",
    "success_strong":   "#8CF0C4",
    "warning":          "#FBBF24",
    "warning_soft":     "#3D2E0B",
    "warning_medium":   "#5B440F",
    "warning_strong":   "#FDD873",
    "danger":           "#F87171",
    "danger_soft":      "#3E1518",
    "danger_medium":    "#5C1E22",
    "danger_strong":    "#FCA5A5",
    "info":             "#60A5FA",
    "info_soft":        "#12244A",
    "info_medium":      "#1B3568",
    "info_strong":      "#A9CBFC",

    # Navegação
    "nav_bg":           "#171B2E",
    "nav_text":         "#9EA2C0",
    "nav_muted":        "#666B92",
    "nav_active_bg":    "#282C56",
    "nav_hover":        "#20233C",
    "nav_active_text":  "#B4BAFB",

    # Marca / gradiente
    "brand_accent":         "#818CF8",
    "brand_gradient_start": "#6366F1",
    "brand_gradient_mid":   "#8B5CF6",
    "brand_gradient_end":   "#A855F7",

    # Chat
    "bg_chat":          "#0E1120",
    "bubble_sent":      "#6366F1",
    "bubble_recv":      "#20253E",

    # Tags / chips
    "tag_bg":           "#20253E",
    "tag_text":         "#C6C9DE",

    # Chips específicos (relatórios)
    "chip_geral_bg":        "#212555",
    "chip_geral_text":      "#B4BAFB",
    "chip_estudante_bg":    "#0E3B31",
    "chip_estudante_text":  "#8CF0C4",
    "chip_agenda_bg":       "#3D2E0B",
    "chip_agenda_text":     "#FDD873",
    "export_item_bg":       "#212555",

    # Status
    "status_online":    "#34D399",
    "status_offline":   "#565B80",
    "status_busy":      "#FBBF24",

    # Inputs
    "input_bg":          "#181C30",
    "input_border":      "#3C426B",
    "input_border_focus": "#818CF8",
    "input_placeholder":  "#666B92",
    "input_error":       "#F87171",
    "input_error_soft":  "#3E1518",

    # Música
    "card_music":       "#6366F1",
    "border_music":     "#4F46E5",

    # Risco / bem-estar
    "critico":          "#F87171",
    "critico_soft":     "#3E1518",
    "alto":             "#FB923C",
    "alto_soft":        "#3F260D",
    "medio":            "#FBBF24",
    "medio_soft":       "#3D2E0B",
    "normal":           "#34D399",
    "normal_soft":      "#0E3B31",

    # KPI
    "kpi_blue":         "#818CF8",
    "kpi_blue_soft":    "#212555",
    "kpi_green":        "#34D399",
    "kpi_green_soft":   "#0E3B31",
    "kpi_red":          "#F87171",
    "kpi_red_soft":     "#3E1518",
    "kpi_violet":       "#A78BFA",
    "kpi_violet_soft":  "#2C2059",
    "kpi_amber":        "#FBBF24",
    "kpi_amber_soft":   "#3D2E0B",
    "kpi_pink":         "#F472B6",
    "kpi_pink_soft":    "#3E1330",

    # Linhas de tabela
    "row_bg":           "#181C30",
    "row_hover":        "#212555",

    # Gráfico
    "chart_grid":       "#20253E",
    "chart_line":       "#818CF8",
    "chart_fill":       "#212555",
    "chart_bar_1":      "#818CF8",
    "chart_bar_2":      "#A78BFA",
    "chart_bar_3":      "#34D399",
    "chart_bar_soft_1": "#212555",
    "chart_bar_soft_2": "#2C2059",
    "chart_bar_soft_3": "#0E3B31",
    "dot_good":         "#34D399",
    "dot_mid":          "#FBBF24",
    "dot_bad":          "#F87171",

    # Overlay
    "overlay":          "#05060D",
    "overlay_light":    "#F8FAFC",

    # Shadows
    "shadow_xs": "0 1px 2px 0 rgb(0 0 0 / 0.30)",
    "shadow_sm": "0 1px 3px 0 rgb(0 0 0 / 0.40), 0 1px 2px -1px rgb(0 0 0 / 0.40)",
    "shadow_md": "0 4px 6px -1px rgb(0 0 0 / 0.40), 0 2px 4px -2px rgb(0 0 0 / 0.40)",
    "shadow_lg": "0 10px 15px -3px rgb(0 0 0 / 0.40), 0 4px 6px -4px rgb(0 0 0 / 0.40)",
    "shadow_xl": "0 20px 25px -5px rgb(0 0 0 / 0.50), 0 8px 10px -6px rgb(0 0 0 / 0.50)",
}


# ——————————————————————————————————————————————————————————————————————————
#  Estado do tema ativo + listeners
# ——————————————————————————————————————————————————————————————————————————
THEME = LIGHT_THEME.copy()
_current_mode: Literal["light", "dark"] = "light"
_LISTENERS: list[Callable[[str], None]] = []


def get_theme() -> dict:
    """Retorna o dicionário do tema ativo (mesma referência de THEME)."""
    return THEME


def current() -> dict:
    """Alias explícito de get_theme(), preferível em código novo:
    sempre lê o tema *atual*, mesmo se chamado bem depois de um toggle.
    """
    return THEME


def get_mode() -> str:
    return _current_mode


def on_theme_change(callback: Callable[[str], None]) -> None:
    """Registra um callback chamado com o novo modo ('light'/'dark')
    sempre que o tema mudar. Usado pelo shell principal (app.py) para
    reconstruir a interface com as cores corretas ao alternar o tema —”
    CustomTkinter não atualiza cores de widgets já criados sozinho.
    """
    if callback not in _LISTENERS:
        _LISTENERS.append(callback)


def off_theme_change(callback: Callable[[str], None]) -> None:
    if callback in _LISTENERS:
        _LISTENERS.remove(callback)


def set_mode(mode: Literal["light", "dark"]) -> None:
    global _current_mode, THEME
    if mode not in ("light", "dark"):
        mode = "light"
    _current_mode = mode
    THEME.clear()
    THEME.update(LIGHT_THEME if mode == "light" else DARK_THEME)
    try:
        ctk.set_appearance_mode(mode)
    except Exception:
        pass
    for cb in list(_LISTENERS):
        try:
            cb(mode)
        except Exception:
            pass


def toggle_mode() -> str:
    new_mode = "dark" if _current_mode == "light" else "light"
    set_mode(new_mode)
    return new_mode


def apply_global_style(mode: Literal["light", "dark"] = "light", color_theme: str = "blue") -> None:
    """Aplica aparência global e valores padrão sensatos para o app."""
    try:
        ctk.set_default_color_theme(color_theme)
    except Exception:
        pass
    set_mode(mode)


# ——————————————————————————————————————————————————————————————————————————
#  Espaçamento / raio / elevação / tipografia / animação
# ——————————————————————————————————————————————————————————————————————————
SPACING = {
    "page_x": 32,
    "page_y": 28,
    "section_gap": 24,
    "card_pad": 24,
    "item_gap": 14,
    "input_y": 12,
    "label_gap": 8,
    "icon_gap": 12,
    "button_pad_x": 20,
    "button_pad_y": 12,
    "grid_gap": 20,
}

RADIUS = {
    "none": 0,
    "xs": 4,
    "sm": 6,
    "md": 8,
    "lg": 12,
    "xl": 16,
    "2xl": 20,
    "pill": 999,
    "button": 8,
    "card": 16,
    "input": 10,
    "modal": 20,
    "avatar": 999,
}

ELEVATION = {
    "flat": 0,
    "raised": 1,
    "overlay": 8,
    "modal": 16,
}

TYPO = {
    "display": 36,
    "h1": 30,
    "h2": 24,
    "h3": 18,
    "h4": 16,
    "body": 14,
    "body_sm": 13,
    "caption": 12,
    "overline": 10,
    "button": 14,
}

ANIMATION = {
    "duration_fast": 150,
    "duration_normal": 250,
    "duration_slow": 400,
    "easing": "ease-in-out",
}


# ——————————————————————————————————————————————————————————————————————————
#  Fontes
# ——————————————————————————————————————————————————————————————————————————
def font(
    size: int = 14,
    weight: Literal["normal", "bold"] = "normal",
    family: str = FONT_FAMILY,
) -> ctk.CTkFont:
    return ctk.CTkFont(family=family, size=size, weight=weight)


def themed_font(
    role: Literal["display", "h1", "h2", "h3", "h4", "body", "body_sm", "caption", "overline", "button"],
    weight: Literal["normal", "bold"] = "normal",
) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=TYPO[role], weight=weight)


def mono_font(size: int = 12) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY_MONO, size=size)


# ——————————————————————————————————————————————————————————————————————————
#  Utilitários de cor
# ——————————————————————————————————————————————————————————————————————————
def _hex_to_rgb(hex_c: str) -> tuple[int, int, int]:
    hex_c = hex_c.lstrip("#")
    return int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def blend_color(hex_c: str, alpha: float, base: str | None = None) -> str:
    """Mistura hex_c sobre `base` (padrão: fundo de superfície do tema ativo)
    com a opacidade `alpha`. Antes, o fundo era sempre branco fixo —” o que
    quebrava a mistura no modo escuro. Agora respeita o tema ativo.
    """
    base = base or THEME["surface"]
    r, g, b = _hex_to_rgb(hex_c)
    br, bg, bb = _hex_to_rgb(base)
    return _rgb_to_hex(
        int(r * alpha + br * (1 - alpha)),
        int(g * alpha + bg * (1 - alpha)),
        int(b * alpha + bb * (1 - alpha)),
    )


def darken(hex_c: str, amount: float = 0.15) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    return _rgb_to_hex(int(r * (1 - amount)), int(g * (1 - amount)), int(b * (1 - amount)))


def lighten(hex_c: str, amount: float = 0.15) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    return _rgb_to_hex(
        int(r + (255 - r) * amount),
        int(g + (255 - g) * amount),
        int(b + (255 - b) * amount),
    )


def shift_hue(hex_c: str, degrees: float) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + degrees / 360) % 1.0
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
    return _rgb_to_hex(int(r2 * 255), int(g2 * 255), int(b2 * 255))


def readable_text_color(bg_hex: str) -> str:
    """Retorna preto ou branco, o que tiver melhor contraste sobre bg_hex.
    Útil para avatares/badges com cor dinâmica (ex.: iniciais de estudantes)."""
    r, g, b = _hex_to_rgb(bg_hex)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#14162B" if luminance > 0.6 else "#FFFFFF"


# ——————————————————————————————————————————————————————————————————————————
#  Constantes semânticas usadas pelas views
# ——————————————————————————————————————————————————————————————————————————
# ——————————————————————————————————————————————————————————————————————————
#  Constantes semânticas usadas pelas views
# ——————————————————————————————————————————————————————————————————————————
SEMANTIC_COLORS = {
    "positive": "#10B981",
    "negative": "#EF4444",
    "neutral":  "#6366F1",
    "caution":  "#F59E0B",
    "info":     "#3B82F6",
}

STATUS_COLORS = {
    "active":   "#10B981",
    "inactive": "#94A3B8",
    "pending":  "#F59E0B",
    "blocked":  "#EF4444",
    "review":   "#6366F1",
}

PRIORITY_COLORS = {
    "Urgente": ("critico", "critico_soft"),
    "Alta":    ("alto",    "alto_soft"),
    "Média":   ("medio",   "medio_soft"),
    "Baixa":   ("normal",  "normal_soft"),
}

# MOOD_* movidos para ser_pleno.ui.components.icons para evitar corrupção
# de encoding e centralizar emojis em uma única fonte.


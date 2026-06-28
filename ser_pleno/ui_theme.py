import customtkinter as ctk
from typing import Literal

import platform

# Prefer platform-native UI fonts with fallbacks for consistency
_PLATFORM = platform.system()
if _PLATFORM == "Windows":
    FONT_FAMILY = "Segoe UI"
elif _PLATFORM == "Darwin":
    FONT_FAMILY = "San Francisco" if False else "Helvetica Neue"
else:
    FONT_FAMILY = "Inter"

FONT_FAMILY_MONO = "JetBrains Mono"

# Paleta semântica unificada (SerPleno Design System)
# Família de cor principal: índigo (#4F46E5) alinhada com o design existente

LIGHT_THEME = {
    # Neutros / superfície
    "bg":               "#F8F7FF",
    "page_bg":          "#F8F7FF",
    "bg_alt":           "#F1F5F9",
    "surface":          "#FFFFFF",
    "surface_elevated": "#FFFFFF",
    "border":           "#E5E7EB",
    "border_strong":    "#CBD5E1",
    "divider":          "#F3F4F6",

    # Tipografia
    "text":             "#111827",
    "text_secondary":   "#6B7280",
    "text_muted":       "#9CA3AF",
    "text_disabled":    "#D1D5DB",
    "text_on_primary":  "#FFFFFF",

    # Marca / primária (alinhada com o design existente nas views)
    "primary":          "#4F46E5",
    "primary_hover":    "#4338CA",
    "primary_soft":     "#EEF2FF",
    "primary_medium":   "#C7D2FE",
    "primary_strong":   "#312E81",
    "primary_light":    "#EEF2FF",

    # Acento / secundária
    "accent":           "#6366F1",
    "accent_hover":     "#4F46E5",
    "accent_soft":      "#EEF2FF",
    "accent_medium":    "#A5B4FC",
    "accent_strong":    "#3730A3",

    # Semântico
    "success":          "#059669",
    "success_soft":     "#D1FAE5",
    "success_medium":   "#A7F3D0",
    "success_strong":   "#065F46",
    "warning":          "#D97706",
    "warning_soft":     "#FEF3C7",
    "warning_medium":   "#FDE68A",
    "warning_strong":   "#92400E",
    "danger":           "#DC2626",
    "danger_soft":      "#FEE2E2",
    "danger_medium":    "#FECACA",
    "danger_strong":    "#991B1B",
    "info":             "#3B82F6",
    "info_soft":        "#DBEAFE",
    "info_medium":      "#BFDBFE",
    "info_strong":      "#1D4ED8",

    # Navegação
    "nav_bg":           "#FFFFFF",
    "nav_text":         "#64748B",
    "nav_muted":        "#94A3B8",
    "nav_active_bg":    "#EEF2FF",
    "nav_hover":        "#F8FAFC",
    "nav_active_text":  "#4F46E5",

    # Marca / gradiente
    "brand_accent":     "#4F46E5",
    "brand_gradient_start": "#4F46E5",
    "brand_gradient_mid":   "#6366F1",
    "brand_gradient_end":   "#7C3AED",

    # Chat
    "bg_chat":          "#F8F7FF",
    "bubble_sent":      "#4F46E5",
    "bubble_recv":      "#FFFFFF",

    # Tags / chips
    "tag_bg":           "#F3F4F6",
    "tag_text":         "#4B5563",

    # Status
    "status_online":    "#059669",
    "status_offline":   "#D1D5DB",
    "status_busy":      "#D97706",

    # Inputs
    "input_bg":         "#F9FAFB",
    "input_border":     "#D1D5DB",
    "input_border_focus":"#4F46E5",
    "input_placeholder": "#9CA3AF",

    # Música
    "card_music":       "#4F46E5",
    "border_music":     "#4338CA",

    # Risco / bem-estar
    "critico":          "#DC2626",
    "critico_soft":     "#FEE2E2",
    "alto":             "#EA580C",
    "alto_soft":        "#FFEDD5",
    "medio":            "#D97706",
    "medio_soft":       "#FEF3C7",
    "normal":           "#059669",
    "normal_soft":      "#D1FAE5",

    # KPI
    "kpi_blue":         "#4F46E5",
    "kpi_blue_soft":    "#EEF2FF",
    "kpi_green":        "#059669",
    "kpi_green_soft":   "#D1FAE5",
    "kpi_red":          "#DC2626",
    "kpi_red_soft":     "#FEE2E2",
    "kpi_violet":       "#7C3AED",
    "kpi_violet_soft":  "#EDE9FE",
    "kpi_amber":        "#D97706",
    "kpi_amber_soft":   "#FEF3C7",
    "kpi_pink":         "#DB2777",
    "kpi_pink_soft":    "#FCE7F3",

    # Gráfico
    "chart_grid":       "#E5E7EB",
    "chart_line":       "#4F46E5",
    "chart_fill":       "#EEF2FF",
    "dot_good":         "#059669",
    "dot_mid":          "#D97706",
    "dot_bad":          "#DC2626",

    # Chips / tags específicas de relatórios
    "chip_geral_bg":    "#EEF2FF",
    "chip_geral_text":  "#4F46E5",
    "chip_estudante_bg":"#D1FAE5",
    "chip_estudante_text":"#065F46",
    "chip_agenda_bg":   "#FEF3C7",
    "chip_agenda_text": "#92400E",
    "chip_default_bg":  "#F3F4F6",
    "chip_default_text":"#374151",
    "chip_intervencoes_bg":"#EDE9FE",
    "chip_intervencoes_text":"#5B21B6",
    "chip_triagens_bg": "#FEF3C7",
    "chip_triagens_text":"#92400E",
    "chip_estatisticas_bg":"#F5F3FF",
    "chip_estatisticas_text":"#4F46E5",

    # Exportação
    "export_item_bg":   "#F5F3FF",
    "export_item_hover":"#EEF2FF",

    # Lista de relatórios
    "row_bg":           "#FAFAFA",
    "row_hover":        "#F5F3FF",
    "row_border":       "#F3F4F6",

    # Gráfico de barras (relatórios)
    "chart_bar_1":      "#4F46E5",
    "chart_bar_2":      "#059669",
    "chart_bar_3":      "#D97706",
    "chart_bar_soft_1": "#C7D2FE",
    "chart_bar_soft_2": "#6EE7B7",
    "chart_bar_soft_3": "#FDE68A",

    # Gráfico
    "chart_grid":       "#E5E7EB",
    "chart_line":       "#4F46E5",
    "chart_fill":       "#EEF2FF",
    "dot_good":         "#059669",
    "dot_mid":          "#D97706",
    "dot_bad":          "#DC2626",

    # Overlay
    "overlay":          "#0F172A",
    "overlay_light":    "#F8FAFC",

    # Shadows
    "shadow_xs": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "shadow_sm": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
    "shadow_md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    "shadow_lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    "shadow_xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
}


DARK_THEME = {
    # Neutros / superfície
    "bg":               "#0F172A",
    "page_bg":          "#0F172A",
    "bg_alt":           "#1E293B",
    "surface":          "#1E293B",
    "surface_elevated": "#334155",
    "border":           "#334155",
    "border_strong":    "#475569",
    "divider":          "#1E293B",

    # Tipografia
    "text":             "#F8FAFC",
    "text_secondary":   "#CBD5E1",
    "text_muted":       "#94A3B8",
    "text_disabled":    "#64748B",
    "text_on_primary":  "#FFFFFF",

    # Marca / primária
    "primary":          "#818CF8",
    "primary_hover":    "#6366F1",
    "primary_soft":     "#1E1B4B",
    "primary_medium":   "#312E81",
    "primary_strong":   "#A5B4FC",
    "primary_light":    "#1E1B4B",

    # Acento / secundária
    "accent":           "#A78BFA",
    "accent_hover":     "#8B5CF6",
    "accent_soft":      "#2E1065",
    "accent_medium":    "#4C1D95",
    "accent_strong":    "#C4B5FD",

    # Semântico
    "success":          "#34D399",
    "success_soft":     "#064E3B",
    "success_medium":   "#065F46",
    "success_strong":   "#6EE7B7",
    "warning":          "#FBBF24",
    "warning_soft":     "#78350F",
    "warning_medium":   "#92400E",
    "warning_strong":   "#FCD34D",
    "danger":           "#F87171",
    "danger_soft":      "#7F1D1D",
    "danger_medium":    "#991B1B",
    "danger_strong":    "#FCA5A5",
    "info":             "#60A5FA",
    "info_soft":        "#1E3A8A",
    "info_medium":      "#1E40AF",
    "info_strong":      "#93C5FD",

    # Navegação
    "nav_bg":           "#1E293B",
    "nav_text":         "#94A3B8",
    "nav_muted":        "#64748B",
    "nav_active_bg":    "#312E81",
    "nav_hover":        "#334155",
    "nav_active_text":  "#A5B4FC",

    # Marca / gradiente
    "brand_accent":     "#818CF8",
    "brand_gradient_start": "#6366F1",
    "brand_gradient_mid":   "#8B5CF6",
    "brand_gradient_end":   "#A855F7",

    # Chat
    "bg_chat":          "#0F172A",
    "bubble_sent":      "#6366F1",
    "bubble_recv":      "#334155",

    # Tags / chips
    "tag_bg":           "#334155",
    "tag_text":         "#CBD5E1",

    # Status
    "status_online":    "#34D399",
    "status_offline":   "#64748B",
    "status_busy":      "#FBBF24",

    # Inputs
    "input_bg":         "#1E293B",
    "input_border":     "#334155",
    "input_border_focus":"#818CF8",
    "input_placeholder": "#64748B",

    # Música
    "card_music":       "#6366F1",
    "border_music":     "#4F46E5",

    # Risco / bem-estar
    "critico":          "#F87171",
    "critico_soft":     "#7F1D1D",
    "alto":             "#F97316",
    "alto_soft":        "#7C2D12",
    "medio":            "#FBBF24",
    "medio_soft":       "#78350F",
    "normal":           "#34D399",
    "normal_soft":      "#064E3B",

    # KPI
    "kpi_blue":         "#818CF8",
    "kpi_blue_soft":    "#1E1B4B",
    "kpi_green":        "#34D399",
    "kpi_green_soft":   "#064E3B",
    "kpi_red":          "#F87171",
    "kpi_red_soft":     "#7F1D1D",
    "kpi_violet":       "#A78BFA",
    "kpi_violet_soft":  "#2E1065",
    "kpi_amber":        "#FBBF24",
    "kpi_amber_soft":   "#78350F",
    "kpi_pink":         "#F472B6",
    "kpi_pink_soft":    "#831843",

    # Gráfico
    "chart_grid":       "#1E293B",
    "chart_line":       "#818CF8",
    "chart_fill":       "#1E1B4B",
    "dot_good":         "#34D399",
    "dot_mid":          "#FBBF24",
    "dot_bad":          "#F87171",

    # Overlay
    "overlay":          "#000000",
    "overlay_light":    "#F8FAFC",

    # Shadows
    "shadow_xs": "0 1px 2px 0 rgb(0 0 0 / 0.3)",
    "shadow_sm": "0 1px 3px 0 rgb(0 0 0 / 0.4), 0 1px 2px -1px rgb(0 0 0 / 0.4)",
    "shadow_md": "0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.4)",
    "shadow_lg": "0 10px 15px -3px rgb(0 0 0 / 0.4), 0 4px 6px -4px rgb(0 0 0 / 0.4)",
    "shadow_xl": "0 20px 25px -5px rgb(0 0 0 / 0.5), 0 8px 10px -6px rgb(0 0 0 / 0.5)",
}


THEME = LIGHT_THEME.copy()

_current_mode: Literal["light", "dark"] = "light"


def get_theme() -> dict:
    return THEME


def get_mode() -> str:
    return _current_mode


def set_mode(mode: Literal["light", "dark"]) -> None:
    global _current_mode, THEME
    _current_mode = mode
    THEME = LIGHT_THEME.copy() if mode == "light" else DARK_THEME.copy()
    ctk.set_appearance_mode(mode)


def toggle_mode() -> str:
    new_mode = "dark" if _current_mode == "light" else "light"
    set_mode(new_mode)
    return new_mode


def apply_global_style(mode: Literal["light", "dark"] = "light", color_theme: str = "blue") -> None:
    """Apply global appearance and sensible defaults for the app.

    - Sets appearance mode (light/dark)
    - Applies a default color theme
    - Ensures customtkinter uses the selected mode
    """
    try:
        ctk.set_appearance_mode(mode)
    except Exception:
        pass
    try:
        ctk.set_default_color_theme(color_theme)
    except Exception:
        pass


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


def _hex_to_rgb(hex_c: str) -> tuple[int, int, int]:
    hex_c = hex_c.lstrip("#")
    return int(hex_c[0:2], 16), int(hex_c[2:4], 16), int(hex_c[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def blend_color(hex_c: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    return _rgb_to_hex(
        int(r * alpha + 255 * (1 - alpha)),
        int(g * alpha + 255 * (1 - alpha)),
        int(b * alpha + 255 * (1 - alpha)),
    )


def darken(hex_c: str, amount: float = 0.15) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return _rgb_to_hex(r, g, b)


def lighten(hex_c: str, amount: float = 0.15) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return _rgb_to_hex(r, g, b)


def shift_hue(hex_c: str, degrees: float) -> str:
    r, g, b = _hex_to_rgb(hex_c)
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + degrees / 360) % 1.0
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
    return _rgb_to_hex(int(r2 * 255), int(g2 * 255), int(b2 * 255))


SEMANTIC_COLORS = {
    "positive": "#10B981",
    "negative": "#EF4444",
    "neutral":  "#6366F1",
    "caution":  "#F59E0B",
    "info":     "#3B82F6",
}

STATUS_COLORS = {
    "active":   "#10B981",
    "inactive": "#CBD5E1",
    "pending":  "#F59E0B",
    "blocked":  "#EF4444",
    "review":   "#6366F1",
}

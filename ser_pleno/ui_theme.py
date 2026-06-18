import customtkinter as ctk
from typing import Literal

FONT_FAMILY = "Inter"
FONT_FAMILY_MONO = "JetBrains Mono"

THEME = {
    "bg": "#F8FAFC",
    "bg_alt": "#F1F5F9",
    "surface": "#FFFFFF",
    "surface_elevated": "#FFFFFF",
    "border": "#E2E8F0",
    "border_strong": "#CBD5E1",
    "divider": "#F1F5F9",
    "text": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#94A3B8",
    "text_disabled": "#CBD5E1",
    "text_on_primary": "#FFFFFF",
    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "primary_soft": "#EEF2FF",
    "primary_medium": "#C7D2FE",
    "primary_strong": "#4338CA",
    "accent": "#8B5CF6",
    "accent_soft": "#F5F3FF",
    "accent_medium": "#DDD6FE",
    "success": "#10B981",
    "success_soft": "#D1FAE5",
    "success_medium": "#A7F3D0",
    "success_strong": "#047857",
    "warning": "#F59E0B",
    "warning_soft": "#FEF3C7",
    "warning_medium": "#FDE68A",
    "warning_strong": "#B45309",
    "danger": "#EF4444",
    "danger_soft": "#FEE2E2",
    "danger_medium": "#FECACA",
    "danger_strong": "#B91C1C",
    "info": "#3B82F6",
    "info_soft": "#DBEAFE",
    "info_medium": "#BFDBFE",
    "info_strong": "#1D4ED8",
    "nav_bg": "#FFFFFF",
    "nav_text": "#64748B",
    "nav_muted": "#94A3B8",
    "nav_active_bg": "#EEF2FF",
    "nav_hover": "#F8FAFC",
    "nav_active_text": "#6366F1",
    "brand_accent": "#6366F1",
    "brand_gradient_start": "#6366F1",
    "brand_gradient_mid": "#8B5CF6",
    "brand_gradient_end": "#A855F7",
    "bg_chat": "#F8FAFC",
    "card": "#FFFFFF",
    "primary_light": "#EEF2FF",
    "bubble_sent": "#6366F1",
    "bubble_recv": "#FFFFFF",
    "tag_bg": "#F1F5F9",
    "tag_text": "#475569",
    "status_online": "#10B981",
    "status_offline": "#CBD5E1",
    "status_busy": "#F59E0B",
    "input_bg": "#FFFFFF",
    "input_border": "#E2E8F0",
    "input_border_focus": "#6366F1",
    "input_placeholder": "#94A3B8",
    "card_music": "#6366F1",
    "border_music": "#4F46E5",
    "purple": "#7E22CE",
    "purple_light": "#F3E8FF",
    "purple_soft": "#EDE9FE",
    "chart_grid": "#F1F5F9",
    "chart_line": "#6366F1",
    "chart_area_start": "#6366F1",
    "chart_area_end": "#FFFFFF",
    "overlay": "#0F172A",
    "overlay_light": "#F8FAFC",
    "shadow_xs": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "shadow_sm": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
    "shadow_md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    "shadow_lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    "shadow_xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
}

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
    "neutral": "#6366F1",
    "caution": "#F59E0B",
    "info": "#3B82F6",
}

STATUS_COLORS = {
    "active": "#10B981",
    "inactive": "#CBD5E1",
    "pending": "#F59E0B",
    "blocked": "#EF4444",
    "review": "#6366F1",
}

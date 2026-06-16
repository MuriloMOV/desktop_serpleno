import customtkinter as ctk
from typing import Literal

# ============================================================
# SerPleno — Design System (CustomTkinter)
# ============================================================

FONT_FAMILY = "Inter"

THEME = {
    # Base
    "bg": "#F9FAFB",
    "bg_alt": "#F3F4F6",
    "card": "#FFFFFF",
    "border": "#E5E7EB",
    "border_strong": "#D1D5DB",
    "divider": "#E5E7EB",
    # Texto
    "text": "#111827",
    "text_secondary": "#374151",
    "text_muted": "#6B7280",
    "text_disabled": "#9CA3AF",
    "text_on_primary": "#FFFFFF",
    # Primária (Indigo)
    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "primary_light": "#EEF2FF",
    "primary_soft": "#C7D2FE",
    # Feedback
    "success": "#10B981",
    "success_soft": "#D1FAE5",
    "success_strong": "#059669",
    "warning": "#F59E0B",
    "warning_soft": "#FEF3C7",
    "warning_strong": "#D97706",
    "danger": "#EF4444",
    "danger_soft": "#FEE2E2",
    "danger_strong": "#DC2626",
    "info": "#3B82F6",
    "info_soft": "#DBEAFE",
    "info_strong": "#2563EB",
    # Sidebar / Navegação
    "nav_bg": "#FFFFFF",
    "nav_text": "#6B7280",
    "nav_muted": "#9CA3AF",
    "nav_active_bg": "#EEF2FF",
    "nav_hover": "#F9FAFB",
    "nav_active_text": "#6366F1",
    "brand_accent": "#6366F1",
    # Chat
    "bg_chat": "#F8FAFC",
    "bubble_sent": "#6366F1",
    "bubble_recv": "#FFFFFF",
    # Tags / Status
    "tag_bg": "#EEF2FF",
    "tag_text": "#4F46E5",
    "status_online": "#10B981",
    "status_offline": "#9CA3AF",
    # Superfícies especiais
    "input_bg": "#FFFFFF",
    "input_border": "#E5E7EB",
    "input_border_focus": "#6366F1",
    "shadow": "#00000012",
    "overlay": "#00000040",
    # Gradientes sutis (para uso em elementos pontuais)
    "gradient_primary_start": "#6366F1",
    "gradient_primary_end": "#8B5CF6",
    "gradient_danger_start": "#EF4444",
    "gradient_danger_end": "#DC2626",
    # Login / extras
    "card_music": "#6366F1",
    "border_music": "#523C8F",
}

SPACING = {
    "page_x": 32,
    "page_y": 24,
    "section_gap": 20,
    "card_pad": 20,
    "item_gap": 12,
    "input_y": 10,
    "label_gap": 6,
    "icon_gap": 10,
    "button_pad_x": 16,
    "button_pad_y": 10,
}

RADIUS = {
    "xs": 6,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 20,
    "pill": 999,
    "button": 10,
    "card": 16,
    "input": 12,
}

ELEVATION = {
    "flat": 0,
    "raised": 1,
    "overlay": 8,
}

TYPO = {
    "display": 28,
    "h1": 24,
    "h2": 20,
    "h3": 16,
    "body": 14,
    "caption": 12,
    "overline": 11,
}


def font(
    size: int = 14,
    weight: Literal["normal", "bold"] = "normal",
    family: str = FONT_FAMILY,
) -> ctk.CTkFont:
    return ctk.CTkFont(family=family, size=size, weight=weight)


def themed_font(role: Literal["display", "h1", "h2", "h3", "body", "caption", "overline"], weight: Literal["normal", "bold"] = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=TYPO[role], weight=weight)

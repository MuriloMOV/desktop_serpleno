import customtkinter as ctk
from typing import Literal

# Tema global do Desktop SerPleno
FONT_FAMILY = "Inter"

THEME = {
    # Base
    "bg": "#F9FAFB",
    "bg_alt": "#F3F4F6",
    "card": "#FFFFFF",
    "border": "#E5E7EB",
    # Texto
    "text": "#111827",
    "text_main": "#111827",
    "text_muted": "#6B7280",
    "text_highlight": "#9CA3AF",
    # Primária
    "primary": "#6366F1",
    "primary_hover": "#4F46E5",
    "primary_light": "#EEF2FF",
    # Feedback
    "success": "#10B981",
    "success_light": "#D1FAE5",
    "warning": "#F59E0B",
    "warning_light": "#FEF3C7",
    "danger": "#EF4444",
    "danger_light": "#FEE2E2",
    "info": "#3B82F6",
    "info_light": "#DBEAFE",
    "slot_green_bg": "#F0FDF4",
    "slot_green_text": "#16A34A",
    "slot_purple_bg": "#EEF2FF",
    "slot_purple_text": "#3B5BDB",
    # Chat
    "bg_chat": "#F1F5F9",
    "bubble_sent": "#6366F1",
    "bubble_recv": "#FFFFFF",
    # Tags
    "tag_bg": "#EEF2FF",
    "tag_text": "#4F46E5",
    # Extras
    "purple_light": "#F5F3FF",
    "purple_icon": "#8B5CF6",
    # Sidebar
    "nav_bg": "#FFFFFF",
    "nav_text": "#6B7280",
    "nav_muted": "#9CA3AF",
    "nav_active_bg": "#EEF2FF",
    "nav_hover": "#F9FAFB",
    "nav_active_text": "#6366F1",
    "brand_accent": "#6366F1",
    # Status
    "pending": {"bg": "#FEF3C7", "fg": "#D97706"},
    "completed": {"bg": "#DCFCE7", "fg": "#16A34A"},
    "critical": {"bg": "#FEE2E2", "fg": "#EF4444"},
}

SPACING = {
    "page_x": 32,
    "page_y": 24,
    "section_gap": 20,
    "card_pad": 20,
    "item_gap": 12,
}

RADIUS = {
    "card": 16,
    "button": 10,
    "input": 12,
    "pill": 999,
}


def font(size: int = 14, weight: Literal["normal", "bold"] = "normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

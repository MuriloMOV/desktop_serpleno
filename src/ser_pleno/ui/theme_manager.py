"""Gerenciador de tema da aplicação SerPleno."""

from __future__ import annotations

from ser_pleno.ui.theme import THEME, toggle_mode, on_theme_change, get_mode
from ser_pleno.ui.components.icons import ICONS


class ThemeManager:
    """Gerencia alternância de tema e reconstrução de UI."""

    def __init__(self, app):
        self.app = app
        on_theme_change(self._on_theme_changed)

    def toggle(self):
        """Alterna entre tema claro e escuro."""
        try:
            self.app.focus()
        except Exception:
            pass
        toggle_mode()

    def _on_theme_changed(self, mode: str) -> None:
        """Reconstrói a interface autenticada com as cores do novo tema."""
        if not self.app.winfo_exists():
            return
        self.app.configure(fg_color=THEME["bg"])
        if hasattr(self.app, "container") and self.app.container.winfo_exists():
            self.app.container.configure(fg_color=THEME["bg"])

        if not self.app.usuario_logado:
            if self.app._is_login_active():
                self.app.mostrar_login()
            return

        tela_anterior = self.app.navigation.get_active_screen()
        self.app.navigation.clear_screen()
        self.app.navigation.create_sidebar()
        self.app.navigation.create_content_area()
        self.app.navigation.show(tela_anterior)

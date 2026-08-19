"""Gerenciador de navegação da aplicação SerPleno."""

from __future__ import annotations

import logging
import time
from collections import OrderedDict

import customtkinter as ctk

from ser_pleno.infrastructure.desktop.native_notifier import get_desktop_notifier
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.components.ui_components import Avatar, Divider, GhostButton
from ser_pleno.ui.theme import SPACING, THEME, font
from ser_pleno.ui.view_factory import ViewFactory
from ser_pleno.utils.async_runner import AsyncRunner

logger = logging.getLogger(__name__)

MENU_ITEMS = [
    {"key": "dashboard",     "label": "Painel",         "icon": ICONS["chart"],
     "header": ("Painel", "Resumo geral do ambiente")},
    {"key": "estudantes",    "label": "Estudantes",        "icon": ICONS["users"],
     "header": ("Estudantes", "Acompanhamento e gestao academica")},
    {"key": "agenda",        "label": "Agenda",            "icon": ICONS["calendar"],
     "header": ("Agenda", "Planejamento e compromissos")},
    {"key": "bem_estar",     "label": "Bem-estar",         "icon": ICONS["heart_blue"],
     "header": ("Bem-estar", "Monitoramento e apoio emocional")},
    {"key": "analise",       "label": "Analise",           "icon": ICONS["search"],
     "header": ("Analise", "Triagem e classificacao")},
    {"key": "relatorios",    "label": "Relatorios",        "icon": ICONS["document"],
     "header": ("Relatorios", "Indicadores e exportacoes")},
    {"key": "comunicacao",   "label": "Comunicacao",       "icon": ICONS["chat"],
     "header": ("Comunicacao", "Mensagens internas e suporte")},
    {"key": "orientacoes",   "label": "Orientacoes",       "icon": ICONS["compass"],
     "header": ("Orientacoes", "Fluxo de apoio e encaminhamentos")},
    {"key": "intervencoes",  "label": "Intervencoes",      "icon": ICONS["heart_blue"],
     "header": ("Intervencoes", "Gestao de intervencoes e acompanhamentos")},
    {"key": "wellness_challenges", "label": "Wellness Challenges", "icon": ICONS["heart"],
     "header": ("Wellness Challenges", "Desafios e metas de bem-estar")},
    {"key": "avisos",        "label": "Quadro de avisos",  "icon": ICONS["megaphone"],
     "header": ("Avisos", "Quadro de comunicacao institucional")},
    {"key": "configuracoes", "label": "Configuracoes",     "icon": ICONS["settings"],
     "header": ("Configuracoes", "Preferencias da aplicacao")},
]
_MENU_BY_KEY = {item["key"]: item for item in MENU_ITEMS}

SIDEBAR_WIDTH = 272
PAGE_HEADER_HEIGHT = 86
VIEW_CACHE_MAXSIZE = 8


class NavigationManager:
    """Gerencia a navegação entre telas da aplicação."""

    def __init__(self, app, auth_service=None):
        self.app = app
        self._active_menu_key = None
        self.menu_buttons = {}
        self.view_factory = ViewFactory(app)
        self._view_cache: OrderedDict[str, ctk.CTkFrame] = OrderedDict()
        self._current_view: ctk.CTkFrame | None = None
        self._desktop_notifier = get_desktop_notifier()
        self._notification_poll_after_id = None

    # ================= SIDEBAR =================
    def create_sidebar(self):
        self.app.sidebar = ctk.CTkFrame(
            self.app.container,
            width=SIDEBAR_WIDTH,
            fg_color=THEME["nav_bg"],
            corner_radius=0,
            border_width=0,
        )
        self.app.sidebar.grid(row=0, column=0, sticky="nsew")
        self.app.sidebar.pack_propagate(False)

        self._create_brand()
        Divider(self.app.sidebar).pack(fill="x", padx=18, pady=(6, 16))

        menu_label = ctk.CTkLabel(
            self.app.sidebar,
            text="NAVEGACAO",
            font=font(11, "bold"),
            text_color=THEME["text_muted"],
        )
        menu_label.pack(anchor="w", padx=22, pady=(4, 10))

        self.app.menu_container = ctk.CTkScrollableFrame(
            self.app.sidebar, fg_color="transparent",
            scrollbar_button_color=THEME["nav_bg"],
            scrollbar_button_hover_color=THEME["border_strong"],
        )
        self.app.menu_container.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        self._create_menu()
        self._create_sidebar_footer()

    def _create_brand(self):
        brand_frame = ctk.CTkFrame(self.app.sidebar, fg_color="transparent")
        brand_frame.pack(pady=(24, 16), padx=20, fill="x")

        icon_lbl = ctk.CTkLabel(
            brand_frame,
            text=f"{ICONS['group']} ",
            font=font(22, "bold"),
            text_color=THEME["brand_accent"],
        )
        icon_lbl.pack(side="left", padx=(0, 10))

        title_frame = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_frame,
            text="SerPleno",
            font=font(20, "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame,
            text="Gestao escolar e bem-estar",
            font=font(11),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w")

    def _create_sidebar_footer(self):
        footer = ctk.CTkFrame(self.app.sidebar, fg_color="transparent")
        footer.pack(fill="x", padx=18, pady=(12, 18), side="bottom")

        nome = self.app.usuario_logado.get("first_name") or self.app.usuario_logado.get("username", "usuario")
        iniciais = "".join(p[0] for p in nome.split()[:2]).upper() or "U"

        self.app.user_chip = ctk.CTkFrame(footer, fg_color=THEME["primary_soft"], corner_radius=14)
        self.app.user_chip.pack(fill="x", pady=(0, 10))

        chip_inner = ctk.CTkFrame(self.app.user_chip, fg_color="transparent")
        chip_inner.pack(fill="x", padx=12, pady=10)

        Avatar(chip_inner, initials=iniciais, size=36, color=THEME["primary"]).pack(side="left", padx=(0, 10))

        texto_frame = ctk.CTkFrame(chip_inner, fg_color="transparent")
        texto_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            texto_frame,
            text=f"Ola, {nome}",
            font=font(12, "bold"),
            text_color=THEME["primary"],
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            texto_frame,
            text="Psicologa(o) escolar",
            font=font(10),
            text_color=THEME["text_muted"],
            anchor="w",
        ).pack(fill="x")

        modo_atual = get_mode()
        rotulo = f"{ICONS['moon']}  Modo escuro" if modo_atual == "light" else f"{ICONS['sun']}  Modo claro"
        self.app.theme_toggle_btn = ctk.CTkButton(
            footer,
            text=rotulo,
            command=self.app.theme_manager.toggle,
            height=40,
            corner_radius=10,
            fg_color=THEME["surface"],
            hover_color=THEME["nav_hover"],
            text_color=THEME["text"],
            border_width=1,
            border_color=THEME["border"],
            cursor="hand2",
        )
        self.app.theme_toggle_btn.pack(fill="x")

    def _create_menu(self):
        self.menu_buttons = {}
        for item in MENU_ITEMS:
            self._create_menu_button(item)

    def _create_menu_button(self, item: dict) -> None:
        key = item["key"]
        item_frame = ctk.CTkFrame(self.app.menu_container, fg_color="transparent")
        item_frame.pack(fill="x", padx=6, pady=3)

        indicator = ctk.CTkFrame(item_frame, width=4, height=36, corner_radius=999, fg_color="transparent")
        indicator.pack(side="left", fill="y", padx=(2, 8))

        btn = GhostButton(
            item_frame,
            text=item["label"],
            icon=item["icon"],
            command=lambda k=key: self.show(k),
            width=210,
            height=40,
            corner_radius=10,
            anchor="w",
        )
        btn.pack(side="left", fill="x", expand=True)

        self.menu_buttons[key] = {"frame": item_frame, "indicator": indicator, "btn": btn}
        self._apply_menu_button_style(key, active=(key == self._active_menu_key))

    def _apply_menu_button_style(self, key: str, active: bool = False) -> None:
        data = self.menu_buttons.get(key)
        if not data:
            return

        btn = data["btn"]
        indicator = data["indicator"]

        if active:
            indicator.configure(fg_color=THEME["brand_accent"])
            btn.configure(
                fg_color=THEME["nav_active_bg"],
                hover_color=THEME["nav_active_bg"],
                text_color=THEME["nav_active_text"],
                border_color=THEME["nav_active_text"],
                border_width=1,
            )
        else:
            indicator.configure(fg_color="transparent")
            btn.configure(
                fg_color="transparent",
                hover_color=THEME["nav_hover"],
                text_color=THEME["nav_text"],
                border_width=0,
            )

    # ================= AREA DE CONTEUDO =================
    def create_content_area(self):
        self.app.content = ctk.CTkFrame(self.app.container, fg_color=THEME["bg"])
        self.app.content.grid(row=0, column=1, sticky="nsew")
        self.app.content.grid_columnconfigure(0, weight=1)
        self.app.content.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.app.content, fg_color="transparent", height=PAGE_HEADER_HEIGHT)
        header.grid(row=0, column=0, sticky="ew", padx=SPACING["page_x"], pady=(SPACING["page_y"], 8))
        header.grid_columnconfigure(0, weight=1)

        self.app.header_title = ctk.CTkLabel(
            header,
            text="Painel",
            font=font(24, "bold"),
            text_color=THEME["text"],
            anchor="w",
        )
        self.app.header_title.grid(row=0, column=0, sticky="w")

        self.app.header_subtitle = ctk.CTkLabel(
            header,
            text="Resumo geral do ambiente",
            font=font(12),
            text_color=THEME["text_secondary"],
            anchor="w",
        )
        self.app.header_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self._build_global_search(header)

        self.app.content_body = ctk.CTkFrame(self.app.content, fg_color="transparent")
        self.app.content_body.grid(row=1, column=0, sticky="nsew", padx=SPACING["page_x"], pady=(0, SPACING["page_y"]))

        self._start_notification_polling()

    def _build_global_search(self, header):
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=(12, 0))

        self.app.global_search = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar... (Ctrl+K)",
            width=260,
            height=36,
            corner_radius=10,
            border_width=1,
            border_color=THEME["border"],
            fg_color=THEME["surface"],
            text_color=THEME["text"],
            font=font(12),
        )
        self.app.global_search.pack(side="left", padx=(0, 8))
        self.app.global_search.bind("<KeyRelease>", self._on_global_search)

        self.search_dropdown = ctk.CTkFrame(self.app, fg_color=THEME["surface"], corner_radius=10, border_width=1, border_color=THEME["border"])
        self.search_dropdown.place_forget()
        self.search_dropdown._search_callback = None

    def _on_global_search(self, event):
        query = getattr(self.app, "global_search", None)
        if not query:
            return
        term = query.get().strip()
        if len(term) < 2:
            self._hide_search_dropdown()
            return
        try:
            from ser_pleno.features.analytics.service import ServicoAnalytics
            service = ServicoAnalytics(auth_service=getattr(self.app, "auth_service", None))
            result = service.buscar_global(term)
            items = self._normalize_search_result(result)
        except Exception:
            items = []
        self._show_search_dropdown(items)

    @staticmethod
    def _normalize_search_result(result: dict) -> list[dict]:
        if not isinstance(result, dict):
            return []
        if "results" in result:
            return result.get("results", [])
        items: list[dict] = []
        for student in result.get("students", []) or []:
            items.append({
                "type": "student",
                "label": student.get("name", "Estudante"),
                "subtitle": "Estudante",
                "target": "estudantes",
            })
        for appt in result.get("appointments", []) or []:
            items.append({
                "type": "appointment",
                "label": appt.get("name", "Agendamento"),
                "subtitle": appt.get("detail", "") or appt.get("curso", ""),
                "target": "agenda",
            })
        for screening in result.get("screenings", []) or []:
            items.append({
                "type": "screening",
                "label": screening.get("name", "Triagem"),
                "subtitle": screening.get("status", "pending"),
                "target": "analise",
            })
        return items

    def _show_search_dropdown(self, items):
        for child in getattr(self, "search_dropdown", []).winfo_children() if hasattr(self, "search_dropdown") else []:
            try:
                child.destroy()
            except Exception:
                pass
        if not items:
            self._hide_search_dropdown()
            return
        dropdown = self.search_dropdown
        dropdown.configure(width=340)
        dropdown.place(x=60, y=86)
        dropdown.lift()

        groups: dict[str, list] = {}
        for item in items:
            tipo = item.get("type", "outros")
            label_map = {
                "student": "Estudantes",
                "appointment": "Agendamentos",
                "screening": "Triagens",
                "outros": "Outros",
            }
            group_key = label_map.get(tipo, tipo.title())
            groups.setdefault(group_key, []).append(item)

        type_order = ["Estudantes", "Agendamentos", "Triagens", "Outros"]
        for group_key in type_order:
            group_items = groups.get(group_key)
            if not group_items:
                continue
            header = ctk.CTkLabel(
                dropdown,
                text=group_key,
                font=font(10, "bold"),
                text_color=THEME["text_muted"],
                anchor="w",
            )
            header.pack(fill="x", padx=12, pady=(8, 2))

            for item in group_items[:5]:
                label = item.get("label", "Sem título")
                subtitle = item.get("subtitle", "") or item.get("detail", "") or item.get("status", "")
                target = item.get("target")
                row = ctk.CTkFrame(dropdown, fg_color="transparent")
                row.pack(fill="x", padx=8, pady=2)
                btn = ctk.CTkButton(
                    row,
                    text=f"{label}\n{subtitle}" if subtitle else label,
                    anchor="w",
                    height=44,
                    corner_radius=8,
                    fg_color="transparent",
                    hover_color=THEME["nav_hover"],
                    text_color=THEME["text"],
                    font=font(12),
                )
                btn.pack(fill="x")
                if target:
                    btn.configure(command=lambda k=target: self._navigate_search_result(k))

        close = ctk.CTkButton(dropdown, text="Fechar", width=300, height=28, command=self._hide_search_dropdown)
        close.pack(pady=(6, 8))

    def _hide_search_dropdown(self):
        try:
            self.search_dropdown.place_forget()
        except Exception:
            pass

    def _navigate_search_result(self, key):
        self._hide_search_dropdown()
        if hasattr(self.app, "global_search"):
            self.app.global_search.delete(0, "end")
        self.show(key)

    # ================= NAVEGACAO =================
    def update_menu(self, active_key: str) -> None:
        self._active_menu_key = active_key
        for key in self.menu_buttons:
            self._apply_menu_button_style(key, key == active_key)

    def get_active_screen(self) -> str:
        """Retorna a chave da tela atualmente ativa, ou 'dashboard' como fallback."""
        return self._active_menu_key or "dashboard"

    def update_header(self, title: str, subtitle: str) -> None:
        if hasattr(self.app, "header_title") and self.app.header_title.winfo_exists():
            self.app.header_title.configure(text=title)
        if hasattr(self.app, "header_subtitle") and self.app.header_subtitle.winfo_exists():
            self.app.header_subtitle.configure(text=subtitle)

    def show(self, key: str) -> None:
        item = _MENU_BY_KEY.get(key)
        if not item:
            return
        t0 = time.perf_counter()
        self.update_menu(key)
        title, subtitle = item["header"]
        self.update_header(title, subtitle)
        parent = getattr(self.app, "content_body", None)
        if parent is None or not hasattr(parent, "winfo_exists"):
            self.create_content_area()
            parent = self.app.content_body

        # Esconde view atual antes de trocar
        if self._current_view is not None and self._current_view.winfo_exists():
            self._current_view.pack_forget()

        # Reutiliza view cacheada se disponível
        frame = self._view_cache.get(key)
        if frame is not None and frame.winfo_exists():
            self._view_cache.move_to_end(key)
            reloader = getattr(frame, "reload", None)
            if callable(reloader):
                try:
                    reloader()
                except Exception:
                    pass
            frame.pack(fill="both", expand=True)
            self._current_view = frame
        else:
            frame = self.view_factory.create(key, parent)
            if frame is not None:
                if key in self._view_cache:
                    old = self._view_cache.pop(key)
                    if old.winfo_exists():
                        old.destroy()
                self._view_cache[key] = frame
                self._current_view = frame
                while len(self._view_cache) > VIEW_CACHE_MAXSIZE:
                    _, oldest = self._view_cache.popitem(last=False)
                    if oldest.winfo_exists():
                        oldest.destroy()
                frame.pack(fill="both", expand=True)

        try:
            logger.info("PERF nav_switch_%s_ms=%.1f", key, (time.perf_counter() - t0) * 1000)
        except Exception:
            pass

    def invalidate_view(self, key: str) -> None:
        """Remove uma view do cache (usado após mutações de dados)."""
        frame = self._view_cache.pop(key, None)
        if frame is not None and frame.winfo_exists():
            frame.destroy()
        if self._active_menu_key == key:
            self._current_view = None

    def refresh(self, key: str) -> None:
        """Força recriação de uma view na próxima navegação."""
        self.invalidate_view(key)
        if self._active_menu_key == key:
            self.show(key)

    def precreate(self, key: str) -> None:
        """Pre-cria uma view e armazena no cache sem exibi-la."""
        if key in self._view_cache:
            return
        parent = getattr(self.app, "content_body", None)
        if parent is None or not hasattr(parent, "winfo_exists"):
            return
        frame = self.view_factory.create(key, parent)
        if frame is not None:
            self._view_cache[key] = frame

    def clear_screen(self):
        for widget in self.app.container.winfo_children():
            widget.destroy()
        self._view_cache.clear()
        self._current_view = None

    def _get_recipient_id(self) -> int | None:
        user_id = getattr(self.app, "usuario_logado_id", None)
        if user_id:
            return user_id
        auth = getattr(self.app, "auth_service", None)
        if auth and hasattr(auth, "user") and isinstance(auth.user, dict):
            return auth.user.get("id")
        return None

    def _refresh_notification_count(self) -> None:
        recipient_id = self._get_recipient_id()
        if not recipient_id:
            return

        def _fetch():
            from ser_pleno.features.notificacoes.service import ServicoNotificacoes
            service = ServicoNotificacoes(auth_service=getattr(self.app, "auth_service", None))
            return service.contar_nao_lidas(recipient_id=recipient_id)

        def _on_success(res):
            if not isinstance(res, dict):
                return
            count = res.get("data", 0) if res.get("success") else 0
            try:
                notifier = getattr(self, "_desktop_notifier", None)
                if notifier is not None:
                    notifier.update_unread_badge(count)
                    if count > getattr(notifier, "_last_count", 0):
                        notifier.notify("SerPleno", f"Você tem {count} notificação(ões) não lida(s).")
            except Exception as exc:
                logger.debug("Falha ao atualizar notificador desktop: %s", exc)

        def _on_error(exc):
            pass

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self.app)

    def _start_notification_polling(self) -> None:
        if self._notification_poll_after_id is not None:
            try:
                self.after_cancel(self._notification_poll_after_id)
            except Exception:
                pass
        try:
            self._notification_poll_after_id = self.after(30000, self._poll_notifications)
        except Exception:
            pass

    def _poll_notifications(self) -> None:
        self._refresh_notification_count()
        self._start_notification_polling()


def get_mode():
    """Importado de ser_pleno.ui.theme para uso em _criar_rodape_sidebar."""
    from ser_pleno.ui.theme import get_mode as _get_mode
    return _get_mode()

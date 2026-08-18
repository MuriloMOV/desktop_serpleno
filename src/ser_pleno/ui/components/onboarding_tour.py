# -*- coding: utf-8 -*-
"""Onboarding tour guiado — overlay, tooltips e persistência de estado."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from typing import Callable, Optional

import customtkinter as ctk

from ser_pleno.infrastructure.local.local_cache import get_local_cache
from ser_pleno.ui.navigation import MENU_ITEMS
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font

logger = logging.getLogger(__name__)

ONBOARDING_VERSION = "1.0"
_ONBOARDING_KEY = "onboarding_tour"


@dataclass
class OnboardingTourStep:
    key: str
    title: str
    description: str
    icon: str = ""
    highlight_pad: int = 8


class OnboardingTourStorage:
    """Lê/grava estado do onboarding em user_preferences (local cache)."""

    def __init__(self, user_id: int):
        self._user_id = user_id
        self._lock = threading.Lock()
        self._cache = get_local_cache()

    def _pref_row(self) -> dict:
        rows = self._cache.list_user_preferences()
        for r in rows:
            if r.get("user_id") == self._user_id:
                return r
        return {}

    def get_state(self) -> dict:
        with self._lock:
            row = self._pref_row()
            raw = row.get("onboarding_tour")
            if raw:
                try:
                    return json.loads(raw)
                except Exception:
                    pass
        return {"completed": False, "skipped": False, "last_step": 0, "version": ONBOARDING_VERSION}

    def save_state(self, state: dict) -> None:
        with self._lock:
            existing = self._pref_row()
            prefs = {
                "user_id": self._user_id,
                "theme": existing.get("theme"),
                "notifications": existing.get("notifications"),
                "font_size": existing.get("font_size"),
                "onboarding_tour": json.dumps(state),
            }
            try:
                conn = self._cache._get_connection()
                cols = list(prefs.keys())
                placeholders = ", ".join(["?"] * len(cols))
                columns = ", ".join(cols)
                update_set = ", ".join(
                    f"{c}=excluded.{c}" for c in cols if c != "user_id"
                )
                query = (
                    f"INSERT INTO user_preferences ({columns}) VALUES ({placeholders}) "
                    f"ON CONFLICT(user_id) DO UPDATE SET {update_set}"
                )
                values = [
                    json.dumps(v) if isinstance(v, (dict, list)) else v
                    for v in prefs.values()
                ]
                conn.execute(query, values)
                conn.commit()
            except Exception as exc:
                logger.debug("Falha ao salvar estado do onboarding: %s", exc)

    def mark_completed(self) -> None:
        state = self.get_state()
        state["completed"] = True
        state["skipped"] = False
        state["last_step"] = len(MENU_ITEMS)
        self.save_state(state)

    def mark_skipped(self) -> None:
        state = self.get_state()
        state["skipped"] = True
        state["completed"] = False
        self.save_state(state)

    def reset(self) -> None:
        self.save_state({"completed": False, "skipped": False, "last_step": 0, "version": ONBOARDING_VERSION})


class OnboardingTourOverlay(ctk.CTkToplevel):
    """Overlay em tela cheia que escurece o app e destaca o widget alvo."""

    def __init__(self, master, on_close: Callable, on_next: Callable, on_prev: Callable):
        super().__init__(master)
        self._on_close = on_close
        self._on_next = on_next
        self._on_prev = on_prev
        self._highlight_frame: Optional[ctk.CTkFrame] = None
        self._alive = True
        self._anim_job: Optional[str] = None

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.85)
        except Exception:
            pass
        self.configure(fg_color=THEME["overlay"])
        self._bind_escape()
        self._bind_nav_keys()
        self.after(60, self._fit_screen)

    def _bind_escape(self):
        self.bind("<Escape>", lambda _: self._safe_close())

    def _bind_nav_keys(self):
        self.bind("<Right>", lambda _: self._on_next())
        self.bind("<Left>", lambda _: self._on_prev())
        self.bind("<Return>", lambda _: self._on_next())

    def _fit_screen(self):
        if not self._alive:
            return
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{sw}x{sh}+0+0")
        except Exception:
            pass

    def highlight_widget(self, widget):
        if not self._alive:
            return
        self._clear_highlight()
        try:
            if widget is None or not widget.winfo_exists():
                return
            widget.update_idletasks()
            wx = widget.winfo_rootx()
            wy = widget.winfo_rooty()
            ww = widget.winfo_width()
            wh = widget.winfo_height()
            pad = 10
            x1 = wx - pad
            y1 = wy - pad
            x2 = wx + ww + pad
            y2 = wy + wh + pad

            self._highlight_frame = ctk.CTkFrame(
                self,
                width=x2 - x1,
                height=y2 - y1,
                fg_color="transparent",
                border_width=3,
                border_color=THEME["brand_accent"],
                corner_radius=RADIUS["md"],
            )
            self._highlight_frame.place(x=x1, y=y1)
            self._highlight_frame.lift()
        except Exception as exc:
            logger.debug("highlight_widget falhou: %s", exc)

    def _clear_highlight(self):
        if self._highlight_frame is not None:
            try:
                self._highlight_frame.destroy()
            except Exception:
                pass
            self._highlight_frame = None

    def _safe_close(self):
        if not self._alive:
            return
        self._alive = False
        try:
            self._on_close()
        except Exception:
            pass
        self._safe_destroy()

    def _safe_destroy(self):
        try:
            self._clear_highlight()
            if self._anim_job:
                self.after_cancel(self._anim_job)
                self._anim_job = None
            self.destroy()
        except Exception:
            pass


class OnboardingTourTooltip(ctk.CTkToplevel):
    """Tooltip flutuante com título, descrição e controles de navegação."""

    def __init__(self, master, step: OnboardingTourStep, step_index: int,
                 total_steps: int, on_next: Callable, on_prev: Callable,
                 on_skip: Callable):
        super().__init__(master)
        self._step = step
        self._step_index = step_index
        self._total_steps = total_steps
        self._on_next = on_next
        self._on_prev = on_prev
        self._on_skip = on_skip
        self._alive = True

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=THEME["surface"], border_width=1, border_color=THEME["border"])
        self._build()
        self._bind_keys()

    def _bind_keys(self):
        self.bind("<Escape>", lambda _: self._on_skip())
        self.bind("<Right>", lambda _: self._on_next())
        self.bind("<Left>", lambda _: self._on_prev())
        self.bind("<Return>", lambda _: self._on_next())

    def _build(self):
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["card_pad"])

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        if self._step.icon:
            ctk.CTkLabel(header, text=self._step.icon,
                         font=themed_font("h3")).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            header, text=self._step.title,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        step_lbl = ctk.CTkLabel(
            header, text=f"{self._step_index + 1}/{self._total_steps}",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
        )
        step_lbl.pack(side="right")

        ctk.CTkLabel(
            outer, text=self._step.description,
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            wraplength=380, justify="left",
        ).pack(anchor="w", pady=(0, 14))

        footer = ctk.CTkFrame(outer, fg_color="transparent")
        footer.pack(fill="x")

        skip_btn = ctk.CTkButton(
            footer, text="Pular tour",
            command=self._on_skip,
            fg_color="transparent", hover_color=THEME["bg_alt"],
            text_color=THEME["text_muted"],
            border_width=0, font=themed_font("caption"),
            cursor="hand2",
        )
        skip_btn.pack(side="left")

        prev_btn = ctk.CTkButton(
            footer, text="Anterior",
            command=self._on_prev,
            fg_color=THEME["bg_alt"], hover_color=THEME["border"],
            text_color=THEME["text"],
            border_width=1, border_color=THEME["border"],
            font=themed_font("body", "bold"), width=90, height=32,
            corner_radius=RADIUS["button"], cursor="hand2",
        )
        prev_btn.pack(side="right", padx=(8, 0))

        is_last = self._step_index >= self._total_steps - 1
        next_text = "Concluir" if is_last else "Proximo"
        next_btn = ctk.CTkButton(
            footer, text=next_text,
            command=self._on_next,
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
            text_color="white",
            font=themed_font("body", "bold"), width=110, height=32,
            corner_radius=RADIUS["button"], cursor="hand2",
        )
        next_btn.pack(side="right")

        progress_bg = ctk.CTkFrame(outer, fg_color=THEME["bg_alt"], corner_radius=RADIUS["xs"], height=4)
        progress_bg.pack(fill="x", pady=(12, 0))
        progress_bg.pack_propagate(False)
        ratio = (self._step_index + 1) / self._total_steps
        fill = ctk.CTkFrame(progress_bg, fg_color=THEME["brand_accent"], corner_radius=RADIUS["xs"], height=4)
        fill.place(x=0, y=0, relwidth=ratio)
        fill.lift()

    def move_toward(self, widget):
        if not self._alive or not self.winfo_exists():
            return
        try:
            if widget is None or not widget.winfo_exists():
                self._place_default()
                return
            widget.update_idletasks()
            wx = widget.winfo_rootx()
            wy = widget.winfo_rooty()
            ww = widget.winfo_width()
            wh = widget.winfo_height()
            tw = self.winfo_reqwidth()
            th = self.winfo_reqheight()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()

            if wx + ww / 2 > sw / 2:
                tx = wx - tw - 16
            else:
                tx = wx + ww + 16

            ty = wy + wh / 2 - th / 2
            ty = max(8, min(ty, sh - th - 8))
            tx = max(8, min(tx, sw - tw - 8))

            self.geometry(f"{tw}x{th}+{int(tx)}+{int(ty)}")
            self.lift()
        except Exception:
            self._place_default()

    def _place_default(self):
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            tw = 420
            th = 200
            self.geometry(f"{tw}x{th}+{sw // 2 - tw // 2}+{sh // 2 - th // 2}")
        except Exception:
            pass


class OnboardingTourController:
    """Controla o fluxo do onboarding tour."""

    def __init__(self, app, navigation):
        self.app = app
        self.navigation = navigation
        self._storage = OnboardingTourStorage(user_id=getattr(app, "usuario_logado_id", 0))
        self._steps: list[OnboardingTourStep] = []
        self._current_index: int = 0
        self._overlay: Optional[OnboardingTourOverlay] = None
        self._tooltip: Optional[OnboardingTourTooltip] = None
        self._active: bool = False
        self._move_job: Optional[str] = None
        self._build_steps()

    def _build_steps(self):
        menu_map = {item["key"]: item for item in MENU_ITEMS}
        tour_keys = [
            "dashboard", "estudantes", "agenda", "bem_estar",
            "wellness_challenges", "analise", "relatorios", "comunicacao",
            "orientacoes", "avisos", "configuracoes",
        ]
        descriptions = {
            "dashboard": "Visao consolidada com KPIs, agenda e alertas em um so lugar.",
            "estudantes": "Cadastro, acompanhamento e historico de cada estudante.",
            "agenda": "Agendamentos, compromissos e disponibilidade de horarios.",
            "bem_estar": "Monitoramento emocional e dimensoes de bem-estar.",
            "wellness_challenges": "Desafios de bem-estar para engajar os estudantes.",
            "analise": "Triagens, classificacoes e encaminhamentos.",
            "relatorios": "Indicadores consolidados e exportacao de relatorios.",
            "comunicacao": "Mensagens internas, chats e suporte.",
            "orientacoes": "Fluxo de orientacoes e encaminhamentos pedagogicos.",
            "avisos": "Comunicados institucionais e quadro de avisos.",
            "configuracoes": "Preferencias, tema e personalizacao do sistema.",
        }
        for key in tour_keys:
            item = menu_map.get(key)
            if not item:
                continue
            icon = item.get("icon", "")
            self._steps.append(
                OnboardingTourStep(
                    key=key,
                    title=item["label"],
                    description=descriptions.get(key, item["header"][1]),
                    icon=icon,
                )
            )

    def is_completed(self) -> bool:
        state = self._storage.get_state()
        return bool(state.get("completed"))

    def was_skipped(self) -> bool:
        state = self._storage.get_state()
        return bool(state.get("skipped"))

    def should_show(self) -> bool:
        return not self.is_completed() and not self.was_skipped()

    def start(self) -> None:
        if self._active:
            return
        self._active = True
        self._current_index = 0
        self._create_overlay_and_tooltip()
        self._show_step(0)
        self._start_move_listener()

    def restart(self) -> None:
        self.stop()
        self._storage.reset()
        self._active = True
        self._current_index = 0
        self._create_overlay_and_tooltip()
        self._show_step(0)
        self._start_move_listener()

    def stop(self) -> None:
        self._active = False
        self._stop_move_listener()
        self._destroy_tooltip()
        self._destroy_overlay()

    def skip(self) -> None:
        self._storage.mark_skipped()
        self.stop()

    def complete(self) -> None:
        self._storage.mark_completed()
        self.stop()

    def next(self) -> None:
        if self._current_index < len(self._steps) - 1:
            self._current_index += 1
            self._show_step(self._current_index)
        else:
            self.complete()

    def prev(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._show_step(self._current_index)

    def _create_overlay_and_tooltip(self):
        self._destroy_overlay()
        self._destroy_tooltip()
        self._overlay = OnboardingTourOverlay(
            self.app,
            on_close=self._on_overlay_close,
            on_next=self.next,
            on_prev=self.prev,
        )
        self._tooltip = OnboardingTourTooltip(
            self.app,
            step=self._steps[self._current_index],
            step_index=self._current_index,
            total_steps=len(self._steps),
            on_next=self.next,
            on_prev=self.prev,
            on_skip=self.skip,
        )

    def _destroy_overlay(self):
        if self._overlay is not None:
            try:
                self._overlay._safe_destroy()
            except Exception:
                pass
            self._overlay = None

    def _destroy_tooltip(self):
        if self._tooltip is not None:
            try:
                if self._tooltip.winfo_exists():
                    self._tooltip.destroy()
            except Exception:
                pass
            self._tooltip = None

    def _on_overlay_close(self):
        self._active = False

    def _start_move_listener(self):
        self._stop_move_listener()
        self._move_job = self.app.after(100, self._tick_move)

    def _stop_move_listener(self):
        if self._move_job:
            try:
                self.app.after_cancel(self._move_job)
            except Exception:
                pass
            self._move_job = None

    def _tick_move(self):
        if not self._active:
            self._move_job = None
            return
        try:
            self._reposition()
        except Exception:
            pass
        self._move_job = self.app.after(100, self._tick_move)

    def _reposition(self):
        if not self._active or self._tooltip is None or not self._tooltip.winfo_exists():
            return
        step = self._steps[self._current_index]
        target = self._get_menu_button(step.key)
        if target is None:
            target = self._find_target_widget(step.key)
        if target and self._overlay is not None and self._overlay.winfo_exists():
            self._overlay.highlight_widget(target)
        self._tooltip.move_toward(target)

    def _show_step(self, index: int):
        if not self._active or index >= len(self._steps):
            return

        step = self._steps[index]

        self.navigation.show(step.key)
        self.app.update_idletasks()

        target = self._get_menu_button(step.key)
        if target is None:
            target = self._find_target_widget(step.key)
        if target is None:
            current_view = getattr(self.navigation, "_current_view", None)
            target = current_view if current_view and current_view.winfo_exists() else None

        self.app.after_idle(lambda: self._position_tooltip(step, target))

    def _get_menu_button(self, key: str):
        try:
            data = getattr(self.navigation, "menu_buttons", {}).get(key)
            if not data:
                return None
            return data.get("btn")
        except Exception:
            return None

    def _find_target_widget(self, key: str):
        try:
            current_view = getattr(self.navigation, "_current_view", None)
            content_body = getattr(self.app, "content_body", None)
            search_root = current_view if (current_view and current_view.winfo_exists()) else content_body
            if search_root is None or not search_root.winfo_exists():
                return None
            return self._find_in_tree(search_root, key)
        except Exception:
            return None

    @staticmethod
    def _find_in_tree(widget, target_key: str):
        candidates = []
        try:
            if not widget.winfo_exists():
                return None
        except Exception:
            return None

        def _walk(w):
            try:
                if not w.winfo_exists():
                    return
            except Exception:
                return
            txt = ""
            try:
                txt = str(w.cget("text")) if hasattr(w, "cget") else ""
            except Exception:
                pass
            size = (w.winfo_width() or 0) * (w.winfo_height() or 0)
            if target_key in txt.lower():
                if size > 100:
                    candidates.append((size, w))
            for child in w.winfo_children():
                _walk(child)

        _walk(widget)
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        return widget

    def _position_tooltip(self, step, target_widget):
        if self._tooltip is None or not self._tooltip.winfo_exists():
            return
        if self._overlay is not None and self._overlay.winfo_exists():
            self._overlay.highlight_widget(target_widget)
        self._tooltip._step = step
        self._tooltip._step_index = self._current_index
        self._tooltip._total_steps = len(self._steps)
        try:
            for child in list(self._tooltip.winfo_children()):
                child.destroy()
            self._tooltip._build()
        except Exception:
            pass
        self.app.after(80, lambda: self._tooltip.move_toward(target_widget) if self._tooltip else None)

# -*- coding: utf-8 -*-
"""View de Wellness Challenges."""

from __future__ import annotations

import logging
import customtkinter as ctk
from typing import Optional

from ser_pleno.features.wellness_challenges.service import ServicoWellnessChallenges
from ser_pleno.features.estudantes.service import ServicoEstudante
from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.components.ui_components import (
    Card, EmptyState, PrimaryButton, GhostButton, Divider, BaseModal, Toast, Badge, SkeletonLoader,
)
from ser_pleno.ui.views.base import _ErrorModal
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

_CHALLENGE_CATEGORIES = [
    ("breathing", "Respiração"),
    ("gratitude", "Gratidão"),
    ("activity", "Atividade Física"),
    ("hydration", "Hidratação"),
    ("organization", "Organização"),
    ("sleep", "Sono"),
    ("social", "Social"),
    ("emotional", "Emocional"),
    ("academic", "Acadêmico"),
    ("other", "Outro"),
]

_DIFFICULTY_LABELS = {
    "easy": "Fácil",
    "medium": "Médio",
    "hard": "Difícil",
}

_DIFFICULTY_COLORS = {
    "easy": THEME["success"],
    "medium": THEME["warning"],
    "hard": THEME["danger"],
}

_STATUS_COLORS = {
    "assigned": THEME["warning"],
    "completed": THEME["success"],
    "pending": THEME["info"],
}

logger = logging.getLogger("apps.desktop")


class _ChallengeFormModal(BaseModal):
    def __init__(self, parent, on_salvar, challenge: Optional[dict] = None):
        self.on_salvar = on_salvar
        self.challenge = challenge
        super().__init__(parent, title="Novo Desafio" if not challenge else "Editar Desafio", width=520, height=480)
        self.configure(fg_color=THEME["surface"])
        self._build()

    def _build(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=f"{ICONS['heart']}  {'Novo Desafio' if not self.challenge else 'Editar Desafio'}",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        form = ctk.CTkFrame(wrapper, fg_color="transparent")
        form.pack(fill="both", expand=True)

        ctk.CTkLabel(form, text="Título", font=font(size=12), text_color=THEME["text"]).pack(anchor="w")
        self.f_title = ctk.CTkEntry(form, fg_color=THEME["input_bg"], border_width=1, border_color=THEME["input_border"], font=font(size=12))
        self.f_title.pack(fill="x", pady=(0, spacing("md")))

        ctk.CTkLabel(form, text="Descrição", font=font(size=12), text_color=THEME["text"]).pack(anchor="w")
        self.f_desc = ctk.CTkTextbox(form, height=80, fg_color=THEME["input_bg"], border_width=1, border_color=THEME["input_border"], font=font(size=12))
        self.f_desc.pack(fill="x", pady=(0, spacing("md")))

        row_cat = ctk.CTkFrame(form, fg_color="transparent")
        row_cat.pack(fill="x", pady=(0, spacing("md")))
        row_cat.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(row_cat, text="Categoria", font=font(size=12), text_color=THEME["text"]).grid(row=0, column=0, sticky="w")
        self.f_cat = ctk.CTkOptionMenu(
            row_cat,
            values=[c[1] for c in _CHALLENGE_CATEGORIES],
            font=font(size=12),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
        )
        self.f_cat.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(row_cat, text="Dificuldade", font=font(size=12), text_color=THEME["text"]).grid(row=0, column=1, sticky="w")
        self.f_diff = ctk.CTkOptionMenu(
            row_cat,
            values=list(_DIFFICULTY_LABELS.values()),
            font=font(size=12),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
        )
        self.f_diff.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        ctk.CTkLabel(form, text="Pontos", font=font(size=12), text_color=THEME["text"]).pack(anchor="w")
        self.f_points = ctk.CTkEntry(form, fg_color=THEME["input_bg"], border_width=1, border_color=THEME["input_border"], font=font(size=12))
        self.f_points.pack(fill="x", pady=(0, spacing("md")))

        btns = ctk.CTkFrame(wrapper, fg_color="transparent")
        btns.pack(fill="x", pady=(spacing("md"), 0))

        PrimaryButton(btns, text="Salvar", command=self._salvar, width=120).pack(side="right", padx=(spacing("sm"), 0))
        GhostButton(btns, text="Cancelar", command=self.destroy, width=120).pack(side="right")

        if self.challenge:
            self.f_title.insert(0, self.challenge.get("title", ""))
            self.f_desc.insert("1.0", self.challenge.get("description", ""))
            cat_val = self.challenge.get("category", "other")
            cat_label = dict(_CHALLENGE_CATEGORIES).get(cat_val, "Outro")
            self.f_cat.set(cat_label)
            diff_val = self.challenge.get("difficulty", "medium")
            self.f_diff.set(_DIFFICULTY_LABELS.get(diff_val, "Médio"))
            self.f_points.insert(0, str(self.challenge.get("points", 0)))

    def _salvar(self):
        title = self.f_title.get().strip()
        if not title:
            self._show_error("Título do desafio é obrigatório.")
            return
        try:
            points = int(self.f_points.get() or 0)
        except Exception:
            points = 0
        cat_label = self.f_cat.get()
        cat_map = {v: k for k, v in _CHALLENGE_CATEGORIES}
        category = cat_map.get(cat_label, "other")
        diff_label = self.f_diff.get()
        diff_map = {v: k for k, v in _DIFFICULTY_LABELS.items()}
        difficulty = diff_map.get(diff_label, "medium")
        dados = {
            "title": title,
            "description": self.f_desc.get("1.0", "end").strip(),
            "category": category,
            "difficulty": difficulty,
            "points": points,
        }
        self.on_salvar(dados, self.challenge.get("id") if self.challenge else None)
        self.destroy()


class _AssignModal(BaseModal):
    def __init__(self, parent, on_assign, challenge_id: int, students: list):
        self.on_assign = on_assign
        self.challenge_id = challenge_id
        self.students = students
        super().__init__(parent, title="Atribuir Desafio", width=420, height=320)
        self.configure(fg_color=THEME["surface"])
        self._build()

    def _build(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            wrapper,
            text=f"{ICONS['user']}  Atribuir a Estudante",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(wrapper, text="Estudante", font=font(size=12), text_color=THEME["text"]).pack(anchor="w")
        values = [f"{s.get('name', '')} ({s.get('id')})" for s in self.students]
        self.f_student = ctk.CTkOptionMenu(
            wrapper,
            values=values if values else ["Nenhum estudante"],
            font=font(size=12),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
        )
        self.f_student.pack(fill="x", pady=(0, spacing("md")))

        btns = ctk.CTkFrame(wrapper, fg_color="transparent")
        btns.pack(fill="x", pady=(spacing("md"), 0))

        PrimaryButton(btns, text="Atribuir", command=self._salvar, width=120).pack(side="right", padx=(spacing("sm"), 0))
        GhostButton(btns, text="Cancelar", command=self.destroy, width=120).pack(side="right")

    def _salvar(self):
        sel = self.f_student.get()
        student_id = None
        for s in self.students:
            if f"{s.get('name', '')} ({s.get('id')})" == sel:
                student_id = s.get("id")
                break
        if student_id is None:
            self._show_error("Selecione um estudante.")
            return
        self.on_assign(self.challenge_id, student_id)
        self.destroy()


class WellnessChallengesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        import time as _time
        self._t0 = _time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico = ServicoWellnessChallenges(auth_service=getattr(controller, "auth_service", None))
        self.servico_estudantes = ServicoEstudante(auth_service=getattr(controller, "auth_service", None))
        self._challenges: list[dict] = []
        self._students: list[dict] = []
        self._filtro_cat = ""
        self._filtro_diff = ""
        self._dashboard_cache: dict = {}

        self._build_header()
        self._build_dashboard()
        self._build_filtros()
        self._build_lista()
        self.carregar_dados_async()
        log_view_init_ms("wellness_challenges", self._t0, widget_ref=self)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=spacing("xl"), pady=(spacing("lg"), spacing("sm")))

        ctk.CTkLabel(
            header, text=f"{ICONS['heart']}  Wellness Challenges",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        PrimaryButton(
            header, text="Novo Desafio", command=self._abrir_novo,
            height=36, width=140,
        ).pack(side="right")

    def _build_dashboard(self):
        card = Card(self, padding=(SPACING["card_pad"], SPACING["label_gap"]))
        card.pack(fill="x", padx=spacing("xl"), pady=(0, spacing("md")))

        hdr = ctk.CTkFrame(card.body, fg_color="transparent")
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="Dashboard",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        stats = ctk.CTkFrame(card.body, fg_color="transparent")
        stats.pack(fill="x", pady=(SPACING["label_gap"], 0))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)

        kpis = [
            ("Total Atribuições", "_lbl_dash_total", "0", THEME["primary"], THEME["primary_soft"]),
            ("Concluídas", "_lbl_dash_completed", "0", THEME["success"], THEME["success_soft"]),
            ("Pendentes", "_lbl_dash_pending", "0", THEME["warning"], THEME["warning_soft"]),
            ("Taxa Conclusão", "_lbl_dash_rate", "0%", THEME["info"], THEME["info_soft"]),
        ]
        for i, (title, attr, initial, accent, soft) in enumerate(kpis):
            col = ctk.CTkFrame(stats, fg_color=THEME["surface"], corner_radius=RADIUS["button"], border_width=1, border_color=THEME["border"])
            col.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2)
            inner = ctk.CTkFrame(col, fg_color="transparent")
            inner.pack(fill="x", padx=spacing("md"), pady=spacing("sm"))
            ctk.CTkLabel(inner, text=title, font=themed_font("caption"), text_color=THEME["text_muted"]).pack(anchor="w")
            lbl = ctk.CTkLabel(inner, text=initial, font=themed_font("body", "bold"), text_color=accent)
            lbl.pack(anchor="w")
            setattr(self, attr, lbl)

    def _build_filtros(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=spacing("xl"), pady=(0, spacing("sm")))

        ctk.CTkLabel(frame, text="Categoria:", font=font(size=12), text_color=THEME["text_muted"]).pack(side="left", padx=(0, spacing("xs")))
        self.f_cat = ctk.CTkOptionMenu(
            frame,
            values=["Todas"] + [c[1] for c in _CHALLENGE_CATEGORIES],
            font=font(size=12),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            width=160,
            height=34,
            corner_radius=RADIUS["input"],
            command=self._aplicar_filtro_cat,
        )
        self.f_cat.pack(side="left", padx=(0, spacing("md")))

        ctk.CTkLabel(frame, text="Dificuldade:", font=font(size=12), text_color=THEME["text_muted"]).pack(side="left", padx=(0, spacing("xs")))
        self.f_diff = ctk.CTkOptionMenu(
            frame,
            values=["Todas", "Fácil", "Médio", "Difícil"],
            font=font(size=12),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            dropdown_fg_color=THEME["surface"],
            dropdown_text_color=THEME["text"],
            width=140,
            height=34,
            corner_radius=RADIUS["input"],
            command=self._aplicar_filtro_diff,
        )
        self.f_diff.pack(side="left")

    def _build_lista(self):
        card = Card(self, padding=(SPACING["card_pad"], SPACING["label_gap"]))
        card.pack(fill="both", expand=True, padx=spacing("xl"), pady=(0, spacing("xl")))

        hdr = ctk.CTkFrame(card.body, fg_color="transparent")
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr, text="Desafios",
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        Divider(card.body).pack(fill="x", pady=(SPACING["label_gap"], 0))

        self.lista = ctk.CTkScrollableFrame(
            card.body, fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.lista.pack(fill="both", expand=True, pady=(SPACING["label_gap"], 0))

    def _aplicar_filtro_cat(self, valor):
        self._filtro_cat = "" if valor == "Todas" else dict(_CHALLENGE_CATEGORIES).get(valor, "")
        self.carregar_dados_async()

    def _aplicar_filtro_diff(self, valor):
        mapa = {"Todas": "", "Fácil": "easy", "Médio": "medium", "Difícil": "hard"}
        self._filtro_diff = mapa.get(valor, "")
        self.carregar_dados_async()

    def _limpar_lista(self):
        try:
            if self.lista.winfo_exists():
                for w in self.lista.winfo_children():
                    w.destroy()
        except Exception:
            pass

    def _mostrar_skeletons(self):
        for _ in range(3):
            SkeletonLoader(self.lista, width=760, height=64, variant="card").pack(
                fill="x", pady=(0, 12)
            )

    def carregar_dados_async(self):
        self._limpar_lista()
        self._mostrar_skeletons()

        def _fetch():
            return (
                self.servico.listar_desafios(apenas_ativos=True),
                self.servico.obter_dashboard(),
                self.servico_estudantes.listar_estudantes(),
            )

        def _on_success(result):
            if not self.winfo_exists():
                return
            challenges_res, dash_res, students_res = result
            challenges = self._parse(challenges_res)
            self._challenges = challenges

            students = []
            if isinstance(students_res, dict):
                data = students_res.get("data") or {}
                if isinstance(data, list):
                    students = data
                elif isinstance(data, dict):
                    students = data.get("students") or data.get("results") or []
            self._students = students

            dash = {}
            if isinstance(dash_res, dict):
                data = dash_res.get("data") or {}
                if isinstance(data, dict):
                    dash = data
            self._dashboard_cache = dash
            self._atualizar_dashboard(dash)

            self._limpar_lista()
            filtered = challenges
            if self._filtro_cat:
                filtered = [c for c in filtered if c.get("category") == self._filtro_cat]
            if self._filtro_diff:
                filtered = [c for c in filtered if c.get("difficulty") == self._filtro_diff]

            if not filtered:
                EmptyState(
                    self.lista,
                    icon=ICONS["heart"],
                    title="Nenhum desafio encontrado",
                    subtitle="Crie um novo desafio para comecar",
                ).pack(pady=30)
                return

            batch = WidgetBatchBuilder(parent=self, batch_size=20)
            for c in filtered:
                if not isinstance(c, dict):
                    continue
                batch.add(lambda c=c: self._criar_row(c))
            batch.execute()

        def _on_error(exc):
            if not self.winfo_exists():
                return
            self._limpar_lista()
            EmptyState(
                self.lista,
                icon=ICONS["bolt"],
                title="Erro ao carregar desafios",
                subtitle=str(exc),
            ).pack(pady=20)

        AsyncRunner.run(
            task=_fetch,
            on_success=_on_success,
            on_error=_on_error,
            widget_ref=self,
        )

    def _parse(self, res) -> list[dict]:
        if isinstance(res, dict):
            if res.get("success") is False:
                return []
            data = res.get("data")
            if isinstance(data, list):
                return data
            if res.get("id"):
                return [res]
        if isinstance(res, list):
            return res
        return []

    def _atualizar_dashboard(self, dash: dict):
        total = dash.get("total_assignments", 0)
        completed = dash.get("completed", 0)
        pending = dash.get("pending", total - completed)
        rate = dash.get("completion_rate", 0)
        if hasattr(self, "_lbl_dash_total"):
            self._lbl_dash_total.configure(text=str(total))
        if hasattr(self, "_lbl_dash_completed"):
            self._lbl_dash_completed.configure(text=str(completed))
        if hasattr(self, "_lbl_dash_pending"):
            self._lbl_dash_pending.configure(text=str(pending))
        if hasattr(self, "_lbl_dash_rate"):
            self._lbl_dash_rate.configure(text=f"{rate}%")

    def _criar_row(self, challenge: dict):
        row = ctk.CTkFrame(
            self.lista,
            fg_color=THEME["row_bg"],
            corner_radius=RADIUS["button"],
        )
        row.pack(fill="x", pady=SPACING["grid_gap"] // 4)
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(2, weight=1)
        row.grid_columnconfigure(3, weight=1)

        row.bind("<Enter>", lambda e, r=row: r.configure(fg_color=THEME["row_hover"]))
        row.bind("<Leave>", lambda e, r=row: r.configure(fg_color=THEME["row_bg"]))

        title = challenge.get("title", "Desafio")
        category = challenge.get("category", "other")
        cat_label = dict(_CHALLENGE_CATEGORIES).get(category, category)
        difficulty = challenge.get("difficulty", "medium")
        diff_label = _DIFFICULTY_LABELS.get(difficulty, difficulty)
        points = challenge.get("points", 0)
        is_active = challenge.get("is_active", True)
        challenge_id = challenge.get("id")

        ctk.CTkLabel(
            row, text=title,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).grid(row=0, column=0, sticky="w", padx=spacing("md"), pady=spacing("item_gap"))

        ctk.CTkLabel(
            row, text=cat_label,
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=1, sticky="w", padx=spacing("md"), pady=spacing("item_gap"))

        diff_color = _DIFFICULTY_COLORS.get(difficulty, THEME["text_muted"])
        Badge(row, text=diff_label, fg_color=THEME["bg_alt"], text_color=diff_color).grid(row=0, column=2, sticky="w", padx=spacing("md"), pady=spacing("item_gap"))

        acts = ctk.CTkFrame(row, fg_color="transparent")
        acts.grid(row=0, column=3, sticky="e", padx=spacing("md"), pady=spacing("icon_gap"))

        for icon, cmd in [
            (ICONS["edit"], lambda c=challenge: self._abrir_editar(c)),
            (ICONS["delete"], lambda c=challenge: self._excluir(c)),
        ]:
            GhostButton(
                acts, text=icon,
                width=30, height=30, corner_radius=RADIUS["xs"],
                text_color=THEME["text_secondary"],
                font=themed_font("body"),
                command=cmd,
            ).pack(side="left", padx=spacing("label_gap") // 2)

        assign_btn = PrimaryButton(
            acts, text=f"{ICONS['user']} Atribuir",
            command=lambda c=challenge: self._abrir_atribuir(c),
            height=30, width=100,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_on_primary"],
        )
        assign_btn.pack(side="right", padx=(spacing("sm"), 0))

    def _abrir_novo(self):
        def _salvar(dados, challenge_id=None):
            def _fetch():
                if challenge_id:
                    return self.servico.atualizar_desafio(challenge_id, dados)
                return self.servico.criar_desafio(dados)

            def _on_success(res):
                if isinstance(res, dict) and res.get("success") is False:
                    self._show_error(res.get("message", "Falha ao salvar desafio."))
                    return
                self.carregar_dados_async()

            def _on_error(exc):
                self._show_error(f"Falha ao salvar desafio: {exc}")

            AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

        _ChallengeFormModal(self, on_salvar=_salvar)

    def _abrir_editar(self, challenge):
        def _salvar(dados, challenge_id=None):
            def _fetch():
                return self.servico.atualizar_desafio(challenge.get("id"), dados)

            def _on_success(res):
                if isinstance(res, dict) and res.get("success") is False:
                    self._show_error(res.get("message", "Falha ao atualizar desafio."))
                    return
                self.carregar_dados_async()

            def _on_error(exc):
                self._show_error(f"Falha ao atualizar desafio: {exc}")

            AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

        _ChallengeFormModal(self, on_salvar=_salvar, challenge=challenge)

    def _abrir_atribuir(self, challenge):
        if not self._students:
            def _fetch():
                return self.servico_estudantes.listar_estudantes()

            def _on_success(res):
                if not self.winfo_exists():
                    return
                students = []
                if isinstance(res, dict):
                    data = res.get("data") or {}
                    if isinstance(data, list):
                        students = data
                    elif isinstance(data, dict):
                        students = data.get("students") or data.get("results") or []
                self._students = students
                self._mostrar_modal_atribuir(challenge, students)

            def _on_error(exc):
                self._show_error(f"Falha ao carregar estudantes: {exc}")

            AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)
        else:
            self._mostrar_modal_atribuir(challenge, self._students)

    def _mostrar_modal_atribuir(self, challenge, students):
        def _assign(challenge_id, student_id):
            def _fetch():
                return self.servico.atribuir_desafio({
                    "challenge_id": challenge_id,
                    "student_id": student_id,
                    "assigned_by_id": 1,
                })

            def _on_success(res):
                if isinstance(res, dict) and res.get("success") is False:
                    self._show_error(res.get("message", "Falha ao atribuir desafio."))
                    return
                self._show_success("Desafio atribuído com sucesso.")
                self.carregar_dados_async()

            def _on_error(exc):
                self._show_error(f"Falha ao atribuir desafio: {exc}")

            AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

        _AssignModal(self, on_assign=_assign, challenge_id=challenge.get("id"), students=students)

    def _excluir(self, challenge):
        if not self._confirmar(f"Excluir desafio '{challenge.get('title')}'?"):
            return

        def _fetch():
            return self.servico.deletar_desafio(challenge.get("id"))

        def _on_success(res):
            if isinstance(res, dict) and res.get("success") is False:
                self._show_error(res.get("message", "Falha ao excluir desafio."))
                return
            self.carregar_dados_async()

        def _on_error(exc):
            self._show_error(f"Falha ao excluir desafio: {exc}")

        AsyncRunner.run(task=_fetch, on_success=_on_success, on_error=_on_error, widget_ref=self)

    def _show_error(self, message: str, title: str = "Não foi possível concluir") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _show_success(self, message: str, duration: int = 3000) -> None:
        try:
            if hasattr(self, "_toast") and self._toast and self._toast.winfo_exists():
                self._toast.destroy()
            self._toast = Toast(
                self.winfo_toplevel(), message=message, status="success", duration=duration
            )
        except Exception:
            pass

    def _confirmar(self, mensagem: str) -> bool:
        modal = ctk.CTkToplevel(self)
        modal.title("Confirmar")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)
        w, h = 420, 200
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        resultado = {"ok": False}
        ctk.CTkLabel(
            modal, text=mensagem,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
            wraplength=360, justify="center"
        ).pack(pady=(24, 16))
        botoes = ctk.CTkFrame(modal, fg_color="transparent")
        botoes.pack(pady=(0, 20))
        ctk.CTkButton(
            botoes, text="Cancelar", width=110, height=36,
            fg_color=THEME["bg_alt"], hover_color=THEME["border"],
            text_color=THEME["text"],
            command=lambda: modal.destroy(),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            botoes, text="Confirmar", width=110, height=36,
            fg_color=THEME["primary"], hover_color=THEME["primary_hover"],
            text_color=THEME["text_on_primary"],
            command=lambda: self._confirmar_callback(modal, resultado),
        ).pack(side="right")
        modal.wait_window(modal)
        return resultado.get("ok", False)

    def _confirmar_callback(self, modal: ctk.CTkToplevel, resultado: dict):
        resultado["ok"] = True
        modal.destroy()

    def load_data(self):
        self.carregar_dados_async()

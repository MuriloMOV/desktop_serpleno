import logging
from datetime import datetime
from typing import Any

import customtkinter as ctk

from ser_pleno.ui.components.icons import ICONS, MOOD_EMOJIS, MOOD_LABELS
from ser_pleno.ui.components.ui_components import (
    Avatar,
    Card,
    DangerButton,
    Divider,
    EmptyState,
    GhostButton,
    KPICard,
    PrimaryButton,
    SectionCard,
    Toast,
)
from ser_pleno.ui.theme import (
    FONT_FAMILY,
    RADIUS,
    SPACING,
    THEME,
    blend_color,
    themed_font,
)
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.ui.views.base import _ErrorModal
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.avatar_utils import get_avatar_color
from ser_pleno.utils.mood import mood_emoji_from_score
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

_RISK_COLS = [
    ("Crítico", THEME["critico"], THEME["critico_soft"], "critico"),
    ("Alto", THEME["alto"], THEME["alto_soft"], "alto"),
    ("Médio", THEME["medio"], THEME["medio_soft"], "medio"),
    ("Normal", THEME["normal"], THEME["normal_soft"], "normal"),
]

_MOOD_COLOR = {
    1: THEME["danger"],
    2: THEME["alto"],
    3: THEME["medio"],
    4: THEME["success"],
    5: THEME["primary"],
}
_MOOD_LABEL = {1: "Muito triste", 2: "Triste", 3: "Neutro", 4: "Bem", 5: "Ótimo"}

_CHECKIN_TYPE_LABELS = {
    "weekly": "Semanal",
    "monthly": "Mensal",
    "post_session": "Pós-Sessão",
    "crisis": "Crise",
}

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


class _MoodEntryModal(ctk.CTkToplevel):
    def __init__(self, parent, on_save, student_id=None, student_name=""):
        super().__init__(parent)
        self.title("Registrar Humor")
        self.configure(fg_color=THEME["surface"])
        self.resizable(False, False)
        self._on_save = on_save
        w, h = 520, 620
        sx = self.winfo_screenwidth() // 2 - w // 2
        sy = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{sx}+{sy}")
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self._build(student_id, student_name)

    def _build(self, student_id, student_name):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["page_y"])
        ctk.CTkLabel(
            scroll,
            text="Registro de Humor",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 16))
        self._student_id = student_id
        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        row1.grid_columnconfigure((0, 1), weight=1)
        self._en_student = ctk.CTkEntry(
            row1,
            placeholder_text="Estudante",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_student.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._en_student.insert(0, student_name or "")
        self._en_student.configure(state="disabled")
        self._en_date = ctk.CTkEntry(
            row1,
            placeholder_text="Data",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_date.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self._en_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self._var_mood = ctk.StringVar(value="3")
        mood_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        mood_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            mood_frame,
            text="Nível de Humor (1–5)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        mood_opts = [f"{i} — {MOOD_LABELS[i]}" for i in range(1, 6)]
        self._sel_mood = ctk.CTkOptionMenu(
            mood_frame,
            values=mood_opts,
            variable=self._var_mood,
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        self._sel_mood.pack(fill="x")
        self._var_energy = ctk.StringVar(value="3")
        energy_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        energy_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            energy_frame,
            text="Nível de Energia (1–5)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._sl_energy = ctk.CTkSlider(
            energy_frame,
            from_=1,
            to=5,
            number_of_steps=4,
            progress_color=THEME["primary"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
        )
        self._sl_energy.pack(fill="x")
        self._sl_energy.set(3)
        self._var_stress = ctk.StringVar(value="3")
        stress_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stress_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            stress_frame,
            text="Nível de Estresse (1–5)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._sl_stress = ctk.CTkSlider(
            stress_frame,
            from_=1,
            to=5,
            number_of_steps=4,
            progress_color=THEME["danger"],
            button_color=THEME["danger"],
            button_hover_color=THEME["danger_strong"],
        )
        self._sl_stress.pack(fill="x")
        self._sl_stress.set(3)
        self._var_sleep = ctk.StringVar(value="3")
        sleep_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        sleep_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            sleep_frame,
            text="Qualidade do Sono (1–5)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._sl_sleep = ctk.CTkSlider(
            sleep_frame,
            from_=1,
            to=5,
            number_of_steps=4,
            progress_color=THEME["success"],
            button_color=THEME["success"],
            button_hover_color=THEME["success_strong"],
        )
        self._sl_sleep.pack(fill="x")
        self._sl_sleep.set(3)
        ctk.CTkLabel(
            scroll,
            text="Observações",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._txt_notes = ctk.CTkTextbox(
            scroll,
            font=themed_font("body"),
            height=80,
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            corner_radius=RADIUS["input"],
        )
        self._txt_notes.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            scroll,
            text="Gatilhos (separados por vírgula)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._en_triggers = ctk.CTkEntry(
            scroll,
            placeholder_text="Ex: falta de sono, pressão acadêmica",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_triggers.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            scroll,
            text="Atividades (separadas por vírgula)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._en_activities = ctk.CTkEntry(
            scroll,
            placeholder_text="Ex: estudou, fez exercício",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_activities.pack(fill="x", pady=(0, 16))
        footer = ctk.CTkFrame(scroll, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=self.destroy,
            width=110,
            height=38,
            corner_radius=RADIUS["button"],
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(0, 8))
        PrimaryButton(
            footer,
            text=f"{ICONS['save']}  Salvar",
            command=self._salvar,
            height=38,
            width=140,
        ).pack(side="right")

    def _salvar(self):
        try:
            mood_raw = self._sel_mood.get()
            mood_level = int(mood_raw.split(" — ")[0]) if " — " in mood_raw else int(mood_raw)
        except Exception:
            mood_level = 3
        dados = {
            "student_id": self._student_id,
            "mood_level": mood_level,
            "entry_date": self._en_date.get(),
            "energy_level": int(self._sl_energy.get()),
            "stress_level": int(self._sl_stress.get()),
            "sleep_quality": int(self._sl_sleep.get()),
            "notes": self._txt_notes.get("1.0", "end").strip(),
            "triggers": [t.strip() for t in self._en_triggers.get().split(",") if t.strip()],
            "activities": [a.strip() for a in self._en_activities.get().split(",") if a.strip()],
        }
        self._on_save(dados)
        self.destroy()


class _CheckinModal(ctk.CTkToplevel):
    def __init__(self, parent, on_save, student_id=None, student_name=""):
        super().__init__(parent)
        self.title("Novo Check-in")
        self.configure(fg_color=THEME["surface"])
        self.resizable(False, False)
        self._on_save = on_save
        w, h = 520, 680
        sx = self.winfo_screenwidth() // 2 - w // 2
        sy = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{sx}+{sy}")
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self._build(student_id, student_name)

    def _build(self, student_id, student_name):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["page_y"])
        ctk.CTkLabel(
            scroll,
            text="Novo Check-in",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 16))
        self._student_id = student_id
        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 12))
        row1.grid_columnconfigure((0, 1), weight=1)
        self._en_student = ctk.CTkEntry(
            row1,
            placeholder_text="Estudante",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_student.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._en_student.insert(0, student_name or "")
        self._en_student.configure(state="disabled")
        self._en_date = ctk.CTkEntry(
            row1,
            placeholder_text="Data",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_date.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self._en_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        type_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        type_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            type_frame,
            text="Tipo de Check-in",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._sel_type = ctk.CTkOptionMenu(
            type_frame,
            values=list(_CHECKIN_TYPE_LABELS.values()),
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        self._sel_type.pack(fill="x")
        self._sel_type.set("Semanal")
        self._var_wellbeing = ctk.StringVar(value="5")
        wellbeing_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        wellbeing_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            wellbeing_frame,
            text="Bem-estar Geral (1–10)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._sl_wellbeing = ctk.CTkSlider(
            wellbeing_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            progress_color=THEME["success"],
            button_color=THEME["success"],
            button_hover_color=THEME["success_strong"],
        )
        self._sl_wellbeing.pack(fill="x")
        self._sl_wellbeing.set(5)
        ctk.CTkLabel(
            scroll,
            text="Áreas de Atenção (separadas por vírgula)",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._en_areas = ctk.CTkEntry(
            scroll,
            placeholder_text="Ex: ansiedade, sono, estudos",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_areas.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            scroll,
            text="Recomendações",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._txt_recommendations = ctk.CTkTextbox(
            scroll,
            font=themed_font("body"),
            height=60,
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            corner_radius=RADIUS["input"],
        )
        self._txt_recommendations.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            scroll,
            text="Notas do Profissional",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._txt_prof_notes = ctk.CTkTextbox(
            scroll,
            font=themed_font("body"),
            height=60,
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            corner_radius=RADIUS["input"],
        )
        self._txt_prof_notes.pack(fill="x", pady=(0, 12))
        follow_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        follow_frame.pack(fill="x", pady=(0, 12))
        self._var_followup = ctk.StringVar(value="off")
        ctk.CTkSwitch(
            follow_frame,
            text="Necessita acompanhamento",
            variable=self._var_followup,
            onvalue="on",
            offvalue="off",
            progress_color=THEME["primary"],
            button_color=THEME["surface"],
            button_hover_color=THEME["bg_alt"],
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["pill"],
            cursor="hand2",
        ).pack(side="left")
        self._en_followup_date = ctk.CTkEntry(
            scroll,
            placeholder_text="Data do acompanhamento (YYYY-MM-DD)",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_followup_date.pack(fill="x", pady=(0, 16))
        footer = ctk.CTkFrame(scroll, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=self.destroy,
            width=110,
            height=38,
            corner_radius=RADIUS["button"],
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(0, 8))
        PrimaryButton(
            footer,
            text=f"{ICONS['save']}  Salvar Check-in",
            command=self._salvar,
            height=38,
            width=160,
        ).pack(side="right")

    def _salvar(self):
        type_map = {v: k for k, v in _CHECKIN_TYPE_LABELS.items()}
        dados = {
            "student_id": self._student_id,
            "check_in_type": type_map.get(self._sel_type.get(), "weekly"),
            "check_in_date": self._en_date.get(),
            "overall_wellbeing": int(self._sl_wellbeing.get()),
            "attention_areas": [a.strip() for a in self._en_areas.get().split(",") if a.strip()],
            "recommendations": self._txt_recommendations.get("1.0", "end").strip(),
            "professional_notes": self._txt_prof_notes.get("1.0", "end").strip(),
            "follow_up_needed": self._var_followup.get() == "on",
            "follow_up_date": self._en_followup_date.get() or None,
        }
        self._on_save(dados)
        self.destroy()


class _ChallengeFormModal(ctk.CTkToplevel):
    def __init__(self, parent, on_save, challenge_id=None, challenge_data=None):
        super().__init__(parent)
        self.title("Desafio" if not challenge_id else "Editar Desafio")
        self.configure(fg_color=THEME["surface"])
        self.resizable(False, False)
        self._on_save = on_save
        self._challenge_id = challenge_id
        w, h = 480, 520
        sx = self.winfo_screenwidth() // 2 - w // 2
        sy = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{sx}+{sy}")
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self._build(challenge_data or {})

    def _build(self, data):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["page_y"])
        ctk.CTkLabel(
            scroll,
            text="Desafio de Bem-Estar",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w", pady=(0, 16))
        ctk.CTkLabel(
            scroll,
            text="Título",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._en_title = ctk.CTkEntry(
            scroll,
            placeholder_text="Título do desafio",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_title.pack(fill="x", pady=(0, 12))
        self._en_title.insert(0, data.get("title", ""))
        row_cat = ctk.CTkFrame(scroll, fg_color="transparent")
        row_cat.pack(fill="x", pady=(0, 12))
        row_cat.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(
            row_cat,
            text="Categoria",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self._sel_cat = ctk.CTkOptionMenu(
            row_cat,
            values=[c[1] for c in _CHALLENGE_CATEGORIES],
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        self._sel_cat.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        cat_val = data.get("category", "emotional")
        cat_label = dict(_CHALLENGE_CATEGORIES).get(cat_val, "Emocional")
        self._sel_cat.set(cat_label)
        ctk.CTkLabel(
            row_cat,
            text="Dificuldade",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=1, sticky="w", pady=(0, 6))
        self._var_diff = ctk.StringVar(value=data.get("difficulty", "medium"))
        diff_opts = [
            c[1].capitalize() for c in [("easy", "Fácil"), ("medium", "Médio"), ("hard", "Difícil")]
        ]
        self._sel_diff = ctk.CTkOptionMenu(
            row_cat,
            values=diff_opts,
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            height=40,
            corner_radius=RADIUS["input"],
            font=themed_font("body"),
        )
        self._sel_diff.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        self._sel_diff.set("Médio")
        row_pts = ctk.CTkFrame(scroll, fg_color="transparent")
        row_pts.pack(fill="x", pady=(0, 12))
        row_pts.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkLabel(
            row_pts,
            text="Pontos",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self._en_points = ctk.CTkEntry(
            row_pts,
            placeholder_text="0",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_points.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self._en_points.insert(0, str(data.get("points", 0)))
        ctk.CTkLabel(
            row_pts,
            text="Ordem",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).grid(row=0, column=1, sticky="w", pady=(0, 6))
        self._en_order = ctk.CTkEntry(
            row_pts,
            placeholder_text="0",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._en_order.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        self._en_order.insert(0, str(data.get("order", 0)))
        ctk.CTkLabel(
            scroll,
            text="Descrição",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        ).pack(anchor="w", pady=(0, 6))
        self._txt_desc = ctk.CTkTextbox(
            scroll,
            font=themed_font("body"),
            height=80,
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            corner_radius=RADIUS["input"],
        )
        self._txt_desc.pack(fill="x", pady=(0, 16))
        self._txt_desc.insert("1.0", data.get("description", ""))
        footer = ctk.CTkFrame(scroll, fg_color="transparent")
        footer.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=self.destroy,
            width=110,
            height=38,
            corner_radius=RADIUS["button"],
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(0, 8))
        PrimaryButton(
            footer,
            text=f"{ICONS['save']}  Salvar",
            command=self._salvar,
            height=38,
            width=140,
        ).pack(side="right")

    def _salvar(self):
        cat_label = self._sel_cat.get()
        cat_map = {v: k for k, v in _CHALLENGE_CATEGORIES}
        category = cat_map.get(cat_label, "other")
        diff_label = self._sel_diff.get().lower()
        diff_map = {"fácil": "easy", "médio": "medium", "difícil": "hard"}
        difficulty = diff_map.get(diff_label, "medium")
        dados = {
            "title": self._en_title.get().strip(),
            "description": self._txt_desc.get("1.0", "end").strip(),
            "category": category,
            "difficulty": difficulty,
            "points": int(self._en_points.get() or 0),
            "order": int(self._en_order.get() or 0),
        }
        self._on_save(dados, self._challenge_id)
        self.destroy()


class BemEstarFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        import time as _time

        self._t0 = _time.perf_counter()
        super().__init__(
            parent,
            fg_color=THEME["bg"],
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.controller: Any = controller
        self.servico_bem_estar: Any = getattr(controller, "servico_bem_estar", None)
        self.colunas_risco: dict = {}
        self._chart_data: list = []
        self._selected_student: dict | None = None
        self._selected_challenge_id: int | None = None
        self._period_days: int = 30
        self._all_students: list = []
        self._detail_tab_cache: dict = {}
        self._mood_modal: _MoodEntryModal | None = None
        self._checkin_modal: _CheckinModal | None = None
        self._challenge_modal: _ChallengeFormModal | None = None
        self._editing_challenge_id: int | None = None
        self._current_user_id: int = 1
        self._lazy_sections_ready: bool = False

        self._student_search: ctk.CTkEntry | None = None
        self._student_list_body: ctk.CTkScrollableFrame | None = None
        self._profile_avatar: ctk.CTkFrame | None = None
        self._profile_name: ctk.CTkLabel | None = None
        self._profile_course: ctk.CTkLabel | None = None
        self._mini_chart_canvas: ctk.CTkCanvas | None = None
        self._detail_tabs: ctk.CTkTabview | None = None
        self._tab_history: str | None = None
        self._tab_checkins: str | None = None
        self._tab_challenges: str | None = None
        self._history_body: ctk.CTkScrollableFrame | None = None
        self._checkins_detail_body: ctk.CTkScrollableFrame | None = None
        self._challenges_detail_body: ctk.CTkScrollableFrame | None = None
        self._checkins_body: ctk.CTkFrame | None = None
        self._history_timeline_canvas: ctk.CTkCanvas | None = None
        self._lbl_general_avg: ctk.CTkLabel | None = None
        self._lbl_student_avg: ctk.CTkLabel | None = None
        self._lbl_total_entries: ctk.CTkLabel | None = None
        self._averages_row: ctk.CTkFrame | None = None
        self._student_timeline_data: list = []
        self._student_timeline_after_id = None

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=SPACING["page_x"], pady=SPACING["page_y"])

        self._criar_toolbar(self._content)
        self._criar_kpis(self._content)
        self._criar_secao_grafico(self._content)

        self.after_idle(self._build_lazy_sections)
        self.after_idle(self.load_data)
        log_view_init_ms("bem_estar", self._t0, widget_ref=self)

    def _build_lazy_sections(self):
        if getattr(self, "_lazy_sections_ready", False):
            return
        self._lazy_sections_ready = True
        content = getattr(self, "_content", None)
        if content is None or not content.winfo_exists():
            return
        self._criar_area_estudante(content)
        self._criar_visao_risco_ui(content)
        self._criar_lista_checkins_ui(content)
        self.after(0, self._carregar_lista_estudantes)

    def _criar_toolbar(self, content):
        bar = ctk.CTkFrame(content, fg_color="transparent")
        bar.pack(fill="x", pady=(0, SPACING["section_gap"]))
        ctk.CTkLabel(
            bar,
            text=f"{ICONS['mood_good']}  Bem-Estar",
            font=themed_font("h2", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")
        period_opts = [("7 dias", 7), ("30 dias", 30), ("90 dias", 90)]
        self._var_period = ctk.StringVar(value="30 dias")
        self._sel_period = ctk.CTkOptionMenu(
            right,
            values=[o[0] for o in period_opts],
            variable=self._var_period,
            fg_color=THEME["input_bg"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            width=120,
            height=36,
            corner_radius=RADIUS["button"],
            font=themed_font("body"),
            command=lambda _: self._on_period_changed(),
        )
        self._sel_period.pack(side="left", padx=(0, 8))
        GhostButton(
            right,
            text=f"{ICONS['export']}  Exportar",
            command=self._exportar_dados,
            height=36,
            width=120,
        ).pack(side="left", padx=(0, 8))
        PrimaryButton(
            right,
            text=f"{ICONS['chart']}  Novo Check-in",
            command=self._abrir_checkin_modal,
            height=36,
            width=180,
            fg_color=THEME["info"],
            hover_color=THEME["info_strong"],
            text_color=THEME["text_on_primary"],
        ).pack(side="left", padx=(0, 8))
        PrimaryButton(
            right,
            text=f"{ICONS['mood_good']}  Registrar Humor",
            command=self._abrir_mood_modal,
            height=36,
            width=180,
        ).pack(side="left")

    def _on_period_changed(self):
        label = self._var_period.get()
        for text, days in [("7 dias", 7), ("30 dias", 30), ("90 dias", 90)]:
            if text == label:
                self._period_days = days
                break
        self._detail_tab_cache = {}
        self.load_data()

    def _exportar_dados(self):
        self._show_success("Exportando dados de bem-estar...", duration=2000)

    def _abrir_mood_modal(self) -> None:
        if not self._selected_student:
            self._show_error("Selecione um estudante primeiro.", title="Atenção")
            return
        sid = self._selected_student.get("id")
        nome = self._selected_student.get("name", "")
        self._mood_modal = _MoodEntryModal(
            self,
            on_save=self._salvar_mood_entry,
            student_id=sid,
            student_name=nome,
        )

    def _salvar_mood_entry(self, dados: dict) -> None:
        def fetch() -> Any:
            return self.servico_bem_estar.criar_entrada_humor(dados)

        def on_success(res: dict) -> None:
            if res.get("success"):
                self._show_success(res.get("message", "Humor registrado."))
                self.load_data()
                if self._selected_student:
                    sid = self._selected_student.get("id")
                    self._carregar_historico_estudante(sid)
            else:
                self._show_error(res.get("message", "Falha ao registrar humor."))

        def on_error(exc: Exception) -> None:
            self._show_error(f"Falha ao registrar humor.\n{exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _abrir_checkin_modal(self) -> None:
        if not self._selected_student:
            self._show_error("Selecione um estudante primeiro.", title="Atenção")
            return
        sid = self._selected_student.get("id")
        nome = self._selected_student.get("name", "")
        self._checkin_modal = _CheckinModal(
            self,
            on_save=self._salvar_checkin,
            student_id=sid,
            student_name=nome,
        )

    def _salvar_checkin(self, dados: dict) -> None:
        def fetch() -> Any:
            return self.servico_bem_estar.criar_checkin(dados)

        def on_success(res: dict) -> None:
            if res.get("success"):
                self._show_success(res.get("message", "Check-in registrado."))
                self.load_data()
                if self._selected_student:
                    sid = self._selected_student.get("id")
                    self._carregar_checkins_estudante(sid)
            else:
                self._show_error(res.get("message", "Falha ao criar check-in."))

        def on_error(exc: Exception) -> None:
            self._show_error(f"Falha ao criar check-in.\n{exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _abrir_challenge_form(self, challenge_id=None):
        data = {}
        if challenge_id:

            def fetch():
                return self.servico_bem_estar.listar_desafios()

            def on_success(res):
                challenges = []
                if isinstance(res, dict):
                    challenges = (
                        (res.get("data") or {}).get("challenges")
                        if isinstance(res.get("data"), dict)
                        else res.get("data") or []
                    )
                ch = next((c for c in challenges if c.get("id") == challenge_id), {})
                self._challenge_modal = _ChallengeFormModal(
                    self,
                    on_save=self._salvar_challenge,
                    challenge_id=challenge_id,
                    challenge_data=ch,
                )

            def on_error(exc):
                self._show_error(f"Falha ao carregar desafio.\n{exc}")

            AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)
            return
        self._challenge_modal = _ChallengeFormModal(
            self,
            on_save=self._salvar_challenge,
            challenge_data=data,
        )

    def _salvar_challenge(self, dados, challenge_id=None):
        if challenge_id:

            def fetch():
                return self.servico_bem_estar.atualizar_desafio(challenge_id, dados)

            def on_success(res):
                if res.get("success"):
                    self._show_success("Desafio atualizado.")
                    self._carregar_desafios_estudante()
                    self._carregar_dashboard_desafios()
                else:
                    self._show_error(res.get("message", "Falha ao atualizar desafio."))

            def on_error(exc):
                self._show_error(f"Falha ao atualizar desafio.\n{exc}")

            AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)
        else:

            def fetch():
                return self.servico_bem_estar.criar_desafio(dados)

            def on_success(res):
                if res.get("success"):
                    self._show_success("Desafio criado.")
                    self._carregar_desafios_estudante()
                    self._carregar_dashboard_desafios()
                else:
                    self._show_error(res.get("message", "Falha ao criar desafio."))

            def on_error(exc):
                self._show_error(f"Falha ao criar desafio.\n{exc}")

            AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _deletar_desafio(self, challenge_id):
        if not self._confirmar("Excluir este desafio?"):
            return

        def fetch():
            return self.servico_bem_estar.deletar_desafio(challenge_id)

        def on_success(res):
            if res.get("success"):
                self._show_success("Desafio excluído.")
                self._carregar_desafios_estudante()
                self._carregar_dashboard_desafios()
            else:
                self._show_error(res.get("message", "Falha ao excluir desafio."))

        def on_error(exc):
            self._show_error(f"Falha ao excluir desafio.\n{exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _atribuir_desafio(self):
        if not self._selected_student or not self._selected_challenge_id:
            self._show_error("Selecione um estudante e um desafio.", title="Atenção")
            return
        dados = {
            "challenge_id": self._selected_challenge_id,
            "student_id": self._selected_student.get("id"),
            "assigned_by_id": self._current_user_id,
        }

        def fetch():
            return self.servico_bem_estar.atribuir_desafio(dados)

        def on_success(res):
            if res.get("success"):
                self._show_success("Desafio atribuído.")
                self._selected_challenge_id = None
                self._carregar_desafios_estudante(self._selected_student.get("id"))
                self._carregar_dashboard_desafios()
            else:
                self._show_error(res.get("message", "Falha ao atribuir desafio."))

        def on_error(exc):
            self._show_error(f"Falha ao atribuir desafio.\n{exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _completar_desafio(self, assignment_id):
        def fetch():
            return self.servico_bem_estar.completar_desafio(assignment_id)

        def on_success(res):
            if res.get("success"):
                self._show_success("Desafio concluído!")
                if self._selected_student:
                    self._carregar_desafios_estudante(self._selected_student.get("id"))
                self._carregar_dashboard_desafios()
            else:
                self._show_error(res.get("message", "Falha ao concluir desafio."))

        def on_error(exc):
            self._show_error(f"Falha ao concluir desafio.\n{exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _desatribuir_desafio(self, assignment_id):
        if not self._confirmar("Remover atribuição deste desafio?"):
            return

        def fetch():
            return self.servico_bem_estar.desatribuir_desafio(assignment_id)

        def on_success(res):
            if res.get("success"):
                self._show_success("Desafio removido.")
                if self._selected_student:
                    self._carregar_desafios_estudante(self._selected_student.get("id"))
                self._carregar_dashboard_desafios()
            else:
                self._show_error(res.get("message", "Falha ao remover atribuição."))

        def on_error(exc):
            self._show_error(f"Falha ao remover atribuição.\n{exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _carregar_lista_estudantes(self):
        def fetch():
            return self.servico_bem_estar.listar_estudantes()

        def on_success(res):
            students = []
            if isinstance(res, dict):
                data = res.get("data")
                if isinstance(data, list):
                    students = data
                elif isinstance(data, dict):
                    students = data.get("students", [])
            self._all_students = students
            self._renderizar_lista_estudantes(students)

        def on_error(exc):
            logging.error(f"Falha ao carregar estudantes: {exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _renderizar_lista_estudantes(self, lista: list):
        if not hasattr(self, "_student_list_body") or self._student_list_body is None or not self._student_list_body.winfo_exists():
            return
        for w in self._student_list_body.winfo_children():
            w.destroy()
        if not lista:
            EmptyState(
                self._student_list_body,
                icon=ICONS["mood_bad"],
                title="Nenhum estudante",
                subtitle="Ajuste o filtro de busca",
            ).pack(pady=16)
            return
        batch = WidgetBatchBuilder(parent=self._student_list_body, batch_size=30)
        for st in lista:
            if not isinstance(st, dict):
                continue
            batch.add(lambda s=st: self._criar_item_estudante(s))
        batch.execute()

    def _criar_item_estudante(self, st: dict):
        nome = st.get("name", "??")
        curso = st.get("course", "")
        row = ctk.CTkFrame(
            self._student_list_body,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"), padx=spacing("xs"))
        row.st_data = st
        row.bind("<Button-1>", lambda e, s=st, w=row: self._selecionar_estudante(s, w))
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("sm"))
        inner.grid_columnconfigure(1, weight=1)
        av = Avatar(inner, initials=nome[:2], size=32, color=get_avatar_color(nome))
        av.grid(row=0, column=0, rowspan=2, padx=(0, spacing("md")), sticky="ns")
        ctk.CTkLabel(
            inner,
            text=nome,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")
        if curso:
            ctk.CTkLabel(
                inner,
                text=curso,
                font=themed_font("caption"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).grid(row=1, column=1, sticky="w")
        row.bind(
            "<Enter>",
            lambda e, r=row, s=st: (
                r.configure(fg_color=THEME["primary_soft"]) if self._selected_student != s else None
            ),
        )
        row.bind(
            "<Leave>",
            lambda e, r=row, s=st: r.configure(
                fg_color=THEME["primary_soft"] if self._selected_student == s else THEME["bg_alt"]
            ),
        )

    def _selecionar_estudante(self, st: dict, widget=None):
        for w in self._student_list_body.winfo_children():
            w.configure(fg_color=THEME["bg_alt"])
        if widget:
            widget.configure(fg_color=THEME["primary_soft"])
        self._selected_student = st
        self._detail_tab_cache = {}
        sid = st.get("id")
        self._carregar_perfil_estudante(sid)
        self._carregar_historico_estudante(sid)
        self._carregar_checkins_estudante(sid)
        self._carregar_desafios_estudante(sid)
        self._carregar_dashboard_desafios()
        self._carregar_medias_gerais()

    def _carregar_perfil_estudante(self, student_id):
        def fetch():
            return self.servico_bem_estar.obter_humor_estudante(student_id)

        def on_success(res):
            if not self.winfo_exists():
                return
            entries = []
            student_name = "Estudante"
            if isinstance(res, dict):
                data = res.get("data") or {}
                if isinstance(data, dict):
                    entries = data.get("entries") or data.get("chart_data") or []
                    student_info = data.get("student") or {}
                    student_name = student_info.get("name", "Estudante")
                elif isinstance(data, list):
                    entries = data
            if hasattr(self, "_profile_name") and self._profile_name is not None and self._profile_name.winfo_exists():
                self._profile_name.configure(text=student_name)
            if hasattr(self, "_profile_avatar") and self._profile_avatar is not None and self._profile_avatar.winfo_exists():
                for w in self._profile_avatar.winfo_children():
                    w.destroy()
                Avatar(
                    self._profile_avatar,
                    initials=student_name[:2],
                    size=48,
                    color=get_avatar_color(student_name),
                ).pack(expand=True)
            if hasattr(self, "_mini_chart_canvas") and self._mini_chart_canvas is not None and entries:
                self._draw_mini_chart(entries)
            self._atualizar_medias_ui(student_entries=entries)

        def on_error(exc):
            logging.error(f"Falha ao carregar perfil: {exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _draw_mini_chart(self, entries):
        canvas = getattr(self, "_mini_chart_canvas", None)
        if not canvas or not canvas.winfo_exists():
            return
        canvas.delete("all")
        pts = [e.get("mood_level", 3) for e in entries[:30]]
        if not pts:
            return
        w = canvas.winfo_width() or 260
        h = canvas.winfo_height() or 60
        pad = 8
        cw = w - 2 * pad
        ch = h - 2 * pad
        coords = [
            (pad + i * cw / max(len(pts) - 1, 1), (h - pad) - ((v - 1) * ch / 4))
            for i, v in enumerate(pts)
        ]
        poly = []
        for x, y in coords:
            poly += [x, y]
        poly += [coords[-1][0], h - pad, coords[0][0], h - pad]
        canvas.create_polygon(poly, fill=THEME["chart_fill"], outline="")
        for i in range(len(coords) - 1):
            canvas.create_line(
                coords[i][0],
                coords[i][1],
                coords[i + 1][0],
                coords[i + 1][1],
                fill=THEME["chart_line"],
                width=2,
                capstyle="round",
            )
        for x, y in coords:
            canvas.create_oval(
                x - 3,
                y - 3,
                x + 3,
                y + 3,
                fill=THEME["dot_good"],
                outline=THEME["surface"],
                width=1,
            )

    def _draw_chart(self):
        self._draw_mini_chart(getattr(self, "_chart_data", []))

    def _carregar_historico_estudante(self, student_id):
        if not hasattr(self, "_history_body") or self._history_body is None or not self._history_body.winfo_exists():
            return
        for w in self._history_body.winfo_children():
            w.destroy()

        def fetch():
            return self.servico_bem_estar.obter_historico_humor_estudante(student_id)

        def on_success(res):
            if not self.winfo_exists():
                return
            entries = []
            if isinstance(res, dict):
                data = res.get("data") or {}
                if isinstance(data, dict):
                    entries = data.get("entries") or []
                elif isinstance(data, list):
                    entries = data
            self._student_timeline_data = entries
            self._draw_student_timeline(entries)
            self._atualizar_medias_ui(student_entries=entries)
            if not entries:
                EmptyState(
                    self._history_body,
                    icon=ICONS["chart"],
                    title="Sem registros de humor",
                    subtitle="Os registros aparecerão aqui quando houver entradas",
                ).pack(pady=16)
                return
            batch = WidgetBatchBuilder(parent=self._history_body, batch_size=20)
            for e in entries:
                batch.add(lambda e=e: self._criar_row_historico(e))
            batch.execute()

        def on_error(exc):
            logging.error(f"Falha ao carregar histórico: {exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _criar_row_historico(self, e: dict):
        mood = e.get("mood_level", 3)
        emoji = MOOD_EMOJIS.get(mood, MOOD_EMOJIS[3])
        label = MOOD_LABELS.get(mood, "Neutro")
        date = e.get("entry_date", "—")
        energy = e.get("energy_level", "—")
        stress = e.get("stress_level", "—")
        row = ctk.CTkFrame(
            self._history_body,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"))
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("sm"))
        inner.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(inner, text=emoji, font=themed_font("h3")).grid(
            row=0, column=0, padx=(0, spacing("md"))
        )
        ctk.CTkLabel(
            inner,
            text=label,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            inner,
            text=f"E:{energy} S:{stress}",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
            anchor="e",
        ).grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(
            inner,
            text=str(date),
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(2, 0))

    def _carregar_checkins_estudante(self, student_id):
        if not hasattr(self, "_checkins_detail_body") or self._checkins_detail_body is None or not self._checkins_detail_body.winfo_exists():
            return
        for w in self._checkins_detail_body.winfo_children():
            w.destroy()

        def fetch():
            return self.servico_bem_estar.listar_checkins()

        def on_success(res):
            if not self.winfo_exists():
                return
            checkins = []
            if isinstance(res, dict):
                data = res.get("data") or {}
                if isinstance(data, dict):
                    checkins = data.get("checkins") or []
                elif isinstance(data, list):
                    checkins = data
            checkins = [
                c
                for c in checkins
                if c.get("student_id") == student_id or c.get("student_id") == str(student_id)
            ]
            if not checkins:
                EmptyState(
                    self._checkins_detail_body,
                    icon=ICONS["chart"],
                    title="Nenhum check-in",
                    subtitle="Os check-ins aparecerão aqui",
                ).pack(pady=16)
                return
            batch = WidgetBatchBuilder(parent=self._checkins_detail_body, batch_size=20)
            for c in checkins:
                batch.add(lambda c=c: self._criar_row_checkin_detail(c))
            batch.execute()

        def on_error(exc):
            logging.error(f"Falha ao carregar check-ins: {exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _criar_row_checkin_detail(self, c: dict):
        ctype = c.get("check_in_type", "—")
        ctype_label = _CHECKIN_TYPE_LABELS.get(ctype, ctype)
        wellbeing = c.get("overall_wellbeing", "—")
        date = c.get("check_in_date", c.get("date", "—"))
        followup = c.get("follow_up_needed", False)
        areas = c.get("attention_areas", [])
        recommendations = c.get("recommendations", "")
        row = ctk.CTkFrame(
            self._checkins_detail_body,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"))
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            inner,
            text=ctype_label,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            inner,
            text=str(date),
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
            anchor="e",
        ).grid(row=0, column=2, sticky="e")
        ctk.CTkLabel(
            inner,
            text=f"Bem-estar: {wellbeing}/10" + ("  ! Acompanhamento" if followup else ""),
            font=themed_font("body"),
            text_color=THEME["warning"] if followup else THEME["text"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        if recommendations:
            ctk.CTkLabel(
                inner,
                text=str(recommendations)[:120],
                font=themed_font("caption"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).grid(row=2, column=0, sticky="w", pady=(2, 0))
        if areas:
            ctk.CTkLabel(
                inner,
                text="Áreas: " + ", ".join(str(a) for a in areas[:3]),
                font=themed_font("caption"),
                text_color=THEME["text_muted"],
                anchor="w",
            ).grid(row=3, column=0, sticky="w", pady=(2, 0))

    def _carregar_desafios_estudante(self, student_id=None):
        if not hasattr(self, "_challenges_detail_body") or self._challenges_detail_body is None or not self._challenges_detail_body.winfo_exists():
            return
        for w in self._challenges_detail_body.winfo_children():
            w.destroy()

        sid = student_id or (self._selected_student.get("id") if self._selected_student else None)
        if not sid:
            return

        def fetch():
            return self.servico_bem_estar.listar_desafios_estudante(sid)

        def on_success(res):
            if not self.winfo_exists():
                return
            assignments = []
            if isinstance(res, dict):
                data = res.get("data") or {}
                if isinstance(data, dict):
                    assignments = data.get("assignments") or []
                elif isinstance(data, list):
                    assignments = res.get("data") or []
            if not assignments:
                EmptyState(
                    self._challenges_detail_body,
                    icon=ICONS["heart"],
                    title="Nenhum desafio atribuído",
                    subtitle="Os desafios aparecerão aqui",
                ).pack(pady=16)
                return
            batch = WidgetBatchBuilder(parent=self._challenges_detail_body, batch_size=20)
            for a in assignments:
                batch.add(lambda a=a: self._criar_row_challenge_detail(a))
            batch.execute()

        def on_error(exc):
            logging.error(f"Falha ao carregar desafios: {exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _criar_row_challenge_detail(self, a: dict):
        ch = a.get("challenge") or {}
        title = ch.get("title", a.get("challenge_title", "Desafio"))
        xp = ch.get("points", 0)
        category = ch.get("category", "")
        cat_label = dict(_CHALLENGE_CATEGORIES).get(category, category)
        is_completed = a.get("is_completed", False)
        completed_at = a.get("completed_at", "")
        assignment_id = a.get("id")
        row = ctk.CTkFrame(
            self._challenges_detail_body,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"))
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("md"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            inner,
            text=title,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            inner,
            text=f"{cat_label} · {xp} XP",
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        status_text = "Concluído" + (f" em {str(completed_at)[:10]}" if completed_at else "")
        status_color = THEME["success"] if is_completed else THEME["warning"]
        ctk.CTkLabel(
            inner,
            text=status_text,
            font=themed_font("caption", "bold"),
            text_color=status_color,
            anchor="e",
        ).grid(row=0, column=2, sticky="e")
        if not is_completed:
            PrimaryButton(
                inner,
                text=f"{ICONS['check']}  Concluir",
                command=lambda aid=assignment_id: self._completar_desafio(aid),
                height=30,
                width=100,
                fg_color=THEME["success"],
                hover_color=THEME["success_strong"],
                text_color=THEME["text_on_primary"],
            ).grid(row=1, column=2, sticky="e", pady=(4, 0))
        DangerButton(
            inner,
            text=f"{ICONS['delete']}",
            command=lambda aid=assignment_id: self._desatribuir_desafio(aid),
            height=30,
            width=36,
            fg_color=THEME["danger"],
            hover_color=THEME["danger_strong"],
        ).grid(row=0, column=3, padx=(spacing("sm"), 0))

    def _carregar_dashboard_desafios(self):
        def fetch():
            return self.servico_bem_estar.obter_dashboard_desafios()

        def on_success(res):
            if not self.winfo_exists():
                return
            summary = {}
            if isinstance(res, dict):
                data = res.get("data") or {}
                if isinstance(data, dict):
                    summary = data.get("summary") or {}
            total = summary.get("total_assignments", 0)
            completed = summary.get("completed_assignments", 0)
            rate = summary.get("completion_rate", 0)
            if hasattr(self, "_lbl_dash_total"):
                self._lbl_dash_total.configure(text=str(total))
            if hasattr(self, "_lbl_dash_completed"):
                self._lbl_dash_completed.configure(text=str(completed))
            if hasattr(self, "_lbl_dash_rate"):
                self._lbl_dash_rate.configure(text=f"{rate}%")

        def on_error(exc):
            logging.error(f"Falha ao carregar dashboard desafios: {exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def load_data(self) -> None:
        self._set_status_carregando()

        def fetch() -> tuple:
            dash = self.servico_bem_estar.obter_dashboard()
            checkins = self.servico_bem_estar.listar_checkins()
            risks = self.servico_bem_estar.listar_estudantes_risco()
            medias = self.servico_bem_estar.obter_medias_humor()
            return dash, checkins, risks, medias

        def on_success(result: tuple) -> None:
            dash, checkins, risks, medias = result
            self.update_ui(dash, checkins, risks)
            if isinstance(medias, dict):
                data = medias.get("data") or {}
                if isinstance(data, dict):
                    avg = data.get("average_mood")
                    self._atualizar_medias_ui(general_avg=avg)

        def on_error(exc: Exception) -> None:
            self._show_error(
                f"Não foi possível carregar os dados de bem-estar.\n{exc}", title="Erro de conexão"
            )
            self._set_status_erro()

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def update_ui(self, dash_res: dict, checkins_res: dict, risks_res: dict) -> None:
        if dash_res.get("success"):
            self.update_metrics(dash_res.get("data", {}))
        else:
            logging.warning("Dashboard retornou erro: %s", dash_res)
        if checkins_res.get("success"):
            data = checkins_res.get("data", {})
            checkins = data.get("checkins") if isinstance(data, dict) else []
            self.populate_checkins(checkins or [])
        else:
            logging.warning("Check-ins retornaram erro: %s", checkins_res)
        if risks_res.get("success"):
            data = risks_res.get("data", {})
            groups = data.get("groups", {})
            mapping = {"critical": "critico", "high": "alto", "medium": "medio", "low": "normal"}
            flat = []
            for bk, ui in mapping.items():
                for s in groups.get(bk, []):
                    s["level"] = ui
                    s["msg"] = ", ".join(s.get("reasons", [])) or "Requer atenção"
                    flat.append(s)
            self.populate_risks(flat)
        else:
            logging.warning("Risco retornou erro: %s", risks_res)

    def update_metrics(self, data: dict) -> None:
        summary = data.get("summary", {})
        humor = summary.get("average_mood")
        if humor is not None and hasattr(self, "_kpi_humor"):
            emoji = mood_emoji_from_score(round(humor))
            self._kpi_humor.set_value(f"{emoji}  {humor:.1f}")
        moods = data.get("moods", []) or []
        if moods:
            self._chart_data = moods
            self.draw_30day_chart()
            self._update_distribution(moods)
        else:
            self._chart_data = []
            self.draw_30day_chart()
            self._update_distribution([])

    def _criar_kpis(self, content):
        row = ctk.CTkFrame(content, fg_color="transparent")
        row.pack(fill="x", pady=(0, SPACING["section_gap"]))
        kpis = [
            (
                "Humor Médio",
                f"{ICONS['mood_good']}  —",
                ICONS["heart"],
                THEME["kpi_blue"],
                THEME["kpi_blue_soft"],
                "_kpi_humor",
                "Média dos últimos 7 dias",
            ),
            (
                "Participação",
                "—%",
                ICONS["chart"],
                THEME["kpi_pink"],
                THEME["kpi_pink_soft"],
                "_kpi_part",
                "Taxa de check-ins",
            ),
            (
                "Alertas Críticos",
                "—",
                ICONS["alert"],
                THEME["kpi_red"],
                THEME["kpi_red_soft"],
                "_kpi_crit",
                "Estudantes em situação crítica",
            ),
        ]
        for i, (title, initial, icon, accent, soft, attr, sub) in enumerate(kpis):
            row.grid_columnconfigure(i, weight=1)
            card = KPICard(
                row, title=title, value=initial, icon=icon, accent=accent, unit="", size="md"
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2)
            setattr(self, attr, card)

    def _criar_secao_grafico(self, content):
        card = SectionCard(
            content, f"{ICONS['chart']}  Tendência de Bem-Estar — últimos {self._period_days} dias"
        )
        card.pack(fill="x", pady=(0, SPACING["section_gap"]))
        self._secao_grafico_outer = card.body
        chart_wrap = ctk.CTkFrame(card.body, fg_color="transparent")
        chart_wrap.pack(
            fill="both", expand=True, padx=spacing("sm"), pady=(spacing("sm"), spacing("md"))
        )
        chart_wrap.grid_rowconfigure(0, weight=1)
        chart_wrap.grid_columnconfigure(0, weight=1)
        self.canvas_30d = ctk.CTkCanvas(
            chart_wrap, bg=THEME["surface"], height=200, highlightthickness=0
        )
        self.canvas_30d.grid(row=0, column=0, sticky="nsew")
        self._chart_after_id = None
        chart_wrap.bind("<Configure>", self._schedule_draw_chart)
        self._chart_empty = EmptyState(
            chart_wrap,
            icon=ICONS["chart"],
            title="Sem dados de humor",
            subtitle="Os registros aparecerão aqui quando houver entradas",
        )
        self._chart_empty.grid(row=0, column=0, sticky="nsew")
        self._chart_empty.lower()
        dist_row = ctk.CTkFrame(card.body, fg_color="transparent")
        dist_row.pack(fill="x", pady=(spacing("xs"), spacing("sm")))
        self._dist_bars: dict[str, ctk.CTkFrame] = {}
        self._dist_pcts: dict[str, ctk.CTkLabel] = {}
        for label, color, pct_key, default in [
            (f"{ICONS['mood_good']}  Bom", THEME["success"], "bom", 65),
            (f"{ICONS['mood_bad']}  Neutro", THEME["warning"], "med", 25),
            (f"{ICONS['mood_bad']}  Baixo", THEME["danger"], "mau", 10),
        ]:
            col = ctk.CTkFrame(dist_row, fg_color="transparent")
            col.pack(side="left", expand=True, padx=SPACING["grid_gap"], pady=(0, spacing("xs")))
            ctk.CTkLabel(
                col,
                text=label,
                font=themed_font("body", "bold"),
                text_color=THEME["text_secondary"],
            ).pack(anchor="w", pady=(0, spacing("xs")))
            bar_bg = ctk.CTkFrame(
                col, height=8, fg_color=THEME["chart_grid"], corner_radius=RADIUS["pill"]
            )
            bar_bg.pack(fill="x", pady=(0, spacing("xs")))
            bar_bg.pack_propagate(False)
            fill = ctk.CTkFrame(bar_bg, height=8, fg_color=color, corner_radius=RADIUS["pill"])
            fill.pack(side="left", fill="y")
            self._dist_bars[pct_key] = fill
            pct_lbl = ctk.CTkLabel(
                col, text=f"{default}%", font=themed_font("body", "bold"), text_color=THEME["text"]
            )
            pct_lbl.pack(anchor="w", pady=(spacing("xs"), 0))
            self._dist_pcts[pct_key] = pct_lbl

    def _schedule_draw_chart(self, event=None):
        if self._chart_after_id:
            self.after_cancel(self._chart_after_id)
        self._chart_after_id = self.after(80, lambda: self.draw_30day_chart())

    def draw_30day_chart(self, data=None):
        if data:
            self._chart_data = data
        self.canvas_30d.delete("all")
        cw = self.canvas_30d.winfo_width()
        ch = self.canvas_30d.winfo_height()
        if cw < 80 or ch < 60:
            return
        pts = (
            [
                d.get("mood_level") or d.get("avg_mood") or d.get("media_humor") or 3.0
                for d in self._chart_data
            ]
            if self._chart_data
            else []
        )
        if not pts:
            self.canvas_30d.delete("all")
            if hasattr(self, "_chart_empty") and self._chart_empty.winfo_exists():
                self._chart_empty.lift()
            return
        if hasattr(self, "_chart_empty") and self._chart_empty.winfo_exists():
            self._chart_empty.lower()
        mx, my = 40, 20
        cw2 = cw - 2 * mx
        ch2 = ch - 2 * my
        n = len(pts)
        for i in range(6):
            v = 1 + i
            gy = (ch - my) - (i * ch2 / 5)
            self.canvas_30d.create_line(mx, gy, cw - mx, gy, fill=THEME["chart_grid"], dash=(3, 5))
            self.canvas_30d.create_text(
                mx - 6, gy, text=str(v), font=(FONT_FAMILY, 8), fill=THEME["text_muted"], anchor="e"
            )
        coords = [
            (mx + i * cw2 / max(n - 1, 1), (ch - my) - ((v - 1) * ch2 / 4))
            for i, v in enumerate(pts)
        ]
        poly = []
        for x, y in coords:
            poly += [x, y]
        poly += [coords[-1][0], ch - my, coords[0][0], ch - my]
        self.canvas_30d.create_polygon(poly, fill=THEME["chart_fill"], outline="")
        for i in range(len(coords) - 1):
            self.canvas_30d.create_line(
                coords[i][0],
                coords[i][1],
                coords[i + 1][0],
                coords[i + 1][1],
                fill=THEME["chart_line"],
                width=2.5,
                capstyle="round",
                joinstyle="round",
            )
        for i, (x, y) in enumerate(coords):
            v = pts[i]
            dot_c = (
                THEME["dot_bad"]
                if v < 2.5
                else (THEME["dot_mid"] if v < 3.5 else THEME["dot_good"])
            )
            self.canvas_30d.create_oval(
                x - 4, y - 4, x + 4, y + 4, fill=dot_c, outline=THEME["surface"], width=2
            )
        step = max(1, n // 7)
        for i, (x, _) in enumerate(coords):
            if i % step == 0 and self._chart_data:
                raw = self._chart_data[i]
                lbl = raw.get("entry_date") or raw.get("date") or raw.get("data") or ""
                lbl = str(lbl)
                if len(lbl) > 5:
                    lbl = lbl[5:]
                self.canvas_30d.create_text(
                    x, ch - 6, text=lbl, font=(FONT_FAMILY, 8), fill=THEME["text_secondary"]
                )

    def _update_distribution(self, moods: list[dict]):
        if not moods:
            for pct_key in ("bom", "med", "mau"):
                if pct_key in self._dist_pcts:
                    self._dist_pcts[pct_key].configure(text="0%")
                fill = self._dist_bars.get(pct_key)
                if fill and fill.winfo_exists():
                    fill.configure(width=1)
            return
        total = len(moods)
        bom = sum(1 for m in moods if (m.get("mood_level") or 0) >= 4)
        mau = sum(1 for m in moods if (m.get("mood_level") or 0) <= 2)
        med = total - bom - mau

        def _set(pct_key, count):
            pct = int((count / total) * 100) if total else 0
            if pct_key in self._dist_pcts:
                self._dist_pcts[pct_key].configure(text=f"{pct}%")
            fill = self._dist_bars.get(pct_key)
            if fill and fill.winfo_exists():
                parent = fill.master
                if parent.winfo_exists():
                    fill.configure(width=max(1, int(parent.winfo_width() * pct / 100)))

        _set("bom", bom)
        _set("med", med)
        _set("mau", mau)

    def _criar_area_estudante(self, content):
        outer = Card(content, padding=(SPACING["card_pad"], SPACING["label_gap"]), auto_body=False)
        outer.pack(fill="x", pady=(0, SPACING["section_gap"]))
        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(
            fill="x", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], SPACING["label_gap"])
        )
        ctk.CTkLabel(
            hdr,
            text=f"{ICONS['user']}  Visão por Estudante",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")
        Divider(outer).pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["label_gap"]))
        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(1, weight=1)
        search_row = ctk.CTkFrame(body, fg_color="transparent")
        search_row.grid(row=0, column=0, sticky="ew", pady=(0, spacing("sm")))
        search_row.grid_columnconfigure(0, weight=1)
        self._student_search = ctk.CTkEntry(
            search_row,
            placeholder_text="Buscar estudante por nome...",
            fg_color=THEME["input_bg"],
            border_width=1,
            border_color=THEME["input_border"],
            font=themed_font("body"),
            height=40,
        )
        self._student_search.grid(row=0, column=0, sticky="ew", padx=(0, spacing("sm")))
        self._student_search.bind("<KeyRelease>", self._filtrar_lista_estudantes)
        self._student_list_body = ctk.CTkScrollableFrame(
            body,
            fg_color="transparent",
            height=160,
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self._student_list_body.grid(row=1, column=0, sticky="nsew")
        detail_card = Card(body, auto_body=False)
        detail_card.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(spacing("md"), 0))
        detail_card._inner.grid_columnconfigure(0, weight=1)
        detail_card._inner.grid_rowconfigure(3, weight=1)
        profile_hdr = ctk.CTkFrame(detail_card._inner, fg_color="transparent")
        profile_hdr.grid(
            row=0, column=0, sticky="ew", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], 0)
        )
        self._profile_avatar = ctk.CTkFrame(
            profile_hdr, width=48, height=48, fg_color="transparent"
        )
        self._profile_avatar.pack(side="left", padx=(0, spacing("md")))
        self._profile_avatar.pack_propagate(False)
        Avatar(self._profile_avatar, initials="??", size=48, color=THEME["primary"]).pack(
            expand=True
        )
        name_stack = ctk.CTkFrame(profile_hdr, fg_color="transparent")
        name_stack.pack(side="left", fill="both", expand=True)
        self._profile_name = ctk.CTkLabel(
            name_stack,
            text="Selecione um estudante",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
            anchor="w",
        )
        self._profile_name.pack(anchor="w")
        self._profile_course = ctk.CTkLabel(
            name_stack,
            text="Busque ou selecione na lista",
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        )
        self._profile_course.pack(anchor="w", pady=(2, 0))
        actions = ctk.CTkFrame(profile_hdr, fg_color="transparent")
        actions.pack(side="right")
        PrimaryButton(
            actions,
            text=f"{ICONS['mood_good']}  Humor",
            command=self._abrir_mood_modal,
            height=36,
            width=110,
        ).pack(side="left", padx=(0, spacing("xs")))
        PrimaryButton(
            actions,
            text=f"{ICONS['chart']}  Check-in",
            command=self._abrir_checkin_modal,
            height=36,
            width=110,
            fg_color=THEME["info"],
            hover_color=THEME["info_strong"],
            text_color=THEME["text_on_primary"],
        ).pack(side="left", padx=(0, spacing("xs")))
        mini_chart_card = Card(detail_card._inner, auto_body=False)
        mini_chart_card.grid(
            row=1, column=0, sticky="nsew", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"])
        )
        mini_chart_card.grid_rowconfigure(0, weight=1)
        mini_chart_card.grid_columnconfigure(0, weight=1)
        self._mini_chart_canvas = ctk.CTkCanvas(
            mini_chart_card._inner, bg=THEME["surface"], height=80, highlightthickness=0
        )
        self._mini_chart_canvas.grid(row=0, column=0, sticky="nsew")
        self._averages_row = ctk.CTkFrame(detail_card._inner, fg_color="transparent")
        self._averages_row.grid(row=2, column=0, sticky="ew", padx=SPACING["card_pad"], pady=(0, spacing("xs")))
        self._lbl_general_avg = ctk.CTkLabel(
            self._averages_row,
            text="Média Geral: —",
            font=themed_font("caption", "bold"),
            text_color=THEME["text_secondary"],
        )
        self._lbl_general_avg.pack(side="left", padx=(0, spacing("md")))
        self._lbl_student_avg = ctk.CTkLabel(
            self._averages_row,
            text="Média: —",
            font=themed_font("caption", "bold"),
            text_color=THEME["primary"],
        )
        self._lbl_student_avg.pack(side="left", padx=(0, spacing("md")))
        self._lbl_total_entries = ctk.CTkLabel(
            self._averages_row,
            text="Registros: —",
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        )
        self._lbl_total_entries.pack(side="right")
        self._detail_tabs = ctk.CTkTabview(
            detail_card._inner,
            fg_color="transparent",
            segmented_button_fg_color=THEME["bg_alt"],
            segmented_button_selected_color=THEME["primary"],
            segmented_button_selected_hover_color=THEME["primary_hover"],
            text_color=THEME["text_secondary"],
            text_color_disabled=THEME["text_muted"],
            corner_radius=RADIUS["lg"],
        )
        self._detail_tabs.grid(
            row=3, column=0, sticky="nsew", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"])
        )
        self._tab_history = self._detail_tabs.add("Histórico")
        self._tab_checkins = self._detail_tabs.add("Check-ins")
        self._tab_challenges = self._detail_tabs.add("Desafios")
        self._history_timeline_canvas = ctk.CTkCanvas(
            self._tab_history, bg=THEME["surface"], height=120, highlightthickness=0
        )
        self._history_timeline_canvas.pack(fill="x", pady=(0, spacing("sm")))
        self._history_timeline_canvas.bind("<Configure>", self._schedule_draw_student_timeline)
        self._history_body = ctk.CTkScrollableFrame(
            self._tab_history,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self._history_body.pack(fill="both", expand=True)
        self._checkins_detail_body = ctk.CTkScrollableFrame(
            self._tab_checkins,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self._checkins_detail_body.pack(fill="both", expand=True)
        self._challenges_detail_body = ctk.CTkScrollableFrame(
            self._tab_challenges,
            fg_color="transparent",
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self._challenges_detail_body.pack(fill="both", expand=True)
        self._detail_tabs.set("Histórico")

    def _atualizar_medias_ui(self, general_avg=None, student_entries=None):
        if hasattr(self, "_lbl_general_avg") and self._lbl_general_avg and self._lbl_general_avg.winfo_exists():
            if general_avg is not None:
                self._lbl_general_avg.configure(text=f"Média Geral: {general_avg:.1f}")
            else:
                self._lbl_general_avg.configure(text="Média Geral: —")
        if hasattr(self, "_lbl_student_avg") and self._lbl_student_avg and self._lbl_student_avg.winfo_exists():
            if student_entries:
                avg = sum(e.get("mood_level", 3) for e in student_entries) / len(student_entries)
                self._lbl_student_avg.configure(text=f"Média: {avg:.1f}")
            else:
                self._lbl_student_avg.configure(text="Média: —")
        if hasattr(self, "_lbl_total_entries") and self._lbl_total_entries and self._lbl_total_entries.winfo_exists():
            if student_entries is not None:
                self._lbl_total_entries.configure(text=f"Registros: {len(student_entries)}")
            else:
                self._lbl_total_entries.configure(text="Registros: —")

    def _carregar_medias_gerais(self):
        def fetch():
            return self.servico_bem_estar.obter_medias_humor()

        def on_success(res):
            if not self.winfo_exists():
                return
            avg = None
            if isinstance(res, dict):
                data = res.get("data") or {}
                if isinstance(data, dict):
                    avg = data.get("average_mood")
            self._atualizar_medias_ui(general_avg=avg)

        def on_error(exc):
            logging.error(f"Falha ao carregar médias gerais: {exc}")

        AsyncRunner.run(task=fetch, on_success=on_success, on_error=on_error, widget_ref=self)

    def _schedule_draw_student_timeline(self, event=None):
        if hasattr(self, "_student_timeline_after_id") and self._student_timeline_after_id:
            self.after_cancel(self._student_timeline_after_id)
        self._student_timeline_after_id = self.after(80, lambda: self._draw_student_timeline(getattr(self, "_student_timeline_data", [])))

    def _draw_student_timeline(self, entries):
        canvas = getattr(self, "_history_timeline_canvas", None)
        if not canvas or not canvas.winfo_exists():
            return
        canvas.delete("all")
        if not entries:
            return
        sorted_entries = sorted(entries, key=lambda e: e.get("entry_date", "") or "")
        pts = [e.get("mood_level", 3) for e in sorted_entries]
        w = canvas.winfo_width() or 400
        h = canvas.winfo_height() or 120
        pad = 20
        cw = w - 2 * pad
        ch = h - 2 * pad
        coords = [
            (pad + i * cw / max(len(pts) - 1, 1), (h - pad) - ((v - 1) * ch / 4))
            for i, v in enumerate(pts)
        ]
        poly = []
        for x, y in coords:
            poly += [x, y]
        poly += [coords[-1][0], h - pad, coords[0][0], h - pad]
        canvas.create_polygon(poly, fill=THEME["chart_fill"], outline="")
        for i in range(len(coords) - 1):
            canvas.create_line(
                coords[i][0], coords[i][1],
                coords[i + 1][0], coords[i + 1][1],
                fill=THEME["chart_line"], width=2, capstyle="round"
            )
        for x, y in coords:
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=THEME["dot_good"], outline=THEME["surface"], width=1)
        step = max(1, len(pts) // 6)
        for i, (x, _) in enumerate(coords):
            if i % step == 0 and sorted_entries:
                lbl = sorted_entries[i].get("entry_date", "")
                lbl = str(lbl)
                if len(lbl) > 5:
                    lbl = lbl[5:]
                canvas.create_text(x, h - 6, text=lbl, font=(FONT_FAMILY, 8), fill=THEME["text_secondary"])

    def _filtrar_lista_estudantes(self, _=None):
        termo = self._student_search.get().lower().strip()
        filtrados = (
            [s for s in self._all_students if termo in s.get("name", "").lower()]
            if termo
            else self._all_students
        )
        self._renderizar_lista_estudantes(filtrados)

    def _criar_visao_risco_ui(self, content):
        cols_card = Card(
            content, padding=(SPACING["card_pad"], SPACING["label_gap"]), auto_body=False
        )
        cols_card.pack(fill="x", pady=(0, SPACING["section_gap"]))
        hdr = ctk.CTkFrame(cols_card, fg_color="transparent")
        hdr.pack(
            fill="x", padx=SPACING["card_pad"], pady=(SPACING["card_pad"], SPACING["label_gap"])
        )
        ctk.CTkLabel(
            hdr,
            text=f"{ICONS['mood_good']}  Visão de Risco dos Estudantes",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")
        ctk.CTkLabel(
            hdr,
            text="Classificação por nível de atenção necessária",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=(10, 0), pady=(2, 0))
        Divider(cols_card).pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["label_gap"]))
        cols_wrap = ctk.CTkFrame(cols_card, fg_color="transparent")
        cols_wrap.pack(fill="x", padx=SPACING["card_pad"], pady=(0, SPACING["card_pad"]))
        for i in range(4):
            cols_wrap.grid_columnconfigure(i, weight=1)
        self.colunas_risco = {}
        for i, (title, color, soft, key) in enumerate(_RISK_COLS):
            col_card = ctk.CTkFrame(
                cols_wrap,
                fg_color=THEME["surface"],
                corner_radius=RADIUS["card"],
                border_width=1,
                border_color=THEME["border"],
            )
            col_card.grid(row=0, column=i, sticky="nsew", padx=SPACING["grid_gap"] // 2)
            col_card.grid_rowconfigure(1, weight=1)
            col_card.grid_columnconfigure(0, weight=1)
            col_hdr = ctk.CTkFrame(col_card, fg_color=soft, corner_radius=0, height=44)
            col_hdr.grid(row=0, column=0, sticky="ew", padx=spacing("sm"), pady=spacing("sm"))
            col_hdr.grid_propagate(False)
            col_hdr.grid_columnconfigure(1, weight=1)
            ctk.CTkFrame(col_hdr, width=10, height=10, corner_radius=5, fg_color=color).grid(
                row=0, column=0, padx=(spacing("xs"), spacing("sm"))
            )
            ctk.CTkLabel(
                col_hdr, text=title, font=themed_font("body", "bold"), text_color=color
            ).grid(row=0, column=1, sticky="w")
            count_lbl = ctk.CTkLabel(
                col_hdr, text="0", font=themed_font("body", "bold"), text_color=color
            )
            count_lbl.grid(row=0, column=2, padx=(spacing("sm"), spacing("xs")))
            body = ctk.CTkScrollableFrame(
                col_card,
                fg_color="transparent",
                height=220,
                scrollbar_button_color=THEME["border_strong"],
                scrollbar_button_hover_color=THEME["text_muted"],
            )
            body.grid(row=1, column=0, sticky="nsew", padx=spacing("sm"), pady=(0, spacing("sm")))
            self.colunas_risco[key] = {
                "content": body,
                "count_lbl": count_lbl,
                "color": color,
                "soft": soft,
            }

    def populate_risks(self, risks: list):
        if not self.colunas_risco:
            return
        for col in self.colunas_risco.values():
            for w in col["content"].winfo_children():
                w.destroy()
            col["count_lbl"].configure(text="0")
        counts = {k: 0 for k in self.colunas_risco}
        if not risks:
            for key in self.colunas_risco:
                EmptyState(
                    self.colunas_risco[key]["content"],
                    icon=ICONS["mood_bad"],
                    title="Nenhum estudante",
                    subtitle="",
                ).pack(pady=4)
            return
        batch = WidgetBatchBuilder(parent=self, batch_size=20)
        for s in risks:
            nivel = s.get("level", "normal").lower()
            if nivel not in self.colunas_risco:
                nivel = "normal"
            counts[nivel] += 1
            batch.add(
                lambda s=s, n=nivel: self._criar_card_risco(
                    self.colunas_risco[n]["content"],
                    s,
                    self.colunas_risco[n]["color"],
                    self.colunas_risco[n]["soft"],
                )
            )
        batch.execute()
        for key, count in counts.items():
            self.colunas_risco[key]["count_lbl"].configure(text=str(count))
            if count == 0:
                EmptyState(
                    self.colunas_risco[key]["content"],
                    icon=ICONS["mood_bad"],
                    title="Nenhum estudante",
                    subtitle="",
                ).pack(pady=4)

    def _criar_card_risco(self, parent, student: dict, color: str, soft: str):
        nome = student.get("name", "Estudante")
        curso = student.get("course", "Geral")
        msg = student.get("msg", "Requer atenção")
        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        card.pack(fill="x", pady=SPACING["item_gap"])
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("lg"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)
        av = Avatar(inner, initials=nome[:2], size=34, color=get_avatar_color(nome))
        av.grid(row=0, column=0, rowspan=2, padx=(0, spacing("md")), sticky="ns")
        ctk.CTkLabel(
            inner, text=nome, font=themed_font("body", "bold"), text_color=THEME["text"], anchor="w"
        ).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            inner,
            text=curso,
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w")
        if msg:
            chip = ctk.CTkFrame(card, fg_color=soft, corner_radius=RADIUS["sm"])
            chip.pack(fill="x", padx=spacing("lg"), pady=(0, spacing("md")))
            ctk.CTkLabel(
                chip,
                text=msg,
                font=themed_font("caption", "bold"),
                text_color=color,
                wraplength=140,
                anchor="w",
            ).pack(padx=spacing("sm"), pady=spacing("xs"), anchor="w")

    def _criar_lista_checkins_ui(self, content):
        card = SectionCard(content, f"{ICONS['chart']} Check-ins Recentes")
        card.pack(fill="x", pady=(0, SPACING["section_gap"]))
        self._checkins_body = card.body

    def populate_checkins(self, checkins: list):
        if not hasattr(self, "_checkins_body") or self._checkins_body is None or not self._checkins_body.winfo_exists():
            return
        for w in self._checkins_body.winfo_children():
            w.destroy()
        if not isinstance(checkins, list):
            checkins = []
        if not checkins:
            EmptyState(
                self._checkins_body,
                icon=ICONS["chart"],
                title="Nenhum check-in registrado",
                subtitle="Os check-ins aparecerão aqui quando forem realizados",
            ).pack(pady=8)
            return
        batch = WidgetBatchBuilder(parent=self, batch_size=20)
        for c in checkins:
            if not isinstance(c, dict):
                continue
            batch.add(lambda c=c: self._criar_row_checkin(c))
        batch.execute()

    def _criar_row_checkin(self, c: dict):
        nome = c.get("student_name", "Estudante")
        mood = c.get("mood_score") or c.get("mood") or 3
        mood = max(1, min(5, int(mood)))
        texto = c.get("mood_text") or _MOOD_LABEL.get(mood, "Neutro")
        data = c.get("date", "Hoje")
        curso = c.get("course", "")
        color = _MOOD_COLOR.get(mood, THEME["text_muted"])
        emoji = mood_emoji_from_score(mood)
        row = ctk.CTkFrame(
            self._checkins_body, fg_color=THEME["bg_alt"], corner_radius=RADIUS["lg"]
        )
        row.pack(fill="x", pady=SPACING["item_gap"])
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=spacing("lg"), pady=spacing("md"))
        inner.grid_columnconfigure(1, weight=1)
        av = Avatar(inner, initials=nome[:2], size=38, color=get_avatar_color(nome))
        av.grid(row=0, column=0, rowspan=2, padx=(0, spacing("md")), sticky="ns")
        ctk.CTkLabel(
            inner, text=nome, font=themed_font("body", "bold"), text_color=THEME["text"], anchor="w"
        ).grid(row=0, column=1, sticky="w")
        if curso:
            ctk.CTkLabel(
                inner,
                text=curso,
                font=themed_font("caption"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).grid(row=1, column=1, sticky="w")
        mood_frame = ctk.CTkFrame(inner, fg_color="transparent")
        mood_frame.grid(row=0, column=2, rowspan=2, padx=(spacing("md"), 0), sticky="e")
        chip_bg = ctk.CTkFrame(
            mood_frame, fg_color=blend_color(color, 0.15), corner_radius=RADIUS["button"]
        )
        chip_bg.pack(anchor="e")
        ctk.CTkLabel(
            chip_bg, text=f"{emoji}  {texto}", font=themed_font("body", "bold"), text_color=color
        ).pack(padx=spacing("sm"), pady=spacing("xs"))
        ctk.CTkLabel(
            mood_frame, text=data, font=themed_font("caption"), text_color=THEME["text_muted"]
        ).pack(anchor="e", pady=(spacing("xs"), 0))

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
            modal,
            text=mensagem,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
            wraplength=360,
            justify="center",
        ).pack(pady=(24, 16))
        botoes = ctk.CTkFrame(modal, fg_color="transparent")
        botoes.pack(pady=(0, 20))
        ctk.CTkButton(
            botoes,
            text="Cancelar",
            width=110,
            height=36,
            fg_color=THEME["bg_alt"],
            hover_color=THEME["border"],
            text_color=THEME["text"],
            command=lambda: modal.destroy(),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            botoes,
            text="Confirmar",
            width=110,
            height=36,
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color=THEME["text_on_primary"],
            command=lambda: self._confirmar_callback(modal, resultado),
        ).pack(side="right")
        modal.wait_window(modal)
        return resultado.get("ok", False)

    def _confirmar_callback(self, modal: ctk.CTkToplevel, resultado: dict) -> None:
        resultado["ok"] = True
        modal.destroy()
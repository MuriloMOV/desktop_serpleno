import logging
import customtkinter as ctk
from utils.async_runner import AsyncRunner

from ui_theme import (
    THEME, SPACING, RADIUS, ELEVATION, TYPO, ANIMATION, FONT_FAMILY,
    font, themed_font, mono_font, blend_color, darken, lighten, shift_hue,
)
from ui_theme_extensions import extend_theme
from components.ui_components import (
    Card, PrimaryButton, DangerButton, GhostButton, Avatar,
    Badge, Pill, EmptyState, Toast, Tabs, Divider, KPICard, ClickableFrame, bind_clickable
)
from services.bem_estar import ServicoBemEstar
from utils.avatar_utils import get_avatar_color
from utils.mood import mood_emoji_from_score

logger = logging.getLogger(__name__)

BE_TOKENS = extend_theme(THEME, {
    "kpi_size": "md",
})




# Avatar cores por inicial — agora via utils.avatar_utils.get_avatar_color.
# _AV_COLORS e _av_color legados removidos; use utils.avatar_utils.get_avatar_color.


# Configuração das colunas de risco
_RISK_COLS = [
    ("Crítico",  THEME["critico"],    THEME["critico_soft"], "critico"),
    ("Alto",     THEME["alto"],       THEME["alto_soft"],    "alto"),
    ("Médio",    THEME["medio"],      THEME["medio_soft"],   "medio"),
    ("Normal",   THEME["normal"],     THEME["normal_soft"],  "normal"),
]

# Emojis e labels por nível de humor (1–5) — agora via utils.mood.
_MOOD_COLOR = {
    1: THEME["danger"], 2: THEME["alto"], 3: THEME["medio"],
    4: THEME["success"], 5: THEME["primary"],
}
_MOOD_LABEL = {1: "Muito triste", 2: "Triste", 3: "Neutro", 4: "Bem", 5: "Ótimo"}


# Helpers


def _card(parent, **kw) -> ctk.CTkFrame:
    return ctk.CTkFrame(
        parent,
        fg_color=THEME["surface"],
        corner_radius=RADIUS["card"],
        border_width=1,
        border_color=THEME["border"],
        **kw,
    )


def _section_card(parent, title: str,
                  action_text: str = "", action_cmd=None) -> ctk.CTkFrame:
    """Card de seção com cabeçalho, divider e body."""
    outer = _card(parent)

    hdr = ctk.CTkFrame(outer, fg_color="transparent")
    hdr.pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["section_gap"], 0))

    ctk.CTkLabel(
        hdr, text=title,
        font=themed_font("body", "bold"),
        text_color=THEME["text"],
    ).pack(side="left")

    if action_text and action_cmd:
        GhostButton(
            hdr, text=action_text, command=action_cmd,
            height=28, corner_radius=RADIUS["button"],
            text_color=THEME["primary"],
        ).pack(side="right")

    Divider(outer).pack(fill="x", padx=SPACING["card_pad"], pady=(SPACING["item_gap"], 0))

    body = ctk.CTkFrame(outer, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=(SPACING["label_gap"], SPACING["section_gap"]))
    outer.body = body
    return outer


def _avatar(parent, initials: str, color: str, size: int = 36) -> ctk.CTkFrame:
    av = ctk.CTkFrame(parent, width=size, height=size,
                      corner_radius=size // 2, fg_color=color)
    av.pack_propagate(False)
    ctk.CTkLabel(
        av, text=initials[:2].upper(),
        font=themed_font("body", "bold"),
        text_color="#FFFFFF",
    ).place(relx=0.5, rely=0.5, anchor="center")
    return av


# ══════════════════════════════════════════════════════════════════════════════
#  BemEstarFrame
# ══════════════════════════════════════════════════════════════════════════════
class BemEstarFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(
            parent,
            fg_color=THEME["bg"],
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.controller        = controller
        self.servico_bem_estar = ServicoBemEstar()
        self.colunas_risco: dict = {}
        self._chart_data: list  = []

        self._criar_kpis()
        self._criar_secao_grafico()
        self._criar_visao_risco()
        self._criar_lista_checkins()

        self.load_data()

    # ══════════════════════════════════════
    #  Dados
    # ══════════════════════════════════════
    def load_data(self):
        self._set_status_carregando()

        def fetch():
            dash     = self.servico_bem_estar.obter_dashboard()
            checkins = self.servico_bem_estar.listar_checkins()
            risks    = self.servico_bem_estar.listar_estudantes_risco()
            return dash, checkins, risks

        def on_success(result):
            dash, checkins, risks = result
            self.update_ui(dash, checkins, risks)

        def on_error(exc):
            import tkinter.messagebox as mb
            mb.showerror("Erro de conexão", f"Não foi possível carregar os dados de bem-estar.\n{exc}")
            self._set_status_erro()

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            on_complete=lambda: None,  # mantém status carregando até sucesso/erro
            widget_ref=self,
        )

    # ══════════════════════════════════════
    #  STATUS HELPERS
    # ══════════════════════════════════════
    def _set_status_carregando(self):
        try:
            self._kpi_humor.set_value("...")
            self._kpi_part.set_value("...")
            self._kpi_crit.set_value("...")
        except Exception:
            pass

    def _set_status_erro(self):
        try:
            self._kpi_humor.set_value("—")
            self._kpi_part.set_value("—")
            self._kpi_crit.set_value("—")
        except Exception:
            pass

    def update_ui(self, dash_res, checkins_res, risks_res):
        if dash_res.get("success"):
            self.update_metrics(dash_res.get("data", {}))
        else:
            logger.warning("Dashboard retornou erro: %s", dash_res)

        if checkins_res.get("success"):
            data     = checkins_res.get("data", {})
            checkins = data.get("checkins") if isinstance(data, dict) else []
            self.populate_checkins(checkins or [])
        else:
            logger.warning("Check-ins retornaram erro: %s", checkins_res)

        if risks_res.get("success"):
            data   = risks_res.get("data", {})
            groups = data.get("groups", {})
            mapping = {"critical": "critico", "high": "alto",
                       "medium": "medio",   "low": "normal"}
            flat = []
            for bk, ui in mapping.items():
                for s in groups.get(bk, []):
                    s["level"] = ui
                    s["msg"]   = ", ".join(s.get("reasons", [])) or "Requer atenção"
                    flat.append(s)
            self.populate_risks(flat)
        else:
            logger.warning("Risco retornou erro: %s", risks_res)

    def update_metrics(self, data):
        summary = data.get("summary", {})
        humor   = summary.get("avg_mood")
        if humor and hasattr(self, "_kpi_humor"):
            emoji = mood_emoji_from_score(round(humor))
            self._kpi_humor.set_value(f"{emoji}  {humor:.1f}")
        part = summary.get("participation_rate")
        if part and hasattr(self, "_kpi_part"):
            self._kpi_part.set_value(f"{part:.0f}%")
        crit = summary.get("critical_count")
        if crit is not None and hasattr(self, "_kpi_crit"):
            self._kpi_crit.set_value(str(crit))

        history = data.get("history") or data.get("mood_history") or []
        if history:
            self._chart_data = history
            self._draw_chart()

    # ══════════════════════════════════════
    #  CABEÇALHO
    # ══════════════════════════════════════
    def _criar_cabecalho(self):
        raise NotImplementedError

    # ══════════════════════════════════════
    #  KPI CARDS
    # ══════════════════════════════════════
    def _criar_kpis(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))

        kpis = [
            ("Humor Médio",       "😊  —",  "💚", THEME["kpi_blue"],  THEME["kpi_blue_soft"],  "_kpi_humor",
             "Média dos últimos 7 dias"),
            ("Participação",      "—%",    "📈", THEME["kpi_pink"],  THEME["kpi_pink_soft"],  "_kpi_part",
             "Taxa de check-ins"),
            ("Alertas Críticos",  "—",     "🚨", THEME["kpi_red"],   THEME["kpi_red_soft"],   "_kpi_crit",
             "Estudantes em situação crítica"),
        ]

        for i, (title, initial, icon, accent, soft, attr, sub) in enumerate(kpis):
            row.grid_columnconfigure(i, weight=1)
            card = KPICard(
                row, title=title, value=initial, icon=icon,
                accent=accent, unit="", size=BE_TOKENS.get("kpi_size", "md"),
            )
            card.grid(row=0, column=i, sticky="ew", padx=SPACING["grid_gap"] // 2)
            setattr(self, attr, card)

    # ══════════════════════════════════════
    #  GRÁFICO DE TENDÊNCIA
    # ══════════════════════════════════════
    def _criar_secao_grafico(self):
        outer = _section_card(self, "📈  Tendência de Bem-Estar — últimos 30 dias")
        outer.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 0))
        self._secao_grafico_outer = outer

        # Canvas
        self.canvas_30d = ctk.CTkCanvas(
            outer.body, bg=THEME["surface"],
            height=200, highlightthickness=0,
        )
        self.canvas_30d.pack(fill="both", expand=True, padx=4, pady=(4, 12))
        self._chart_after_id = None
        outer.body.bind("<Configure>", self._schedule_draw_chart)

        # Barras de distribuição de humor (criadas uma única vez)
        dist_row = ctk.CTkFrame(outer.body, fg_color="transparent")
        dist_row.pack(fill="x", pady=(4, 4))

        self._dist_bars: dict[str, ctk.CTkFrame] = {}
        self._dist_pcts: dict[str, ctk.CTkLabel] = {}

        for label, color, pct_key, default in [
            ("😊  Bom",     THEME["success"], "bom",  65),
            ("😐  Neutro",  THEME["warning"], "med",  25),
            ("😢  Baixo",   THEME["danger"],  "mau",  10),
        ]:
            col = ctk.CTkFrame(dist_row, fg_color="transparent")
            col.pack(side="left", expand=True, padx=SPACING["grid_gap"])

            ctk.CTkLabel(col, text=label,
                         font=themed_font("body", "bold"),
                         text_color=THEME["text_secondary"]).pack(anchor="w")

            bar_bg = ctk.CTkFrame(col, height=8, fg_color=THEME["chart_grid"],
                                  corner_radius=RADIUS["pill"])
            bar_bg.pack(fill="x", pady=(5, 4))
            bar_bg.pack_propagate(False)

            fill = ctk.CTkFrame(bar_bg, height=8, fg_color=color, corner_radius=RADIUS["pill"])
            fill.pack(side="left", fill="y")
            self._dist_bars[pct_key] = fill

            pct_lbl = ctk.CTkLabel(col, text=f"{default}%",
                                   font=themed_font("body", "bold"),
                                   text_color=THEME["text"])
            pct_lbl.pack(anchor="w")
            self._dist_pcts[pct_key] = pct_lbl

    def _schedule_draw_chart(self, event=None):
        if self._chart_after_id:
            self.after_cancel(self._chart_after_id)
        self._chart_after_id = self.after(80, lambda: self._draw_chart())

    def _draw_chart(self, data=None):
        if data:
            self._chart_data = data

        self.canvas_30d.delete("all")
        cw = self.canvas_30d.winfo_width()
        ch = self.canvas_30d.winfo_height()
        if cw < 80 or ch < 60:
            return

        pts  = ([d.get("avg_mood") or d.get("media_humor", 3.0)
                  for d in self._chart_data]
                if self._chart_data
                else [3.5, 3.2, 3.8, 3.4, 3.1, 3.0, 3.6, 3.9,
                      4.2, 4.0, 3.8, 4.1, 4.3, 4.2, 4.5])

        mx, my = 40, 20
        cw2    = cw - 2 * mx
        ch2    = ch - 2 * my
        n      = len(pts)

        # Grades + labels Y
        for i in range(6):
            v  = 1 + i
            gy = (ch - my) - (i * ch2 / 5)
            self.canvas_30d.create_line(mx, gy, cw - mx, gy,
                                        fill=THEME["chart_grid"], dash=(3, 5))
            self.canvas_30d.create_text(mx - 6, gy, text=str(v),
                                        font=(FONT_FAMILY, 8),
                                        fill=THEME["text_muted"], anchor="e")

        # Coordenadas
        coords = [
            (mx + i * cw2 / max(n - 1, 1),
             (ch - my) - ((v - 1) * ch2 / 4))
            for i, v in enumerate(pts)
        ]

        # Área preenchida
        poly = []
        for x, y in coords:
            poly += [x, y]
        poly += [coords[-1][0], ch - my, coords[0][0], ch - my]
        self.canvas_30d.create_polygon(poly, fill=THEME["chart_fill"], outline="")

        # Linha
        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            self.canvas_30d.create_line(
                x1, y1, x2, y2,
                fill=THEME["chart_line"], width=2.5,
                capstyle="round", joinstyle="round",
            )

        # Pontos coloridos
        for i, (x, y) in enumerate(coords):
            v     = pts[i]
            dot_c = (THEME["dot_bad"] if v < 2.5 else
                     THEME["dot_mid"] if v < 3.5 else THEME["dot_good"])
            self.canvas_30d.create_oval(
                x - 4, y - 4, x + 4, y + 4,
                fill=dot_c, outline="#FFFFFF", width=2,
            )

        # Labels X (a cada 4 pontos)
        step = max(1, n // 7)
        for i, (x, _) in enumerate(coords):
            if i % step == 0 and self._chart_data:
                raw = self._chart_data[i]
                lbl = raw.get("data") or raw.get("date") or ""
                if len(lbl) > 5:
                    lbl = lbl[5:]   # só MM-DD
                self.canvas_30d.create_text(
                    x, ch - 6, text=lbl,
                    font=(FONT_FAMILY, 8), fill=THEME["text_secondary"],
                )

    # ══════════════════════════════════════
    #  VISÃO DE RISCO (kanban 4 colunas)
    # ══════════════════════════════════════
    def _criar_visao_risco(self):
        # Título externo ao card
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], 10))

        ctk.CTkLabel(
            title_row, text="🛡  Visão de Risco dos Estudantes",
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        ctk.CTkLabel(
            title_row, text="Classificação por nível de atenção necessária",
            font=themed_font("body_sm"),
            text_color=THEME["text_secondary"],
        ).pack(side="left", padx=(10, 0), pady=(2, 0))

        # Grid de colunas
        cols_wrap = ctk.CTkFrame(self, fg_color="transparent")
        cols_wrap.pack(fill="x", padx=SPACING["page_x"])
        for i in range(4):
            cols_wrap.grid_columnconfigure(i, weight=1)

        self.colunas_risco = {}

        for i, (title, color, soft, key) in enumerate(_RISK_COLS):
            col_card = _card(cols_wrap)
            col_card.grid(row=0, column=i, sticky="nsew", padx=SPACING["grid_gap"] // 2)

            # Cabeçalho da coluna
            col_hdr = ctk.CTkFrame(
                col_card, fg_color=soft,
                corner_radius=0, height=44,
            )
            col_hdr.pack(fill="x")
            col_hdr.pack_propagate(False)
            col_hdr.grid_columnconfigure(1, weight=1)

            # Ponto colorido
            ctk.CTkFrame(
                col_hdr, width=10, height=10,
                corner_radius=5, fg_color=color,
            ).grid(row=0, column=0, padx=(14, 8))

            ctk.CTkLabel(
                col_hdr, text=title,
                font=themed_font("body", "bold"),
                text_color=color,
            ).grid(row=0, column=1, sticky="w")

            count_lbl = ctk.CTkLabel(
                col_hdr, text="0",
                font=themed_font("body", "bold"),
                text_color=color,
            )
            count_lbl.grid(row=0, column=2, padx=(0, 14))

            # Corpo scrollável
            body = ctk.CTkScrollableFrame(
                col_card, fg_color="transparent",
                height=220,
                scrollbar_button_color=THEME["border_strong"],
                scrollbar_button_hover_color=THEME["text_muted"],
            )
            body.pack(fill="both", expand=True, padx=8, pady=8)

            self.colunas_risco[key] = {
                "content": body,
                "count_lbl": count_lbl,
                "color": color,
                "soft": soft,
            }

    def populate_risks(self, risks: list):
        for col in self.colunas_risco.values():
            for w in col["content"].winfo_children():
                w.destroy()
            col["count_lbl"].configure(text="0")

        counts = {k: 0 for k in self.colunas_risco}

        if not risks:
            for key in self.colunas_risco:
                EmptyState(
                    self.colunas_risco[key]["content"], icon="😕",
                    title="Nenhum estudante", subtitle=""
                ).pack(pady=12)
            return

        for s in risks:
            nivel = s.get("level", "normal").lower()
            if nivel not in self.colunas_risco:
                nivel = "normal"
            counts[nivel] += 1
            self._criar_card_risco(
                self.colunas_risco[nivel]["content"], s,
                self.colunas_risco[nivel]["color"],
                self.colunas_risco[nivel]["soft"],
            )

        for key, count in counts.items():
            self.colunas_risco[key]["count_lbl"].configure(text=str(count))
            if count == 0:
                EmptyState(
                    self.colunas_risco[key]["content"], icon="😕",
                    title="Nenhum estudante", subtitle=""
                ).pack(pady=12)

    def _criar_card_risco(self, parent, student: dict,
                          color: str, soft: str):
        nome  = student.get("name", "Estudante")
        curso = student.get("course", "Geral")
        msg   = student.get("msg", "Requer atenção")

        card = ctk.CTkFrame(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        card.pack(fill="x", pady=SPACING["item_gap"] // 2)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)
        inner.grid_columnconfigure(1, weight=1)

        # Avatar colorido
        av = _avatar(inner, nome[:2], get_avatar_color(nome), 34)
        av.grid(row=0, column=0, rowspan=2, padx=(0, 8), sticky="ns")

        ctk.CTkLabel(
            inner, text=nome,
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner, text=curso,
            font=themed_font("caption"),
            text_color=THEME["text_secondary"], anchor="w",
        ).grid(row=1, column=1, sticky="w")

        # Chip de motivo
        if msg:
            chip = ctk.CTkFrame(card, fg_color=soft, corner_radius=RADIUS["sm"])
            chip.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkLabel(
                chip, text=msg,
                font=themed_font("caption", "bold"),
                text_color=color, wraplength=140, anchor="w",
            ).pack(padx=8, pady=4, anchor="w")

    # Alias legado
    def criar_card_estudante_risco(self, parent, student, color):
        soft = {
            THEME["critico"]: THEME["critico_soft"], THEME["alto"]: THEME["alto_soft"],
            THEME["medio"]:   THEME["medio_soft"],   THEME["normal"]: THEME["normal_soft"],
        }.get(color, THEME["primary_soft"])
        self._criar_card_risco(parent, student, color, soft)

    # ══════════════════════════════════════
    #  LISTA DE CHECK-INS
    # ══════════════════════════════════════
    def _criar_lista_checkins(self):
        outer = _section_card(self, "📝  Check-ins Recentes")
        outer.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], SPACING["page_y"]))
        self._checkins_body = outer.body

    def populate_checkins(self, checkins: list):
        if not hasattr(self, "_checkins_body"):
            return
        for w in self._checkins_body.winfo_children():
            w.destroy()

        if not isinstance(checkins, list):
            checkins = []

        if not checkins:
            EmptyState(
                self._checkins_body, icon="📝",
                title="Nenhum check-in registrado",
                subtitle="Os check-ins aparecerão aqui quando forem realizados",
            ).pack(pady=20)
            return

        for c in checkins:
            if not isinstance(c, dict):
                continue
            self._criar_row_checkin(c)

    def _criar_row_checkin(self, c: dict):
        nome  = c.get("student_name", "Estudante")
        mood  = c.get("mood_score") or c.get("mood") or 3
        mood  = max(1, min(5, int(mood)))
        texto = c.get("mood_text") or _MOOD_LABEL.get(mood, "Neutro")
        data  = c.get("date", "Hoje")
        curso = c.get("course", "")

        color = _MOOD_COLOR.get(mood, THEME["text_muted"])
        emoji = mood_emoji_from_score(mood)

        row = ctk.CTkFrame(
            self._checkins_body,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=SPACING["item_gap"] // 2)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=8)
        inner.grid_columnconfigure(1, weight=1)

        # Avatar
        av = _avatar(inner, nome[:2], get_avatar_color(nome), 38)
        av.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="ns")

        # Nome + curso
        ctk.CTkLabel(
            inner, text=nome,
            font=themed_font("body", "bold"),
            text_color=THEME["text"], anchor="w",
        ).grid(row=0, column=1, sticky="w")

        if curso:
            ctk.CTkLabel(
                inner, text=curso,
                font=themed_font("caption"),
                text_color=THEME["text_secondary"], anchor="w",
            ).grid(row=1, column=1, sticky="w")

        # Mood chip
        mood_frame = ctk.CTkFrame(inner, fg_color="transparent")
        mood_frame.grid(row=0, column=2, rowspan=2, padx=(8, 0), sticky="e")

        chip_bg = ctk.CTkFrame(
            mood_frame,
            fg_color=blend_color(color, 0.15),
            corner_radius=RADIUS["button"],
        )
        chip_bg.pack(anchor="e")
        ctk.CTkLabel(
            chip_bg,
            text=f"{emoji}  {texto}",
            font=themed_font("body", "bold"),
            text_color=color,
        ).pack(padx=10, pady=5)

        # Data
        ctk.CTkLabel(
            mood_frame, text=data,
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
        ).pack(anchor="e", pady=(4, 0))

    # ══════════════════════════════════════
    #  Aliases legados
    # ══════════════════════════════════════
    def criar_cabecalho(self):
        pass

    def criar_cards_humor(self):
        pass

    def criar_analise_mensal(self):
        pass

    def draw_30day_chart(self, event=None):
        self._draw_chart()

    def criar_visao_risco(self):
        pass

    def criar_lista_checkins(self):
        pass


# ──────────────────────────────────────────────────────────────────────────────
#  Utilitário: pastel de cor
# ──────────────────────────────────────────────────────────────────────────────
def _soft_from_color(color: str) -> str:
    mapping = {
        THEME["danger"]:  THEME["danger_soft"],
        THEME["alto"]:    THEME["alto_soft"],
        THEME["medio"]:   THEME["medio_soft"],
        THEME["success"]: THEME["normal_soft"],
        THEME["primary"]: THEME["primary_soft"],
    }
    return mapping.get(color, THEME["primary_soft"])

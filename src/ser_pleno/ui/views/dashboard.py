import json
import logging
import os

import customtkinter as ctk

from ser_pleno.config.paths import get_project_root
from ser_pleno.features.analytics.service import ServicoAnalytics
from ser_pleno.features.dashboard.service import ServicoDashboard
from ser_pleno.ui.components.icons import ICONS, IconLabel
from ser_pleno.ui.components.ui_components import (
    AlertRow,
    BaseModal,
    Card,
    Divider,
    EmptyState,
    KPICard,
    ListRow,
    PrimaryButton,
    ProgressBar,
    bind_clickable,
)
from ser_pleno.ui.theme import FONT_FAMILY, RADIUS, SPACING, THEME, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms
from ser_pleno.utils.cache import NotificationCache
from ser_pleno.utils.widget_batch import WidgetBatchBuilder

logger = logging.getLogger(__name__)


class NotificationPanel(BaseModal):
    def __init__(
        self,
        parent,
        titulo: str,
        notificacoes: list,
        tipo: str,
        on_mark_read=None,
        on_mark_all_read=None,
    ):
        super().__init__(parent, title=titulo, width=520, height=480)
        self._parent_window = parent.winfo_toplevel()
        self.titulo = titulo
        self.notificacoes = notificacoes
        self.tipo = tipo
        self.on_mark_read = on_mark_read
        self.on_mark_all_read = on_mark_all_read
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        is_ajuda = self.tipo == "ajuda"
        accent = THEME["primary"] if is_ajuda else THEME["danger"]
        soft = THEME["primary_soft"] if is_ajuda else THEME["danger_soft"]
        icon_txt = ICONS["help"] if is_ajuda else ICONS["notification"]

        header = ctk.CTkFrame(self.scroll, fg_color=soft, corner_radius=0)
        header.pack(fill="x")

        hinner = ctk.CTkFrame(header, fg_color="transparent")
        hinner.pack(fill="x", padx=SPACING["page_x"], pady=14)

        ctk.CTkLabel(
            hinner,
            text=f"{icon_txt}  {self.title()}",
            font=themed_font("h4", "bold"),
            text_color=accent,
        ).pack(side="left")

        PrimaryButton(
            hinner,
            text="Marcar todas como lidas",
            command=self._mark_all_read,
            height=30,
            width=180,
            text_color="white",
        ).pack(side="right")

        lst = ctk.CTkScrollableFrame(self, fg_color="transparent")
        lst.pack(fill="both", padx=spacing("xxl"), pady=spacing("lg"))

        if not self.notificacoes:
            EmptyState(
                lst,
                icon=ICONS["empty"],
                title="Sem notificações",
                subtitle=f"Nenhuma notificação de {self.tipo} no momento",
            ).pack(pady=spacing("xl"))
        else:
            for notif in self.notificacoes:
                self._create_item(lst, notif, accent, soft, icon_txt)

    def _create_item(self, parent, notif, accent, soft, icon_txt):
        row = ctk.CTkFrame(
            parent,
            fg_color=soft,
            corner_radius=RADIUS["lg"],
        )
        row.pack(fill="x", pady=spacing("xs"))
        row.pack_propagate(True)

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="both", padx=spacing("md"), pady=spacing("sm"))
        inner.grid_columnconfigure(1, weight=1)

        icon_bg = ctk.CTkFrame(
            inner,
            width=34,
            height=34,
            corner_radius=RADIUS["button"],
            fg_color=accent,
        )
        icon_bg.grid(
            row=0, column=0, rowspan=2, padx=(0, spacing("md")), sticky="n", pady=(spacing("xs"), 0)
        )
        icon_bg.grid_propagate(False)
        ctk.CTkLabel(
            icon_bg,
            text=icon_txt,
            font=themed_font("body"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text=notif.get("titulo", ""),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            inner,
            text=notif.get("descricao", ""),
            font=themed_font("caption"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).grid(row=1, column=1, sticky="w")

        ctk.CTkLabel(
            inner,
            text=notif.get("data", ""),
            font=themed_font("caption"),
            text_color=THEME["text_muted"],
            anchor="e",
        ).grid(row=0, column=2, sticky="ne", padx=(spacing("sm"), 0))

        bind_clickable(
            row,
            lambda nid=notif["id"], t=self.tipo: self._on_click(nid, t),
        )

    def _on_click(self, notif_id, tipo):
        if self.on_mark_read:
            self.on_mark_read(notif_id, tipo)
        self.destroy()

    def _mark_all_read(self):
        if self.on_mark_all_read:
            self.on_mark_all_read(self.tipo)
        self.destroy()


class ProfileModal(BaseModal):
    def __init__(self, parent, user_data: dict, on_edit=None):
        super().__init__(parent, title="Meu Perfil", width=440, height=380)
        self._parent_window = parent.winfo_toplevel()
        self.user_data = user_data or {}
        self.on_edit = on_edit
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        initials = (
            (self.user_data.get("first_name", "") or "")[0:1]
            + (self.user_data.get("last_name", "") or "")[0:1]
        ).upper() or self.user_data.get("username", "?")[:2].upper()

        av = ctk.CTkFrame(
            self,
            width=64,
            height=64,
            corner_radius=32,
            fg_color=THEME["primary"],
        )
        av.pack(pady=(0, spacing("md")))
        av.pack_propagate(False)
        ctk.CTkLabel(
            av,
            text=initials,
            font=themed_font("h3", "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        body = ctk.CTkFrame(self.scroll, fg_color="transparent")
        body.pack(fill="both", padx=SPACING["page_x"], pady=(0, spacing("md")))

        nome = (
            f"{self.user_data.get('first_name', '')} {self.user_data.get('last_name', '')}"
        ).strip() or self.user_data.get("username", "Usuário")

        ctk.CTkLabel(
            body,
            text=nome,
            font=themed_font("h4", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            body,
            text=self.user_data.get("email", ""),
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(anchor="w", pady=(spacing("xs"), spacing("sm")))

        chip = ctk.CTkFrame(body, fg_color=THEME["primary_soft"], corner_radius=RADIUS["button"])
        chip.pack(anchor="w")
        ctk.CTkLabel(
            chip,
            text="Analista Escolar",
            font=themed_font("body", "bold"),
            text_color=THEME["primary"],
        ).pack(padx=spacing("sm"), pady=spacing("xs"))

        Divider(body).pack(fill="x", pady=spacing("md"))

        for label, value in [
            ("Usuário", self.user_data.get("username", "")),
            ("Função", "Analista Escolar"),
            ("Módulos", "Painel, Estudantes, Agenda, Bem-Estar"),
        ]:
            self._row(body, label, value)

        PrimaryButton(
            self,
            text="Editar Perfil",
            command=lambda: self.on_edit() if self.on_edit else None,
            height=38,
            corner_radius=RADIUS["button"],
            width=160,
        ).pack(pady=(spacing("xs"), spacing("xl")))

    def _row(self, parent, label, value):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=spacing("xs"))

        ctk.CTkLabel(
            row,
            text=label,
            width=90,
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=value,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).pack(side="left")


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        import time as _time

        self._t0 = _time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_dashboard = ServicoDashboard(
            auth_service=getattr(controller, "auth_service", None)
        )
        self.servico_analytics = ServicoAnalytics(
            auth_service=getattr(controller, "auth_service", None)
        )
        self._notification_cache = NotificationCache(ttl=60)
        self._responsive_after = None
        self._last_responsive_width = None

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=THEME["bg"],
            scrollbar_button_color=THEME["border_strong"],
            scrollbar_button_hover_color=THEME["text_muted"],
        )
        self.scroll.pack(fill="both", expand=True)

        self._criar_toolbar_acoes()
        self._criar_kpi_container()
        self._criar_grid_principal()
        self._carregar_dados()

        self.bind("<Configure>", self._on_configure)
        self.after(100, lambda: self._apply_responsive_layout())
        log_view_init_ms("dashboard", self._t0, widget_ref=self)

    def _on_configure(self, event):
        width = getattr(event, "width", self.winfo_width())
        if width <= 0:
            return
        if (
            self._last_responsive_width is not None
            and abs(width - self._last_responsive_width) < 20
        ):
            return
        self._last_responsive_width = width
        if self._responsive_after:
            try:
                self.after_cancel(self._responsive_after)
            except Exception:
                pass
        self._responsive_after = self.after(120, self._apply_responsive_layout)

    def _carregar_dados(self):
        self._mostrar_skeletons()
        self._carregar_quick_actions()

        def fetch():
            return self.servico_dashboard.obter_kpis()

        def on_success(data):
            self._atualizar_dashboard(data)
            self._carregar_dados_serpleno()

        def on_error(exc):
            self._show_error(f"Não foi possível carregar o dashboard.\n{exc}")

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _show_error(self, message: str, title: str = "Não foi possível concluir") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _carregar_dados_serpleno(self):
        def fetch():
            mood = self.servico_analytics.obter_mood_timeline()
            wellness = self.servico_analytics.obter_wellness_distribution()
            risk = self.servico_analytics.obter_risk_overview()
            engagement = self.servico_analytics.obter_engagement_stats()
            return mood, wellness, risk, engagement

        def on_success(result):
            mood, wellness, risk, engagement = result
            self._atualizar_secao_humor_serpleno(mood)
            self._atualizar_secao_bem_estar(wellness)
            self._atualizar_secao_risco(risk)
            self._atualizar_secao_engajamento(engagement)

        def on_error(exc):
            logger.debug("Dados SerPleno não disponíveis: %s", exc)

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _atualizar_dashboard(self, data):
        self._last_kpi_data = data
        self._render_kpis(data)
        self._atualizar_secao_agenda(data)
        self._atualizar_secao_alertas(data)
        self._atualizar_secao_atendimentos_recentes(data)
        self._atualizar_secao_bem_estar(data)
        self._atualizar_secao_humor(data)
        self.after(0, self._atualizar_badge_notificacoes)

    def _criar_toolbar_acoes(self):
        bar = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bar.pack(fill="x", padx=SPACING["page_x"], pady=(SPACING["page_y"], spacing("sm")))

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right")

        help_f = ctk.CTkFrame(
            right,
            width=40,
            height=40,
            corner_radius=RADIUS["button"],
            fg_color=THEME["primary_soft"],
        )
        help_f.pack(side="left", padx=spacing("xs"))
        help_f.pack_propagate(False)
        bind_clickable(help_f, self._abrir_notificacoes_ajuda)
        IconLabel(
            help_f,
            icon=ICONS["help"],
            size=20,
            fg_color="transparent",
            text_color=THEME["primary"],
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.help_badge = self._criar_badge(right)
        self.help_badge_anchor = help_f

        alert_f = ctk.CTkFrame(
            right,
            width=40,
            height=40,
            corner_radius=RADIUS["button"],
            fg_color=THEME["danger_soft"],
        )
        alert_f.pack(side="left", padx=spacing("xs"))
        alert_f.pack_propagate(False)
        bind_clickable(alert_f, self._abrir_notificacoes_alertas)
        IconLabel(
            alert_f,
            icon=ICONS["notification"],
            size=20,
            fg_color="transparent",
            text_color=THEME["danger"],
        ).place(relx=0.5, rely=0.5, anchor="center")
        self.alert_badge = self._criar_badge(right)
        self.alert_badge_anchor = alert_f

        name = ""
        if self.controller.usuario_logado:
            name = self.controller.usuario_logado.get("username", "?")[:2].upper()
        av_f = ctk.CTkFrame(
            right, width=40, height=40, corner_radius=RADIUS["button"], fg_color=THEME["primary"]
        )
        av_f.pack(side="left", padx=(spacing("md"), 0))
        av_f.pack_propagate(False)
        bind_clickable(av_f, self._abrir_perfil)
        ctk.CTkLabel(
            av_f,
            text=name,
            font=themed_font("body", "bold"),
            text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

    def _criar_quick_actions(self):
        self._quick_actions_card = Card(self.scroll, title="Ações Rápidas")
        self._quick_actions_card.pack(fill="x", padx=SPACING["page_x"], pady=(0, spacing("sm")))
        self._quick_actions_container = self._quick_actions_card.body
        self._quick_action_items = []
        self._quick_actions_data = []
        self._renderizar_quick_actions()

    def _carregar_quick_actions(self):
        def fetch():
            return self.servico_analytics.obter_quick_actions()

        def on_success(acoes):
            self._quick_actions_data = acoes if isinstance(acoes, list) else []
            self._renderizar_quick_actions()

        def on_error(exc):
            logger.debug("Quick actions não disponíveis: %s", exc)
            self._quick_actions_data = self._fallback_quick_actions()
            self._renderizar_quick_actions()

        AsyncRunner.run(
            task=fetch,
            on_success=on_success,
            on_error=on_error,
            widget_ref=self,
        )

    def _fallback_quick_actions(self):
        return [
            {
                "id": "nova_triagem",
                "label": "Nova Triagem",
                "icon": ICONS["add"],
                "description": "Iniciar triagem de estudante",
                "action_type": "navigate",
                "target": "analise",
            },
            {
                "id": "check_in",
                "label": "Registrar Check-in",
                "icon": ICONS["heart"],
                "description": "Registrar check-in de bem-estar",
                "action_type": "navigate",
                "target": "bem_estar",
            },
            {
                "id": "add_student",
                "label": "Adicionar Estudante",
                "icon": ICONS["add"],
                "description": "Cadastrar novo estudante",
                "action_type": "navigate",
                "target": "estudantes",
            },
            {
                "id": "criar_orientacao",
                "label": "Criar Orientação",
                "icon": ICONS["compass"],
                "description": "Nova orientação para encaminhamento",
                "action_type": "navigate",
                "target": "orientacoes",
            },
        ]

    def _renderizar_quick_actions(self):
        if not hasattr(self, "_quick_actions_container"):
            return
        for item in self._quick_action_items:
            if item.winfo_exists():
                item.destroy()
        self._quick_action_items = []

        acoes = self._quick_actions_data or self._fallback_quick_actions()
        favoritos = self._carregar_favoritos()

        if favoritos:
            acoes_filtradas = [a for a in acoes if a.get("id") in favoritos]
            if not acoes_filtradas:
                acoes_filtradas = acoes[:4]
        else:
            acoes_filtradas = acoes[:4]

        for acao in acoes_filtradas:
            self._criar_item_quick_action(acao)

    def _criar_item_quick_action(self, acao):
        item = ctk.CTkFrame(
            self._quick_actions_container,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["lg"],
        )
        item.pack(fill="x", pady=spacing("xs"))

        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", padx=spacing("md"), pady=spacing("sm"))
        inner.grid_columnconfigure(1, weight=1)

        icon_lbl = ctk.CTkLabel(
            inner,
            text=acao.get("icon", "•"),
            font=themed_font("h4"),
            text_color=THEME["primary"],
        )
        icon_lbl.grid(row=0, column=0, padx=(0, spacing("md")), sticky="w")

        text_frame = ctk.CTkFrame(inner, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(
            text_frame,
            text=acao.get("label", ""),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).pack(anchor="w")

        descricao = acao.get("description", "")
        if descricao:
            ctk.CTkLabel(
                text_frame,
                text=descricao,
                font=themed_font("caption"),
                text_color=THEME["text_secondary"],
                anchor="w",
            ).pack(anchor="w")

        fav_id = acao.get("id", "")
        is_fav = fav_id in self._carregar_favoritos()
        star_text = "★" if is_fav else "☆"
        star_color = THEME["warning"] if is_fav else THEME["text_muted"]

        star_btn = ctk.CTkButton(
            inner,
            text=star_text,
            width=32,
            height=32,
            corner_radius=RADIUS["button"],
            fg_color="transparent",
            hover_color=THEME["bg_alt"],
            text_color=star_color,
            command=lambda aid=fav_id: self._toggle_favorito(aid),
        )
        star_btn.grid(row=0, column=2, padx=(spacing("sm"), 0), sticky="e")

        bind_clickable(item, lambda a=acao: self._executar_quick_action(a))
        self._quick_action_items.append(item)

    def _executar_quick_action(self, acao):
        target = acao.get("target")
        if target:
            try:
                self.controller.app.mostrar_tela(target)
            except Exception as e:
                self._show_error(f"Não foi possível abrir {acao.get('label', '')}.\n{e}")

    def _toggle_favorito(self, acao_id):
        favoritos = self._carregar_favoritos()
        if acao_id in favoritos:
            favoritos.discard(acao_id)
        else:
            favoritos.add(acao_id)
        self._salvar_favoritos(favoritos)
        self._renderizar_quick_actions()

    def _carregar_favoritos(self):
        try:
            path = os.path.join(get_project_root(), "user_profile.json")
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.get("quick_action_favorites", []))
        except Exception:
            pass
        return set()

    def _salvar_favoritos(self, favoritos_set):
        try:
            path = os.path.join(get_project_root(), "user_profile.json")
            data = {}
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
            data["quick_action_favorites"] = list(favoritos_set)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Erro ao salvar favoritos: %s", e)

    def _reflow_quick_actions(self, width):
        if not hasattr(self, "_quick_action_buttons"):
            return
        for btn in self._quick_action_buttons:
            btn.pack_forget()
        if width >= 900:
            for btn in self._quick_action_buttons:
                btn.configure(width=180 if width >= 1400 else 160)
                btn.pack(side="left", padx=(0, spacing("sm")))
        else:
            for btn in self._quick_action_buttons:
                btn.configure(width=0)
                btn.pack(fill="x", pady=spacing("xs"))

    def _criar_badge(self, parent) -> ctk.CTkFrame:
        badge = ctk.CTkFrame(
            parent,
            corner_radius=9,
            fg_color=THEME["danger"],
        )
        ctk.CTkLabel(
            badge,
            text="0",
            font=themed_font("caption", "bold"),
            text_color="white",
        ).pack(padx=5, pady=1)
        return badge

    def _criar_kpi_container(self):
        self.kpi_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.kpi_frame.pack(
            fill="x", padx=SPACING["page_x"], pady=(SPACING["section_gap"], spacing("sm"))
        )
        self._kpi_cards = []
        self._kpi_cols = None

    def _kpi_cols_for_width(self, width):
        if width >= 1600:
            return 7
        if width >= 1300:
            return 4
        if width >= 900:
            return 3
        return 2

    def _mostrar_skeletons(self):
        width = self.winfo_width()
        cols = max(2, self._kpi_cols_for_width(width))
        self._limpar(self.kpi_frame)
        self._kpi_cards = []
        for i in range(7):
            row = i // cols
            col = i % cols
            self.kpi_frame.grid_columnconfigure(col, weight=1)
            EmptyState(
                self.kpi_frame,
                icon="",
                title="",
            ).grid(
                row=row, column=col, sticky="ew", padx=SPACING["grid_gap"] // 2, pady=spacing("xs")
            )

    def _render_kpis(self, data):
        width = self.winfo_width()
        cols = max(2, self._kpi_cols_for_width(width))

        media_humor = data.get("media_humor")
        humor_emoji = self._humor_emoji(media_humor)

        kpis = [
            (
                "Atendimentos Hoje",
                str(data.get("appointments_today", 0)),
                ICONS["users"],
                THEME["kpi_blue"],
                THEME["kpi_blue_soft"],
                "Atendimentos marcados",
            ),
            (
                "Vagas Disponíveis",
                str(data.get("available_slots", 0)),
                ICONS["calendar"],
                THEME["kpi_green"],
                THEME["kpi_green_soft"],
                "Horários livres",
            ),
            (
                "Alertas Ativos",
                str(data.get("alerts", 0)),
                ICONS["bell"],
                THEME["kpi_red"],
                THEME["kpi_red_soft"],
                "Requerem atenção",
            ),
            (
                "Estudantes em Atenção",
                str(len(data.get("attention_students", []))),
                ICONS["priority_high"],
                THEME["kpi_amber"],
                THEME["kpi_amber_soft"],
                "Requerem acompanhamento",
            ),
            (
                "Total de Estudantes",
                str(data.get("total_students", 0)),
                ICONS["group"],
                THEME["kpi_violet"],
                THEME["kpi_violet_soft"],
                "Alunos cadastrados",
            ),
            (
                "Triagens Pendentes",
                str(data.get("screenings_pending", 0)),
                ICONS["document"],
                THEME["kpi_pink"],
                THEME["kpi_pink_soft"],
                "Aguardando avaliação",
            ),
            (
                "Humor Médio",
                f"{media_humor:.1f}/5" if media_humor is not None else "—",
                humor_emoji,
                THEME["kpi_amber"],
                THEME["kpi_amber_soft"],
                "Média dos últimos 30 dias",
            ),
        ]

        if len(self._kpi_cards) != len(kpis) or self._kpi_cols != cols:
            self._limpar(self.kpi_frame)
            self._kpi_cards = []
            self._kpi_cols = cols
            for i in range(cols):
                self.kpi_frame.grid_columnconfigure(i, weight=1)

            for i, (title, value, icon, accent, soft, sub) in enumerate(kpis):
                row = i // cols
                col = i % cols
                card = KPICard(
                    self.kpi_frame,
                    title=title,
                    value=value,
                    icon=icon,
                    accent=accent,
                    trend="",
                    unit="",
                    size="wide",
                )
                card.grid(
                    row=row,
                    column=col,
                    sticky="ew",
                    padx=SPACING["grid_gap"] // 2,
                    pady=spacing("xs"),
                )
                self._kpi_cards.append(card)
        else:
            for card, (title, value, icon, accent, soft, sub) in zip(self._kpi_cards, kpis):
                card.set_value(value)

    def _criar_grid_principal(self):
        self._criar_quick_actions()

        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x", padx=SPACING["page_x"], pady=spacing("sm"))

        self.left_col = ctk.CTkFrame(grid, fg_color="transparent")
        self.right_col = ctk.CTkFrame(grid, fg_color="transparent")
        self._main_grid = grid

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        self._apply_column_layout(self.winfo_width() or 900)
        self._criar_card_chart()

    def _apply_column_layout(self, width):
        if not hasattr(self, "_main_grid") or not self._main_grid.winfo_exists():
            return
        width = width or self.winfo_width() or 900
        if width >= 900:
            self.left_col.pack_forget()
            self.right_col.pack_forget()

            self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["grid_gap"] // 2))
            self.right_col.grid(row=0, column=1, sticky="nsew", padx=(SPACING["grid_gap"] // 2, 0))
        else:
            self.left_col.grid_forget()
            self.right_col.grid_forget()

            self.left_col.pack(fill="x", anchor="n", pady=(0, spacing("md")))
            self.right_col.pack(fill="x", anchor="n", pady=(0, spacing("md")))

    def _apply_responsive_layout(self):
        width = self.winfo_width()
        if width <= 0:
            return
        self._apply_column_layout(width)
        self._reflow_quick_actions(width)
        self._resize_chart(width)
        if hasattr(self, "_last_kpi_data"):
            self._render_kpis(self._last_kpi_data)

    def _resize_chart(self, width):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        new_height = self._chart_height_for_width(width)
        self.canvas.configure(height=new_height)

    def _criar_card_chart(self):
        self.chart_card = Card(
            self.left_col, title=f"{ICONS['chart']}  Humor dos Estudantes — últimos 30 dias"
        )
        self.chart_card.pack(fill="x", pady=(0, spacing("md")))
        chart_body = self.chart_card.body

        self.canvas = ctk.CTkCanvas(
            chart_body,
            bg=THEME["surface"],
            height=320,
            highlightthickness=0,
        )
        self.canvas.pack(fill="x", padx=spacing("sm"), pady=(spacing("xs"), spacing("sm")))
        self.canvas.bind("<Configure>", self._schedule_draw_chart)
        self._chart_after_id = None
        self._pending_humor_history = None
        chart_body.bind("<Configure>", self._schedule_draw_chart)

        self._chart_empty = EmptyState(
            chart_body,
            icon=ICONS["chart"],
            title="Sem dados de humor",
            subtitle="Os registros aparecerão aqui quando houver entradas",
        )
        self._chart_empty.pack(fill="both", padx=spacing("xl"), pady=spacing("xl"))
        self._chart_empty.pack_forget()

    def _chart_height_for_width(self, width):
        if width >= 1400:
            return 400
        if width >= 1100:
            return 320
        if width >= 800:
            return 260
        return 220

    def _schedule_draw_chart(self, event=None):
        if self._chart_after_id:
            try:
                self.after_cancel(self._chart_after_id)
            except Exception:
                pass
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self._chart_after_id = self.after(80, lambda: self._draw_chart(self._pending_humor_history))

    def _atualizar_secao_agenda(self, data):
        if hasattr(self, "_agenda_card") and self._agenda_card.winfo_exists():
            self._agenda_card.destroy()
        card = Card(
            self.left_col,
            title=f"{ICONS['calendar']}  Próximos Atendimentos",
            padding=(spacing("sm"), spacing("xs")),
        )
        card.pack(fill="x", pady=(0, spacing("md")))
        self._agenda_card = card

        appointments = data.get("upcoming_appointments", [])
        if appointments:
            batch = WidgetBatchBuilder(parent=self, batch_size=20)
            for appt in appointments:
                batch.add(
                    lambda a=appt: ListRow(
                        card.body,
                        title=a.get("student_name", "?"),
                        subtitle=a.get("curso", ""),
                        color=THEME["primary"],
                        soft_color=THEME["primary_soft"],
                        trailing_badge=a.get("time", ""),
                        icon=ICONS["clock"],
                    ).pack(fill="x", pady=spacing("xs"))
                )
            batch.execute()
        else:
            EmptyState(
                card.body,
                icon=ICONS["calendar"],
                title="Nenhum atendimento próximo",
                subtitle="Não há agendamentos futuros",
            ).pack(pady=spacing("sm"))

    def _atualizar_secao_alertas(self, data):
        if hasattr(self, "_alert_card") and self._alert_card.winfo_exists():
            self._alert_card.destroy()
        card = Card(
            self.right_col,
            title=f"{ICONS['alert']}  Estudantes em Alerta",
            padding=(spacing("sm"), spacing("xs")),
        )
        card.pack(fill="x", pady=(0, spacing("md")))
        self._alert_card = card

        students = data.get("attention_students", [])
        if students:
            batch = WidgetBatchBuilder(parent=self, batch_size=20)
            for s in students:
                batch.add(lambda s=s: AlertRow(card.body, name=s.get("name", "?"), reason=s.get("attention_reason", ""), priority=s.get("priority_level", 0)).pack(fill="x", pady=spacing("xs")))
            batch.execute()
        else:
            EmptyState(
                card.body,
                icon=ICONS["cross"],
                title="Tudo sob controle",
                subtitle="Nenhum estudante em alerta",
            ).pack(pady=spacing("sm"))

    def _atualizar_secao_atendimentos_recentes(self, data):
        if hasattr(self, "_recent_card") and self._recent_card.winfo_exists():
            self._recent_card.destroy()
        card = Card(
            self.right_col,
            title=f"{ICONS['clock']}  Atendimentos Recentes",
            padding=(spacing("sm"), spacing("xs")),
        )
        card.pack(fill="x", pady=(0, spacing("md")))
        self._recent_card = card

        appointments = data.get("recent_appointments", [])
        if appointments:
            batch = WidgetBatchBuilder(parent=self, batch_size=20)
            for appt in appointments:
                batch.add(
                    lambda a=appt: ListRow(
                        card.body,
                        title=a.get("student_name", "?"),
                        subtitle=a.get("curso", ""),
                        color=THEME["success"],
                        soft_color=THEME["success_soft"],
                        trailing_badge=a.get("time", ""),
                        icon=ICONS["check"],
                    ).pack(fill="x", pady=spacing("xs"))
                )
            batch.execute()
        else:
            EmptyState(
                card.body,
                icon=ICONS["clock"],
                title="Sem atendimentos recentes",
                subtitle="Nenhum atendimento concluído ainda",
            ).pack(pady=spacing("sm"))

    def _atualizar_secao_humor(self, data):
        humor_history = data.get("humor_history", [])
        self._pending_humor_history = humor_history if humor_history else None
        self._schedule_draw_chart()

    def _atualizar_secao_humor_serpleno(self, mood_data):
        if not mood_data or not mood_data.get("success"):
            return
        data = mood_data.get("data", {})
        timeline = data.get("timeline", []) if isinstance(data, dict) else list(data)
        if not timeline:
            return
        history = [
            {
                "data": item.get("date", ""),
                "media_humor": item.get("average", 0),
            }
            for item in timeline
        ]
        self._pending_humor_history = history
        self._schedule_draw_chart()

    def _atualizar_secao_bem_estar(self, wellness_data=None):
        if hasattr(self, "_bem_estar_card") and self._bem_estar_card.winfo_exists():
            self._bem_estar_card.destroy()
        card = Card(self.left_col, title=f"{ICONS['heart']}  Bem-Estar por Dimensão")
        card.pack(fill="x", pady=(0, spacing("md")))
        self._bem_estar_card = card

        if wellness_data and wellness_data.get("success"):
            data = wellness_data.get("data", {})
            academico = data.get("academico", 0) / 100.0
            emocional = data.get("emocional", 0) / 100.0
            social = data.get("social", 0) / 100.0
        else:
            be = getattr(self, "_last_bem_estar_fallback", {})
            academico = be.get("academico", 0) / 5
            emocional = be.get("emocional", 0) / 5
            social = be.get("social", 0) / 5

        dims = [
            (f"{ICONS['document']} Acadêmico", academico, THEME["primary"], THEME["primary_soft"]),
            (f"{ICONS['chat']}  Emocional", emocional, "#EC4899", "#FCE7F3"),
            (f"{ICONS['group']}  Social", social, THEME["success"], THEME["success_soft"]),
        ]
        batch = WidgetBatchBuilder(parent=self, batch_size=10)
        for nome, val, color, soft in dims:
            batch.add(
                lambda n=nome, v=val, c=color, s=soft: ProgressBar(card.body, nome=n, valor=v, color=c, soft=s).pack(
                    fill="x", padx=spacing("xs"), pady=spacing("sm")
                )
            )
        batch.execute()

    def _atualizar_secao_risco(self, risk_data):
        if not risk_data or not risk_data.get("success"):
            return
        data = risk_data.get("data", {})
        groups = data.get("groups", {})
        counts = data.get("counts", {})

        if hasattr(self, "_risk_card") and self._risk_card.winfo_exists():
            self._risk_card.destroy()
        card = Card(self.right_col, title=f"{ICONS['priority_high']}  Visão de Risco")
        card.pack(fill="x", pady=(0, spacing("md")))
        self._risk_card = card

        risk_configs = [
            ("critical", "Crítico", THEME["danger"], THEME["danger_soft"]),
            ("high", "Alto", THEME["warning"], THEME["warning_soft"]),
            ("medium", "Médio", THEME["kpi_amber"], THEME["kpi_amber_soft"]),
            ("low", "Normal", THEME["success"], THEME["success_soft"]),
        ]
        card_width = max(300, card.winfo_width() or self.winfo_width() or 900)
        cols = 4 if card_width >= 600 else 2
        grid = ctk.CTkFrame(card.body, fg_color="transparent")
        grid.pack(fill="x", pady=spacing("sm"))
        for i in range(cols):
            grid.grid_columnconfigure(i, weight=1)

        for idx, (level, label, color, soft) in enumerate(risk_configs):
            row = idx // cols
            col = idx % cols
            count = counts.get(level, 0)
            students = groups.get(level, [])
            chip_container = ctk.CTkFrame(grid, fg_color="transparent")
            chip_container.grid(row=row, column=col, sticky="ew", padx=SPACING["grid_gap"] // 2)

            chip = ctk.CTkFrame(chip_container, fg_color=soft, corner_radius=RADIUS["pill"])
            chip.pack(anchor="center")
            ctk.CTkLabel(
                chip,
                text=f"{label}: {count}",
                font=themed_font("caption", "bold"),
                text_color=color,
            ).pack(padx=spacing("sm"), pady=spacing("xs"))

            if students:
                for s in students[:5]:
                    self._criar_risk_student_row(chip_container, s, color)

    def _criar_risk_student_row(self, parent, student: dict, color: str):
        row = ctk.CTkFrame(parent, fg_color=THEME["bg_alt"], corner_radius=RADIUS["md"])
        row.pack(fill="x", pady=spacing("xs"))
        ctk.CTkLabel(
            row,
            text=student.get("name", "?"),
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
            anchor="w",
        ).pack(side="left", padx=spacing("sm"), pady=spacing("xs"))
        if student.get("reasons"):
            ctk.CTkLabel(
                row,
                text=student["reasons"][0],
                font=themed_font("caption"),
                text_color=color,
                anchor="w",
            ).pack(side="right", padx=spacing("sm"), pady=spacing("xs"))

    def _atualizar_secao_engajamento(self, engagement_data):
        if not engagement_data or not engagement_data.get("success"):
            return
        data = engagement_data.get("data", {})

        if hasattr(self, "_engagement_card") and self._engagement_card.winfo_exists():
            self._engagement_card.destroy()
        card = Card(self.right_col, title=f"{ICONS['group']}  Engajamento SerPleno")
        card.pack(fill="x", pady=(0, spacing("md")))
        self._engagement_card = card

        stats = [
            ("Alunos Ativos", str(data.get("alunos_ativos", 0)), THEME["primary"]),
            ("Registros de Humor", str(data.get("registros_humor", 0)), THEME["kpi_amber"]),
            ("Autoavaliações", str(data.get("autoavaliacoes", 0)), THEME["success"]),
            ("Check-ins", str(data.get("check_ins", 0)), THEME["kpi_violet"]),
        ]
        card_width = max(300, card.winfo_width() or self.winfo_width() or 900)
        cols = 4 if card_width >= 600 else 2
        rows = 1 if cols == 4 else 2
        grid = ctk.CTkFrame(card.body, fg_color="transparent")
        grid.pack(fill="x", pady=spacing("sm"))
        for i in range(cols):
            grid.grid_columnconfigure(i, weight=1)
        for i in range(rows):
            grid.grid_rowconfigure(i, weight=1)

        for idx, (label, value, accent) in enumerate(stats):
            row = idx // cols
            col = idx % cols
            frame = ctk.CTkFrame(grid, fg_color=THEME["bg_alt"], corner_radius=RADIUS["lg"])
            frame.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=SPACING["grid_gap"] // 2,
                pady=spacing("xs"),
            )
            ctk.CTkLabel(
                frame,
                text=value,
                font=themed_font("h2", "bold"),
                text_color=accent,
            ).pack(pady=(spacing("sm"), 0))
            ctk.CTkLabel(
                frame,
                text=label,
                font=themed_font("caption"),
                text_color=THEME["text_secondary"],
            ).pack(pady=(0, spacing("sm")))

    def _draw_chart(self, humor_history=None):
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        self.canvas.delete("all")
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 80 or ch < 80:
            return

        if not humor_history:
            pts = []
            dates = []
        else:
            pts = [item.get("media_humor", 0) or 0 for item in humor_history]
            dates = [item.get("data") or item.get("date") or "" for item in humor_history]

        if len(pts) < 2:
            if len(pts) == 1:
                pts = [pts[0], pts[0]]
                dates = [dates[0], dates[0]] if dates else dates
            else:
                pts = []
                dates = []

        if not pts:
            self.canvas.pack_forget()
            if hasattr(self, "_chart_empty") and self._chart_empty.winfo_exists():
                self._chart_empty.pack(fill="both", padx=spacing("xl"), pady=spacing("xl"))
            return

        if hasattr(self, "_chart_empty") and self._chart_empty.winfo_exists():
            self._chart_empty.pack_forget()
        if not self.canvas.winfo_exists():
            return
        if not self.canvas.winfo_ismapped():
            self.canvas.pack(fill="both", padx=spacing("xs"), pady=(spacing("xs"), spacing("md")))

        mx = max(24, int(cw * 0.06))
        my = max(14, int(ch * 0.1))
        cw2 = cw - 2 * mx
        ch2 = ch - 2 * my

        self.canvas.create_rectangle(
            mx,
            my,
            cw - mx,
            ch - my,
            fill=THEME["surface"],
            outline=THEME["chart_grid"],
            width=1,
        )

        for i in range(6):
            val = 1 + i
            gy = (ch - my) - (i * ch2 / 5)
            self.canvas.create_line(
                mx,
                gy,
                cw - mx,
                gy,
                fill=THEME["chart_grid"],
                dash=(3, 5),
            )
            self.canvas.create_text(
                mx - 6,
                gy,
                text=str(val),
                font=(FONT_FAMILY, 8),
                fill=THEME["text_muted"],
                anchor="e",
            )

        n = len(pts)
        coords = [
            (mx + i * cw2 / (n - 1), (ch - my) - ((v - 1) * ch2 / 4)) for i, v in enumerate(pts)
        ]

        poly_pts = []
        for x, y in coords:
            poly_pts += [x, y]
        poly_pts += [coords[-1][0], ch - my, coords[0][0], ch - my]
        self.canvas.create_polygon(poly_pts, fill=THEME["chart_fill"], outline="")

        for i in range(len(coords) - 1):
            x1, y1 = coords[i]
            x2, y2 = coords[i + 1]
            self.canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=THEME["chart_line"],
                width=2,
                capstyle="round",
                joinstyle="round",
            )

        for i, (x, y) in enumerate(coords):
            v = pts[i]
            dot = (
                THEME["dot_bad"] if v < 2.5 else THEME["dot_mid"] if v < 3.5 else THEME["dot_good"]
            )
            self.canvas.create_oval(
                x - 4,
                y - 4,
                x + 4,
                y + 4,
                fill=dot,
                outline=THEME["surface"],
                width=2,
            )

        step = max(1, n // 7)
        for i, (x, _) in enumerate(coords):
            if i % step == 0:
                self.canvas.create_text(
                    x,
                    ch - 8,
                    text=dates[i],
                    font=(FONT_FAMILY, 8),
                    fill=THEME["text_muted"],
                )

        legend = [
            ("● Bom", THEME["dot_good"]),
            ("● Atenção", THEME["dot_mid"]),
            ("● Baixo", THEME["dot_bad"]),
        ]
        lx = cw - mx - 4
        for j, (lbl, lcolor) in enumerate(reversed(legend)):
            self.canvas.create_text(
                lx,
                my + 12 + j * 14,
                text=lbl,
                font=(FONT_FAMILY, 8),
                fill=lcolor,
                anchor="e",
            )

    def _abrir_notificacoes_ajuda(self):
        notifs = self.servico_dashboard.obter_notificacoes_ajuda()
        NotificationPanel(
            self,
            "Notificações de Ajuda",
            notifs,
            "ajuda",
            on_mark_read=self._marcar_lida,
            on_mark_all_read=self._marcar_todas_lidas,
        )

    def _abrir_notificacoes_alertas(self):
        notifs = self.servico_dashboard.obter_notificacoes_alertas()
        NotificationPanel(
            self,
            "Notificações de Alerta",
            notifs,
            "alerta",
            on_mark_read=self._marcar_lida,
            on_mark_all_read=self._marcar_todas_lidas,
        )

    def _abrir_perfil(self):
        ProfileModal(self, self.controller.usuario_logado, on_edit=self._editar_perfil)

    def _editar_perfil(self):
        user = getattr(self.controller, "usuario_logado", {}) or {}
        modal = ctk.CTkToplevel(self)
        modal.title("Editar Perfil")
        modal.configure(fg_color=THEME["surface"])
        modal.resizable(False, False)
        w, h = 480, 420
        sx = modal.winfo_screenwidth() // 2 - w // 2
        sy = modal.winfo_screenheight() // 2 - h // 2
        modal.geometry(f"{w}x{h}+{sx}+{sy}")
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        card = ctk.CTkFrame(modal, fg_color=THEME["surface"], corner_radius=RADIUS["lg"])
        card.pack(fill="both", padx=spacing("xl"), pady=spacing("xl"))

        ctk.CTkLabel(
            card, text="Editar Perfil", font=themed_font("h2", "bold"), text_color=THEME["text"]
        ).pack(anchor="w", pady=(0, spacing("md")))

        entry_nome = ctk.CTkEntry(card, placeholder_text="Nome completo")
        entry_nome.insert(0, user.get("first_name", ""))
        entry_nome.pack(fill="x", pady=(0, spacing("sm")))

        entry_email = ctk.CTkEntry(card, placeholder_text="E-mail")
        entry_email.insert(0, user.get("email", ""))
        entry_email.pack(fill="x", pady=(0, spacing("sm")))

        entry_senha = ctk.CTkEntry(card, placeholder_text="Nova senha (opcional)", show="*")
        entry_senha.pack(fill="x", pady=(0, spacing("sm")))

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", pady=(spacing("md"), 0))

        def _salvar():
            nome = entry_nome.get().strip()
            email = entry_email.get().strip()
            senha = entry_senha.get().strip()
            if not nome or not email:
                self._show_error("Nome e email são obrigatórios.")
                return
            try:
                user["first_name"] = nome
                user["email"] = email
                if senha:
                    from ser_pleno.application.services.autenticacao import ServicoAutenticacao

                    auth_service = ServicoAutenticacao(
                        auth_service=getattr(self.controller, "auth_service", None)
                    )
                    res = auth_service.alterar_senha(user.get("password", ""), senha)
                    if not res.get("success"):
                        self._show_error(res.get("message", "Falha ao alterar senha."))
                        return
                self._show_success("Perfil atualizado.")
                modal.destroy()
            except Exception as e:
                self._show_error(f"Falha ao atualizar perfil.\n{e}")

        ctk.CTkButton(
            footer,
            text="Cancelar",
            command=modal.destroy,
            width=110,
            height=36,
            corner_radius=RADIUS["button"],
            fg_color=THEME["divider"],
            hover_color=THEME["border"],
            text_color=THEME["text_muted"],
        ).pack(side="left", padx=(0, spacing("sm")))
        ctk.CTkButton(
            footer,
            text="Salvar",
            command=_salvar,
            width=140,
            height=36,
            corner_radius=RADIUS["button"],
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            text_color="white",
            font=themed_font("button", "bold"),
        ).pack(side="right")

    def _atualizar_badge_notificacoes(self):
        if not hasattr(self, "help_badge") or not hasattr(self, "alert_badge"):
            return

        ajuda_cache = self._notification_cache.get_ajuda()
        if ajuda_cache is not None:
            ajuda, n_ajuda = ajuda_cache
        else:
            ajuda = self.servico_dashboard.obter_notificacoes_ajuda()
            n_ajuda = sum(1 for n in ajuda if not n.get("lida", True))
            self._notification_cache.set_ajuda(ajuda, n_ajuda)

        alertas_cache = self._notification_cache.get_alertas()
        if alertas_cache is not None:
            alertas, n_alertas = alertas_cache
        else:
            alertas = self.servico_dashboard.obter_notificacoes_alertas()
            n_alertas = sum(1 for n in alertas if not n.get("lida", True))
            self._notification_cache.set_alertas(alertas, n_alertas)

        self._set_badge(self.help_badge, n_ajuda, getattr(self, "help_badge_anchor", None))
        self._set_badge(self.alert_badge, n_alertas, getattr(self, "alert_badge_anchor", None))

    def _set_badge(self, badge: ctk.CTkFrame, count: int, anchor=None):
        lbl = next((c for c in badge.winfo_children() if isinstance(c, ctk.CTkLabel)), None)
        if lbl:
            lbl.configure(text=str(count) if count else "")
        if count > 0 and anchor and anchor.winfo_exists():
            self.update_idletasks()
            anchor_x = anchor.winfo_x()
            anchor_y = anchor.winfo_y()
            badge.place(x=anchor_x + anchor.winfo_width() + 4, y=anchor_y - 4)
            badge.lift()
        else:
            badge.place_forget()

    def _marcar_lida(self, notif_id, tipo):
        self.servico_dashboard.marcar_notificacao_como_lida(notif_id, tipo)
        self._notification_cache.invalidate_all()
        self._atualizar_badge_notificacoes()

    def _marcar_todas_lidas(self, tipo):
        try:
            notifs = (
                self.servico_dashboard.obter_notificacoes_ajuda()
                if tipo == "ajuda"
                else self.servico_dashboard.obter_notificacoes_alertas()
            )
            for n in notifs:
                self.servico_dashboard.marcar_notificacao_como_lida(n["id"], tipo)
            self._notification_cache.invalidate_all()
            self._atualizar_badge_notificacoes()
        except Exception as e:
            logger.error("Erro ao marcar todas como lidas: %s", e)
            self._show_error(f"Erro ao marcar notificações como lidas:\n{e}")

    @staticmethod
    def _limpar(widget):
        for child in widget.winfo_children():
            child.destroy()

    @staticmethod
    def _humor_emoji(media) -> str:
        if media is None:
            return ICONS["mood_bad"]
        if media < 2.5:
            return ICONS["mood_bad"]
        if media < 3.5:
            return ICONS["mood_neutral"]
        return ICONS["mood_good"]

    @staticmethod
    def get_humor_emoji(media):
        return DashboardFrame._humor_emoji(media)

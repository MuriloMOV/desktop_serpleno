from __future__ import annotations

import json
import logging
import os
import tkinter as tk
from typing import Any

import customtkinter as ctk

from ser_pleno.application.services.autenticacao import ServicoAutenticacao
from ser_pleno.features.configuracoes.service import ServicoConfiguracoes
from ser_pleno.ui.components.icons import ICONS
from ser_pleno.ui.components.ui_components import (
    Badge,
    BaseModal,
    GhostButton,
    PageHeader,
    PrimaryButton,
    Toast,
)
from ser_pleno.ui.theme import RADIUS, SPACING, THEME, themed_font
from ser_pleno.ui.theme_extensions import spacing
from ser_pleno.utils.async_runner import AsyncRunner, log_view_init_ms

logger = logging.getLogger("apps.desktop")


# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Helpers
# ••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=THEME["divider"]).pack(fill="x")


# •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Paleta dedicada + helpers de cor
# •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••


# •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Componentes reutilizáveis
# •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class ConfigInputField(ctk.CTkFrame):
    """
    Campo de entrada com label, ícone e estados
    normal / foco / erro.
    """

    _BORDER_NORMAL = THEME["border"]
    _BORDER_FOCUS = THEME["primary"]
    _BORDER_ERROR = THEME["danger"]
    _BG_NORMAL = THEME["bg_alt"]
    _BG_FOCUS = THEME["surface"]

    def __init__(
        self,
        parent,
        label: str,
        value: str = "",
        icon: str = "",
        placeholder: str = "",
        password: bool = False,
    ):
        super().__init__(parent, fg_color="transparent")

        self._label = ctk.CTkLabel(
            self,
            text=label,
            font=themed_font("caption", "bold"),
            text_color=THEME["text_muted"],
            anchor="w",
        )
        self._label.pack(fill="x", pady=(0, 4))

        box = ctk.CTkFrame(
            self,
            corner_radius=RADIUS["md"],
            fg_color=self._BG_NORMAL,
            border_width=1,
            border_color=self._BORDER_NORMAL,
        )
        box.pack(fill="x")
        box.grid_columnconfigure(1, weight=1)
        self._box = box

        if icon:
            ctk.CTkLabel(
                box,
                text=icon,
                font=themed_font("body"),
                text_color=THEME["text_muted"],
                width=36,
            ).grid(row=0, column=0, padx=(10, 4), pady=8)

        self.entry = ctk.CTkEntry(
            box,
            placeholder_text=placeholder,
            fg_color=THEME["bg_alt"],
            border_width=0,
            font=themed_font("body"),
            height=36,
            show="●" if password else "",
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
        if value:
            self.entry.insert(0, value)

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    # API ---------------------------------------------------------------------
    def get(self) -> str:
        return self.entry.get()

    def set_error(self, msg: str = ""):
        self._box.configure(
            border_color=self._BORDER_ERROR,
            fg_color=THEME["danger_soft"],
        )
        self._label.configure(text_color=THEME["danger"])

    def clear_state(self):
        self._box.configure(
            border_color=self._BORDER_NORMAL,
            fg_color=self._BG_NORMAL,
        )
        self._label.configure(text_color=THEME["text_muted"])

    # Internos ----------------------------------------------------------------
    def _on_focus_in(self, _=None):
        self._box.configure(
            border_color=self._BORDER_FOCUS,
            fg_color=self._BG_FOCUS,
        )
        self._label.configure(text_color=THEME["primary"])

    def _on_focus_out(self, _=None):
        self._box.configure(
            border_color=self._BORDER_NORMAL,
            fg_color=self._BG_NORMAL,
        )
        self._label.configure(text_color=THEME["text_muted"])


class ToggleRow(ctk.CTkFrame):
    """Linha com ícone + título + subtítulo + switch."""

    def __init__(
        self, parent, icon: str, title: str, sub: str, on_toggle=None, initial: bool = False
    ):
        super().__init__(parent, fg_color="transparent")

        self._on_toggle = on_toggle

        txt = ctk.CTkFrame(self, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            txt,
            text=title,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            txt,
            text=sub,
            font=themed_font("overline"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w")

        self.switch = ctk.CTkSwitch(
            self,
            text="",
            progress_color=THEME["primary"],
        )
        self.switch.pack(side="right", padx=spacing("sm"))
        if initial:
            self.switch.select()
        else:
            self.switch.deselect()
        self.switch.configure(command=self._handle_toggle)

    def _handle_toggle(self):
        if self._on_toggle:
            self._on_toggle(self.switch.get())


class ActionItemRow(ctk.CTkFrame):
    """Linha de item de ação com ícone, título, subtítulo e botão."""

    def __init__(
        self,
        parent,
        icon: str,
        title: str,
        sub: str,
        btn_text: str,
        danger: bool = False,
        on_action=None,
    ):
        super().__init__(parent, fg_color="transparent")

        self._on_action = on_action

        ctk.CTkLabel(
            self,
            text=icon,
            font=themed_font("h3"),
            fg_color=THEME["bg_alt"],
            width=40,
            height=40,
            corner_radius=RADIUS["pill"],
        ).pack(side="left", padx=(0, spacing("md")))

        txt = ctk.CTkFrame(self, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            txt,
            text=title,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            txt,
            text=sub,
            font=themed_font("overline"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w")

        color = THEME["danger"] if danger else THEME["primary"]
        hover = THEME["danger_soft"] if danger else THEME["primary_soft"]

        btn = GhostButton(
            self,
            text=btn_text,
            width=150,
            command=lambda: self._handle_action(btn_text),
        )
        btn.pack(side="right", padx=spacing("sm"))
        if danger:
            btn.configure(
                text_color=color,
                hover_color=hover,
            )

    def _handle_action(self, btn_text: str):
        if self._on_action:
            self._on_action(btn_text)


class SectionCard(ctk.CTkFrame):
    """Card de seção com ícone e título."""

    def __init__(self, parent, icon: str, title: str, badge: str = ""):
        super().__init__(
            parent,
            fg_color=THEME["surface"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=THEME["border"],
        )
        self._icon = icon
        self._title = title
        self._badge = badge

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=spacing("lg"), pady=(spacing("md"), spacing("item_gap")))

        ctk.CTkLabel(
            header,
            text=f"{icon}  {title}",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        if badge:
            Badge(
                header,
                text=badge,
                color=THEME["warning"],
            ).pack(side="right")

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=spacing("lg"), pady=(0, spacing("md")))

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body


class FormModal(BaseModal):
    """Modal reutilizável para formulários."""

    def __init__(
        self, parent, title: str, width: int = 420, height: int = 340, icon: str = ICONS["lock"]
    ):
        super().__init__(parent, title, width, height, fg_color=THEME["surface"])
        self.withdraw()
        self._title = title
        self._icon = icon
        self._build()
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.deiconify()

    def _center(self, parent, w, h):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _build(self):
        # Banner
        banner = ctk.CTkFrame(self, fg_color=THEME["primary_soft"], corner_radius=0, height=64)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        bi = ctk.CTkFrame(banner, fg_color="transparent")
        bi.pack(fill="both", expand=True, padx=spacing("xl"))
        ib = ctk.CTkFrame(
            bi, width=38, height=38, corner_radius=RADIUS["button"], fg_color=THEME["primary"]
        )
        ib.pack(side="left", padx=(0, 12))
        ib.pack_propagate(False)
        ctk.CTkLabel(ib, text=self._icon, font=themed_font("h3", "bold")).place(
            relx=0.5, rely=0.5, anchor="center"
        )
        ctk.CTkLabel(
            bi, text=self._title, font=themed_font("h3", "bold"), text_color=THEME["primary"]
        ).pack(side="left")

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=SPACING["card_pad"], pady=SPACING["item_gap"])

        self._fields_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self._fields_frame.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(inner, fg_color="transparent", height=52)
        footer.pack(fill="x", side="bottom", pady=(SPACING["item_gap"], 0))
        footer.pack_propagate(False)

        GhostButton(
            footer,
            text="Cancelar",
            width=120,
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))
        self._primary = PrimaryButton(
            footer,
            text="Confirmar",
            width=140,
            command=self._on_confirm,
        )
        self._primary.pack(side="right")

    def _on_confirm(self):
        raise NotImplementedError


class AlterarSenhaModal(FormModal):
    def __init__(self, parent, on_save):
        super().__init__(parent, "Alterar Senha", width=420, height=520, icon=ICONS["key"])
        self._on_save = on_save

        self.f_senha_atual = ConfigInputField(
            self._fields_frame,
            "Senha Atual",
            placeholder="••••••••",
            password=True,
            icon=ICONS["lock"],
        )
        self.f_confirmar_senha_atual = ConfigInputField(
            self._fields_frame,
            "Confirmar Senha Atual",
            placeholder="repita a senha atual",
            password=True,
            icon=ICONS["lock"],
        )
        self.f_nova_senha = ConfigInputField(
            self._fields_frame,
            "Nova Senha",
            placeholder="mín. 8 caracteres",
            password=True,
            icon=ICONS["key"],
        )
        self.f_confirmar_senha = ConfigInputField(
            self._fields_frame,
            "Confirmar Nova Senha",
            placeholder="confirme a nova senha",
            password=True,
            icon=ICONS["key"],
        )

        strength_frame = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
        strength_frame.pack(fill="x", pady=(0, 10))
        self._strength_bar = ctk.CTkFrame(strength_frame, fg_color=THEME["border"], corner_radius=RADIUS["xs"], height=6)
        self._strength_bar.pack(fill="x")
        self._strength_bar.pack_propagate(False)
        self._strength_segments = []
        for i in range(5):
            seg = ctk.CTkFrame(self._strength_bar, fg_color="transparent", corner_radius=0)
            seg.place(relx=i / 5, rely=0, relwidth=0.2, relheight=1)
            self._strength_segments.append(seg)
        self._strength_label = ctk.CTkLabel(
            strength_frame,
            text="",
            font=themed_font("overline"),
            text_color=THEME["text_muted"],
        )
        self._strength_label.pack(anchor="w", pady=(4, 0))

        for f in (self.f_senha_atual, self.f_confirmar_senha_atual, self.f_nova_senha, self.f_confirmar_senha):
            f.pack(fill="x", pady=(0, 10))

        self.f_nova_senha.entry.bind("<KeyRelease>", self._on_new_password_change)

    def _on_new_password_change(self, event=None):
        senha = self.f_nova_senha.get()
        score = self._calcular_forca_senha(senha)
        self._update_strength_ui(score)

    def _calcular_forca_senha(self, senha):
        if not senha:
            return 0
        score = 0
        if len(senha) >= 8:
            score += 1
        if any(c.islower() for c in senha):
            score += 1
        if any(c.isupper() for c in senha):
            score += 1
        if any(c.isdigit() for c in senha):
            score += 1
        if any(not c.isalnum() for c in senha):
            score += 1
        return score

    def _update_strength_ui(self, score):
        colors = [THEME["danger"], THEME["danger"], THEME["warning"], THEME["warning"], THEME["success"]]
        labels = ["", "Fraca", "Fraca", "Média", "Média", "Forte"]
        label_colors = [THEME["text_muted"], THEME["danger"], THEME["danger"], THEME["warning"], THEME["warning"], THEME["success"]]
        for i, seg in enumerate(self._strength_segments):
            seg.configure(fg_color=colors[score] if i < score else "transparent")
        self._strength_label.configure(text=labels[score], text_color=label_colors[score])

    def _on_confirm(self):
        atual = self.f_senha_atual.get().strip()
        confirmar_atual = self.f_confirmar_senha_atual.get().strip()
        nova = self.f_nova_senha.get().strip()
        confirm = self.f_confirmar_senha.get().strip()

        for f in (self.f_senha_atual, self.f_confirmar_senha_atual, self.f_nova_senha, self.f_confirmar_senha):
            f.clear_state()

        if not atual or not confirmar_atual or not nova or not confirm:
            self._show_error("Preencha todos os campos.", title="Atenção")
            return
        if atual != confirmar_atual:
            self.f_confirmar_senha_atual.set_error("Senha atual não confere.")
            self._show_error("Confirmação da senha atual não confere.", title="Atenção")
            return
        if nova != confirm:
            self.f_confirmar_senha.set_error("As senhas não coincidem.")
            self._show_error("As senhas não coincidem.", title="Atenção")
            return
        if len(nova) < 8:
            self.f_nova_senha.set_error("Mínimo de 8 caracteres.")
            self._show_error("A nova senha deve ter pelo menos 8 caracteres.", title="Atenção")
            return
        if not self._senha_atende_policy(nova):
            self.f_nova_senha.set_error("Política de senha não atendida.")
            self._show_error("Use maiúscula, minúscula, número e símbolo.", title="Atenção")
            return

        self._on_save(atual, nova)
        self.destroy()

    def _senha_atende_policy(self, senha):
        if len(senha) < 8:
            return False
        if not any(c.islower() for c in senha):
            return False
        if not any(c.isupper() for c in senha):
            return False
        if not any(c.isdigit() for c in senha):
            return False
        if not any(not c.isalnum() for c in senha):
            return False
        return True

    def _show_error(self, message: str, title: str = "Atenção") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass


# •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Frame principal de configurações
# •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class ConfiguracoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        import time as _time

        self._t0 = _time.perf_counter()
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.servico_configuracoes = ServicoConfiguracoes(
            auth_service=getattr(controller, "auth_service", None)
        )
        self._servico_autenticacao = ServicoAutenticacao(
            auth_service=getattr(controller, "auth_service", None)
        )
        from ser_pleno.config.paths import get_project_root

        self.base_path = get_project_root()
        self._notificacoes_state: dict[str, bool] = {}
        self._toggle_rows: dict[str, Any] = {}
        self._images: dict[str, Any] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self._build_header()
        self._build_body()
        log_view_init_ms("configuracoes", self._t0, widget_ref=self)
        self.after_idle(self._carregar_configuracoes)

    # —— helpers ---------------------------------------------------------------
    def _load_image(self, name: str, size: tuple[int, int]):
        key = f"{name}:{size}"
        if key in self._images:
            return self._images[key]
        path = os.path.join(self.base_path, "assets", "avatars", name)
        if not os.path.exists(path):
            return None
        try:

            def _load(p=path, s=size):
                from PIL import Image

                return ctk.CTkImage(light_image=Image.open(p), size=s)

            def _on_ready(img, k=key):
                self._images[k] = img

            AsyncRunner.run(task=_load, on_success=_on_ready, widget_ref=self)
        except Exception as exc:
            logger.exception("Erro ao carregar imagem %s: %s", name, exc)
        return None

    def _profile_data(self) -> dict[str, str]:
        try:
            with open(os.path.join(self.base_path, "user_profile.json")) as f:
                return json.load(f)
        except Exception:
            return {}

    # —— layout ---------------------------------------------------------------
    def _build_header(self):
        header = PageHeader(
            self,
            title="Preferências do Sistema",
            subtitle="Personalize sua experiência no SerPleno",
        )
        header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=SPACING["page_x"],
            pady=(SPACING["page_y"], 16),
        )

    def _build_body(self):
        col_left = ctk.CTkFrame(self, fg_color="transparent")
        col_left.grid(row=1, column=0, sticky="nsew", padx=(SPACING["page_x"], 10))
        self._build_cartao_pessoal(col_left)

        col_right = ctk.CTkFrame(self, fg_color="transparent")
        col_right.grid(row=1, column=1, sticky="nsew", padx=(10, SPACING["page_x"]))

        self._build_central_avisos(col_right)
        self._build_aparencia(col_right)
        self._build_seguranca(col_right)
        self._build_onboarding(col_right)

    # —— cartão pessoal -------------------------------------------------------
    def _build_cartao_pessoal(self, container):
        card = SectionCard(container, ICONS["user"], "Informações Pessoais")
        card.pack(fill="both", expand=True)

        profile = self._profile_data()
        avatar_name = profile.get("avatar", "avatar-1.jpg")

        # Avatar com ring
        av_outer = ctk.CTkFrame(card.body, fg_color="transparent")
        av_outer.pack(pady=(4, 10))

        av_ring = ctk.CTkFrame(
            av_outer,
            width=130,
            height=130,
            corner_radius=RADIUS["avatar"],
            fg_color=THEME["primary_soft"],
        )
        av_ring.pack()
        av_ring.pack_propagate(False)

        img = self._load_image(avatar_name, (118, 118))
        self.avatar_display = ctk.CTkLabel(
            av_ring, text="" if img else ICONS["user"], image=img, font=themed_font("h2", "bold")
        )
        self.avatar_display.place(relx=0.5, rely=0.5, anchor="center")

        if img is None:

            def _refresh_avatar():
                refreshed = self._load_image(avatar_name, (118, 118))
                if refreshed and self.avatar_display.winfo_exists():
                    self.avatar_display.configure(image=refreshed, text="")

            self.after_idle(_refresh_avatar)

        # Nome e email
        user = self.controller.usuario_logado or {}
        nome = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user.get(
            "username", "Usuário"
        )
        email = user.get("email", "email@exemplo.com")

        ctk.CTkLabel(
            card.body, text=nome, font=themed_font("h4", "bold"), text_color=THEME["text"]
        ).pack()
        ctk.CTkLabel(
            card.body, text=email, font=themed_font("body_sm"), text_color=THEME["text_muted"]
        ).pack(pady=(2, 12))

        # Botão galeria
        self._btn_gallery = GhostButton(
            card.body,
            text="Alterar imagem de perfil",
            command=self._toggle_gallery,
            width=240,
        )
        self._btn_gallery.pack(pady=(0, 8))

        # Galeria de avatares (oculta por padrão)
        self.gallery_frame = ctk.CTkFrame(
            card.body,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=THEME["border"],
        )
        self.grid_galeria = ctk.CTkFrame(self.gallery_frame, fg_color="transparent")
        self.grid_galeria.pack(padx=SPACING["item_gap"], pady=SPACING["item_gap"])
        self._fill_gallery()

        _divider(card.body)

        ConfigInputField(card.body, "Nome de exibição", value=nome, icon=ICONS["user"]).pack(
            fill="x", pady=(0, 8)
        )
        ConfigInputField(card.body, "Endereço de E-mail", value=email, icon=ICONS["mail"]).pack(
            fill="x", pady=(0, 8)
        )

    def _fill_gallery(self):
        avatars_dir = os.path.join(self.base_path, "assets", "avatars")
        try:
            files = sorted(
                f for f in os.listdir(avatars_dir) if f.startswith("avatar-") and f.endswith(".jpg")
            )
        except Exception:
            files = []

        for i, filename in enumerate(files):
            btn = ctk.CTkButton(
                self.grid_galeria,
                text="",
                image=self._load_image(filename, (52, 52)),
                width=52,
                height=52,
                fg_color="white",
                hover_color=THEME["primary_soft"],
                corner_radius=RADIUS["md"],
                command=lambda fn=filename: self._select_avatar(fn),
            )
            btn._avatar_filename = filename
            btn.grid(row=i // 4, column=i % 4, padx=spacing("xs"), pady=spacing("xs"))

        self.after_idle(self._refresh_gallery_images)

    def _refresh_gallery_images(self):
        for btn in self.grid_galeria.winfo_children():
            if isinstance(btn, ctk.CTkButton) and hasattr(btn, "_avatar_filename"):
                filename = btn._avatar_filename
                img = self._load_image(filename, (52, 52))
                if img and btn.winfo_exists():
                    btn.configure(image=img)

    def _toggle_gallery(self):
        if self.gallery_frame.winfo_ismapped():
            self.gallery_frame.pack_forget()
        else:
            self.gallery_frame.pack(
                fill="x", padx=spacing("xl"), pady=spacing("md"), before=self.avatar_display
            )

    def _select_avatar(self, filename):
        img = self._load_image(filename, (160, 160))
        if img:
            self.avatar_display.configure(image=img)
            try:
                with open(os.path.join(self.base_path, "user_profile.json"), "w") as f:
                    json.dump({"avatar": filename}, f)
            except Exception as exc:
                logger.exception("Erro ao salvar avatar: %s", exc)
        self.gallery_frame.pack_forget()

    # —— central de avisos ----------------------------------------------------
    def _build_central_avisos(self, container):
        card = SectionCard(
            container, ICONS["notification"], "Central de Avisos", badge="Tempo Real"
        )
        card.pack(fill="x", pady=(0, 16))

        itens = [
            ("Mensagens Diretas", "Alertar novos chats privados e mural"),
            ("Pedidos de Ajuda", "Notificações críticas de suporte ao aluno"),
            ("Feedback de Alunos", "Novas avaliações e comentários"),
            ("Efeitos Sonoros", "Feedback auditivo para alertas"),
        ]
        for titulo, subtitulo in itens:
            row = ToggleRow(
                card.body,
                "",
                titulo,
                subtitulo,
                on_toggle=lambda estado, t=titulo: self._on_toggle_notificacao(t, estado),
            )
            row.pack(fill="x", pady=4)
            self._toggle_rows[titulo] = row
            self._notificacoes_state[titulo] = row.switch.get()

    def _on_toggle_notificacao(self, tipo: str, estado: bool):
        self._notificacoes_state[tipo] = estado
        logger.info("Notificação '%s' %s", tipo, "ativada" if estado else "desativada")

    # —— aparência ------------------------------------------------------------
    def _build_aparencia(self, container):
        card = SectionCard(container, ICONS["heart"], "Aparência & Acessibilidade")
        card.pack(fill="x", pady=(0, 16))

        row = ctk.CTkFrame(card.body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

        self._theme_values = ["Modo Sereno (Claro)", "Modo Foco (Escuro)"]
        self._font_values = ["Padrão (16px)", "Grande (18px)"]

        self._theme_btn = ctk.CTkButton(
            row,
            text="Modo Sereno (Claro)",
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            anchor="w",
            height=34,
            command=lambda: self._toggle_menu("theme"),
        )
        self._theme_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self._font_btn = ctk.CTkButton(
            row,
            text="Padrão (16px)",
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            hover_color=THEME["bg_alt"],
            border_width=1,
            border_color=THEME["border"],
            anchor="w",
            height=34,
            command=lambda: self._toggle_menu("font"),
        )
        self._font_btn.pack(side="left", expand=True, fill="x")

        self._select_menu = None

        tip = SectionCard(card.body, "", "Dica de Produtividade")
        tip.pack(fill="x")
        ctk.CTkLabel(
            tip.body,
            text=f"{ICONS['chart']} O Modo Foco reduz a emissão de luz azul, ideal para sessões noturnas.",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=spacing("md"), pady=spacing("md"))

        PrimaryButton(
            tip.body,
            text="Salvar Preferências",
            command=self._salvar_configuracoes,
        ).pack(pady=(spacing("md"), 0))

    def _toggle_menu(self, kind: str) -> None:
        if self._select_menu is not None:
            try:
                self._select_menu.unpost()
            except Exception as exc:
                logger.debug("Falha ao fechar menu: %s", exc)
            self._select_menu = None
            return

        btn = self._theme_btn if kind == "theme" else self._font_btn
        values = self._theme_values if kind == "theme" else self._font_values
        current = btn.cget("text")

        menu = tk.Menu(btn, tearoff=0)
        for v in values:
            menu.add_command(label=v, command=lambda val=v, k=kind: self._choose(k, val))

        self._select_menu = menu
        try:
            menu.tk_popup(btn.winfo_rootx(), btn.winfo_rooty() + btn.winfo_height())
        except Exception as exc:
            logger.debug("Falha ao exibir menu: %s", exc)

    def _choose(self, kind: str, value: str):
        if kind == "theme":
            self._theme_btn.configure(text=value)
            self._alterar_tema(value)
        else:
            self._font_btn.configure(text=value)
            self._alterar_fonte(value)
        self._select_menu = None

    def _alterar_fonte(self, value: str):
        """Altera o tamanho de fonte global da aplicação."""
        try:
            tamanho = 18 if "Grande" in value else 16
            ctk.set_widget_scaling(tamanho / 16)
            logger.info("Fonte alterada para: %s (scaling=%s)", value, tamanho / 16)
        except Exception as exc:
            logger.exception("Erro ao alterar fonte: %s", exc)

    def _alterar_tema(self, value: str):
        """Altera o tema da aplicação."""
        try:
            if "Escuro" in value:
                ctk.set_appearance_mode("dark")
            else:
                ctk.set_appearance_mode("light")
            logger.info("Tema alterado para: %s", value)
        except Exception as exc:
            logger.exception("Erro ao alterar tema: %s", exc)

    def _carregar_configuracoes(self):
        try:
            res = self.servico_configuracoes.obter_configuracoes()
            if res.get("success") and res.get("data"):
                user_id = None
                auth = getattr(self.servico_configuracoes, "_auth_service", None)
                if auth and getattr(auth, "user", None):
                    user_id = auth.user.get("id")
                
                for item in res["data"]:
                    if item.get("user_id") == user_id and user_id is not None:
                        theme = item.get("theme")
                        notifications = item.get("notifications")
                        if theme:
                            self._theme_btn.configure(text=theme)
                            self._alterar_tema(theme)
                        if notifications:
                            try:
                                notif = json.loads(notifications)
                                for titulo, estado in notif.items():
                                    self._notificacoes_state[titulo] = estado
                                    if titulo in self._toggle_rows:
                                        switch = self._toggle_rows[titulo].switch
                                        if estado:
                                            switch.select()
                                        else:
                                            switch.deselect()
                            except Exception:
                                pass
                        break
        except Exception as exc:
            logger.exception("Erro ao carregar configurações: %s", exc)
        self._apply_notification_settings()

    def _salvar_configuracoes(self):
        user_id = None
        auth = getattr(self.servico_configuracoes, "_auth_service", None)
        if auth and getattr(auth, "user", None):
            user_id = auth.user.get("id")
        
        dados = {
            "user_id": user_id,
            "theme": self._theme_btn.cget("text"),
            "notifications": json.dumps(self._notificacoes_state),
        }
        
        try:
            res = self.servico_configuracoes.atualizar_configuracoes(dados)
            if res.get("success"):
                Toast(self.winfo_toplevel(), "Preferências salvas com sucesso!", status="success")
                self._apply_notification_settings()
            else:
                self._show_error(res.get("message", "Falha ao salvar preferências."))
        except Exception as exc:
            logger.exception("Erro ao salvar configurações: %s", exc)
            self._show_error("Falha ao salvar preferências.")

    def _apply_notification_settings(self) -> None:
        try:
            notifier = getattr(self.controller, "_desktop_notifier", None)
            if notifier is None:
                return
            sound_enabled = self._notificacoes_state.get("Efeitos Sonoros", True)
            notifier.set_sound_enabled(bool(sound_enabled))
        except Exception as exc:
            logger.debug("Falha ao aplicar configurações de notificação: %s", exc)

    # —— segurança ------------------------------------------------------------
    def _build_seguranca(self, container):
        card = SectionCard(container, ICONS["settings"], "Sessão & Segurança")
        card.pack(fill="x")

        ActionItemRow(
            card.body,
            ICONS["users"],
            "Perfil Público",
            "Permitir que outros visualizem suas conquistas",
            btn_text="",
            on_action=lambda t: self._on_seguranca_action(t),
        ).pack(fill="x", pady=2)

        ActionItemRow(
            card.body,
            ICONS["key"],
            "Credenciais",
            "Última alteração há 3 meses",
            btn_text="Alterar Senha",
            on_action=lambda t: self._on_seguranca_action(t),
        ).pack(fill="x", pady=2)

        ActionItemRow(
            card.body,
            ICONS["code"],
            "Este Dispositivo",
            "Sessão ativa agora — Windows Desktop",
            btn_text="Encerrar Acesso",
            danger=True,
            on_action=lambda t: self._on_seguranca_action(t),
        ).pack(fill="x", pady=2)

    def _build_onboarding(self, container):
        card = SectionCard(container, ICONS["help"], "Tour Guiado")
        card.pack(fill="x", pady=(16, 0))

        ctk.CTkLabel(
            card.body,
            text="Reinicie o onboarding para revisar as principais funcionalidades do sistema.",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        PrimaryButton(
            card.body,
            text="Reiniciar tour guiado",
            command=self._reiniciar_onboarding,
        ).pack(pady=(0, spacing("md")))

    def _reiniciar_onboarding(self):
        app = self.winfo_toplevel()
        tour = getattr(app, "onboarding_tour", None)
        if tour is not None:
            tour.restart()

    def _on_seguranca_action(self, btn_text: str):
        if btn_text == "Alterar Senha":
            self._abrir_modal_senha()
        elif btn_text == "Encerrar Acesso":
            self._encerrar_sessao()

    def _abrir_modal_senha(self):
        AlterarSenhaModal(self, on_save=self._salvar_senha)

    def _salvar_senha(self, senha_atual: str, nova_senha: str):
        res = self._servico_autenticacao.alterar_senha(senha_atual, nova_senha)
        if res.get("success"):
            self._show_success(res.get("message", "Senha alterada com sucesso."))
        else:
            self._show_error(res.get("message", "Falha ao alterar senha."))

    def _encerrar_sessao(self) -> None:
        if self._confirmar("Deseja encerrar a sessão atual?"):
            try:
                self.winfo_toplevel().mostrar_login()
            except Exception as exc:
                logger.exception("Falha ao encerrar sessão: %s", exc)

    def _show_error(self, message: str, title: str = "Não foi possível concluir") -> None:
        try:
            _ErrorModal(self.winfo_toplevel(), message=message, title=title)
        except Exception:
            pass

    def _show_success(self, message: str, duration: int = 3000) -> None:
        try:
            if hasattr(self, "_toast") and self._toast and self._toast.winfo_exists():
                self._toast.destroy()
            self._toast = Toast(self.winfo_toplevel(), message=message, status="success", duration=duration)
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

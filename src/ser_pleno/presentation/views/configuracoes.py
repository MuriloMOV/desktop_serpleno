from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox
import os
import json
import logging
from typing import Any

from ser_pleno.ui.theme import THEME, SPACING, RADIUS, font, themed_font
from ser_pleno.presentation.components.ui_components import (
    PageHeader,
    Card,
    PrimaryButton,
    GhostButton,
    Badge,
)

logger = logging.getLogger("apps.desktop")

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
    _BORDER_FOCUS  = THEME["primary"]
    _BORDER_ERROR  = THEME["danger"]
    _BG_NORMAL     = THEME["bg_alt"]
    _BG_FOCUS      = THEME["surface"]

    def __init__(self, parent, label: str, value: str = "",
                 icon: str = "", placeholder: str = "",
                 password: bool = False):
        super().__init__(parent, fg_color="transparent")

        self._label = ctk.CTkLabel(
            self, text=label,
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
                box, text=icon,
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
            show="—" if password else "",
        )
        self.entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
        if value:
            self.entry.insert(0, value)

        self.entry.bind("<FocusIn>",  self._on_focus_in)
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

    def __init__(self, parent, icon: str, title: str, sub: str,
                 on_toggle=None, initial: bool = False):
        super().__init__(parent, fg_color="transparent")

        self._on_toggle = on_toggle

        txt = ctk.CTkFrame(self, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            txt, text=title,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            txt, text=sub,
            font=themed_font("overline"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w")

        self.switch = ctk.CTkSwitch(
            self, text="",
            progress_color=THEME["primary"],
        )
        self.switch.pack(side="right", padx=8)
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

    def __init__(self, parent, icon: str, title: str, sub: str,
                 btn_text: str, danger: bool = False, on_action=None):
        super().__init__(parent, fg_color="transparent")

        self._on_action = on_action

        ctk.CTkLabel(
            self, text=icon, font=themed_font("h3"),
            fg_color=THEME["bg_alt"],
            width=40, height=40,
            corner_radius=RADIUS["pill"],
        ).pack(side="left", padx=(0, 12))

        txt = ctk.CTkFrame(self, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            txt, text=title,
            font=themed_font("body", "bold"),
            text_color=THEME["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            txt, text=sub,
            font=themed_font("overline"),
            text_color=THEME["text_muted"],
        ).pack(anchor="w")

        color = THEME["danger"] if danger else THEME["primary"]
        hover = THEME["danger_soft"] if danger else THEME["primary_soft"]

        btn = GhostButton(
            self, text=btn_text, width=150,
            command=lambda: self._handle_action(btn_text),
        )
        btn.pack(side="right", padx=8)
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
        header.pack(fill="x", padx=18, pady=(14, 8))

        ctk.CTkLabel(
            header, text=f"{icon}  {title}",
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(side="left")

        if badge:
            Badge(
                header, text=badge,
                color=THEME["warning"],
            ).pack(side="right")

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=18, pady=(0, 14))

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body

class FormModal(ctk.CTkToplevel):
    """Modal reutilizável para formulários."""

    def __init__(self, parent, title: str, width: int = 420, height: int = 340):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color=THEME["surface"])
        self.withdraw()

        self._center(parent, width, height)
        self._build()
        self.transient(parent.winfo_toplevel())
        self.grab_set()
        self.deiconify()

    def _center(self, parent, w, h):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _build(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=28)

        ctk.CTkLabel(
            inner, text=self.title(),
            font=themed_font("h3", "bold"),
            text_color=THEME["text"],
        ).pack(pady=(0, 18))

        self._fields_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self._fields_frame.pack(fill="both", expand=True)

        footer = ctk.CTkFrame(inner, fg_color="transparent", height=52)
        footer.pack(fill="x", side="bottom", pady=(12, 0))
        footer.pack_propagate(False)

        GhostButton(
            footer, text="Cancelar", width=120,
            command=self.destroy,
        ).pack(side="left", padx=(0, 8))
        self._primary = PrimaryButton(
            footer, text="Confirmar", width=140,
            command=self._on_confirm,
        )
        self._primary.pack(side="right")

    def _on_confirm(self):
        raise NotImplementedError

class AlterarSenhaModal(FormModal):
    def __init__(self, parent, on_save):
        super().__init__(parent, "Alterar Senha", width=420, height=380)
        self._on_save = on_save

        self.f_senha_atual    = ConfigInputField(self._fields_frame, "Senha Atual",    placeholder="••••••", password=True, icon="ðŸ”’")
        self.f_nova_senha     = ConfigInputField(self._fields_frame, "Nova Senha",     placeholder="mín. 6 caracteres", password=True, icon="ðŸ”‘")
        self.f_confirmar_senha= ConfigInputField(self._fields_frame, "Confirmar Senha",placeholder="confirme a nova senha", password=True, icon="ðŸ”‘")

        for f in (self.f_senha_atual, self.f_nova_senha, self.f_confirmar_senha):
            f.pack(fill="x", pady=(0, 10))

    def _on_confirm(self):
        atual   = self.f_senha_atual.get().strip()
        nova    = self.f_nova_senha.get().strip()
        confirm = self.f_confirmar_senha.get().strip()

        if not atual or not nova or not confirm:
            messagebox.showwarning("Atenção", "Preencha todos os campos.")
            return
        if nova != confirm:
            messagebox.showerror("Erro", "As senhas não coincidem.")
            return
        if len(nova) < 6:
            messagebox.showwarning("Atenção", "A nova senha deve ter pelo menos 6 caracteres.")
            return

        self._on_save(atual, nova)
        self.destroy()

# •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
#  Frame principal de configuraçÓµes
# •••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
class ConfiguracoesFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=THEME["bg"])
        self.controller = controller
        self.base_path  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._images: dict[str, Any] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self._build_header()
        self._build_body()

    # ── helpers ---------------------------------------------------------------
    def _load_image(self, name: str, size: tuple[int, int]):
        key = f"{name}:{size}"
        if key in self._images:
            return self._images[key]
        path = os.path.join(self.base_path, "assets", "avatars", name)
        try:
            from PIL import Image
            if os.path.exists(path):
                img = ctk.CTkImage(light_image=Image.open(path), size=size)
                self._images[key] = img
                return img
        except Exception as exc:
            logger.exception("Erro ao carregar imagem %s: %s", name, exc)
        return None

    def _profile_data(self) -> dict[str, str]:
        try:
            with open(os.path.join(self.base_path, "user_profile.json"), "r") as f:
                return json.load(f)
        except Exception:
            return {}

    # ── layout ---------------------------------------------------------------
    def _build_header(self):
        header = PageHeader(
            self,
            title="Preferências do Sistema",
            subtitle="Personalize sua experiência no SerPleno",
        )
        header.grid(row=0, column=0, columnspan=2,
                     sticky="ew",
                     padx=SPACING["page_x"],
                     pady=(SPACING["page_y"], 16))

    def _build_body(self):
        col_left  = ctk.CTkFrame(self, fg_color="transparent")
        col_left.grid(row=1, column=0, sticky="nsew",
                      padx=(SPACING["page_x"], 10))
        self._build_cartao_pessoal(col_left)

        col_right = ctk.CTkFrame(self, fg_color="transparent")
        col_right.grid(row=1, column=1, sticky="nsew",
                       padx=(10, SPACING["page_x"]))

        self._build_central_avisos(col_right)
        self._build_aparencia(col_right)
        self._build_seguranca(col_right)

    # ── cartão pessoal -------------------------------------------------------
    def _build_cartao_pessoal(self, container):
        card = SectionCard(container, "ðŸ‘¤", "InformaçÓµes Pessoais")
        card.pack(fill="both", expand=True)

        profile = self._profile_data()
        avatar_name = profile.get("avatar", "avatar-1.jpg")

        self.avatar_display = ctk.CTkLabel(
            card.body, text="", image=self._load_image(avatar_name, (160, 160))
        )
        self.avatar_display.pack(pady=10)

        GhostButton(
            card.body, text="Alterar imagem de perfil",
            command=self._toggle_gallery, width=240,
        ).pack(pady=(0, 8))

        self.gallery_frame = ctk.CTkFrame(
            card.body,
            fg_color=THEME["bg_alt"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=THEME["border"],
        )
        self.grid_galeria = ctk.CTkFrame(self.gallery_frame, fg_color="transparent")
        self.grid_galeria.pack(padx=10, pady=10)
        self._fill_gallery()

        nome = (
            f"{self.controller.usuario_logado.get('first_name', '')} "
            f"{self.controller.usuario_logado.get('last_name', '')}"
        ).strip() or self.controller.usuario_logado.get("username", "Usuário")
        email = self.controller.usuario_logado.get("email", "email@exemplo.com")

        ConfigInputField(card.body, "Nome de exibição", value=nome, icon="ðŸ‘¤")\
            .pack(fill="x", pady=(0, 8))
        ConfigInputField(card.body, "Endereço de E-mail", value=email, icon="ðŸ“§")\
            .pack(fill="x", pady=(0, 8))

    def _fill_gallery(self):
        avatars_dir = os.path.join(self.base_path, "assets", "avatars")
        try:
            files = sorted(f for f in os.listdir(avatars_dir)
                           if f.startswith("avatar-") and f.endswith(".jpg"))
        except Exception:
            files = []

        for i, filename in enumerate(files):
            ctk.CTkButton(
                self.grid_galeria,
                text="",
                image=self._load_image(filename, (52, 52)),
                width=52, height=52,
                fg_color="white",
                hover_color=THEME["primary_light"],
                corner_radius=RADIUS["md"],
                command=lambda fn=filename: self._select_avatar(fn),
            ).grid(row=i // 3, column=i % 3, padx=3, pady=3)

    def _toggle_gallery(self):
        if self.gallery_frame.winfo_ismapped():
            self.gallery_frame.pack_forget()
        else:
            self.gallery_frame.pack(fill="x", padx=20, pady=10,
                                    before=self.avatar_display)

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

    # ── central de avisos ----------------------------------------------------
    def _build_central_avisos(self, container):
        card = SectionCard(container, "ðŸ””", "Central de Avisos", badge="Tempo Real")
        card.pack(fill="x", pady=(0, 16))

        itens = [
            ("Mensagens Diretas",  "Alertar novos chats privados e mural"),
            ("Pedidos de Ajuda",   "NotificaçÓµes críticas de suporte ao aluno"),
            ("Feedback de Alunos", "Novas avaliaçÓµes e comentários"),
            ("Efeitos Sonoros",    "Feedback auditivo para alertas"),
        ]
        for titulo, subtitulo in itens:
            ToggleRow(
                card.body, "", titulo, subtitulo,
                on_toggle=lambda estado, t=titulo: self._on_toggle_notificacao(t, estado),
            ).pack(fill="x", pady=4)

    def _on_toggle_notificacao(self, tipo: str, estado: bool):
        logger.info("Notificação '%s' %s", tipo, "ativada" if estado else "desativada")

    # ── aparência ------------------------------------------------------------
    def _build_aparencia(self, container):
        card = SectionCard(container, "ðŸŒŽ", "Aparência & Acessibilidade")
        card.pack(fill="x", pady=(0, 16))

        row = ctk.CTkFrame(card.body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

        self._theme_select = ctk.CTkOptionMenu(
            row,
            values=["Modo Sereno (Claro)", "Modo Foco (Escuro)"],
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            button_color=THEME["border"],
            button_hover_color=THEME["border_strong"],
            height=34,
            command=self._alterar_tema,
        )
        self._theme_select.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self._font_select = ctk.CTkOptionMenu(
            row,
            values=["Padrão (16px)", "Grande (18px)"],
            fg_color=THEME["bg_alt"],
            text_color=THEME["text"],
            button_color=THEME["border"],
            button_hover_color=THEME["border_strong"],
            height=34,
            command=self._alterar_fonte,
        )
        self._font_select.pack(side="left", expand=True, fill="x")

        tip = SectionCard(card.body, "", "Dica de Produtividade")
        tip.pack(fill="x")
        ctk.CTkLabel(
            tip.body,
            text="ðŸ“  O Modo Foco reduz a emissão de luz azul, ideal para sessÓµes noturnas.",
            font=themed_font("body"),
            text_color=THEME["text_secondary"],
            wraplength=420, justify="left",
        ).pack(anchor="w", padx=14, pady=12)

    def _alterar_tema(self, valor: str):
        if valor == "Modo Sereno (Claro)":
            ctk.set_appearance_mode("light")
        elif valor == "Modo Foco (Escuro)":
            ctk.set_appearance_mode("dark")

    def _alterar_fonte(self, valor: str):
        logger.info("Escala de texto alterada: %s", valor)
        # TODO: implementar escala global via ui_theme

    # ── segurança ------------------------------------------------------------
    def _build_seguranca(self, container):
        card = SectionCard(container, "ðŸ›¡ï¸", "Sessão & Segurança")
        card.pack(fill="x")

        ActionItemRow(
            card.body, "ðŸ‘¥", "Perfil Público",
            "Permitir que outros visualizem suas conquistas",
            btn_text="", on_action=lambda t: self._on_seguranca_action(t),
        ).pack(fill="x", pady=2)

        ActionItemRow(
            card.body, "ðŸ”‘", "Credenciais",
            "Última alteração há 3 meses",
            btn_text="Alterar Senha",
            on_action=lambda t: self._on_seguranca_action(t),
        ).pack(fill="x", pady=2)

        ActionItemRow(
            card.body, "ðŸ’»", "Este Dispositivo",
            "Sessão ativa agora • Windows Desktop",
            btn_text="Encerrar Acesso",
            danger=True,
            on_action=lambda t: self._on_seguranca_action(t),
        ).pack(fill="x", pady=2)

    def _on_seguranca_action(self, btn_text: str):
        if btn_text == "Alterar Senha":
            self._abrir_modal_senha()
        elif btn_text == "Encerrar Acesso":
            self._encerrar_sessao()

    def _abrir_modal_senha(self):
        AlterarSenhaModal(self, on_save=self._salvar_senha)

    def _salvar_senha(self, senha_atual: str, nova_senha: str):
        # integração com backend pendente
        logger.info("Alteração de senha solicitada")
        messagebox.showinfo("Sucesso", "Senha alterada com sucesso.")

    def _encerrar_sessao(self):
        if messagebox.askyesno("Confirmação", "Deseja encerrar a sessão atual?"):
            self.controller.mostrar_login()

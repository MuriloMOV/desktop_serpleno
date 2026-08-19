from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from ser_pleno.domain.models.auth import UserProfile

logger = logging.getLogger(__name__)

_permission_cache: dict[int, dict[str, bool]] = {}


def clear_permission_cache(user_id: int | None = None) -> None:
    if user_id is None:
        _permission_cache.clear()
    else:
        _permission_cache.pop(user_id, None)


def get_user_profile(controller: Any) -> UserProfile | None:
    auth_service = getattr(controller, "auth_service", None)
    if not auth_service or not getattr(auth_service, "user", None):
        return None
    user_data = auth_service.user
    user_id = user_data.get("id")
    if not user_id:
        return None
    if user_id in _permission_cache:
        cached = _permission_cache[user_id]
        return UserProfile(
            id=user_id,
            user_id=user_id,
            role=cached.get("role", "visitante"),
            permissions=list(cached.get("permissions", [])),
        )
    try:
        from ser_pleno.infrastructure.db.query_helpers import fetch_one
        row = fetch_one(
            "SELECT user_id, role, permissions FROM user_profile"
            " WHERE user_id = %s AND is_active_profile = 1",
            (user_id,),
        )
        if row:
            perms_raw = row.get("permissions") or "[]"
            if isinstance(perms_raw, str):
                import json
                perms = json.loads(perms_raw)
            else:
                perms = list(perms_raw)
            profile = UserProfile(
                id=row.get("user_id", user_id),
                user_id=row.get("user_id", user_id),
                role=row.get("role", "visitante"),
                permissions=perms,
            )
            _permission_cache[user_id] = {
                "role": profile.role,
                "permissions": profile.permissions,
            }
            return profile
    except Exception as exc:
        logger.debug("Falha ao carregar perfil do usuário: %s", exc)
    return None


def has_permission(controller: Any, permission_code: str) -> bool:
    profile = get_user_profile(controller)
    if profile is None:
        return False
    return profile.has_permission(permission_code)


def can_access_screen(controller: Any, screen_name: str) -> bool:
    profile = get_user_profile(controller)
    if profile is None:
        return False
    return profile.can_access_screen(screen_name)


def require_permission(permission_code: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            controller = getattr(self, "controller", None)
            if not has_permission(controller, permission_code):
                try:
                    from ser_pleno.ui.views.base import _ErrorModal
                    _ErrorModal(
                        self.winfo_toplevel(),
                        message=f"Permissão necessária: {permission_code}",
                        title="Acesso negado",
                    )
                except Exception:
                    pass
                return None
            return fn(self, *args, **kwargs)
        return wrapper
    return decorator


ENDPOINT_PERMISSIONS: dict[str, str] = {
    "students.create": "criar_estudante",
    "students.update": "editar_estudante",
    "students.delete": "excluir_estudante",
    "schedule.create": "criar_agendamento",
    "schedule.update": "editar_agendamento",
    "schedule.delete": "excluir_agendamento",
    "screenings.create": "criar_screening",
    "screenings.update": "editar_screening",
    "screenings.delete": "excluir_screening",
    "reports.create": "gerenciar_relatorios",
    "reports.export": "exportar_dados",
    "analytics.view": "ver_analytics",
    "users.manage": "gerenciar_usuarios",
    "permissions.manage": "gerenciar_permissoes",
    "audit.view": "ver_audit_log",
    "orientations.manage": "gerenciar_orientacoes",
    "goals.manage": "gerenciar_metas",
    "wellness.manage": "gerenciar_bem_estar",
    "sharing.manage": "gerenciar_compartilhamento",
    "notifications.manage": "gerenciar_notificacoes",
}


def check_screen_access(controller: Any, screen_name: str) -> bool:
    return can_access_screen(controller, screen_name)


def require_role(role_name: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            profile = get_user_profile(getattr(self, "controller", None))
            if profile is None or profile.role != role_name:
                try:
                    from ser_pleno.ui.views.base import _ErrorModal
                    _ErrorModal(
                        self.winfo_toplevel(),
                        message=f"Permissão necessária: role {role_name}",
                        title="Acesso negado",
                    )
                except Exception:
                    pass
                return None
            return fn(self, *args, **kwargs)
        return wrapper
    return decorator


def require_admin() -> Callable:
    return require_role("admin")


def apply_rbac_to_button(button: ctk.CTkButton, controller: Any, permission_code: str) -> None:
    visible = has_permission(controller, permission_code)
    if visible:
        button.configure(state="normal")
        if not button.winfo_ismapped():
            button.pack(**{})  # no-op, just ensure it can be shown
    else:
        button.configure(state="disabled")
        if button.winfo_ismapped():
            button.pack_forget()


def apply_rbac_to_widget(widget: Any, controller: Any, permission_code: str) -> None:
    visible = has_permission(controller, permission_code)
    if visible:
        try:
            if not widget.winfo_ismapped():
                widget.pack(**{})
        except Exception:
            pass
        try:
            widget.configure(state="normal")
        except Exception:
            pass
    else:
        try:
            if widget.winfo_ismapped():
                widget.pack_forget()
        except Exception:
            pass
        try:
            widget.configure(state="disabled")
        except Exception:
            pass

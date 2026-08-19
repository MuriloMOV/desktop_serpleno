from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable

from ser_pleno.domain.models.auth import ROLE_PERMISSIONS, AuditLog

logger = logging.getLogger(__name__)


def require_role(role_name: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            profile = _get_user_profile(getattr(self, "controller", None))
            if profile is None or profile.role != role_name:
                return _deny(f"Permissão necessária: role {role_name}")
            return fn(self, *args, **kwargs)
        return wrapper
    return decorator


def require_admin() -> Callable:
    return require_role("admin")


def session_expired_handler(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        controller = getattr(self, "controller", None)
        auth_service = getattr(controller, "auth_service", None) if controller else None
        if auth_service and hasattr(auth_service, "user") and not getattr(auth_service, "user", None):
            try:
                from ser_pleno.ui.views.login import LoginView  # type: ignore
                from ser_pleno.ui.navigation import NavigationManager  # type: ignore
                NavigationManager.show("login")  # type: ignore
            except Exception:
                pass
            return None
        return fn(self, *args, **kwargs)
    return wrapper


def audit_log(action: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            controller = getattr(self, "controller", None)
            auth_service = getattr(controller, "auth_service", None) if controller else None
            user_id = getattr(auth_service, "user", {}).get("id") if auth_service else None
            ip_address = ""
            user_agent = ""
            try:
                import socket
                ip_address = socket.gethostbyname(socket.gethostname())
            except Exception:
                pass
            try:
                import platform
                user_agent = f"Desktop/{platform.system()}"
            except Exception:
                pass
            try:
                AuditLog.log_action(
                    user_id=user_id or 0,
                    action=action,
                    ip=ip_address,
                    user_agent=user_agent,
                    metadata={"args": str(args), "kwargs": str(kwargs)},
                )
            except Exception:
                pass
            return fn(self, *args, **kwargs)
        return wrapper
    return decorator


def _get_user_profile(controller: Any):
    try:
        from ser_pleno.ui.rbac import get_user_profile
        return get_user_profile(controller)
    except Exception:
        return None


def _deny(message: str) -> dict[str, Any]:
    try:
        from ser_pleno.ui.views.base import _ErrorModal  # type: ignore
    except Exception:
        pass
    try:
        from ser_pleno.utils.response import api_response  # type: ignore
        return api_response(success=False, message=message)
    except Exception:
        return {"success": False, "message": message}

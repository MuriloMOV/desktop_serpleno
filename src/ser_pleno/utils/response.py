from __future__ import annotations

from typing import Any


def api_response(data: Any = None, success: bool = True, message: str = "") -> dict[str, Any]:
    return {
        "success": success,
        "message": message,
        "data": data if data is not None else {},
    }


def api_login_required(view_func):
    def wrapper(self, *args, **kwargs):
        auth_service = getattr(self, "auth_service", None)
        if not auth_service or not getattr(auth_service, "user", None):
            return api_response(success=False, message="Login necessário")
        return view_func(self, *args, **kwargs)
    return wrapper


def paginate_queryset(items: list, page: int = 1, per_page: int = 20) -> dict[str, Any]:
    page = max(page, 1)
    per_page = max(per_page, 1)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]
    return {
        "items": page_items,
        "page": page,
        "per_page": per_page,
        "total": len(items),
        "total_pages": max(1, (len(items) + per_page - 1) // per_page),
    }


def build_pagination_response(items: list, page: int = 1, per_page: int = 20) -> dict[str, Any]:
    return api_response(data=paginate_queryset(items, page, per_page))


def validate_required_fields(fields: list[str], data: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in fields if not data.get(field)]
    if missing:
        return {
            "success": False,
            "message": f"Campos obrigatórios: {', '.join(missing)}",
            "missing_fields": missing,
        }
    return {"success": True, "message": "Campos válidos"}

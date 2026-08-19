from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def paginate_and_serialize(
    queryset: list[Any],
    per_page: int,
    serializer_class: type[Any] | None = None,
) -> dict[str, Any]:
    total = len(queryset)
    total_pages = max(1, (total + per_page - 1) // per_page) if total > 0 else 1
    page_items = queryset[:per_page]
    if serializer_class is not None:
        page_items = [serializer_class(item).data for item in page_items]
    return {
        "data": page_items,
        "pagination": {
            "page": 1,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }


def date_to_datetime_range(
    start_date: date,
    end_date: date,
) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    return start_dt, end_dt


def invalidate_related_caches(
    mutation_type: str,
    related_ids: list[int],
) -> None:
    try:
        from ser_pleno.features.dashboard.repo import invalidate_dashboard_cache

        invalidate_dashboard_cache()
    except Exception:
        pass
    try:
        from ser_pleno.utils.cache import global_cache

        if hasattr(global_cache, "invalidate_pattern"):
            for entity_id in related_ids:
                global_cache.invalidate_pattern(f"{mutation_type}:{entity_id}:*")
    except Exception:
        pass

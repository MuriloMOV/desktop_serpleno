from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SharedClinicalData:
    id: int
    data_type: str
    content: Any
    owner_id: int
    shared_with: list[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    is_active: bool = True

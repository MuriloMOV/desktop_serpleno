from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MinigameBlockLog:
    id: int
    student_id: int
    block_reason: str
    blocked_at: datetime = field(default_factory=datetime.now)
    unblocked_at: datetime | None = None
    blocked_by_id: int | None = None

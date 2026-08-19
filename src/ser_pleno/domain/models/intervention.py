from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Intervention:
    id: int
    student_id: int
    intervention_type: str
    outcome: str | None = None
    tags: dict[str, Any] = field(default_factory=dict)
    psychologist: str | None = None
    scheduled_time: datetime | None = None
    completed_time: datetime | None = None
    notes: str | None = None
    duration_minutes: int | None = None
    is_confidential: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def categorize(self) -> str:
        return self.intervention_type.lower()

    def is_follow_up_required(self) -> bool:
        return self.outcome is not None and "follow-up" in (self.outcome or "").lower()

    def get_duration(self) -> int | None:
        if self.completed_time is None or self.scheduled_time is None:
            return None
        return int((self.completed_time - self.scheduled_time).total_seconds() // 60)

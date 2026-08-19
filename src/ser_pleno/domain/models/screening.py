from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ScreeningForm:
    id: int
    name: str
    sections: list[str] = field(default_factory=list)
    score_per_section: dict[str, int] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def validate_response(self, responses: dict[str, Any]) -> bool:
        return all(section in responses for section in self.sections)


@dataclass
class Screening:
    id: int
    student_id: int
    psychologist_id: int
    form_id: int
    responses: dict[str, Any] = field(default_factory=dict)
    completed_at: datetime | None = None
    score: float | None = None
    status: str = "draft"
    priority: str = "normal"
    requires_followup: bool = False
    followup_date: datetime | None = None
    observations: str | None = None
    recommendations: str | None = None

    def calculate_score(self) -> float | None:
        if not self.responses:
            return None
        values = [v for v in self.responses.values() if isinstance(v, (int, float))]
        return sum(values) / len(values) if values else None

    def is_complete(self) -> bool:
        return self.status == "completed" and self.completed_at is not None

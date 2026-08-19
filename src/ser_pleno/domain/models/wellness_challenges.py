from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class WellnessChallenge:
    id: int
    title: str
    description: str
    category: str
    difficulty: str
    points: int
    start_date: date
    end_date: date
    target_count: int
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def is_available(self) -> bool:
        today = datetime.now().date()
        return self.is_active and self.start_date <= today <= self.end_date


@dataclass
class StudentWellnessChallenge:
    id: int
    student_id: int
    challenge_id: int
    status: str
    completed_count: int = 0
    assigned_by_id: int | None = None
    assigned_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def complete(self) -> None:
        self.status = "completed"
        self.completed_at = datetime.now()
        self.completed_count += 1

    def calculate_progress(self) -> float:
        from .wellness_challenges import WellnessChallenge
        challenge = WellnessChallenge(id=0, title="", description="", category="", difficulty="", points=0, start_date=datetime.now().date(), end_date=datetime.now().date(), target_count=1)
        if challenge.target_count == 0:
            return 0.0
        return min(100.0, max(0.0, (self.completed_count / challenge.target_count) * 100))

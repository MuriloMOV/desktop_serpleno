from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class GoalProgress:
    id: int
    goal_id: int
    date: datetime | None = None
    value: float | None = None
    notes: str | None = None
    percentage: float | None = None
    recorded_by_id: int | None = None
    recorded_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if self.date is None:
            self.date = self.recorded_at
        if self.value is None and self.percentage is not None:
            self.value = self.percentage


@dataclass
class Goal:
    id: int
    student_id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    target_date: datetime
    target_value: float
    current_value: float = 0.0
    progress_percentage: float = 0.0
    notes: str | None = None
    success_criteria: str | None = None
    created_by_id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_date: datetime | None = None

    def calculate_progress(self) -> float:
        if self.target_value == 0:
            return 0.0
        self.progress_percentage = min(100.0, max(0.0, (self.current_value / self.target_value) * 100))
        return self.progress_percentage

    def check_overdue(self) -> bool:
        return self.target_date < datetime.now() and self.status != "completed"

    def update_target(self, value: float) -> None:
        self.target_value = value
        self.progress_percentage = self.calculate_progress()

    def is_completed(self) -> bool:
        return self.status == "completed"

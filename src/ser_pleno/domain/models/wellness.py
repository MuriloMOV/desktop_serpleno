from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class MoodEntry:
    id: int
    student_id: int
    date: date
    mood_value: float
    note: str | None = None
    linked_screening_id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)

    @staticmethod
    def get_average(student_id: int) -> float:
        return 0.0


@dataclass
class WellnessCheckIn:
    id: int
    student_id: int
    date: date
    energy: float
    focus: float
    stress: float
    mood_average: float | None = None
    percentile: float | None = None
    overall_wellbeing: str | None = None
    attention_areas: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    professional_notes: str | None = None
    follow_up_needed: bool = False
    follow_up_date: date | None = None
    check_in_type: str = "standard"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None

    @staticmethod
    def generate_checkin(student_id: int) -> "WellnessCheckIn":
        return WellnessCheckIn(
            id=0,
            student_id=student_id,
            date=datetime.now().date(),
            energy=0.0,
            focus=0.0,
            stress=0.0,
        )

    def get_percentile(self) -> float | None:
        return self.percentile

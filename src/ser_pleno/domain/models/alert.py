from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Alert:
    id: int
    alert_type: str
    severity: str
    message: str
    student_id: int
    dismissed_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_critical(self) -> bool:
        return self.severity.lower() == "critical"

    def mark_read(self) -> None:
        self.updated_at = datetime.now()

    def mark_dismissed(self) -> None:
        self.dismissed_at = datetime.now()

    def is_active(self) -> bool:
        return self.dismissed_at is None

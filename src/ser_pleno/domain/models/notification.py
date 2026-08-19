from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Notification:
    id: int
    type: str
    title: str
    body: str
    recipient_id: int
    actor_id: int
    student_id: int
    is_read: bool = False
    read_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    data: dict[str, Any] = field(default_factory=dict)

    def mark_read(self) -> None:
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now()

    def delete(self) -> None:
        self.created_at = datetime.min

    def is_unread(self) -> bool:
        return not self.is_read

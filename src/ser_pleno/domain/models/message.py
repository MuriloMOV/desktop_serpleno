from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    id: int
    sender_id: int
    receiver_id: int
    content: str
    attachments: list[str] = field(default_factory=list)
    read_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def mark_as_read(self) -> None:
        if self.read_at is None:
            self.read_at = datetime.now()

    def delete_attachments(self) -> None:
        self.attachments = []

    def is_read(self) -> bool:
        return self.read_at is not None

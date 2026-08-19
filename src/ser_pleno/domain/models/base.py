from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TimestampMixin:
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CreatedAtMixin:
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ActiveMixin:
    is_active: bool = True

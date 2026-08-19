from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class Orientation:
    id: int
    title: str
    content: str
    content_type: str
    publish_at: date | None = None
    is_published: bool = False
    psychologist_id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def publish_if_ready(self) -> None:
        if self.publish_at is None or self.publish_at <= datetime.now().date():
            self.is_published = True

    def get_action_plan(self) -> list[str]:
        return []

    def is_visible_to(self, student_id: int) -> bool:
        return self.is_published


@dataclass
class OrientationAttachment:
    id: int
    orientation_id: int
    file_name: str
    file_path: str
    file_size: int
    uploaded_at: datetime = field(default_factory=datetime.now)


@dataclass
class Template:
    id: int
    name: str
    template_type: str
    content: str
    sections: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def validate_structure(self) -> bool:
        return all(section.strip() for section in self.sections)


@dataclass
class Theme:
    id: int
    name: str
    parent_id: int | None = None
    hierarchy: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def get_hierarchy(self) -> dict[str, Any]:
        return self.hierarchy

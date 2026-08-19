from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class UserProfile:
    id: int
    user_id: int
    role: str
    permissions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission_code: str) -> bool:
        return permission_code in self.permissions

    def can_access_screen(self, screen_name: str) -> bool:
        return self.has_permission(f"screen:{screen_name}")


@dataclass
class Role:
    id: int
    name: str
    permissions: list[str] = field(default_factory=list)


@dataclass
class Permission:
    id: int
    code: str
    description: str


@dataclass
class AuditLog:
    id: int
    user_id: int
    action: str
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def log_action(
        user_id: int,
        action: str,
        ip: str,
        user_agent: str,
        metadata: dict[str, Any] | None = None,
    ) -> "AuditLog":
        return AuditLog(
            id=0,
            user_id=user_id,
            action=action,
            ip_address=ip,
            user_agent=user_agent,
            metadata=metadata or {},
        )

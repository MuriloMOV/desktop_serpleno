from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


ROLE_PERMISSIONS: dict[str, list[str]] = field(default_factory=lambda: {
    "admin": [
        "acessar_tela", "editar_estudante", "excluir_estudante", "criar_estudante",
        "editar_agendamento", "excluir_agendamento", "criar_agendamento",
        "excluir_screening", "criar_screening", "editar_screening",
        "gerenciar_usuarios", "gerenciar_permissoes", "ver_audit_log",
        "gerenciar_relatorios", "exportar_dados", "ver_analytics",
        "gerenciar_orientacoes", "gerenciar_metas", "gerenciar_bem_estar",
        "gerenciar_compartilhamento", "gerenciar_notificacoes",
    ],
    "psicologo": [
        "acessar_tela", "editar_estudante", "criar_estudante",
        "editar_agendamento", "criar_agendamento",
        "criar_screening", "editar_screening",
        "gerenciar_relatorios", "ver_analytics",
        "gerenciar_orientacoes", "gerenciar_metas", "gerenciar_bem_estar",
        "gerenciar_compartilhamento",
    ],
    "coordenador": [
        "acessar_tela", "editar_estudante", "criar_estudante",
        "editar_agendamento", "criar_agendamento",
        "criar_screening", "editar_screening",
        "gerenciar_relatorios", "ver_analytics",
        "gerenciar_orientacoes", "gerenciar_metas", "gerenciar_bem_estar",
        "gerenciar_compartilhamento", "exportar_dados",
    ],
    "analista": [
        "acessar_tela", "ver_analytics", "exportar_dados", "ver_audit_log",
    ],
    "suporte": [
        "acessar_tela", "editar_estudante", "criar_estudante",
        "editar_agendamento", "criar_agendamento",
    ],
    "visitante": [
        "acessar_tela",
    ],
})


@dataclass
class UserProfile:
    id: int
    user_id: int
    role: str
    permissions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def has_permission(self, permission_code: str) -> bool:
        if not self.permissions:
            role_perms = ROLE_PERMISSIONS.get(self.role, [])
            return permission_code in role_perms
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

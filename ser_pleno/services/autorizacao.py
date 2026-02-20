"""
Sistema de Autorização para o Desktop CustomTkinter
Implementa controle de acesso baseado em roles (RBAC)
"""
import logging
from typing import Optional, Dict, Any, List, Callable, Set
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Roles disponíveis no sistema"""
    ADMIN = "admin"
    PSICOLOGO = "psicologo"
    COORDENADOR = "coordenador"
    ESTUDANTE = "estudante"
    VISITANTE = "visitante"


class Permission(Enum):
    """Permissões disponíveis no sistema"""
    # Estudantes
    VIEW_STUDENTS = "view_students"
    CREATE_STUDENT = "create_student"
    EDIT_STUDENT = "edit_student"
    DELETE_STUDENT = "delete_student"
    EXPORT_STUDENTS = "export_students"
    IMPORT_STUDENTS = "import_students"
    
    # Agendamentos
    VIEW_APPOINTMENTS = "view_appointments"
    CREATE_APPOINTMENT = "create_appointment"
    EDIT_APPOINTMENT = "edit_appointment"
    DELETE_APPOINTMENT = "delete_appointment"
    
    # Orientações
    VIEW_ORIENTATIONS = "view_orientations"
    CREATE_ORIENTATION = "create_orientation"
    EDIT_ORIENTATION = "edit_orientation"
    DELETE_ORIENTATION = "delete_orientation"
    
    # Relatórios
    VIEW_REPORTS = "view_reports"
    CREATE_REPORT = "create_report"
    DELETE_REPORT = "delete_report"
    EXPORT_REPORTS = "export_reports"
    
    # Triagens
    VIEW_SCREENINGS = "view_screenings"
    CREATE_SCREENING = "create_screening"
    EDIT_SCREENING = "edit_screening"
    
    # Bem-estar
    VIEW_WELLNESS = "view_wellness"
    EDIT_WELLNESS = "edit_wellness"
    
    # Comunicação
    VIEW_MESSAGES = "view_messages"
    SEND_MESSAGES = "send_messages"
    MANAGE_BOARD = "manage_board"
    
    # Sistema
    VIEW_SETTINGS = "view_settings"
    EDIT_SETTINGS = "edit_settings"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_BACKUP = "manage_backup"
    VIEW_MONITORING = "view_monitoring"


# Mapeamento de Role -> Permissões
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        # Admin tem todas as permissões
        Permission.VIEW_STUDENTS, Permission.CREATE_STUDENT, Permission.EDIT_STUDENT,
        Permission.DELETE_STUDENT, Permission.EXPORT_STUDENTS, Permission.IMPORT_STUDENTS,
        Permission.VIEW_APPOINTMENTS, Permission.CREATE_APPOINTMENT, Permission.EDIT_APPOINTMENT,
        Permission.DELETE_APPOINTMENT,
        Permission.VIEW_ORIENTATIONS, Permission.CREATE_ORIENTATION, Permission.EDIT_ORIENTATION,
        Permission.DELETE_ORIENTATION,
        Permission.VIEW_REPORTS, Permission.CREATE_REPORT, Permission.DELETE_REPORT,
        Permission.EXPORT_REPORTS,
        Permission.VIEW_SCREENINGS, Permission.CREATE_SCREENING, Permission.EDIT_SCREENING,
        Permission.VIEW_WELLNESS, Permission.EDIT_WELLNESS,
        Permission.VIEW_MESSAGES, Permission.SEND_MESSAGES, Permission.MANAGE_BOARD,
        Permission.VIEW_SETTINGS, Permission.EDIT_SETTINGS, Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT_LOG, Permission.MANAGE_BACKUP, Permission.VIEW_MONITORING,
    },
    UserRole.PSICOLOGO: {
        # Psicólogo pode gerenciar atendimentos e orientações
        Permission.VIEW_STUDENTS, Permission.CREATE_STUDENT, Permission.EDIT_STUDENT,
        Permission.EXPORT_STUDENTS,
        Permission.VIEW_APPOINTMENTS, Permission.CREATE_APPOINTMENT, Permission.EDIT_APPOINTMENT,
        Permission.DELETE_APPOINTMENT,
        Permission.VIEW_ORIENTATIONS, Permission.CREATE_ORIENTATION, Permission.EDIT_ORIENTATION,
        Permission.DELETE_ORIENTATION,
        Permission.VIEW_REPORTS, Permission.CREATE_REPORT, Permission.EXPORT_REPORTS,
        Permission.VIEW_SCREENINGS, Permission.CREATE_SCREENING, Permission.EDIT_SCREENING,
        Permission.VIEW_WELLNESS, Permission.EDIT_WELLNESS,
        Permission.VIEW_MESSAGES, Permission.SEND_MESSAGES,
        Permission.VIEW_SETTINGS,
    },
    UserRole.COORDENADOR: {
        # Coordenador pode visualizar e gerenciar estudantes
        Permission.VIEW_STUDENTS, Permission.CREATE_STUDENT, Permission.EDIT_STUDENT,
        Permission.EXPORT_STUDENTS, Permission.IMPORT_STUDENTS,
        Permission.VIEW_APPOINTMENTS, Permission.CREATE_APPOINTMENT, Permission.EDIT_APPOINTMENT,
        Permission.VIEW_ORIENTATIONS, Permission.VIEW_REPORTS, Permission.EXPORT_REPORTS,
        Permission.VIEW_SCREENINGS,
        Permission.VIEW_MESSAGES, Permission.SEND_MESSAGES, Permission.MANAGE_BOARD,
        Permission.VIEW_SETTINGS,
    },
    UserRole.ESTUDANTE: {
        # Estudante tem acesso limitado
        Permission.VIEW_APPOINTMENTS,
        Permission.VIEW_WELLNESS, Permission.EDIT_WELLNESS,
        Permission.VIEW_MESSAGES, Permission.SEND_MESSAGES,
    },
    UserRole.VISITANTE: {
        # Visitante apenas visualiza
        Permission.VIEW_STUDENTS,
        Permission.VIEW_APPOINTMENTS,
        Permission.VIEW_MESSAGES,
    },
}


@dataclass
class User:
    """Representa um usuário do sistema"""
    id: int
    username: str
    email: str
    role: UserRole
    name: Optional[str] = None
    is_active: bool = True
    permissions: Set[Permission] = field(default_factory=set)
    
    def __post_init__(self):
        # Carrega permissões do role
        if not self.permissions:
            self.permissions = ROLE_PERMISSIONS.get(self.role, set()).copy()
    
    def has_permission(self, permission: Permission) -> bool:
        """Verifica se o usuário tem uma permissão específica"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Verifica se o usuário tem qualquer uma das permissões"""
        return any(p in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Verifica se o usuário tem todas as permissões"""
        return all(p in self.permissions for p in permissions)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "name": self.name,
            "is_active": self.is_active,
            "permissions": [p.value for p in self.permissions],
        }


class AuthorizationError(Exception):
    """Exceção lançada quando acesso é negado"""
    def __init__(self, message: str, permission: Optional[Permission] = None):
        super().__init__(message)
        self.permission = permission


class AuthorizationService:
    """Serviço de autorização e controle de acesso"""
    
    def __init__(self):
        self._current_user: Optional[User] = None
        self._permission_overrides: Dict[int, Set[Permission]] = {}
    
    def set_current_user(self, user: Optional[User]):
        """Define o usuário atual"""
        self._current_user = user
        if user:
            logger.info(f"Usuário definido: {user.username} (role: {user.role.value})")
    
    def get_current_user(self) -> Optional[User]:
        """Retorna o usuário atual"""
        return self._current_user
    
    def is_authenticated(self) -> bool:
        """Verifica se há um usuário autenticado"""
        return self._current_user is not None and self._current_user.is_active
    
    def is_admin(self) -> bool:
        """Verifica se o usuário atual é admin"""
        return self._current_user is not None and self._current_user.role == UserRole.ADMIN
    
    def has_role(self, role: UserRole) -> bool:
        """Verifica se o usuário atual tem um role específico"""
        return self._current_user is not None and self._current_user.role == role
    
    def has_any_role(self, roles: List[UserRole]) -> bool:
        """Verifica se o usuário atual tem qualquer um dos roles"""
        return self._current_user is not None and self._current_user.role in roles
    
    def check_permission(self, permission: Permission) -> bool:
        """Verifica se o usuário atual tem uma permissão"""
        if not self.is_authenticated():
            return False
        
        # Admin sempre tem permissão
        if self._current_user.role == UserRole.ADMIN:
            return True
        
        # Verifica permissões customizadas
        user_id = self._current_user.id
        if user_id in self._permission_overrides:
            if permission in self._permission_overrides[user_id]:
                return True
        
        return self._current_user.has_permission(permission)
    
    def require_permission(self, permission: Permission) -> None:
        """
        Exige que o usuário tenha uma permissão.
        Lança AuthorizationError se não tiver.
        """
        if not self.is_authenticated():
            raise AuthorizationError(
                "Você precisa estar autenticado para acessar este recurso",
                permission
            )
        
        if not self.check_permission(permission):
            raise AuthorizationError(
                f"Você não tem permissão para: {permission.value}",
                permission
            )
    
    def require_any_permission(self, permissions: List[Permission]) -> None:
        """Exige que o usuário tenha qualquer uma das permissões"""
        if not self.is_authenticated():
            raise AuthorizationError(
                "Você precisa estar autenticado para acessar este recurso"
            )
        
        if not any(self.check_permission(p) for p in permissions):
            raise AuthorizationError(
                f"Você não tem nenhuma das permissões necessárias"
            )
    
    def grant_permission(self, user_id: int, permission: Permission) -> None:
        """Concede uma permissão extra a um usuário"""
        if user_id not in self._permission_overrides:
            self._permission_overrides[user_id] = set()
        self._permission_overrides[user_id].add(permission)
        logger.info(f"Permissão {permission.value} concedida ao usuário {user_id}")
    
    def revoke_permission(self, user_id: int, permission: Permission) -> None:
        """Revoga uma permissão extra de um usuário"""
        if user_id in self._permission_overrides:
            self._permission_overrides[user_id].discard(permission)
            logger.info(f"Permissão {permission.value} revogada do usuário {user_id}")
    
    def get_user_permissions(self) -> List[str]:
        """Retorna lista de permissões do usuário atual"""
        if not self._current_user:
            return []
        return [p.value for p in self._current_user.permissions]
    
    def can_access_screen(self, screen_name: str) -> bool:
        """Verifica se o usuário pode acessar uma tela específica"""
        SCREEN_PERMISSIONS: Dict[str, List[Permission]] = {
            "estudantes": [Permission.VIEW_STUDENTS],
            "agenda": [Permission.VIEW_APPOINTMENTS],
            "orientacoes": [Permission.VIEW_ORIENTATIONS],
            "relatorios": [Permission.VIEW_REPORTS],
            "analise_triagem": [Permission.VIEW_SCREENINGS],
            "bem_estar": [Permission.VIEW_WELLNESS],
            "comunicacao_interna": [Permission.VIEW_MESSAGES],
            "quadro_avisos": [Permission.VIEW_MESSAGES],
            "configuracoes": [Permission.VIEW_SETTINGS],
        }
        
        required = SCREEN_PERMISSIONS.get(screen_name, [])
        if not required:
            return True  # Tela sem restrição
        
        return any(self.check_permission(p) for p in required)
    
    def log_access_denied(self, resource: str, permission: Permission) -> None:
        """Registra tentativa de acesso negado"""
        user_info = self._current_user.username if self._current_user else "anônimo"
        logger.warning(
            f"ACESSO NEGADO: Usuário '{user_info}' tentou acessar '{resource}' "
            f"(permissão necessária: {permission.value})"
        )


def require_permission(permission: Permission):
    """
    Decorator para exigir permissão em métodos.
    
    Usage:
        @require_permission(Permission.CREATE_STUDENT)
        def criar_estudante(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Tenta obter o serviço de autorização
            auth_service = get_authorization_service()
            
            if not auth_service.is_authenticated():
                from tkinter import messagebox
                messagebox.showerror("Acesso Negado", "Você precisa estar autenticado.")
                return None
            
            if not auth_service.check_permission(permission):
                auth_service.log_access_denied(func.__name__, permission)
                from tkinter import messagebox
                messagebox.showerror(
                    "Acesso Negado",
                    f"Você não tem permissão para realizar esta ação.\n"
                    f"Permissão necessária: {permission.value}"
                )
                return None
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_role(roles: List[UserRole]):
    """
    Decorator para exigir role específico em métodos.
    
    Usage:
        @require_role([UserRole.ADMIN, UserRole.PSICOLOGO])
        def metodo_restrito(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            auth_service = get_authorization_service()
            
            if not auth_service.is_authenticated():
                from tkinter import messagebox
                messagebox.showerror("Acesso Negado", "Você precisa estar autenticado.")
                return None
            
            if not auth_service.has_any_role(roles):
                from tkinter import messagebox
                messagebox.showerror(
                    "Acesso Negado",
                    f"Esta ação requer um dos seguintes perfis: "
                    f"{', '.join(r.value for r in roles)}"
                )
                return None
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_admin(func: Callable) -> Callable:
    """
    Decorator para exigir que o usuário seja admin.
    
    Usage:
        @require_admin
        def excluir_todos_dados(self):
            ...
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        auth_service = get_authorization_service()
        
        if not auth_service.is_admin():
            from tkinter import messagebox
            messagebox.showerror(
                "Acesso Negado",
                "Esta ação requer privilégios de administrador."
            )
            return None
        
        return func(self, *args, **kwargs)
    return wrapper


# Instância global do serviço de autorização
_authorization_service: Optional[AuthorizationService] = None


def get_authorization_service() -> AuthorizationService:
    """Retorna a instância global do serviço de autorização"""
    global _authorization_service
    if _authorization_service is None:
        _authorization_service = AuthorizationService()
    return _authorization_service


def init_authorization(user_data: Optional[Dict[str, Any]] = None) -> AuthorizationService:
    """
    Inicializa o serviço de autorização com dados do usuário.
    
    Args:
        user_data: Dict com dados do usuário logado
            - id: ID do usuário
            - username: Nome de usuário
            - email: Email
            - role: Role do usuário (string)
            - name: Nome completo (opcional)
    
    Returns:
        AuthorizationService configurado
    """
    service = get_authorization_service()
    
    if user_data:
        try:
            role_str = user_data.get('role', 'visitante')
            role = UserRole(role_str.lower()) if role_str else UserRole.VISITANTE
            
            user = User(
                id=user_data.get('id', 0),
                username=user_data.get('username', ''),
                email=user_data.get('email', ''),
                role=role,
                name=user_data.get('name'),
                is_active=user_data.get('is_active', True),
            )
            service.set_current_user(user)
        except ValueError as e:
            logger.error(f"Erro ao criar usuário: {e}")
            service.set_current_user(None)
    else:
        service.set_current_user(None)
    
    return service


def create_user_from_db(user_id: int) -> Optional[User]:
    """
    Cria um objeto User a partir dos dados do banco.
    
    Args:
        user_id: ID do usuário no banco
    
    Returns:
        User ou None se não encontrado
    """
    try:
        from config.db_config import get_db_connection
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT u.id, u.username, u.email, u.first_name, u.last_name, u.is_active,
                   COALESCE(p.role, 'visitante') as role
            FROM auth_user u
            LEFT JOIN user_profile p ON u.id = p.user_id
            WHERE u.id = %s
        """, (user_id,))
        
        row = cursor.fetchone()
        connection.close()
        
        if row:
            role_str = row.get('role', 'visitante')
            try:
                role = UserRole(role_str.lower())
            except ValueError:
                role = UserRole.VISITANTE
            
            return User(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                role=role,
                name=f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                is_active=bool(row.get('is_active', True)),
            )
        
        return None
        
    except Exception as e:
        logger.error(f"Erro ao criar usuário do banco: {e}")
        return None

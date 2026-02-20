"""
Services - Serviços do Desktop SerPleno

Este módulo contém todos os serviços da aplicação, organizados por responsabilidade:
- Autenticação e Autorização
- CRUD de entidades (estudantes, agendamentos, orientações)
- Importação e Exportação de dados
- Backup e Restore
- Auditoria e Monitoramento
- Validações
"""

# Autenticação
from services.autenticacao import ServicoAutenticacao

# Autorização
from services.autorizacao import (
    UserRole,
    Permission,
    User,
    AuthorizationService,
    AuthorizationError,
    get_authorization_service,
    init_authorization,
    require_permission,
    require_role,
    require_admin,
    create_user_from_db
)

# Estudantes
from services.estudantes import ServicoEstudante

# Agendamentos
from services.agendamentos import ServicoAgendamento

# Orientações
from services.orientacoes import ServicoOrientacoes

# Relatórios
from services.relatorios import ServicoRelatorio

# Bem-estar
from services.bem_estar import ServicoBemEstar

# Comunicação
from services.comunicacao import ServicoComunicacao

# Mural
from services.mural import ServicoMural

# Dashboard
from services.dashboard import ServicoDashboard, DashboardService

# Triagem
from services.triagem import ServicoTriagem

# Configurações
from services.configuracoes import ServicoConfiguracoes

# API
from services.api import ClienteAPI, api, get_auth_service, set_auth_service

# Sincronização
from services.sync_service import SyncService, SyncQueue, get_sync_service, queue_sync

# Importação
from services.importacao import (
    ServicoImportacao,
    servico_importacao,
    ImportStatus,
    ImportResult,
    ImportReport,
    ColumnMapping
)

# Backup
from services.backup import (
    BackupService,
    servico_backup,
    BackupType,
    BackupStatus,
    BackupInfo,
    RestoreResult
)

# Auditoria
from services.auditoria import (
    AuditService,
    AuditAction,
    AuditEntry,
    AuditedModel,
    get_audit_service,
    init_audit
)

# Monitoramento
from services.monitoramento import (
    MonitoringService,
    HealthStatus,
    HealthCheckResult,
    MetricValue,
    AlertSeverity,
    Alert,
    get_monitoring_service
)

# Validações
from services.validacoes import (
    ValidationService,
    ValidationResult,
    ValidationError,
    ValidationSeverity,
    Validator,
    RequiredValidator,
    LengthValidator,
    EmailValidator,
    PhoneValidator,
    CPFValidator,
    DateValidator,
    IntegerValidator,
    ChoiceValidator,
    RegexValidator,
    get_validation_service,
    validate_required,
    validate_email,
    validate_phone,
    validate_cpf,
    validate_length
)

# Compatibilidade (wrappers para testes)
from services.students import StudentService
from services.auth import AuthService


__all__ = [
    # Autenticação
    'ServicoAutenticacao',
    
    # Autorização
    'UserRole',
    'Permission',
    'User',
    'AuthorizationService',
    'AuthorizationError',
    'get_authorization_service',
    'init_authorization',
    'require_permission',
    'require_role',
    'require_admin',
    'create_user_from_db',
    
    # Estudantes
    'ServicoEstudante',
    
    # Agendamentos
    'ServicoAgendamento',
    
    # Orientações
    'ServicoOrientacoes',
    
    # Relatórios
    'ServicoRelatorio',
    
    # Bem-estar
    'ServicoBemEstar',
    
    # Comunicação
    'ServicoComunicacao',
    
    # Mural
    'ServicoMural',
    
    # Dashboard
    'ServicoDashboard',
    'DashboardService',
    
    # Triagem
    'ServicoTriagem',
    
    # Configurações
    'ServicoConfiguracoes',
    
    # API
    'ClienteAPI',
    'api',
    'get_auth_service',
    'set_auth_service',
    
    # Sincronização
    'SyncService',
    'SyncQueue',
    'get_sync_service',
    'queue_sync',
    
    # Importação
    'ServicoImportacao',
    'servico_importacao',
    'ImportStatus',
    'ImportResult',
    'ImportReport',
    'ColumnMapping',
    
    # Backup
    'BackupService',
    'servico_backup',
    'BackupType',
    'BackupStatus',
    'BackupInfo',
    'RestoreResult',
    
    # Auditoria
    'AuditService',
    'AuditAction',
    'AuditEntry',
    'AuditedModel',
    'get_audit_service',
    'init_audit',
    
    # Monitoramento
    'MonitoringService',
    'HealthStatus',
    'HealthCheckResult',
    'MetricValue',
    'AlertSeverity',
    'Alert',
    'get_monitoring_service',
    
    # Validações
    'ValidationService',
    'ValidationResult',
    'ValidationError',
    'ValidationSeverity',
    'Validator',
    'RequiredValidator',
    'LengthValidator',
    'EmailValidator',
    'PhoneValidator',
    'CPFValidator',
    'DateValidator',
    'IntegerValidator',
    'ChoiceValidator',
    'RegexValidator',
    'get_validation_service',
    'validate_required',
    'validate_email',
    'validate_phone',
    'validate_cpf',
    'validate_length',
    
    # Compatibilidade
    'StudentService',
    'AuthService',
]

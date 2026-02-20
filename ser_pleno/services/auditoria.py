"""
Serviço de Auditoria para o Desktop CustomTkinter
Implementa rastreamento de alterações e log de auditoria
"""
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager

from config.db_config import get_db_connection

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Tipos de ações auditáveis"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS = "ACCESS"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    BACKUP = "BACKUP"
    RESTORE = "RESTORE"


@dataclass
class AuditEntry:
    """Representa uma entrada de auditoria"""
    id: Optional[int] = None
    table_name: str = ""
    record_id: Optional[int] = None
    action: AuditAction = AuditAction.CREATE
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    username: str = ""
    ip_address: str = ""
    user_agent: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "action": self.action.value,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "details": self.details,
        }


class AuditService:
    """Serviço para gerenciar auditoria do sistema"""
    
    # Tabelas a serem auditadas
    AUDITED_TABLES = [
        "aluno",
        "agendamento",
        "desktop_orientation",
        "desktop_goal",
        "desktop_note",
        "desktop_screening",
        "desktop_report",
        "desktop_alert",
        "desktop_message",
    ]
    
    def __init__(self):
        self._current_user_id: Optional[int] = None
        self._current_username: str = ""
        self._enabled: bool = True
    
    def set_current_user(self, user_id: Optional[int], username: str = ""):
        """Define o usuário atual para auditoria"""
        self._current_user_id = user_id
        self._current_username = username
    
    def enable(self):
        """Habilita auditoria"""
        self._enabled = True
    
    def disable(self):
        """Desabilita auditoria temporariamente"""
        self._enabled = False
    
    @contextmanager
    def skip_audit(self):
        """Context manager para pular auditoria temporariamente"""
        was_enabled = self._enabled
        self._enabled = False
        try:
            yield
        finally:
            self._enabled = was_enabled
    
    def log_action(
        self,
        action: AuditAction,
        table_name: str,
        record_id: Optional[int] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        details: Optional[str] = None
    ) -> Optional[int]:
        """
        Registra uma ação no log de auditoria.
        
        Args:
            action: Tipo de ação
            table_name: Nome da tabela afetada
            record_id: ID do registro afetado
            old_values: Valores anteriores (para UPDATE/DELETE)
            new_values: Novos valores (para CREATE/UPDATE)
            details: Detalhes adicionais
            
        Returns:
            ID da entrada de auditoria ou None se falhar
        """
        if not self._enabled:
            return None
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Verifica se tabela de auditoria existe
            self._ensure_audit_table_exists(cursor)
            
            query = """
                INSERT INTO audit_log 
                (table_name, record_id, action, old_values, new_values, user_id, username, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                table_name,
                record_id,
                action.value,
                json.dumps(old_values, default=str) if old_values else None,
                json.dumps(new_values, default=str) if new_values else None,
                self._current_user_id,
                self._current_username,
                details
            ))
            
            connection.commit()
            audit_id = cursor.lastrowid
            connection.close()
            
            logger.debug(
                f"Auditoria: {action.value} em {table_name}#{record_id} "
                f"por usuário {self._current_user_id}"
            )
            
            return audit_id
            
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {e}")
            return None
    
    def log_create(self, table_name: str, record_id: int, new_values: Dict[str, Any]) -> Optional[int]:
        """Registra criação de registro"""
        return self.log_action(
            action=AuditAction.CREATE,
            table_name=table_name,
            record_id=record_id,
            new_values=new_values
        )
    
    def log_update(
        self,
        table_name: str,
        record_id: int,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any]
    ) -> Optional[int]:
        """Registra atualização de registro"""
        return self.log_action(
            action=AuditAction.UPDATE,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values,
            new_values=new_values
        )
    
    def log_delete(self, table_name: str, record_id: int, old_values: Dict[str, Any]) -> Optional[int]:
        """Registra exclusão de registro"""
        return self.log_action(
            action=AuditAction.DELETE,
            table_name=table_name,
            record_id=record_id,
            old_values=old_values
        )
    
    def log_login(self, user_id: int, username: str, success: bool = True) -> Optional[int]:
        """Registra tentativa de login"""
        return self.log_action(
            action=AuditAction.LOGIN,
            table_name="auth_user",
            record_id=user_id,
            details=f"Login {'bem-sucedido' if success else 'falhou'}"
        )
    
    def log_logout(self, user_id: int, username: str) -> Optional[int]:
        """Registra logout"""
        return self.log_action(
            action=AuditAction.LOGOUT,
            table_name="auth_user",
            record_id=user_id,
            details="Logout"
        )
    
    def log_access(self, resource: str, allowed: bool = True) -> Optional[int]:
        """Registra acesso a recurso"""
        return self.log_action(
            action=AuditAction.ACCESS,
            table_name="system",
            details=f"Acesso {'permitido' if allowed else 'negado'} a: {resource}"
        )
    
    def log_export(self, table_name: str, record_count: int, format: str = "csv") -> Optional[int]:
        """Registra exportação de dados"""
        return self.log_action(
            action=AuditAction.EXPORT,
            table_name=table_name,
            details=f"Exportados {record_count} registros em formato {format}"
        )
    
    def log_import(self, table_name: str, record_count: int, success_count: int) -> Optional[int]:
        """Registra importação de dados"""
        return self.log_action(
            action=AuditAction.IMPORT,
            table_name=table_name,
            details=f"Importados {success_count}/{record_count} registros"
        )
    
    def get_history(
        self,
        table_name: str,
        record_id: Optional[int] = None,
        user_id: Optional[int] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEntry]:
        """
        Obtém histórico de auditoria.
        
        Args:
            table_name: Filtrar por tabela
            record_id: Filtrar por ID do registro
            user_id: Filtrar por ID do usuário
            action: Filtrar por tipo de ação
            start_date: Data inicial
            end_date: Data final
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de AuditEntry
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Constrói query dinamicamente
            query = "SELECT * FROM audit_log WHERE 1=1"
            params: List[Any] = []
            
            if table_name:
                query += " AND table_name = %s"
                params.append(table_name)
            
            if record_id is not None:
                query += " AND record_id = %s"
                params.append(record_id)
            
            if user_id is not None:
                query += " AND user_id = %s"
                params.append(user_id)
            
            if action:
                query += " AND action = %s"
                params.append(action.value)
            
            if start_date:
                query += " AND created_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND created_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            connection.close()
            
            entries = []
            for row in rows:
                entries.append(self._row_to_entry(row))
            
            return entries
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def get_record_history(self, table_name: str, record_id: int) -> List[AuditEntry]:
        """
        Obtém histórico completo de um registro específico.
        
        Args:
            table_name: Nome da tabela
            record_id: ID do registro
            
        Returns:
            Lista de AuditEntry ordenada por data
        """
        return self.get_history(table_name=table_name, record_id=record_id, limit=1000)
    
    def get_user_activity(
        self,
        user_id: int,
        days: int = 30
    ) -> List[AuditEntry]:
        """
        Obtém atividade de um usuário nos últimos N dias.
        
        Args:
            user_id: ID do usuário
            days: Número de dias para olhar atrás
            
        Returns:
            Lista de AuditEntry
        """
        start_date = datetime.now() - timedelta(days=days)
        return self.get_history(user_id=user_id, start_date=start_date, limit=500)
    
    def get_recent_activity(self, limit: int = 50) -> List[AuditEntry]:
        """
        Obtém atividade recente do sistema.
        
        Args:
            limit: Número máximo de entradas
            
        Returns:
            Lista de AuditEntry
        """
        return self.get_history(limit=limit)
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Obtém estatísticas de auditoria.
        
        Args:
            days: Período em dias
            
        Returns:
            Dict com estatísticas
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Total de ações por tipo
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM audit_log
                WHERE created_at >= %s
                GROUP BY action
                ORDER BY count DESC
            """, (start_date,))
            actions_by_type = {row['action']: row['count'] for row in cursor.fetchall()}
            
            # Total de ações por tabela
            cursor.execute("""
                SELECT table_name, COUNT(*) as count
                FROM audit_log
                WHERE created_at >= %s
                GROUP BY table_name
                ORDER BY count DESC
                LIMIT 10
            """, (start_date,))
            actions_by_table = {row['table_name']: row['count'] for row in cursor.fetchall()}
            
            # Usuários mais ativos
            cursor.execute("""
                SELECT username, COUNT(*) as count
                FROM audit_log
                WHERE created_at >= %s AND username != ''
                GROUP BY username
                ORDER BY count DESC
                LIMIT 10
            """, (start_date,))
            active_users = {row['username']: row['count'] for row in cursor.fetchall()}
            
            # Total de ações no período
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM audit_log
                WHERE created_at >= %s
            """, (start_date,))
            total = cursor.fetchone()
            total_actions = total['total'] if total else 0
            
            connection.close()
            
            return {
                "period_days": days,
                "total_actions": total_actions,
                "actions_by_type": actions_by_type,
                "actions_by_table": actions_by_table,
                "active_users": active_users,
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                "period_days": days,
                "total_actions": 0,
                "actions_by_type": {},
                "actions_by_table": {},
                "active_users": {},
            }
    
    def cleanup_old_logs(self, keep_days: int = 365) -> int:
        """
        Remove logs antigos de auditoria.
        
        Args:
            keep_days: Manter logs dos últimos N dias
            
        Returns:
            Número de registros removidos
        """
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            cursor.execute(
                "DELETE FROM audit_log WHERE created_at < %s",
                (cutoff_date,)
            )
            
            deleted = cursor.rowcount
            connection.commit()
            connection.close()
            
            logger.info(f"Limpeza de auditoria: {deleted} registros removidos")
            return deleted
            
        except Exception as e:
            logger.error(f"Erro na limpeza de auditoria: {e}")
            return 0
    
    def export_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = "json"
    ) -> str:
        """
        Exporta logs de auditoria.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            format: Formato de exportação (json, csv)
            
        Returns:
            String com dados exportados
        """
        entries = self.get_history(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if format == "json":
            return json.dumps(
                [e.to_dict() for e in entries],
                ensure_ascii=False,
                indent=2,
                default=str
            )
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "id", "table_name", "record_id", "action",
                "user_id", "username", "created_at", "details"
            ])
            
            # Data
            for entry in entries:
                writer.writerow([
                    entry.id,
                    entry.table_name,
                    entry.record_id,
                    entry.action.value,
                    entry.user_id,
                    entry.username,
                    entry.created_at.isoformat() if entry.created_at else "",
                    entry.details
                ])
            
            return output.getvalue()
        
        return ""
    
    def _ensure_audit_table_exists(self, cursor):
        """Garante que a tabela de auditoria existe"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                table_name VARCHAR(100) NOT NULL,
                record_id BIGINT,
                action VARCHAR(20) NOT NULL,
                old_values JSON,
                new_values JSON,
                user_id INT,
                username VARCHAR(150),
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                details TEXT,
                created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                INDEX idx_table_record (table_name, record_id),
                INDEX idx_user (user_id),
                INDEX idx_action (action),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    
    def _row_to_entry(self, row: Dict[str, Any]) -> AuditEntry:
        """Converte linha do banco para AuditEntry"""
        return AuditEntry(
            id=row.get('id'),
            table_name=row.get('table_name', ''),
            record_id=row.get('record_id'),
            action=AuditAction(row.get('action', 'CREATE')),
            old_values=json.loads(row['old_values']) if row.get('old_values') else None,
            new_values=json.loads(row['new_values']) if row.get('new_values') else None,
            user_id=row.get('user_id'),
            username=row.get('username', ''),
            ip_address=row.get('ip_address', ''),
            user_agent=row.get('user_agent', ''),
            created_at=row.get('created_at'),
            details=row.get('details'),
        )


class AuditedModel:
    """
    Mixin para adicionar auditoria automática a modelos.
    
    Usage:
        class Estudante(AuditedModel):
            table_name = "aluno"
            
            def save(self):
                if self.id:
                    old = self.get_old_values()
                    super().save()
                    self.audit_update(old, self.to_dict())
                else:
                    super().save()
                    self.audit_create(self.to_dict())
    """
    
    table_name: str = ""
    _audit_service: Optional[AuditService] = None
    
    @property
    def audit_service(self) -> AuditService:
        if self._audit_service is None:
            self._audit_service = get_audit_service()
        return self._audit_service
    
    def audit_create(self, values: Dict[str, Any]):
        """Registra criação do registro"""
        self.audit_service.log_create(
            table_name=self.table_name,
            record_id=getattr(self, 'id', None),
            new_values=values
        )
    
    def audit_update(self, old_values: Dict[str, Any], new_values: Dict[str, Any]):
        """Registra atualização do registro"""
        self.audit_service.log_update(
            table_name=self.table_name,
            record_id=getattr(self, 'id', None),
            old_values=old_values,
            new_values=new_values
        )
    
    def audit_delete(self, old_values: Dict[str, Any]):
        """Registra exclusão do registro"""
        self.audit_service.log_delete(
            table_name=self.table_name,
            record_id=getattr(self, 'id', None),
            old_values=old_values
        )


# Instância global para fácil acesso
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Retorna a instância global do serviço de auditoria"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service


def init_audit(user_id: Optional[int] = None, username: str = "") -> AuditService:
    """Inicializa o serviço de auditoria com dados do usuário"""
    service = get_audit_service()
    service.set_current_user(user_id, username)
    return service

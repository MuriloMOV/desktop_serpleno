"""
Serviço de Backup e Restore para o Desktop CustomTkinter
Implementa backup completo e incremental do banco de dados e arquivos
"""
import logging
import os
import gzip
import json
import shutil
import hashlib
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import subprocess

from config.db_config import get_db_connection
from config.settings import settings

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Tipo de backup"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DATA_ONLY = "data_only"


class BackupStatus(Enum):
    """Status do backup"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackupInfo:
    """Informações sobre um backup"""
    id: str
    type: BackupType
    created_at: datetime
    file_path: str
    file_size: int
    checksum: str
    status: BackupStatus
    tables_included: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "created_at": self.created_at.isoformat(),
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_size_human": self._format_size(self.file_size),
            "checksum": self.checksum,
            "status": self.status.value,
            "tables_included": self.tables_included,
            "error_message": self.error_message,
        }
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Formata tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"


@dataclass
class RestoreResult:
    """Resultado de uma operação de restore"""
    success: bool
    backup_id: str
    restored_at: datetime
    tables_restored: List[str] = field(default_factory=list)
    records_restored: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "backup_id": self.backup_id,
            "restored_at": self.restored_at.isoformat(),
            "tables_restored": self.tables_restored,
            "records_restored": self.records_restored,
            "errors": self.errors,
        }


class BackupService:
    """Serviço para gerenciar backups do sistema"""
    
    # Tabelas principais para backup
    MAIN_TABLES = [
        "aluno",
        "agendamento",
        "desktop_orientation",
        "desktop_goal",
        "desktop_note",
        "desktop_screening",
        "desktop_moodentry",
        "desktop_intervention",
        "desktop_alert",
        "desktop_report",
        "desktop_message",
        "desktop_boardmessage",
    ]
    
    def __init__(self, backup_dir: Optional[str] = None):
        self._backup_dir = backup_dir or self._get_default_backup_dir()
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None
        
        # Cria diretório de backup se não existir
        Path(self._backup_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_default_backup_dir(self) -> str:
        """Retorna diretório padrão de backup"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "backups")
    
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Define callback para acompanhar progresso"""
        self._progress_callback = callback
    
    def _report_progress(self, current: int, total: int, message: str):
        """Reporta progresso da operação"""
        if self._progress_callback:
            self._progress_callback(current, total, message)
        logger.info(f"[{current}/{total}] {message}")
    
    def _generate_backup_id(self) -> str:
        """Gera ID único para o backup"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calcula checksum MD5 do arquivo"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_db_config(self) -> Dict[str, str]:
        """Obtém configuração do banco de dados"""
        return {
            "host": settings.DB_HOST,
            "port": str(settings.DB_PORT),
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "database": settings.DB_NAME,
        }
    
    def create_full_backup(
        self,
        include_files: bool = True,
        compress: bool = True,
        description: Optional[str] = None
    ) -> BackupInfo:
        """
        Cria um backup completo do sistema.
        
        Args:
            include_files: Se deve incluir arquivos anexados
            compress: Se deve comprimir o backup
            description: Descrição opcional do backup
            
        Returns:
            BackupInfo com informações do backup
        """
        backup_id = self._generate_backup_id()
        backup_file = os.path.join(self._backup_dir, f"backup_{backup_id}.json")
        if compress:
            backup_file += ".gz"
        
        backup_info = BackupInfo(
            id=backup_id,
            type=BackupType.FULL,
            created_at=datetime.now(),
            file_path=backup_file,
            file_size=0,
            checksum="",
            status=BackupStatus.IN_PROGRESS,
            tables_included=self.MAIN_TABLES.copy(),
        )
        
        try:
            self._report_progress(0, len(self.MAIN_TABLES), "Iniciando backup completo...")
            
            # Exporta dados de cada tabela
            backup_data = {
                "metadata": {
                    "backup_id": backup_id,
                    "type": "full",
                    "created_at": datetime.now().isoformat(),
                    "description": description,
                    "version": "1.0.0",
                },
                "tables": {},
            }
            
            for i, table in enumerate(self.MAIN_TABLES, 1):
                self._report_progress(i, len(self.MAIN_TABLES), f"Exportando tabela: {table}")
                backup_data["tables"][table] = self._export_table(table)
            
            # Inclui arquivos se solicitado
            if include_files:
                self._report_progress(len(self.MAIN_TABLES), len(self.MAIN_TABLES) + 1, "Incluindo arquivos...")
                backup_data["files"] = self._export_files_list()
            
            # Salva backup
            self._report_progress(len(self.MAIN_TABLES) + 1, len(self.MAIN_TABLES) + 2, "Salvando arquivo de backup...")
            
            json_data = json.dumps(backup_data, ensure_ascii=False, indent=2, default=str)
            
            if compress:
                with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
                    f.write(json_data)
            else:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            
            # Atualiza informações do backup
            backup_info.file_size = os.path.getsize(backup_file)
            backup_info.checksum = self._calculate_checksum(backup_file)
            backup_info.status = BackupStatus.COMPLETED
            
            # Salva metadados do backup
            self._save_backup_metadata(backup_info)
            
            self._report_progress(
                len(self.MAIN_TABLES) + 2,
                len(self.MAIN_TABLES) + 2,
                f"Backup concluído: {backup_info._format_size(backup_info.file_size)}"
            )
            
            logger.info(f"Backup completo criado: {backup_id}")
            return backup_info
            
        except Exception as e:
            logger.exception(f"Erro ao criar backup: {e}")
            backup_info.status = BackupStatus.FAILED
            backup_info.error_message = str(e)
            return backup_info
    
    def create_incremental_backup(
        self,
        since: datetime,
        compress: bool = True
    ) -> BackupInfo:
        """
        Cria um backup incremental (apenas alterações desde uma data).
        
        Args:
            since: Data a partir da qual capturar alterações
            compress: Se deve comprimir o backup
            
        Returns:
            BackupInfo com informações do backup
        """
        backup_id = self._generate_backup_id()
        backup_file = os.path.join(self._backup_dir, f"incremental_{backup_id}.json")
        if compress:
            backup_file += ".gz"
        
        backup_info = BackupInfo(
            id=backup_id,
            type=BackupType.INCREMENTAL,
            created_at=datetime.now(),
            file_path=backup_file,
            file_size=0,
            checksum="",
            status=BackupStatus.IN_PROGRESS,
        )
        
        try:
            backup_data = {
                "metadata": {
                    "backup_id": backup_id,
                    "type": "incremental",
                    "created_at": datetime.now().isoformat(),
                    "since": since.isoformat(),
                    "version": "1.0.0",
                },
                "tables": {},
            }
            
            # Exporta apenas registros alterados
            for table in self.MAIN_TABLES:
                data = self._export_table_incremental(table, since)
                if data:
                    backup_data["tables"][table] = data
                    backup_info.tables_included.append(table)
            
            # Salva backup
            json_data = json.dumps(backup_data, ensure_ascii=False, indent=2, default=str)
            
            if compress:
                with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
                    f.write(json_data)
            else:
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            
            backup_info.file_size = os.path.getsize(backup_file)
            backup_info.checksum = self._calculate_checksum(backup_file)
            backup_info.status = BackupStatus.COMPLETED
            
            self._save_backup_metadata(backup_info)
            
            logger.info(f"Backup incremental criado: {backup_id}")
            return backup_info
            
        except Exception as e:
            logger.exception(f"Erro ao criar backup incremental: {e}")
            backup_info.status = BackupStatus.FAILED
            backup_info.error_message = str(e)
            return backup_info
    
    def restore_backup(
        self,
        backup_id: str,
        tables: Optional[List[str]] = None,
        truncate_before_restore: bool = False
    ) -> RestoreResult:
        """
        Restaura um backup.
        
        Args:
            backup_id: ID do backup a ser restaurado
            tables: Lista de tabelas específicas (None = todas)
            truncate_before_restore: Se deve limpar tabelas antes de restaurar
            
        Returns:
            RestoreResult com resultado da operação
        """
        result = RestoreResult(
            success=False,
            backup_id=backup_id,
            restored_at=datetime.now(),
        )
        
        try:
            # Encontra arquivo de backup
            backup_file = self._find_backup_file(backup_id)
            if not backup_file:
                result.errors.append(f"Backup não encontrado: {backup_id}")
                return result
            
            # Carrega dados do backup
            backup_data = self._load_backup_file(backup_file)
            if not backup_data:
                result.errors.append("Erro ao carregar arquivo de backup")
                return result
            
            # Determina tabelas a restaurar
            tables_to_restore = tables or list(backup_data.get("tables", {}).keys())
            
            # Restaura cada tabela
            for table in tables_to_restore:
                if table not in backup_data.get("tables", {}):
                    result.errors.append(f"Tabela não encontrada no backup: {table}")
                    continue
                
                try:
                    records = self._restore_table(
                        table,
                        backup_data["tables"][table],
                        truncate=truncate_before_restore
                    )
                    result.tables_restored.append(table)
                    result.records_restored[table] = records
                except Exception as e:
                    result.errors.append(f"Erro ao restaurar {table}: {str(e)}")
            
            result.success = len(result.errors) == 0
            logger.info(f"Restore concluído: {backup_id}")
            return result
            
        except Exception as e:
            logger.exception(f"Erro ao restaurar backup: {e}")
            result.errors.append(str(e))
            return result
    
    def list_backups(self) -> List[BackupInfo]:
        """
        Lista todos os backups disponíveis.
        
        Returns:
            Lista de BackupInfo
        """
        backups = []
        
        try:
            # Carrega metadados salvos
            metadata_file = os.path.join(self._backup_dir, "backups_metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                for backup_data in metadata.get("backups", []):
                    try:
                        backup_info = BackupInfo(
                            id=backup_data["id"],
                            type=BackupType(backup_data["type"]),
                            created_at=datetime.fromisoformat(backup_data["created_at"]),
                            file_path=backup_data["file_path"],
                            file_size=backup_data["file_size"],
                            checksum=backup_data["checksum"],
                            status=BackupStatus(backup_data["status"]),
                            tables_included=backup_data.get("tables_included", []),
                            error_message=backup_data.get("error_message"),
                        )
                        backups.append(backup_info)
                    except Exception as e:
                        logger.warning(f"Erro ao carregar metadados do backup: {e}")
            
            # Verifica arquivos órfãos
            for file in os.listdir(self._backup_dir):
                if file.startswith("backup_") or file.startswith("incremental_"):
                    if not any(b.file_path.endswith(file) for b in backups):
                        # Tenta recuperar informações do arquivo
                        backup_info = self._recover_backup_info(os.path.join(self._backup_dir, file))
                        if backup_info:
                            backups.append(backup_info)
            
            # Ordena por data (mais recente primeiro)
            backups.sort(key=lambda b: b.created_at, reverse=True)
            
        except Exception as e:
            logger.exception(f"Erro ao listar backups: {e}")
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """
        Remove um backup.
        
        Args:
            backup_id: ID do backup a ser removido
            
        Returns:
            True se removido com sucesso
        """
        try:
            backup_file = self._find_backup_file(backup_id)
            if backup_file and os.path.exists(backup_file):
                os.remove(backup_file)
                
                # Remove dos metadados
                self._remove_backup_metadata(backup_id)
                
                logger.info(f"Backup removido: {backup_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.exception(f"Erro ao remover backup: {e}")
            return False
    
    def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Verifica integridade de um backup.
        
        Args:
            backup_id: ID do backup a verificar
            
        Returns:
            Dict com resultado da verificação
        """
        result = {
            "valid": False,
            "backup_id": backup_id,
            "errors": [],
            "warnings": [],
        }
        
        try:
            backup_file = self._find_backup_file(backup_id)
            if not backup_file:
                result["errors"].append("Arquivo de backup não encontrado")
                return result
            
            # Verifica se arquivo existe
            if not os.path.exists(backup_file):
                result["errors"].append("Arquivo não existe")
                return result
            
            # Verifica checksum
            backups = self.list_backups()
            backup_info = next((b for b in backups if b.id == backup_id), None)
            
            if backup_info:
                current_checksum = self._calculate_checksum(backup_file)
                if current_checksum != backup_info.checksum:
                    result["warnings"].append("Checksum diferente do registrado")
            
            # Tenta carregar o backup
            backup_data = self._load_backup_file(backup_file)
            if not backup_data:
                result["errors"].append("Não foi possível carregar o backup")
                return result
            
            # Verifica estrutura
            if "metadata" not in backup_data:
                result["errors"].append("Metadados ausentes")
            
            if "tables" not in backup_data:
                result["errors"].append("Dados de tabelas ausentes")
            else:
                result["tables_count"] = len(backup_data["tables"])
                result["tables"] = list(backup_data["tables"].keys())
            
            result["valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10) -> int:
        """
        Remove backups antigos.
        
        Args:
            keep_days: Manter backups dos últimos N dias
            keep_count: Manter pelo menos N backups
            
        Returns:
            Número de backups removidos
        """
        removed = 0
        
        try:
            backups = self.list_backups()
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            # Identifica backups a manter
            to_keep = set()
            
            # Mantém backups recentes por data
            for backup in backups:
                if backup.created_at >= cutoff_date:
                    to_keep.add(backup.id)
            
            # Mantém pelo menos keep_count backups
            for backup in backups[:keep_count]:
                to_keep.add(backup.id)
            
            # Remove os demais
            for backup in backups:
                if backup.id not in to_keep:
                    if self.delete_backup(backup.id):
                        removed += 1
            
            logger.info(f"Limpeza de backups: {removed} removidos")
            
        except Exception as e:
            logger.exception(f"Erro na limpeza de backups: {e}")
        
        return removed
    
    # Métodos auxiliares
    
    def _export_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Exporta todos os dados de uma tabela"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            connection.close()
            
            # Converte para lista de dicts serializáveis
            result = []
            for row in rows:
                result.append(dict(row))
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao exportar tabela {table_name}: {e}")
            return []
    
    def _export_table_incremental(self, table_name: str, since: datetime) -> List[Dict[str, Any]]:
        """Exporta registros alterados desde uma data"""
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Verifica se tabela tem coluna updated_at
            cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE 'updated_at'")
            has_updated = cursor.fetchone() is not None
            
            if has_updated:
                cursor.execute(
                    f"SELECT * FROM {table_name} WHERE updated_at >= %s",
                    (since,)
                )
            else:
                cursor.execute(f"SELECT * FROM {table_name}")
            
            rows = cursor.fetchall()
            connection.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Erro ao exportar tabela incremental {table_name}: {e}")
            return []
    
    def _restore_table(
        self,
        table_name: str,
        data: List[Dict[str, Any]],
        truncate: bool = False
    ) -> int:
        """Restaura dados em uma tabela"""
        if not data:
            return 0
        
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Limpa tabela se solicitado
            if truncate:
                cursor.execute(f"TRUNCATE TABLE {table_name}")
            
            # Obtém colunas da tabela
            columns = list(data[0].keys())
            placeholders = ", ".join(["%s"] * len(columns))
            columns_str = ", ".join(columns)
            
            # Insere registros
            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            records_inserted = 0
            for row in data:
                values = [row.get(col) for col in columns]
                try:
                    cursor.execute(query, values)
                    records_inserted += 1
                except Exception as e:
                    logger.warning(f"Erro ao inserir registro em {table_name}: {e}")
            
            connection.commit()
            return records_inserted
            
        finally:
            connection.close()
    
    def _export_files_list(self) -> List[Dict[str, str]]:
        """Exporta lista de arquivos anexados"""
        files_list = []
        
        # Diretório de uploads/assets
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(base_dir, "assets")
        
        if os.path.exists(assets_dir):
            for root, _, files in os.walk(assets_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, base_dir)
                    files_list.append({
                        "path": rel_path,
                        "size": os.path.getsize(file_path),
                    })
        
        return files_list
    
    def _find_backup_file(self, backup_id: str) -> Optional[str]:
        """Encontra arquivo de backup pelo ID"""
        for file in os.listdir(self._backup_dir):
            if backup_id in file:
                return os.path.join(self._backup_dir, file)
        return None
    
    def _load_backup_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Carrega dados de um arquivo de backup"""
        try:
            if file_path.endswith('.gz'):
                with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar backup {file_path}: {e}")
            return None
    
    def _save_backup_metadata(self, backup_info: BackupInfo):
        """Salva metadados do backup"""
        metadata_file = os.path.join(self._backup_dir, "backups_metadata.json")
        
        try:
            # Carrega metadados existentes
            metadata = {"backups": []}
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            # Adiciona novo backup
            metadata["backups"].append(backup_info.to_dict())
            
            # Salva
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Erro ao salvar metadados: {e}")
    
    def _remove_backup_metadata(self, backup_id: str):
        """Remove metadados de um backup"""
        metadata_file = os.path.join(self._backup_dir, "backups_metadata.json")
        
        try:
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                metadata["backups"] = [
                    b for b in metadata.get("backups", [])
                    if b.get("id") != backup_id
                ]
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.error(f"Erro ao remover metadados: {e}")
    
    def _recover_backup_info(self, file_path: str) -> Optional[BackupInfo]:
        """Tenta recuperar informações de um arquivo de backup órfão"""
        try:
            backup_data = self._load_backup_file(file_path)
            if not backup_data:
                return None
            
            metadata = backup_data.get("metadata", {})
            
            return BackupInfo(
                id=metadata.get("backup_id", os.path.basename(file_path)),
                type=BackupType(metadata.get("type", "full")),
                created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
                file_path=file_path,
                file_size=os.path.getsize(file_path),
                checksum=self._calculate_checksum(file_path),
                status=BackupStatus.COMPLETED,
                tables_included=list(backup_data.get("tables", {}).keys()),
            )
            
        except Exception as e:
            logger.warning(f"Erro ao recuperar info do backup {file_path}: {e}")
            return None


# Instância global para fácil acesso
servico_backup = BackupService()

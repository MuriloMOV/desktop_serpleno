"""
Configurações centralizadas do Desktop SerPleno
Carrega configurações de variáveis de ambiente com fallbacks seguros
"""
import os
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path

# Tenta carregar .env se disponível
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv não instalado, usar variáveis do sistema


@dataclass
class DatabaseConfig:
    """Configurações do banco de dados"""
    host: str = field(default_factory=lambda: os.getenv('DB_HOST', '127.0.0.1'))
    user: str = field(default_factory=lambda: os.getenv('DB_USER', 'root'))
    password: str = field(default_factory=lambda: os.getenv('DB_PASSWORD', ''))
    database: str = field(default_factory=lambda: os.getenv('DB_NAME', 'ser_pleno'))
    port: int = field(default_factory=lambda: int(os.getenv('DB_PORT', '3306')))
    
    def to_dict(self) -> dict:
        return {
            'host': self.host,
            'user': self.user,
            'password': self.password,
            'database': self.database,
            'port': self.port
        }
    
    def get_connection_string(self) -> str:
        """Retorna string de conexão MySQL"""
        return f"mysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ApiConfig:
    """Configurações da API"""
    base_url: str = field(default_factory=lambda: os.getenv('API_BASE_URL', 'http://127.0.0.1:8000'))
    timeout: int = field(default_factory=lambda: int(os.getenv('API_TIMEOUT', '5')))
    desktop_prefix: str = '/api/v1/desktop'


@dataclass
class SyncConfig:
    """Configurações de sincronização"""
    interval: int = field(default_factory=lambda: int(os.getenv('SYNC_INTERVAL', '300')))
    auto_sync: bool = field(default_factory=lambda: os.getenv('AUTO_SYNC', 'true').lower() == 'true')


@dataclass
class Settings:
    """Configurações globais da aplicação"""
    app_name: str = "SerPleno Desktop"
    app_version: str = "1.0.0"
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: ApiConfig = field(default_factory=ApiConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    
    @property
    def operation_mode(self) -> str:
        """Retorna o modo de operação"""
        return os.getenv('OPERATION_MODE', 'hybrid')
    
    @classmethod
    def load(cls) -> 'Settings':
        """Carrega configurações do ambiente"""
        return cls()


# Instância global de configurações
settings = Settings.load()


def get_settings() -> Settings:
    """Retorna a instância global de configurações"""
    return settings

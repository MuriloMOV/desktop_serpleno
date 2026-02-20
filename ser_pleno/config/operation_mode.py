"""
Configuração de Modo de Operação do Desktop SerPleno

Este módulo gerencia o modo de operação do sistema desktop:
- INDEPENDENT: Funciona totalmente de forma independente, usando apenas o banco local
- HYBRID: Funciona de forma independente, mas sincroniza com serpleno_web quando disponível
- CONNECTED: Requer conexão com serpleno_web (modo legado)

O sistema pode alternar entre modos automaticamente baseado na disponibilidade da API.
"""
import os
import json
import logging
from enum import Enum
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    """Modos de operação do sistema"""
    INDEPENDENT = "independent"  # Totalmente independente
    HYBRID = "hybrid"            # Independente com sincronização opcional
    CONNECTED = "connected"      # Requer conexão (legado)


class OperationConfig:
    """Gerenciador de configuração de modo de operação"""
    
    # Arquivo de configuração local
    CONFIG_FILE = "operation_config.json"
    
    # Configurações padrão
    DEFAULT_CONFIG = {
        "mode": "hybrid",
        "api_base_url": "http://127.0.0.1:8000",
        "api_timeout": 5,
        "sync_interval": 300,  # 5 minutos
        "auto_sync": True,
        "offline_cache_size": 1000,
        "last_sync": None,
        "api_available": False
    }
    
    _instance: Optional['OperationConfig'] = None
    _config: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = {}  # Inicializa no __new__ para evitar problemas de tipo
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self._load_config()
    
    def _get_config_path(self) -> str:
        """Retorna o caminho do arquivo de configuração"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, self.CONFIG_FILE)
    
    def _load_config(self):
        """Carrega configuração do arquivo ou usa padrão"""
        config_path = self._get_config_path()
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = {**self.DEFAULT_CONFIG, **json.load(f)}
                logger.info(f"Configuração carregada: modo {self._config['mode']}")
            except Exception as e:
                logger.warning(f"Erro ao carregar configuração: {e}, usando padrão")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
            self._save_config()
    
    def _save_config(self):
        """Salva configuração no arquivo"""
        config_path = self._get_config_path()
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
    
    @property
    def mode(self) -> OperationMode:
        """Retorna o modo de operação atual"""
        return OperationMode(self._config.get("mode", "hybrid"))
    
    def set_mode(self, mode: OperationMode):
        """Define o modo de operação"""
        self._config["mode"] = mode.value
        self._save_config()
        logger.info(f"Modo de operação alterado para: {mode.value}")
    
    @property
    def api_base_url(self) -> str:
        """Retorna a URL base da API"""
        return self._config.get("api_base_url", "http://127.0.0.1:8000")
    
    @property
    def api_timeout(self) -> int:
        """Retorna o timeout da API em segundos"""
        return self._config.get("api_timeout", 5)
    
    @property
    def sync_interval(self) -> int:
        """Retorna o intervalo de sincronização em segundos"""
        return self._config.get("sync_interval", 300)
    
    @property
    def auto_sync(self) -> bool:
        """Retorna se a sincronização automática está ativa"""
        return self._config.get("auto_sync", True)
    
    def set_auto_sync(self, enabled: bool):
        """Ativa/desativa sincronização automática"""
        self._config["auto_sync"] = enabled
        self._save_config()
    
    @property
    def api_available(self) -> bool:
        """Retorna se a API está disponível"""
        return self._config.get("api_available", False)
    
    def set_api_available(self, available: bool):
        """Define disponibilidade da API"""
        self._config["api_available"] = available
        self._save_config()
    
    @property
    def last_sync(self) -> Optional[datetime]:
        """Retorna a data/hora da última sincronização"""
        last = self._config.get("last_sync")
        if last:
            try:
                return datetime.fromisoformat(last)
            except:
                return None
        return None
    
    def update_last_sync(self):
        """Atualiza a data/hora da última sincronização"""
        self._config["last_sync"] = datetime.now().isoformat()
        self._save_config()
    
    def is_independent(self) -> bool:
        """Verifica se o sistema está em modo independente"""
        return self.mode == OperationMode.INDEPENDENT
    
    def is_hybrid(self) -> bool:
        """Verifica se o sistema está em modo híbrido"""
        return self.mode == OperationMode.HYBRID
    
    def is_connected(self) -> bool:
        """Verifica se o sistema está em modo conectado"""
        return self.mode == OperationMode.CONNECTED
    
    def should_use_api(self) -> bool:
        """Verifica se deve tentar usar a API"""
        if self.is_independent():
            return False
        return True
    
    def should_sync(self) -> bool:
        """Verifica se deve sincronizar com a API"""
        if not self.auto_sync:
            return False
        if self.is_independent():
            return False
        if not self.api_available:
            return False
        return True
    
    def get_all_config(self) -> dict:
        """Retorna todas as configurações"""
        return self._config.copy()


# Instância global
operation_config = OperationConfig()


def get_operation_config() -> OperationConfig:
    """Retorna a instância global de configuração de operação"""
    return operation_config


def get_mode() -> OperationMode:
    """Retorna o modo de operação atual"""
    return operation_config.mode


def is_api_available() -> bool:
    """Verifica se a API está disponível"""
    return operation_config.api_available


def should_use_api() -> bool:
    """Verifica se deve usar a API"""
    return operation_config.should_use_api()

"""
Serviço de Monitoramento para o Desktop CustomTkinter
Implementa health checks, métricas e alertas do sistema
"""
import logging
import time
import psutil
import threading
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

try:
    import requests
except Exception:
    requests = None

from config.db_config import get_db_connection

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Status de saúde de um componente"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Severidade de um alerta"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    """Resultado de um health check"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
            "response_time_ms": self.response_time_ms,
        }


@dataclass
class MetricValue:
    """Valor de uma métrica"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
        }


@dataclass
class Alert:
    """Representa um alerta do sistema"""
    id: Optional[int] = None
    severity: AlertSeverity = AlertSeverity.WARNING
    component: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity.value,
            "component": self.component,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
        }


class MonitoringService:
    """Serviço para monitoramento do sistema"""
    
    def __init__(self):
        self._metrics_history: Dict[str, deque] = {}
        self._max_metrics_history = 1000
        self._health_checks: Dict[str, HealthCheckResult] = {}
        self._alerts: List[Alert] = []
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._api_base_url = "http://localhost:8000/api/v1"
    
    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """Registra callback para ser chamado quando um alerta é gerado"""
        self._alert_callbacks.append(callback)
    
    def check_database_health(self) -> HealthCheckResult:
        """Verifica saúde da conexão com banco de dados"""
        start_time = time.time()
        
        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            
            # Testa query simples
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            # Obtém informações do banco
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            
            # Obtém número de conexões
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            connections = cursor.fetchone()
            
            connection.close()
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                component="database",
                status=HealthStatus.HEALTHY,
                message="Conexão com banco de dados OK",
                details={
                    "version": str(version[0]) if version else "unknown",
                    "connections": str(connections[1]) if connections else "unknown",
                },
                response_time_ms=response_time
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Erro na conexão com banco: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_api_health(self) -> HealthCheckResult:
        """Verifica saúde da API"""
        start_time = time.time()
        
        if not requests:
            return HealthCheckResult(
                component="api",
                status=HealthStatus.UNKNOWN,
                message="Biblioteca requests não disponível"
            )
        
        try:
            response = requests.get(
                f"{self._api_base_url}/health/",
                timeout=5
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.ok:
                return HealthCheckResult(
                    component="api",
                    status=HealthStatus.HEALTHY,
                    message="API respondendo normalmente",
                    details={"status_code": response.status_code},
                    response_time_ms=response_time
                )
            else:
                return HealthCheckResult(
                    component="api",
                    status=HealthStatus.DEGRADED,
                    message=f"API retornou status {response.status_code}",
                    details={"status_code": response.status_code},
                    response_time_ms=response_time
                )
                
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                component="api",
                status=HealthStatus.UNHEALTHY,
                message="Timeout ao conectar com API",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                component="api",
                status=HealthStatus.UNHEALTHY,
                message="API indisponível (modo offline)",
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                component="api",
                status=HealthStatus.UNHEALTHY,
                message=f"Erro ao verificar API: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def check_memory_health(self) -> HealthCheckResult:
        """Verifica uso de memória"""
        try:
            memory = psutil.virtual_memory()
            
            status = HealthStatus.HEALTHY
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
            elif memory.percent > 75:
                status = HealthStatus.DEGRADED
            
            return HealthCheckResult(
                component="memory",
                status=status,
                message=f"Uso de memória: {memory.percent:.1f}%",
                details={
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Erro ao verificar memória: {str(e)}"
            )
    
    def check_cpu_health(self) -> HealthCheckResult:
        """Verifica uso de CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            status = HealthStatus.HEALTHY
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
            elif cpu_percent > 75:
                status = HealthStatus.DEGRADED
            
            return HealthCheckResult(
                component="cpu",
                status=status,
                message=f"Uso de CPU: {cpu_percent:.1f}%",
                details={
                    "percent": cpu_percent,
                    "cores": psutil.cpu_count(),
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="cpu",
                status=HealthStatus.UNKNOWN,
                message=f"Erro ao verificar CPU: {str(e)}"
            )
    
    def check_disk_health(self) -> HealthCheckResult:
        """Verifica uso de disco"""
        try:
            disk = psutil.disk_usage('/')
            
            status = HealthStatus.HEALTHY
            if disk.percent > 90:
                status = HealthStatus.UNHEALTHY
            elif disk.percent > 80:
                status = HealthStatus.DEGRADED
            
            return HealthCheckResult(
                component="disk",
                status=status,
                message=f"Uso de disco: {disk.percent:.1f}%",
                details={
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "percent": disk.percent,
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="disk",
                status=HealthStatus.UNKNOWN,
                message=f"Erro ao verificar disco: {str(e)}"
            )
    
    def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """Executa todos os health checks"""
        results = {
            "database": self.check_database_health(),
            "api": self.check_api_health(),
            "memory": self.check_memory_health(),
            "cpu": self.check_cpu_health(),
            "disk": self.check_disk_health(),
        }
        
        self._health_checks = results
        
        # Gera alertas para componentes não saudáveis
        for component, result in results.items():
            if result.status == HealthStatus.UNHEALTHY:
                self._create_alert(
                    severity=AlertSeverity.ERROR,
                    component=component,
                    message=result.message,
                    details=result.details
                )
            elif result.status == HealthStatus.DEGRADED:
                self._create_alert(
                    severity=AlertSeverity.WARNING,
                    component=component,
                    message=result.message,
                    details=result.details
                )
        
        return results
    
    def get_system_health(self) -> Dict[str, Any]:
        """Retorna status geral de saúde do sistema"""
        if not self._health_checks:
            self.run_all_health_checks()
        
        # Determina status geral
        overall_status = HealthStatus.HEALTHY
        for result in self._health_checks.values():
            if result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
                break
            elif result.status == HealthStatus.DEGRADED:
                overall_status = HealthStatus.DEGRADED
        
        return {
            "overall_status": overall_status.value,
            "components": {k: v.to_dict() for k, v in self._health_checks.items()},
            "checked_at": datetime.now().isoformat(),
        }
    
    def collect_metrics(self) -> List[MetricValue]:
        """Coleta métricas atuais do sistema"""
        metrics = []
        now = datetime.now()
        
        try:
            # Métricas de memória
            memory = psutil.virtual_memory()
            metrics.append(MetricValue(
                name="memory.used_percent",
                value=memory.percent,
                unit="percent",
                timestamp=now
            ))
            metrics.append(MetricValue(
                name="memory.available_mb",
                value=memory.available / (1024**2),
                unit="MB",
                timestamp=now
            ))
            
            # Métricas de CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics.append(MetricValue(
                name="cpu.used_percent",
                value=cpu_percent,
                unit="percent",
                timestamp=now
            ))
            
            # Métricas de disco
            disk = psutil.disk_usage('/')
            metrics.append(MetricValue(
                name="disk.used_percent",
                value=disk.percent,
                unit="percent",
                timestamp=now
            ))
            
            # Métricas de processo
            process = psutil.Process()
            metrics.append(MetricValue(
                name="process.memory_mb",
                value=process.memory_info().rss / (1024**2),
                unit="MB",
                timestamp=now
            ))
            metrics.append(MetricValue(
                name="process.cpu_percent",
                value=process.cpu_percent(),
                unit="percent",
                timestamp=now
            ))
            
            # Armazena no histórico
            for metric in metrics:
                if metric.name not in self._metrics_history:
                    self._metrics_history[metric.name] = deque(maxlen=self._max_metrics_history)
                self._metrics_history[metric.name].append(metric)
            
        except Exception as e:
            logger.error(f"Erro ao coletar métricas: {e}")
        
        return metrics
    
    def get_metric_history(self, metric_name: str, minutes: int = 60) -> List[MetricValue]:
        """Obtém histórico de uma métrica"""
        if metric_name not in self._metrics_history:
            return []
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            m for m in self._metrics_history[metric_name]
            if m.timestamp >= cutoff
        ]
    
    def get_all_metrics(self) -> Dict[str, List[MetricValue]]:
        """Retorna todas as métricas atuais"""
        return {
            name: list(history)
            for name, history in self._metrics_history.items()
        }
    
    def _create_alert(
        self,
        severity: AlertSeverity,
        component: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Cria um novo alerta"""
        alert = Alert(
            severity=severity,
            component=component,
            message=message,
            details=details or {},
        )
        
        self._alerts.append(alert)
        
        # Notifica callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Erro no callback de alerta: {e}")
        
        logger.warning(f"ALERTA [{severity.value}] {component}: {message}")
        
        return alert
    
    def get_active_alerts(self) -> List[Alert]:
        """Retorna alertas ativos (não reconhecidos)"""
        return [a for a in self._alerts if not a.acknowledged]
    
    def get_all_alerts(self, limit: int = 100) -> List[Alert]:
        """Retorna todos os alertas"""
        return self._alerts[-limit:]
    
    def acknowledge_alert(self, alert_id: int, acknowledged_by: str = "") -> bool:
        """Marca um alerta como reconhecido"""
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by
                return True
        return False
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Inicia monitoramento em background"""
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            logger.warning("Monitoramento já está em execução")
            return
        
        self._stop_monitoring.clear()
        
        def monitor_loop():
            while not self._stop_monitoring.is_set():
                try:
                    self.run_all_health_checks()
                    self.collect_metrics()
                except Exception as e:
                    logger.error(f"Erro no loop de monitoramento: {e}")
                
                self._stop_monitoring.wait(interval_seconds)
        
        self._monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info(f"Monitoramento iniciado (intervalo: {interval_seconds}s)")
    
    def stop_monitoring(self):
        """Para o monitoramento em background"""
        self._stop_monitoring.set()
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Monitoramento parado")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Retorna dados consolidados para dashboard de monitoramento"""
        # Coleta métricas atuais
        current_metrics = self.collect_metrics()
        
        # Executa health checks
        health = self.get_system_health()
        
        # Obtém alertas ativos
        active_alerts = self.get_active_alerts()
        
        return {
            "health": health,
            "metrics": {m.name: m.to_dict() for m in current_metrics},
            "active_alerts": [a.to_dict() for a in active_alerts],
            "alert_count": len(active_alerts),
            "collected_at": datetime.now().isoformat(),
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Retorna resumo de performance"""
        try:
            # Query performance
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            
            # Queries lentas (MySQL)
            cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
            slow_queries = cursor.fetchone()
            
            # Tempo de uptime
            cursor.execute("SHOW STATUS LIKE 'Uptime'")
            uptime = cursor.fetchone()
            
            connection.close()
            
            # Performance do sistema
            process = psutil.Process()
            
            return {
                "database": {
                    "slow_queries": int(slow_queries[1]) if slow_queries else 0,
                    "uptime_seconds": int(uptime[1]) if uptime else 0,
                },
                "application": {
                    "memory_mb": round(process.memory_info().rss / (1024**2), 2),
                    "cpu_percent": process.cpu_percent(),
                    "threads": process.num_threads(),
                },
                "system": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage('/').percent,
                },
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter resumo de performance: {e}")
            return {"error": str(e)}


# Instância global para fácil acesso
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Retorna a instância global do serviço de monitoramento"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service

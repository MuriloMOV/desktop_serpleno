"""
Exceções customizadas do Desktop SerPleno
"""
from typing import Optional, Any


class SerPlenoException(Exception):
    """Exceção base do SerPleno"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Detalhes: {self.details}"
        return self.message


class DatabaseException(SerPlenoException):
    """Exceção relacionada ao banco de dados"""
    
    def __init__(self, message: str, query: Optional[str] = None, details: Optional[Any] = None):
        self.query = query
        super().__init__(message, details)
    
    def __str__(self) -> str:
        base = super().__str__()
        if self.query:
            return f"{base} - Query: {self.query[:100]}..."
        return base


class ApiException(SerPlenoException):
    """Exceção relacionada à API"""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        endpoint: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.status_code = status_code
        self.endpoint = endpoint
        super().__init__(message, details)
    
    def __str__(self) -> str:
        base = super().__str__()
        parts = []
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
        if parts:
            return f"{base} - {', '.join(parts)}"
        return base


class ValidationException(SerPlenoException):
    """Exceção de validação de dados"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.field = field
        self.value = value
        super().__init__(message)
    
    def __str__(self) -> str:
        base = super().__str__()
        if self.field:
            return f"{base} - Campo: {self.field}"
        return base


class NotFoundException(SerPlenoException):
    """Exceção quando recurso não é encontrado"""
    
    def __init__(self, resource: str, identifier: Any):
        self.resource = resource
        self.identifier = identifier
        super().__init__(f"{resource} não encontrado", identifier)


class AuthenticationException(SerPlenoException):
    """Exceção de autenticação"""
    pass


class ConnectionException(SerPlenoException):
    """Exceção de conexão (API ou Banco)"""
    pass


class SyncException(SerPlenoException):
    """Exceção de sincronização"""
    pass

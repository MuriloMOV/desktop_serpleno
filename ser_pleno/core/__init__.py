"""
Core - Módulos base do Desktop SerPleno
"""
from .base_service import BaseService
from .exceptions import (
    SerPlenoException,
    DatabaseException,
    ApiException,
    ValidationException,
    NotFoundException
)

__all__ = [
    'BaseService',
    'SerPlenoException',
    'DatabaseException',
    'ApiException',
    'ValidationException',
    'NotFoundException'
]

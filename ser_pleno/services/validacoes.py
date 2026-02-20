"""
Serviço de Validações Centralizadas para o Desktop CustomTkinter
Implementa validações de dados reutilizáveis
"""
import re
from typing import Optional, Dict, Any, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date


class ValidationSeverity(Enum):
    """Severidade de um erro de validação"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Representa um erro de validação"""
    field: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    value: Any = None
    code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "value": str(self.value) if self.value is not None else None,
            "code": self.code,
        }


@dataclass
class ValidationResult:
    """Resultado de uma validação"""
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    
    def add_error(self, field: str, message: str, value: Any = None, code: Optional[str] = None):
        """Adiciona um erro ao resultado"""
        self.errors.append(ValidationError(
            field=field,
            message=message,
            severity=ValidationSeverity.ERROR,
            value=value,
            code=code
        ))
        self.is_valid = False
    
    def add_warning(self, field: str, message: str, value: Any = None, code: Optional[str] = None):
        """Adiciona um aviso ao resultado"""
        self.warnings.append(ValidationError(
            field=field,
            message=message,
            severity=ValidationSeverity.WARNING,
            value=value,
            code=code
        ))
    
    def merge(self, other: 'ValidationResult'):
        """Mescla outro resultado de validação"""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }
    
    def get_error_messages(self) -> List[str]:
        """Retorna lista de mensagens de erro"""
        return [e.message for e in self.errors]
    
    def get_field_errors(self, field: str) -> List[ValidationError]:
        """Retorna erros de um campo específico"""
        return [e for e in self.errors if e.field == field]


class Validator:
    """Classe base para validadores"""
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        """Valida um valor"""
        raise NotImplementedError


class RequiredValidator(Validator):
    """Validador de campo obrigatório"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "Este campo é obrigatório"
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            result.add_error(field_name, self.message, value, "required")
        elif isinstance(value, str) and not value.strip():
            result.add_error(field_name, self.message, value, "required")
        elif isinstance(value, (list, dict)) and not value:
            result.add_error(field_name, self.message, value, "required")
        
        return result


class LengthValidator(Validator):
    """Validador de tamanho de string"""
    
    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        message: Optional[str] = None
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.message = message
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if value is None or not isinstance(value, str):
            return result
        
        length = len(value)
        
        if self.min_length is not None and length < self.min_length:
            msg = self.message or f"Deve ter pelo menos {self.min_length} caracteres"
            result.add_error(field_name, msg, value, "min_length")
        
        if self.max_length is not None and length > self.max_length:
            msg = self.message or f"Deve ter no máximo {self.max_length} caracteres"
            result.add_error(field_name, msg, value, "max_length")
        
        return result


class EmailValidator(Validator):
    """Validador de email"""
    
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "Email inválido"
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if not value:
            return result
        
        if not isinstance(value, str) or not self.EMAIL_REGEX.match(value):
            result.add_error(field_name, self.message, value, "invalid_email")
        
        return result


class PhoneValidator(Validator):
    """Validador de telefone brasileiro"""
    
    # Aceita formatos: (XX) XXXXX-XXXX, (XX) XXXX-XXXX, XX XXXXX XXXX, etc.
    PHONE_REGEX = re.compile(
        r'^(\+?55\s?)?(\(?[1-9]{2}\)?\s?)?(9?[0-9]{4}[-\s]?[0-9]{4})$'
    )
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "Telefone inválido"
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if not value:
            return result
        
        # Remove caracteres não numéricos para validação
        if isinstance(value, str):
            digits = re.sub(r'\D', '', value)
            
            # Deve ter 10 ou 11 dígitos (com ou sem 9º dígito)
            if len(digits) not in [10, 11]:
                result.add_error(field_name, self.message, value, "invalid_phone")
        
        return result


class CPFValidator(Validator):
    """Validador de CPF"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "CPF inválido"
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if not value:
            return result
        
        # Remove caracteres não numéricos
        if isinstance(value, str):
            cpf = re.sub(r'\D', '', value)
            
            if not self._validate_cpf_digits(cpf):
                result.add_error(field_name, self.message, value, "invalid_cpf")
        
        return result
    
    def _validate_cpf_digits(self, cpf: str) -> bool:
        """Valida dígitos do CPF"""
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Valida primeiro dígito verificador
        total = sum(int(cpf[i]) * (10 - i) for i in range(9))
        remainder = (total * 10) % 11
        if remainder == 10:
            remainder = 0
        if remainder != int(cpf[9]):
            return False
        
        # Valida segundo dígito verificador
        total = sum(int(cpf[i]) * (11 - i) for i in range(10))
        remainder = (total * 10) % 11
        if remainder == 10:
            remainder = 0
        if remainder != int(cpf[10]):
            return False
        
        return True


class DateValidator(Validator):
    """Validador de data"""
    
    def __init__(
        self,
        min_date: Optional[date] = None,
        max_date: Optional[date] = None,
        message: Optional[str] = None
    ):
        self.min_date = min_date
        self.max_date = max_date
        self.message = message
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if not value:
            return result
        
        # Converte para date se necessário
        if isinstance(value, str):
            try:
                # Tenta vários formatos
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                    try:
                        value = datetime.strptime(value, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    result.add_error(field_name, "Formato de data inválido", value, "invalid_date")
                    return result
            except Exception:
                result.add_error(field_name, "Data inválida", value, "invalid_date")
                return result
        
        if isinstance(value, datetime):
            value = value.date()
        
        if isinstance(value, date):
            if self.min_date and value < self.min_date:
                msg = self.message or f"Data deve ser a partir de {self.min_date.strftime('%d/%m/%Y')}"
                result.add_error(field_name, msg, value, "min_date")
            
            if self.max_date and value > self.max_date:
                msg = self.message or f"Data deve ser até {self.max_date.strftime('%d/%m/%Y')}"
                result.add_error(field_name, msg, value, "max_date")
        
        return result


class IntegerValidator(Validator):
    """Validador de número inteiro"""
    
    def __init__(
        self,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        message: Optional[str] = None
    ):
        self.min_value = min_value
        self.max_value = max_value
        self.message = message
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        try:
            int_value = int(value)
            
            if self.min_value is not None and int_value < self.min_value:
                msg = self.message or f"Valor deve ser no mínimo {self.min_value}"
                result.add_error(field_name, msg, value, "min_value")
            
            if self.max_value is not None and int_value > self.max_value:
                msg = self.message or f"Valor deve ser no máximo {self.max_value}"
                result.add_error(field_name, msg, value, "max_value")
                
        except (ValueError, TypeError):
            result.add_error(field_name, "Valor deve ser um número inteiro", value, "invalid_integer")
        
        return result


class ChoiceValidator(Validator):
    """Validador de escolha (enum)"""
    
    def __init__(self, choices: List[Any], message: Optional[str] = None):
        self.choices = choices
        self.message = message or f"Valor deve ser um de: {', '.join(str(c) for c in choices)}"
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if value is None:
            return result
        
        if value not in self.choices:
            result.add_error(field_name, self.message, value, "invalid_choice")
        
        return result


class RegexValidator(Validator):
    """Validador baseado em expressão regular"""
    
    def __init__(self, pattern: str, message: Optional[str] = None):
        self.pattern = re.compile(pattern)
        self.message = message or "Formato inválido"
    
    def validate(self, value: Any, field_name: str = "field") -> ValidationResult:
        result = ValidationResult()
        
        if not value:
            return result
        
        if not isinstance(value, str) or not self.pattern.match(value):
            result.add_error(field_name, self.message, value, "invalid_format")
        
        return result


class ValidationService:
    """Serviço centralizado de validações"""
    
    def __init__(self):
        self._validators: Dict[str, List[Validator]] = {}
        self._custom_validators: Dict[str, Callable[[Any], ValidationResult]] = {}
    
    def register_validator(self, field_name: str, validator: Validator):
        """Registra um validador para um campo"""
        if field_name not in self._validators:
            self._validators[field_name] = []
        self._validators[field_name].append(validator)
    
    def register_custom_validator(
        self,
        name: str,
        validator_func: Callable[[Any], ValidationResult]
    ):
        """Registra um validador customizado"""
        self._custom_validators[name] = validator_func
    
    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """Valida um único campo"""
        result = ValidationResult()
        
        validators = self._validators.get(field_name, [])
        for validator in validators:
            result.merge(validator.validate(value, field_name))
        
        return result
    
    def validate_data(
        self,
        data: Dict[str, Any],
        rules: Optional[Dict[str, List[Validator]]] = None
    ) -> ValidationResult:
        """
        Valida múltiplos campos de dados.
        
        Args:
            data: Dicionário com dados a validar
            rules: Regras de validação (opcional, usa registradas se não informado)
            
        Returns:
            ValidationResult consolidado
        """
        result = ValidationResult()
        
        validation_rules = rules or self._validators
        
        for field_name, validators in validation_rules.items():
            value = data.get(field_name)
            for validator in validators:
                result.merge(validator.validate(value, field_name))
        
        return result
    
    # Métodos de conveniência para validações comuns
    
    def validate_student(self, data: Dict[str, Any]) -> ValidationResult:
        """Valida dados de estudante"""
        rules = {
            "nome": [
                RequiredValidator("Nome é obrigatório"),
                LengthValidator(min_length=3, max_length=200),
            ],
            "email": [
                EmailValidator("Email inválido"),
                LengthValidator(max_length=254),
            ],
            "telefone": [
                PhoneValidator("Telefone inválido"),
            ],
            "idade": [
                IntegerValidator(min_value=0, max_value=150),
            ],
        }
        return self.validate_data(data, rules)
    
    def validate_appointment(self, data: Dict[str, Any]) -> ValidationResult:
        """Valida dados de agendamento"""
        result = ValidationResult()
        
        # Valida estudante
        if not data.get("student_id"):
            result.add_error("student_id", "Estudante é obrigatório")
        
        # Valida data/hora
        if not data.get("data_hora"):
            result.add_error("data_hora", "Data e hora são obrigatórias")
        else:
            # Verifica se não é no passado
            if isinstance(data.get("data_hora"), datetime):
                if data["data_hora"] < datetime.now():
                    result.add_warning("data_hora", "Agendamento no passado")
        
        return result
    
    def validate_orientation(self, data: Dict[str, Any]) -> ValidationResult:
        """Valida dados de orientação"""
        rules = {
            "student_id": [RequiredValidator("Estudante é obrigatório")],
            "session_date": [RequiredValidator("Data da sessão é obrigatória")],
            "main_complaint": [LengthValidator(max_length=500)],
            "notes": [LengthValidator(max_length=5000)],
        }
        return self.validate_data(data, rules)
    
    def validate_user(self, data: Dict[str, Any]) -> ValidationResult:
        """Valida dados de usuário"""
        rules = {
            "username": [
                RequiredValidator("Nome de usuário é obrigatório"),
                LengthValidator(min_length=3, max_length=150),
                RegexValidator(r'^[a-zA-Z0-9_]+$', "Apenas letras, números e underscore"),
            ],
            "email": [
                RequiredValidator("Email é obrigatório"),
                EmailValidator("Email inválido"),
            ],
            "password": [
                RequiredValidator("Senha é obrigatória"),
                LengthValidator(min_length=8, max_length=128),
            ],
        }
        return self.validate_data(data, rules)
    
    def validate_login(self, data: Dict[str, Any]) -> ValidationResult:
        """Valida dados de login"""
        rules = {
            "username": [RequiredValidator("Nome de usuário é obrigatório")],
            "password": [RequiredValidator("Senha é obrigatória")],
        }
        return self.validate_data(data, rules)


# Instância global para fácil acesso
_validation_service: Optional[ValidationService] = None


def get_validation_service() -> ValidationService:
    """Retorna a instância global do serviço de validação"""
    global _validation_service
    if _validation_service is None:
        _validation_service = ValidationService()
    return _validation_service


# Funções de conveniência
def validate_required(value: Any, field_name: str = "field") -> ValidationResult:
    """Valida campo obrigatório"""
    return RequiredValidator().validate(value, field_name)


def validate_email(value: Any, field_name: str = "email") -> ValidationResult:
    """Valida email"""
    return EmailValidator().validate(value, field_name)


def validate_phone(value: Any, field_name: str = "telefone") -> ValidationResult:
    """Valida telefone"""
    return PhoneValidator().validate(value, field_name)


def validate_cpf(value: Any, field_name: str = "cpf") -> ValidationResult:
    """Valida CPF"""
    return CPFValidator().validate(value, field_name)


def validate_length(
    value: Any,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    field_name: str = "field"
) -> ValidationResult:
    """Valida tamanho de string"""
    return LengthValidator(min_length, max_length).validate(value, field_name)

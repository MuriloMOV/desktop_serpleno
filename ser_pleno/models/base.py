"""
Modelos de dados do Desktop SerPleno
Usando dataclasses para modelos ricos com comportamento
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PriorityLevel(Enum):
    """Níveis de prioridade"""
    BAIXA = 0
    MEDIA = 1
    ALTA = 2
    URGENTE = 3


class AgendamentoStatus(Enum):
    """Status de agendamento"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


@dataclass
class BaseModel:
    """Classe base para todos os modelos"""
    
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte modelo para dicionário"""
        data = asdict(self)
        # Remove campos None
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """Cria modelo a partir de dicionário"""
        return cls(**data)


@dataclass
class Estudante(BaseModel):
    """Modelo de Estudante"""
    
    nome: str = ""
    email: Optional[str] = None
    curso: Optional[str] = None
    idade: Optional[int] = None
    matricula: Optional[str] = None
    phone: Optional[str] = None
    
    # Campos de atenção
    requires_attention: bool = False
    attention_reason: Optional[str] = None
    priority_level: int = 0
    
    # Campos médicos
    has_medical_report: bool = False
    medical_report_notes: Optional[str] = None
    
    # Contatos de emergência
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    
    # Relacionamentos
    user_id: Optional[int] = None
    
    @property
    def iniciais(self) -> str:
        """Retorna as iniciais do nome"""
        if not self.nome:
            return "??"
        return "".join([n[0] for n in self.nome.split()[:2]]).upper()
    
    @property
    def priority(self) -> PriorityLevel:
        """Retorna o nível de prioridade"""
        try:
            return PriorityLevel(self.priority_level)
        except ValueError:
            return PriorityLevel.BAIXA
    
    @property
    def priority_icon(self) -> str:
        """Retorna ícone de prioridade"""
        icons = {
            PriorityLevel.URGENTE: "🔴",
            PriorityLevel.ALTA: "🟠",
            PriorityLevel.MEDIA: "🟡",
            PriorityLevel.BAIXA: "🟢"
        }
        return icons.get(self.priority, "⚪")
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        # Adiciona campos computados
        data['iniciais'] = self.iniciais
        data['priority_icon'] = self.priority_icon
        return data


@dataclass
class Agendamento(BaseModel):
    """Modelo de Agendamento"""
    
    student_id: int = 0
    data_hora: Optional[datetime] = None
    status: str = "pending"
    notes: Optional[str] = None
    duration_minutes: int = 60
    
    # Relacionamentos (preenchidos via join)
    student_name: Optional[str] = None
    student_course: Optional[str] = None
    
    @property
    def status_enum(self) -> AgendamentoStatus:
        try:
            return AgendamentoStatus(self.status)
        except ValueError:
            return AgendamentoStatus.PENDING
    
    @property
    def status_label(self) -> str:
        labels = {
            AgendamentoStatus.PENDING: "Pendente",
            AgendamentoStatus.CONFIRMED: "Confirmado",
            AgendamentoStatus.COMPLETED: "Concluído",
            AgendamentoStatus.CANCELLED: "Cancelado",
            AgendamentoStatus.NO_SHOW: "Não Compareceu"
        }
        return labels.get(self.status_enum, self.status)
    
    @property
    def status_color(self) -> str:
        colors = {
            AgendamentoStatus.PENDING: "#F59E0B",  # Amarelo
            AgendamentoStatus.CONFIRMED: "#3B82F6",  # Azul
            AgendamentoStatus.COMPLETED: "#10B981",  # Verde
            AgendamentoStatus.CANCELLED: "#EF4444",  # Vermelho
            AgendamentoStatus.NO_SHOW: "#6B7280"  # Cinza
        }
        return colors.get(self.status_enum, "#6B7280")
    
    @property
    def time_str(self) -> str:
        """Retorna horário formatado"""
        if self.data_hora:
            return self.data_hora.strftime("%H:%M")
        return "--:--"
    
    @property
    def date_str(self) -> str:
        """Retorna data formatada"""
        if self.data_hora:
            return self.data_hora.strftime("%d/%m/%Y")
        return "--/--/----"


@dataclass
class Orientacao(BaseModel):
    """Modelo de Orientação"""
    
    student_id: int = 0
    title: str = ""
    theme: Optional[str] = None
    content: Optional[str] = None
    session_date: Optional[datetime] = None
    
    # Campos estruturados
    motivational_message: Optional[str] = None
    action_plan: List[Dict[str, Any]] = field(default_factory=list)
    is_markdown: bool = False
    
    # Anexos
    attachments: List[str] = field(default_factory=list)
    
    # Relacionamentos
    student_name: Optional[str] = None
    
    @property
    def preview(self) -> str:
        """Retorna preview do conteúdo"""
        if self.content:
            return self.content[:100] + "..." if len(self.content) > 100 else self.content
        return ""
    
    @property
    def action_plan_pending(self) -> int:
        """Retorna quantidade de tarefas pendentes"""
        return sum(1 for item in self.action_plan if not item.get('done', False))
    
    @property
    def action_plan_completed(self) -> int:
        """Retorna quantidade de tarefas concluídas"""
        return sum(1 for item in self.action_plan if item.get('done', False))


@dataclass
class Usuario(BaseModel):
    """Modelo de Usuário do sistema"""
    
    username: str = ""
    email: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_staff: bool = False
    
    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p)
    
    @property
    def iniciais(self) -> str:
        if self.full_name:
            return "".join([n[0] for n in self.full_name.split()[:2]]).upper()
        return self.username[:2].upper() if self.username else "??"


@dataclass
class Notificacao(BaseModel):
    """Modelo de Notificação"""
    
    title: str = ""
    message: str = ""
    notification_type: str = "info"  # info, warning, danger, success
    is_read: bool = False
    read_at: Optional[datetime] = None
    
    # Referência ao objeto relacionado
    related_object_type: Optional[str] = None
    related_object_id: Optional[int] = None
    
    @property
    def icon(self) -> str:
        icons = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'danger': '🔴',
            'success': '✅',
            'help': '🤝'
        }
        return icons.get(self.notification_type, '📌')


@dataclass
class MoodEntry(BaseModel):
    """Registro de humor/bem-estar"""
    
    student_id: int = 0
    mood_level: int = 3  # 1-5
    notes: Optional[str] = None
    entry_date: Optional[datetime] = None
    
    @property
    def mood_emoji(self) -> str:
        emojis = {
            1: "😢",
            2: "😕",
            3: "😐",
            4: "😊",
            5: "😄"
        }
        return emojis.get(self.mood_level, "😐")
    
    @property
    def mood_label(self) -> str:
        labels = {
            1: "Muito Ruim",
            2: "Ruim",
            3: "Neutro",
            4: "Bom",
            5: "Muito Bom"
        }
        return labels.get(self.mood_level, "Neutro")

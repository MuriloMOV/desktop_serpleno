from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base import ActiveMixin, CreatedAtMixin


@dataclass
class Estudante(ActiveMixin, CreatedAtMixin):
    id_estudante: int = 0
    nome: str = ""
    email: str = ""
    curso: str = ""
    matricula: str = ""
    telefone: str | None = None
    ultimo_contato: datetime | None = None
    atendimento_prioritario: bool = False
    tags: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.nome

    @property
    def course(self) -> str:
        return self.curso

    @property
    def contact(self) -> str:
        if self.telefone:
            return self.telefone
        return self.email

    @property
    def full_display(self) -> str:
        return f"{self.nome} ({self.matricula}) - {self.email}"

    @property
    def days_since_last_contact(self) -> int | None:
        if self.ultimo_contato is None:
            return None
        return (datetime.now() - self.ultimo_contato).days

    @property
    def needs_followup(self) -> bool:
        if self.days_since_last_contact is None:
            return False
        return self.days_since_last_contact > 30 or self.atendimento_prioritario

    def get_active_appointments(self) -> list[Any]:
        return []

    def get_completed_screenings(self) -> list[Any]:
        return []

    def get_active_goals(self) -> list[Any]:
        return []

    def get_mood_average(self) -> float | None:
        return None

    def update_last_contact(self) -> None:
        self.ultimo_contato = datetime.now()

    def set_attention(self) -> None:
        self.atendimento_prioritario = True

    def clear_attention(self) -> None:
        self.atendimento_prioritario = False

    def get_summary(self) -> dict[str, Any]:
        return {
            "id_estudante": self.id_estudante,
            "nome": self.nome,
            "curso": self.curso,
            "is_active": self.is_active,
            "needs_followup": self.needs_followup,
            "tags": self.tags,
        }

from dataclasses import dataclass
from datetime import datetime

from .base import ActiveMixin, TimestampMixin


@dataclass
class Disponibilidade(ActiveMixin, TimestampMixin):
    id_disponibilidade: int = 0
    dias: str = ""
    horario: str = ""
    analista_id: int = 0


@dataclass
class Agendamento(TimestampMixin):
    id_agendamento: int = 0
    aluno_id: int = 0
    disponibilidade_id: int = 0
    data: str = ""
    status: str = ""
    aluno_nome: str | None = None
    psicologo_nome: str | None = None
    observacoes: str | None = None
    motivo_cancelamento: str | None = None

    @property
    def date(self) -> str:
        return self.data

    @property
    def time(self) -> str | None:
        return None

    @property
    def notes(self) -> str:
        return self.observacoes or ""

    @property
    def is_upcoming(self) -> bool:
        try:
            appointment_date = datetime.strptime(self.data, "%Y-%m-%d").date()
            return appointment_date >= datetime.now().date()
        except ValueError:
            return True

    @property
    def is_past_due(self) -> bool:
        try:
            appointment_date = datetime.strptime(self.data, "%Y-%m-%d").date()
            return appointment_date < datetime.now().date()
        except ValueError:
            return False

    def mark_completed(self) -> None:
        self.status = "concluido"

    def mark_cancelled(self, motivo: str | None = None) -> None:
        self.status = "cancelado"
        self.motivo_cancelamento = motivo

    def mark_missed(self) -> None:
        self.status = "faltou"

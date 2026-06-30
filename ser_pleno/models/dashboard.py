from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Disponibilidade:
    id_disponibilidade: int
    dias: str
    horario: str
    is_active: bool
    analista_id: int


@dataclass
class Agendamento:
    id_agendamento: int
    aluno_id: int
    disponibilidade_id: int
    data: str
    status: str

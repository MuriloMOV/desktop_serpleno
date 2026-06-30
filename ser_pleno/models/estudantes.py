from dataclasses import dataclass
from typing import Optional


@dataclass
class Estudante:
    id_estudante: int
    nome: str
    email: str
    curso: str
    matricula: str

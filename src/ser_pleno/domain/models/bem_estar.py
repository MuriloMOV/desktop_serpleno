from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Autoavaliacao:
    id_autoavaliacao: int
    aluno_id: int
    data_avaliacao: Optional[date] = None
    bem_estar_academico: Optional[str] = None
    bem_estar_emocional: Optional[str] = None
    bem_estar_social: Optional[str] = None
    reflexoes_pessoais: Optional[str] = None
    pontos_xp: Optional[int] = None


@dataclass
class Gamificacao:
    id_gamificacao: int
    pontos_atuais: int
    nivel: str
    conquistas: str
    check_in: bool
    metas_pessoais: str
    aluno_id: int
    last_check_in_date: Optional[date] = None


@dataclass
class MeuHistorico:
    id_historico: int
    aluno_id: int
    humor_media: float
    dias_consecutivos: int
    total_registros: int


@dataclass
class RegistrosDiarios:
    id_registro: int
    aluno_id: int
    data: date
    humor: str
    observacoes: Optional[str] = None

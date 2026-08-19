from dataclasses import dataclass
from datetime import date


@dataclass
class Autoavaliacao:
    id_autoavaliacao: int
    aluno_id: int
    data_avaliacao: date | None = None
    bem_estar_academico: str | None = None
    bem_estar_emocional: str | None = None
    bem_estar_social: str | None = None
    reflexoes_pessoais: str | None = None
    pontos_xp: int | None = None


@dataclass
class Gamificacao:
    id_gamificacao: int
    pontos_atuais: int
    nivel: str
    conquistas: str
    check_in: bool
    metas_pessoais: str
    aluno_id: int
    last_check_in_date: date | None = None


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
    observacoes: str | None = None

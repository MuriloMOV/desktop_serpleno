"""
Models - Modelos de dados do Desktop SerPleno

Este módulo contém modelos ricos usando dataclasses com:
- Tipagem forte
- Propriedades computadas
- Métodos de serialização
- Enums para valores fixos

Uso:
    from models import Estudante, Agendamento, Orientacao
    
    # Criar um estudante
    estudante = Estudante(
        id=1,
        nome="João Silva",
        email="joao@email.com",
        curso="Engenharia"
    )
    
    # Usar propriedades computadas
    print(estudante.iniciais)  # "JS"
    print(estudante.to_dict())  # Converte para dict
"""

from .base import (
    BaseModel,
    Estudante,
    Agendamento,
    Orientacao,
    Usuario,
    Notificacao,
    MoodEntry,
    PriorityLevel,
    AgendamentoStatus
)

__all__ = [
    'BaseModel',
    'Estudante',
    'Agendamento',
    'Orientacao',
    'Usuario',
    'Notificacao',
    'MoodEntry',
    'PriorityLevel',
    'AgendamentoStatus',
]

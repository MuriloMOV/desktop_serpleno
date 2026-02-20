"""
Components - Componentes reutilizáveis para CustomTkinter

Este módulo contém componentes UI reutilizáveis seguindo os princípios de:
- Single Responsibility Principle (SRP)
- Don't Repeat Yourself (DRY)
- Composition over Inheritance

Uso:
    from components import KPICard, FormField, SearchField
    
    # Criar um card de KPI
    card = KPICard(parent, title="Atendimentos", value="42", icon="👥")
    
    # Criar um campo de formulário
    field = FormField(parent, label="Nome", placeholder="Digite...")
"""

from .cards import (
    KPICard,
    ContainerCard,
    AlertCard,
    StudentCard,
    HistoryCard
)

from .forms import (
    FormField,
    PasswordField,
    TextAreaField,
    SearchField,
    SelectField,
    CheckboxField,
    Form
)

__all__ = [
    # Cards
    'KPICard',
    'ContainerCard',
    'AlertCard',
    'StudentCard',
    'HistoryCard',
    # Forms
    'FormField',
    'PasswordField',
    'TextAreaField',
    'SearchField',
    'SelectField',
    'CheckboxField',
    'Form',
]

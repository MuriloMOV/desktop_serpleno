from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_THEME_HIERARCHY: dict[str, dict[str, Any]] = {
    "Geral": {
        "subthemes": ["Acolhimento", "Encaminhamento", "Fechamento"],
        "color": "#4F46E5",
        "icon": "📋",
    },
    "Acadêmico": {
        "subthemes": ["Estudo", "Tarefas", "Provas", "Aulas"],
        "color": "#2563EB",
        "icon": "📚",
    },
    "Emocional": {
        "subthemes": ["Ansiedade", "Frustração", "Autoestima", "Relacionamentos"],
        "color": "#DB2777",
        "icon": "❤️",
    },
    "Social": {
        "subthemes": ["Integração", "Bullying", "Amizades", "Família"],
        "color": "#0891B2",
        "icon": "👥",
    },
    "Familiar": {
        "subthemes": ["Comunicação", "Rotina", "Expectativas", "Apoio"],
        "color": "#EA580C",
        "icon": "🏠",
    },
    "Vocacional": {
        "subthemes": ["Interesses", "Habilidades", "Cursos", "Carreira"],
        "color": "#7C3AED",
        "icon": "🎯",
    },
}

_REQUIRED_TEMPLATE_FIELDS = {"label", "components"}


def get_theme_hierarchy(theme_id: str) -> dict[str, Any]:
    normalized = (theme_id or "").strip()
    return _THEME_HIERARCHY.get(normalized, {"subthemes": [], "color": "#666666", "icon": "📋"})


def validate_template_structure(template: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(template, dict):
        return {"valid": False, "errors": ["Template deve ser um dicionário"]}
    missing = list(_REQUIRED_TEMPLATE_FIELDS - set(template.keys()))
    errors: list[str] = []
    if missing:
        errors.append(f"Campos obrigatórios ausentes: {', '.join(missing)}")
    components = template.get("components")
    if not isinstance(components, list):
        errors.append("'components' deve ser uma lista")
    elif not components:
        errors.append("'components' não pode estar vazio")
    return {"valid": len(errors) == 0, "errors": errors, "template": template}


def render_orientation_content(content: Any, theme: str | None = None) -> str:
    text = str(content or "").strip()
    if not text:
        return ""
    theme_info = get_theme_hierarchy(theme or "Geral")
    header = f"Orientacao - {theme or 'Geral'} {theme_info.get('icon', '')}"
    rendered = f"{header}\n\n{text}"
    return rendered

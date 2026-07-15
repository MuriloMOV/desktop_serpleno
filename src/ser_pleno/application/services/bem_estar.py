# -*- coding: utf-8 -*-
"""Service de Bem-Estar —” orquestrador, sem SQL inline."""

from ser_pleno.repositories.bem_estar import BemEstarRepository
from ser_pleno.repositories.estudantes import EstudanteRepository
from ser_pleno.utils.mappers import safe_str


class ServicoBemEstar:
    def __init__(self, auth_service=None):
        self.repo = BemEstarRepository()
        self.repo_estudante = EstudanteRepository()

    def obter_dashboard(self):
        raw = self.repo.obter_dashboard()
        data = {
            "summary": {"average_mood": raw["avg"].get("average_mood") if raw["avg"] else None},
            "moods": raw["moods"],
            "checkins": raw["checkins"],
        }
        return {"success": True, "data": data}

    def listar_entradas_humor(self):
        result = self.repo.listar_entradas_humor()
        return {"success": True, "data": result}

    def obter_medias_humor(self):
        result = self.repo.obter_medias_humor()
        return {"success": True, "data": result}

    def obter_humor_estudante(self, id_estudante):
        result = self.repo.obter_humor_estudante(id_estudante)
        return {"success": True, "data": result}

    def listar_checkins(self):
        result = self.repo.listar_checkins()
        return {"success": True, "data": {"checkins": result}}

    def listar_estudantes_risco(self):
        rows = self.repo_estudante.listar(requer_atencao=True)
        groups = {"critical": [], "high": [], "medium": [], "low": []}
        for r in rows:
            priority = r.get("priority_level") or 0
            student = {
                "id": r.get("id_aluno"),
                "name": r.get("nome"),
                "reasons": [r.get("attention_reason") or "Requer atenção"],
            }
            if priority >= 4:
                groups["critical"].append(student)
            elif priority == 3:
                groups["high"].append(student)
            elif priority == 2:
                groups["medium"].append(student)
            else:
                groups["low"].append(student)
        return {"success": True, "data": {"groups": groups}}


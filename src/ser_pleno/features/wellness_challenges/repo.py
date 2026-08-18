# -*- coding: utf-8 -*-
"""Repositorio local de Wellness Challenges."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ser_pleno.infrastructure.local.local_cache import (
    local_cache,
    validate_table_name,
)
from ser_pleno.repositories.base import generate_local_id


class WellnessChallengeRepository:
    def listar_desafios(self, apenas_ativos: bool = True) -> List[Dict[str, Any]]:
        rows = local_cache.list_wellness_challenges()
        if apenas_ativos:
            rows = [r for r in rows if r.get("is_active", True)]
        return sorted(rows, key=lambda x: x.get("created_at") or "", reverse=True)

    def obter_desafio(self, challenge_id: int) -> Optional[Dict[str, Any]]:
        rows = local_cache.list_wellness_challenges()
        for r in rows:
            if r.get("id") == challenge_id:
                return r
        return None

    def criar_desafio(self, title: str, description: str, category: str,
                      difficulty: str, points: int = 0, is_active: bool = True) -> int:
        last_id = generate_local_id(None)
        challenge_data = {
            "id": last_id,
            "title": title,
            "description": description,
            "category": category,
            "difficulty": difficulty,
            "points": points,
            "is_active": is_active,
        }
        local_cache.upsert_wellness_challenge(challenge_data)
        return last_id

    def atualizar_desafio(self, challenge_id: int, **dados: Any) -> bool:
        row = self.obter_desafio(challenge_id)
        if not row:
            return False
        row.update(dados)
        local_cache.upsert_wellness_challenge(row)
        return True

    def deletar_desafio(self, challenge_id: int) -> bool:
        validate_table_name("wellness_challenges")
        local_cache.delete("wellness_challenges", "id", challenge_id)
        return True

    def listar_atribuicoes(self, student_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return local_cache.list_wellness_challenge_assignments(student_id=student_id)

    def obter_atribuicao(self, assignment_id: int) -> Optional[Dict[str, Any]]:
        rows = local_cache.list_wellness_challenge_assignments()
        for r in rows:
            if r.get("id") == assignment_id:
                return r
        return None

    def atribuir_desafio(self, challenge_id: int, student_id: int,
                         assigned_by_id: int, status: str = "assigned") -> int:
        last_id = generate_local_id(None)
        assignment_data = {
            "id": last_id,
            "challenge_id": challenge_id,
            "student_id": student_id,
            "assigned_by_id": assigned_by_id,
            "status": status,
        }
        local_cache.upsert_wellness_challenge_assignment(assignment_data)
        return last_id

    def desatribuir_desafio(self, assignment_id: int) -> bool:
        validate_table_name("wellness_challenge_assignments")
        local_cache.delete("wellness_challenge_assignments", "id", assignment_id)
        return True

    def completar_desafio(self, assignment_id: int) -> bool:
        row = self.obter_atribuicao(assignment_id)
        if not row:
            return False
        row["status"] = "completed"
        row["completed_at"] = "now"
        local_cache.upsert_wellness_challenge_assignment(row)
        return True

    def obter_dashboard(self) -> Dict[str, Any]:
        assignments = local_cache.list_wellness_challenge_assignments()
        total = len(assignments)
        completed = sum(1 for a in assignments if a.get("status") == "completed")
        return {
            "total_assignments": total,
            "completed": completed,
            "pending": total - completed,
            "completion_rate": round((completed / total) * 100) if total else 0,
        }

    def obter_desafios_estudante(self, student_id: int) -> List[Dict[str, Any]]:
        assignments = local_cache.list_wellness_challenge_assignments(student_id=student_id)
        challenges = {c.get("id"): c for c in local_cache.list_wellness_challenges()}
        result = []
        for a in assignments:
            ch = challenges.get(a.get("challenge_id"), {})
            merged = dict(a)
            merged["challenge"] = ch
            merged["challenge_title"] = ch.get("title", "Desafio")
            merged["is_completed"] = a.get("status") == "completed"
            merged["completed_at"] = a.get("completed_at")
            result.append(merged)
        return sorted(result, key=lambda x: x.get("assigned_at") or "", reverse=True)

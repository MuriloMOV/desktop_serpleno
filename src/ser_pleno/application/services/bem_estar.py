# -*- coding: utf-8 -*-
"""Service de Bem-Estar — orquestrador, sem SQL inline."""

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

    def criar_entrada_humor(self, dados):
        try:
            mood_id = self.repo.criar_entrada_humor(
                student_id=dados.get("student_id"),
                mood_level=dados.get("mood_level"),
                entry_date=dados.get("entry_date"),
                notes=dados.get("notes", ""),
            )
            return {"success": True, "message": "Entrada de humor registrada", "data": {"id": mood_id}}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def obter_medias_humor(self):
        result = self.repo.obter_medias_humor()
        return {"success": True, "data": result}

    def obter_humor_estudante(self, id_estudante):
        result = self.repo.obter_humor_estudante(id_estudante)
        return {"success": True, "data": result}

    def obter_historico_humor_estudante(self, id_estudante):
        result = self.repo.obter_humor_estudante(id_estudante)
        return {"success": True, "data": result}

    def listar_checkins(self):
        result = self.repo.listar_checkins()
        return {"success": True, "data": {"checkins": result}}

    def criar_checkin(self, dados):
        try:
            checkin_id = self.repo.criar_checkin(
                student_id=dados.get("student_id"),
                check_in_date=dados.get("check_in_date"),
                overall_wellbeing=dados.get("overall_wellbeing"),
                notes=dados.get("notes", ""),
            )
            return {"success": True, "message": "Check-in criado", "data": {"id": checkin_id}}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def obter_checkin(self, checkin_id):
        result = self.repo.obter_checkin(checkin_id)
        if result:
            return {"success": True, "data": result}
        return {"success": False, "message": "Check-in não encontrado"}

    def listar_desafios(self):
        result = self.repo.listar_desafios()
        return {"success": True, "data": result}

    def criar_desafio(self, dados):
        try:
            challenge_id = self.repo.criar_desafio(
                title=dados.get("title"),
                description=dados.get("description"),
                category=dados.get("category"),
                difficulty=dados.get("difficulty"),
                points=dados.get("points", 0),
            )
            return {"success": True, "message": "Desafio criado", "data": {"id": challenge_id}}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def atualizar_desafio(self, challenge_id, dados):
        try:
            self.repo.atualizar_desafio(challenge_id, **dados)
            return {"success": True, "message": "Desafio atualizado"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def deletar_desafio(self, challenge_id):
        try:
            self.repo.deletar_desafio(challenge_id)
            return {"success": True, "message": "Desafio deletado"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def atribuir_desafio(self, dados):
        try:
            assignment_id = self.repo.atribuir_desafio(
                challenge_id=dados.get("challenge_id"),
                student_id=dados.get("student_id"),
                assigned_by_id=dados.get("assigned_by_id"),
            )
            return {"success": True, "message": "Desafio atribuído", "data": {"id": assignment_id}}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def desatribuir_desafio(self, assignment_id):
        try:
            self.repo.desatribuir_desafio(assignment_id)
            return {"success": True, "message": "Desafio desatribuído"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def completar_desafio(self, assignment_id):
        try:
            self.repo.completar_desafio(assignment_id)
            return {"success": True, "message": "Desafio completado"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def listar_desafios_estudante(self, student_id):
        result = self.repo.listar_desafios_estudante(student_id)
        return {"success": True, "data": result}

    def obter_dashboard_desafios(self):
        result = self.repo.obter_dashboard_desafios()
        return {"success": True, "data": result}

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


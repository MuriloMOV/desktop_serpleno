# -*- coding: utf-8 -*-
"""Repositório de bem-estar."""

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    execute_non_query,
    with_local_fallback,
    local_cache,
    write_with_fallback,
    generate_local_id,
)


class BemEstarRepository:
    @with_local_fallback("_local_obter_dashboard")
    def obter_dashboard(self):
        moods = fetch_all("SELECT * FROM desktop_moodentry ORDER BY entry_date DESC LIMIT 10")
        checkins = fetch_all("SELECT * FROM desktop_wellnesscheckin ORDER BY check_in_date DESC LIMIT 10")
        avg = fetch_one("SELECT AVG(mood_level) as average_mood FROM desktop_moodentry")
        return {"moods": moods, "checkins": checkins, "avg": avg}

    def _local_obter_dashboard(self):
        moods = local_cache.list_wellness_moods()
        checkins = local_cache.list_wellness_checkins()
        moods_sorted = sorted(moods, key=lambda x: x.get("entry_date") or "", reverse=True)[:10]
        checkins_sorted = sorted(checkins, key=lambda x: x.get("check_in_date") or "", reverse=True)[:10]
        avg_mood = None
        if moods:
            avg_mood = sum(r.get("mood_level", 0) for r in moods) / len(moods)
        # Enrich checkins with student name for dashboard consistency
        name_map = local_cache.get_student_name_map()
        for c in checkins_sorted:
            c["student_name"] = name_map.get(c.get("student_id"), "Estudante")
            c["mood_score"] = c.get("overall_wellbeing")
        return {"moods": moods_sorted, "checkins": checkins_sorted, "avg": {"average_mood": avg_mood}}

    @with_local_fallback("_local_listar_entradas_humor")
    def listar_entradas_humor(self):
        return fetch_all("SELECT * FROM desktop_moodentry")

    def _local_listar_entradas_humor(self):
        return local_cache.list_wellness_moods()

    @with_local_fallback("_local_obter_medias_humor")
    def obter_medias_humor(self):
        return fetch_one("SELECT AVG(mood_level) as average_mood FROM desktop_moodentry")

    def _local_obter_medias_humor(self):
        rows = local_cache.list_wellness_moods()
        if rows:
            avg = sum(r.get("mood_level", 0) for r in rows) / len(rows)
            return {"average_mood": avg}
        return {"average_mood": None}

    @with_local_fallback("_local_obter_humor_estudante")
    def obter_humor_estudante(self, id_estudante):
        return fetch_all("SELECT * FROM desktop_moodentry WHERE student_id = %s", (id_estudante,))

    def _local_obter_humor_estudante(self, id_estudante):
        return local_cache.list_wellness_moods(student_id=id_estudante)

    @with_local_fallback("_local_listar_checkins")
    def listar_checkins(self):
        return fetch_all("SELECT * FROM desktop_wellnesscheckin ORDER BY check_in_date DESC LIMIT 20")

    def _local_listar_checkins(self):
        rows = local_cache.list_wellness_checkins()
        name_map = local_cache.get_student_name_map()
        for r in rows:
            r["student_name"] = name_map.get(r.get("student_id"), "Estudante")
            r["mood_score"] = r.get("overall_wellbeing")
            r["date"] = r.get("check_in_date")
        return sorted(rows, key=lambda x: x.get("check_in_date") or "", reverse=True)[:20]

    def criar_entrada_humor(self, student_id, mood_level, entry_date, notes=""):
        query = """
            INSERT INTO desktop_moodentry (student_id, mood_level, entry_date, notes, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """
        mood_data = {
            "student_id": student_id,
            "mood_level": mood_level,
            "entry_date": entry_date,
            "notes": notes,
        }

        def _mysql():
            return execute_non_query(query, (student_id, mood_level, entry_date, notes))

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            mood_data["id"] = last_id
            local_cache.upsert_wellness_mood(mood_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            mood_data["id"] = last_id
            return mood_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="wellness_moods", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def criar_checkin(self, student_id, check_in_date, overall_wellbeing, check_in_type="weekly",
                      attention_areas=None, recommendations="", professional_notes="",
                      follow_up_needed=False, follow_up_date=None):
        query = """
            INSERT INTO desktop_wellnesscheckin
                (student_id, check_in_date, check_in_type, overall_wellbeing,
                 attention_areas, recommendations, professional_notes,
                 follow_up_needed, follow_up_date, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        import json as _json
        attention_areas_json = _json.dumps(attention_areas or [])
        follow_up_needed_val = 1 if follow_up_needed else 0
        checkin_data = {
            "student_id": student_id,
            "check_in_date": check_in_date,
            "check_in_type": check_in_type,
            "overall_wellbeing": overall_wellbeing,
            "attention_areas": attention_areas or [],
            "recommendations": recommendations,
            "professional_notes": professional_notes,
            "follow_up_needed": follow_up_needed,
            "follow_up_date": follow_up_date,
        }

        def _mysql():
            return execute_non_query(
                query,
                (student_id, check_in_date, check_in_type, overall_wellbeing,
                 attention_areas_json, recommendations, professional_notes,
                 follow_up_needed_val, follow_up_date),
            )

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            checkin_data["id"] = last_id
            local_cache.upsert_wellness_checkin(checkin_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            checkin_data["id"] = last_id
            return checkin_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="wellness_checkins", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def obter_checkin(self, checkin_id):
        query = "SELECT * FROM desktop_wellnesscheckin WHERE id = %s"
        return fetch_one(query, (checkin_id,))

    def listar_desafios(self):
        return fetch_all("SELECT * FROM wellness_challenges ORDER BY created_at DESC")

    def criar_desafio(self, title, description, category, difficulty, points=0):
        query = """
            INSERT INTO wellness_challenges (title, description, category, difficulty, points, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, 1, NOW())
        """
        challenge_data = {
            "title": title,
            "description": description,
            "category": category,
            "difficulty": difficulty,
            "points": points,
            "is_active": 1,
        }

        def _mysql():
            return execute_non_query(query, (title, description, category, difficulty, points))

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            challenge_data["id"] = last_id
            local_cache.upsert_wellness_challenge(challenge_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            challenge_data["id"] = last_id
            return challenge_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="wellness_challenges", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def atualizar_desafio(self, challenge_id, **dados):
        sets = []
        params = []
        for key, value in dados.items():
            sets.append(f"{key} = %s")
            params.append(value)
        params.append(challenge_id)
        query = f"UPDATE wellness_challenges SET {', '.join(sets)} WHERE id = %s"
        challenge_data = {"id": challenge_id}
        challenge_data.update(dados)

        def _mysql():
            execute_non_query(query, params)
            return 1

        def _local(mysql_result):
            local_cache.upsert_wellness_challenge(challenge_data)
            return 1

        def _queue_data(mysql_result, entity_id):
            return challenge_data

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="wellness_challenges", entity_id=challenge_id,
            queue_data_fn=_queue_data,
        )

    def deletar_desafio(self, challenge_id):
        query = "DELETE FROM wellness_challenges WHERE id = %s"

        def _mysql():
            execute_non_query(query, (challenge_id,))
            return 1

        def _local(mysql_result):
            local_cache.delete("wellness_challenges", "id", challenge_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="wellness_challenges", entity_id=challenge_id,
            queue_data_fn=lambda r, eid: {"id": challenge_id},
        )

    def atribuir_desafio(self, challenge_id, student_id, assigned_by_id):
        query = """
            INSERT INTO wellness_challenge_assignments (challenge_id, student_id, assigned_by_id, status, assigned_at)
            VALUES (%s, %s, %s, 'assigned', NOW())
        """
        assignment_data = {
            "challenge_id": challenge_id,
            "student_id": student_id,
            "assigned_by_id": assigned_by_id,
            "status": "assigned",
        }

        def _mysql():
            return execute_non_query(query, (challenge_id, student_id, assigned_by_id))

        def _local(mysql_result):
            last_id = generate_local_id(mysql_result)
            assignment_data["id"] = last_id
            local_cache.upsert_wellness_challenge_assignment(assignment_data)
            return last_id

        def _queue_data(mysql_result, entity_id):
            last_id = generate_local_id(mysql_result)
            assignment_data["id"] = last_id
            return assignment_data

        last_id = write_with_fallback(
            _mysql, _local,
            operation="create", entity="wellness_challenge_assignments", entity_id="novo",
            queue_data_fn=_queue_data,
        )
        return last_id

    def desatribuir_desafio(self, assignment_id):
        query = "DELETE FROM wellness_challenge_assignments WHERE id = %s"

        def _mysql():
            execute_non_query(query, (assignment_id,))
            return 1

        def _local(mysql_result):
            local_cache.delete("wellness_challenge_assignments", "id", assignment_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="delete", entity="wellness_challenge_assignments", entity_id=assignment_id,
            queue_data_fn=lambda r, eid: {"id": assignment_id},
        )

    def completar_desafio(self, assignment_id):
        query = "UPDATE wellness_challenge_assignments SET status = 'completed', completed_at = NOW() WHERE id = %s"

        def _mysql():
            execute_non_query(query, (assignment_id,))
            return 1

        def _local(mysql_result):
            local_cache.update("wellness_challenge_assignments", {"status": "completed", "completed_at": "now"}, "id", assignment_id)
            return 1

        return write_with_fallback(
            _mysql, _local,
            operation="update", entity="wellness_challenge_assignments", entity_id=assignment_id,
            queue_data_fn=lambda r, eid: {"id": assignment_id, "status": "completed"},
        )

    def listar_desafios_estudante(self, student_id):
        query = """
            SELECT a.*, c.title, c.description, c.category, c.difficulty, c.points
            FROM wellness_challenge_assignments a
            INNER JOIN wellness_challenges c ON a.challenge_id = c.id
            WHERE a.student_id = %s
            ORDER BY a.assigned_at DESC
        """
        return fetch_all(query, (student_id,))

    def obter_dashboard_desafios(self):
        total = fetch_one("SELECT COUNT(*) as total FROM wellness_challenge_assignments")
        completed = fetch_one("SELECT COUNT(*) as total FROM wellness_challenge_assignments WHERE status = 'completed'")
        return {
            "total_assignments": total.get("total") if total else 0,
            "completed": completed.get("total") if completed else 0,
        }

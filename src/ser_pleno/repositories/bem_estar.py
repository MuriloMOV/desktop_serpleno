# -*- coding: utf-8 -*-
"""Repositório de bem-estar."""

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    with_local_fallback,
    local_cache,
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

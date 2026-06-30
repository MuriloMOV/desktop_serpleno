# -*- coding: utf-8 -*-
"""Repositório de bem-estar."""

from repositories.base import fetch_all, fetch_one


class BemEstarRepository:
    def obter_dashboard(self):
        moods = fetch_all("SELECT * FROM desktop_moodentry ORDER BY entry_date DESC LIMIT 10")
        checkins = fetch_all("SELECT * FROM desktop_wellnesscheckin ORDER BY check_in_date DESC LIMIT 10")
        avg = fetch_one("SELECT AVG(mood_level) as average_mood FROM desktop_moodentry")
        return {"moods": moods, "checkins": checkins, "avg": avg}

    def listar_entradas_humor(self):
        return fetch_all("SELECT * FROM desktop_moodentry")

    def obter_medias_humor(self):
        return fetch_one("SELECT AVG(mood_level) as average_mood FROM desktop_moodentry")

    def obter_humor_estudante(self, id_estudante):
        return fetch_all("SELECT * FROM desktop_moodentry WHERE student_id = %s", (id_estudante,))

    def listar_checkins(self):
        return fetch_all("SELECT * FROM desktop_wellnesscheckin ORDER BY check_in_date DESC LIMIT 20")

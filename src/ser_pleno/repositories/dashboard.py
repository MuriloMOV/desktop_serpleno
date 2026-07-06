# -*- coding: utf-8 -*-
"""Repositório de dashboard/bem-estar."""

from ser_pleno.repositories.base import fetch_all, fetch_one


class DashboardRepository:
    def obter_kpis(self):
        return {
            "appointments_today": self._contar_agendamentos_hoje(),
            "screenings_pending": self._contar_triagens_pendentes(),
            "alerts": self._contar_alertas_nao_lidos(),
            "total_students": self._contar_alunos(),
            "attention_students": self._estudantes_atencao(),
            "upcoming_appointments": self._proximos_agendamentos(5),
            "media_humor": self._media_humor_hoje(),
            "humor_history": self._historico_humor_30_dias(),
            "bem_estar_dimensions": self._bem_estar_dimensoes(),
            "available_slots": self._vagas_disponiveis(),
        }

    def _contar_agendamentos_hoje(self):
        result = fetch_one("SELECT COUNT(*) as total FROM agendamento WHERE DATE(data_hora) = CURDATE()")
        return result.get("total") if result else 0

    def _contar_triagens_pendentes(self):
        result = fetch_one("SELECT COUNT(*) as total FROM desktop_screening WHERE status = 'pending'")
        return result.get("total") if result else 0

    def _contar_alertas_nao_lidos(self):
        result = fetch_one("SELECT COUNT(*) as total FROM desktop_alert WHERE is_read = 0")
        return result.get("total") if result else 0

    def _contar_alunos(self):
        result = fetch_one("SELECT COUNT(*) as total FROM aluno")
        return result.get("total") if result else 0

    def _estudantes_atencao(self):
        query = "SELECT id_aluno, nome, attention_reason, priority_level FROM aluno WHERE requires_attention = 1"
        rows = fetch_all(query)
        return [
            {
                "id": r.get("id_aluno"),
                "name": r.get("nome"),
                "attention_reason": r.get("attention_reason") or r.get("attention_notes") or "Requer atenção",
                "priority_level": r.get("priority_level") or 0,
            }
            for r in rows
        ]

    def _proximos_agendamentos(self, limite=5):
        query = """
            SELECT a.id, a.data_hora, a.status, al.nome AS student_name, al.curso
            FROM agendamento a
            LEFT JOIN aluno al ON a.student_id = al.id_aluno
            WHERE a.data_hora > NOW() AND a.status != 'cancelled'
            ORDER BY a.data_hora ASC
            LIMIT %s
        """
        rows = fetch_all(query, (limite,))
        resultado = []
        for r in rows:
            data_hora = r.get("data_hora")
            resultado.append(
                {
                    "id": r.get("id"),
                    "student_name": r.get("student_name") or "Estudante",
                    "curso": r.get("curso") or "Curso não informado",
                    "time": data_hora.strftime("%H:%M") if hasattr(data_hora, "strftime") else "--:--",
                    "date": data_hora.strftime("%Y-%m-%d") if hasattr(data_hora, "strftime") else str(data_hora),
                }
            )
        return resultado

    def _media_humor_hoje(self):
        result = fetch_one(
            "SELECT AVG(mood_level) as media_humor FROM desktop_moodentry WHERE DATE(entry_date) = CURDATE()"
        )
        valor = result.get("media_humor") if result else None
        return round(valor, 2) if valor else None

    def _historico_humor_30_dias(self):
        query = """
            SELECT DATE(entry_date) as data, AVG(mood_level) as media_humor
            FROM desktop_moodentry
            WHERE DATE(entry_date) >= CURDATE() - INTERVAL 30 DAY
            GROUP BY DATE(entry_date)
            ORDER BY data
        """
        rows = fetch_all(query)
        return [
            {
                "data": r["data"].strftime("%d/%m") if hasattr(r["data"], "strftime") else str(r["data"]),
                "media_humor": round(r["media_humor"], 2) if r.get("media_humor") else 0,
            }
            for r in rows
        ]

    def _bem_estar_dimensoes(self):
        result = fetch_one(
            "SELECT AVG(overall_wellbeing) as media_bem_estar FROM desktop_wellnesscheckin WHERE DATE(check_in_date) >= CURDATE() - INTERVAL 7 DAY"
        )
        media = result.get("media_bem_estar") if result else 0
        media = round(media, 2) if media else 0
        return {
            "academico": round(media * 0.9, 2),
            "emocional": round(media * 0.8, 2),
            "social": round(media * 0.85, 2),
        }

    def _vagas_disponiveis(self):
        total = fetch_one("SELECT COUNT(*) as total FROM disponibilidade WHERE is_active = 1")
        agendados = fetch_one("SELECT COUNT(*) as total FROM agendamento WHERE DATE(data_hora) = CURDATE() AND status != 'canceled'")
        total_disp = total.get("total") if total else 0
        total_agend = agendados.get("total") if agendados else 0
        return max(0, total_disp - total_agend)

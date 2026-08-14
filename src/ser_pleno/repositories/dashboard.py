# -*- coding: utf-8 -*-
"""Repositório de dashboard/bem-estar."""

from ser_pleno.repositories.base import (
    fetch_all,
    fetch_one,
    fetch_all_batch,
    fetch_one_batch,
    execute_non_query,
    with_local_fallback,
    local_cache,
)
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
import time


# TTL cache simples em memória para KPIs do dashboard.
_DASHBOARD_CACHE_TTL = 20  # segundos
_dashboard_cache = {
    "data": None,
    "ts": 0.0,
}


def invalidate_dashboard_cache() -> None:
    """Invalida o cache de KPIs do dashboard."""
    _dashboard_cache["ts"] = 0.0


class DashboardRepository:
    @with_local_fallback("_local_obter_kpis")
    def obter_kpis(self):
        agora = time.time()
        cached = _dashboard_cache["data"]
        if cached is not None and (agora - _dashboard_cache["ts"]) < _DASHBOARD_CACHE_TTL:
            return dict(cached)

        data = self._contar_kpis_consolidado()
        _dashboard_cache["data"] = data
        _dashboard_cache["ts"] = agora
        return dict(data)

    def _contar_kpis_consolidado(self):
        # Executa o count principal + helpers em batch para reutilizar conexão.
        base_query = """
            SELECT
                (SELECT COUNT(*) FROM aluno) AS total_alunos,
                (SELECT COUNT(*) FROM aluno WHERE requires_attention = 1) AS total_atencao,
                (SELECT COUNT(*) FROM agendamento WHERE DATE(data_hora) = CURDATE()) AS agendamentos_hoje,
                (SELECT COUNT(*) FROM desktop_screening WHERE status = 'pending') AS triagens_pendentes,
                (SELECT COUNT(*) FROM desktop_alert WHERE is_read = 0) AS alertas_nao_lidos,
                (SELECT COUNT(*) FROM disponibilidade WHERE is_active = 1) AS total_disponibilidade,
                (SELECT COUNT(*) FROM agendamento WHERE DATE(data_hora) = CURDATE() AND status != 'canceled') AS agendamentos_hoje_ativos,
                (SELECT AVG(mood_level) FROM desktop_moodentry WHERE DATE(entry_date) = CURDATE()) AS media_humor_hoje,
                (SELECT AVG(overall_wellbeing) FROM desktop_wellnesscheckin WHERE DATE(check_in_date) >= CURDATE() - INTERVAL 7 DAY) AS media_bem_estar
            """
        attention_query = "SELECT id_aluno, nome, attention_reason, priority_level FROM aluno WHERE requires_attention = 1"
        upcoming_query = """
            SELECT a.id, a.data_hora, a.status, al.nome AS student_name, al.curso
            FROM agendamento a
            LEFT JOIN aluno al ON a.student_id = al.id_aluno
            WHERE a.data_hora > NOW() AND a.status != 'cancelled'
            ORDER BY a.data_hora ASC
            LIMIT %s
        """
        humor_query = """
            SELECT DATE(entry_date) as data, AVG(mood_level) as media_humor
            FROM desktop_moodentry
            WHERE DATE(entry_date) >= CURDATE() - INTERVAL 30 DAY
            GROUP BY DATE(entry_date)
            ORDER BY data
        """
        bem_estar_query = """
            SELECT AVG(overall_wellbeing) as media_bem_estar FROM desktop_wellnesscheckin WHERE DATE(check_in_date) >= CURDATE() - INTERVAL 7 DAY
        """

        base_row, attention_rows, upcoming_rows, humor_rows, bem_estar_row = fetch_one_batch([
            (base_query, ()),
            (attention_query, ()),
            (upcoming_query, (5,)),
            (humor_query, ()),
            (bem_estar_query, ()),
        ])

        base = base_row or {}
        attention_students = [
            {
                "id": r.get("id_aluno"),
                "name": r.get("nome"),
                "attention_reason": r.get("attention_reason") or r.get("attention_notes") or "Requer atenção",
                "priority_level": r.get("priority_level") or 0,
            }
            for r in attention_rows
        ]

        upcoming_appointments = []
        for r in upcoming_rows:
            data_hora = r.get("data_hora")
            upcoming_appointments.append(
                {
                    "id": r.get("id"),
                    "student_name": r.get("student_name") or "Estudante",
                    "curso": r.get("curso") or "Curso não informado",
                    "time": data_hora.strftime("%H:%M") if hasattr(data_hora, "strftime") else "--:--",
                    "date": data_hora.strftime("%Y-%m-%d") if hasattr(data_hora, "strftime") else str(data_hora),
                }
            )

        humor_history = [
            {
                "data": r["data"].strftime("%d/%m") if hasattr(r["data"], "strftime") else str(r["data"]),
                "media_humor": round(r["media_humor"], 2) if r.get("media_humor") else 0,
            }
            for r in humor_rows
        ]

        bem_estar_media = bem_estar_row.get("media_bem_estar") if bem_estar_row else 0
        bem_estar_media = round(bem_estar_media, 2) if bem_estar_media else 0
        bem_estar_dimensions = {
            "academico": round(bem_estar_media * 0.9, 2),
            "emocional": round(bem_estar_media * 0.8, 2),
            "social": round(bem_estar_media * 0.85, 2),
        }

        recent_query = """
            SELECT a.id, a.data_hora, a.status, al.nome AS student_name, al.curso
            FROM agendamento a
            LEFT JOIN aluno al ON a.student_id = al.id_aluno
            WHERE a.data_hora <= NOW() AND a.status = 'completed'
            ORDER BY a.data_hora DESC
            LIMIT %s
        """
        recent_rows = fetch_all(recent_query, (5,))

        recent_appointments = []
        for r in recent_rows:
            data_hora = r.get("data_hora")
            recent_appointments.append(
                {
                    "id": r.get("id"),
                    "student_name": r.get("student_name") or "Estudante",
                    "curso": r.get("curso") or "Curso não informado",
                    "time": data_hora.strftime("%H:%M") if hasattr(data_hora, "strftime") else "--:--",
                    "date": data_hora.strftime("%Y-%m-%d") if hasattr(data_hora, "strftime") else str(data_hora),
                    "status": r.get("status") or "completed",
                }
            )

        total_disp = base.get("total_disponibilidade") or 0
        total_agend = base.get("agendamentos_hoje_ativos") or 0

        return {
            "appointments_today": base.get("agendamentos_hoje") or 0,
            "screenings_pending": base.get("triagens_pendentes") or 0,
            "alerts": base.get("alertas_nao_lidos") or 0,
            "total_students": base.get("total_alunos") or 0,
            "attention_students": attention_students,
            "upcoming_appointments": upcoming_appointments,
            "recent_appointments": recent_appointments,
            "media_humor": round(base.get("media_humor_hoje"), 2) if base.get("media_humor_hoje") else None,
            "humor_history": humor_history,
            "bem_estar_dimensions": bem_estar_dimensions,
            "available_slots": max(0, total_disp - total_agend),
        }

    def _local_obter_kpis(self):
        return {
            "appointments_today": self._local_contar_agendamentos_hoje(),
            "screenings_pending": self._local_contar_triagens_pendentes(),
            "alerts": self._local_contar_alertas_nao_lidos(),
            "total_students": self._local_contar_alunos(),
            "attention_students": self._local_estudantes_atencao(),
            "upcoming_appointments": self._local_proximos_agendamentos(5),
            "recent_appointments": self._local_proximos_atendimentos_recentes(5),
            "media_humor": self._local_media_humor_hoje(),
            "humor_history": self._local_historico_humor_30_dias(),
            "bem_estar_dimensions": self._local_bem_estar_dimensoes(),
            "available_slots": 0,
        }

    def _contar_agendamentos_hoje(self):
        result = fetch_one("SELECT COUNT(*) as total FROM agendamento WHERE DATE(data_hora) = CURDATE()")
        return result.get("total") if result else 0

    def _local_contar_agendamentos_hoje(self):
        hoje = datetime.now().strftime("%Y-%m-%d")
        rows = local_cache.list_appointments(data=hoje)
        return len(rows)

    def _contar_triagens_pendentes(self):
        result = fetch_one("SELECT COUNT(*) as total FROM desktop_screening WHERE status = 'pending'")
        return result.get("total") if result else 0

    def _local_contar_triagens_pendentes(self):
        rows = local_cache.list_screenings()
        return sum(1 for r in rows if r.get("status") == "pending")

    def _contar_alertas_nao_lidos(self):
        result = fetch_one("SELECT COUNT(*) as total FROM desktop_alert WHERE is_read = 0")
        return result.get("total") if result else 0

    def _local_contar_alertas_nao_lidos(self):
        rows = local_cache.list_alerts()
        return sum(1 for r in rows if not r.get("is_read"))

    def _contar_alunos(self):
        result = fetch_one("SELECT COUNT(*) as total FROM aluno")
        return result.get("total") if result else 0

    def _local_contar_alunos(self):
        rows = local_cache.list_students()
        return len(rows)

    def _estudantes_atencao(self, cursor=None):
        query = "SELECT id_aluno, nome, attention_reason, priority_level FROM aluno WHERE requires_attention = 1"
        if cursor is not None:
            cursor.execute(query)
            rows = cursor.fetchall()
        else:
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

    def _local_estudantes_atencao(self):
        rows = local_cache.list_students()
        return [
            {
                "id": r.get("id"),
                "name": r.get("nome"),
                "attention_reason": "Requer atenção",
                "priority_level": 0,
            }
            for r in rows
            if r.get("requires_attention")
        ]

    def _proximos_agendamentos(self, limite=5, cursor=None):
        query = """
            SELECT a.id, a.data_hora, a.status, al.nome AS student_name, al.curso
            FROM agendamento a
            LEFT JOIN aluno al ON a.student_id = al.id_aluno
            WHERE a.data_hora > NOW() AND a.status != 'cancelled'
            ORDER BY a.data_hora ASC
            LIMIT %s
        """
        if cursor is not None:
            cursor.execute(query, (limite,))
            rows = cursor.fetchall()
        else:
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

    def _local_proximos_agendamentos(self, limite=5):
        rows = local_cache.list_all(
            "appointments",
            where_clause="status != ?",
            params=("cancelled",),
        )
        rows = sorted(rows, key=lambda x: x.get("data_hora") or "")[:limite]
        resultado = []
        for r in rows:
            data_hora = r.get("data_hora") or ""
            resultado.append({
                "id": r.get("id"),
                "student_name": "Estudante",
                "curso": "Curso não informado",
                "time": data_hora[11:16] if len(data_hora) >= 16 else "--:--",
                "date": data_hora[:10] if len(data_hora) >= 10 else str(data_hora),
            })
        return resultado

    def _local_proximos_atendimentos_recentes(self, limite=5):
        rows = local_cache.list_all(
            "appointments",
            where_clause="status = ?",
            params=("completed",),
        )
        rows = sorted(rows, key=lambda x: x.get("data_hora") or "", reverse=True)[:limite]
        resultado = []
        for r in rows:
            data_hora = r.get("data_hora") or ""
            resultado.append({
                "id": r.get("id"),
                "student_name": "Estudante",
                "curso": "Curso não informado",
                "time": data_hora[11:16] if len(data_hora) >= 16 else "--:--",
                "date": data_hora[:10] if len(data_hora) >= 10 else str(data_hora),
                "status": "completed",
            })
        return resultado

    def _media_humor_hoje(self):
        result = fetch_one(
            "SELECT AVG(mood_level) as media_humor FROM desktop_moodentry WHERE DATE(entry_date) = CURDATE()"
        )
        valor = result.get("media_humor") if result else None
        return round(valor, 2) if valor else None

    def _local_media_humor_hoje(self):
        rows = local_cache.list_wellness_moods()
        hoje = datetime.now().strftime("%Y-%m-%d")
        rows_hoje = [r for r in rows if (r.get("entry_date") or "").startswith(hoje)]
        if rows_hoje:
            avg = sum(r.get("mood_level", 0) for r in rows_hoje) / len(rows_hoje)
            return round(avg, 2)
        return None

    def _historico_humor_30_dias(self, cursor=None):
        query = """
            SELECT DATE(entry_date) as data, AVG(mood_level) as media_humor
            FROM desktop_moodentry
            WHERE DATE(entry_date) >= CURDATE() - INTERVAL 30 DAY
            GROUP BY DATE(entry_date)
            ORDER BY data
        """
        if cursor is not None:
            cursor.execute(query)
            rows = cursor.fetchall()
        else:
            rows = fetch_all(query)
        return [
            {
                "data": r["data"].strftime("%d/%m") if hasattr(r["data"], "strftime") else str(r["data"]),
                "media_humor": round(r["media_humor"], 2) if r.get("media_humor") else 0,
            }
            for r in rows
        ]

    def _local_historico_humor_30_dias(self):
        rows = local_cache.list_wellness_moods()
        from collections import defaultdict
        agrupado: Dict[str, List[int]] = defaultdict(list)
        for r in rows:
            entry_date = r.get("entry_date") or ""
            data = entry_date[:10] if len(entry_date) >= 10 else entry_date
            agrupado[data].append(r.get("mood_level", 0))
        resultado = []
        for data, valores in sorted(agrupado.items()):
            media = sum(valores) / len(valores)
            data_fmt = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m")
            resultado.append({"data": data_fmt, "media_humor": round(media, 2)})
        return resultado

    def _bem_estar_dimensoes(self, cursor=None):
        query = "SELECT AVG(overall_wellbeing) as media_bem_estar FROM desktop_wellnesscheckin WHERE DATE(check_in_date) >= CURDATE() - INTERVAL 7 DAY"
        if cursor is not None:
            cursor.execute(query)
            result = cursor.fetchone()
        else:
            result = fetch_one(query)
        media = result.get("media_bem_estar") if result else 0
        media = round(media, 2) if media else 0
        return {
            "academico": round(media * 0.9, 2),
            "emocional": round(media * 0.8, 2),
            "social": round(media * 0.85, 2),
        }

    def _local_bem_estar_dimensoes(self):
        rows = local_cache.list_wellness_checkins()
        if rows:
            avg = sum(r.get("overall_wellbeing", 0) for r in rows) / len(rows)
        else:
            avg = 0
        media = round(avg, 2)
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

    def _local_vagas_disponiveis(self):
        # Disponibilidade não é sincronizada; retorna 0
        return 0

    @with_local_fallback("_local_obter_notificacoes_alertas")
    def obter_notificacoes_alertas(self):
        """Obtém notificações de alertas do sistema."""
        query = """
            SELECT id, alert_type, message, created_at, is_read
            FROM desktop_alert
            WHERE is_read = 0
            ORDER BY created_at DESC
        """
        rows = fetch_all(query)
        return [
            {
                "id": alerta["id"],
                "titulo": self._formatar_tipo_alerta(alerta["alert_type"]) or "Alerta",
                "descricao": alerta["message"] or "Mensagem de alerta",
                "data": alerta["created_at"].strftime("%Y-%m-%d") if hasattr(alerta["created_at"], "strftime") else str(alerta["created_at"]),
                "lida": alerta["is_read"],
            }
            for alerta in rows
        ]

    def _local_obter_notificacoes_alertas(self):
        rows = local_cache.list_alerts()
        rows = [r for r in rows if not r.get("is_read")]
        return [
            {
                "id": alerta["id"],
                "titulo": self._formatar_tipo_alerta(alerta.get("alert_type")) or "Alerta",
                "descricao": alerta.get("message") or "Mensagem de alerta",
                "data": str(alerta.get("created_at", ""))[:10],
                "lida": alerta.get("is_read"),
            }
            for alerta in rows
        ]

    @with_local_fallback("_local_marcar_notificacao_como_lida")
    def marcar_notificacao_como_lida(self, notificacao_id):
        """Marca uma notificação como lida."""
        query = "UPDATE desktop_alert SET is_read = 1 WHERE id = %s"
        return execute_non_query(query, (notificacao_id,))

    def _local_marcar_notificacao_como_lida(self, notificacao_id):
        local_cache.update("alerts", {"is_read": 1}, "id", notificacao_id)
        return 1

    def _formatar_tipo_alerta(self, alert_type):
        """Formata o tipo de alerta para exibição."""
        tipos = {
            "screening_pending": "Triagem Pendente",
            "appointment_reminder": "Lembrete de Consulta",
            "followup_required": "Acompanhamento Necessário",
            "high_risk": "Alto Risco",
            "missed_appointment": "Falta em Consulta",
            "system": "Alerta do Sistema",
        }
        return tipos.get(alert_type, alert_type.replace("_", " ").title() if alert_type else "Alerta")

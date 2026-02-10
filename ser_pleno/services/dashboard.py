from config.db_config import get_db_connection
from services import api

class ServicoDashboard:
    def obter_kpis(self):
        """Obtém estatísticas consolidadas do dashboard via banco de dados."""
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Obter contadores
        cursor.execute("SELECT COUNT(*) as total FROM agendamento WHERE DATE(data_hora) = CURDATE()")
        appointments_today = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM desktop_screening WHERE status = 'pending'")
        screenings_pending = cursor.fetchone()['total']

        # Alertas não lidos: is_read = 0
        cursor.execute("SELECT COUNT(*) as total FROM desktop_alert WHERE is_read = 0")
        alerts = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM aluno")
        total_students = cursor.fetchone()['total']

        # Calcular taxa de presença (proporção de agendamentos realizados nos últimos 30 dias)
        try:
            cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed FROM agendamento WHERE DATE(data_hora) >= CURDATE() - INTERVAL 30 DAY")
            row = cursor.fetchone()
            total_appts = row.get('total') or 0
            completed = row.get('completed') or 0
            attendance_rate = round((completed / total_appts * 100), 1) if total_appts else None
        except Exception:
            attendance_rate = None

        # Obter estudantes em atenção (mapear campos esperados pela UI)
        cursor.execute("SELECT id_aluno, nome, attention_reason, priority_level FROM aluno WHERE requires_attention = 1")
        rows = cursor.fetchall()
        attention_students = []
        for r in rows:
            attention_students.append({
                'id': r.get('id_aluno'),
                'name': r.get('nome'),
                'attention_reason': r.get('attention_reason') or r.get('attention_notes') or 'Requer atenção',
                'priority_level': r.get('priority_level') or 0
            })

        # Obter próximos agendamentos, juntando com aluno para obter nome
        cursor.execute("""
            SELECT a.id, a.data_hora, a.status, al.nome AS student_name
            FROM agendamento a
            LEFT JOIN aluno al ON a.student_id = al.id_aluno
            WHERE DATE(a.data_hora) > CURDATE()
            ORDER BY a.data_hora ASC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        upcoming_appointments = []
        for r in rows:
            data_hora = r.get('data_hora')
            # Formatar data e horário
            try:
                date_str = data_hora.strftime('%Y-%m-%d') if hasattr(data_hora, 'strftime') else str(data_hora)
                time_str = data_hora.strftime('%H:%M') if hasattr(data_hora, 'strftime') else '--:--'
            except Exception:
                date_str = str(data_hora) or ''
                time_str = '--:--'
            upcoming_appointments.append({
                'id': r.get('id'),
                'student_name': r.get('student_name') or 'Estudante',
                'time': time_str,
                'date': date_str
            })

        connection.close()

        return {
            "appointments_today": appointments_today,
            "screenings_pending": screenings_pending,
            "alerts": alerts,
            "total_students": total_students,
            "attendance_rate": attendance_rate,
            "attention_students": attention_students,
            "upcoming_appointments": upcoming_appointments
        }


class DashboardService:
    """Wrapper compatível com a interface esperada pelos testes (get_kpis)."""
    def __init__(self):
        self._svc = ServicoDashboard()

    def get_kpis(self):
        return self._svc.obter_kpis()

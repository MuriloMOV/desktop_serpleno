from config.db_config import get_db_connection
from services import api

class ServicoDashboard:
    def obter_kpis(self):
        """Obtém estatísticas consolidadas do dashboard via banco de dados."""
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Obter contadores
        cursor.execute("SELECT COUNT(*) as total FROM desktop_appointment WHERE date = CURDATE()")
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
            cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed FROM desktop_appointment WHERE date >= CURDATE() - INTERVAL 30 DAY")
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

        # Obter próximos agendamentos, juntando com aluno e disponibilidade para obter nome e horário
        cursor.execute("""
            SELECT da.id, da.date, da.status, a.nome AS student_name, COALESCE(t.horario, '') AS time_horario
            FROM desktop_appointment da
            LEFT JOIN aluno a ON da.student_id = a.id_aluno
            LEFT JOIN disponibilidade t ON da.time = t.id_disponibilidade
            WHERE da.date > CURDATE()
            ORDER BY da.date ASC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        upcoming_appointments = []
        for r in rows:
            time_val = r.get('time_horario')
            # Se for time object, formatar; caso contrário, deixar como string
            try:
                time_str = time_val.strftime('%H:%M') if hasattr(time_val, 'strftime') else (str(time_val) if time_val else '--:--')
            except Exception:
                time_str = str(time_val) or '--:--'
            upcoming_appointments.append({
                'id': r.get('id'),
                'student_name': r.get('student_name') or 'Estudante',
                'time': time_str,
                'date': str(r.get('date'))
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

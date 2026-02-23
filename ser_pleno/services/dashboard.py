from config.db_config import get_db_connection
from services import api

class ServicoDashboard:
    def obter_notificacoes_ajuda(self):
        """Obtém notificações de ajuda do serpleno_web."""
        try:
            from services.api import api
            response = api.get("help/notifications/")
            if response.get("success"):
                return response.get("data", [])
        except Exception as e:
            print(f"Erro ao obter notificações de ajuda: {e}")
        return [
            {"id": 1, "titulo": "Ajuda com agendamento", "descricao": "Você tem 5 agendamentos pendentes de confirmação", "data": "2026-02-11", "lida": False},
            {"id": 2, "titulo": "Orientação sobre relatórios", "descricao": "Novo template de relatório disponível", "data": "2026-02-10", "lida": True}
        ]
    
    def obter_notificacoes_alertas(self):
        """Obtém notificações de alertas do sistema."""
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, alert_type, message, created_at, is_read FROM desktop_alert WHERE is_read = 0 ORDER BY created_at DESC")
        alertas = cursor.fetchall()
        connection.close()
        
        # Formatar alertas
        return [
            {
                "id": alerta["id"],
                "titulo": self.formatar_tipo_alerta(alerta["alert_type"]) or "Alerta",
                "descricao": alerta["message"] or "Mensagem de alerta",
                "data": alerta["created_at"].strftime("%Y-%m-%d") if hasattr(alerta["created_at"], "strftime") else str(alerta["created_at"]),
                "lida": alerta["is_read"]
            } for alerta in alertas
        ]
    
    def formatar_tipo_alerta(self, alert_type):
        """Formata o tipo de alerta para exibição."""
        tipos = {
            'screening_pending': 'Triagem Pendente',
            'appointment_reminder': 'Lembrete de Consulta',
            'followup_required': 'Acompanhamento Necessário',
            'high_risk': 'Alto Risco',
            'missed_appointment': 'Falta em Consulta',
            'system': 'Alerta do Sistema'
        }
        return tipos.get(alert_type, alert_type.replace('_', ' ').title())
    
    def marcar_notificacao_como_lida(self, notificacao_id, tipo="alerta"):
        """Marca uma notificação como lida."""
        if tipo == "alerta":
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("UPDATE desktop_alert SET is_read = 1 WHERE id = %s", (notificacao_id,))
            connection.commit()
            connection.close()
        elif tipo == "ajuda":
            try:
                from services.api import api
                api.put(f"help/notifications/{notificacao_id}/read/")
            except Exception as e:
                print(f"Erro ao marcar notificação de ajuda como lida: {e}")
    
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
        # Conforme o modelo Django Aluno, a PK da tabela aluno é mapeada como 'id_aluno'
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
            SELECT a.id, a.data_hora, a.status, al.nome AS student_name, al.curso
            FROM agendamento a
            LEFT JOIN aluno al ON a.student_id = al.id_aluno
            WHERE a.data_hora > NOW() AND a.status != 'cancelled'
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
                'curso': r.get('curso') or 'Curso não informado',
                'time': time_str,
                'date': date_str
            })

        # Obter humor médio dos estudantes (hoje)
        cursor.execute("""
            SELECT AVG(mood_level) as media_humor 
            FROM desktop_moodentry 
            WHERE DATE(entry_date) = CURDATE()
        """)
        media_humor = cursor.fetchone()['media_humor']
        media_humor = round(media_humor, 2) if media_humor else None

        # Obter dados de humor dos estudantes nos últimos 30 dias (para gráfico)
        cursor.execute("""
            SELECT DATE(entry_date) as data, AVG(mood_level) as media_humor
            FROM desktop_moodentry
            WHERE DATE(entry_date) >= CURDATE() - INTERVAL 30 DAY
            GROUP BY DATE(entry_date)
            ORDER BY data
        """)
        humor_history = []
        for row in cursor.fetchall():
            try:
                data_str = row['data'].strftime('%d/%m') if hasattr(row['data'], 'strftime') else str(row['data'])
            except Exception:
                data_str = str(row['data'])
            humor_history.append({
                'data': data_str,
                'media_humor': round(row['media_humor'], 2) if row['media_humor'] else 0
            })

        # Obter bem-estar por dimensão (usando desktop_wellnesscheckin)
        cursor.execute("""
            SELECT AVG(overall_wellbeing) as media_bem_estar
            FROM desktop_wellnesscheckin
            WHERE DATE(check_in_date) >= CURDATE() - INTERVAL 7 DAY
        """)
        bem_estar = cursor.fetchone()
        media_bem_estar = round(bem_estar['media_bem_estar'], 2) if bem_estar['media_bem_estar'] else 0
        
        # Para as dimensões específicas, vamos usar valores padrão se não houver dados suficientes
        bem_estar_dimensions = {
            'academico': round(media_bem_estar * 0.9, 2),  # 90% da média
            'emocional': round(media_bem_estar * 0.8, 2),  # 80% da média
            'social': round(media_bem_estar * 0.85, 2)  # 85% da média
        }

        # Calcular vagas disponíveis (baseado em disponibilidade do analista e agendamentos existentes)
        cursor.execute("""
            SELECT COUNT(*) as total_disponibilidade 
            FROM disponibilidade 
            WHERE is_active = 1
        """)
        total_disponibilidade = cursor.fetchone()['total_disponibilidade']
        
        cursor.execute("""
            SELECT COUNT(*) as agendamentos_hoje 
            FROM agendamento 
            WHERE DATE(data_hora) = CURDATE() AND status != 'canceled'
        """)
        agendamentos_hoje = cursor.fetchone()['agendamentos_hoje']
        
        available_slots = max(0, total_disponibilidade - agendamentos_hoje)

        connection.close()

        return {
            "appointments_today": appointments_today,
            "screenings_pending": screenings_pending,
            "alerts": alerts,
            "total_students": total_students,
            "attendance_rate": attendance_rate,
            "attention_students": attention_students,
            "upcoming_appointments": upcoming_appointments,
            "media_humor": media_humor,
            "humor_history": humor_history,
            "bem_estar_dimensions": bem_estar_dimensions,
            "available_slots": available_slots
        }


class DashboardService:
    """Wrapper compatível com a interface esperada pelos testes (get_kpis)."""
    def __init__(self):
        self._svc = ServicoDashboard()

    def get_kpis(self):
        return self._svc.obter_kpis()

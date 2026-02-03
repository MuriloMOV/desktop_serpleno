from .api import api

class ServicoDashboard:
    def obter_kpis(self):
        """Obtém estatísticas consolidadas do dashboard via endpoint dedicado."""
        response = api.get('analytics/dashboard/')
        
        if response.get('success'):
            data = response.get('data', {})
            contadores = data.get('counters', {})
            
            # Mapeia a resposta aninhada da API para a estrutura plana esperada pela UI
            return {
                "appointments_today": contadores.get('appointments', {}).get('today', 0),
                "screenings_pending": contadores.get('screenings', {}).get('pending', 0),
                "alerts": contadores.get('alerts', {}).get('unread', 0),
                "total_students": contadores.get('students', {}).get('total', 0),
                "attendance_rate": contadores.get('appointments', {}).get('attendance_rate', 0),
                # Preserva acesso a outros dados se necessário
                "attention_students": data.get('attention_students', []),
                "upcoming_appointments": data.get('schedule', {}).get('upcoming', [])
            }
            
        return {
            "appointments_today": 0,
            "students_attention": 0,
            "total_students": 0,
            "screenings_pending": 0,
            "attendance_rate": 0
        }

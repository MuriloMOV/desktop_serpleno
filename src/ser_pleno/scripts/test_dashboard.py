
from ser_pleno.application.services.dashboard import ServicoDashboard

svc = ServicoDashboard()
data = svc.obter_kpis()

print('=== Dados do Dashboard ===')
print('Atendimentos hoje:', data.get('appointments_today'))
print('Vagas disponíveis:', data.get('available_slots'))
print('Alertas:', data.get('alerts'))
print('Total estudantes:', data.get('total_students'))
print('Média humor:', data.get('media_humor'))
print('Histórico humor:', len(data.get('humor_history', [])))
print('Bem-estar por dimensão:', data.get('bem_estar_dimensions'))
print('Próximos atendimentos:', len(data.get('upcoming_appointments', [])))
print('Estudantes em alerta:', len(data.get('attention_students', [])))

# Exibir detalhes dos atendimentos
if data.get('upcoming_appointments'):
    print('\n=== Próximos Atendimentos ===')
    for appt in data.get('upcoming_appointments'):
        print(f"{appt['student_name']} - {appt['curso']} A s {appt['time']}")

# Exibir detalhes dos estudantes em alerta
if data.get('attention_students'):
    print('\n=== Estudantes em Alerta ===')
    for student in data.get('attention_students'):
        print(f"{student['name']} - {student['attention_reason']}")


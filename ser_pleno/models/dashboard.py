class Disponibilidade:
	def __init__(self, id_disponibilidade, dias, horario, is_active, analista_id):
		self.id_disponibilidade = id_disponibilidade
		self.dias = dias
		self.horario = horario
		self.is_active = is_active
		self.analista_id = analista_id

class Agendamento:
	def __init__(self, id_agendamento, aluno_id, disponibilidade_id, data, status):
		self.id_agendamento = id_agendamento
		self.aluno_id = aluno_id
		self.disponibilidade_id = disponibilidade_id
		self.data = data
		self.status = status
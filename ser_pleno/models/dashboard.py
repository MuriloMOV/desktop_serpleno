class Disponibilidade:
	def __init__(self, id, dias, horario, is_active, analista_id):
		self.id = id
		self.dias = dias
		self.horario = horario
		self.is_active = is_active
		self.analista_id = analista_id

class Agendamento:
	def __init__(self, id, aluno_id, disponibilidade_id, data, status):
		self.id = id
		self.aluno_id = aluno_id
		self.disponibilidade_id = disponibilidade_id
		self.data = data
		self.status = status

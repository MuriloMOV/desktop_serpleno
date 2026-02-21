class Autoavaliacao:
	def __init__(self, id, aluno_id, data_avaliacao=None, bem_estar_academico=None,
				 bem_estar_emocional=None, bem_estar_social=None, reflexoes_pessoais=None, pontos_xp=None):
		self.id = id
		self.aluno_id = aluno_id
		self.data_avaliacao = data_avaliacao
		self.bem_estar_academico = bem_estar_academico
		self.bem_estar_emocional = bem_estar_emocional
		self.bem_estar_social = bem_estar_social
		self.reflexoes_pessoais = reflexoes_pessoais
		self.pontos_xp = pontos_xp

class Gamificacao:
	def __init__(self, id, pontos_atuais, nivel, conquistas, check_in, metas_pessoais, aluno_id, last_check_in_date=None):
		self.id = id
		self.pontos_atuais = pontos_atuais
		self.nivel = nivel
		self.conquistas = conquistas
		self.check_in = check_in
		self.metas_pessoais = metas_pessoais
		self.aluno_id = aluno_id
		self.last_check_in_date = last_check_in_date

class MeuHistorico:
	def __init__(self, id, aluno_id, humor_media, dias_consecutivos, total_registros):
		self.id = id
		self.aluno_id = aluno_id
		self.humor_media = humor_media
		self.dias_consecutivos = dias_consecutivos
		self.total_registros = total_registros

class RegistrosDiarios:
	def __init__(self, id, aluno_id, data, humor, observacoes=None):
		self.id = id
		self.aluno_id = aluno_id
		self.data = data
		self.humor = humor
		self.observacoes = observacoes

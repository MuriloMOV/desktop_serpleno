from .api import api

class ServicoAgendamento:
    def listar_agendamentos(self, data=None, id_estudante=None, status=None, pagina=1):
        params = {'page': pagina}
        if data:
            params['date'] = data
        if id_estudante:
            params['student'] = id_estudante
        if status:
            params['status'] = status
            
        return api.get('schedule/appointments/', params=params)

    def criar_agendamento(self, dados):
        return api.post('schedule/appointments/add/', json=dados)

    def atualizar_agendamento(self, id_agendamento, dados):
        # A rota de edição no backend é 'schedule/appointments/edit/'
        dados['id'] = id_agendamento
        return api.post('schedule/appointments/edit/', json=dados)

    def deletar_agendamento(self, id_agendamento):
        return api.delete(f'schedule/appointments/delete/{id_agendamento}/')

    def listar_horarios_disponiveis(self, data=None):
        params = {}
        if data:
            params['date'] = data
        return api.get('schedule/times/', params=params)
        params = {}
        if date:
            params['date'] = date
        return api.get('schedule/times/', params=params)

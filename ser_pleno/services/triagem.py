from .api import api

class ServicoTriagem:
    def listar_triagens(self, busca=None, status=None, prioridade=None, id_estudante=None, pagina=1):
        params = {'page': pagina}
        if busca: params['search'] = busca
        if status: params['status'] = status
        if prioridade: params['priority'] = prioridade
        if id_estudante: params['student_id'] = id_estudante
        
        return api.get('screenings/', params=params)

    def obter_triagem(self, id_triagem):
        return api.get(f'screenings/{id_triagem}/')

    def criar_triagem(self, dados):
        return api.post('screenings/create/', json=dados)

    def atualizar_triagem(self, id_triagem, dados):
        return api.put(f'screenings/{id_triagem}/update/', json=dados)

    def deletar_triagem(self, id_triagem):
        return api.delete(f'screenings/{id_triagem}/delete/')

    def listar_formularios(self):
        return api.get('screenings/forms/')

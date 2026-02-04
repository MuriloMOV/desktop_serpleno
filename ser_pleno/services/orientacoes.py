from .api import api

class ServicoOrientacoes:
    def listar_orientacoes(self, busca=None, id_estudante=None, pagina=1):
        params = {'page': pagina}
        if busca: params['search'] = busca
        if id_estudante: params['student_id'] = id_estudante
        
        return api.get('orientations/', params=params)

    def criar_orientacao(self, dados):
        return api.post('orientations/create/', json=dados)

    def obter_orientacao(self, id_orientacao):
         return api.get(f'orientations/{id_orientacao}/')

    def deletar_orientacao(self, id_orientacao):
        return api.delete(f'orientations/{id_orientacao}/delete/')
